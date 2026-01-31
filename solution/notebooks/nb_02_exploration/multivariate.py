import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import warnings

# Suppress pkg_resources deprecation warning from ppscore
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module='pkg_resources')
    import ppscore as pps


def calculate_correlation(df: pd.DataFrame, method: str = 'spearman') -> pd.DataFrame:
    """
    Calculates the correlation matrix.

    Args:
        df (pd.DataFrame): Input dataframe.
        method (str): 'pearson' (linear) or 'spearman' (monotonic).

    Returns:
        pd.DataFrame: The correlation matrix.
    """

    # Select only numeric columns for standard correlation
    numeric_df = df.select_dtypes(include=[np.number])
    return numeric_df.corr(method=method)

def calculate_pps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the Predictive Power Score (PPS) matrix.
    Detects non-linear asymmetric relationships.

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        pd.DataFrame: The PPS matrix.
    """

    # PPS handles both numeric and categorical, but can be slow on large data.
    # We recommend sampling if df > 100k rows
    if len(df) > 100000:
        print("Dataset > 100k rows. Sampling 10k for PPS calculation to save time.")
        data_sample = df.sample(10000)
    else:
        data_sample = df

    # Suppress sklearn UserWarning about low class counts for n_splits
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.model_selection")
        pps_matrix = pps.matrix(data_sample)[['x', 'y', 'ppscore']].pivot(columns='x', index='y', values='ppscore')
    return pps_matrix

def plot_hexbin_density(df: pd.DataFrame, x: str, y: str, gridsize: int = 30, title: str = None):
    """
    Plots a Hexbin plot for dense 2D data (to avoid overplotting of scatter).

    Args:
        df (pd.DataFrame): Dataframe.
        x (str): Column for x-axis.
        y (str): Column for y-axis.
        gridsize (int): Resolution of the hex grid.
    """

    plt.figure(figsize=(10, 8))

    valid_data = df[[x, y]].dropna()

    plt.hexbin(valid_data[x], valid_data[y], gridsize=gridsize, cmap='inferno', mincnt=1)
    plt.colorbar(label='Count')

    plt.title(title or f"Hexbin Density Plot: {x} vs {y}")
    plt.xlabel(x)
    plt.ylabel(y)
    plt.show()

def plot_pps_heatmap(pps_df: pd.DataFrame):
    """
    Plots the heatmap for the PPS matrix.
    """

    plt.figure(figsize=(12, 10))
    sns.heatmap(pps_df, vmin=0, vmax=1, cmap="Blues", linewidths=0.5, annot=True, fmt=".2f")
    plt.title("Predictive Power Score Matrix")
    plt.show()
