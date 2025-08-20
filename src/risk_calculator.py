# =============================================================================
# File: src/risk_calculator.py
# =============================================================================
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
import warnings

warnings.filterwarnings('ignore')


class RiskCalculator:
    def __init__(self):
        self.confidence_levels = [0.95, 0.99]

    def calculate_var(self, returns, confidence_level=0.95, method='historical'):
        """Calculate Value at Risk using different methods"""
        if returns is None or len(returns) == 0:
            return None

        if method == 'historical':
            return np.percentile(returns, (1 - confidence_level) * 100)

        elif method == 'parametric':
            mu = np.mean(returns)
            sigma = np.std(returns)
            return stats.norm.ppf(1 - confidence_level, mu, sigma)

        elif method == 'monte_carlo':
            # Simple Monte Carlo simulation
            mu = np.mean(returns)
            sigma = np.std(returns)
            simulated_returns = np.random.normal(mu, sigma, 10000)
            return np.percentile(simulated_returns, (1 - confidence_level) * 100)

    def calculate_expected_shortfall(self, returns, confidence_level=0.95):
        """Calculate Expected Shortfall (Conditional VaR)"""
        if returns is None or len(returns) == 0:
            return None

        var = self.calculate_var(returns, confidence_level, 'historical')
        return np.mean(returns[returns <= var])

    def calculate_portfolio_var(self, returns_matrix, weights, confidence_level=0.95):
        """Calculate portfolio VaR considering correlations"""
        if returns_matrix is None or returns_matrix.empty:
            return None

        # Calculate portfolio returns
        portfolio_returns = (returns_matrix * weights).sum(axis=1)
        return self.calculate_var(portfolio_returns, confidence_level)

    def stress_test(self, returns, scenario_type='crisis'):
        """Perform stress testing on returns"""
        if returns is None or len(returns) == 0:
            return None

        scenarios = {
            '2008_crisis': {'shock': -0.15, 'volatility_multiplier': 2.5},
            'covid_2020': {'shock': -0.25, 'volatility_multiplier': 3.0},
            'ukraine_conflict': {'shock': -0.12, 'volatility_multiplier': 2.0}
        }

        if scenario_type not in scenarios:
            scenario_type = '2008_crisis'

        scenario = scenarios[scenario_type]
        stressed_returns = returns + scenario['shock']
        stressed_volatility = np.std(returns) * scenario['volatility_multiplier']

        # Calculate stressed VaR
        stressed_var_95 = np.percentile(stressed_returns, 5)
        stressed_var_99 = np.percentile(stressed_returns, 1)

        return {
            'scenario': scenario_type,
            'stressed_var_95': stressed_var_95,
            'stressed_var_99': stressed_var_99,
            'volatility_increase': scenario['volatility_multiplier']
        }




