import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def setup_style():
    """Sets up the seaborn style."""
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 12

def plot_distribution(df: pd.DataFrame, column: str, log_scale: bool = False, title: str = None, kde: bool = True):
    """
    Plots the distribution of a variable.
    """
    plt.figure(figsize=(12, 6))
    
    # Filter out NaNs to prevent RuntimeWarning in nanops (kde calculation)
    valid_data = df.dropna(subset=[column])
    
    if log_scale:
        # For log scale, we handle 0 values? sns.histplot handles log_scale arg natively now
        sns.histplot(data=valid_data, x=column, kde=kde, log_scale=log_scale, stat="density")
        scale_label = " (Log Scale)"
    else:
        sns.histplot(data=valid_data, x=column, kde=kde, stat="density")
        scale_label = ""
        
    plt.title(title or f"Distribution of {column}{scale_label}")
    plt.xlabel(column)
    plt.ylabel("Density")
    plt.show()

def plot_correlation_matrix(df: pd.DataFrame, columns: list = None):
    """
    Plots a heatmap of correlations.
    """
    plt.figure(figsize=(10, 8))
    
    if columns:
        corr_df = df[columns]
    else:
        corr_df = df.select_dtypes(include=[np.number])
        
    corr = corr_df.corr(method='pearson') # Standard Pearson
    
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1)
    plt.title("Correlation Matrix")
    plt.show()

def plot_categorical_comparison(df: pd.DataFrame, cat_col: str, num_col: str, top_n: int = 10):
    """
    Boxplot comparison of numeric vs categorical.
    """
    plt.figure(figsize=(14, 7))
    
    # If too many categories, take top N by count
    counts = df[cat_col].value_counts()
    if len(counts) > top_n:
        top_cats = counts.head(top_n).index
        data_to_plot = df[df[cat_col].isin(top_cats)]
        title_suffix = f" (Top {top_n} Categories)"
    else:
        data_to_plot = df
        title_suffix = ""
        
    order = data_to_plot.groupby(cat_col, observed=True)[num_col].median().sort_values(ascending=False).index
    
    sns.boxplot(x=cat_col, y=num_col, data=data_to_plot, order=order)
    plt.title(f"{num_col} by {cat_col}{title_suffix}")
    plt.xticks(rotation=45, ha='right')
    plt.show()
