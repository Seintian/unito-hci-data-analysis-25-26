import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

def resample_data(df: pd.DataFrame, timestamp_col: str, rule: str = 'D', columns: list = None) -> pd.DataFrame:
    """
    Resamples the dataframe by a time rule (e.g., 'D' for daily, 'ME' for month end).
    
    Args:
        df (pd.DataFrame): Input dataframe.
        timestamp_col (str): Column containing datetime objects.
        rule (str): Resampling frequency.
        columns (list): Columns to aggregate (sum/mean).

    Returns:
        pd.DataFrame: Resampled time series.
    """
    # Ensure datetime
    ts_df = df.copy()
    ts_df[timestamp_col] = pd.to_datetime(ts_df[timestamp_col], errors='coerce')
    ts_df = ts_df.dropna(subset=[timestamp_col]).set_index(timestamp_col)
    
    # If no columns specified, count occurrences (e.g. number of entries per day)
    if columns is None:
        return ts_df.resample(rule).size().to_frame(name='count')
    
    # Otherwise aggregate specified columns
    # We default to mean for general numerics, but caller might want sum?
    # Let's assume Mean for now as safe default for "trends". 
    # For pure counts, user should pass specific logic.
    return ts_df[columns].resample(rule).mean()

def check_stationarity(series: pd.Series):
    """
    Performs Augmented Dickey-Fuller (ADF) test to check for stationarity.
    Returns True if stationary (p < 0.05).
    """
    clean_series = series.dropna()
    print(f"Performing ADF Test on {series.name}...")
    
    try:
        result = adfuller(clean_series, autolag='AIC')
        print(f'ADF Statistic: {result[0]}')
        print(f'p-value: {result[1]}')
        
        if result[1] <= 0.05:
            print("Strong evidence against the null hypothesis -> Stationary")
            return True
        else:
            print("Weak evidence against the null hypothesis -> Non-Stationary")
            return False
            
    except Exception as e:
        print(f"ADF Test Failed: {e}")
        return False

def decompose_series(series: pd.Series, model: str = 'additive', period: int = None):
    """
    Decomposes a time series into Trend, Seasonality, and Residuals.
    
    Args:
        series (pd.Series): Time series data (index must be datetime).
        model (str): 'additive' or 'multiplicative'.
        period (int): Periodicity (e.g. 7 for weekly, 30 for monthly). 
                      If None, statsmodels tries to guess or use index freq.
    """
    clean_series = series.dropna()
    
    # Handle missing dates by filling or ensuring freq? 
    # seasonal_decompose essentially requires a dense index or specified period.
    
    try:
        decomposition = seasonal_decompose(clean_series, model=model, period=period)
        
        fig = decomposition.plot()
        fig.set_size_inches(12, 8)
        plt.show()
        
        return decomposition
    except Exception as e:
        print(f"Decomposition failed: {e}. Try defining a specific period or handling gaps.")
        return None
