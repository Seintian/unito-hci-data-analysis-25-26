"""
Unit Tests for the Statistics Accumulation Logic.

This module validates the `StreamStats` class, which is responsible for aggregating
data properties (min, max, nulls, cardinality) from streaming chunks.
Critically, it verifies the 'decimal tracking' logic used to distinguish
between true floating point numbers and integers stored as floats.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the source directory to path to allow imports
# Assuming structure: solution/tests/nb_00.../test_stats.py
# Source is: solution/notebooks/nb_00...
# We go up 3 levels to 'solution', then down to 'notebooks'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../notebooks"))
sys.path.insert(0, project_root)

from nb_00_pre_cleaning_analysis.stats import StreamStats

class TestStreamStats(unittest.TestCase):
    def setUp(self):
        self.stats = StreamStats()

    def test_numeric_accumulation(self):
        """Verify min/max/nulls for standard numeric data."""
        df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [1.5, 2.5, np.nan]})
        self.stats.update(df1)

        self.assertEqual(self.stats.total_rows, 3)

        # Check Column 'a' (Integers)
        prof_a = self.stats.cols_stats['a']
        self.assertEqual(prof_a.min_val, 1)
        self.assertEqual(prof_a.max_val, 3)
        self.assertEqual(prof_a.nulls, 0)
        self.assertTrue(prof_a.is_numeric)
        self.assertFalse(prof_a.is_float) # Pure integers in Pandas often inference as int64

        # Check Column 'b' (Floats with Null)
        prof_b = self.stats.cols_stats['b']
        self.assertEqual(prof_b.min_val, 1.5)
        self.assertEqual(prof_b.max_val, 2.5)
        self.assertEqual(prof_b.nulls, 1)
        self.assertTrue(prof_b.is_float)
        self.assertTrue(prof_b.has_decimals)

    def test_decimal_tracking(self):
        """Verify accurate decimal detection (critical for ID inference)."""
        # Case 1: Float but effectively Int (e.g. IDs)
        df_ids = pd.DataFrame({'id': [1.0, 2.0, 3.0, 4.0]}) 
        self.stats.update(df_ids)

        prof = self.stats.cols_stats['id']
        self.assertTrue(prof.is_float)
        self.assertFalse(prof.has_decimals, "Should NOT detect decimals for distinct whole numbers")

        # Case 2: Float with real decimals
        df_real = pd.DataFrame({'val': [1.0, 2.1]})
        self.stats.update(df_real)

        prof_real = self.stats.cols_stats['val']
        self.assertTrue(prof_real.is_float)
        self.assertTrue(prof_real.has_decimals, "Should detect decimals")

    def test_object_accumulation(self):
        """Verify unique counts and samples for object columns."""
        df = pd.DataFrame({'cat': ['A', 'B', 'A', 'C', None]})
        self.stats.update(df)

        prof = self.stats.cols_stats['cat']
        self.assertFalse(prof.is_numeric)
        self.assertEqual(prof.nulls, 1)
        self.assertEqual(prof.unique_count, 3) # A, B, C
        self.assertIn('A', prof.unique_set)

if __name__ == '__main__':
    unittest.main()
