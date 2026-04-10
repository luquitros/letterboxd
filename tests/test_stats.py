import json

from letterboxd.stats import gerar_stats


def test_gerar_stats_basico(watched_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["total"] == 5
    assert data["active_years"] == 2
    assert "by_year" in data
    assert "by_decade" in data
    assert "monthly" in data
    assert "heatmap" in data
    assert data["ratings"] is None



def test_gerar_stats_com_ratings(watched_csv, ratings_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out, ratings_csv)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["ratings"] is not None
    assert data["ratings"]["total_avaliados"] == 4
    assert data["ratings"]["media_geral"] == round((5 + 4.5 + 5 + 3.5) / 4, 2)



def test_heatmap_tem_datas_corretas(watched_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "2023-01-10" in data["heatmap"]
    assert data["heatmap"]["2023-01-10"] == 1



def test_by_year_correto(watched_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["by_year"]["2023"] == 3
    assert data["by_year"]["2024"] == 2



def test_top_day_correto(watched_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["top_day"]["count"] == 1



def test_ratings_distribuicao(watched_csv, ratings_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out, ratings_csv)
    data = json.loads(out.read_text(encoding="utf-8"))
    dist = data["ratings"]["distribuicao"]
    assert dist["5.0"] == 2
    assert dist["4.5"] == 1
    assert dist["3.5"] == 1



def test_nota_maxima_lista(watched_csv, ratings_csv, workspace_tmp_path):
    out = workspace_tmp_path / "stats.json"
    gerar_stats(watched_csv, out, ratings_csv)
    data = json.loads(out.read_text(encoding="utf-8"))
    nomes = [filme["name"] for filme in data["ratings"]["nota_maxima"]]
    assert "The Godfather" in nomes
    assert "Perfect Blue" in nomes
    assert "Akira" not in nomes
