import pandas as pd
import numpy as np
import gc
from solution.src.common import PROCESSED_DATA_DIR

def get_memory_usage_mb(df: pd.DataFrame) -> float:
    """Returns the memory usage of the DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / 1024 ** 2

def print_fancy_progress(current: int, total: int, prefix: str = '', length: int = 30):
    """
    Prints a terminal-style progress bar with colored lines.
    Style: Prefix -------_______ 50.0% (Green filled, Gray empty)
    """
    percent = current / total
    if percent > 1.0: percent = 1.0
    
    filled = int(length * percent)
    
    # ANSI Colors
    GREEN = "\033[32m" # Standard Green
    GRAY = "\033[90m"  # Bright Black (Gray)
    RESET = "\033[0m"
    
    # Character to use
    char = '-'
    
    # Build the bar: Green filled part + Gray empty part
    bar = f"{GREEN}{char * filled}{GRAY}{char * (length - filled)}{RESET}"
    
    # \r returns to start of line
    print(f"\r{prefix} {bar} {percent:.1%}", end="", flush=True)
    
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

def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trims whitespace from string columns and optionally standardizes format.
    Safely handles NaNs.
    """
    for col in df.columns:
        # Check if column is object/string and not categorical
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            if isinstance(df[col].dtype, pd.CategoricalDtype):
                continue
            
            # Apply .str.strip() which is NaN-safe for object columns containing strings/NaNs
            try:
                # This works if the column is of object dtype with strings.
                # If it contains mixed types (int and str), .str might fail or result in NaNs for non-strings depending on pandas version.
                # Safe approach: convert to string only if it's not null?
                # Actually, .str accessor usually handles NaN gracefully by keeping it NaN.
                df[col] = df[col].str.strip()
            except AttributeError:
                # Column might not support .str accessor (e.g. if it's all integers cast to object?)
                pass
                
    return df

def enforce_referential_integrity(df: pd.DataFrame, col_name: str, valid_ids: set) -> tuple[pd.DataFrame, int]:
    """
    Drops rows where col_name is not in valid_ids.
    Returns (cleaned_df, num_dropped).
    """
    if col_name not in df.columns:
        return df, 0
    
    initial_rows = len(df)
    
    # Ensure compatible types for matching
    # Helper to infer type for safety? Assuming ID types match (usually int or string)
    # We'll rely on the caller ensuring types match or just try matching.
    
    df = df[df[col_name].isin(valid_ids)]
    
    dropped = initial_rows - len(df)
    return df, dropped
