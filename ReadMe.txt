# Agricultural Commodity Risk Monitoring System

A comprehensive quantitative risk management system for agricultural commodity trading desks, built with Python and Streamlit.

## Features

### Risk Management
- **Value at Risk (VaR)** calculation using multiple methodologies:
  - Historical simulation
  - Parametric (normal distribution)
  - Monte Carlo simulation
- **Expected Shortfall (Conditional VaR)** for tail risk measurement
- **Portfolio-level risk aggregation** with correlation considerations
- **Individual commodity risk metrics**

### Stress Testing
- Pre-configured historical scenarios:
  - 2008 Financial Crisis
  - COVID-19 Market Shock (2020)
  - Ukraine Conflict Impact
- Custom volatility multipliers and shock parameters
- Stressed VaR calculations across confidence levels

### Risk Monitoring
- **Real-time limit monitoring** for VaR and position sizes
- **Automated alert system** for limit breaches
- **Risk dashboard** with visual indicators and gauges
- **Correlation analysis** between commodities

### Portfolio Management
- **Position tracking** with average price calculation
- **Trade history** and P&L monitoring
- **Market value updates** with live price feeds
- **Position limit enforcement**

### Data Management
- **Yahoo Finance integration** for commodity price data
- **Automatic data caching** for performance optimization
- **Multiple commodity support**: Corn, Wheat, Soybeans, Sugar, Coffee, Cotton, Cocoa, Rice

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agricultural-risk-monitor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

4. Run the application:
```bash
streamlit run main.py
```

## Project Structure

```
agricultural-risk-monitor/
│
├── config/
│   └── config.py                 # Configuration settings
│
├── src/
│   ├── data_manager.py           # Data fetching and processing
│   ├── risk_calculator.py        # Risk calculation engine
│   ├── portfolio_manager.py      # Portfolio management
│   └── risk_monitor.py           # Risk monitoring and alerts
│
├── tests/
│   ├── conftest.py               # PyTest configuration and fixtures
│   ├── test_risk_calculator.py   # Risk calculation tests
│   └── test_portfolio_manager.py # Portfolio management tests
│
├── docker/
│   ├── Dockerfile                # Container configuration
│   └── docker-compose.yml        # Multi-service orchestration
│
├── main.py                       # Streamlit application
├── requirements.txt              # Python dependencies
├── requirements-test.txt         # Testing dependencies
├── pytest.ini                   # PyTest configuration file
└── README.md                     # This file
```

## Testing

### Running Tests with PyTest

Run all tests:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/test_risk_calculator.py
pytest tests/test_portfolio_manager.py
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

Run tests in parallel:
```bash
pytest -n auto
```

Run tests with verbose output:
```bash
pytest -v
```

Run specific test classes or methods:
```bash
pytest tests/test_risk_calculator.py::TestVaRCalculations
pytest tests/test_portfolio_manager.py::TestPositionManagement::test_add_single_position
```

### Test Configuration
- **conftest.py**: Contains shared fixtures and PyTest configuration
- **pytest.ini**: PyTest settings, markers, and command-line options
- **requirements-test.txt**: Testing-specific dependencies

### Test Coverage

The test suite uses **pytest** with comprehensive coverage including:

#### Risk Calculation Tests (`test_risk_calculator.py`)
- **VaR Methodologies**: Historical simulation, parametric (normal distribution), and Monte Carlo methods
- **Confidence Level Testing**: Parametrized tests across 90%, 95%, and 99% confidence levels
- **Expected Shortfall**: Tail risk measurement and validation of mathematical properties (ES ≤ VaR)
- **Stress Testing**: All crisis scenarios (2008 Financial Crisis, COVID-2020, Ukraine Conflict)
- **Portfolio-level Risk**: Multi-asset VaR calculations with correlation considerations
- **Edge Cases**: Robust handling of None values, empty datasets, and single-value arrays
- **Method Consistency**: Cross-validation between different VaR calculation approaches

