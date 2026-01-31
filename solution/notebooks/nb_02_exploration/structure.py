import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import MiniBatchKMeans
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
from typing import Tuple


def perform_pca(df: pd.DataFrame, numeric_cols: list = None, n_components: int = 3) -> Tuple[pd.DataFrame, PCA]:
    """
    Performs Principal Component Analysis (PCA) to reduce dimensionality.
    automatically handles imputing NaNs and Standard Scaling.

    Args:
        df (pd.DataFrame): Input dataframe.
        numeric_cols (list): List of numeric columns to include.
        n_components (int): How many components to keep.

    Returns:
        Tuple[pd.DataFrame, PCA]: DataFrame with PCA components, and the PCA object.
    """

    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Preprocessing pipeline
    # scikit fix: Convert to float64 to handle nullable integers (Int64) and pd.NA -> np.nan conversion
    X = df[numeric_cols].astype(float).values

    # 1. Impute missing values (Mean strategy is simple/fast)
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)

    # 2. Scale features (StandardScaler is crucial for PCA)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    # 3. PCA
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(X_scaled)

    # Create result DF
    cols = [f'PC{i+1}' for i in range(n_components)]
    pca_df = pd.DataFrame(data=components, columns=cols, index=df.index)

    print(f"Explained Variance Ratio: {pca.explained_variance_ratio_}")
    print(f"Total Variance Explained: {sum(pca.explained_variance_ratio_):.2f}")

    return pca_df, pca

def perform_clustering(df: pd.DataFrame, numeric_cols: list = None, n_clusters: int = 5) -> Tuple[pd.DataFrame, MiniBatchKMeans]:
    """
    Performs K-Means clustering (MiniBatch implementation for large datasets).

    Args:
        df (pd.DataFrame): DataFrame with features (can be raw or PCA result).
        numeric_cols (list): Columns to cluster on. If None, uses all columns (assuming df is already numeric/PCA'd).
        n_clusters (int): Number of clusters to find.

    Returns:
        Tuple[pd.DataFrame, MiniBatchKMeans]: Original DF with 'Cluster' column, and the model.
    """

    if numeric_cols:
        X = df[numeric_cols].values
    else:
        # Assume whole DF is numeric features
        X = df.select_dtypes(include=[np.number]).values

    # Impute if needed (KMeans breaks on NaN)
    if np.isnan(X).any():
        imputer = SimpleImputer(strategy='mean')
        X = imputer.fit_transform(X)

    kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=2048)
    clusters = kmeans.fit_predict(X)

    result_df = df.copy()
    result_df['Cluster'] = clusters

    return result_df, kmeans

def plot_pca_3d(pca_df: pd.DataFrame, color_col: str = None, title: str = "PCA 3D Visualization"):
    """
    Plots the first 3 PCA components in 3D.
    """

    if pca_df.shape[1] < 3:
        print("Need at least 3 components for 3D plot")
        return

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Sample if too large to render fast
    if len(pca_df) > 5000:
        plot_data = pca_df.sample(5000)
        c_data = color_col.sample(5000) if color_col is not None else None
    else:
        plot_data = pca_df
        c_data = color_col

    sc = ax.scatter(plot_data['PC1'], plot_data['PC2'], plot_data['PC3'], 
                    c=c_data, cmap='viridis', s=10, alpha=0.6)

    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_zlabel('PC3')
    plt.title(title)
    if color_col is not None:
        plt.colorbar(sc, label='Cluster / Value')
    plt.show()
