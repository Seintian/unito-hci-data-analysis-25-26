import pandas as pd
from typing import Tuple, Dict, Any
from solution.src.data import load_raw
from solution.src.common import PROCESSED_DATA_DIR
from solution.src.utils import save_refined
from .cleaning import standardize_column_names_and_text, merge_content_duplicates
from .optimizations import get_memory_usage_mb, reduce_memory_usage


def process_ratings_batch(chunk: pd.DataFrame, valid_anime_ids: set, id_map_anime: dict) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Processes a batch of ratings: REMAPS foreign keys, REMOVES orphans, and REDUCES memory.
    """

    # Defensive copy for joblib safety
    chunk = chunk.copy()

    metrics = {
        'rows_read': len(chunk),
        'dropped_orphans': 0,
        'fk_remapped': 0,
        'fk_samples': []
    }

    # 1. Consistent IDs (Remapping)
    if id_map_anime:
        _apply_id_remapping(chunk, 'anime_id', id_map_anime, metrics)

    # 2. Referential Integrity (Drop Orphans)
    initial_len = len(chunk)
    chunk = chunk[chunk['anime_id'].isin(valid_anime_ids)]
    metrics['dropped_orphans'] += (initial_len - len(chunk))

    # 3. Optimization
    chunk = reduce_memory_usage(chunk, verbose=False)

    return chunk, metrics

def clean_and_optimize_dataset(dataset_name: str, file_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Full pipeline for a generic dataset: Load -> Clean -> Optimize -> Save.
    """

    df = load_raw(dataset_name)

    initial_stats = {
        'rows': len(df),
        'mem': get_memory_usage_mb(df)
    }

    actions_taken = []

    # Standardize
    df, clean_metrics = standardize_column_names_and_text(df)
    if clean_metrics.get('duplicates_dropped', 0) > 0:
        actions_taken.append(f"Removed {clean_metrics['duplicates_dropped']} duplicates")

    # Drop empty rows
    df.dropna(how='all', inplace=True)

    # Type-specific parsing
    if _parse_date_if_exists(df, 'birthday'): actions_taken.append("Parsed birthdays")
    if _parse_date_if_exists(df, 'joined'): actions_taken.append("Parsed join dates")

    cleaned_mem = get_memory_usage_mb(df)

    # Optimize
    df = reduce_memory_usage(df, verbose=False)

    # Save
    if dataset_name in file_map:
        save_refined(df, PROCESSED_DATA_DIR / file_map[dataset_name], format='parquet')

    return {
        'file': dataset_name,
        'rows_src': initial_stats['rows'],
        'rows_dst': len(df),
        'mem_src': initial_stats['mem'],
        'mem_cleaned': cleaned_mem,
        'mem_dst': get_memory_usage_mb(df),
        'actions': actions_taken
    }

def clean_characters_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Pipeline for characters.csv"""

    initial_rows = len(df)

    # 1. Standardize
    df, std_metrics = standardize_column_names_and_text(df)

    # 2. Merge Content Duplicates
    df, dup_metrics = merge_content_duplicates(df, primary_key='character_id')

    # 3. Specific Cleaning: Drop 'about'
    if 'about' in df.columns:
        df = df.drop(columns=['about'])

    # 4. Drop empty rows (but not just missing IDs if we want to keep them? Notebook said: "Drop empty rows but NOT just missing IDs... dropna(how='all')")
    df.dropna(how='all', inplace=True)

    report = {
        "Initial Rows": initial_rows,
        "Standardization": std_metrics,
        "Content Resolution": dup_metrics,
        "Final Rows": len(df)
    }

    return df, dup_metrics['id_map'], report

def clean_anime_details_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Pipeline for details.csv"""

    initial_rows = len(df)

    # 1. Standardize
    df, std_metrics = standardize_column_names_and_text(df)

    # 2. Merge Duplicates
    df, dup_metrics = merge_content_duplicates(df, primary_key='anime_id')

    df.dropna(how='all', inplace=True)

    # 3. Feature Engineering / Imputation
    # Parse dates
    for col in ['start_date', 'end_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Impute Year
    imputed_count = 0
    if 'year' in df.columns and 'start_date' in df.columns:
        missing_before = df['year'].isna().sum()
        df['year'] = df['year'].fillna(df['start_date'].dt.year)
        imputed_count = missing_before - df['year'].isna().sum()

    # Convert Categoricals (Explicit list from notebook)
    cat_cols = ['type', 'status', 'source', 'rating', 'season']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')

    report = {
        "Initial Rows": initial_rows,
        "Standardization": std_metrics,
        "Content Resolution": dup_metrics,
        "Final Rows": len(df),
        "Year Imputed": imputed_count
    }

    return df, dup_metrics['id_map'], report

def clean_anime_stats_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Pipeline for stats.csv"""

    initial_rows = len(df)

    # 1. Standardize
    df, std_metrics = standardize_column_names_and_text(df)

    # 2. Merge Duplicates
    df, dup_metrics = merge_content_duplicates(df, primary_key='anime_id')

    df.dropna(how='all', inplace=True)

    report = {
        "Initial Rows": initial_rows,
        "Standardization": std_metrics,
        "Content Resolution": dup_metrics,
        "Final Rows": len(df)
    }

    return df, dup_metrics['id_map'], report

def count_total_rows_in_file(file_path: str) -> int:
    """
    Efficiently counts the number of lines in a file.
    """

    with open(file_path, 'rb') as f:
        lines = 0
        buf_size = 1024 * 1024 * 12 # 12MB buffer

        read_chunk = f.read
        chunk = read_chunk(buf_size)

        while chunk:
            lines += chunk.count(b'\n')
            chunk = read_chunk(buf_size)

    return lines


# --- Helpers ---

def _apply_id_remapping(df: pd.DataFrame, col: str, mapping: dict, metrics: dict):
    mask = df[col].isin(mapping.keys())
    if mask.any():
        # Capture sample for reporting
        sample_mask = mask & df[col].notna()
        if sample_mask.any():
            old = df.loc[sample_mask, col].head(1)
            new = old.map(mapping)
            metrics['fk_samples'].append(dict(zip(old, new)))

        df.loc[mask, col] = df.loc[mask, col].map(mapping)
        metrics['fk_remapped'] += int(mask.sum())

def _parse_date_if_exists(df: pd.DataFrame, col: str) -> bool:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        return True

    return False
