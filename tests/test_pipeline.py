import importlib
from unittest.mock import patch

import pandas as pd
import pytest

from letterboxd.config import AppConfig
from letterboxd.main import enrich_movies_with_countries, load_watched_csv, parse_args, run_pipeline
from letterboxd.pipeline import DataArtifacts, ExecutionSummary, PipelineOptions, generate_data_artifacts
from letterboxd.tmdb import TMDBTemporaryError


def _stub_config(tmp_dir) -> AppConfig:
    return AppConfig(
        base_dir=tmp_dir,
        data_dir=tmp_dir / "data",
        docs_dir=tmp_dir / "docs",
        tmdb_api_key="fake-key",
        cache_ttl_days=0,
        csv_path=tmp_dir / "data" / "watched.csv",
        ratings_path=tmp_dir / "data" / "ratings.csv",
        cache_path=tmp_dir / "data" / "tmdb_cache.csv",
        output_html=tmp_dir / "docs" / "mapa_cinema.html",
        stats_json=tmp_dir / "docs" / "stats.json",
    )



def test_parse_args_no_open():
    args = parse_args(["--no-open"])
    assert args.no_open is True
    assert args.stats_only is False
    assert args.map_only is False



def test_parse_args_stats_only():
    args = parse_args(["--stats-only"])
    assert args.stats_only is True
    assert args.map_only is False



def test_parse_args_map_only():
    args = parse_args(["--map-only"])
    assert args.map_only is True
    assert args.stats_only is False



def test_parse_args_refresh_cache():
    args = parse_args(["--refresh-cache"])
    assert args.refresh_cache is True



def test_parse_args_clear_cache():
    args = parse_args(["--clear-cache"])
    assert args.clear_cache is True



def test_parse_args_rejeita_modos_conflitantes():
    with pytest.raises(SystemExit):
        parse_args(["--stats-only", "--map-only"])



def test_load_watched_csv_valida_colunas(workspace_tmp_path):
    csv_path = workspace_tmp_path / "watched.csv"
    csv_path.write_text("Name\nAkira\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_watched_csv(csv_path)


@patch("letterboxd.main.time.sleep")
@patch("letterboxd.main.buscar_paises", side_effect=TMDBTemporaryError("timeout"))
def test_enrich_movies_nao_cacheia_falha_temporaria(mock_buscar, mock_sleep, workspace_tmp_path):
    df = pd.DataFrame([{"Name": "Akira", "Year": "1988"}])
    cache = {}
    config = _stub_config(workspace_tmp_path)

    novos_registros, filmes_por_pais, paises_distintos, summary = enrich_movies_with_countries(df, cache, config=config)

    assert novos_registros == []
    assert filmes_por_pais == {}
    assert paises_distintos == set()
    assert summary.temporary_failures == 1
    assert summary.api_requests == 1
    assert cache == {}
    mock_sleep.assert_not_called()



def test_generate_data_artifacts_separa_dados_da_renderizacao(monkeypatch, workspace_tmp_path):
    df = pd.DataFrame([{"Name": "Akira", "Year": "1988"}])
    cache_df = pd.DataFrame(columns=["Name", "Year", "Countries", "FetchedAt"])
    summary = ExecutionSummary(cache_hits=1)
    calls: list[str] = []
    config = _stub_config(workspace_tmp_path)

    monkeypatch.setattr("letterboxd.pipeline.validate_runtime_config", lambda _config: calls.append("validate"))
    monkeypatch.setattr("letterboxd.pipeline.ensure_output_dirs", lambda _config: calls.append("dirs"))
    monkeypatch.setattr("letterboxd.pipeline.load_watched_csv", lambda _path: df)
    monkeypatch.setattr("letterboxd.pipeline.load_cache_state", lambda _options, _config, _logger: (cache_df, {}))
    monkeypatch.setattr(
        "letterboxd.pipeline.enrich_movies_with_countries",
        lambda *_args, **_kwargs: ([], {"Japan": ["Akira"]}, {"Japan"}, summary),
    )
    monkeypatch.setattr("letterboxd.pipeline.salvar_cache", lambda *_args, **_kwargs: calls.append("save_cache"))
    monkeypatch.setattr("letterboxd.pipeline.generate_map_artifact", lambda *_args, **_kwargs: calls.append("map"))
    monkeypatch.setattr("letterboxd.pipeline.generate_stats_artifact", lambda *_args, **_kwargs: calls.append("stats"))

    logger = type("LoggerStub", (), {"info": lambda *args, **kwargs: None})()

    artifacts = generate_data_artifacts(PipelineOptions(), logger=logger, sleep_fn=lambda _seconds: None, config=config)

    assert artifacts == DataArtifacts(
        summary=summary,
        total_movies=1,
        distinct_countries=1,
        stats_generated=True,
        map_generated=True,
    )
    assert calls == ["dirs", "validate", "save_cache", "map", "stats"]



def test_generate_data_artifacts_limpa_cache_quando_pedido(monkeypatch, workspace_tmp_path):
    config = _stub_config(workspace_tmp_path)
    logger = type("LoggerStub", (), {"info": lambda *args, **kwargs: None})()
    calls: list[str] = []

    monkeypatch.setattr("letterboxd.pipeline.ensure_output_dirs", lambda _config: None)
    monkeypatch.setattr("letterboxd.pipeline.validate_runtime_config", lambda _config: None)
    monkeypatch.setattr("letterboxd.pipeline.load_watched_csv", lambda _path: pd.DataFrame([{"Name": "Akira", "Year": "1988"}]))
    monkeypatch.setattr(
        "letterboxd.pipeline.load_cache_state",
        lambda options, _config, _logger: (calls.append("clear") or pd.DataFrame(columns=["Name", "Year", "Countries", "FetchedAt"]), {}),
    )
    monkeypatch.setattr(
        "letterboxd.pipeline.enrich_movies_with_countries",
        lambda *_args, **_kwargs: ([], {}, set(), ExecutionSummary()),
    )
    monkeypatch.setattr("letterboxd.pipeline.salvar_cache", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("letterboxd.pipeline.generate_map_artifact", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("letterboxd.pipeline.generate_stats_artifact", lambda *_args, **_kwargs: None)

    generate_data_artifacts(PipelineOptions(clear_cache=True), logger=logger, sleep_fn=lambda _seconds: None, config=config)

    assert calls == ["clear"]



def test_run_pipeline_renderiza_site_so_quando_stats_existe(monkeypatch):
    calls: list[str] = []
    artifacts = DataArtifacts(
        summary=ExecutionSummary(),
        total_movies=1,
        distinct_countries=1,
        stats_generated=False,
        map_generated=True,
    )
    main_module = importlib.import_module("letterboxd.main")

    monkeypatch.setattr(main_module.pipeline, "generate_data_artifacts", lambda *_args, **_kwargs: artifacts)
    monkeypatch.setattr(main_module, "render_site", lambda **_kwargs: calls.append("render"))
    monkeypatch.setattr(main_module, "open_dashboard", lambda **_kwargs: calls.append("open"))
    monkeypatch.setattr(main_module, "log_summary", lambda *_args, **_kwargs: calls.append("summary"))

    run_pipeline(PipelineOptions(map_only=True))

    assert calls == ["summary"]
