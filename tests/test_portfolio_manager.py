# =============================================================================
# File: tests/test_portfolio_manager.py (PyTest Version)
# =============================================================================
import pytest
from datetime import datetime, timedelta
from src.portfolio_manager import PortfolioManager


@pytest.fixture
def portfolio():
    """Fixture to create fresh PortfolioManager instance for each test"""
    return PortfolioManager()


@pytest.fixture
def portfolio_with_positions():
    """Fixture with pre-loaded sample positions"""
    p = PortfolioManager()
    p.generate_sample_portfolio()
    return p


class TestPositionManagement:
    """Test position management functionality"""

    def test_add_single_position(self, portfolio):
        """Test adding a single position to empty portfolio"""
        portfolio.add_position('Corn', 1000, 6.50)

        assert 'Corn' in portfolio.positions
        assert portfolio.positions['Corn']['quantity'] == 1000
        assert portfolio.positions['Corn']['avg_price'] == 6.50
        assert portfolio.positions['Corn']['market_value'] == 0  # Not updated yet

    def test_add_multiple_positions(self, portfolio):
        """Test adding multiple different positions"""
        trades = [
            ('Corn', 1000, 6.50),
            ('Wheat', 500, 8.00),
            ('Soybeans', 750, 14.80)
        ]

        for commodity, quantity, price in trades:
            portfolio.add_position(commodity, quantity, price)

        assert len([p for p in portfolio.positions.values() if p['quantity'] != 0]) == 3
        assert all(commodity in portfolio.positions for commodity, _, _ in trades)

    @pytest.mark.parametrize("quantity1,price1,quantity2,price2,expected_qty,expected_avg", [
        (500, 8.00, 500, 9.00, 1000, 8.50),  # Equal quantities
        (300, 10.00, 700, 15.00, 1000, 13.50),  # Unequal quantities
        (1000, 5.00, -500, 6.00, 500, 5.00),  # Partial close
        (1000, 10.00, -1000, 12.00, 0, 0),  # Full close
    ])
    def test_position_averaging_scenarios(self, portfolio, quantity1, price1, quantity2, price2,
                                          expected_qty, expected_avg):
        """Test position averaging with various trade scenarios"""
        portfolio.add_position('Wheat', quantity1, price1)
        portfolio.add_position('Wheat', quantity2, price2)

        assert portfolio.positions['Wheat']['quantity'] == expected_qty
        assert abs(portfolio.positions['Wheat']['avg_price'] - expected_avg) < 0.01

    def test_position_with_timestamp(self, portfolio):
        """Test position addition with custom timestamp"""
        trade_date = datetime(2024, 1, 15, 10, 30, 0)
        portfolio.add_position('Sugar', 1200, 0.22, trade_date)

        assert len(portfolio.trade_history) == 1
        assert portfolio.trade_history[0]['date'] == trade_date
        assert portfolio.trade_history[0]['commodity'] == 'Sugar'

    def test_long_and_short_positions(self, portfolio):
        """Test handling of long and short positions"""
        # Add long position
        portfolio.add_position('Coffee', 400, 1.85)
        assert portfolio.positions['Coffee']['quantity'] == 400

        # Add short position (negative quantity)
        portfolio.add_position('Cotton', -700, 0.75)
        assert portfolio.positions['Cotton']['quantity'] == -700

        # Verify both positions exist
        assert len([p for p in portfolio.positions.values() if p['quantity'] != 0]) == 2


