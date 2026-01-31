import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Iterable, Union, Generator, cast, Any
from solution.src.data import load_raw
from solution.src.common import PROCESSED_DATA_DIR


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


def optimize_dtypes(df: Union[pd.DataFrame, Iterable[pd.DataFrame]], verbose: bool = True, check_intern_loss: bool = True) -> Union[pd.DataFrame, Generator[pd.DataFrame, None, None]]:
    """
    Optimizes the DataFrame's memory usage by downcasting numeric types and 
    converting object types to categorical where appropriate.

    Supports both single DataFrame and Iterable of DataFrames (chunks).

    Args:
        df: Input DataFrame or Iterable of DataFrames.
        verbose: If True, prints memory reduction statistics.
        check_intern_loss: If True, checks for increase in unique object creation (slow).

    Returns:
        pd.DataFrame or Generator[pd.DataFrame]: Optimized DataFrame(s).
    """

    # Helper function for single DF optimization
    def _optimize_single(d_in: pd.DataFrame, verbose: bool) -> pd.DataFrame:
        # Working on a copy to allow reversion
        d = d_in.copy()

        # Track memory and potential string interning status
        def get_col_metrics(df_obj):
            col_metrics = {}
            for col in df_obj.columns:
                mem = df_obj[col].memory_usage(deep=True)
                dtype = df_obj[col].dtype
                # Check for string interning / unique object count explicitly for object columns
                num_unique_objs = -1

                if check_intern_loss and pd.api.types.is_object_dtype(dtype):
                    # .map(id).nunique() counts how many unique python objects are referenced
                    # If this is significantly lower than len(df) or even num_unique_values 
                    # it means we have interning/reuse.
                    try:
                        num_unique_objs = df_obj[col].map(id).nunique()
                    except Exception:
                        pass

                col_metrics[col] = {
                    'mem': mem,
                    'dtype': dtype,
                    'unique_objs': num_unique_objs
                }
            return col_metrics

        # Only compute expensive metrics if verbose or we need to check interning
        if verbose or check_intern_loss:
            start_metrics = get_col_metrics(d_in)
            start_mem = sum(m['mem'] for m in start_metrics.values()) / 1024**2
        else:
            start_mem = get_memory_usage_mb(d_in)
            start_metrics = {}

        changes = []

        for col in d.columns:
            col_type = d[col].dtype
            new_type = None
            extra_info = ""

            if pd.api.types.is_integer_dtype(col_type):
                d[col] = pd.to_numeric(d[col], downcast='integer')
                new_type = d[col].dtype
            elif pd.api.types.is_float_dtype(col_type):
                d[col] = pd.to_numeric(d[col], downcast='float')

                # Attempt conversion to Nullable Integer (Int32/Int64)
                no_nans = d[col].dropna()
                if len(no_nans) > 0 and np.all(np.mod(no_nans, 1) == 0):
                    min_val, max_val = no_nans.min(), no_nans.max()
                    if min_val >= -2_147_483_648 and max_val <= 2_147_483_647:
                        d[col] = d[col].astype("Int32")
                    else:
                        d[col] = d[col].astype("Int64")

                new_type = d[col].dtype

            # Categorical Conversion Heuristic
            elif pd.api.types.is_object_dtype(col_type):
                num_unique = len(d[col].unique())
                num_total = len(d)
                if num_total > 100 and (num_unique / num_total < 0.5):
                    d[col] = d[col].astype('category')
                    new_type = 'category'
                    extra_info = f" (card: {num_unique}/{num_total})"

            if new_type and str(new_type) != str(col_type):
                # Just log the type change here, detailed metrics come later
                changes.append(f"{col}: {col_type}->{new_type}{extra_info}")

        # Recalculate metrics
        if verbose or check_intern_loss:
            end_metrics = get_col_metrics(d)
            end_mem = sum(m['mem'] for m in end_metrics.values()) / 1024**2
        else:
            end_mem = get_memory_usage_mb(d)

        diff = start_mem - end_mem
        reduction = 100 * diff / start_mem if start_mem > 0 else 0

        # Detailed Report Generation
        report_lines = []
        if verbose or end_mem > start_mem: # Force report if memory increased
            report_lines.append(f"Memory optimization: {start_mem:.2f} MB -> {end_mem:.2f} MB ({reduction:.1f}% reduction)")

            if start_metrics: # Only detailed report if we computed start metrics
                # Identify columns with significant changes (good or bad)
                # Sort by magnitude of change (absolute bytes)
                col_changes = []
                for col in d.columns:
                    m_start = start_metrics.get(col)
                    m_end = end_metrics.get(col)

                    if not m_start or not m_end: continue

                    mem_diff_bytes = m_end['mem'] - m_start['mem']

                    # Only report if changed
                    if mem_diff_bytes != 0 or str(m_start['dtype']) != str(m_end['dtype']):
                        col_changes.append({
                            'col': col,
                            'diff': mem_diff_bytes,
                            'desc': f"{col}: {m_start['dtype']}->{m_end['dtype']} ({m_start['mem']/1024:.1f}KB -> {m_end['mem']/1024:.1f}KB)"
                        })

                        # Check for object intern loss
                        if m_start['unique_objs'] != -1 and m_end['unique_objs'] != -1:
                            # If unique objects increased, we lost sharing
                            if m_end['unique_objs'] > m_start['unique_objs']:
                                col_changes[-1]['desc'] += f" [INTERN LOSS: {m_start['unique_objs']}->{m_end['unique_objs']} objs]"

                # Print top changes
                col_changes.sort(key=lambda x: x['diff'], reverse=True) # Biggest increase first
                for c in col_changes:
                    if c['diff'] > 0:
                        report_lines.append(f"   CREATED overhead: {c['desc']} (+{c['diff']/1024:.1f} KB)")
                    else:
                        report_lines.append(f"   Optimized: {c['desc']}")
            else:
                # Fallback concise report
                if changes:
                    report_lines.append(f"   Changes: {', '.join(changes)}")

        # Output the report
        if report_lines and verbose:
            print("\n".join(report_lines), flush=True)

        if end_mem > start_mem:
            print(f"   Warning: Memory increased! Reverting changes.")
            return d_in # Return original

        return d

    if isinstance(df, pd.DataFrame):
        return _optimize_single(df, verbose)

    # Handle Iterable
    def _generator():
        # Help type checker know this is an Iterable of DataFrames, not a single DataFrame
        # explicitly, avoiding the ambiguity that causes the Hashable error.
        iterator = cast(Iterable[pd.DataFrame], df)
        for i, chunk in enumerate(iterator):
            yield _optimize_single(chunk, verbose=verbose)

    return _generator()

