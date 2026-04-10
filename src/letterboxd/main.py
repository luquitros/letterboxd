import argparse
import logging
import socket
import subprocess
import time
import webbrowser

from . import pipeline
from .config import CONFIG, AppConfig
from .pipeline import ExecutionSummary, PipelineOptions
from .site_renderer import render_docs_pages
from .tmdb import buscar_paises

logger = logging.getLogger(__name__)
load_watched_csv = pipeline.load_watched_csv



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera o dashboard do Letterboxd.")
    parser.add_argument("--no-open", action="store_true", help="Nao abre o dashboard no navegador ao final.")
    parser.add_argument("--stats-only", action="store_true", help="Gera apenas o stats.json e atualiza os HTMLs.")
    parser.add_argument("--map-only", action="store_true", help="Gera apenas o mapa de paises.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignora o cache atual e consulta novamente a TMDB.")
    parser.add_argument("--clear-cache", action="store_true", help="Apaga o arquivo de cache local antes de executar.")
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
        clear_cache=args.clear_cache,
    )



def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")



def enrich_movies_with_countries(df, cache_dict, *, config: AppConfig = CONFIG):
    return pipeline.enrich_movies_with_countries(
        df,
        cache_dict,
        tmdb_api_key=config.tmdb_api_key,
        logger=logger,
        sleep_fn=time.sleep,
        buscar_paises_fn=buscar_paises,
    )



def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])



def open_dashboard(*, config: AppConfig = CONFIG) -> None:
    dashboard_path = config.docs_dir / "index.html"
    if not dashboard_path.exists():
        logger.warning("   Nao foi possivel abrir o navegador: %s nao existe.", dashboard_path)
        return

    try:
        port = _get_free_port()
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            ["python", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=str(config.docs_dir),
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



def render_site(*, config: AppConfig = CONFIG) -> None:
    logger.info("\nRenderizando paginas do site...")
    render_docs_pages(config=config)



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



def run_pipeline(options: PipelineOptions, *, config: AppConfig = CONFIG) -> ExecutionSummary:
    artifacts = pipeline.generate_data_artifacts(options, logger, sleep_fn=time.sleep, config=config)

    if artifacts.stats_generated:
        render_site(config=config)

    log_summary(artifacts.summary, artifacts.total_movies, artifacts.distinct_countries)
    logger.info("\nTudo gerado em docs/")
    if not options.no_open and not options.map_only:
        open_dashboard(config=config)

    return artifacts.summary



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
