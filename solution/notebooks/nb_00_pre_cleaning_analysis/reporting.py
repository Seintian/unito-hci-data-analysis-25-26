from IPython.display import display
import pandas as pd

from .stats import StreamStats
from . import analysis

def report_stats(stats: StreamStats) -> None:
    """
    Visualizes the collected statistics in a readable Markdown report.

    This function acts as the Presentation Layer. It does not perform analysis
    but renders the results provided by the `analysis` module.

    Args:
        stats (StreamStats): The populated statistics object.
    """

    if stats.total_rows == 0:
        print("[WARN] File appears to be empty or unreadable.")
        return

    # 1. Shape & Integrity
    print(f"Total Rows: {stats.total_rows}")
    if stats.bad_lines > 0:
        print(f"[FAIL] Bad Lines Skipped: {stats.bad_lines}")

    _print_primary_key_report(stats)

    # 2. Missing Values
    print("\nMISSING VALUES ANALYSIS")
    df_missing = analysis.get_missing_values_table(stats)
    if not df_missing.empty:
        print("[WARN] Missing Values Detected:")
        display(df_missing)
    else:
        print("[OK] No Missing Values Found")

    # 3. Ghost Rows
    if stats.ghost_row_count > 0:
        print(f"\n[INFO] Found {stats.ghost_row_count} rows with >80% missing values (Ghost Rows)")
    else:
        print("\n[OK] No 'almost-empty' rows found")

    # 4. Current Data Types
    _print_current_dtypes(stats)

    # 5. Optimization Recommendations
    print("\n[INFO] Optimization Recommendations:")

    # 5a. Debug: Show current content for objects
    for col, profile in stats.cols_stats.items():
        if pd.api.types.is_object_dtype(stats.dtypes.get(col)):
            print(f"   [INFO] Content Check '{col}': {profile.sample_values}")

    df_recs = analysis.get_optimization_recommendations(stats)
    if not df_recs.empty:
        display(df_recs)
    else:
        print("   No type optimizations found.")


def _print_primary_key_report(stats: StreamStats) -> None:
    """Prints primary key validation results."""

    print("\nPrimary Key Validation:")
    report = analysis.get_primary_key_report(stats)

    pk_found = False
    for col, status in report.items():
        if status == "FAIL":
            print(f"   [FAIL] '{col}': Duplicates found (Not a PK)")
        elif status == "WARN_LARGE":
            print(f"   [WARN] '{col}': >5M unique values (uniqueness check stopped for safety, likely PK)")
            pk_found = True
        elif status == "OK":
            print(f"   [OK] '{col}': Unique (Candidate for PK)")
            pk_found = True
            
    if not pk_found:
        print("   [WARN] No obvious unique Primary Key found.")

def _print_current_dtypes(stats: StreamStats) -> None:
    """Prints the inferred data types for all columns."""

    print("\n[INFO] Current Data Types:")
    if stats.dtypes is not None and not stats.dtypes.empty:
        # Create a clean DataFrame for display
        dtype_df = pd.DataFrame(stats.dtypes.items(), columns=['Column', 'Dtype'])
        dtype_df = dtype_df.set_index('Column')
        display(dtype_df)
    else:
        print("   No columns found.")

    print("-" * 40)

