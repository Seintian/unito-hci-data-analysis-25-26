import pandas as pd
from typing import Tuple, Dict, Any, Iterable
from solution.src.data import load_raw
from solution.src.common import PROCESSED_DATA_DIR
from solution.src.utils import save_refined
from .cleaning import standardize_column_names_and_text, merge_content_duplicates
from .optimizations import get_memory_usage_mb, reduce_memory_usage


def process_ratings_batch(chunk: pd.DataFrame, id_map_anime: dict) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Processes a batch of ratings: REMAPS foreign keys and REDUCES memory.
    Note: Orphans are KEPT (not dropped).
    """

    # Defensive copy for joblib safety
    chunk = chunk.copy()

    metrics = {
        'rows_read': len(chunk),
        'fk_remapped': 0,
        'fk_samples': []
    }

    # 1. Consistent IDs (Remapping)
    if id_map_anime:
        _apply_id_remapping(chunk, 'anime_id', id_map_anime, metrics)

    # 2. Optimization
    chunk = reduce_memory_usage(chunk, verbose=False)

    return chunk, metrics

def clean_and_optimize_dataset(dataset_name: str, file_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Full pipeline for a generic dataset: Load -> Clean -> Optimize -> Save.
    """

    raw_data = load_raw(dataset_name)

    # We need to accumulate stats differently depending on whether it's a stream or a single DF
    stats_accumulator = {
        'rows_src': 0,
        'rows_dst': 0,
        'mem_src': 0.0,
        'acc_mem_cleaned': 0.0,
        'mem_dst': 0.0,
        'actions': set()
    }

    def process_chunk(df: pd.DataFrame) -> pd.DataFrame:
        """Applies cleaning logic to a single chunk (or full DF)."""

        current_rows = len(df)
        current_mem = get_memory_usage_mb(df)

        stats_accumulator['rows_src'] += current_rows
        stats_accumulator['mem_src'] += current_mem

        # Standardize
        df, clean_metrics = standardize_column_names_and_text(df)
        if clean_metrics.get('duplicates_dropped', 0) > 0:
            stats_accumulator['actions'].add(f"Removed duplicates")

        # Drop empty rows
        df.dropna(how='all', inplace=True)

        # Type-specific parsing
        if _parse_date_if_exists(df, 'birthday'): stats_accumulator['actions'].add("Parsed birthdays")
        if _parse_date_if_exists(df, 'joined'): stats_accumulator['actions'].add("Parsed join dates")

        cleaned_mem = get_memory_usage_mb(df)
        stats_accumulator['acc_mem_cleaned'] += cleaned_mem

        # Optimize
        df = reduce_memory_usage(df, verbose=False)

        stats_accumulator['rows_dst'] += len(df)
        stats_accumulator['mem_dst'] += get_memory_usage_mb(df)

        return df

    if isinstance(raw_data, pd.DataFrame):
        # Single DataFrame Path
        final_df = process_chunk(raw_data)

        if dataset_name in file_map:
            save_refined(final_df, PROCESSED_DATA_DIR / file_map[dataset_name], format='parquet')

    else:
        # Streaming Path
        def result_generator():
            for chunk in raw_data:
                yield process_chunk(chunk)

        # Drive the generator by saving
        if dataset_name in file_map:
            save_refined(result_generator(), PROCESSED_DATA_DIR / file_map[dataset_name], format='parquet')

    return {
        'file': dataset_name,
        'rows_src': stats_accumulator['rows_src'],
        'rows_dst': stats_accumulator['rows_dst'],
        'mem_src': stats_accumulator['mem_src'],
        'mem_cleaned': stats_accumulator['acc_mem_cleaned'],
        'mem_dst': stats_accumulator['mem_dst'],
        'actions': list(stats_accumulator['actions'])
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
