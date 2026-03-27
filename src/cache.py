import pandas as pd
from pathlib import Path

_MISS_SENTINEL = "__NOT_FOUND__"


def carregar_cache(cache_path: Path) -> tuple[pd.DataFrame, dict]:
    try:
        df = pd.read_csv(cache_path, dtype=str).fillna("")
        cache_dict = {
            (row["Name"], row["Year"]): row["Countries"]
            for _, row in df.iterrows()
        }
        return df, cache_dict
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Year", "Countries"]), {}


def cache_miss(paises_str: str) -> bool:
    return paises_str == _MISS_SENTINEL


def salvar_cache(cache_df: pd.DataFrame, novos_registros: list, cache_path: Path) -> None:
    if not novos_registros:
        return
    novo_cache = pd.concat(
        [cache_df, pd.DataFrame(novos_registros)],
        ignore_index=True,
    )
    novo_cache.to_csv(cache_path, index=False)
    acertos = sum(1 for r in novos_registros if r["Countries"] != _MISS_SENTINEL)
    falhas  = len(novos_registros) - acertos
    print(f" Cache atualizado: {acertos} encontrados, {falhas} não encontrados.")


def miss_sentinel() -> str:
    return _MISS_SENTINEL
