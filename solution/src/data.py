"""
Dataset definitions and loading logic.
"""

from pathlib import Path
import pandas as pd
import pandas.io.parsers as pd_parsers
from .common import RAW_DATA_DIR, PROCESSED_DATA_DIR
from .utils import load_csv_smart

# Define canonical raw files
RAW_FILES = {
    'details': 'details.csv',
    'stats': 'stats.csv',
    'profiles': 'profiles.csv',
    'reviews': 'reviews.csv',
    'recommendations': 'recommendations.csv',
    'characters': 'characters.csv',
    'favs': 'favs.csv',
    'ratings': 'ratings.csv',
    'character_nicknames': 'character_nicknames.csv',
    'character_anime_works': 'character_anime_works.csv',
    'person': 'person.csv',
    'person_details': 'person_details.csv',
    'person_anime_works': 'person_anime_works.csv',
    'person_voice_works': 'person_voice_works.csv',
    'person_alternate_names': 'person_alternate_names.csv'
}

PROCESSED_FILES = {
    'detailed': 'detailed.parquet',
    'stats': 'stats.parquet',
    'profiles': 'profiles.parquet',
    'reviews': 'reviews.parquet',
    'recommendations': 'recommendations.parquet',
    'characters': 'characters.parquet',
    'favs': 'favs.parquet',
    'ratings': 'ratings.parquet',
    'character_nicknames': 'character_nicknames.parquet',
    'character_anime_works': 'character_anime_works.parquet',
    'person': 'person.parquet',
    'person_details': 'person_details.parquet',
    'person_anime_works': 'person_anime_works.parquet',
    'person_voice_works': 'person_voice_works.parquet',
    'person_alternate_names': 'person_alternate_names.parquet'
}

def get_raw_path(dataset_name: str) -> Path:
    """Returns the absolute path to a raw dataset."""
    filename = RAW_FILES.get(dataset_name)
    if not filename:
        raise ValueError(f"Unknown dataset: {dataset_name}. Available: {list(RAW_FILES.keys())}")
    return RAW_DATA_DIR / filename

def load_raw(dataset_name: str, **kwargs) -> pd.DataFrame | pd_parsers.TextFileReader:
    """Loads a raw dataset using smart loading."""
    path = get_raw_path(dataset_name)
    return load_csv_smart(path, **kwargs)

def load_processed(dataset_name: str) -> pd.DataFrame:
    """Loads a processed dataset (Parquet preferred)."""
    # Assuming processed files match detailed/stats/etc structure
    path = PROCESSED_DATA_DIR / f"{dataset_name}.parquet"
    if not path.exists():
        # Fallback to CSV if parquet doesn't exist
        path_csv = PROCESSED_DATA_DIR / f"{dataset_name}.csv"
        if path_csv.exists():
            return pd.read_csv(path_csv)
        raise FileNotFoundError(f"Processed dataset not found: {dataset_name}")

    return pd.read_parquet(path)
