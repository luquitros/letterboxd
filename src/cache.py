import logging
from pathlib import Path

import pandas as pd

_MISS_SENTINEL = "__NOT_FOUND__"
logger = logging.getLogger(__name__)


def _build_cache_key(name: str, year: str) -> tuple[str, str]:
    return name.strip(), year.strip()


def carregar_cache(cache_path: Path) -> tuple[pd.DataFrame, dict[tuple[str, str], str]]:
    try:
        df = pd.read_csv(cache_path, dtype=str).fillna("")
        cache_dict = {
            _build_cache_key(row["Name"], row["Year"]): row["Countries"]
            for _, row in df.iterrows()
        }
        return df, cache_dict
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Year", "Countries"]), {}


def cache_miss(paises_str: str) -> bool:
    return paises_str == _MISS_SENTINEL


def salvar_cache(cache_df: pd.DataFrame, novos_registros: list[dict], cache_path: Path) -> None:
    if not novos_registros:
        return

    novo_cache = pd.concat(
        [cache_df, pd.DataFrame(novos_registros)],
        ignore_index=True,
    )
    novo_cache.to_csv(cache_path, index=False)
    acertos = sum(1 for registro in novos_registros if registro["Countries"] != _MISS_SENTINEL)
    falhas = len(novos_registros) - acertos
    logger.info(" Cache atualizado: %s encontrados, %s nao encontrados.", acertos, falhas)


def miss_sentinel() -> str:
    return _MISS_SENTINEL
