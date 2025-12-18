# 💾 Gestione e Workflow dei Dati

**⚠️ IMPORTANTE: NON COMMIGLIARE I FILE DI DATI (.csv, .parquet, .zip) SU GIT.**

Questa directory gestisce l'ingestione e l'elaborazione dei dataset del progetto. Per garantire che la collaborazione funzioni senza problemi e senza appesantire la repository, segui rigorosamente il workflow descritto di seguito.

## 🔄 Il Workflow del Team

1.  **Scarica i Dati Grezzi (Raw):**
    * Accedi ai dataset tramite il Link Google Drive ufficiale fornito nell'assignment.
    * Decomprimi il contenuto nella cartella `/data/raw/`.

2.  **Esegui la Pipeline di Pulizia:**
    * Prima di iniziare qualsiasi analisi, esegui `/notebooks/01_cleaning.ipynb`.
    * Questo script legge i CSV da `/data/raw/`, pulisce i dati e salva i file ottimizzati **.parquet** in `/data/processed/`.

3.  **Analizza:**
    * Tutti i notebook di analisi (`/notebooks/02_exploration.ipynb`, `/notebooks/03_story.ipynb`) devono caricare rigorosamente i dati da `/data/processed/` usando `pd.read_parquet()`.
    * **Non caricare mai** file da `/data/raw/` nel notebook della storia (story notebook).

## 📂 Definizioni delle Cartelle

### `raw/` (Sola Lettura)
* **Status:** Ignorato da Git.
* **Scopo:** Contiene i file CSV originali e immutabili scaricati dalla fonte.
* **Contenuto:**
    * `Characters.csv` (209,963 dettagli)
    * `Character_anime_works.csv` (236,816 ruoli)
    * `Character_nicknames.csv` (37,080 soprannomi)
    * Più dataset per Attori, Utenti e dettagli Anime.

### `processed/` (Lettura/Scrittura)
* **Status:** Ignorato da Git.
* **Formato:** `.parquet` (Ottimizzato)
* **Scopo:** Contiene i dataset puliti, uniti (merged) e con i tipi corretti (type-casted), pronti per l'analisi.
* **Perché Parquet?** È più veloce da caricare e preserva automaticamente i tipi di dati (interi, date), il che è essenziale per i nostri 130M+ punti dati.
* **Fonte:** Generato programmaticamente da `/notebooks/01_cleaning.ipynb`.

### `temp/` (Area di Appoggio)
* **Status:** Ignorato da Git.
* **Scopo:** Contiene file intermedi temporanei se il processo di pulizia richiede passaggi multipli (ad es. pickling di oggetti grandi).
