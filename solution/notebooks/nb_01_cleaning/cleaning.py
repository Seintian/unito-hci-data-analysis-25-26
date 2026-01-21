import pandas as pd
import numpy as np
from typing import Optional, Set, Dict, Tuple, List
from .utils import clean_string_columns, enforce_referential_integrity

def clean_characters_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans characters DataFrame: drops missing IDs, fills favorites, drops 'about'.
    Prints a report of actions.
    """
    initial_rows = len(df)
    
    # Rename ID for consistency
    if 'character_mal_id' in df.columns:
        df = df.rename(columns={'character_mal_id': 'character_id'})

    missing_ids = df['character_id'].isna().sum()
    missing_favs = df['favorites'].isna().sum()

    # 1. Drop missing IDs
    df = df.dropna(subset=['character_id'])
    rows_after_drop_id = len(df)
    
    # 1.1 Drop duplicates (Keep first)
    df = df.drop_duplicates(subset=['character_id'])
    rows_after_dedup = len(df)

    # 1.2 Drop if 'name' is missing (Key field logic)
    if 'name' in df.columns:
        df = df.dropna(subset=['name'])
    rows_after_name = len(df)
    
    # 1.3 String Cleaning
    df = clean_string_columns(df)

    # 2. Fill favorites
    df['favorites'] = df['favorites'].fillna(0)

    # 3. Drop 'about'
    dropped_cols = []
    if 'about' in df.columns:
        df = df.drop(columns=['about'])
        dropped_cols.append('about')

    # Report
    print(f"--- Characters Cleaning Report ---")
    print(f"Initial Rows: {initial_rows}")
    print(f"Rows Dropped (Missing ID): {initial_rows - rows_after_drop_id}")
    print(f"Rows Dropped (Duplicates): {rows_after_drop_id - rows_after_dedup}")
    print(f"Rows Dropped (Missing Name): {rows_after_dedup - rows_after_name}")
    print(f"Favorites Imputed (NaN -> 0): {missing_favs}")
    print(f"Columns Dropped: {dropped_cols}")
    print(f"Final Shape: {df.shape}")
    
    return df

def clean_details_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans details: Date parsing, Year imputation.
    Prints a report.
    """
    initial_rows = len(df)

    # Rename ID for consistency
    if 'mal_id' in df.columns:
        df = df.rename(columns={'mal_id': 'anime_id'})

    # 0.1 Deduplicate
    if 'anime_id' in df.columns:
        df = df.drop_duplicates(subset=['anime_id'])
    rows_after_dedup = len(df)
    
    # 0.2 Check Title (Key Field)
    if 'title' in df.columns:
        df = df.dropna(subset=['title'])
    rows_after_title = len(df)

    # 0.3 String Cleaning
    df = clean_string_columns(df)

    # 0.4 Impute Text
    for text_col in ['synopsis', 'background']:
        if text_col in df.columns:
             df[text_col] = df[text_col].fillna("Unknown")

    # 1. Date Parsing
    df['start_date'] = pd.to_datetime(df['start_date'],  errors='coerce')
    df['end_date'] = pd.to_datetime(df['end_date'],  errors='coerce')

    # 2. Impute Year from Start Date
    missing_year_before = df['year'].isna().sum()
    df['year'] = df['year'].fillna(df['start_date'].dt.year) # type: ignore
    missing_year_after = df['year'].isna().sum()

    # Report
    print(f"--- Details Cleaning Report ---")
    print(f"Initial Rows: {initial_rows}")
    print(f"Rows Dropped (Duplicates): {initial_rows - rows_after_dedup}")
    print(f"Rows Dropped (Missing Title): {rows_after_dedup - rows_after_title}")
    print(f"Year Imputed from Start Date: {missing_year_before - missing_year_after}")
    print(f"Remaining Missing Years: {missing_year_after}")
    print(f"Final Shape: {df.shape}")
    
    # Explicitly convert known low-cardinality columns to category
    cat_cols = ['type', 'status', 'source', 'rating', 'season']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df.astype({col: 'category'})[col] # safer assignment
            
    return df