class TestMarketValueUpdates:
    """Test market value update functionality"""

    def test_market_value_update_single_position(self, portfolio):
        """Test market value update for single position"""
        portfolio.add_position('Sugar', 1000, 0.20)
        current_prices = {'Sugar': 0.25}

        portfolio.update_market_values(current_prices)

        expected_value = 1000 * 0.25
        assert portfolio.positions['Sugar']['market_value'] == expected_value
        assert portfolio.market_values['Sugar'] == expected_value

    def test_market_value_update_multiple_positions(self, portfolio):
        """Test market value updates for multiple positions"""
        positions_data = [
            ('Corn', 1000, 6.50),
            ('Wheat', 800, 8.25),
            ('Soybeans', 600, 14.80)
        ]

        for commodity, quantity, price in positions_data:
            portfolio.add_position(commodity, quantity, price)

        current_prices = {'Corn': 6.75, 'Wheat': 8.50, 'Soybeans': 15.20}
        portfolio.update_market_values(current_prices)

        # Check individual market values
        assert portfolio.positions['Corn']['market_value'] == 1000 * 6.75
        assert portfolio.positions['Wheat']['market_value'] == 800 * 8.50
        assert portfolio.positions['Soybeans']['market_value'] == 600 * 15.20

    def test_market_value_missing_prices(self, portfolio):
        """Test market value update when some prices are missing"""
        portfolio.add_position('Coffee', 500, 1.85)
        portfolio.add_position('Cotton', 700, 0.75)

        # Only provide price for one commodity
        current_prices = {'Coffee': 1.90}
        portfolio.update_market_values(current_prices)

        # Coffee should be updated, Cotton should remain at 0
        assert portfolio.positions['Coffee']['market_value'] == 500 * 1.90
        assert portfolio.positions['Cotton']['market_value'] == 0

    def test_market_value_zero_quantity(self, portfolio):
        """Test market value update for positions with zero quantity"""
        portfolio.add_position('Cocoa', 500, 2.50)
        portfolio.add_position('Cocoa', -500, 2.60)  # Close position

        current_prices = {'Cocoa': 2.75}
        portfolio.update_market_values(current_prices)

        # Should be zero since quantity is zero
        assert portfolio.positions['Cocoa']['market_value'] == 0


class TestPortfolioSummary:
    """Test portfolio summary and statistics"""

    def test_portfolio_summary_empty(self, portfolio):
        """Test portfolio summary with no positions"""
        summary = portfolio.get_portfolio_summary()

        assert summary['total_value'] == 0
        assert summary['num_positions'] == 0
        assert len(summary['weights']) == 0

    def test_portfolio_summary_with_positions(self, portfolio_with_positions):
        """Test portfolio summary with sample positions"""
        # Update with sample prices
        current_prices = {
            'Corn': 6.75, 'Wheat': 8.50, 'Soybeans': 15.20,
            'Sugar': 0.24, 'Coffee': 1.90, 'Cotton': 0.78
        }

        portfolio_with_positions.update_market_values(current_prices)
        summary = portfolio_with_positions.get_portfolio_summary()

        assert summary['total_value'] > 0
        assert summary['num_positions'] > 0

        # Weights should sum to approximately 1.0 (within floating point precision)
        weights_sum = sum(summary['weights'].values())
        assert abs(weights_sum - 1.0) < 0.01

    def test_portfolio_weights_calculation(self, portfolio):
        """Test portfolio weights calculation"""
        # Add positions with known values
        portfolio.add_position('Corn', 100, 10.00)  # $1,000
        portfolio.add_position('Wheat', 200, 5.00)  # $1,000
        portfolio.add_position('Sugar', 5000, 0.40)  # $2,000
        # Total: $4,000

        current_prices = {'Corn': 10.00, 'Wheat': 5.00, 'Sugar': 0.40}
        portfolio.update_market_values(current_prices)
        summary = portfolio.get_portfolio_summary()

        # Check weights
        assert abs(summary['weights']['Corn'] - 0.25) < 0.01  # 1000/4000
        assert abs(summary['weights']['Wheat'] - 0.25) < 0.01  # 1000/4000
        assert abs(summary['weights']['Sugar'] - 0.50) < 0.01  # 2000/4000


