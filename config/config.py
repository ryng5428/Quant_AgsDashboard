import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class Config:
    # Commodity tickers for data fetching
    COMMODITY_TICKERS = {
        'Corn': 'ZC=F', #Original CORN=F
        'Wheat': 'ZW=F',
        'Soybeans': 'ZS=F',
        'Sugar': 'SB=F',
        'Coffee': 'KC=F',
        'Cotton': 'CT=F',
        'Cocoa': 'CC=F',
        'Rice': 'ZR=F'
    }

    # Risk parameters
    CONFIDENCE_LEVELS = [0.95, 0.99]
    VAR_HORIZON = 1  # 1 day
    STRESS_TEST_SCENARIOS = ['2008_crisis', 'covid_2020', 'ukraine_conflict']

    # Position limits (in USD millions)
    POSITION_LIMITS = {
        'Corn': 50,
        'Wheat': 40,
        'Soybeans': 60,
        'Sugar': 30,
        'Coffee': 35,
        'Cotton': 25,
        'Cocoa': 20,
        'Rice': 15
    }

    # VaR limits (in USD millions)
    VAR_LIMITS = {
        'portfolio': 3,
        'individual': 1.2
    }
