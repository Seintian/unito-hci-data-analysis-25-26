# 💾 Data Workflow & Management

**⚠️ IMPORTANT: DO NOT COMMIT DATA FILES (.csv, .parquet, .zip) TO GIT.**

This directory manages the ingestion and processing of the project's datasets. To ensure collaboration works smoothly without bloating the repository, please follow the workflow below strictly.

## 🔄 The Team Workflow

1.  **Download Raw Data:**
    * Access the datasets via the official Google Drive Link provided in the assignment.
    * Unzip the contents into the `/data/raw/` folder.

2.  **Run the Cleaning Pipeline:**
    * Before starting any analysis, run `/notebooks/01_cleaning.ipynb`.
    * This script reads CSVs from `/data/raw/`, cleans the data, and saves optimized **.parquet** files to `/data/processed/`.

3.  **Analyze:**
    * All analysis notebooks (`/notebooks/02_exploration.ipynb`, `/notebooks/03_story.ipynb`) must strictly load data from `/data/processed/` using `pd.read_parquet()`.
    * **Never** load files from `/data/raw/` in the story notebook.

## 📂 Folder Definitions

### `raw/` (Read-Only)
* **Status:** Ignored by Git.
* **Purpose:** Stores the original, immutable CSV files downloaded from the source.
* **Contents:**
    * `Characters.csv` (209,963 details)
    * `Character_anime_works.csv` (236,816 roles)
    * `Character_nicknames.csv` (37,080 nicknames)
    * Plus datasets for Actors, Users, and Anime details.

### `processed/` (Read/Write)
* **Status:** Ignored by Git.
* **Format:** `.parquet` (Optimized)
* **Purpose:** Stores the cleaned, merged, and type-casted datasets ready for analysis.
* **Why Parquet?** It is faster to load and preserves data types (integers, dates) automatically, which is essential for our 130M+ data points.
* **Source:** Generated programmatically by `/notebooks/01_cleaning.ipynb`.

### `temp/` (Scratchpad)
* **Status:** Ignored by Git.
* **Purpose:** Stores temporary intermediate files if the cleaning process requires multiple steps (e.g., pickling large objects).
