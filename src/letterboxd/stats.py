from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)
STATS_SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class TopDay:
    date: str
    count: int


@dataclass(frozen=True, slots=True)
class RatedMovie:
    name: str
    year: str


@dataclass(frozen=True, slots=True)
class RatingsSummary:
    total_avaliados: int
    media_geral: float
    distribuicao: dict[str, int]
    media_por_ano: dict[str, float]
    nota_maxima: list[RatedMovie]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["nota_maxima"] = [asdict(movie) for movie in self.nota_maxima]
        return data


@dataclass(frozen=True, slots=True)
class SourceFiles:
    watched_csv: str
    ratings_csv: str | None
    ratings_included: bool


@dataclass(frozen=True, slots=True)
class StatsPayload:
    schema_version: int
    gerado_em: str
    total: int
    active_years: int
    avg_per_year: int
    top_day: TopDay
    by_year: dict[str, int]
    by_decade: dict[str, int]
    monthly: dict[str, int]
    heatmap: dict[str, int]
    ratings: RatingsSummary | None
    source_files: SourceFiles

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gerado_em": self.gerado_em,
            "total": self.total,
            "active_years": self.active_years,
            "avg_per_year": self.avg_per_year,
            "top_day": asdict(self.top_day),
            "by_year": self.by_year,
            "by_decade": self.by_decade,
            "monthly": self.monthly,
            "heatmap": self.heatmap,
            "ratings": self.ratings.to_dict() if self.ratings else None,
            "source_files": asdict(self.source_files),
        }



def _build_ratings_summary(ratings_path: Path) -> RatingsSummary:
    ratings_df = pd.read_csv(ratings_path, dtype=str).fillna("")
    ratings_df["Rating"] = pd.to_numeric(ratings_df["Rating"], errors="coerce")
    ratings_df["Date"] = pd.to_datetime(ratings_df["Date"], errors="coerce")
    ratings_df = ratings_df.dropna(subset=["Rating", "Date"])
    ratings_df["year"] = ratings_df["Date"].dt.year

    distribution = ratings_df["Rating"].value_counts().sort_index()
    average_by_year = ratings_df.groupby("year")["Rating"].mean().round(2)
    top_rated = ratings_df[ratings_df["Rating"] == 5.0][["Name", "Year"]].head(20)

    summary = RatingsSummary(
        total_avaliados=len(ratings_df),
        media_geral=round(float(ratings_df["Rating"].mean()), 2),
        distribuicao={str(k): int(v) for k, v in distribution.items()},
        media_por_ano={str(k): float(v) for k, v in average_by_year.items()},
        nota_maxima=[RatedMovie(name=str(row["Name"]), year=str(row["Year"])) for _, row in top_rated.iterrows()],
    )
    logger.info("   %s avaliacoes processadas, media %s", summary.total_avaliados, summary.media_geral)
    return summary



def gerar_stats(csv_path: Path, output_path: Path, ratings_path: Path | None = None) -> StatsPayload:
    """Le watched.csv (e opcionalmente ratings.csv) e gera stats.json."""

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["year_watched"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.to_period("M").astype(str)
    df["decade"] = df["Year"].str[:3].fillna("?") + "0s"

    by_year = df["year_watched"].value_counts().sort_index()
    by_decade = df["decade"].value_counts().sort_index()
    monthly = df.groupby("month").size()
    top_day_series = df.groupby("Date").size()
    top_date = top_day_series.idxmax()
    top_count = int(top_day_series.max())

    active_years = int((by_year > 0).sum())
    avg_per_year = round(len(df) / active_years) if active_years else 0

    heatmap = {
        row["Date"].strftime("%Y-%m-%d"): int(row[0])
        for _, row in df.groupby("Date").size().reset_index().iterrows()
    }

    ratings_summary: RatingsSummary | None = None
    resolved_ratings_path = ratings_path if ratings_path and ratings_path.exists() else None
    if resolved_ratings_path:
        ratings_summary = _build_ratings_summary(resolved_ratings_path)

    payload = StatsPayload(
        schema_version=STATS_SCHEMA_VERSION,
        gerado_em=date.today().isoformat(),
        total=len(df),
        active_years=active_years,
        avg_per_year=avg_per_year,
        top_day=TopDay(date=top_date.strftime("%d %b %Y"), count=top_count),
        by_year={str(k): int(v) for k, v in by_year.items()},
        by_decade={str(k): int(v) for k, v in by_decade.items()},
        monthly={str(k): int(v) for k, v in monthly.items()},
        heatmap=heatmap,
        ratings=ratings_summary,
        source_files=SourceFiles(
            watched_csv=csv_path.name,
            ratings_csv=resolved_ratings_path.name if resolved_ratings_path else None,
            ratings_included=resolved_ratings_path is not None,
        ),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("stats.json gerado (%s filmes)", len(df))
    return payload
