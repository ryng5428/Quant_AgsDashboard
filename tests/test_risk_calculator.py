# =============================================================================
# File: tests/test_risk_calculator.py (PyTest Version)
# =============================================================================
import pytest
import numpy as np
import pandas as pd
from src.risk_calculator import RiskCalculator # import the RiskCalculator class from our Source Code (Function Library)


@pytest.fixture
def risk_calculator():
    """Fixture to create RiskCalculator instance"""
    return RiskCalculator() # Create an instance of the RiskCalculator class


@pytest.fixture
def sample_returns():
    """Fixture to create sample returns data"""
    np.random.seed(42)
    return np.random.normal(0.001, 0.02, 1000)


@pytest.fixture
def sample_returns_matrix():
    """Fixture to create sample returns matrix for portfolio tests"""
    np.random.seed(42)
    return pd.DataFrame({
        'Corn': np.random.normal(0.001, 0.02, 100),
        'Wheat': np.random.normal(0.0005, 0.025, 100),
        'Soybeans': np.random.normal(0.002, 0.018, 100)
    })


class TestVaRCalculations:
    """Test Value at Risk calculations"""

    def test_var_calculation_basic(self, risk_calculator, sample_returns):
        """Test basic VaR calculation methods"""
        var_hist = risk_calculator.calculate_var(sample_returns, 0.95, 'historical')
        var_param = risk_calculator.calculate_var(sample_returns, 0.95, 'parametric')
        var_mc = risk_calculator.calculate_var(sample_returns, 0.95, 'monte_carlo')

        # VaR should be negative (representing losses)
        assert var_hist < 0
        assert var_param < 0
        assert var_mc < 0

        # All VaR values should be reasonable (not extreme)
        assert var_hist > -0.1  # Not more than 10% loss
        assert var_param > -0.1
        assert var_mc > -0.1

    def test_var_different_confidence_levels(self, risk_calculator, sample_returns):
        """Test VaR at different confidence levels"""
        var_90 = risk_calculator.calculate_var(sample_returns, 0.90, 'historical')
        var_95 = risk_calculator.calculate_var(sample_returns, 0.95, 'historical')
        var_99 = risk_calculator.calculate_var(sample_returns, 0.99, 'historical')

        # Higher confidence should result in worse (more negative) VaR
        assert var_99 < var_95 < var_90

    @pytest.mark.parametrize("confidence_level", [0.90, 0.95, 0.99])
    def test_var_parametrized_confidence(self, risk_calculator, sample_returns, confidence_level):
        """Test VaR calculation across multiple confidence levels"""
        var = risk_calculator.calculate_var(sample_returns, confidence_level, 'historical')

        assert var < 0  # Should always be negative (loss)
        assert var > -1  # Should be reasonable (not 100% loss)

    @pytest.mark.parametrize("method", ['historical', 'parametric', 'monte_carlo'])
    def test_var_different_methods(self, risk_calculator, sample_returns, method):
        """Test different VaR calculation methods"""
        var = risk_calculator.calculate_var(sample_returns, 0.95, method)

        assert var is not None
        assert var < 0
        assert isinstance(var, (int, float, np.float64))

    def test_var_methods_consistency(self, risk_calculator, sample_returns):
        """Test that different VaR methods produce reasonably consistent results"""
        var_hist = risk_calculator.calculate_var(sample_returns, 0.95, 'historical')
        var_param = risk_calculator.calculate_var(sample_returns, 0.95, 'parametric')

        # Methods should be within 50% of each other (reasonable tolerance)
        assert abs(var_hist - var_param) / abs(var_hist) < 0.5

    def test_var_empty_data_handling(self, risk_calculator):
        """Test VaR calculation with edge cases"""
        # Test with None
        assert risk_calculator.calculate_var(None, 0.95) is None

        # Test with empty array
        assert risk_calculator.calculate_var([], 0.95) is None

        # Test with single value
        single_return = [0.01]
        var_single = risk_calculator.calculate_var(single_return, 0.95)
        assert var_single == 0.01


