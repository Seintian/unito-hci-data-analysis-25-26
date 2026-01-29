import pandas as pd
import os
import time

from .stats import StreamStats
from .config import CHUNK_SIZE, RAM_SAFETY_FACTOR, PYARROW_BLOCK_SIZE

def process_file_stream(file_path: str, chunk_size: int = CHUNK_SIZE) -> StreamStats:
    """
    Reads a CSV file in chunks and computes statistics on the fly.

    This function implements a **Hybrid Loading Strategy**:
    1.  **Fast Path (Pyarrow)**: Attempts to load the entire file into memory using the 
        fast `pyarrow` engine. This is significantly faster but requires RAM > 4x File Size.
        It checks available memory before attempting this.
    2.  **Safe Path (Standard C-Engine)**: If memory is insufficient or Pyarrow fails 
        (e.g., malformed CSV), it falls back to the standard Pandas C engine processing 
        the file in `chunk_size` streams. This is slower but memory-safe for arbitrarily 
        large files.

    Args:
        file_path (str): Absolute path to the CSV file.
        chunk_size (int): Number of rows per chunk (only used for C-Engine fallback).

    Returns:
        StreamStats: Object containing aggregated analysis results (ranges, nulls, types).
    """

    start_time = time.time()
    stats = StreamStats()

    # PERFORMANCE OPTIMIZATION:
    # 1. Try 'pyarrow' engine: Fastest, but loads entire file into RAM.
    #    We perform a Pre-Flight Check: Ensure File Size * Safety Factor < Available RAM.
    # 2. Fallback to 'c' engine: Slower, but supports chunking (Memory Safe).

    use_pyarrow = False
    try:
        import psutil
        file_size = os.path.getsize(file_path)
        available_ram = psutil.virtual_memory().available

        # Check if we have enough RAM
        if available_ram > (file_size * RAM_SAFETY_FACTOR):
            use_pyarrow = True
        else:
            # Print with newline to ensure it's not overwritten by the progress bar later
            print(f"  [INFO] File size ({file_size/1024/1024:.1f} MB) too large for safer Pyarrow load with {available_ram/1024/1024:.1f} MB RAM available.\n  -> Using chunked stream...", end='\n')

    except ImportError:
        # psutil not installed, skip smart check and try pyarrow blindly (or default to C-engine if preferred)
        # Here we'll try pyarrow but catch the OOM in the inner try/except
        use_pyarrow = True

    except Exception as e:
        print(f"[WARN] Memory check failed: {e}. Proceeding blindly.")
        use_pyarrow = True

    engine_used = "Unknown"

    try:
        processed_with_fast_engine = False

        if use_pyarrow:
            try:
                # Attempt 1: Pyarrow (All at once) - Direct Usage for maximal control
                print(f"  [INFO] Attempting fast load with 'pyarrow'...", end='\r')

                import pyarrow.csv as pa_csv

                # Configure robust options
                # newlines_in_values=True allows robustly handling fields containing line breaks
                parse_options = pa_csv.ParseOptions(newlines_in_values=True)

                # block_size=10MB: Larger blocks can improve performance on high-throughput IO
                read_options = pa_csv.ReadOptions(block_size=PYARROW_BLOCK_SIZE) 

                # Read to Table then convert to Pandas
                table = pa_csv.read_csv(
                    file_path,
                    parse_options=parse_options,
                    read_options=read_options
                )
                df = table.to_pandas()

                # Process as a single "chunk"
                stats.update(df)
                print(f"  Processed {stats.total_rows:,} rows (pyarrow)...", end='\r')

                # Clear memory immediately after processing
                del df
                processed_with_fast_engine = True
                engine_used = "Pyarrow (Fast)"

            except Exception as pyarrow_err:
                # Fallback to C engine if pyarrow fails (e.g. OOM, chunksize error, encoding)
                # Clear line first
                print(f"{' '*80}", end='\r')
                print(f"  [INFO] Pyarrow engine failed: {pyarrow_err}\n  -> Falling back to chunked 'c' engine...")
                # Reset stats just in case partial update happened
                stats = StreamStats() 
                processed_with_fast_engine = False

        if not processed_with_fast_engine:
            # Fallback (or Primary if RAM was low): Chunked C Engine
            engine_used = "Standard C-Engine (Chunked)"
            with pd.read_csv(
                file_path, 
                chunksize=chunk_size, 
                engine='c', 
                on_bad_lines='skip',
                encoding_errors='replace' 
            ) as reader:
                for i, chunk in enumerate(reader):
                    stats.update(chunk)
                    print(f"  Processed {stats.total_rows:,} rows (c-engine)...", end='\r')

        elapsed_time = time.time() - start_time
        print(f"  [DONE] Finished processing {stats.total_rows:,} rows in {elapsed_time:.2f}s using {engine_used}.        ")

    except Exception as e:
        print(f"[ERROR] reading file: {e}")

    return stats
