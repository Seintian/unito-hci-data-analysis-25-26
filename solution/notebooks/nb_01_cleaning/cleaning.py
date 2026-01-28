import pandas as pd
import numpy as np
from typing import Optional, Set, Dict, Tuple, List
from .utils import clean_string_columns, enforce_referential_integrity

def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names to a common schema.
    Returns the dataframe with renamed columns.
    """
    # Mapping of source column names to target standardized names
    renames = {
        'mal_id': 'anime_id',
        'anime_mal_id': 'anime_id',
        'character_mal_id': 'character_id',
        'person_mal_id': 'person_id'
    }
    
    # Only rename columns that exist in the dataframe
    # Check intersection of keys to avoid unnecessary processing
    cols_to_rename = {k: v for k, v in renames.items() if k in df.columns and v not in df.columns}
    
    if cols_to_rename:
        df = df.rename(columns=cols_to_rename)
        
    return df

def _standardize_dataset(df: pd.DataFrame, primary_key: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Performs standard cleaning operations: column renaming, string cleaning, and deduplication.
    
    Args:
        df: Input DataFrame.
        primary_key: The column name to use for deduplication (optional).
        
    Returns:
        Tuple containing the cleaned DataFrame and a dictionary of metrics.
    """
    initial_rows = len(df)
    metrics = {}
    
    # 1. Standardize Column Names
    df = _rename_columns(df)
    
    # 2. String Cleaning
    df = clean_string_columns(df)
    
    # 3. Deduplication
    if primary_key and primary_key in df.columns:
        df = df.drop_duplicates(subset=[primary_key])
    else:
        df = df.drop_duplicates()
        
    metrics['duplicates_dropped'] = initial_rows - len(df)
    
    return df, metrics

