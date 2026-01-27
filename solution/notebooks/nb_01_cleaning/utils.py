import pandas as pd
import numpy as np
import gc
from solution.src.common import PROCESSED_DATA_DIR

def get_memory_usage_mb(df: pd.DataFrame) -> float:
    """
    Calculates the memory usage of the DataFrame in Megabytes (MB).
    
    Args:
        df: The pandas DataFrame to inspect.
        
    Returns:
        float: Memory usage in MB.
    """
    return df.memory_usage(deep=True).sum() / 1024 ** 2

def print_fancy_progress(current: int, total: int, prefix: str = '', length: int = 30):
    """
    Displays a terminal-based progress bar.
    
    Args:
        current: Current iteration or value.
        total: Total iterations or target value.
        prefix: Optional text to prepend to the bar.
        length: Character length of the progress bar.
    """
    percent = current / total
    if percent > 1.0: percent = 1.0
    
    filled = int(length * percent)
    
    # ANSI Escape Codes for coloring
    GREEN = "\033[32m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    
    char = '-'
    bar = f"{GREEN}{char * filled}{GRAY}{char * (length - filled)}{RESET}"
    
    print(f"\r{prefix} {bar} {percent:.1%}", end="", flush=True)
    
    if current == total:
        print() 

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

        # Numeric Downcasting
        if pd.api.types.is_numeric_dtype(col_type):
            if pd.api.types.is_integer_dtype(col_type):
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
                # Downcast float64 to float32 for efficiency
                df[col] = df[col].astype(np.float32)

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

def save_refined(df: pd.DataFrame, filename: str, verbose: bool = True):
    """
    Persists the DataFrame to storage, preferring Parquet format with compression.
    Falls back to CSV if Parquet writing fails.
    
    Args:
        df: DataFrame to save.
        filename: Base filename (e.g. 'data.csv').
        verbose: If True, prints status messages.
    """
    file_path = PROCESSED_DATA_DIR / f"{filename.replace('.csv', '.parquet')}"
    if verbose:
        print(f"Saving {filename} to {file_path}...")
    try:
        # Use zstd compression for optimal speed/size ratio
        df.to_parquet(file_path, index=False, compression='zstd')
        if verbose:
            print("Done.")
    except Exception as e:
        print(f"Error saving parquet: {e}. Falling back to CSV.")
        df.to_csv(PROCESSED_DATA_DIR / filename, index=False)
    
    # Trigger Garbage Collection
    gc.collect()

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