class TestTradeHistory:
    """Test trade history tracking"""

    def test_trade_history_recording(self, portfolio):
        """Test that trades are properly recorded in history"""
        trade_date = datetime(2024, 1, 15)
        portfolio.add_position('Rice', 800, 12.50, trade_date)

        assert len(portfolio.trade_history) == 1
        trade = portfolio.trade_history[0]

        assert trade['date'] == trade_date
        assert trade['commodity'] == 'Rice'
        assert trade['quantity'] == 800
        assert trade['price'] == 12.50
        assert trade['trade_value'] == 800 * 12.50

    def test_multiple_trades_history(self, portfolio):
        """Test multiple trades are recorded in chronological order"""
        trades = [
            ('Corn', 1000, 6.50, datetime(2024, 1, 10)),
            ('Wheat', 500, 8.00, datetime(2024, 1, 11)),
            ('Corn', 500, 6.75, datetime(2024, 1, 12))  # Additional corn
        ]

        for commodity, quantity, price, date in trades:
            portfolio.add_position(commodity, quantity, price, date)

        assert len(portfolio.trade_history) == 3

        # Check chronological order
        for i, (commodity, quantity, price, date) in enumerate(trades):
            trade = portfolio.trade_history[i]
            assert trade['commodity'] == commodity
            assert trade['date'] == date

    def test_trade_value_calculation(self, portfolio):
        """Test trade value calculation in history"""
        test_cases = [
            ('Corn', 1000, 6.50, 6500.00),
            ('Wheat', -500, 8.00, -4000.00),  # Short position
            ('Sugar', 2500, 0.22, 550.00)
        ]

        for commodity, quantity, price, expected_value in test_cases:
            portfolio.add_position(commodity, quantity, price)

        for i, (_, quantity, price, expected_value) in enumerate(test_cases):
            trade = portfolio.trade_history[i]
            assert trade['trade_value'] == expected_value


class TestSamplePortfolioGeneration:
    """Test sample portfolio generation"""

    def test_generate_sample_portfolio(self, portfolio):
        """Test sample portfolio generation creates expected positions"""
        portfolio.generate_sample_portfolio()

        # Should create positions for multiple commodities
        active_positions = [p for p in portfolio.positions.values() if p['quantity'] != 0]
        assert len(active_positions) > 0

        # Should have trade history
        assert len(portfolio.trade_history) > 0

        # All positions should have reasonable values
        for commodity, position in portfolio.positions.items():
            if position['quantity'] != 0:
                assert position['avg_price'] > 0
                assert position['quantity'] > 0

    def test_sample_portfolio_specific_commodities(self, portfolio_with_positions):
        """Test that sample portfolio includes expected commodities"""
        expected_commodities = ['Corn', 'Wheat', 'Soybeans', 'Sugar', 'Coffee', 'Cotton']

        for commodity in expected_commodities:
            assert commodity in portfolio_with_positions.positions
            assert portfolio_with_positions.positions[commodity]['quantity'] > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_add_position_zero_quantity(self, portfolio):
        """Test adding position with zero quantity"""
        portfolio.add_position('Corn', 0, 6.50)

        # Position should be created but with zero quantity
        assert 'Corn' in portfolio.positions
        assert portfolio.positions['Corn']['quantity'] == 0

    def test_add_position_negative_price(self, portfolio):
        """Test adding position with negative price (should still work)"""
        portfolio.add_position('Wheat', 1000, -8.00)  # Unusual but possible

        assert portfolio.positions['Wheat']['avg_price'] == -8.00

    def test_update_market_values_empty_prices(self, portfolio):
        """Test market value update with empty price dictionary"""
        portfolio.add_position('Sugar', 1000, 0.20)

        # Update with empty prices
        portfolio.update_market_values({})

        # Market value should remain 0
        assert portfolio.positions['Sugar']['market_value'] == 0

    def test_portfolio_summary_single_position(self, portfolio):
        """Test portfolio summary with single position"""
        portfolio.add_position('Coffee', 400, 1.85)
        current_prices = {'Coffee': 1.90}

        portfolio.update_market_values(current_prices)
        summary = portfolio.get_portfolio_summary()

        assert summary['total_value'] == 400 * 1.90
        assert summary['num_positions'] == 1
        assert summary['weights']['Coffee'] == 1.0  # 100% weight