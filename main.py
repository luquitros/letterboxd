import time
import pandas as pd
from tqdm import tqdm

from config import TMDB_API_KEY, CSV_PATH, CACHE_PATH, OUTPUT_HTML
from cache import carregar_cache, salvar_cache, cache_miss, miss_sentinel
from tmdb import buscar_paises
from mapa import gerar_mapa


def main() -> None:
    print(" Carregando watched.csv...")
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    print(f"   {len(df)} filmes encontrados.\n")

    cache_df, cache_dict = carregar_cache(CACHE_PATH)

    print(" Consultando TMDB API...")
    novos_registros: list[dict] = []
    todos_paises: list[str] = []
    filmes_por_pais: dict[str, list[str]] = {}   

    for _, row in tqdm(df.iterrows(), total=len(df)):
        nome = row["Name"]
        ano = row["Year"].split(".")[0] if row["Year"] else ""  
        chave = (nome, ano)

        if chave in cache_dict:
            paises_str = cache_dict[chave]
        else:
            paises = buscar_paises(nome, ano, TMDB_API_KEY)
            paises_str = "|".join(paises) if paises else miss_sentinel()
            cache_dict[chave] = paises_str
            novos_registros.append({"Name": nome, "Year": ano, "Countries": paises_str})
            time.sleep(0.25)

        if cache_miss(paises_str) or not paises_str:
            continue

        for p in paises_str.split("|"):
            p = p.strip()
            if p:
                todos_paises.append(p)
                filmes_por_pais.setdefault(p, []).append(nome)

    salvar_cache(cache_df, novos_registros, CACHE_PATH)

    print(f"\n   {len(set(todos_paises))} países distintos encontrados.")
    print("\n  Gerando mapa...")
    gerar_mapa(filmes_por_pais, OUTPUT_HTML)


if __name__ == "__main__":
    main()