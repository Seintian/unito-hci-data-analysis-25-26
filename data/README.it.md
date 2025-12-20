# 💾 Gestione e Workflow dei Dati

**⚠️ IMPORTANTE: NON COMMITTARE I FILE DI DATI (.csv, .parquet, .zip) SU GIT.**

Questa directory gestisce l'ingestione e l'elaborazione dei dataset del progetto. Per garantire che la collaborazione funzioni senza problemi e senza appesantire la repository, segui rigorosamente il workflow descritto di seguito.

## 🔄 Il Workflow del Team

1.  **Scarica i Dati Grezzi (Raw):**
    *   Accedi ai dataset tramite il Link Google Drive ufficiale fornito nell'assignment.
    *   Decomprimi il contenuto nella cartella `/data/raw/`.

2.  **Esegui la Pipeline di Pulizia:**
    *   Prima di iniziare qualsiasi analisi, esegui `/notebooks/01_cleaning.ipynb`.
    *   Questo script legge i CSV da `/data/raw/`, pulisce i dati e salva i file ottimizzati **.parquet** in `/data/processed/`.

3.  **Analizza:**
    *   Tutti i notebook di analisi (`/notebooks/02_exploration.ipynb`, `/notebooks/03_story.ipynb`) devono caricare rigorosamente i dati da `/data/processed/` usando `pd.read_parquet()`.
    *   **Non caricare mai** file da `/data/raw/` nel notebook della storia (story notebook).

## 📂 Definizioni delle Cartelle

### `raw/` (Sola Lettura)
*   **Status:** Ignorato da Git.
*   **Scopo:** Contiene i file CSV originali e immutabili.
*   **Contenuto e Semantica:**

#### 🎬 Dati Anime
*   **`details.csv`**: File master. Contiene `mal_id` (PK), titoli, generi, studi, rating (PG-13 ecc.) e sinossi. *Semantica: Di cosa parla lo show?*
*   **`stats.csv`**: Metriche di coinvolgimento. Contiene conteggi di `watching`, `completed`, `dropped`, e la **distribuzione completa dei voti** (1-10). *Semantica: Come ha reagito la community?*
*   **`recommendations.csv`**: Grafo di similarità. `mal_id` -> `recommendation_mal_id`. *Semantica: "Se ti piace X, ti piacerà Y".*

#### 🦸 Personaggi (Characters)
*   **`characters.csv`**: Profili. `character_mal_id`, nomi, `about` (bio), `favorites`. *Semantica: Chi sono?*
*   **`character_nicknames.csv`**: Ottimizzazione ricerca. Collega nickname agli ID.
*   **`character_anime_works.csv`**: Ruoli. Collega Personaggi ad Anime (`Main` vs `Supporting`).

#### 🎙️ Persone (Staff/Doppiatori)
*   **`person_details.csv`**: Biografie di Doppiatori (VA) e Staff.
*   **`person_voice_works.csv`**: Cast List. Collega Persone -> Personaggi. Cruciale per l'analisi dei "Seiyuu".
*   **`person_anime_works.csv`**: Staff List. Collega Persone -> Anime (Registi, Musicisti).

#### 👥 Utenti
*   **`profiles.csv`**: Demografica (`gender`, `birthday`). *Semantica: Chi è il pubblico?*
*   **`ratings.csv`**: **FILE PIÙ GRANDE**. Interazioni (`user_id`, `anime_id`, `rating`). *Semantica: Gusto individuale.*
*   **`favs.csv`**: Top favoriti (Elementi "Pinnati").

### `processed/` (Lettura/Scrittura)
*   **Status:** Ignorato da Git.
*   **Formato:** `.parquet` (Ottimizzato)
*   **Scopo:** Contiene dataset puliti, uniti e con tipi corretti (type-casted).

## 🧹 Report di Pulizia Esaustiva e Ottimizzazione

Basato su un'analisi approfondita dei dataset grezzi, ecco la strategia di pulizia che **devi** implementare in `01_cleaning.ipynb`:

### 1. Dati Mancanti Critici (Maneggiare con Cura)
*   **`details.csv`**:
    *   **Voti (`score`, `scored_by`)**: ~32% MANCANTI. Probabilmente show nuovi o oscuri. **Azione**: Non riempire con 0. Mantieni `NaN` o filtrali se analizzi "Anime Valutati".
    *   **Date (`end_date`)**: ~61% MANCANTI. Indica show "In Corso" o dati incompleti. **Azione**: Tratta come "Sconosciuto" o controlla la colonna `status`.
    *   **Stagione/Anno**: ~77% MANCANTI. **Azione**: Non fare affidamento su queste colonne. Estrai l'anno da `start_date`.
*   **`characters.csv`**:
    *   **Bio (`about`)**: ~80% MANCANTI. **Azione**: Non utilizzabile per analisi NLP affidabili.
*   **`profiles.csv`**:
    *   **Demografica (`birthday`, `gender`)**: 50-65% MANCANTI. **Azione**: Attenzione alle conclusioni demografiche; il campione è distorto verso chi ha compilato il profilo.

### 2. Ottimizzazione dei Tipi
*   **Interi**: Molte colonne ID (`mal_id`) sono lette come `int64`. Converti in `int32` (o `uint32`) per risparmiare il 50% di memoria.
*   **Float a Interi**: I conteggi dei voti in `stats.csv` (`score_10_votes`) sono caricati come float a causa di valori mancanti (~1.5%). **Azione**: Riempi i NaN con 0 e converti in `int32`.
*   **Categorici**:
    *   `details.csv`: `type` (TV, Movie), `source` (Original, Manga), `rating` (PG-13).
    *   `person_voice_works.csv`: `role` (Main, Supporting), `language` (Japanese).
    *   **Azione**: Converti questi in `category` dtype immediatamente.

### 3. Colonne da Rimuovere (Riduzione Rumore)
*   **`url`, `image_url`**: Presenti in quasi tutti i file. Rimuovile a meno che tu non stia costruendo una UI.
*   **`website_url`**: 61% mancante in `person_details.csv`.
*   **`name_kanji`**: 37% mancante in `characters.csv`.

### 4. Strategia di Partizionamento
*   **`ratings.csv`**: Questo è il file più grande. Salvalo come dataset **Parquet Partizionato** (es. partizionato per `score` o user ID hash) se incontri errori di memoria (OOM) durante l'analisi.
