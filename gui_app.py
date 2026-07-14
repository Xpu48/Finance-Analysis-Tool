import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database as db
import risk_engine as risk

# Page configurations
st.set_page_config(page_title="Enterprise Risk Analytics", layout="wide")
st.title("📊 Enterprise Risk & Portfolio Analytics Tool")
st.markdown("---")

# Initialize database
db.init_db()

# Sidebar User Inputs
st.sidebar.header("📁 Portfolio Configuration")
ticker_input = st.sidebar.text_input("Assets (comma-separated)", "AAPL, MSFT, GOOGL, AMZN")
weights_input = st.sidebar.text_input("Weights (comma-separated)", "0.3, 0.3, 0.2, 0.2")
initial_investment = st.sidebar.number_input("Portfolio Value (£)", min_value=10000, value=1000000, step=50000)
simulations = st.sidebar.slider("Monte Carlo Simulations", min_value=100, max_value=5000, value=1000, step=100)

# Process sidebar text inputs into lists/arrays
tickers = [t.strip().upper() for t in ticker_input.split(",")]
weights = np.array([float(w.strip()) for w in weights_input.split(",")])

if len(tickers) != len(weights):
    st.sidebar.error("❌ Total tickers must match total weights!")
elif not np.isclose(np.sum(weights), 1.0):
    st.sidebar.warning("⚠️ Weights should ideally sum up to 1.0")

# Run Analytics button
if st.sidebar.button("⚡ Run Risk Analysis"):
    with st.spinner("Fetching 5 years of historical market data..."):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        price_data = {}
        
        for ticker in tickers:
            try:
                data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), multi_level_index=False)
                if not data.empty and 'Close' in data.columns:
                    series = data['Close'].squeeze()
                    if series.isnull().any():
                        series = series.ffill().bfill()
                    price_data[ticker] = series
                    db.save_to_db(data, ticker)
            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {e}")
                
        if len(price_data) == len(tickers):
            # 1. Run Calculations
            port_returns, asset_returns = risk.calculate_portfolio_returns(price_data, weights)
            p_var = risk.calculate_parametric_var(port_returns, confidence_level=0.95)
            mc_var, ending_values, paths = risk.run_monte_carlo_simulation(asset_returns, weights, initial_investment, simulations=simulations)
            
            # 2. Key Performance Indicators (KPI) Blocks
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Daily Parametric VaR (95%)", value=f"{p_var * 100:.2f}%")
            with col2:
                st.metric(label="Daily Capital at Risk", value=f"£{initial_investment * p_var:,.2f}")
            with col3:
                st.metric(label="Simulated Annual Stress Loss", value=f"£{mc_var:,.2f}")
                
            st.markdown("---")
            
            # 3. Interactive Chart Layout
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.subheader("📉 Monte Carlo Simulation Paths (Systemic Crash Test)")
                # Build an interactive Plotly chart for the asset projection paths
                fig_paths = go.Figure()
                # Plot up to 50 paths to avoid browser rendering lag
                for i in range(min(50, simulations)):
                    fig_paths.add_trace(go.Scatter(y=paths[:, i], mode='lines', line=dict(width=1), opacity=0.4, showlegend=False))
                fig_paths.update_layout(xaxis_title="Trading Days", yaxis_title="Portfolio Value (£)", template="plotly_dark")
                st.plotly_chart(fig_paths, use_container_width=True)
                
            with chart_col2:
                st.subheader("🧮 Terminal Value Distribution")
                # Histogram layout showing the distribution of losses
                fig_dist = go.Figure()
                fig_dist.add_trace(go.Histogram(x=ending_values, nbinsx=50, marker_color='#ff4b4b', opacity=0.75))
                fig_dist.add_trace(go.Scatter(x=[initial_investment - mc_var, initial_investment - mc_var], y=[0, 10], mode="lines", name="95% VaR Threshold", line=dict(color="yellow", width=3, dash="dash")))
                fig_dist.update_layout(xaxis_title="Ending Portfolio Value (£)", yaxis_title="Frequency", template="plotly_dark")
                st.plotly_chart(fig_dist, use_container_width=True)
                
            st.success("Analysis Complete! Data lineage successfully written to SQLite database.")
        else:
            st.error("Failed to gather all asset classes. Verify connection and ticker list.")
