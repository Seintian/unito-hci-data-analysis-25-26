import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import scipy.stats as stats
from sklearn.impute import SimpleImputer


def detect_isolation_forest(df: pd.DataFrame, numeric_cols: list = None, contamination: float = 0.01) -> pd.DataFrame:
    """
    Uses Isolation Forest to identify global anomalies in high-dimensional space.

    Args:
        df (pd.DataFrame): Input dataframe.
        numeric_cols (list): Columns to use for detection.
        contamination (float): Expected proportion of outliers (default 1%).

    Returns:
        pd.DataFrame: DataFrame containing only the identified anomalies.
    """

    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    X = df[numeric_cols].values

    # Handle NaNs
    imputer = SimpleImputer(strategy='median')
    X_imputed = imputer.fit_transform(X)

    # Scaling isn't strictly necessary for tree-based IF, but good practice if magnitude differs wildly

    iso_forest = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    # -1 for outliers, 1 for inliers
    preds = iso_forest.fit_predict(X_imputed)

    # Filter original DF
    anomalies = df[preds == -1].copy()
    anomalies['anomaly_score'] = iso_forest.decision_function(X_imputed)[preds == -1]

    print(f"Isolation Forest detected {len(anomalies)} anomalies in {len(df)} records.")

    return anomalies

def identify_outliers_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.DataFrame:
    """
    Identifies outliers using the Z-Score method (Global Univariate Outliers).
    Moved from exploration.py.
    """

    df_clean = df.dropna(subset=[column]).copy()
    df_clean['zscore'] = stats.zscore(df_clean[column])

    outliers = df_clean[np.abs(df_clean['zscore']) > threshold]
    print(f"Z-Score Outliers for '{column}': found {len(outliers)} (Threshold: {threshold} sigma)")

    return outliers

def identify_outliers_iqr(df: pd.DataFrame, column: str, factor: float = 1.5):
    """
    Identifies outliers using the IQR method (Robust Univariate Outliers).
    Moved from exploration.py.
    """

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR

    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    print(f"IQR Outliers for '{column}': found {len(outliers)} (Bounds: {lower_bound:.2f}, {upper_bound:.2f})")

    return outliers, lower_bound, upper_bound
