import json
import pandas as pd
from datetime import date
from pathlib import Path


def gerar_stats(csv_path: Path, output_path: Path, ratings_path: Path | None = None) -> None:
    """Le watched.csv (e opcionalmente ratings.csv) e gera stats.json."""

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df["Date"]         = pd.to_datetime(df["Date"], errors="coerce")
    df                 = df.dropna(subset=["Date"])
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

    heatmap = {
        row["Date"].strftime("%Y-%m-%d"): int(row[0])
        for _, row in df.groupby("Date").size().reset_index().iterrows()
    }

    stats = {
        "gerado_em":    date.today().isoformat(),
        "total":        len(df),
        "active_years": active_years,
        "avg_per_year": avg_per_year,
        "top_day":      {"date": top_date.strftime("%d %b %Y"), "count": top_count},
        "by_year":      {str(k): int(v) for k, v in by_year.items()},
        "by_decade":    {str(k): int(v) for k, v in by_decade.items()},
        "monthly":      {str(k): int(v) for k, v in monthly.items()},
        "heatmap":      heatmap,
        "ratings":      None,
    }

    if ratings_path and Path(ratings_path).exists():
        rt = pd.read_csv(ratings_path, dtype=str).fillna("")
        rt["Rating"] = pd.to_numeric(rt["Rating"], errors="coerce")
        rt["Date"]   = pd.to_datetime(rt["Date"], errors="coerce")
        rt           = rt.dropna(subset=["Rating", "Date"])
        rt["year"]   = rt["Date"].dt.year

        dist        = rt["Rating"].value_counts().sort_index()
        avg_by_year = rt.groupby("year")["Rating"].mean().round(2)
        top5        = rt[rt["Rating"] == 5.0][["Name", "Year"]].head(20)

        stats["ratings"] = {
            "total_avaliados": len(rt),
            "media_geral":     round(float(rt["Rating"].mean()), 2),
            "distribuicao":    {str(k): int(v) for k, v in dist.items()},
            "media_por_ano":   {str(k): float(v) for k, v in avg_by_year.items()},
            "nota_maxima":     [
                {"name": row["Name"], "year": row["Year"]}
                for _, row in top5.iterrows()
            ],
        }
        print(f"   {len(rt)} avaliacoes processadas, media {stats['ratings']['media_geral']}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"stats.json gerado ({len(df)} filmes)")