"""
Shared utilities for the Data Analysis project.
"""

import pandas as pd
from pathlib import Path
from typing import Union, Generator, Any

try:
    import pyarrow.csv as pa_csv
except ImportError:
    pa_csv = None

try:
    import psutil
except ImportError:
    psutil = None


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

def get_available_memory() -> int:
    """Returns available virtual memory in bytes."""

    if psutil:
        return psutil.virtual_memory().available
    return 0

def load_csv_smart(
    file_path: Union[str, Path],
    chunk_size: int = 5_000_000,
    use_pyarrow: bool = True,
    **kwargs: Any
) -> Union[pd.DataFrame, pd.io.parsers.TextFileReader]:
    """
    Smartly loads a CSV file.

    Attempts to use PyArrow for performance if memory allows and the engine is available.
    Falls back to standard Pandas C-engine (chunked if specific arguments imply it, 
    but strictly speaking this function is designed to return a DataFrame mostly).

    Args:
        file_path: Path to the CSV file.
        chunk_size: specific chunk size for fallback or forced chunking.
        use_pyarrow: strict flag to attempt pyarrow.
        **kwargs: Additional arguments passed to pd.read_csv.

    Returns:
        pd.DataFrame or TextFileReader (if chunksize is passed in kwargs)
    """

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Safety factor for RAM usage (PyArrow needs ~3-4x file size just in case)
    RAM_SAFETY_FACTOR = 4.0

    is_chunked = 'chunksize' in kwargs or kwargs.get('iterator', False)

    # Try PyArrow if requested, not chunked, and module is available
    if use_pyarrow and pa_csv and not is_chunked:
        try:
            file_size = file_path.stat().st_size
            available_ram = get_available_memory()

            # Pre-flight check
            if psutil and available_ram < (file_size * RAM_SAFETY_FACTOR):
                print(f"Using standard pandas (File {file_size/1e6:.1f}MB vs RAM {available_ram/1e6:.1f}MB)")
            else:
                print(f"Loading {file_path.name} with PyArrow...")

                # Note: passing complex kwargs to pyarrow is tricky. 
                # If complex kwargs are present, we might want to skip pyarrow to ensure correctness.
                # simpler approach: read to table, to pandas
                return pa_csv.read_csv(file_path).to_pandas()

        except Exception as e:
            print(f"PyArrow load failed ({e}), falling back to standard engine.")

    # Fallback to standard pandas
    print(f"Loading {file_path.name} with Pandas (Engine: c)...")
    return pd.read_csv(file_path, chunksize=chunk_size, **kwargs)


def save_refined(
    df: pd.DataFrame, 
    path: Union[str, Path], 
    format: str = 'parquet',
    **kwargs: Any
) -> None:
    """
    Saves a DataFrame to the specified format (parquet or csv) with optimized settings.

    Args:
        df: DataFrame to save.
        path: Destination path.
        format: 'parquet' or 'csv'.
        **kwargs: Additional arguments for to_parquet/to_csv.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Saving to {path} ({format})...")

    if format == 'parquet':
        # Default to pyarrow engine and snappy compression for balance
        defaults = {'engine': 'pyarrow', 'compression': 'snappy', 'index': False}
        defaults.update(kwargs)
        df.to_parquet(path, **defaults)

    elif format == 'csv':
        defaults = {'index': False}
        defaults.update(kwargs)
        df.to_csv(path, **defaults)

    else:
        raise ValueError(f"Unsupported format: {format}")

    print("Save complete.")
