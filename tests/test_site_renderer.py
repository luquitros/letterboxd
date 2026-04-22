import pytest

from letterboxd.config import AppConfig
from letterboxd.site_renderer import load_stats_payload, render_docs_pages


def test_render_docs_pages_embute_stats_e_copia_paginas(workspace_tmp_path):
    template_dir = workspace_tmp_path / "templates"
    docs_dir = workspace_tmp_path / "docs"
    data_dir = workspace_tmp_path / "data"
    stats_path = docs_dir / "stats.json"
    template_dir.mkdir()
    docs_dir.mkdir()
    data_dir.mkdir()

    (template_dir / "index.html").write_text(
        '<script id="embedded-stats" type="application/json">{{EMBEDDED_STATS}}</script>',
        encoding="utf-8",
    )
    (template_dir / "dashboard.html").write_text(
        '<script id="embedded-stats" type="application/json">{{EMBEDDED_STATS}}</script>',
        encoding="utf-8",
    )
    (template_dir / "wrapped_generator.html").write_text("wrapped static", encoding="utf-8")
    stats_path.write_text('{"total": 10}', encoding="utf-8")

    config = AppConfig(
        base_dir=workspace_tmp_path,
        data_dir=data_dir,
        docs_dir=docs_dir,
        tmdb_api_key="",
        cache_ttl_days=0,
        csv_path=data_dir / "watched.csv",
        ratings_path=data_dir / "ratings.csv",
        cache_path=data_dir / "tmdb_cache.csv",
        output_html=docs_dir / "mapa_cinema.html",
        stats_json=stats_path,
    )

    import letterboxd.site_renderer as site_renderer_module

    original_template_dir = site_renderer_module.TEMPLATE_DIR
    site_renderer_module.TEMPLATE_DIR = template_dir
    try:
        render_docs_pages(config=config)
    finally:
        site_renderer_module.TEMPLATE_DIR = original_template_dir

    assert '{"total": 10}' in (docs_dir / "index.html").read_text(encoding="utf-8")
    assert '{"total": 10}' in (docs_dir / "dashboard.html").read_text(encoding="utf-8")
    assert (docs_dir / "wrapped_generator.html").read_text(encoding="utf-8") == "wrapped static"


def test_load_stats_payload_falha_quando_arquivo_nao_existe(workspace_tmp_path):
    docs_dir = workspace_tmp_path / "docs"
    data_dir = workspace_tmp_path / "data"
    docs_dir.mkdir()
    data_dir.mkdir()
    config = AppConfig(
        base_dir=workspace_tmp_path,
        data_dir=data_dir,
        docs_dir=docs_dir,
        tmdb_api_key="",
        cache_ttl_days=0,
        csv_path=data_dir / "watched.csv",
        ratings_path=data_dir / "ratings.csv",
        cache_path=data_dir / "tmdb_cache.csv",
        output_html=docs_dir / "mapa_cinema.html",
        stats_json=docs_dir / "stats.json",
    )

    with pytest.raises(FileNotFoundError):
        load_stats_payload(config)


def test_load_stats_payload_falha_quando_json_invalido(workspace_tmp_path):
    docs_dir = workspace_tmp_path / "docs"
    data_dir = workspace_tmp_path / "data"
    docs_dir.mkdir()
    data_dir.mkdir()
    stats_path = docs_dir / "stats.json"
    stats_path.write_text('{"total":', encoding="utf-8")

    config = AppConfig(
        base_dir=workspace_tmp_path,
        data_dir=data_dir,
        docs_dir=docs_dir,
        tmdb_api_key="",
        cache_ttl_days=0,
        csv_path=data_dir / "watched.csv",
        ratings_path=data_dir / "ratings.csv",
        cache_path=data_dir / "tmdb_cache.csv",
        output_html=docs_dir / "mapa_cinema.html",
        stats_json=stats_path,
    )

    with pytest.raises(ValueError):
        load_stats_payload(config)
