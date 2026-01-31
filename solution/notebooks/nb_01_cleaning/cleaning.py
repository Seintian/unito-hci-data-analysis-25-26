import pandas as pd
from typing import Optional, Tuple, Dict, Any, cast


def standardize_column_names_and_text(df: pd.DataFrame, primary_key: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Standardizes dataset by renaming columns to a common schema, trimming text, 
    and removing exact duplicates.
    """

    initial_rows = len(df)
    metrics = {}

    df = _rename_columns_to_schema(df)
    df = trim_all_text_columns(df)

    # Deduplication
    if primary_key and primary_key in df.columns:
        df = df.drop_duplicates(subset=[primary_key])
    else:
        df = df.drop_duplicates()

    metrics['duplicates_dropped'] = initial_rows - len(df)
    return df, metrics

def trim_all_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trims whitespace from all string columns in the DataFrame.
    """

    for col in df.columns:
        if _is_text_column(df[col]):
            try:
                df[col] = df[col].str.strip()
            except AttributeError:
                pass

    return df

def merge_content_duplicates(df: pd.DataFrame, primary_key: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Identifies rows that have identical content (ignoring the primary key) and merges them.
    Returns the cleaned DataFrame and a map of {old_id: new_id}.
    """

    metrics = {
        'duplicates_found': 0,
        'duplicates_dropped': 0,
        'id_map': {}
    }

    if primary_key not in df.columns:
        return df, metrics

    cols_to_check = df.columns.drop(primary_key).tolist()
    dupes_mask = df.duplicated(subset=cols_to_check, keep=False)

    if not dupes_mask.any():
        return df, metrics

    return _perform_merge_logic(df, dupes_mask, cols_to_check, primary_key)

def remove_orphaned_records(df: pd.DataFrame, foreign_key_col: str, valid_primary_keys: set) -> tuple[pd.DataFrame, int]:
    """
    Removes rows where the foreign key is not present in the set of valid primary keys.
    """

    if foreign_key_col not in df.columns:
        return df, 0

    initial_rows = len(df)
    df = df[df[foreign_key_col].isin(valid_primary_keys)]
    dropped_count = initial_rows - len(df)

    return df, dropped_count


# --- Private Helpers ---

def _rename_columns_to_schema(df: pd.DataFrame) -> pd.DataFrame:
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

def _is_text_column(series: pd.Series) -> bool:
    return (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)) and \
            not isinstance(series.dtype, pd.CategoricalDtype)

def _perform_merge_logic(df: pd.DataFrame, dupes_mask: pd.Series, content_cols: list, pk: str) -> Tuple[pd.DataFrame, Dict]:
    metrics = {'duplicates_found': int(dupes_mask.sum()), 'duplicates_dropped': 0, 'id_map': {}}

    dupes = df[dupes_mask].copy()
    grouped = dupes.groupby(content_cols, dropna=False)

    ids_to_drop = []

    for _, group in grouped:
        group = cast(pd.DataFrame, group)
        if len(group) < 2: continue

        # Sort to keep the "best" ID (e.g. non-null, then lowest)
        sorted_group = group.sort_values(by=pk, na_position='last')

        kept_id = sorted_group.iloc[0][pk]
        dropped_rows = sorted_group.iloc[1:]

        for _, row in dropped_rows.iterrows():
            dropped_id = row[pk]
            if pd.notna(dropped_id) and pd.notna(kept_id):
                metrics['id_map'][dropped_id] = kept_id
            ids_to_drop.append(row.name) # Use index to drop

    df_clean = df.drop(index=ids_to_drop)
    metrics['duplicates_dropped'] = len(ids_to_drop)

    return df_clean, metrics
