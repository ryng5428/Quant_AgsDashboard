# =============================================================================
# File: src/data_manager.py
# =============================================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging


class DataManager:
    def __init__(self):
        self.data_cache = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def fetch_commodity_data(self, ticker, period='2y'):
        """Fetch commodity price data from Yahoo Finance"""
        try:
            commodity = yf.Ticker(ticker)
            data = commodity.history(period=period)
            if data.empty:
                self.logger.warning(f"No data found for {ticker}")
                return None
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    def calculate_returns(self, price_data):
        """Calculate daily returns from price data"""
        if price_data is None or price_data.empty:
            return None
        return price_data['Close'].pct_change().dropna()

    def get_portfolio_data(self, tickers_dict, period='2y'):
        """Fetch data for all commodities in portfolio"""
        portfolio_data = {}
        for name, ticker in tickers_dict.items():
            data = self.fetch_commodity_data(ticker, period)
            if data is not None:
                portfolio_data[name] = data
            else:
                self.logger.warning(f"Failed to fetch data for {name}")
        return portfolio_data
