# Configuration Constants

# Chunk size for streaming processing to handle large files (130M+ rows) without OOM
CHUNK_SIZE = 100_000

# Categorical Optimization
CATEGORY_CARDINALITY_THRESHOLD = 10_000
CATEGORY_DENSITY_THRESHOLD = 0.5

# Boolean Optimization
BOOLEAN_MAX_UNIQUE = 3
BOOLEAN_INDICATORS = {'0', '1', 'true', 'false', 't', 'f', 'yes', 'no', 'y', 'n'}

# Datetime Optimization
# ISO-8601 like pattern YYYY-MM-DD
DATETIME_REGEX_PATTERN = r'^\d{4}-\d{2}-\d{2}'
DATETIME_MATCH_THRESHOLD = 0.5

# Quality Thresholds
GHOST_ROW_THRESHOLD = 0.8  # Fraction of nulls to consider a row "ghost"
SAMPLE_VALUE_COUNT = 5     # Number of non-null samples to collect per column

# Primary Key & Cardinality Tracking
MAX_UNIQUE_TRACKING = 10_000 # Max unique values to track for non-PK columns (prevents OOM)
PK_TRACKING_LIMIT = 5_000_000 # Max unique values to track for PK candidates (stops tracking if exceeded)
PK_CANDIDATE_KEYWORDS = {'id', 'mal_id', 'username', 'user_id'}
PK_SUFFIX_KEYWORD = '_id'

# Processing Safety
RAM_SAFETY_FACTOR = 4      # Required RAM multiplier relative to file size for Pyarrow load
PYARROW_BLOCK_SIZE = 10 * 1024 * 1024 # 10 MB blocks for Pyarrow reading