#### Portfolio Management Tests (`test_portfolio_manager.py`)
- **Position Management**: Single and multiple position additions with average price calculations
- **Trade Scenarios**: Parametrized testing of various trade combinations (long/short, partial/full closes)
- **Market Value Updates**: Real-time portfolio valuation with missing price handling
- **Portfolio Analytics**: Weight calculations, total value aggregation, and summary statistics
- **Trade History**: Chronological audit trail maintenance and value calculations
- **Sample Data Generation**: Demo portfolio creation for testing and demonstrations
- **Edge Cases**: Zero quantity trades, negative prices, empty portfolios, and data validation

#### Advanced Testing Features
- **Parametrized Testing**: Efficient testing across multiple scenarios using `@pytest.mark.parametrize`
- **Fixtures**: Reusable test data and setup with proper isolation between tests
- **Property-based Testing**: Validation of fundamental mathematical relationships
- **Boundary Condition Testing**: Comprehensive edge case coverage
- **Error Handling**: Graceful handling of invalid inputs and system failures

#### Test Markers (defined in pytest.ini)
- `@pytest.mark.slow`: Long-running tests (deselect with `-m "not slow"`)
- `@pytest.mark.integration`: Integration tests requiring external dependencies
- `@pytest.mark.unit`: Fast unit tests for core logic
- `@pytest.mark.parametrize`: Tests with multiple parameter combinations

## Usage

### Dashboard Overview
1. **Portfolio Overview**: View current positions, allocations, and market values
2. **Risk Metrics**: Monitor VaR, Expected Shortfall, and correlations
3. **Stress Testing**: Run scenario analysis and view stressed metrics
4. **Real-time Monitoring**: Track risk limits and receive alerts
5. **Trade Management**: Add/modify positions and view trade history

### Risk Configuration
- Modify risk limits in `config/config.py`
- Add new commodities by updating `COMMODITY_TICKERS`
- Customize stress test scenarios in `STRESS_TEST_SCENARIOS`

### Key Risk Limits
- **Portfolio VaR Limit**: $20M (configurable)
- **Individual Commodity VaR**: $8M (configurable)
- **Position Limits**: Vary by commodity (see config)

## Risk Methodologies

### Value at Risk (VaR)
- **Historical Simulation**: Uses actual historical returns
- **Parametric Method**: Assumes normal distribution of returns
- **Monte Carlo**: Simulates future returns based on historical parameters

### Expected Shortfall
- Calculates average loss beyond VaR threshold
- Provides better tail risk measurement than VaR alone

### Stress Testing
- Applies historical shock scenarios to current portfolio
- Adjusts volatility based on crisis periods
- Tests portfolio resilience under extreme conditions

## Compliance Features

### Risk Monitoring
- Automated limit breach detection
- Escalation procedures for limit violations
- Audit trail for all risk calculations

### Reporting
- Daily risk reports with key metrics
- Stress test results documentation
- Position and exposure summaries

## Customization

### Adding New Commodities
1. Update `COMMODITY_TICKERS` in `config/config.py`
2. Add position limits for new commodities
3. Configure VaR limits if needed

### Custom Risk Models
- Implement new risk calculation methods in `RiskCalculator`
- Add custom stress test scenarios
- Modify correlation models as needed

### Integration
- Replace Yahoo Finance with your data provider
- Add database connectivity for position storage
- Integrate with existing trading systems

## Performance Considerations

- Data is cached for 1 hour to reduce API calls
- Efficient pandas operations for large datasets
- Streamlit caching for improved responsiveness
- Asynchronous data fetching capabilities

## Security Notes

- No sensitive data stored in browser cache
- API keys should be stored in environment variables
- Consider authentication for production deployment
- Implement proper access controls for trading functions

## Support and Maintenance

### Monitoring
- Log all risk calculations and alerts
- Monitor data feed reliability
- Track system performance metrics

### Updates
- Regular dependency updates for security
- Risk model validation and backtesting
- Compliance with regulatory changes