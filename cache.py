import pandas as pd

def carregar_cache(cache_path):
    try:
        df = pd.read_csv(cache_path)
        return df, {
            (row["Name"], str(row["Year"])): row["Countries"]
            for _, row in df.iterrows()
        }
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Year", "Countries"]), {}


def salvar_cache(cache_df, novos_registros, cache_path):
    if novos_registros:
        novo_cache = pd.concat(
            [cache_df, pd.DataFrame(novos_registros)],
            ignore_index=True
        )
        novo_cache.to_csv(cache_path, index=False)
        print(f"💾 Cache atualizado com {len(novos_registros)} novos filmes.")