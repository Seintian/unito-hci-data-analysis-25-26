import pandas as pd
import numpy as np
from typing import Union, Iterable, Generator


def get_memory_usage_mb(df: pd.DataFrame) -> float:
    """
    Returns the memory usage of the DataFrame in Megabytes.
    """

    return df.memory_usage(deep=True).sum() / 1024 ** 2

def reduce_memory_usage(data: Union[pd.DataFrame, Iterable[pd.DataFrame]], verbose: bool = True) -> Union[pd.DataFrame, Generator[pd.DataFrame, None, None]]:
    """
    Reduces memory usage by downcasting numbers and converting low-cardinality strings to categories.
    """

    if isinstance(data, pd.DataFrame):
        return _optimize_single_dataframe(data, verbose)

    return _optimize_stream(data, verbose)


# --- Private Helpers ---

def _optimize_stream(iterator: Iterable[pd.DataFrame], verbose: bool) -> Generator[pd.DataFrame, None, None]:
    for chunk in iterator:
        yield _optimize_single_dataframe(chunk, verbose)

def _optimize_single_dataframe(df: pd.DataFrame, verbose: bool) -> pd.DataFrame:
    df_optimized = df.copy()
    start_mem = get_memory_usage_mb(df)

    # 1. Downcast Numbers
    _downcast_numerics(df_optimized)

    # 2. Convert to Category
    _convert_objects_to_category(df_optimized)

    end_mem = get_memory_usage_mb(df_optimized)

    if verbose:
        _print_reduction_stats(start_mem, end_mem)

    if end_mem > start_mem:
        # Safety check: if memory increased, revert.
        return df

    return df_optimized

def _downcast_numerics(df: pd.DataFrame):
    for col in df.columns:
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='integer')

        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], downcast='float')
            _try_convert_float_to_int(df, col)

def _try_convert_float_to_int(df: pd.DataFrame, col: str):
    """
    Tries to convert float columns that contain only whole numbers to Nullable Ints (Int32/Int64).
    """

    series = df[col]
    no_nans = series.dropna()

    if len(no_nans) > 0 and np.all(np.mod(no_nans, 1) == 0):
        min_val, max_val = no_nans.min(), no_nans.max()
        if min_val >= -2_147_483_648 and max_val <= 2_147_483_647:
            df[col] = series.astype("Int32")
        else:
            df[col] = series.astype("Int64")

def _convert_objects_to_category(df: pd.DataFrame):
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            num_unique = len(df[col].unique())
            num_total = len(df)
            if num_total > 100 and (num_unique / num_total < 0.5):
                df[col] = df[col].astype('category')

def _print_reduction_stats(start: float, end: float):
    diff = start - end
    reduction = 100 * diff / start if start > 0 else 0
    print(f"Memory optimized: {start:.2f} MB -> {end:.2f} MB ({reduction:.1f}% reduction)")
