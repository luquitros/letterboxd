import requests


def buscar_paises(titulo, ano, api_key):
    """Busca países de produção de um filme na TMDB."""
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key,
        "query": titulo,
        "year": ano,
        "language": "pt-BR"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        resultados = r.json().get("results", [])
        if not resultados:
            return []

        movie_id = resultados[0]["id"]

        url_detalhes = f"https://api.themoviedb.org/3/movie/{movie_id}"
        r2 = requests.get(url_detalhes, params={"api_key": api_key}, timeout=10)
        r2.raise_for_status()
        detalhes = r2.json()

        return [p["name"] for p in detalhes.get("production_countries", [])]

    except Exception as e:
        print(f"  Erro em '{titulo}' ({ano}): {e}")
        return []