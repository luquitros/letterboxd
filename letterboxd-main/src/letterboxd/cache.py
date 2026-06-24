from __future__ import annotations

import logging
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from .models import CacheEntry, CacheKey, TimestampFactory

_MISS_SENTINEL = "__NOT_FOUND__"
_CACHE_COLUMNS = ["Name", "Year", "Countries", "FetchedAt"]
logger = logging.getLogger(__name__)


def _build_cache_key(name: str, year: str) -> CacheKey:
    return name.strip(), year.strip()


def _normalize_cache_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in _CACHE_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    return normalized[_CACHE_COLUMNS].fillna("")


def _deduplicate_cache_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    deduped = df.drop_duplicates(subset=["Name", "Year"], keep="last")
    return deduped.reset_index(drop=True)


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
) -> tuple[pd.DataFrame, dict[CacheKey, str]]:
    try:
        df = pd.read_csv(cache_path, dtype=str).fillna("")
    except FileNotFoundError:
        return pd.DataFrame(columns=_CACHE_COLUMNS), {}
    except pd.errors.ParserError:
        logger.warning(" Cache invalido em %s; ignorando conteudo e recriando arquivo.", cache_path)
        return pd.DataFrame(columns=_CACHE_COLUMNS), {}

    normalized = _normalize_cache_frame(df)
    current_time = now or datetime.now(UTC)
    filtered = _apply_ttl(normalized, ttl_days, current_time)
    deduped = _deduplicate_cache_frame(filtered)
    cache_entries = [CacheEntry.from_mapping(row) for row in deduped.to_dict(orient="records")]
    cache_dict = {entry.cache_key: entry.countries for entry in cache_entries}
    return deduped, cache_dict


def cache_miss(paises_str: str) -> bool:
    return paises_str == _MISS_SENTINEL


def salvar_cache(cache_df: pd.DataFrame, novos_registros: list[dict[str, str]], cache_path: Path) -> None:
    if not novos_registros:
        return

    timestamp = TimestampFactory.now_iso()
    normalized_records = [CacheEntry.from_mapping(registro).to_mapping(fetched_at=timestamp) for registro in novos_registros]

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _normalize_cache_frame(cache_df) if not cache_df.empty else pd.DataFrame(columns=_CACHE_COLUMNS)
    novo_cache = pd.concat([existing, pd.DataFrame(normalized_records)], ignore_index=True)
    deduped = _deduplicate_cache_frame(novo_cache)

    temp_file: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=cache_path.parent,
            prefix=f"{cache_path.stem}_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_file = Path(handle.name)
            deduped.to_csv(handle.name, index=False)
        temp_file.replace(cache_path)
    finally:
        if temp_file is not None and temp_file.exists():
            temp_file.unlink()

    acertos = sum(1 for registro in normalized_records if registro["Countries"] != _MISS_SENTINEL)
    falhas = len(normalized_records) - acertos
    logger.info(" Cache atualizado: %s encontrados, %s nao encontrados.", acertos, falhas)


def limpar_cache(cache_path: Path) -> bool:
    if not cache_path.exists():
        return False
    try:
        cache_path.unlink()
    except OSError:
        logger.warning(" Nao foi possivel remover o cache em %s.", cache_path)
        return False
    return True


def miss_sentinel() -> str:
    return _MISS_SENTINEL
