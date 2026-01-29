import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names to a common schema.
    Returns the dataframe with renamed columns.
    """

    renames = {
        'mal_id': 'anime_id',
        'anime_mal_id': 'anime_id',
        'character_mal_id': 'character_id',
        'person_mal_id': 'person_id'
    }

    cols_to_rename = {k: v for k, v in renames.items() if k in df.columns and v not in df.columns}
    if cols_to_rename:
        df = df.rename(columns=cols_to_rename)

    return df

def standardize_dataset(df: pd.DataFrame, primary_key: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Performs standard cleaning operations: column renaming, string cleaning, and deduplication.

    Returns:
        Tuple containing the cleaned DataFrame and a dictionary of metrics.
    """

    initial_rows = len(df)
    metrics = {}

    # 1. Standardize Column Names
    df = rename_columns(df)

    # 2. String Cleaning
    df = clean_string_columns(df)

    # 3. Deduplication
    if primary_key and primary_key in df.columns:
        df = df.drop_duplicates(subset=[primary_key])
    else:
        df = df.drop_duplicates()

    metrics['duplicates_dropped'] = initial_rows - len(df)

    return df, metrics

def get_memory_usage_mb(df: pd.DataFrame) -> float:
    """
    Calculates the memory usage of the DataFrame in Megabytes (MB).

    Args:
        df: The pandas DataFrame to inspect.
        
    Returns:
        float: Memory usage in MB.
    """

    return df.memory_usage(deep=True).sum() / 1024 ** 2

def optimize_dtypes(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Optimizes the DataFrame's memory usage by downcasting numeric types and 
    converting object types to categorical where appropriate.

    Args:
        df: Input DataFrame.
        verbose: If True, prints memory reduction statistics.

    Returns:
        pd.DataFrame: Optimized DataFrame.
    """

    start_mem = get_memory_usage_mb(df)

    for col in df.columns:
        col_type = df[col].dtype

        if pd.api.types.is_integer_dtype(col_type):
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif pd.api.types.is_float_dtype(col_type):
            df[col] = pd.to_numeric(df[col], downcast='float')

        # Categorical Conversion Heuristic
        elif pd.api.types.is_object_dtype(col_type):
            num_unique = len(df[col].unique())
            num_total = len(df)
            if num_total > 100 and (num_unique / num_total < 0.5):
                df[col] = df[col].astype('category')

    end_mem = get_memory_usage_mb(df)
    if verbose:
        reduction = 100 * (start_mem - end_mem) / start_mem
        print(f"Memory optimization: {start_mem:.2f} MB -> {end_mem:.2f} MB ({reduction:.1f}% reduction)")

    return df

def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trims leading/trailing whitespace from string columns.
    Safe for mixed types and NaN values.
    """

    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            if isinstance(df[col].dtype, pd.CategoricalDtype):
                continue

            try:
                df[col] = df[col].str.strip()
            except AttributeError:
                pass

    return df

def enforce_referential_integrity(df: pd.DataFrame, col_name: str, valid_ids: set) -> tuple[pd.DataFrame, int]:
    """
    Filters the DataFrame to ensure all values in `col_name` exist within `valid_ids`.

    Args:
        df: Input DataFrame.
        col_name: The foreign key column to validate.
        valid_ids: A set of valid primary keys.

    Returns:
        tuple: (Filtered DataFrame, number of rows dropped).
    """

    if col_name not in df.columns:
        return df, 0

    initial_rows = len(df)

    # Filter rows where the foreign key is present in the valid check list
    df = df[df[col_name].isin(valid_ids)]

    dropped = initial_rows - len(df)
    return df, dropped
