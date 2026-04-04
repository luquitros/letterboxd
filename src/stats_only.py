
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stats import gerar_stats

BASE_DIR     = Path(__file__).parent.parent
DATA_DIR     = BASE_DIR / "data"
DOCS_DIR     = BASE_DIR / "docs"
CSV_PATH     = DATA_DIR / "watched.csv"
RATINGS_PATH = DATA_DIR / "ratings.csv"
STATS_JSON   = DOCS_DIR / "stats.json"

if __name__ == "__main__":
    ratings = RATINGS_PATH if RATINGS_PATH.exists() else None
    if not CSV_PATH.exists():
        print(f"ERRO: {CSV_PATH} não encontrado.")
        sys.exit(1)
    gerar_stats(CSV_PATH, STATS_JSON, ratings)