import argparse
import logging
import socket
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .cache import cache_miss, carregar_cache, miss_sentinel, salvar_cache
from .config import CACHE_PATH, CSV_PATH, DATA_DIR, DOCS_DIR, OUTPUT_HTML, STATS_JSON, TMDB_API_KEY
from .mapa import gerar_mapa
from .site_renderer import render_docs_pages
from .stats import gerar_stats
from .tmdb import TMDBTemporaryError, buscar_paises

RATINGS_PATH = DATA_DIR / "ratings.csv"
REQUIRED_COLUMNS = {"Name", "Year"}
TMDB_RATE_LIMIT_SECONDS = 0.25
logger = logging.getLogger(__name__)


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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera o dashboard do Letterboxd.")
    parser.add_argument("--no-open", action="store_true", help="Nao abre o dashboard no navegador ao final.")
    parser.add_argument("--stats-only", action="store_true", help="Gera apenas o stats.json e atualiza os HTMLs.")
    parser.add_argument("--map-only", action="store_true", help="Gera apenas o mapa de paises.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignora o cache atual e consulta novamente a TMDB.")
    args = parser.parse_args(argv)

    if args.stats_only and args.map_only:
        parser.error("Use apenas um entre --stats-only e --map-only.")

    return args


def build_options(args: argparse.Namespace) -> PipelineOptions:
    return PipelineOptions(
        no_open=args.no_open,
        stats_only=args.stats_only,
        map_only=args.map_only,
        refresh_cache=args.refresh_cache,
    )


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


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


def load_cache_state(refresh_cache: bool) -> tuple[pd.DataFrame, dict[tuple[str, str], str]]:
    if refresh_cache:
        logger.info("Refresh de cache ativado: ignorando cache atual da TMDB.")
        empty_df = pd.DataFrame(columns=["Name", "Year", "Countries"])
        return empty_df, {}

    return carregar_cache(CACHE_PATH)


def enrich_movies_with_countries(
    df: pd.DataFrame,
    cache_dict: dict[tuple[str, str], str],
) -> tuple[list[dict], dict[str, list[str]], set[str], ExecutionSummary]:
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
                paises = buscar_paises(nome, ano, TMDB_API_KEY)
            except TMDBTemporaryError as exc:
                summary.temporary_failures += 1
                logger.warning("   Falha temporaria ao consultar TMDB para '%s' (%s): %s", nome, ano or "?", exc)
                continue

            paises_str = "|".join(paises) if paises else miss_sentinel()
            cache_dict[chave] = paises_str
            novos_registros.append({"Name": nome, "Year": ano, "Countries": paises_str})
            time.sleep(TMDB_RATE_LIMIT_SECONDS)

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


def generate_map(filmes_por_pais: dict[str, list[str]]) -> None:
    logger.info("\nGerando mapa...")
    gerar_mapa({pais: len(filmes) for pais, filmes in filmes_por_pais.items()}, str(OUTPUT_HTML))


def generate_stats_output() -> None:
    logger.info("\nGerando stats.json...")
    ratings_path = RATINGS_PATH if RATINGS_PATH.exists() else None
    if ratings_path:
        logger.info("   ratings.csv encontrado, incluindo avaliacoes...")
    else:
        logger.info("   ratings.csv nao encontrado, gerando stats sem avaliacoes...")
    gerar_stats(CSV_PATH, STATS_JSON, ratings_path)




def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def open_dashboard() -> None:
    dashboard_path = DOCS_DIR / "index.html"
    if not dashboard_path.exists():
        logger.warning("   Nao foi possivel abrir o navegador: %s nao existe.", dashboard_path)
        return

    try:
        port = _get_free_port()
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            ["python", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=str(DOCS_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        url = f"http://127.0.0.1:{port}/{dashboard_path.name}"
        webbrowser.open(url)
        logger.info("   Abrindo %s no navegador via %s...", dashboard_path.name, url)
    except Exception as exc:
        logger.warning("   Falha ao iniciar servidor local (%s). Abrindo arquivo direto.", exc)
        webbrowser.open(dashboard_path.resolve().as_uri())
        logger.info("   Abrindo %s no navegador...", dashboard_path.name)


def log_summary(summary: ExecutionSummary, total_movies: int, distinct_countries: int) -> None:
    logger.info("\nResumo da execucao:")
    logger.info("   Filmes processados: %s", total_movies)
    logger.info("   Cache hits: %s", summary.cache_hits)
    logger.info("   Consultas TMDB: %s", summary.api_requests)
    logger.info("   Falhas temporarias TMDB: %s", summary.temporary_failures)
    logger.info("   Filmes sem pais: %s", summary.without_country)
    logger.info("   Paises distintos encontrados: %s", distinct_countries)


def log_user_error(exc: Exception) -> None:
    logger.error("\nErro:")
    for line in str(exc).splitlines():
        logger.error("   %s", line)

    logger.error("\nDicas rapidas:")
    logger.error("   1. Confira o arquivo data/watched.csv")
    logger.error("   2. Confira o arquivo .env com TMDB_API_KEY")
    logger.error("   3. Veja exemplos no README.md")


def run_pipeline(options: PipelineOptions) -> ExecutionSummary:
    ensure_output_dirs()
    render_docs_pages()
    validate_runtime_config()

    logger.info("Carregando watched.csv...")
    df = load_watched_csv(CSV_PATH)
    logger.info("   %s filmes encontrados.\n", len(df))

    cache_df, cache_dict = load_cache_state(options.refresh_cache)

    logger.info("Consultando TMDB API...")
    novos_registros, filmes_por_pais, paises_distintos, summary = enrich_movies_with_countries(df, cache_dict)

    salvar_cache(cache_df, novos_registros, CACHE_PATH)
    logger.info("\n   %s paises distintos encontrados.", len(paises_distintos))

    if not options.stats_only:
        generate_map(filmes_por_pais)

    if not options.map_only:
        generate_stats_output()
        render_docs_pages()

    log_summary(summary, len(df), len(paises_distintos))
    logger.info("\nTudo gerado em docs/")
    if not options.no_open and not options.map_only:
        open_dashboard()

    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging()
    try:
        run_pipeline(options)
        return 0
    except KeyboardInterrupt:
        logger.error("\nExecucao interrompida pelo usuario.")
        return 130
    except (FileNotFoundError, ValueError) as exc:
        log_user_error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