def process_ratings_chunk(chunk: pd.DataFrame, valid_anime_ids: set, id_map_anime: dict) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Processes a single chunk of the ratings dataset.
    Designed to be pickleable for parallel processing.
    """
    # Fix for joblib read-only memmap issue
    chunk = chunk.copy()

    chunk_metrics = {
        'rows_read': len(chunk),
        'dropped_orphans': 0,
        'fk_remapped': 0,
        'fk_samples': []
    }

    # 1. Remap FKs
    if id_map_anime:
        mask = chunk['anime_id'].isin(id_map_anime.keys())
        if mask.any():
            # Log sample remappings (limited to avoid huge pickles)
            mask_sample = mask & ~chunk['anime_id'].isna()
            if mask_sample.any():
                # Just take one sample per chunk to keep it light
                old_values = chunk.loc[mask_sample, 'anime_id'].head(1)
                new_values = old_values.map(id_map_anime)
                chunk_metrics['fk_samples'].append(dict(zip(old_values, new_values)))

            chunk.loc[mask, 'anime_id'] = chunk.loc[mask, 'anime_id'].map(id_map_anime)
            chunk_metrics['fk_remapped'] += int(mask.sum())

    # 2. Filter Orphans
    initial_len = len(chunk)
    chunk = chunk[chunk['anime_id'].isin(valid_anime_ids)]
    chunk_metrics['dropped_orphans'] += (initial_len - len(chunk))

    # 3. Optimize (Disable verbose and expensive checks for speed)
    chunk = optimize_dtypes(chunk, verbose=False, check_intern_loss=False)

    return chunk, chunk_metrics

from solution.src.utils import save_refined

def process_generic_dataset(dataset_name: str, processed_files_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Processes a generic dataset end-to-end: Load -> Clean -> Optimize -> Save.
    Designed for parallel execution.
    """
    # 1. Read
    df = load_raw(dataset_name)
    
    # Stats Capture
    initial_rows = len(df)
    initial_mem = get_memory_usage_mb(df)
    actions = []

    # 2. Clean (Generic Logic)
    df, metrics = standardize_dataset(df)
    if metrics.get('duplicates_dropped', 0) > 0:
        actions.append(f"Deduplicated ({metrics['duplicates_dropped']} rows)")

    df.dropna(how='all', inplace=True)

    # Specific Logic
    if dataset_name == "person_details":
        if 'birthday' in df.columns:
            df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce')
            actions.append("Date Parsing (birthday)")
    
    if dataset_name == "profiles":
        if 'joined' in df.columns:
            df['joined'] = pd.to_datetime(df['joined'], errors='coerce')
            actions.append("Date Parsing (joined)")

    # Capture Memory After Cleaning (before optimization)
    mem_cleaned = get_memory_usage_mb(df)

    # 3. Optimize (Disable verbose)
    df = optimize_dtypes(df, verbose=False, check_intern_loss=False)

    # Capture Final Stats
    final_rows = len(df)
    final_mem = get_memory_usage_mb(df)

    # 4. Save
    out_filename = processed_files_map.get(dataset_name)
    if out_filename:
        out_path = PROCESSED_DATA_DIR / out_filename
        save_refined(df, out_path, format='parquet')

    return {
        'file': dataset_name,
        'rows_src': initial_rows,
        'rows_dst': final_rows,
        'mem_src': initial_mem,
        'mem_cleaned': mem_cleaned,
        'mem_dst': final_mem,
        'actions': actions
    }

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

