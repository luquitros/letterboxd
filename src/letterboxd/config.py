import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    base_dir: Path
    data_dir: Path
    docs_dir: Path
    tmdb_api_key: str
    cache_ttl_days: int
    csv_path: Path
    ratings_path: Path
    cache_path: Path
    output_html: Path
    stats_json: Path


BASE_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv(base_dir: Path) -> None:
    env_path = base_dir / ".env"
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


def _resolve_dir(base_dir: Path, env_name: str, default: Path) -> Path:
    value = os.getenv(env_name, "").strip()
    if not value:
        return default

    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()


def _read_int(env_name: str, default: int) -> int:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{env_name} precisa ser um inteiro valido.") from exc
    return max(value, 0)


def load_config() -> AppConfig:
    _load_dotenv(BASE_DIR)

    data_dir = _resolve_dir(BASE_DIR, "LETTERBOXD_DATA_DIR", BASE_DIR / "data")
    docs_dir = _resolve_dir(BASE_DIR, "LETTERBOXD_DOCS_DIR", BASE_DIR / "docs")
    tmdb_api_key = os.getenv("TMDB_API_KEY", "").strip()
    cache_ttl_days = _read_int("LETTERBOXD_CACHE_TTL_DAYS", 0)

    return AppConfig(
        base_dir=BASE_DIR,
        data_dir=data_dir,
        docs_dir=docs_dir,
        tmdb_api_key=tmdb_api_key,
        cache_ttl_days=cache_ttl_days,
        csv_path=data_dir / "watched.csv",
        ratings_path=data_dir / "ratings.csv",
        cache_path=data_dir / "tmdb_cache.csv",
        output_html=docs_dir / "mapa_cinema.html",
        stats_json=docs_dir / "stats.json",
    )


CONFIG = load_config()
DATA_DIR = CONFIG.data_dir
DOCS_DIR = CONFIG.docs_dir
TMDB_API_KEY = CONFIG.tmdb_api_key
CSV_PATH = CONFIG.csv_path
CACHE_PATH = CONFIG.cache_path
OUTPUT_HTML = CONFIG.output_html
STATS_JSON = CONFIG.stats_json
RATINGS_PATH = CONFIG.ratings_path
