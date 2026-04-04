"""
Testes automatizados do projeto letterboxd.
Rode com: pytest src/test_projeto.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import cache_miss, carregar_cache, miss_sentinel, salvar_cache
from main import enrich_movies_with_countries, load_watched_csv
from mapa import get_iso3
from stats import gerar_stats
from tmdb import TMDBTemporaryError, _escolher_resultado, _get, buscar_paises


WATCHED_CSV = """Date,Name,Year,Letterboxd URI
2023-01-10,The Godfather,1972,https://boxd.it/abc
2023-03-15,Akira,1988,https://boxd.it/def
2023-07-23,Perfect Blue,1997,https://boxd.it/ghi
2024-02-01,Dune,2021,https://boxd.it/jkl
2024-05-10,Alien,1979,https://boxd.it/mno
"""

RATINGS_CSV = """Date,Name,Year,Letterboxd URI,Rating
2023-01-10,The Godfather,1972,https://boxd.it/abc,5
2023-03-15,Akira,1988,https://boxd.it/def,4.5
2023-07-23,Perfect Blue,1997,https://boxd.it/ghi,5
2024-02-01,Dune,2021,https://boxd.it/jkl,3.5
"""

CACHE_CSV = """Name,Year,Countries
The Godfather,1972,United States of America
Akira,1988,Japan
"""


@pytest.fixture
def watched_csv(tmp_path):
    path = tmp_path / "watched.csv"
    path.write_text(WATCHED_CSV, encoding="utf-8")
    return path


@pytest.fixture
def ratings_csv(tmp_path):
    path = tmp_path / "ratings.csv"
    path.write_text(RATINGS_CSV, encoding="utf-8")
    return path


@pytest.fixture
def cache_csv(tmp_path):
    path = tmp_path / "cache.csv"
    path.write_text(CACHE_CSV, encoding="utf-8")
    return path


class TestCache:
    def test_carregar_cache_existente(self, cache_csv):
        df, cache = carregar_cache(cache_csv)
        assert len(df) == 2
        assert ("The Godfather", "1972") in cache
        assert cache[("Akira", "1988")] == "Japan"

    def test_carregar_cache_inexistente(self, tmp_path):
        df, cache = carregar_cache(tmp_path / "nao_existe.csv")
        assert len(df) == 0
        assert cache == {}

    def test_cache_miss_sentinel(self):
        assert cache_miss("__NOT_FOUND__") is True
        assert cache_miss("Japan") is False
        assert cache_miss("") is False

    def test_miss_sentinel_valor(self):
        assert miss_sentinel() == "__NOT_FOUND__"

    def test_salvar_cache(self, cache_csv, tmp_path):
        df, _ = carregar_cache(cache_csv)
        novos = [{"Name": "Alien", "Year": "1979", "Countries": "United Kingdom"}]
        out = tmp_path / "cache_out.csv"
        salvar_cache(df, novos, out)
        df2, cache = carregar_cache(out)
        assert len(df2) == 3
        assert ("Alien", "1979") in cache

    def test_salvar_cache_vazio_nao_cria_arquivo(self, cache_csv, tmp_path):
        df, _ = carregar_cache(cache_csv)
        out = tmp_path / "nao_criado.csv"
        salvar_cache(df, [], out)
        assert not out.exists()


class TestStats:
    def test_gerar_stats_basico(self, watched_csv, tmp_path):
        out = tmp_path / "stats.json"
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

    def test_gerar_stats_com_ratings(self, watched_csv, ratings_csv, tmp_path):
        out = tmp_path / "stats.json"
        gerar_stats(watched_csv, out, ratings_csv)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["ratings"] is not None
        assert data["ratings"]["total_avaliados"] == 4
        assert data["ratings"]["media_geral"] == round((5 + 4.5 + 5 + 3.5) / 4, 2)

    def test_heatmap_tem_datas_corretas(self, watched_csv, tmp_path):
        out = tmp_path / "stats.json"
        gerar_stats(watched_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "2023-01-10" in data["heatmap"]
        assert data["heatmap"]["2023-01-10"] == 1

    def test_by_year_correto(self, watched_csv, tmp_path):
        out = tmp_path / "stats.json"
        gerar_stats(watched_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["by_year"]["2023"] == 3
        assert data["by_year"]["2024"] == 2

    def test_top_day_correto(self, watched_csv, tmp_path):
        out = tmp_path / "stats.json"
        gerar_stats(watched_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["top_day"]["count"] == 1

    def test_ratings_distribuicao(self, watched_csv, ratings_csv, tmp_path):
        out = tmp_path / "stats.json"
        gerar_stats(watched_csv, out, ratings_csv)
        data = json.loads(out.read_text(encoding="utf-8"))
        dist = data["ratings"]["distribuicao"]
        assert dist["5.0"] == 2
        assert dist["4.5"] == 1
        assert dist["3.5"] == 1

    def test_nota_maxima_lista(self, watched_csv, ratings_csv, tmp_path):
        out = tmp_path / "stats.json"
        gerar_stats(watched_csv, out, ratings_csv)
        data = json.loads(out.read_text(encoding="utf-8"))
        nomes = [filme["name"] for filme in data["ratings"]["nota_maxima"]]
        assert "The Godfather" in nomes
        assert "Perfect Blue" in nomes
        assert "Akira" not in nomes


class TestTmdb:
    def test_escolher_resultado_ano_correto(self):
        resultados = [
            {"id": 1, "release_date": "1972-03-24"},
            {"id": 2, "release_date": "2001-05-10"},
        ]
        assert _escolher_resultado(resultados, "The Godfather", "1972") == 1

    def test_escolher_resultado_tolerancia_um_ano(self):
        resultados = [{"id": 1, "release_date": "1973-01-01"}]
        assert _escolher_resultado(resultados, "Filme X", "1972") == 1

    def test_escolher_resultado_fallback(self):
        resultados = [
            {"id": 99, "release_date": "2010-01-01"},
            {"id": 2, "release_date": "2015-01-01"},
        ]
        assert _escolher_resultado(resultados, "Filme Y", "1972") == 99

    def test_escolher_resultado_sem_ano(self):
        resultados = [{"id": 42, "release_date": "2000-01-01"}]
        assert _escolher_resultado(resultados, "Qualquer", "") == 42

    def test_escolher_resultado_sem_release_date(self):
        resultados = [
            {"id": 1, "release_date": ""},
            {"id": 2, "release_date": "1988-07-16"},
        ]
        assert _escolher_resultado(resultados, "Akira", "1988") == 2

    @patch("tmdb._get")
    def test_buscar_paises_retorna_lista_de_paises(self, mock_get):
        mock_get.side_effect = [
            {"results": [{"id": 10, "release_date": "1999-10-15"}]},
            {"production_countries": [{"name": "United States of America"}]},
        ]
        assert buscar_paises("Fight Club", "1999", "fake-key") == ["United States of America"]

    @patch("tmdb.time.sleep")
    @patch("tmdb.requests.get")
    def test__get_lanca_erro_temporario_apos_retries(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with pytest.raises(TMDBTemporaryError):
            _get("https://example.com", {})

        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2


class TestMain:
    def test_load_watched_csv_valida_colunas(self, tmp_path):
        csv_path = tmp_path / "watched.csv"
        csv_path.write_text("Name\nAkira\n", encoding="utf-8")

        with pytest.raises(ValueError):
            load_watched_csv(csv_path)

    @patch("main.time.sleep")
    @patch("main.buscar_paises", side_effect=TMDBTemporaryError("timeout"))
    def test_enrich_movies_nao_cacheia_falha_temporaria(self, mock_buscar, mock_sleep):
        df = pd.DataFrame([{"Name": "Akira", "Year": "1988"}])
        cache = {}

        novos_registros, filmes_por_pais, paises_distintos = enrich_movies_with_countries(df, cache)

        assert novos_registros == []
        assert filmes_por_pais == {}
        assert paises_distintos == set()
        assert cache == {}
        mock_sleep.assert_not_called()


class TestMapa:
    def test_iso3_paises_comuns(self):
        assert get_iso3("Brazil") == "BRA"
        assert get_iso3("Japan") == "JPN"
        assert get_iso3("France") == "FRA"
        assert get_iso3("Germany") == "DEU"

    def test_iso3_overrides(self):
        assert get_iso3("South Korea") == "KOR"
        assert get_iso3("Russia") == "RUS"
        assert get_iso3("United States of America") == "USA"
        assert get_iso3("Hong Kong") == "HKG"
        assert get_iso3("Taiwan") == "TWN"

    def test_iso3_pais_invalido(self):
        assert get_iso3("Narnia") is None
        assert get_iso3("") is None

    def test_iso3_united_kingdom(self):
        assert get_iso3("United Kingdom") == "GBR"
