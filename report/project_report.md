# Anime Data Analysis Project Report

## Introduction

This report outlines the technical implementation and design decisions for the "Anime Data Analysis" project. The goal was to process a large-scale anime dataset (incorporating user ratings, details, and statistics), uncover hidden patterns through exploratory analysis, and craft compelling data-driven narratives. The solution prioritizes performance, reproducibility, and modular design.

---

## 1. Data Definition & Cleaning

### Solution

**Design and Motivations:**
To handle the scale of the data—specifically the 120M+ rows in `ratings.csv`—we implemented a **Parallelized Streaming Pipeline**. Instead of loading the entire dataset into RAM, which would cause instability, we process the file in chunks. Each chunk is handled by a separate CPU core using `joblib`, cleaned, and immediately written to disk in the optimized Parquet format.
We introduced a progressive `GLOBAL_ID_MAP` to ensure referential integrity. As we clean the master `details.csv` file, we build a set of valid IDs. When processing `ratings.csv`, we filter out votes for non-existent anime (orphans) or remap IDs if duplicates were merged, ensuring the final relational model is consistent.

### Issues

The primary challenge was **Memory Management**. Initial attempts to load raw CSVs fully into DataFrame structures exceeded the available 16 GB RAM limit. Additionally, the raw data contained "dirty" HTML entities and inconsistent text encoding.

### Requirements

The solution meets the requirement for **efficient data cleaning** by reducing memory usage by approximately 80% through aggressive type downcasting (e.g., converting strings to Categoricals, `float64` to `float32`). It satisfies the need for **automation** as the entire pipeline runs programmatically without manual intervention.

### Limitations

**Global Deduplication** on the `ratings.csv` was skipped. Sorting 120M rows to identify perfect duplicates was prohibitively expensive ($ O(N \log N) $) for negligible gain (0 duplicates found in a 15M row sample).

---

## 2. Data Analysis (Exploration)

### Solution

**Design and Motivations:**
We adopted a multi-layered approach to exploration:

1. **Statistical Moments**: Beyond simple averages, we analyzed Variance and Skewness to understand the data shape.
2. **Dimensionality Reduction (PCA)**: We used Principal Component Analysis to squash 5+ dimensions (Score, Popularity, Episodes, Year, Favorites) into 3D space, allowing us to visualize the "landscape" of anime and identify natural clusters.
3. **Unsupervised Clustering (K-Means)**: We automatically grouped anime into archetypes (e.g., "Mega Hits", "Niche Classics") to prove that distinct tiers of success exist.

### Issues

**High Dimensionality and Overplotting**. Standard scatter plots of 20,000+ anime result in unintelligible blobs. We solved this using **Hexbin Density Plots**, which clearly show where the majority of titles cluster (average score, low popularity) versus the outliers.

### Requirements

This complies with the requirement to **find patterns and relationships**. We successfully identified that popularity does not strictly correlate with quality (Score vs Members relationship is complex/non-linear), as revealed by the **Predictive Power Score (PPS)** matrix which detects non-linear predictive strength that standard correlation misses.

### Limitations

**Interpretation of PCA**: While PCA simplifies visualization, the resulting axes (PC1, PC2) are abstract combinations of features, making them harder to explain to non-technical stakeholders compared to raw variables.

---

## 3. Data Storytelling

### Solution

**Design and Motivations:**
The project features three distinct narrative tracks, each exploring a different facet of the anime industry:

#### A. Chronicles of Immortality (Longevity)

* **Focus**: Analyzes the survival and cultural persistence of anime series.
* **Method**: We filtered for TV series and calculated `duration_days` to find shows that remain relevant decades after release.
* **Key Finding**: A "Power Law" of longevity exists, where a tiny fraction of "Immortal" series (e.g., *One Piece*, *Gintama*) dominate engagement, while the vast majority fade quickly.

#### B. The Midas Touch (Hype vs. Quality)

* **Focus**: Investigates the relationship between Popularity (Hype) and Quality (Score), and the impact of staff "brands".
* **Method**:
  * **Hype Ratio**: Analyzed the ratio of Members to Score to detect "Marketing Triumphs/Content Failures".
  * **Studio DNA**: Used Ridgeline plots to categorize studios into "Boutiques" (consistent high quality, e.g., Kyoto Animation) vs. "Factories" (high variance).
  * **VORD (Value Over Replacement Director)**: Adapted Sabermetrics to quantify how much a specific director (e.g., Hayao Miyazaki) raises the average score of a studio's output.

#### C. Origins and Adaptations (Source Material)

* **Focus**: Explores the ecosystem of source materials (Manga vs. Novels vs. Originals).
* **Method**: Grouped sources into macro-categories to analyze market share and success rates.
* **Key Finding**: "Original" anime are the riskiest investment (high volatility/variance - they either flop or define a generation), whereas Manga adaptations are the "Blue Chips" (consistent, safe, pre-tested audiences).

### Issues

**Data Noise**: The initial dataset included thousands of single-episode OVAs or "Special" shorts that skewed the longevity statistics. Cleaning these required precise filtering logic to distinguish between a short-lived series and a one-shot production.

### Requirements

We met the requirement to **tell a story** by structuring the analysis as a multi-perspective investigation—historical (Chronicles), industrial (Midas), and evolutionary (Origins).

### Limitations

**Survivorship Bias**: Older anime that were unpopular might not even be in the database, potentially skewing the historical data to look "better" than it was (only the hits are remembered and recorded).

---

## 4. Code Modularization

### Solution

**Design and Motivations:**
We adhered to the **DRY (Don't Repeat Yourself)** principle by extracting common logic into a shared `src/` package.

* **`src/utils.py`**: Contains `load_csv_smart`, a robust loader that attempts to use the high-performance **PyArrow** engine for speed but automatically falls back to the standard Pandas C-engine if memory is low or errors occur.
* **`src/data.py`**: Manages path definitions and standardizes I/O operations, ensuring all notebooks read from the exact same raw/processed directories.

### Issues

**Library Compatibility**: PyArrow is fast but strict. It crashes on malformed CSV lines that Pandas usually tolerates. Our `load_csv_smart` wrapper solves this by wrapping the PyArrow call in a try-catch block, ensuring robustness without sacrificing speed for clean files.

### Requirements

The design satisfies the **Code Quality** requirement. The notebooks are thin and readable because complex I/O and plotting logic is hidden in imported modules.

### Limitations

**Dependency Management**: The smart loader introduces a dependency on `psutil` to check RAM before deciding which engine to use. If this library is missing, it skips the optimization check (though it still works).

---

## Conclusions

We effectively transformed a raw, messy dataset into a structured relational model. Our analysis revealed that the anime industry follows a "Power Law" distribution: a tiny fraction of "Immortal" shows garner the vast majority of engagement. The technical implementation proved that modular pipelines using modern tools (Parquet, PyArrow) are essential for handling datasets of this magnitude on standard hardware.

## Division of Work

[TO BE COMPLETED BY USER - MANDATORY]

## Extra Information

**Execution Requirements:**

* Python 3.10+
* Key Libraries: `pandas`, `numpy`, `plotly` (for interactive charts), `scikit-learn` (for PCA/Clustering), `pyarrow` (for fast I/O), `psutil`.
* Unzip the raw data into `data/raw/` before running the `01_cleaning.ipynb` notebook.
