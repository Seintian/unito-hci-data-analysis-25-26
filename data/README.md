# 💾 Data Workflow & Management

**⚠️ IMPORTANT: DO NOT COMMIT DATA FILES (.csv, .parquet, .zip) TO GIT.**

This directory manages the ingestion and processing of the project's datasets. To ensure collaboration works smoothly without bloating the repository, please follow the workflow below strictly.

## 🔄 The Team Workflow

1.  **Download Raw Data:**
    *   Access the datasets via the official Google Drive Link provided in the assignment.
    *   Unzip the contents into the `/data/raw/` folder.

2.  **Run the Cleaning Pipeline:**
    *   Before starting any analysis, run `/notebooks/01_cleaning.ipynb`.
    *   This script reads CSVs from `/data/raw/`, cleans the data, and saves optimized **.parquet** files to `/data/processed/`.

3.  **Analyze:**
    *   All analysis notebooks (`/notebooks/02_exploration.ipynb`, `/notebooks/03_story.ipynb`) must strictly load data from `/data/processed/` using `pd.read_parquet()`.
    *   **Never** load files from `/data/raw/` in the story notebook.

## 📂 Folder Definitions

### `raw/` (Read-Only)
*   **Status:** Ignored by Git.
*   **Purpose:** Stores the original, immutable CSV files.
*   **Contents & Semantics:**

#### 🎬 Anime Data
*   **`details.csv`**: Master file. Contains `mal_id` (PK), titles, genres, studios, rating (PG-13 etc.), and synopsis. *Semantic: What is the show?*
*   **`stats.csv`**: Engagement metrics. Contains `watching`, `completed`, `dropped`, and **full score distribution** (1-10). *Semantic: How did the community react?*
*   **`recommendations.csv`**: Similarity graph. `mal_id` -> `recommendation_mal_id`. *Semantic: "If you like X, you'll like Y".*

#### 🦸 Characters
*   **`characters.csv`**: Profiles. `character_mal_id`, names, `about` (bio), `favorites`. *Semantic: Who are they?*
*   **`character_nicknames.csv`**: Search optimization. Links nicknames to IDs.
*   **`character_anime_works.csv`**: Roles. Links Characters to Anime (`Main` vs `Supporting`).

#### 🎙️ People (Staff/VA)
*   **`person_details.csv`**: Biographies of Voice Actors/Staff.
*   **`person_voice_works.csv`**: Cast List. Links People -> Characters. Crucial for "Seiyuu" analysis.
*   **`person_anime_works.csv`**: Staff List. Links People -> Anime (Directors, Musicians).

#### 👥 Users
*   **`profiles.csv`**: Demographics (`gender`, `birthday`). *Semantic: Who is the audience?*
*   **`ratings.csv`**: **LARGEST FILE**. Interactions (`user_id`, `anime_id`, `rating`). *Semantic: Individual taste.*
*   **`favs.csv`**: Top favorites ("Pinned" items).

### `processed/` (Read/Write)
*   **Status:** Ignored by Git.
*   **Format:** `.parquet` (Optimized)
*   **Purpose:** Stores cleaned, merged, and type-casted datasets.

## 🧹 Exhaustive Cleaning Report & Optimization

Based on a deep analysis of the raw datasets, here is the cleaning strategy you **must** implement in `01_cleaning.ipynb`:

### 1. Critical Missing Data (Handle with Care)
*   **`details.csv`**:
    *   **Scores (`score`, `scored_by`)**: ~32% MISSING. These are likely new or obscure entries. **Action**: Do not fill with 0. Keep as `NaN` or filter them out if analyzing "Rated Anime".
    *   **Dates (`end_date`)**: ~61% MISSING. This implies the show is "Currently Airing" or the data is incomplete. **Action**: Handle as "Unknown" or check `status` column.
    *   **Season/Year**: ~77% MISSING. **Action**: Do not rely on these columns. Extract year from `start_date`.
*   **`characters.csv`**:
    *   **Bio (`about`)**: ~80% MISSING. **Action**: Cannot be used for reliable NLP analysis.
*   **`profiles.csv`**:
    *   **Demographics (`birthday`, `gender`)**: 50-65% MISSING. **Action**: Be careful with demographic conclusions; the sample is biased towards those who filled their profile.

### 2. Type Casting Optimizations
*   **Integers**: Many ID columns (`mal_id`) are read as `int64`. Cast to `int32` (or `uint32`) to save 50% memory.
*   **Floats to Ints**: `stats.csv` vote counts (`score_10_votes`) are loaded as floats because of missing values (~1.5%). **Action**: Fill NaNs with 0 and cast to `int32`.
*   **Categoricals**:
    *   `details.csv`: `type` (TV, Movie), `source` (Original, Manga), `rating` (PG-13).
    *   `person_voice_works.csv`: `role` (Main, Supporting), `language` (Japanese).
    *   **Action**: Convert these to `category` dtype immediately.

### 3. Columns to Drop (Noise Reduction)
*   **`url`, `image_url`**: Present in almost every file. Drop unless building a UI.
*   **`website_url`**: 61% missing in `person_details.csv`.
*   **`name_kanji`**: 37% missing in `characters.csv`.

### 4. Partitioning Strategy
*   **`ratings.csv`**: This is the largest file. Save it as a **Partitioned Parquet** dataset (e.g., partitioned by `score` or hashed user ID) if you encounter Out-Of-Memory (OOM) errors during analysis.
