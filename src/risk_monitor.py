# =============================================================================
# File: src/risk_monitor.py
# =============================================================================
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging


class RiskMonitor:
    def __init__(self, risk_calculator, config):
        self.risk_calculator = risk_calculator
        self.config = config
        self.alerts = []
        self.logger = logging.getLogger(__name__)

    def check_var_limits(self, portfolio_var, individual_vars):
        """Check if VaR limits are breached"""
        breaches = []

        # Check portfolio VaR
        if abs(portfolio_var) > self.config.VAR_LIMITS['portfolio']:
            breaches.append({
                'type': 'Portfolio VaR Breach',
                'current': abs(portfolio_var),
                'limit': self.config.VAR_LIMITS['portfolio'],
                'severity': 'HIGH'
            })

        # Check individual VaRs
        for commodity, var in individual_vars.items():
            if abs(var) > self.config.VAR_LIMITS['individual']:
                breaches.append({
                    'type': f'{commodity} VaR Breach',
                    'current': abs(var),
                    'limit': self.config.VAR_LIMITS['individual'],
                    'severity': 'MEDIUM'
                })

        return breaches

    def check_position_limits(self, positions):
        """Check if position limits are breached"""
        breaches = []

        for commodity, position_data in positions.items():
            market_value = abs(position_data.get('market_value', 0)) / 1_000_000  # Convert to millions
            limit = self.config.POSITION_LIMITS.get(commodity, 0)

            if market_value > limit:
                breaches.append({
                    'type': f'{commodity} Position Limit Breach',
                    'current': market_value,
                    'limit': limit,
                    'severity': 'HIGH'
                })

        return breaches

    def generate_risk_report(self, portfolio_data, returns_data, positions, portfolio_summary):
        """Generate comprehensive risk report with position-weighted calculations"""
        report = {
            'timestamp': datetime.now(),
            'portfolio_metrics': {},
            'individual_metrics': {},
            'stress_test_results': {},
            'limit_breaches': [],
            'recommendations': []
        }

        if returns_data is None or returns_data.empty or portfolio_summary['total_value'] == 0:
            return report

        # Calculate position-weighted portfolio returns
        weights = portfolio_summary['weights']
        portfolio_returns = pd.Series(0.0, index=returns_data.index)

        for commodity in returns_data.columns:
            if commodity in weights and weights[commodity] > 0:
                portfolio_returns += returns_data[commodity] * weights[commodity]

        # Calculate portfolio-level metrics in dollar terms
        total_value = portfolio_summary['total_value']

        if len(portfolio_returns.dropna()) > 0:
            var_95_pct = self.risk_calculator.calculate_var(portfolio_returns.dropna(), 0.95)
            var_99_pct = self.risk_calculator.calculate_var(portfolio_returns.dropna(), 0.99)
            es_95_pct = self.risk_calculator.calculate_expected_shortfall(portfolio_returns.dropna(), 0.95)
            es_99_pct = self.risk_calculator.calculate_expected_shortfall(portfolio_returns.dropna(), 0.99)

            report['portfolio_metrics'] = {
                'var_95': var_95_pct,
                'var_99': var_99_pct,
                'var_95_dollar': abs(var_95_pct * total_value) if var_95_pct else 0,
                'var_99_dollar': abs(var_99_pct * total_value) if var_99_pct else 0,
                'expected_shortfall_95': es_95_pct,
                'expected_shortfall_99': es_99_pct,
                'expected_shortfall_95_dollar': abs(es_95_pct * total_value) if es_95_pct else 0,
                'expected_shortfall_99_dollar': abs(es_99_pct * total_value) if es_99_pct else 0,
                'volatility': np.std(portfolio_returns.dropna()) * np.sqrt(252) if len(
                    portfolio_returns.dropna()) > 0 else 0
            }

        # Calculate individual commodity metrics in dollar terms
        individual_vars = {}
        for commodity in returns_data.columns:
            if commodity in positions and positions[commodity]['quantity'] != 0:
                commodity_returns = returns_data[commodity].dropna()
                position_value = abs(positions[commodity]['market_value'])

                if len(commodity_returns) > 0 and position_value > 0:
                    var_95_pct = self.risk_calculator.calculate_var(commodity_returns, 0.95)
                    var_99_pct = self.risk_calculator.calculate_var(commodity_returns, 0.99)
                    es_95_pct = self.risk_calculator.calculate_expected_shortfall(commodity_returns, 0.95)

                    # Convert to dollar amounts
                    var_95_dollar = abs(var_95_pct * position_value) if var_95_pct else 0
                    individual_vars[commodity] = var_95_dollar

                    report['individual_metrics'][commodity] = {
                        'var_95': var_95_pct,
                        'var_99': var_99_pct,
                        'var_95_dollar': var_95_dollar,
                        'var_99_dollar': abs(var_99_pct * position_value) if var_99_pct else 0,
                        'expected_shortfall_95': es_95_pct,
                        'expected_shortfall_95_dollar': abs(es_95_pct * position_value) if es_95_pct else 0,
                        'volatility': np.std(commodity_returns) * np.sqrt(252),
                        'position_value': position_value
                    }

        # Stress testing with position sizes
        for scenario in self.config.STRESS_TEST_SCENARIOS:
            if len(portfolio_returns.dropna()) > 0:
                stress_result = self.risk_calculator.stress_test(portfolio_returns.dropna(), scenario)
                if stress_result:
                    # Convert to dollar terms
                    stress_result['stressed_var_95_dollar'] = abs(stress_result['stressed_var_95'] * total_value)
                    stress_result['stressed_var_99_dollar'] = abs(stress_result['stressed_var_99'] * total_value)
                    report['stress_test_results'][scenario] = stress_result

        # Check limit breaches using dollar amounts
        if 'var_95_dollar' in report['portfolio_metrics']:
            portfolio_var_dollar = report['portfolio_metrics']['var_95_dollar'] / 1_000_000  # Convert to millions
            var_breaches = self.check_var_limits(portfolio_var_dollar,
                                                 {k: v / 1_000_000 for k, v in individual_vars.items()})
            report['limit_breaches'].extend(var_breaches)

        position_breaches = self.check_position_limits(positions)
        report['limit_breaches'].extend(position_breaches)

        # Generate recommendations
        if report['limit_breaches']:
            report['recommendations'].append("Immediate attention required due to limit breaches")

        if len(report['limit_breaches']) > 3:
            report['recommendations'].append("Consider portfolio rebalancing")

        # Add position-specific recommendations
        if total_value > 0:
            for commodity, metrics in report['individual_metrics'].items():
                if metrics['var_95_dollar'] / 1_000_000 > 5:  # More than $5M VaR
                    report['recommendations'].append(f"High risk concentration in {commodity}")

        return report