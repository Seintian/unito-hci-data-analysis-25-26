# HCI Assignment 2025-2026: Anime Data Storytelling

**Università di Torino - Dipartimento di Informatica**
*Corso di Interazione Uomo-Macchina (HCI)*

## 📖 Panoramica del Progetto

Questa repository ospita il codice e l'analisi per l'Assignment di HCI 2025-2026. L'obiettivo è progettare un sistema in grado di supportare l'analisi e la visualizzazione di un dataset massiccio (oltre 130 milioni di punti dati) che copre anime, personaggi, doppiatori e interazioni degli utenti.

### 🎯 L'Obiettivo: Raccontare una Storia

I dati da soli non parlano. Come da requisiti dell'assignment, questo progetto va oltre le semplici statistiche per **raccontare una storia**. Puntiamo a fornire a fan e giornalisti insight significativi identificando pattern, trend e outlier nell'industria degli anime.

## 📂 Struttura della Repository

* **`notebooks/`**: L'ambiente principale di analisi.
    * `01_cleaning.ipynb`: La pipeline ETL (Raw CSV -> Cleaned Parquet/CSV).
    * `02_exploration.ipynb`: Analisi Esplorativa dei Dati (EDA).
    * `03_story.ipynb`: Il notebook finale per la narrazione e la visualizzazione.
* **`data/`**: Archivio per i dataset. **Vedi `data/README.it.md` per le istruzioni sul workflow.**
* **`src/`**: Moduli Python condivisi e funzioni di supporto.

## 🛠️ Stack Tecnologico

Questo progetto è costruito usando **Python** e gestito da **uv** per una risoluzione delle dipendenze ad alte prestazioni.

### Librerie Principali

* **Manipolazione Dati:** `pandas` (usando il backend `pyarrow` per le performance)
* **Visualizzazione Statica:** `seaborn`, `matplotlib`
* **Analisi Geospaziale:** `geopandas`, `folium`
* **Ambiente:** `jupyterlab`

### Gestione dei Pacchetti

Usiamo [uv](https://github.com/astral-sh/uv) per gestire le versioni di Python e le dipendenze. Questo assicura che ogni membro del team usi esattamente le stesse versioni delle librerie (tramite `uv.lock`) e velocizza significativamente i tempi di installazione.

## 🚀 Per Iniziare

**1. Clona la repository:**

```bash
git clone https://github.com/seintian/unito-hci-data-analysis-25-26.git
cd unito-hci-data-analysis-25-26
```

**2. Installa le Dipendenze (via uv):** Questo comando installerà automaticamente la versione corretta di Python e tutte le dipendenze bloccate (locked).

```bash
# Se non hai ancora installato uv:
# curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync
```

**3. Setup dei Dati:** Naviga nella directory `data/` e segui le istruzioni in `data/README.it.md` per scaricare e preparare i dataset dalla fonte.

**4. Esegui il Progetto:** Per lanciare Jupyter Lab all'interno dell'ambiente gestito:

```bash
uv run jupyter lab
```
