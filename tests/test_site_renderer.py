from letterboxd.site_renderer import render_docs_pages


def test_render_docs_pages_embute_stats_e_copia_paginas(tmp_path, monkeypatch):
    template_dir = tmp_path / "templates"
    docs_dir = tmp_path / "docs"
    stats_path = tmp_path / "stats.json"
    template_dir.mkdir()
    docs_dir.mkdir()

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

    monkeypatch.setattr("letterboxd.site_renderer.TEMPLATE_DIR", template_dir)
    monkeypatch.setattr("letterboxd.site_renderer.DOCS_DIR", docs_dir)
    monkeypatch.setattr("letterboxd.site_renderer.STATS_JSON", stats_path)

    render_docs_pages()

    assert '{"total": 10}' in (docs_dir / "index.html").read_text(encoding="utf-8")
    assert '{"total": 10}' in (docs_dir / "dashboard.html").read_text(encoding="utf-8")
    assert (docs_dir / "wrapped_generator.html").read_text(encoding="utf-8") == "wrapped static"
