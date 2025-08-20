# =============================================================================
# File: src/portfolio_manager.py
# =============================================================================
import pandas as pd
import numpy as np
from datetime import datetime


class PortfolioManager:
    def __init__(self):
        self.positions = {}
        self.market_values = {}
        self.trade_history = []

    def add_position(self, commodity, quantity, price, trade_date=None):
        """Add or update a commodity position"""
        if trade_date is None:
            trade_date = datetime.now()

        if commodity not in self.positions:
            self.positions[commodity] = {
                'quantity': 0,
                'avg_price': 0,
                'market_value': 0
            }

        # Update position
        old_quantity = self.positions[commodity]['quantity']
        old_avg_price = self.positions[commodity]['avg_price']

        new_quantity = old_quantity + quantity
        if new_quantity != 0:
            new_avg_price = ((old_quantity * old_avg_price) + (quantity * price)) / new_quantity
        else:
            new_avg_price = 0

        self.positions[commodity]['quantity'] = new_quantity
        self.positions[commodity]['avg_price'] = new_avg_price

        # Record trade
        self.trade_history.append({
            'date': trade_date,
            'commodity': commodity,
            'quantity': quantity,
            'price': price,
            'trade_value': quantity * price
        })

    def update_market_values(self, current_prices):
        """Update market values based on current prices"""
        for commodity in self.positions:
            if commodity in current_prices:
                quantity = self.positions[commodity]['quantity']
                current_price = current_prices[commodity]
                market_value = quantity * current_price
                self.positions[commodity]['market_value'] = market_value
                self.market_values[commodity] = market_value

    def get_portfolio_summary(self):
        """Get portfolio summary statistics"""
        total_value = sum(self.market_values.values())
        weights = {k: v / total_value if total_value != 0 else 0
                   for k, v in self.market_values.items()}

        return {
            'total_value': total_value,
            'positions': self.positions,
            'weights': weights,
            'num_positions': len([p for p in self.positions.values() if p['quantity'] != 0])
        }

    def generate_sample_portfolio(self):
        """Generate sample portfolio for demonstration"""
        sample_trades = [
            ('Corn', 70000, 350),
            ('Wheat', 58000, 550),
            ('Soybeans', 59500, 900),
            ('Sugar', 72000, 18),
            ('Coffee', 64000, 270),
            ('Cotton', 77000, 65),
            ('Cocoa', 2000, 8000)
        ]

        for commodity, quantity, price in sample_trades:
            self.add_position(commodity, quantity, price)
