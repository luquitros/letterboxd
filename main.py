import pandas as pd
import time
from tqdm import tqdm

from config import TMDB_API_KEY, CSV_PATH, CACHE_PATH, OUTPUT_HTML
from cache import carregar_cache, salvar_cache
from tmdb import buscar_paises
from mapa import gerar_mapa


def main():
    print("📂 Carregando watched.csv...")
    df = pd.read_csv(CSV_PATH)
    print(f"   {len(df)} filmes encontrados.\n")

    cache_df, cache_dict = carregar_cache(CACHE_PATH)

    print("🌐 Consultando TMDB API...")
    novos_registros = []
    todos_paises = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        nome = row["Name"]
        ano = str(int(row["Year"])) if pd.notna(row["Year"]) else ""
        chave = (nome, ano)

        if chave in cache_dict:
            paises_str = cache_dict[chave]
        else:
            paises = buscar_paises(nome, ano, TMDB_API_KEY)
            paises_str = "|".join(paises) if paises else ""
            cache_dict[chave] = paises_str
            novos_registros.append({"Name": nome, "Year": ano, "Countries": paises_str})
            time.sleep(0.25)  
        if paises_str:
            for p in paises_str.split("|"):
                todos_paises.append(p.strip())

    salvar_cache(cache_df, novos_registros, CACHE_PATH)

    print("\n🗺️  Gerando mapa...")
    gerar_mapa(todos_paises, OUTPUT_HTML)


if __name__ == "__main__":
    main()