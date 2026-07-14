import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import database as db
import risk_engine as risk

def main():
    print("Initializing Enterprise Risk Analytics Tool...")
    db.init_db()
    
    # Define Portfolio parameters
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    weights = np.array([0.3, 0.3, 0.2, 0.2])
    initial_investment = 1_000_000 # £1M Portfolio
    
    # Date logic for 5 years of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    price_data = {}
    
    print("Fetching 5 years of historical data from open-source API...")
    for ticker in tickers:
        try:
            # CRITICAL FIX: multi_level_index=False flattens the returned columns into basic strings
            data = yf.download(
                ticker, 
                start=start_date.strftime('%Y-%m-%d'), 
                end=end_date.strftime('%Y-%m-%d'), 
                multi_level_index=False
            )
            
            if not data.empty and 'Close' in data.columns:
                # Squeeze data to explicitly strip multi-dimensional remnants
                series = data['Close'].squeeze()
                
                # Check for and fix missing rows safely
                if series.isnull().any():
                    series = series.ffill().bfill()
                
                price_data[ticker] = series
                db.save_to_db(data, ticker)
            else:
                print(f" Warning: API returned empty or missing 'Close' column for {ticker}")
                
        except Exception as e:
            db.log_governance_event(f"Failed to fetch {ticker}", "FAILED", 0)
            print(f"Error fetching data for {ticker}: {e}")
            
    if len(price_data) < len(tickers):
        print(f"\n❌ Error: Critical Data Failure. Only gathered data for {list(price_data.keys())}.")
        print("Please review your internet connection or ticker selections. Exiting calculations.")
        return

    print("\nProcessing Risk Engine Calculations...")
    # Process Risks
    port_returns, asset_returns = risk.calculate_portfolio_returns(price_data, weights)
    
    # Calculate Parametric VaR
    p_var = risk.calculate_parametric_var(port_returns, confidence_level=0.95)
    print(f"\n--- Risk Profile Metrics ---")
    print(f"Daily Parametric VaR (95% Confidence): {p_var * 100:.2f}%")
    print(f"Estimated Daily Capital at Risk on £1M: £{initial_investment * p_var:,.2f}")
    
    # Run Systemic Crash Monte Carlo Simulation
    mc_var, paths = risk.run_monte_carlo_simulation(asset_returns, weights, initial_investment)
    print(f"\n--- 1-Year Monte Carlo Crash Simulation (Under Stress Conditions) ---")
    print(f"Simulated Annual Capital at Risk (95% VaR): £{mc_var:,.2f}")
    print(f"Worst Case Simulated Portfolio Value: £{np.min(paths):,.2f}")

if __name__ == "__main__":
    main()
