from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd
from tqdm import tqdm

from .cache import cache_miss, carregar_cache, limpar_cache, miss_sentinel, salvar_cache
from .config import CONFIG, AppConfig
from .mapa import gerar_mapa
from .models import CacheEntry, CountryAggregation, MovieRecord
from .stats import gerar_stats
from .tmdb import TMDBTemporaryError, buscar_paises

REQUIRED_COLUMNS = {"Name", "Year"}
TMDB_RATE_LIMIT_SECONDS = 0.25


class LoggerLike(Protocol):
    def info(self, msg: str, *args: object) -> None: ...
    def warning(self, msg: str, *args: object) -> None: ...


class SleepFn(Protocol):
    def __call__(self, seconds: float, /) -> object: ...


class CountryLookupFn(Protocol):
    def __call__(self, name: str, year: str, api_key: str, /) -> list[str]: ...


@dataclass(slots=True)
class PipelineOptions:
    no_open: bool = False
    stats_only: bool = False
    map_only: bool = False
    refresh_cache: bool = False
    clear_cache: bool = False


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



def ensure_output_dirs(config: AppConfig = CONFIG) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.docs_dir.mkdir(parents=True, exist_ok=True)



def validate_runtime_config(config: AppConfig = CONFIG) -> None:
    if not config.tmdb_api_key:
        raise ValueError(
            "TMDB_API_KEY nao configurada.\n"
            "Crie um arquivo .env na raiz do projeto com:\n"
            "TMDB_API_KEY=sua_chave_aqui"
        )



def normalize_year(value: str) -> str:
    if not value:
        return ""
    return value.split(".", 1)[0].strip()



def load_watched_csv(csv_path: Path) -> pd.DataFrame:
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



def load_cache_state(
    options: PipelineOptions,
    config: AppConfig,
    logger: LoggerLike,
) -> tuple[pd.DataFrame, dict[tuple[str, str], str]]:
    if options.clear_cache:
        removed = limpar_cache(config.cache_path)
        logger.info("Cache fisico removido: %s", "sim" if removed else "nao havia arquivo")

    if options.refresh_cache or options.clear_cache:
        empty_df = pd.DataFrame(columns=["Name", "Year", "Countries", "FetchedAt"])
        return empty_df, {}

    return carregar_cache(config.cache_path, ttl_days=config.cache_ttl_days)



def enrich_movies_with_countries(
    df: pd.DataFrame,
    cache_dict: dict[tuple[str, str], str],
    *,
    tmdb_api_key: str,
    logger: LoggerLike,
    sleep_fn: SleepFn,
    buscar_paises_fn: CountryLookupFn = buscar_paises,
) -> tuple[list[dict[str, str]], dict[str, list[str]], set[str], ExecutionSummary]:
    aggregation = CountryAggregation(new_cache_entries=[], movies_by_country={}, distinct_countries=set())
    summary = ExecutionSummary()

    for row in tqdm(df.itertuples(index=False), total=len(df)):
        movie = MovieRecord.from_row(row)
        chave = movie.cache_key

        if chave in cache_dict:
            paises_str = cache_dict[chave]
            summary.cache_hits += 1
        else:
            summary.api_requests += 1
            try:
                paises = buscar_paises_fn(movie.name, movie.year, tmdb_api_key)
            except TMDBTemporaryError as exc:
                summary.temporary_failures += 1
                logger.warning("   Falha temporaria ao consultar TMDB para '%s' (%s): %s", movie.name, movie.year or "?", exc)
                continue

            paises_str = "|".join(paises) if paises else miss_sentinel()
            cache_dict[chave] = paises_str
            aggregation.new_cache_entries.append(CacheEntry(name=movie.name, year=movie.year, countries=paises_str))
            sleep_fn(TMDB_RATE_LIMIT_SECONDS)

        if cache_miss(paises_str) or not paises_str:
            summary.without_country += 1
            continue

        for pais in paises_str.split("|"):
            country_name = pais.strip()
            if not country_name:
                continue
            aggregation.distinct_countries.add(country_name)
            aggregation.movies_by_country.setdefault(country_name, []).append(movie.name)

    return (
        [entry.to_mapping() for entry in aggregation.new_cache_entries],
        aggregation.movies_by_country,
        aggregation.distinct_countries,
        summary,
    )



def generate_map_artifact(
    filmes_por_pais: dict[str, list[str]],
    logger: LoggerLike,
    config: AppConfig = CONFIG,
) -> None:
    logger.info("\nGerando mapa...")
    gerar_mapa({pais: len(filmes) for pais, filmes in filmes_por_pais.items()}, str(config.output_html))



def generate_stats_artifact(logger: LoggerLike, config: AppConfig = CONFIG) -> None:
    logger.info("\nGerando stats.json...")
    ratings_path = config.ratings_path if config.ratings_path.exists() else None
    if ratings_path:
        logger.info("   ratings.csv encontrado, incluindo avaliacoes...")
    else:
        logger.info("   ratings.csv nao encontrado, gerando stats sem avaliacoes...")
    gerar_stats(config.csv_path, config.stats_json, ratings_path)



def generate_data_artifacts(
    options: PipelineOptions,
    logger: LoggerLike,
    sleep_fn: SleepFn,
    *,
    config: AppConfig = CONFIG,
) -> DataArtifacts:
    ensure_output_dirs(config)
    validate_runtime_config(config)

    logger.info("Carregando watched.csv...")
    df = load_watched_csv(config.csv_path)
    logger.info("   %s filmes encontrados.\n", len(df))

    if options.refresh_cache:
        logger.info("Refresh de cache ativado: ignorando cache atual da TMDB.")
    cache_df, cache_dict = load_cache_state(options, config, logger)

    logger.info("Consultando TMDB API...")
    novos_registros, filmes_por_pais, paises_distintos, summary = enrich_movies_with_countries(
        df,
        cache_dict,
        tmdb_api_key=config.tmdb_api_key,
        logger=logger,
        sleep_fn=sleep_fn,
    )

    salvar_cache(cache_df, novos_registros, config.cache_path)
    logger.info("\n   %s paises distintos encontrados.", len(paises_distintos))

    map_generated = False
    stats_generated = False

    if not options.stats_only:
        generate_map_artifact(filmes_por_pais, logger, config)
        map_generated = True

    if not options.map_only:
        generate_stats_artifact(logger, config)
        stats_generated = True

    return DataArtifacts(
        summary=summary,
        total_movies=len(df),
        distinct_countries=len(paises_distintos),
        stats_generated=stats_generated,
        map_generated=map_generated,
    )
