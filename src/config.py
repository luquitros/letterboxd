import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"


def _load_dotenv() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
CSV_PATH = DATA_DIR / "watched.csv"
CACHE_PATH = DATA_DIR / "tmdb_cache.csv"
OUTPUT_HTML = DOCS_DIR / "mapa_cinema.html"
STATS_JSON = DOCS_DIR / "stats.json"
