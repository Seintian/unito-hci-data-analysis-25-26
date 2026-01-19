import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import scipy.stats as stats

# We assume sys.path is set up correctly by the notebook to import solution
from solution.src.common import PROCESSED_DATA_DIR

def load_data(filename: str) -> pd.DataFrame:
    """
    Loads a parquet file from the processed data directory using pyarrow.
    
    Args:
        filename (str): Name of the file (e.g., 'details.parquet' or 'details.csv'). 
                        If extension is .csv, it will try to find .parquet first.
    
    Returns:
        pd.DataFrame: Loaded dataframe.
    """
    # Auto-handle extension
    name = Path(filename).stem
    parquet_path = PROCESSED_DATA_DIR / f"{name}.parquet"
    
    if parquet_path.exists():
        print(f"Loading {parquet_path}...")
        return pd.read_parquet(parquet_path, engine='pyarrow')
    
    # Fallback or strict error? User said "exclusively from data/processed" and "optimized parquet".
    # We'll try to load whatever is there if parquet misses, but warn.
    fpath = PROCESSED_DATA_DIR / filename
    if fpath.exists():
        print(f"Loading {fpath} (warning: not parquet)...")
        return pd.read_csv(fpath) # Engine pyarrow for csv is also possible in newer pandas
        
    raise FileNotFoundError(f"Could not find {name}.parquet or {filename} in {PROCESSED_DATA_DIR}")

def calculate_controversy_metric(df_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the 'Controversy' metric based on the weighted standard deviation of votes.
    
    Args:
        df_stats (pd.DataFrame): Dataframe containing 'score_1_votes' ... 'score_10_votes'.
        
    Returns:
        pd.DataFrame: DataFrame with an added 'controversy_std' column.
    """
    print("Calculating controversy metric (weighted deviation)...")
    vote_cols = [f'score_{i}_votes' for i in range(1, 11)]
    scores = np.arange(1, 11)
    
    def weighted_std(row):
        weights = row[vote_cols].values
        if weights.sum() == 0:
            return 0.0
        
        # Mean is typically already in 'score' col, but let's recalculate to be precise with these weights
        average = np.average(scores, weights=weights)
        variance = np.average((scores - average)**2, weights=weights)
        return np.sqrt(variance)

    # Note: Vectorizing this is better for performance, but this is readable for now.
    # For large datasets, we might use numpy broadcasting.
    
    # Numpy vectorized approach for speed:
    weights = df_stats[vote_cols].fillna(0).values
    total_votes = weights.sum(axis=1)
    
    # Avoid division by zero
    mask = total_votes > 0
    
    # Weighted Mean
    weighted_sum = np.sum(weights * scores, axis=1)
    weighted_mean = np.zeros_like(total_votes, dtype=float)
    weighted_mean[mask] = weighted_sum[mask] / total_votes[mask]
    
    # Weighted Variance
    # (x - mu)**2
    # We need to broadcast weighted_mean to shape (N, 10)
    diff_sq = (scores - weighted_mean[:, None]) ** 2
    weighted_sq_diff = np.sum(weights * diff_sq, axis=1)
    
    weighted_var = np.zeros_like(total_votes, dtype=float)
    weighted_var[mask] = weighted_sq_diff[mask] / total_votes[mask]
    
    df_stats['controversy_std'] = np.sqrt(weighted_var)
    
    return df_stats

def identify_outliers_iqr(df: pd.DataFrame, column: str, factor: float = 1.5) -> Tuple[pd.DataFrame, float, float]:
    """
    Identifies outliers using the IQR method.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    print(f"IQR Outliers for '{column}': found {len(outliers)} (Bounds: {lower_bound:.2f}, {upper_bound:.2f})")
    
    return outliers, lower_bound, upper_bound

def identify_outliers_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.DataFrame:
    """
    Identifies outliers using the Z-Score method.
    """
    df_clean = df.dropna(subset=[column]).copy()
    df_clean['zscore'] = stats.zscore(df_clean[column])
    
    outliers = df_clean[np.abs(df_clean['zscore']) > threshold]
    print(f"Z-Score Outliers for '{column}': found {len(outliers)} (Threshold: {threshold} sigma)")
    
    return outliers
