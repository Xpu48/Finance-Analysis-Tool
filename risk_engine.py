import numpy as np
import pandas as pd
from scipy.stats import norm

def calculate_portfolio_returns(price_dict, weights):
    """
    Safely aligns multiple financial series by handling date indexes,
    filling structural gaps, and calculating clean weighted daily returns.
    """
    # 1. Force all incoming series to have flat, timezone-naive datetime indexes
    cleaned_series = {}
    for ticker, series in price_dict.items():
        # Ensure the index is converted to datetime type safely
        series.index = pd.to_datetime(series.index)
        if series.index.tz is not None:
            series.index = series.index.tz_localize(None)
        
        # Remove any duplicate dates that might skew matrix multiplication
        series = series.loc[~series.index.duplicated(keep='first')]
        cleaned_series[ticker] = series
        
    # 2. Build the DataFrame (Pandas will align them automatically by date)
    df = pd.DataFrame(cleaned_series)
    
    # 3. CRITICAL RISK FIX: Fill individual stock gaps *before* dropping rows
    # This prevents scattered NaN holiday gaps from destroying the entire matrix
    df = df.ffill().bfill()
    
    # 4. Calculate log or percent returns and drop the initial lookback row
    returns = df.pct_change().dropna()
    
    # 5. Dot product calculation to determine clean daily portfolio variance
    portfolio_returns = returns.dot(weights)
    return portfolio_returns, returns

def calculate_parametric_var(portfolio_returns, confidence_level=0.95):
    """Calculates Parametric Value at Risk (VaR) by isolating the downside tail."""
    if portfolio_returns.empty or np.std(portfolio_returns) == 0:
        return 0.0
        
    mean = np.mean(portfolio_returns)
    std_dev = np.std(portfolio_returns)
    
    # norm.ppf(0.95) yields 1.64485
    z_score = norm.ppf(confidence_level)
    
    # CRITICAL MATH FIX: Downside worst-case return is (mean - z_score * std_dev)
    # Taking the negative converts this negative return into a positive loss metric
    var_percentage = -(mean - z_score * std_dev)
    return max(0, var_percentage)


def run_monte_carlo_simulation(returns, weights, initial_investment, days=252, simulations=1000):
    """Simulates market movements and returns the VaR along with all simulated paths for visualization."""
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values
    
    port_mean = np.dot(weights, mean_returns)
    port_var = np.dot(weights, np.dot(cov_matrix, weights))
    port_std = np.sqrt(port_var)
    
    # Apply a 20% annual systemic shock divided by trading days
    stress_drift = port_mean - (0.20 / 252) 
    
    sim_returns = np.random.normal(stress_drift, port_std, (days, simulations))
    
    # Keep track of the full array path matrices
    portfolio_sim_paths = initial_investment * np.cumprod(1 + sim_returns, axis=0)
    
    ending_values = portfolio_sim_paths[-1]
    simulated_losses = initial_investment - ending_values
    monte_carlo_var = np.percentile(simulated_losses, 95)
    
    # Return the metrics AND the full path matrix for charting
    return  monte_carlo_var, ending_values, portfolio_sim_paths

