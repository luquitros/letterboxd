import time
import requests


_MAX_RETRIES = 3
_RETRY_DELAY = 2.0   


def _get(url: str, params: dict) -> dict | None:
    """GET com retry automático em caso de 429 ou erros de rede."""
    for attempt in range(_MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 429:
                wait = _RETRY_DELAY * (2 ** attempt)
                print(f"    Rate limit atingido. Aguardando {wait:.0f}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY)
            else:
                raise e
    return None


def buscar_paises(titulo: str, ano: str, api_key: str) -> list[str]:
    """
    Busca países de produção de um filme na TMDB.

    Validação de ano: só aceita o primeiro resultado se o ano de lançamento
    bater com o esperado (±1 ano de tolerância para lançamentos internacionais).
    Se não bater, percorre os demais resultados antes de desistir.
    """
    params_busca = {
        "api_key": api_key,
        "query": titulo,
        "language": "pt-BR",
    }
    if ano:
        params_busca["year"] = ano

    try:
        data = _get("https://api.themoviedb.org/3/search/movie", params_busca)
        if not data:
            return []

        resultados = data.get("results", [])
        if not resultados:
            return []

        movie_id = _escolher_resultado(resultados, titulo, ano)
        if movie_id is None:
            return []

        detalhes = _get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            {"api_key": api_key},
        )
        if not detalhes:
            return []

        return [p["name"] for p in detalhes.get("production_countries", [])]

    except Exception as e:
        print(f"  ❌ Erro em '{titulo}' ({ano}): {e}")
        return []


def _escolher_resultado(resultados: list, titulo: str, ano: str) -> int | None:
    """
    Percorre os resultados da busca e retorna o ID do filme cujo
    release_date bate com o ano esperado (±1).  Se nenhum bater,
    retorna o ID do primeiro resultado como fallback.
    """
    if not ano:
        return resultados[0]["id"]

    try:
        ano_int = int(ano)
    except ValueError:
        return resultados[0]["id"]

    
    for res in resultados:
        release = res.get("release_date", "")
        if not release:
            continue
        try:
            ano_res = int(release[:4])
            if abs(ano_res - ano_int) <= 1:
                return res["id"]
        except ValueError:
            continue

    
    return resultados[0]["id"]