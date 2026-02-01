import pandas as pd
import numpy as np


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
    diff_sq = (scores - weighted_mean[:, None]) ** 2
    weighted_sq_diff = np.sum(weights * diff_sq, axis=1)

    weighted_var = np.zeros_like(total_votes, dtype=float)
    weighted_var[mask] = weighted_sq_diff[mask] / total_votes[mask]

    df_stats['controversy_std'] = np.sqrt(weighted_var)

    return df_stats
