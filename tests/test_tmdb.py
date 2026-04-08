from unittest.mock import patch

import pytest
import requests

from letterboxd.tmdb import TMDBTemporaryError, _escolher_resultado, _get, buscar_paises


def test_escolher_resultado_ano_correto():
    resultados = [
        {"id": 1, "release_date": "1972-03-24"},
        {"id": 2, "release_date": "2001-05-10"},
    ]
    assert _escolher_resultado(resultados, "The Godfather", "1972") == 1


def test_escolher_resultado_tolerancia_um_ano():
    resultados = [{"id": 1, "release_date": "1973-01-01"}]
    assert _escolher_resultado(resultados, "Filme X", "1972") == 1


def test_escolher_resultado_fallback():
    resultados = [
        {"id": 99, "release_date": "2010-01-01"},
        {"id": 2, "release_date": "2015-01-01"},
    ]
    assert _escolher_resultado(resultados, "Filme Y", "1972") == 99


def test_escolher_resultado_sem_ano():
    resultados = [{"id": 42, "release_date": "2000-01-01"}]
    assert _escolher_resultado(resultados, "Qualquer", "") == 42


def test_escolher_resultado_sem_release_date():
    resultados = [
        {"id": 1, "release_date": ""},
        {"id": 2, "release_date": "1988-07-16"},
    ]
    assert _escolher_resultado(resultados, "Akira", "1988") == 2


@patch("letterboxd.tmdb._get")
def test_buscar_paises_retorna_lista_de_paises(mock_get):
    mock_get.side_effect = [
        {"results": [{"id": 10, "release_date": "1999-10-15"}]},
        {"production_countries": [{"name": "United States of America"}]},
    ]
    assert buscar_paises("Fight Club", "1999", "fake-key") == ["United States of America"]


@patch("letterboxd.tmdb.time.sleep")
@patch("letterboxd.tmdb.requests.get")
def test_get_lanca_erro_temporario_apos_retries(mock_get, mock_sleep):
    mock_get.side_effect = requests.exceptions.Timeout("timeout")

    with pytest.raises(TMDBTemporaryError):
        _get("https://example.com", {})

    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2
