from letterboxd.build_data import main as build_data_main
from letterboxd.build_site import main as build_site_main
from letterboxd.pipeline import DataArtifacts, ExecutionSummary


def test_build_data_main_usa_pipeline_de_dados(monkeypatch):
    calls: list[str] = []
    artifacts = DataArtifacts(
        summary=ExecutionSummary(),
        total_movies=1,
        distinct_countries=1,
        stats_generated=True,
        map_generated=True,
    )

    monkeypatch.setattr("letterboxd.build_data.configure_logging", lambda: calls.append("logging"))
    monkeypatch.setattr("letterboxd.build_data.generate_data_artifacts", lambda *_args, **_kwargs: artifacts)
    monkeypatch.setattr("letterboxd.build_data.log_summary", lambda *_args, **_kwargs: calls.append("summary"))

    assert build_data_main([]) == 0
    assert calls == ["logging", "summary"]


def test_build_site_main_renderiza_e_abre_quando_pedido(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr("letterboxd.build_site.configure_logging", lambda: calls.append("logging"))
    monkeypatch.setattr("letterboxd.build_site.render_site", lambda: calls.append("render"))
    monkeypatch.setattr("letterboxd.build_site.open_dashboard", lambda: calls.append("open"))

    assert build_site_main(["--open"]) == 0
    assert calls == ["logging", "render", "open"]
