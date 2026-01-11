"""
Core analysis logic for the Pre-Cleaning Pipeline.

This module is responsible for interpreting the raw statistics collected by `StreamStats`
and generating higher-level insights, such as optimization recommendations,
primary key candidacy, and missing value summaries.
"""

import numpy as np
import pandas as pd
import re
from typing import List, Dict, Optional, Tuple

from .stats import StreamStats
from .config import (
    CATEGORY_CARDINALITY_THRESHOLD, CATEGORY_DENSITY_THRESHOLD,
    BOOLEAN_MAX_UNIQUE, BOOLEAN_INDICATORS,
    DATETIME_REGEX_PATTERN, DATETIME_MATCH_THRESHOLD
)

# --- Type Constraints ---
# These define the boundaries for safe downcasting.
# They are implementation details of the analysis logic.

CHECK_INT_TYPES: List[Tuple[Tuple[int, int], str]] = [
    ((np.iinfo(np.int8).min, np.iinfo(np.int8).max), "int8"),
    ((np.iinfo(np.int16).min, np.iinfo(np.int16).max), "int16"),
    ((np.iinfo(np.int32).min, np.iinfo(np.int32).max), "int32"),
]

CHECK_FLOAT_TYPES: List[Tuple[Tuple[float, float], str]] = [
    ((np.finfo(np.float16).min, np.finfo(np.float16).max), "float16"),
    ((np.finfo(np.float32).min, np.finfo(np.float32).max), "float32"),
]


def get_primary_key_report(stats: StreamStats) -> Dict[str, str]:
    """
    Analyzes Primary Key candidates and returns a status dict.

    Args:
        stats (StreamStats): The collected statistics.

    Returns:
        Dict[str, str]: Map of column name -> status message ("OK", "FAIL", "WARN").
    """

    report = {}
    for col, cand in stats.pk_candidates.items():
        if cand.failed:
            report[col] = "FAIL"
        elif cand.large_skipped:
            report[col] = "WARN_LARGE" # Optimized candidate
        else:
            report[col] = "OK"

    return report


def get_missing_values_table(stats: StreamStats) -> pd.DataFrame:
    """
    Generates a DataFrame summarizing missing values.

    Returns:
        pd.DataFrame: Columns ['Column', 'Missing Count', 'Percentage']
    """

    missing_data = []
    for col, data in stats.cols_stats.items():
        if data.nulls > 0:
            missing_data.append({
                'Column': col,
                'Missing Count': data.nulls,
                'Percentage': (data.nulls / stats.total_rows) * 100
            })

    df = pd.DataFrame(missing_data)
    if not df.empty:
        df = df.sort_values('Percentage', ascending=False)

    return df


def get_optimization_recommendations(stats: StreamStats) -> pd.DataFrame:
    """
    Generates data type optimization recommendations based on value ranges and cardinality.

    Args:
        stats (StreamStats): Collected statistics.

    Returns:
        pd.DataFrame: Table of recommendations.
    """

    recommendations = []

    for col, data in stats.cols_stats.items():
        original_dtype = stats.dtypes.get(col, 'unknown')
        rec_type: Optional[str] = None
        reason: Optional[str] = None

        # --- A) Integer Optimization (or Float that is effectively Integer) ---
        # We check if it is numeric and NOT a float OR (it is a float but has no decimals)
        is_effectively_int = False
        if data.is_numeric:
            if not data.is_float:
                is_effectively_int = True
            elif data.is_float and not data.has_decimals:
                is_effectively_int = True

        if is_effectively_int:
            c_min = data.min_val
            c_max = data.max_val

            # If it's effectively int but currently stored as float
            current_is_float = 'float' in str(original_dtype)

            # Default logic: check if it fits in smaller types
            if c_min > float('-inf') and c_max < float('inf'):
                for (limit_min, limit_max), type_name in CHECK_INT_TYPES:
                    if c_min >= limit_min and c_max <= limit_max:
                        # If simple int is safe (no nulls), recommend it
                        if data.nulls == 0:
                            rec_type = type_name
                            reason = f"Range [{int(c_min)}, {int(c_max)}]"
                            break

            # Special Case: It is a float, no decimals, no nulls, but didn't fit small ints
            # It might fit int64. If current is float64, recommending int64 is better?
            if current_is_float and data.nulls == 0 and not rec_type:
                # fits in int64?
                if c_min >= np.iinfo(np.int64).min and c_max <= np.iinfo(np.int64).max:
                    rec_type = 'int64'
                    reason = f"Integers stored as Float (Safe to cast)"

        # --- B) Float Optimization ---
        # Only check strict float optimization if we didn't already find an int recommendation
        # (or if we found one but want to see if float16 is even smaller? No, int is usually preferred for IDs)
        if data.is_float and not rec_type:
            c_min = data.min_val
            c_max = data.max_val

            # Check if it fits in smaller float types
            for (limit_min, limit_max), type_name in CHECK_FLOAT_TYPES:
                if c_min > limit_min and c_max < limit_max:
                    # Only recommend if it's smaller than current
                    # Simple string check: 'float16' < 'float32' < 'float64'
                    current_str = str(original_dtype)
                    if type_name == 'float16' and current_str in ['float32', 'float64']:
                        rec_type = type_name
                        reason = f"Range [{c_min:.5g}, {c_max:.5g}]"
                        break
                    elif type_name == 'float32' and current_str == 'float64':
                        rec_type = type_name
                        reason = f"Range [{c_min:.5g}, {c_max:.5g}]"
                        break

        # --- C) Object Optimization (Category, Boolean, Datetime) ---
        elif not data.is_numeric and data.unique_count > 0:
            # Heuristic: If cardinality is Low (<10k unique) AND Dense (<50% of rows), use Category
            if data.unique_count < CATEGORY_CARDINALITY_THRESHOLD and (data.unique_count / stats.total_rows) < CATEGORY_DENSITY_THRESHOLD:
                # Check for Boolean candidate
                unique_set = data.unique_set
                unique_count = data.unique_count

                unique_clean = {
                    str(x).lower().strip()
                    for x in unique_set
                    if pd.notna(x)
                }

                if unique_clean.issubset(BOOLEAN_INDICATORS) and unique_count <= BOOLEAN_MAX_UNIQUE: 
                    rec_type = "boolean"
                    reason = f"Boolean Candidate (Values: {unique_clean})"
                else:
                    rec_type = "category"
                    reason = f"Low Cardinality ({unique_count} unique)"

            # Check for Datetime candidate (Heuristic on sample strings)
            if data.sample_values:
                date_pattern = re.compile(DATETIME_REGEX_PATTERN)
                matches = 0
                samples = data.sample_values
                for s in samples:
                    if date_pattern.match(str(s)):
                        matches += 1

                if len(samples) > 0 and (matches / len(samples)) > DATETIME_MATCH_THRESHOLD:
                    rec_type = "datetime"
                    reason = "ISO-8601 Date Format Detected"

        # Add to recommendations if found
        if rec_type and str(original_dtype) != rec_type:
            # Avoid trivial int64->int64 recommendations
            if str(original_dtype) == 'int64' and rec_type == 'int64':
                pass

            else:
                recommendations.append({
                    "Column": col,
                    "Current": str(original_dtype),
                    "Recommended": rec_type,
                    "Reason": reason
                })

    return pd.DataFrame(recommendations)
