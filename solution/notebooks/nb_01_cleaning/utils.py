import pandas as pd
import numpy as np
import gc
from solution.src.common import PROCESSED_DATA_DIR

def get_memory_usage_mb(df: pd.DataFrame) -> float:
    """Returns the memory usage of the DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / 1024 ** 2

def print_fancy_progress(current: int, total: int, prefix: str = '', length: int = 30):
    """
    Prints a fancy ASCII progress bar via terminal characters.
    Style: [==========          ] 50.0%
    """
    percent = current / total
    # Cap at 1.0 needed for safety
    if percent > 1.0: percent = 1.0
    
    filled = int(length * percent)
    # Use spaces for empty part
    bar = '=' * filled + ' ' * (length - filled) 
    
    # \r returns to start of line, end="" prevents new line until done
    print(f"\r{prefix} [{bar}] {percent:.1%}", end="", flush=True)
    
    if current == total:
        print() # New line on completion

def optimize_dtypes(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Downcast numeric types and convert low-cardinality objects to categories.
    Reports memory reduction.
    """
    start_mem = get_memory_usage_mb(df)
    
    for col in df.columns:
        col_type = df[col].dtype

        # Numeric Downcasting
        if pd.api.types.is_numeric_dtype(col_type):
            if pd.api.types.is_integer_dtype(col_type):
                # Check range for integers
                min_val, max_val = df[col].min(), df[col].max()
                if min_val >= 0:
                    if max_val <= 255: df[col] = df[col].astype(np.uint8)
                    elif max_val <= 65535: df[col] = df[col].astype(np.uint16)
                    elif max_val <= 4294967295: df[col] = df[col].astype(np.uint32)
                else:
                    if min_val >= -128 and max_val <= 127: df[col] = df[col].astype(np.int8)
                    elif min_val >= -32768 and max_val <= 32767: df[col] = df[col].astype(np.int16)
                    elif min_val >= -2147483648 and max_val <= 2147483647: df[col] = df[col].astype(np.int32)

            elif pd.api.types.is_float_dtype(col_type):
                # We can often use float32 instead of float64 for our ranges
                # Skip if column has NaN and needs float behavior, but float32 handles NaNs too.
                df[col] = df[col].astype(np.float32)

        # Categorical Conversion (simple heuristic: < 50% unique values)
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

def save_refined(df: pd.DataFrame, filename: str, verbose: bool = True):
    """Saves DataFrame to Parquet (preferred) or CSV using compression and performs GC."""
    file_path = PROCESSED_DATA_DIR / f"{filename.replace('.csv', '.parquet')}"
    if verbose:
        print(f"Saving {filename} to {file_path}...")
    try:
        # Use zstd compression for good balance of speed and size
        df.to_parquet(file_path, index=False, compression='zstd')
        if verbose:
            print("Done.")
    except Exception as e:
        print(f"Error saving parquet: {e}. Falling back to CSV.")
        df.to_csv(PROCESSED_DATA_DIR / filename, index=False)
    
    # Force Garbage Collection to free memory immediately after save
    gc.collect()
