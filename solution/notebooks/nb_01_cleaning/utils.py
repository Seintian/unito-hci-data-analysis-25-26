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

def resolve_content_duplicates(df: pd.DataFrame, primary_key: str) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    Identifies rows with identical content (excluding the primary key).
    Keeps the row with the 'best' primary key (e.g., non-null, or lowest numerical value).
    Returns:
        - Cleaned DataFrame
        - Dictionary of metrics (including the id_map for remapping foreign keys)
    """

    metrics = {
        'duplicates_found': 0,
        'duplicates_dropped': 0,
        'id_map': {}  # {dropped_id: kept_id}
    }

    if primary_key not in df.columns:
        print(f"Primary key '{primary_key}' not found, skipping content duplicate resolution.")
        return df, metrics

    # Columns to check for duplication (all except PK)
    cols_to_check = df.columns.drop(primary_key).tolist()

    # Identify duplicates
    # keep=False to get all rows involved in duplicated content
    dupes_mask = df.duplicated(subset=cols_to_check, keep=False)

    if not dupes_mask.any():
        return df, metrics

    metrics['duplicates_found'] = int(dupes_mask.sum())

    # Process duplicates to build the map
    dupes = df[dupes_mask].copy()

    # We group by the content columns
    grouped = dupes.groupby(cols_to_check, dropna=False)

    original_indices_to_drop = []

    for _, group in grouped:
        if len(group) < 2:
            continue

        # Strategy: Prefer non-null IDs, then lowest ID
        sorted_group = group.sort_values(by=primary_key, na_position='last')

        kept_row = sorted_group.iloc[0]
        kept_id = kept_row[primary_key]

        # All others are dropped
        dropped_rows = sorted_group.iloc[1:]
        original_indices_to_drop.extend(dropped_rows.index)

        for _, row in dropped_rows.iterrows():
            dropped_id = row[primary_key]

            # valid -> valid mapping only makes sense if both are valid
            if pd.notna(dropped_id) and pd.notna(kept_id):
                metrics['id_map'][dropped_id] = kept_id

    df_clean = df.drop(original_indices_to_drop)

    metrics['duplicates_dropped'] = len(original_indices_to_drop)

    return df_clean, metrics

def print_cleaning_report(step_name: str, metrics: Dict[str, any]):
    """
    Prints a formatted report of the cleaning step.
    """

    print(f"--- {step_name} Report ---")
    for key, value in metrics.items():
        if key == 'id_map':
            print(f"  ID Mappings Created: {len(value)}")
        elif isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
