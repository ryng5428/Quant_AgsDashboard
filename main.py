# Agricultural Commodity Risk Monitoring System
# main.py (Streamlit Application) - CORRECTED VERSION

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go # a sub-module within the Plotly library; contains Classes which can represent graphs (Figure, Scatter, Bar, Layout, etc)
import plotly.express as px
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Import our custom modules (separate .py files from main.py)
    # main.py imports are focused on running the application, not the tests
    # Pytest-related imports only go in your test files, not main.py
from config.config import Config
from src.data_manager import DataManager
from src.risk_calculator import RiskCalculator
from src.portfolio_manager import PortfolioManager
from src.risk_monitor import RiskMonitor

# Page configuration
st.set_page_config(
    page_title="Ags Risk Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = PortfolioManager()
if 'last_update' not in st.session_state:
    st.session_state.last_update = None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_market_data():
    """Load and cache market data"""
    config = Config() # Create an Instance of (ie Instantiate) the Config Class
    data_manager = DataManager()

    portfolio_data = data_manager.get_portfolio_data(config.COMMODITY_TICKERS)

    # Calculate returns
    returns_data = pd.DataFrame()
    current_prices = {}

    for commodity, data in portfolio_data.items():
        if data is not None and not data.empty:
            returns = data_manager.calculate_returns(data)
            if returns is not None:
                returns_data[commodity] = returns
                current_prices[commodity] = data['Close'].iloc[-1]

    return portfolio_data, returns_data, current_prices


def main():
    st.title("Ags Risk Dashboard")
    st.markdown("---")

    # Sidebar
    st.sidebar.header("Portfolio Controls")

    # Load data button
    if st.sidebar.button("🔄 Refresh Market Data"):
        st.cache_data.clear()
        st.session_state.data_loaded = False
        st.rerun()

    # Load market data
    try:
        portfolio_data, returns_data, current_prices = load_market_data()
        st.session_state.data_loaded = True
        st.session_state.last_update = datetime.now()
    except Exception as e:
        st.error(f"Error loading market data: {e}")
        st.stop()

    # Initialize components (Create an instance of a class from the modules)
    config = Config()  # Instance of the Class Config from config folder, config module
    risk_calculator = RiskCalculator() # Instance of the Class RiskCalculator from source folder, risk_calculator module
    risk_monitor = RiskMonitor(risk_calculator, config) # Instance of the Class RiskMonitor from source folder, risk_monitor module

    # Generate sample portfolio if not exists
    if not st.session_state.portfolio_manager.positions:
        st.session_state.portfolio_manager.generate_sample_portfolio()

    # Update market values
    st.session_state.portfolio_manager.update_market_values(current_prices)
    portfolio_summary = st.session_state.portfolio_manager.get_portfolio_summary()

    # Generate risk report
    risk_report = risk_monitor.generate_risk_report(
        portfolio_data,
        returns_data,
        st.session_state.portfolio_manager.positions,
        portfolio_summary
    )

    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Portfolio Value",
            f"${portfolio_summary['total_value']:,.0f}",
            delta=f"{len(portfolio_summary['positions'])} positions"
        )

    # VaR Metric Section - NOW WORKS BECAUSE risk_report IS DEFINED
    with col2:
        if 'var_95_dollar' in risk_report['portfolio_metrics']:
            st.metric(
                "Daily VaR (95%)",
                f"${risk_report['portfolio_metrics']['var_95_dollar']:,.0f}",
                delta="Risk exposure"
            )
        else:
            st.metric("Daily VaR (95%)", "No data", delta="Add positions")

    # Expected Shortfall section - NOW WORKS BECAUSE risk_report IS DEFINED
    with col3:
        if 'expected_shortfall_95_dollar' in risk_report['portfolio_metrics']:
            st.metric(
                "Expected Shortfall (95%)",
                f"${risk_report['portfolio_metrics']['expected_shortfall_95_dollar']:,.0f}",
                delta="Tail risk"
            )
        else:
            st.metric("Expected Shortfall (95%)", "No data", delta="Add positions")

    with col4:
        if st.session_state.last_update:
            st.metric(
                "Last Update",
                st.session_state.last_update.strftime("%H:%M:%S"),
                delta="Real-time monitoring"
            )

    # Risk Alerts
    if risk_report['limit_breaches']:
        st.error("⚠️ RISK LIMIT BREACHES DETECTED")
        for breach in risk_report['limit_breaches']:
            severity_color = "" if breach['severity'] == 'HIGH' else ""
            st.warning(f"{severity_color} {breach['type']}: {breach['current']:.2f} > {breach['limit']:.2f}")

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Portfolio Overview",
        "Risk Metrics",
        "Stress Testing",
        "Real-time Monitoring",
        "Trade Management"
    ])

    with tab1:
        st.header("Portfolio Composition")

        col1, col2 = st.columns(2)

        with col1:
            # Portfolio pie chart
            if portfolio_summary['weights']:
                fig = px.pie(
                    values=list(portfolio_summary['weights'].values()),
                    names=list(portfolio_summary['weights'].keys()),
                    title="Portfolio Allocation"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Position details table
            positions_df = pd.DataFrame([
                {
                    'Commodity': commodity,
                    'Quantity': data['quantity'],
                    'Avg Price': f"${data['avg_price']:.2f}",
                    'Market Value': f"${data['market_value']:,.0f}",
                    'Weight': f"{portfolio_summary['weights'].get(commodity, 0) * 100:.1f}%"
                }
                for commodity, data in st.session_state.portfolio_manager.positions.items()
                if data['quantity'] != 0
            ])

            st.dataframe(positions_df, use_container_width=True)

    with tab2:
        st.header("Risk Metrics Dashboard")

        if returns_data is not None and not returns_data.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Value at Risk (VaR)")

                # VaR comparison chart section
                commodities = list(risk_report['individual_metrics'].keys())
                if commodities:  # Only show if we have individual metrics
                    var_95_values = [risk_report['individual_metrics'][c]['var_95'] * 100 for c in commodities]
                    var_99_values = [risk_report['individual_metrics'][c]['var_99'] * 100 for c in commodities]

                    fig = go.Figure(data=[
                        go.Bar(name='VaR 95%', x=commodities, y=var_95_values),
                        go.Bar(name='VaR 99%', x=commodities, y=var_99_values)
                    ])
                    fig.update_layout(barmode='group', title="VaR by Commodity (%)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Add positions to see individual commodity VaR metrics")

            with col2:
                st.subheader("Expected Shortfall")

                # Expected Shortfall chart - FIXED TO HANDLE EMPTY COMMODITIES
                if commodities:  # Only show if we have individual metrics
                    es_95_values = [risk_report['individual_metrics'][c]['expected_shortfall_95'] * 100 for c in commodities]

                    fig = go.Figure(data=[
                        go.Bar(name='ES 95%', x=commodities, y=es_95_values, marker_color='red')
                    ])
                    fig.update_layout(title="Expected Shortfall by Commodity (%)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Add positions to see individual commodity Expected Shortfall metrics")

            # Correlation heatmap
            st.subheader("Commodity Correlation Matrix")
            correlation_matrix = returns_data.corr()

            fig = px.imshow(
                correlation_matrix,
                title="Correlation Heatmap",
                color_continuous_scale="RdBu_r",
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.header("Stress Testing Results")

        if risk_report['stress_test_results']:
            # Stress test scenarios comparison
            scenarios = list(risk_report['stress_test_results'].keys())
            stressed_var_95 = [risk_report['stress_test_results'][s]['stressed_var_95'] * 100 for s in scenarios]
            stressed_var_99 = [risk_report['stress_test_results'][s]['stressed_var_99'] * 100 for s in scenarios]

            fig = go.Figure(data=[
                go.Bar(name='Stressed VaR 95%', x=scenarios, y=stressed_var_95, marker_color='orange'),
                go.Bar(name='Stressed VaR 99%', x=scenarios, y=stressed_var_99, marker_color='red')
            ])
            fig.update_layout(
                barmode='group',
                title="Stress Test Results - VaR Impact (%)",
                yaxis_title="VaR (%)"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Stress test details
            st.subheader("Scenario Details")
            for scenario, results in risk_report['stress_test_results'].items():
                with st.expander(f"{scenario.replace('_', ' ').title()} Scenario"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Stressed VaR 95%", f"{results['stressed_var_95'] * 100:.2f}%")
                    with col2:
                        st.metric("Stressed VaR 99%", f"{results['stressed_var_99'] * 100:.2f}%")
                    with col3:
                        st.metric("Volatility Multiplier", f"{results['volatility_increase']:.1f}x")

    with tab4:
        st.header("Real-time Risk Monitoring")

        # Risk limits gauge charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Portfolio VaR vs Limit")
            # FIXED TO USE THE NEW DOLLAR METRICS
            if 'var_95_dollar' in risk_report['portfolio_metrics']:
                current_var = risk_report['portfolio_metrics']['var_95_dollar'] / 1_000_000 # Report current Portfolio VaR's units in millions
                limit = config.VAR_LIMITS['portfolio'] # Config is the instance of the config class (Instantiated earlier) -> access the instance's class attribute "VAR_LIMITS" attribute (which is a dictionary) ->  look up the key "portfolio" in that dictionary

                # Create a Gauge Chart with Plotly (https://plotly.com/python/indicator/) using go.Indicator()
                    # go.Indicator is a Plotly graph object which visually represents the data as a Gauge (other common types are scatter, bar, pie, histogram, etc)
                    # 3 distinct visual elements are available to represent that value: number, delta and gauge
                        # "delta" simply displays the difference between the value with respect to a reference
                            # simply takes 1 argument: delta={'reference': number_to_compare_value_against} & compares it to your value=____ above
                    # Any combination of them can be specified via the "mode" attribute
                fig = go.Figure(go.Indicator( # fig is an instance of the Figure Class from the graph_objects module
                    mode="gauge+number+delta",
                    value=current_var, # Current Portfolio VaR (this is the no. delta will compare to)
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "VaR (USD Million)"},
                    delta={'reference': limit}, # returns difference between value vs limit (limit is the value you are specifying)
                    gauge={
                        'axis': {'range': [None, limit * 1.5]}, # gauge = limit * 1.5 to visualise VaRs exceeding VaR limit w/o exceeding the gauge
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, limit * 0.7], 'color': "green"},
                            {'range': [limit * 0.7, limit], 'color': "yellow"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': limit
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Position Concentration")
            # Show largest positions
            largest_positions = sorted(
                [(k, v['market_value']) for k, v in st.session_state.portfolio_manager.positions.items() if
                 v['quantity'] != 0],
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]

            if largest_positions:
                commodities, values = zip(*largest_positions)
                values = [abs(v) / 1_000_000 for v in values]  # Convert to millions

                fig = go.Figure(data=[
                    go.Bar(x=list(commodities), y=values, marker_color='lightblue')
                ])
                fig.update_layout(
                    title="Top 5 Positions (USD Million)",
                    yaxis_title="Position Size (USD Million)"
                )
                st.plotly_chart(fig, use_container_width=True)

        # Live risk metrics table - UPDATED TO USE NEW DOLLAR METRICS
        st.subheader("Live Risk Metrics")
        metrics_df = pd.DataFrame([
            {
                'Metric': 'Portfolio VaR (95%)',
                'Value': f"${risk_report['portfolio_metrics'].get('var_95_dollar', 0):,.0f}",
                'Limit': f"${config.VAR_LIMITS['portfolio'] * 1_000_000:,.0f}",
                'Status': '🔴 Limit Breached' if risk_report['portfolio_metrics'].get('var_95_dollar', 0) > config.VAR_LIMITS['portfolio'] * 1_000_000 else ''
            },
            {
                'Metric': 'Portfolio VaR (99%)',
                'Value': f"${risk_report['portfolio_metrics'].get('var_99_dollar', 0):,.0f}",
                'Limit': f"${config.VAR_LIMITS['portfolio'] * 1_000_000 * 1.5:,.0f}",
                'Status': '🔴 Limit Breached' if risk_report['portfolio_metrics'].get('var_99_dollar', 0) > config.VAR_LIMITS['portfolio'] * 1_000_000 * 1.5 else ''
            },
            {
                'Metric': 'Expected Shortfall (95%)',
                'Value': f"${risk_report['portfolio_metrics'].get('expected_shortfall_95_dollar', 0):,.0f}",
                'Limit': 'N/A',
                'Status': ''
            }
        ])

        st.dataframe(metrics_df, use_container_width=True)

    with tab5:
        st.header("Trade Management")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Add New Position")

            # Trade input form
            with st.form("trade_form"):
                selected_commodity = st.selectbox("Commodity", list(config.COMMODITY_TICKERS.keys()))
                quantity = st.number_input("Quantity", value=1000)
                price = st.number_input("Price", value=250.0, step=0.01)

                if st.form_submit_button("Add Trade"):
                    st.session_state.portfolio_manager.add_position(selected_commodity, quantity, price)
                    st.success(f"Added {quantity} units of {selected_commodity} at ${price:.2f}")
                    st.rerun()

        with col2:
            st.subheader("Recent Trades")

            if st.session_state.portfolio_manager.trade_history:
                trades_df = pd.DataFrame(st.session_state.portfolio_manager.trade_history[-10:])  # Last 10 trades
                trades_df['date'] = pd.to_datetime(trades_df['date']).dt.strftime('%Y-%m-%d %H:%M')
                trades_df['trade_value'] = trades_df['trade_value'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(trades_df[['date', 'commodity', 'quantity', 'price', 'trade_value']],
                             use_container_width=True)

        # Position management
        st.subheader("Position Management")

        # Create position adjustment interface
        for commodity, position in st.session_state.portfolio_manager.positions.items():
            if position['quantity'] != 0:
                with st.expander(f"{commodity} - Current: {position['quantity']} units"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Average Price:** ${position['avg_price']:.2f}")
                        st.write(f"**Market Value:** ${position['market_value']:,.0f}")

                    with col2:
                        st.write(f"**Current Price:** ${current_prices.get(commodity, 0):.2f}")
                        pnl = (current_prices.get(commodity, 0) - position['avg_price']) * position['quantity']
                        pnl_color = "green" if pnl >= 0 else "red"
                        st.markdown(f"**P&L:** <span style='color:{pnl_color}'>${pnl:,.0f}</span>",
                                    unsafe_allow_html=True)

                    with col3:
                        # Quick close position button
                        if st.button(f"Close {commodity} Position", key=f"close_{commodity}"):
                            st.session_state.portfolio_manager.add_position(
                                commodity,
                                -position['quantity'],
                                current_prices.get(commodity, position['avg_price'])
                            )
                            st.success(f"Closed {commodity} position")
                            st.rerun()

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**Data Source:** Yahoo Finance API")
    with col2:
        st.info("**Update Frequency:** Real-time with 1-hour cache")
    with col3:
        st.info("**Risk Model:** Historical VaR with Monte Carlo stress testing")


if __name__ == "__main__":
    main()
