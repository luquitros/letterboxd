from pathlib import Path

from letterboxd.config import AppConfig, load_config


def test_load_config_resolve_dirs_relativos(monkeypatch):
    monkeypatch.setenv("LETTERBOXD_DATA_DIR", "custom-data")
    monkeypatch.setenv("LETTERBOXD_DOCS_DIR", "custom-docs")
    monkeypatch.setenv("TMDB_API_KEY", "abc123")
    monkeypatch.setenv("LETTERBOXD_CACHE_TTL_DAYS", "7")

    config = load_config()

    assert isinstance(config, AppConfig)
    assert config.tmdb_api_key == "abc123"
    assert config.cache_ttl_days == 7
    assert config.data_dir.name == "custom-data"
    assert config.docs_dir.name == "custom-docs"
    assert config.csv_path == config.data_dir / "watched.csv"
    assert config.ratings_path == config.data_dir / "ratings.csv"
    assert config.stats_json == config.docs_dir / "stats.json"



def test_load_config_usa_defaults_quando_env_ausente(monkeypatch):
    monkeypatch.delenv("LETTERBOXD_DATA_DIR", raising=False)
    monkeypatch.delenv("LETTERBOXD_DOCS_DIR", raising=False)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    monkeypatch.delenv("LETTERBOXD_CACHE_TTL_DAYS", raising=False)
    monkeypatch.setattr("letterboxd.config._load_dotenv", lambda _base_dir: None)

    config = load_config()

    assert config.base_dir == Path(__file__).resolve().parents[1]
    assert config.data_dir == config.base_dir / "data"
    assert config.docs_dir == config.base_dir / "docs"
    assert config.tmdb_api_key == ""
    assert config.cache_ttl_days == 0
