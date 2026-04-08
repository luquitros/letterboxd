from dataclasses import dataclass

import pandas as pd
from tqdm import tqdm

from .cache import cache_miss, carregar_cache, miss_sentinel, salvar_cache
from .config import CACHE_PATH, CSV_PATH, DATA_DIR, DOCS_DIR, OUTPUT_HTML, RATINGS_PATH, STATS_JSON, TMDB_API_KEY
from .mapa import gerar_mapa
from .stats import gerar_stats
from .tmdb import TMDBTemporaryError, buscar_paises

REQUIRED_COLUMNS = {"Name", "Year"}
TMDB_RATE_LIMIT_SECONDS = 0.25


@dataclass(slots=True)
class PipelineOptions:
    no_open: bool = False
    stats_only: bool = False
    map_only: bool = False
    refresh_cache: bool = False


@dataclass(slots=True)
class ExecutionSummary:
    cache_hits: int = 0
    api_requests: int = 0
    temporary_failures: int = 0
    without_country: int = 0


@dataclass(slots=True)
class DataArtifacts:
    summary: ExecutionSummary
    total_movies: int
    distinct_countries: int
    stats_generated: bool
    map_generated: bool


def ensure_output_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def validate_runtime_config() -> None:
    if not TMDB_API_KEY:
        raise ValueError(
            "TMDB_API_KEY nao configurada.\n"
            "Crie um arquivo .env na raiz do projeto com:\n"
            "TMDB_API_KEY=sua_chave_aqui"
        )


def normalize_year(value: str) -> str:
    if not value:
        return ""
    return value.split(".", 1)[0].strip()


def load_watched_csv(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {csv_path}\n"
            "Exporte o arquivo watched.csv do Letterboxd e coloque-o na pasta data/."
        )

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"CSV invalido. Colunas obrigatorias ausentes: {missing}\n"
            "Confira se voce selecionou o watched.csv correto do export do Letterboxd."
        )

    if df.empty:
        raise ValueError(
            f"O arquivo {csv_path.name} esta vazio.\n"
            "Verifique se o export do Letterboxd contem filmes assistidos."
        )

    return df


def load_cache_state(refresh_cache: bool):
    if refresh_cache:
        empty_df = pd.DataFrame(columns=["Name", "Year", "Countries"])
        return empty_df, {}

    return carregar_cache(CACHE_PATH)


def enrich_movies_with_countries(
    df: pd.DataFrame,
    cache_dict: dict[tuple[str, str], str],
    *,
    logger,
    sleep_fn,
    buscar_paises_fn=buscar_paises,
):
    novos_registros: list[dict] = []
    paises_distintos: set[str] = set()
    filmes_por_pais: dict[str, list[str]] = {}
    summary = ExecutionSummary()

    for row in tqdm(df.itertuples(index=False), total=len(df)):
        nome = str(getattr(row, "Name", "")).strip()
        ano = normalize_year(str(getattr(row, "Year", "")))
        chave = (nome, ano)

        if chave in cache_dict:
            paises_str = cache_dict[chave]
            summary.cache_hits += 1
        else:
            summary.api_requests += 1
            try:
                paises = buscar_paises_fn(nome, ano, TMDB_API_KEY)
            except TMDBTemporaryError as exc:
                summary.temporary_failures += 1
                logger.warning("   Falha temporaria ao consultar TMDB para '%s' (%s): %s", nome, ano or "?", exc)
                continue

            paises_str = "|".join(paises) if paises else miss_sentinel()
            cache_dict[chave] = paises_str
            novos_registros.append({"Name": nome, "Year": ano, "Countries": paises_str})
            sleep_fn(TMDB_RATE_LIMIT_SECONDS)

        if cache_miss(paises_str) or not paises_str:
            summary.without_country += 1
            continue

        for pais in paises_str.split("|"):
            pais = pais.strip()
            if not pais:
                continue
            paises_distintos.add(pais)
            filmes_por_pais.setdefault(pais, []).append(nome)

    return novos_registros, filmes_por_pais, paises_distintos, summary


def generate_map_artifact(filmes_por_pais: dict[str, list[str]], logger) -> None:
    logger.info("\nGerando mapa...")
    gerar_mapa({pais: len(filmes) for pais, filmes in filmes_por_pais.items()}, str(OUTPUT_HTML))


def generate_stats_artifact(logger) -> None:
    logger.info("\nGerando stats.json...")
    ratings_path = RATINGS_PATH if RATINGS_PATH.exists() else None
    if ratings_path:
        logger.info("   ratings.csv encontrado, incluindo avaliacoes...")
    else:
        logger.info("   ratings.csv nao encontrado, gerando stats sem avaliacoes...")
    gerar_stats(CSV_PATH, STATS_JSON, ratings_path)


def generate_data_artifacts(options: PipelineOptions, logger, sleep_fn) -> DataArtifacts:
    ensure_output_dirs()
    validate_runtime_config()

    logger.info("Carregando watched.csv...")
    df = load_watched_csv(CSV_PATH)
    logger.info("   %s filmes encontrados.\n", len(df))

    if options.refresh_cache:
        logger.info("Refresh de cache ativado: ignorando cache atual da TMDB.")
    cache_df, cache_dict = load_cache_state(options.refresh_cache)

    logger.info("Consultando TMDB API...")
    novos_registros, filmes_por_pais, paises_distintos, summary = enrich_movies_with_countries(
        df,
        cache_dict,
        logger=logger,
        sleep_fn=sleep_fn,
    )

    salvar_cache(cache_df, novos_registros, CACHE_PATH)
    logger.info("\n   %s paises distintos encontrados.", len(paises_distintos))

    map_generated = False
    stats_generated = False

    if not options.stats_only:
        generate_map_artifact(filmes_por_pais, logger)
        map_generated = True

    if not options.map_only:
        generate_stats_artifact(logger)
        stats_generated = True

    return DataArtifacts(
        summary=summary,
        total_movies=len(df),
        distinct_countries=len(paises_distintos),
        stats_generated=stats_generated,
        map_generated=map_generated,
    )
