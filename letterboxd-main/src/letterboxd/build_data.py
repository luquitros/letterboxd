import argparse
import time

from .config import CONFIG
from .main import configure_logging, log_summary, log_user_error, logger
from .pipeline import PipelineOptions, generate_data_artifacts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera apenas os artefatos de dados do Letterboxd.")
    parser.add_argument("--stats-only", action="store_true", help="Gera apenas o stats.json.")
    parser.add_argument("--map-only", action="store_true", help="Gera apenas o mapa de paises.")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignora o cache atual e consulta novamente a TMDB.")
    parser.add_argument("--clear-cache", action="store_true", help="Apaga o arquivo de cache local antes de executar.")
    args = parser.parse_args(argv)

    if args.stats_only and args.map_only:
        parser.error("Use apenas um entre --stats-only e --map-only.")

    return args



def build_options(args: argparse.Namespace) -> PipelineOptions:
    return PipelineOptions(
        no_open=True,
        stats_only=args.stats_only,
        map_only=args.map_only,
        refresh_cache=args.refresh_cache,
        clear_cache=args.clear_cache,
    )



def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging()
    try:
        artifacts = generate_data_artifacts(options, logger, sleep_fn=time.sleep, config=CONFIG)
        log_summary(artifacts.summary, artifacts.total_movies, artifacts.distinct_countries)
        logger.info("\nArtefatos de dados atualizados em docs/.")
        return 0
    except KeyboardInterrupt:
        logger.error("\nExecucao interrompida pelo usuario.")
        return 130
    except (FileNotFoundError, ValueError) as exc:
        log_user_error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