def clean_stats_logic(df: pd.DataFrame, valid_anime_ids: Optional[Set] = None) -> pd.DataFrame:
    """
    Cleans stats: Fills score columns with 0.
    Prints report.
    """
    initial_rows = len(df)
    
    # Rename ID for consistency
    if 'mal_id' in df.columns:
        df = df.rename(columns={'mal_id': 'anime_id'})

    # 0. Deduplicate
    if 'anime_id' in df.columns:
        df = df.drop_duplicates(subset=['anime_id'])
    
    rows_after_dedup = len(df)
    rows_dropped_orphans = 0

    # 0.5 Referential Integrity
    if valid_anime_ids is not None and 'anime_id' in df.columns:
        df, rows_dropped_orphans = enforce_referential_integrity(df, 'anime_id', valid_anime_ids)

    # Fill score columns with 0
    score_cols = df.filter(like='score_').columns
    nan_in_scores = df[score_cols].isna().sum().sum()
    df[score_cols] = df[score_cols].fillna(0)

    # Report
    print(f"--- Stats Cleaning Report ---")
    print(f"Initial Rows: {initial_rows}")
    print(f"Rows Dropped (Duplicates): {initial_rows - rows_after_dedup}")
    print(f"Rows Dropped (Orphans): {rows_dropped_orphans}")
    print(f"Total NaN values filled in score columns: {nan_in_scores}")
    print(f"Final Shape: {df.shape}")
    
    return df

def clean_ratings_chunk_logic(chunk: pd.DataFrame, valid_anime_ids: Optional[Set] = None) -> Tuple[pd.DataFrame, dict]:
    """
    Cleans a single chunk of ratings.
    Returns (cleaned_chunk, metrics_dict)
    """
    metrics = {
        'rows_read': len(chunk),
        'dropped_username': 0,
        'rewatch_imputed': 0,
        'dropped_orphans': 0
    }

    # 0. Referential Integrity
    if valid_anime_ids is not None:
        chunk, dropped = enforce_referential_integrity(chunk, 'anime_id', valid_anime_ids)
        metrics['dropped_orphans'] = dropped

    # 1. Drop missing username
    missing_user_mask = chunk['username'].isna()
    metrics['dropped_username'] = missing_user_mask.sum()
    
    chunk = chunk.dropna(subset=['username'])

    # 1.5. Score Sanity Check
    chunk = chunk[(chunk['score'] >= 0) & (chunk['score'] <= 10)]

    # 2. Fill rewatching
    missing_rewatch_mask = chunk['is_rewatching'].isna()
    metrics['rewatch_imputed'] = missing_rewatch_mask.sum()

    chunk['is_rewatching'] = chunk['is_rewatching'].fillna(0).astype(np.uint8)

    # 2.5 String Cleaning
    chunk = clean_string_columns(chunk)

    # 3. Optimize types strictly
    chunk = chunk.astype({
        'anime_id': np.int32,
        'score': np.int8,
        'num_watched_episodes': np.int32,
        'status': 'category'
    })

    return chunk, metrics

def clean_generic_file_logic(df: pd.DataFrame, filename: str, valid_ids_map: Optional[Dict] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Applies specific fixes for other files based on filename.
    Returns (df, list_of_actions)
    """
    actions = []
    initial_rows = len(df)
    
    # Rename IDs for consistency
    renames = {
        'mal_id': 'anime_id', # Default assumption if mal_id appears in anime related files, but risky? 
                              # Actually 'person_details' has 'person_mal_id'.
        'anime_mal_id': 'anime_id',
        'character_mal_id': 'character_id',
        'person_mal_id': 'person_id'
    }
    # Apply renames if columns exist
    for old, new in renames.items():
        if old in df.columns:
            if new not in df.columns: # Prevent collision if both exist (rare)
                df = df.rename(columns={old: new})
                actions.append(f"Renamed {old}->{new}")

    # 0. Deduplicate
    df = df.drop_duplicates()
    if len(df) < initial_rows:
        actions.append(f"Deduplicated ({initial_rows - len(df)} rows)")

    # 1. String Cleaning
    df = clean_string_columns(df)
    
    # 2. Referential Integrity
    if valid_ids_map:
        for col, valid_ids in valid_ids_map.items():
            if col in df.columns and valid_ids is not None:
                 df, dropped = enforce_referential_integrity(df, col, valid_ids)
                 if dropped > 0:
                     actions.append(f"Dropped Orphans on {col} ({dropped} rows)")

    if filename == "person_details.csv":
        df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce')
        actions.append("Date Parsing (birthday)")

    if filename == "profiles.csv":
        for date_col in ['joined']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                actions.append(f"Date Parsing ({date_col})")
                
    return df, actions
