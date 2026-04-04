import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from tqdm import tqdm

from cache import carregar_cache, salvar_cache, cache_miss, miss_sentinel
from config import TMDB_API_KEY, CSV_PATH, CACHE_PATH, OUTPUT_HTML, STATS_JSON, DOCS_DIR, DATA_DIR
from mapa import gerar_mapa
from stats import gerar_stats
from tmdb import buscar_paises

RATINGS_PATH = DATA_DIR / "ratings.csv"
REQUIRED_COLUMNS = {"Name", "Year"}
TMDB_RATE_LIMIT_SECONDS = 0.25

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_year(value: str) -> str:
    if not value:
        return ""
    return value.split(".", 1)[0].strip()


def load_watched_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV invalido. Colunas obrigatorias ausentes: {missing}")

    return df


def enrich_movies_with_countries(
    df: pd.DataFrame,
    cache_dict: dict[tuple[str, str], str],
) -> tuple[list[dict], dict[str, list[str]], set[str]]:
    novos_registros: list[dict] = []
    paises_distintos: set[str] = set()
    filmes_por_pais: dict[str, list[str]] = {}

    for row in tqdm(df.itertuples(index=False), total=len(df)):
        nome = getattr(row, "Name", "")
        ano = normalize_year(getattr(row, "Year", ""))
        chave = (nome, ano)

        if chave in cache_dict:
            paises_str = cache_dict[chave]
        else:
            try:
                paises = buscar_paises(nome, ano, TMDB_API_KEY)
            except Exception as exc:
                logger.warning(
                    "   Falha ao consultar TMDB para '%s' (%s): %s",
                    nome,
                    ano or "?",
                    exc,
                )
                continue

            paises_str = "|".join(paises) if paises else miss_sentinel()
            cache_dict[chave] = paises_str
            novos_registros.append({"Name": nome, "Year": ano, "Countries": paises_str})
            time.sleep(TMDB_RATE_LIMIT_SECONDS)

        if cache_miss(paises_str) or not paises_str:
            continue

        for pais in paises_str.split("|"):
            pais = pais.strip()
            if not pais:
                continue
            paises_distintos.add(pais)
            filmes_por_pais.setdefault(pais, []).append(nome)

    return novos_registros, filmes_por_pais, paises_distintos


def generate_outputs(filmes_por_pais: dict[str, list[str]]) -> None:
    logger.info("\nGerando mapa...")
    gerar_mapa({pais: len(filmes) for pais, filmes in filmes_por_pais.items()}, str(OUTPUT_HTML))

    logger.info("\nGerando stats.json...")
    ratings_path = RATINGS_PATH if RATINGS_PATH.exists() else None
    if ratings_path:
        logger.info("   ratings.csv encontrado, incluindo avaliacoes...")
    gerar_stats(CSV_PATH, STATS_JSON, ratings_path)


def main() -> None:
    configure_logging()
    ensure_output_dirs()

    logger.info("Carregando watched.csv...")
    df = load_watched_csv(CSV_PATH)
    logger.info("   %s filmes encontrados.\n", len(df))

    cache_df, cache_dict = carregar_cache(CACHE_PATH)

    logger.info("Consultando TMDB API...")
    novos_registros, filmes_por_pais, paises_distintos = enrich_movies_with_countries(df, cache_dict)

    salvar_cache(cache_df, novos_registros, CACHE_PATH)
    logger.info("\n   %s paises distintos encontrados.", len(paises_distintos))

    generate_outputs(filmes_por_pais)

    logger.info("\nTudo gerado em docs/")


if __name__ == "__main__":
    main()
