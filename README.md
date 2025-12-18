# HCI Assignment 2025-2026: Anime Data Storytelling

**University of Turin - Department of Computer Science**
*Human-Computer Interaction Module*

## 📖 Project Overview

This repository hosts the code and analysis for the 2025-2026 HCI Assignment. The objective is to design a system capable of supporting analysis and visualization of a massive dataset (over 130 million data points) covering anime, characters, actors, and user interactions.

### 🎯 The Goal: Telling a Story

Data alone does not speak. As per the assignment requirements, this project moves beyond simple statistics to **tell a story**. We aim to provide fans and journalists with meaningful insights by identifying patterns, trends, and outliers in the anime industry.

## 📂 Repository Structure

* **`notebooks/`**: The core analysis environment.
    * `01_cleaning.ipynb`: The ETL pipeline (Raw CSV -> Cleaned Parquet/CSV).
    * `02_exploration.ipynb`: Exploratory Data Analysis (EDA).
    * `03_story.ipynb`: The final narrative and visualization notebook.
* **`data/`**: Storage for datasets. **See `data/README.md` for workflow instructions.**
* **`src/`**: Shared Python modules and helper functions.

## 🛠️ Technology Stack

This project is built using **Python** and managed by **uv** for high-performance dependency resolution.

### Core Libraries

* **Data Manipulation:** `pandas` (using `pyarrow` backend for performance)
* **Static Visualization:** `seaborn`, `matplotlib`
* **Geospatial Analysis:** `geopandas`, `folium`
* **Environment:** `jupyterlab`

### Package Management

We use [uv](https://github.com/astral-sh/uv) to manage Python versions and dependencies. This ensures that every team member uses the exact same library versions (via `uv.lock`) and speeds up installation times significantly.

## 🚀 Getting Started

**1. Clone the repository:**

```bash
git clone https://github.com/seintian/unito-hci-data-analysis-25-26.git
cd unito-hci-data-analysis-25-26
```

**2. Install Dependencies (via uv):** This command will automatically install the correct Python version and all locked dependencies.

```bash
# If you don't have uv installed yet:
# curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync
```

**3. Setup Data:** Navigate to the `data/` directory and follow the instructions in `data/README.md` to download and prepare the datasets from the source.

**4. Run the Project:** To launch Jupyter Lab inside the managed environment:

```bash
uv run jupyter lab
```
