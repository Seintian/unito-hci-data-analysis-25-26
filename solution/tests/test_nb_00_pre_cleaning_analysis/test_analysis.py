"""
Unit Tests for the Analysis Business Logic.

This module validates the optimization engines in `analysis.py`.
It mocks `StreamStats` objects with known data profiles (e.g., "a float column with no decimals")
and asserts that the recommendation functions return the expected data types suitable for
efficient Parquet storage.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Path handling (same as stats)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../notebooks"))
sys.path.insert(0, project_root)

from nb_00_pre_cleaning_analysis import analysis
from nb_00_pre_cleaning_analysis.stats import StreamStats, ColumnProfile, PkCandidate

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.stats = StreamStats()

    def test_optimization_integer_inference_from_float(self):
        """Test that Float columns with no decimals are recommended as Integers."""
        # Setup specific profile: Float, No Decimals, No Nulls, Range fits int32
        prof = ColumnProfile(
            nulls=0,
            min_val=1.0,
            max_val=1000.0,
            is_numeric=True,
            is_float=True,
            has_decimals=False # CRITICAL FLAG
        )
        self.stats.cols_stats['id_col'] = prof
        self.stats.dtypes['id_col'] = np.dtype('float64')
        self.stats.total_rows = 1000

        df_rec = analysis.get_optimization_recommendations(self.stats)

        # Verify
        self.assertFalse(df_rec.empty)
        rec = df_rec[df_rec['Column'] == 'id_col'].iloc[0]
        self.assertEqual(rec['Recommended'], 'int16') # 1000 fits in int16
        self.assertIn("Range", rec['Reason'])

    def test_optimization_float16_inference(self):
        """Test that small range Floats (with decimals) go to float16."""
        prof = ColumnProfile(
            nulls=0,
            min_val=0.5,
            max_val=10.5,
            is_numeric=True,
            is_float=True,
            has_decimals=True # Has decimals, so must stay float
        )
        self.stats.cols_stats['score'] = prof
        self.stats.dtypes['score'] = np.dtype('float64')
        self.stats.total_rows = 1000

        df_rec = analysis.get_optimization_recommendations(self.stats)

        self.assertFalse(df_rec.empty)
        rec = df_rec[df_rec['Column'] == 'score'].iloc[0]
        self.assertEqual(rec['Recommended'], 'float16')

    def test_optimization_categorical(self):
        """Test categorical inference."""
        prof = ColumnProfile(
            unique_count=5, # Low cardinality
            nulls=0,
            is_numeric=False
        )
        self.stats.cols_stats['status'] = prof
        self.stats.dtypes['status'] = np.dtype('O') # Object
        self.stats.total_rows = 10000

        df_rec = analysis.get_optimization_recommendations(self.stats)

        rec = df_rec[df_rec['Column'] == 'status'].iloc[0]
        self.assertEqual(rec['Recommended'], 'category')

if __name__ == '__main__':
    unittest.main()
