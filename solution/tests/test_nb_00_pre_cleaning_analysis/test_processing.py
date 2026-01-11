"""
Integration Tests for the File Processing Pipeline.

This module tests the end-to-end `process_file_stream` function.
It uses `tempfile` to generate actual CSV files on disk and verifies that
the system can correctly load them (using either Pyarrow or C-Engine fallback)
and return a populated `StreamStats` object.
"""

import unittest
import pandas as pd
import sys
import os
import tempfile

# Path handling
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../notebooks"))
sys.path.insert(0, project_root)

from nb_00_pre_cleaning_analysis import processing

class TestProcessing(unittest.TestCase):
    def setUp(self):
        # Create a temp CSV file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv', newline='')
        self.temp_path = self.temp_file.name

        # Write dummy data (100 rows)
        # col_int: 0..99
        # col_mixed: "A", "B"...
        df = pd.DataFrame({
            'col_int': range(100),
            'col_str': ['A'] * 50 + ['B'] * 50
        })
        df.to_csv(self.temp_path, index=False)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_process_file_stream_full(self):
        """Test processing a file from disk."""
        # Use small chunk size to force C-engine loop if it falls back
        # (Though with valid CSV and RAM check, it might default to pyarrow. 
        # We can't easily force engine choice without mocking, but we verify outcome)
        stats = processing.process_file_stream(self.temp_path, chunk_size=10)
        self.assertEqual(stats.total_rows, 100)

        # Verify Stats
        prof_int = stats.cols_stats['col_int']
        self.assertEqual(prof_int.min_val, 0)
        self.assertEqual(prof_int.max_val, 99)
        self.assertEqual(prof_int.nulls, 0)

        prof_str = stats.cols_stats['col_str']
        self.assertEqual(prof_str.unique_count, 2) # A, B

if __name__ == '__main__':
    unittest.main()
