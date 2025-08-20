# =============================================================================
# File: conftest.py (PyTest Configuration)
# =============================================================================
import pytest
import numpy as np
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="session")
def random_seed():
    """Set random seed for reproducible tests"""
    np.random.seed(42)
    return 42