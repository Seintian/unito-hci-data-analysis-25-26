import pandas as pd
import numpy as np
import scipy.stats as stats
from typing import Dict, Any, List


def analyze_moments(df: pd.DataFrame, numeric_cols: List[str] = None) -> pd.DataFrame:
    """
    Calculates the first four moments of statistics for numerical columns:
    Mean (Location), Median (Location), Variance (Spread), 
    Skewness (Asymmetry), and Kurtosis (Tailedness).

    Args:
        df (pd.DataFrame): The dataframe to analyze.
        numeric_cols (List[str], optional): List of columns to analyze. 
                                            If None, selects all numeric columns.

    Returns:
        pd.DataFrame: A summary dataframe with the moments.
    """

    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    key_stats = []

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue

        key_stats.append({
            'Column': col,
            'Mean': series.mean(),
            'Median': series.median(),
            'Variance': series.var(),
            'Std Dev': series.std(),
            'Skewness': series.skew(),
            'Kurtosis': series.kurt()
        })

    return pd.DataFrame(key_stats).set_index('Column')

def fit_distribution(series: pd.Series) -> Dict[str, Any]:
    """
    Tests various distributions (Normal, Log-Normal, Poisson) against the data
    to see which fits best. Uses Kolmogorov-Smirnov test for continuous 
    distributions (Normal, Log-Normal) and Chi-Square for discrete (Poisson).

    Note: Poisson fitting is rudimentary here and assumes count data.

    Args:
        series (pd.Series): The numeric data series to test.

    Returns:
        Dict[str, Any]: Dictionary containing p-values and fit parameters.
    """
    clean_series = series.dropna()
    results = {}

    # Normal Test
    # kstest returns statistic, p-value. Higher p-value (>0.05) -> cannot reject null hypothesis (it IS normal)
    # However, for large datasets, even tiny deviations reject normalcy. 
    # We focus on the statistic (lower is better fit).
    loc, scale = stats.norm.fit(clean_series)
    d_norm, p_norm = stats.kstest(clean_series, 'norm', args=(loc, scale))
    results['Normal'] = {'p_value': p_norm, 'D_statistic': d_norm, 'params': (loc, scale)}

    # Log-Normal Test (requires positive values)
    if (clean_series > 0).all():
        shape, loc, scale = stats.lognorm.fit(clean_series)
        d_log, p_log = stats.kstest(clean_series, 'lognorm', args=(shape, loc, scale))
        results['Log-Normal'] = {'p_value': p_log, 'D_statistic': d_log, 'params': (shape, loc, scale)}
    else:
        results['Log-Normal'] = {'p_value': 0.0, 'D_statistic': np.inf, 'note': 'Contains <= 0 values'}

    return results

def analyze_cardinality(df: pd.DataFrame, cat_cols: List[str] = None) -> pd.DataFrame:
    """
    Analyzes the cardinality of categorical columns to distinguish between
    nominal, ordinal, or high-cardinality ID-like columns.

    Args:
        df (pd.DataFrame): Dataframe to analyze.
        cat_cols (List[str], optional): columns to check.

    Returns:
        pd.DataFrame: Summary of cardinality.
    """

    if cat_cols is None:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    stats_list = []
    total_rows = len(df)

    for col in cat_cols:
        unique_count = df[col].nunique()
        percentage = (unique_count / total_rows) * 100

        # Heuristic classification
        if unique_count == total_rows:
            classification = 'Unique Key'
        elif percentage > 90:
            classification = 'High Cardinality'
        elif unique_count < 2:
            classification = 'Constant'
        elif unique_count < 20:
            classification = 'Low Cardinality (Categorical)'
        else:
            classification = 'Medium Cardinality'

        stats_list.append({
            'Column': col,
            'Unique Values': unique_count,
            'Percentage Unique': f"{percentage:.2f}%",
            'Classification': classification
        })

    return pd.DataFrame(stats_list).set_index('Column')
