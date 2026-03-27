import json
import pandas as pd
from datetime import date
from pathlib import Path


def gerar_stats(csv_path: Path, output_path: Path) -> None:
    """Lê o watched.csv e gera stats.json com todos os dados do dashboard."""

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df["Date"]   = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    df["year_watched"] = df["Date"].dt.year
    df["month"]        = df["Date"].dt.to_period("M").astype(str)
    df["decade"]       = df["Year"].str[:3].fillna("?") + "0s"

    by_year   = df["year_watched"].value_counts().sort_index()
    by_decade = df["decade"].value_counts().sort_index()
    monthly   = df.groupby("month").size()

    top_day   = df.groupby("Date").size()
    top_date  = top_day.idxmax()
    top_count = int(top_day.max())

    active_years = int((by_year > 0).sum())
    avg_per_year = round(len(df) / active_years) if active_years else 0

    stats = {
        "gerado_em":    date.today().isoformat(),
        "total":        len(df),
        "active_years": active_years,
        "avg_per_year": avg_per_year,
        "top_day": {
            "date":  top_date.strftime("%d %b %Y"),
            "count": top_count,
        },
        "by_year":   {str(k): int(v) for k, v in by_year.items()},
        "by_decade": {str(k): int(v) for k, v in by_decade.items()},
        "monthly":   {str(k): int(v) for k, v in monthly.items()},
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"✅ stats.json gerado em '{output_path}' ({len(df)} filmes)")
