from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent  
DATA_DIR   = BASE_DIR / "data"
DOCS_DIR   = BASE_DIR / "docs"

TMDB_API_KEY = "70a7a0e353d3c954c5b6438e95805822"
CSV_PATH     = DATA_DIR / "watched.csv"
CACHE_PATH   = DATA_DIR / "tmdb_cache.csv"
OUTPUT_HTML  = DOCS_DIR / "mapa_cinema.html"
STATS_JSON   = DOCS_DIR / "stats.json"