def resolve_content_duplicates(df: pd.DataFrame, primary_key: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
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

    # It has some duplicates

    metrics['duplicates_found'] = int(dupes_mask.sum())

    # Process duplicates to build the map
    dupes = df[dupes_mask].copy()

    # We group by the content columns
    grouped = dupes.groupby(cols_to_check, dropna=False)

    original_indices_to_drop = []

    for _, group in grouped:
        group = cast(pd.DataFrame, group)

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

def print_cleaning_report(step_name: str, metrics: Dict[str, Any]):
    """
    Prints a formatted report of the cleaning step.
    """

    print(f"--- {step_name} Report ---")
    for key, value in metrics.items():
        if key == 'id_map':
            print(f"  ID Mappings Created: {len(value)}")
            if value:
                # Print first 5 mappings as sample
                sample = list(value.items())[:5]
                print(f"    Sample: {sample} ...")

        elif isinstance(value, float):
            print(f"  {key}: {value:.2f}")

        else:
            print(f"  {key}: {value}")

def print_fk_remapping_report(samples: list[dict]):
    """
    Prints a user-friendly report of Foreign Key remappings.
    Args:
        samples: List of dictionaries, each containing {old_id: new_id} mappings.
    """

    if not samples:
        return

    print("\n--- FK Remapping (Duplicate Merges) ---")
    print("The following Foreign Keys (Anime IDs) were updated because the original ID")
    print("was identified as a duplicate and merged into a canonical ID.")
    print("-" * 60)

    for i, sample_dict in enumerate(samples, 1):
        items_str = ", ".join([f"{k} -> {v:.0f}" for k, v in sample_dict.items()])
        print(f"Batch {i}: {items_str}")
    print("-" * 60)
