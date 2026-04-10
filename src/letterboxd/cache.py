import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

_MISS_SENTINEL = "__NOT_FOUND__"
_CACHE_COLUMNS = ["Name", "Year", "Countries", "FetchedAt"]
logger = logging.getLogger(__name__)


def _build_cache_key(name: str, year: str) -> tuple[str, str]:
    return name.strip(), year.strip()


def _normalize_cache_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in _CACHE_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    return normalized[_CACHE_COLUMNS].fillna("")


def _apply_ttl(df: pd.DataFrame, ttl_days: int, now: datetime) -> pd.DataFrame:
    if ttl_days <= 0 or df.empty or "FetchedAt" not in df.columns:
        return df

    fetched_at = pd.to_datetime(df["FetchedAt"], errors="coerce", utc=True)
    cutoff = now - timedelta(days=ttl_days)
    keep_mask = fetched_at.isna() | (fetched_at >= cutoff)
    return df.loc[keep_mask].copy()


def carregar_cache(
    cache_path: Path,
    *,
    ttl_days: int = 0,
    now: datetime | None = None,
) -> tuple[pd.DataFrame, dict[tuple[str, str], str]]:
    try:
        df = pd.read_csv(cache_path, dtype=str).fillna("")
    except FileNotFoundError:
        return pd.DataFrame(columns=_CACHE_COLUMNS), {}

    normalized = _normalize_cache_frame(df)
    current_time = now or datetime.now(UTC)
    filtered = _apply_ttl(normalized, ttl_days, current_time)
    cache_dict = {
        _build_cache_key(row["Name"], row["Year"]): row["Countries"]
        for _, row in filtered.iterrows()
    }
    return filtered, cache_dict


def cache_miss(paises_str: str) -> bool:
    return paises_str == _MISS_SENTINEL


def salvar_cache(cache_df: pd.DataFrame, novos_registros: list[dict], cache_path: Path) -> None:
    if not novos_registros:
        return

    timestamp = datetime.now(UTC).isoformat()
    normalized_records = []
    for registro in novos_registros:
        enriched = dict(registro)
        enriched.setdefault("FetchedAt", timestamp)
        normalized_records.append(enriched)

    existing = _normalize_cache_frame(cache_df) if not cache_df.empty else pd.DataFrame(columns=_CACHE_COLUMNS)
    novo_cache = pd.concat([existing, pd.DataFrame(normalized_records)], ignore_index=True)
    novo_cache.to_csv(cache_path, index=False)
    acertos = sum(1 for registro in normalized_records if registro["Countries"] != _MISS_SENTINEL)
    falhas = len(normalized_records) - acertos
    logger.info(" Cache atualizado: %s encontrados, %s nao encontrados.", acertos, falhas)


def limpar_cache(cache_path: Path) -> bool:
    if not cache_path.exists():
        return False
    cache_path.unlink()
    return True


def miss_sentinel() -> str:
    return _MISS_SENTINEL
