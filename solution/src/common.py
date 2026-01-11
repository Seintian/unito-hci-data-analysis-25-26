"""
Centralized configuration for project paths and constants.

This module resolves the project root dynamically based on its own location
within the source tree, ensuring that data paths are always correct regardless
of the current working directory.
"""

import sys
from pathlib import Path

# Resolve the project root relative to this file
# This assumes the structure:
#   <PROJECT_ROOT>/
#       solution/
#           src/
#               common.py
_SRC_DIR = Path(__file__).resolve().parent
_SOLUTION_DIR = _SRC_DIR.parent
PROJECT_ROOT = _SOLUTION_DIR.parent

# Define Canonical Data Directories
# Use these constants throughout the project to access data files
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TEMP_DATA_DIR = DATA_DIR / "temp"

# Helper to ensure specific paths are in sys.path (e.g. for notebook usage)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