class TestExpectedShortfall:
    """Test Expected Shortfall calculations"""

    def test_expected_shortfall_basic(self, risk_calculator, sample_returns):
        """Test basic Expected Shortfall calculation"""
        es = risk_calculator.calculate_expected_shortfall(sample_returns, 0.95)
        var = risk_calculator.calculate_var(sample_returns, 0.95, 'historical')

        # ES should be more negative (worse) than VaR
        assert es < var
        assert es < 0  # Should represent a loss

    @pytest.mark.parametrize("confidence_level", [0.90, 0.95, 0.99])
    def test_expected_shortfall_confidence_levels(self, risk_calculator, sample_returns, confidence_level):
        """Test ES at different confidence levels"""
        es = risk_calculator.calculate_expected_shortfall(sample_returns, confidence_level)

        assert es < 0  # Should always be negative
        assert es > -1  # Should be reasonable

    def test_expected_shortfall_vs_var_relationship(self, risk_calculator, sample_returns):
        """Test that ES is always worse than VaR (fundamental property)"""
        for confidence in [0.90, 0.95, 0.99]:
            es = risk_calculator.calculate_expected_shortfall(sample_returns, confidence)
            var = risk_calculator.calculate_var(sample_returns, confidence, 'historical')

            assert es <= var, f"ES should be <= VaR at {confidence} confidence"

    def test_expected_shortfall_edge_cases(self, risk_calculator):
        """Test ES with edge cases"""
        # Test with None
        assert risk_calculator.calculate_expected_shortfall(None, 0.95) is None

        # Test with empty array
        assert risk_calculator.calculate_expected_shortfall([], 0.95) is None


class TestStressTesting:
    """Test stress testing functionality"""

    @pytest.mark.parametrize("scenario", ['2008_crisis', 'covid_2020', 'ukraine_conflict'])
    def test_stress_testing_all_scenarios(self, risk_calculator, sample_returns, scenario):
        """Test stress testing across all predefined scenarios"""
        stress_result = risk_calculator.stress_test(sample_returns, scenario)

        # Check result structure
        required_keys = ['scenario', 'stressed_var_95', 'stressed_var_99', 'volatility_increase']
        for key in required_keys:
            assert key in stress_result

        # Check scenario name matches
        assert stress_result['scenario'] == scenario

        # Stressed VaR should be worse than normal VaR
        normal_var_95 = risk_calculator.calculate_var(sample_returns, 0.95)
        normal_var_99 = risk_calculator.calculate_var(sample_returns, 0.99)

        assert stress_result['stressed_var_95'] < normal_var_95
        assert stress_result['stressed_var_99'] < normal_var_99

    def test_stress_test_volatility_multipliers(self, risk_calculator, sample_returns):
        """Test that different scenarios have appropriate volatility multipliers"""
        scenarios = ['2008_crisis', 'covid_2020', 'ukraine_conflict']
        expected_multipliers = {'2008_crisis': 2.5, 'covid_2020': 3.0, 'ukraine_conflict': 2.0}

        for scenario in scenarios:
            result = risk_calculator.stress_test(sample_returns, scenario)
            assert result['volatility_increase'] == expected_multipliers[scenario]

    def test_stress_test_invalid_scenario(self, risk_calculator, sample_returns):
        """Test stress testing with invalid scenario (should default to 2008_crisis)"""
        result = risk_calculator.stress_test(sample_returns, 'invalid_scenario')

        # Should default to 2008_crisis
        assert result['scenario'] == '2008_crisis'
        assert result['volatility_increase'] == 2.5

    def test_stress_test_edge_cases(self, risk_calculator):
        """Test stress testing with edge cases"""
        # Test with None
        assert risk_calculator.stress_test(None, '2008_crisis') is None

        # Test with empty array
        assert risk_calculator.stress_test([], '2008_crisis') is None


class TestPortfolioVaR:
    """Test portfolio-level VaR calculations"""

    def test_portfolio_var_basic(self, risk_calculator, sample_returns_matrix):
        """Test basic portfolio VaR calculation"""
        weights = np.array([0.4, 0.3, 0.3])  # Portfolio weights
        portfolio_var = risk_calculator.calculate_portfolio_var(
            sample_returns_matrix, weights, 0.95
        )

        assert portfolio_var is not None
        assert portfolio_var < 0  # Should represent a loss

    def test_portfolio_var_equal_weights(self, risk_calculator, sample_returns_matrix):
        """Test portfolio VaR with equal weights"""
        n_assets = len(sample_returns_matrix.columns)
        weights = np.array([1 / n_assets] * n_assets)

        portfolio_var = risk_calculator.calculate_portfolio_var(
            sample_returns_matrix, weights, 0.95
        )

        assert portfolio_var is not None
        assert portfolio_var < 0

    def test_portfolio_var_edge_cases(self, risk_calculator):
        """Test portfolio VaR with edge cases"""
        # Test with None
        weights = np.array([0.5, 0.5])
        assert risk_calculator.calculate_portfolio_var(None, weights, 0.95) is None

        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        assert risk_calculator.calculate_portfolio_var(empty_df, weights, 0.95) is None