def clean_characters_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the characters DataFrame by removing entries with missing IDs and
    formatting the data.
    """
    initial_rows = len(df)
    
    # Standardize and Deduplicate
    df, metrics = _standardize_dataset(df, primary_key='character_id')
    rows_after_dedup = len(df)
    
    missing_favs = df['favorites'].isna().sum() if 'favorites' in df.columns else 0

    # Ensure valid Identity
    if 'character_id' in df.columns:
        df = df.dropna(subset=['character_id'])
    
    # Remove irrelevant columns
    dropped_cols = []
    if 'about' in df.columns:
        df = df.drop(columns=['about'])
        dropped_cols.append('about')

    # logging.info(f"--- Characters Cleaning Report ---")
    print(f"--- Characters Cleaning Report ---")
    print(f"Initial Rows: {initial_rows}")
    print(f"Rows Dropped (Duplicates): {metrics['duplicates_dropped']}")
    print(f"Rows Dropped (Missing ID): {rows_after_dedup - len(df)}")
    print(f"Favorites Imputed (NaN -> 0): {missing_favs}")
    print(f"Columns Dropped: {dropped_cols}")
    print(f"Final Shape: {df.shape}")
    
    return df

def clean_details_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans anime details data, including date parsing and imputation of missing years.
    """
    initial_rows = len(df)

    # Standardize and Deduplicate
    df, metrics = _standardize_dataset(df, primary_key='anime_id')
    rows_after_dedup = len(df)
    
    # Verify Title existence
    if 'title' in df.columns:
        df = df.dropna(subset=['title'])
    rows_after_title = len(df)

    # Date Parsing
    for col in ['start_date', 'end_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Year Imputation
    missing_year_before = df['year'].isna().sum() if 'year' in df.columns else 0
    if 'year' in df.columns and 'start_date' in df.columns:
        df['year'] = df['year'].fillna(df['start_date'].dt.year)
    missing_year_after = df['year'].isna().sum() if 'year' in df.columns else 0

    print(f"--- Details Cleaning Report ---")
    print(f"Initial Rows: {initial_rows}")
    print(f"Rows Dropped (Duplicates): {metrics['duplicates_dropped']}")
    print(f"Rows Dropped (Missing Title): {rows_after_dedup - rows_after_title}")
    print(f"Year Imputed from Start Date: {missing_year_before - missing_year_after}")
    print(f"Remaining Missing Years: {missing_year_after}")
    print(f"Final Shape: {df.shape}")
    
    # Type Optimization for Categorical Features
    cat_cols = ['type', 'status', 'source', 'rating', 'season']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')
            
    return df

def clean_stats_logic(df: pd.DataFrame, valid_anime_ids: Optional[Set] = None) -> pd.DataFrame:
    """
    Cleans statistics data and enforces referential integrity with the main anime dataset.
    """
    initial_rows = len(df)
    
    # Standardize and Deduplicate
    df, metrics = _standardize_dataset(df, primary_key='anime_id')
    
    rows_after_dedup = len(df)
    rows_dropped_orphans = 0

    # Referential Integrity Check
    if valid_anime_ids is not None and 'anime_id' in df.columns:
        df, rows_dropped_orphans = enforce_referential_integrity(df, 'anime_id', valid_anime_ids)

    # Score integrity check
    score_cols = df.filter(like='score_').columns
    nan_in_scores = df[score_cols].isna().sum().sum()

    print(f"--- Stats Cleaning Report ---")
    print(f"Initial Rows: {initial_rows}")
    print(f"Rows Dropped (Duplicates): {metrics['duplicates_dropped']}")
    print(f"Rows Dropped (Orphans): {rows_dropped_orphans}")
    print(f"Total NaN values filled in score columns: {nan_in_scores}")
    print(f"Final Shape: {df.shape}")
    
    return df

def clean_ratings_chunk_logic(chunk: pd.DataFrame, valid_anime_ids: Optional[Set] = None) -> Tuple[pd.DataFrame, dict]:
    """
    Processes a partition of the ratings dataset.
    
    Returns:
        A tuple containing the processed DataFrame chunk and a metrics dictionary.
    """
    metrics = {
        'rows_read': len(chunk),
        'dropped_username': 0,
        'rewatch_imputed': 0,
        'dropped_orphans': 0
    }

    # 1. Referential Integrity
    if valid_anime_ids is not None:
        # Check for orphans but DO NOT drop them
        # chunk, dropped = enforce_referential_integrity(chunk, 'anime_id', valid_anime_ids)
        if 'anime_id' in chunk.columns:
            orphan_mask = ~chunk['anime_id'].isin(valid_anime_ids)
            metrics['dropped_orphans'] = orphan_mask.sum()
            # chunk = chunk[~orphan_mask] # previously dropped

    # 2. Drop entries with valid Username
    if 'username' in chunk.columns:
        missing_user_mask = chunk['username'].isna()
        metrics['dropped_username'] = missing_user_mask.sum()
        # chunk = chunk.dropna(subset=['username']) # previously dropped

    # 3. Score Validation
    if 'score' in chunk.columns:
        chunk = chunk[(chunk['score'] >= 0) & (chunk['score'] <= 10)]

    # 4. Impute Rewatch Status
    if 'is_rewatching' in chunk.columns:
        missing_rewatch_mask = chunk['is_rewatching'].isna()
        metrics['rewatch_imputed'] = missing_rewatch_mask.sum()

    # 5. String Cleaning
    chunk = clean_string_columns(chunk)

    # 6. Type Optimization
    # Use appropriate numpy types for memory efficiency
    dtype_map = {
        'anime_id': np.int32,
        'score': np.int8,
        'num_watched_episodes': np.int32,
        'status': 'category'
    }
    # Only apply map to existing columns
    final_dtype_map = {k: v for k, v in dtype_map.items() if k in chunk.columns}
    chunk = chunk.astype(final_dtype_map)

    return chunk, metrics

def clean_generic_file_logic(df: pd.DataFrame, filename: str, valid_ids_map: Optional[Dict] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Applies generic cleaning logic suitable for various auxiliary datasets.
    
    Returns:
        Tuple of (cleaned_df, actions_log).
    """
    actions = []
    initial_rows = len(df)
    
    # Standardize (Renaming + Strings + Deduplication)
    # Note: We don't assume a primary key for generic files blindly, so use default deduplication
    df, metrics = _standardize_dataset(df)
    
    if metrics['duplicates_dropped'] > 0:
        actions.append(f"Deduplicated ({metrics['duplicates_dropped']} rows)")
    
    # Update renames log based on actual columns
    # (Implicitly handled by _standardize_dataset, but we reconstruct log for reporting if needed)
    # For exam presentation, detailed rename logs might be excessive, keeping it high level.

    # Referential Integrity
    if valid_ids_map:
        for col, valid_ids in valid_ids_map.items():
            if col in df.columns and valid_ids is not None:
                 df, dropped = enforce_referential_integrity(df, col, valid_ids)
                 if dropped > 0:
                     actions.append(f"Dropped Orphans on {col} ({dropped} rows)")

    # Specific File Logic through filename matching
    if filename == "person_details.csv":
        if 'birthday' in df.columns:
            df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce')
            actions.append("Date Parsing (birthday)")

    if filename == "profiles.csv":
        for date_col in ['joined']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                actions.append(f"Date Parsing ({date_col})")
                
    return df, actions
