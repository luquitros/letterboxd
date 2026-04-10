from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

type CacheKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class MovieRecord:
    name: str
    year: str

    @classmethod
    def from_row(cls, row: object) -> MovieRecord:
        name = str(getattr(row, "Name", "")).strip()
        raw_year = str(getattr(row, "Year", ""))
        year = raw_year.split(".", 1)[0].strip() if raw_year else ""
        return cls(name=name, year=year)

    @property
    def cache_key(self) -> CacheKey:
        return self.name, self.year


@dataclass(frozen=True, slots=True)
class CacheEntry:
    name: str
    year: str
    countries: str
    fetched_at: str = ""

    @property
    def cache_key(self) -> CacheKey:
        return self.name.strip(), self.year.strip()

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> CacheEntry:
        return cls(
            name=str(row.get("Name", "")).strip(),
            year=str(row.get("Year", "")).strip(),
            countries=str(row.get("Countries", "")),
            fetched_at=str(row.get("FetchedAt", "")),
        )

    def to_mapping(self, *, fetched_at: str | None = None) -> dict[str, str]:
        return {
            "Name": self.name,
            "Year": self.year,
            "Countries": self.countries,
            "FetchedAt": fetched_at if fetched_at is not None else self.fetched_at,
        }


@dataclass(slots=True)
class CountryAggregation:
    new_cache_entries: list[CacheEntry]
    movies_by_country: dict[str, list[str]]
    distinct_countries: set[str]


@dataclass(frozen=True, slots=True)
class TimestampFactory:
    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).isoformat()
