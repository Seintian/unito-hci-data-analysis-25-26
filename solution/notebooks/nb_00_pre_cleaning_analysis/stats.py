from collections import defaultdict
import pandas as pd
from typing import Dict, Any, Set, List
from dataclasses import dataclass, field

from .config import (
    GHOST_ROW_THRESHOLD, MAX_UNIQUE_TRACKING, SAMPLE_VALUE_COUNT,
    PK_CANDIDATE_KEYWORDS, PK_SUFFIX_KEYWORD, PK_TRACKING_LIMIT
)

@dataclass
class PkCandidate:
    """
    Tracks the viability of a column to be a Primary Key.

    Attributes:
        seen (Set[Any]): Set of unique values encountered so far.
        failed (bool): True if duplicates have been found.
        large_skipped (bool): True if optimization skipped tracking due to high cardinality.
    """

    seen: Set[Any] = field(default_factory=set)
    failed: bool = False
    large_skipped: bool = False

@dataclass
class ColumnProfile:
    """
    Accumulates statistics for a single column during streaming.

    Attributes:
        nulls (int): Count of missing values (NaN/None).
        min_val (float): Minimum numeric value encountered.
        max_val (float): Maximum numeric value encountered.
        is_numeric (bool): True if the column has only contained numeric data so far.
        is_float (bool): True if floating point values have been detected.
        has_decimals (bool): True if floating point values with non-zero decimals exist.
        unique_count (int): Count of unique values (capped).
        unique_set (Set[Any]): Set of unique values encountered (capped at threshold).
        sample_values (List[Any]): A small sample of non-null values for inspection.
    """

    nulls: int = 0
    min_val: float = float('inf')
    max_val: float = float('-inf')
    is_numeric: bool = True
    is_float: bool = False
    has_decimals: bool = False
    unique_count: int = 0
    unique_set: Set[Any] = field(default_factory=set)
    sample_values: List[Any] = field(default_factory=list)

class StreamStats:
    """
    A stateful accumulator for processing large datasets in chunks.

    This class maintains running statistics (min, max, null counts, cardinality)
    without requiring the entire dataset to be loaded into memory.
    """

    def __init__(self):
        self.total_rows: int = 0
        self.bad_lines: int = 0

        # Use a defaultdict factory that returns a fresh ColumnProfile for new columns
        self.cols_stats: Dict[str, ColumnProfile] = defaultdict(ColumnProfile)

        # Track PK candidates with structured objects
        self.pk_candidates: Dict[str, PkCandidate] = defaultdict(PkCandidate)

        self.ghost_row_count: int = 0
        self.dtypes: Dict[str, Any] = {}

    def update(self, chunk: pd.DataFrame) -> None:
        """
        Ingests a DataFrame chunk and updates the running statistics.

        Args:
            chunk (pd.DataFrame): A subset of the dataset.
        """

        self.total_rows += len(chunk)
        self.dtypes = chunk.dtypes

        # 1. Detect Ghost Rows
        # We calculate the fraction of nulls for each row in this chunk
        nulls_per_row = chunk.isnull().mean(axis=1)
        self.ghost_row_count += (nulls_per_row > GHOST_ROW_THRESHOLD).sum()

        # 2. Column Analysis
        for col in chunk.columns:
            stats = self.cols_stats[col]

            # Type classification
            is_num = pd.api.types.is_numeric_dtype(chunk[col])
            stats.is_numeric &= is_num
            if is_num and pd.api.types.is_float_dtype(chunk[col]):
                stats.is_float = True

                # Check for decimals (if not already found)
                if not stats.has_decimals:
                    # Drop NA first because NaN % 1 is NaN, which evaluates to True in some contexts
                    valid_vals = chunk[col].dropna()
                    if not valid_vals.empty:
                        if (valid_vals % 1 != 0).any():
                            stats.has_decimals = True

            # Nulls
            stats.nulls += chunk[col].isnull().sum()

            # Samples (Collect first N non-null strings) for visual content verification
            if len(stats.sample_values) < SAMPLE_VALUE_COUNT:
                # Get first N non-null values
                valid_samples = chunk[col].dropna().astype(str).head(SAMPLE_VALUE_COUNT - len(stats.sample_values)).tolist()
                stats.sample_values.extend(valid_samples)

            # Numeric Stats (Min/Max)
            if is_num:
                col_min = chunk[col].min()
                col_max = chunk[col].max()

                if not pd.isna(col_min):
                    stats.min_val = min(stats.min_val, col_min)

                if not pd.isna(col_max):
                    stats.max_val = max(stats.max_val, col_max)

            else:
                # Cardinality check for Object columns (Category ID candidates)
                # We cap distinct value tracking to prevent OOM
                if len(stats.unique_set) < MAX_UNIQUE_TRACKING: 
                    stats.unique_set.update(chunk[col].dropna().unique())
                    stats.unique_count = len(stats.unique_set)

        # 3. Primary Key Integrity Check
        for col in chunk.columns:
            # Heuristic: verify columns that look like IDs
            if col.endswith(PK_SUFFIX_KEYWORD) or col in PK_CANDIDATE_KEYWORDS:
                cand = self.pk_candidates[col]

                # If already failed or optimized out, skip
                if cand.failed or cand.large_skipped:
                    continue

                new_ids = chunk[col].dropna()
                if not new_ids.empty:
                    # Check for duplicates within the chunk itself
                    if new_ids.duplicated().any():
                        cand.failed = True
                        continue

                    # Safety Cap: If > Limit unique items, assume it's likely a PK and stop tracking to save RAM
                    if len(cand.seen) > PK_TRACKING_LIMIT:
                        cand.large_skipped = True
                        cand.seen = set() # Free memory
                        continue

                    # Check against globally seen IDs
                    new_set = set(new_ids)
                    if not cand.seen.isdisjoint(new_set):
                        cand.failed = True
                    else:
                        cand.seen.update(new_set)
