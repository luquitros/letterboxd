import argparse

from .config import CONFIG
from .main import configure_logging, log_user_error, open_dashboard, render_site


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renderiza o site a partir dos artefatos ja gerados.")
    parser.add_argument("--open", action="store_true", help="Abre o dashboard no navegador ao final.")
    return parser.parse_args(argv)



def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging()
    try:
        render_site(config=CONFIG)
        if args.open:
            open_dashboard(config=CONFIG)
        return 0
    except KeyboardInterrupt:
        return 130
    except (FileNotFoundError, ValueError) as exc:
        log_user_error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
