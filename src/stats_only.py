from main import (
    configure_logging,
    embed_stats_in_html,
    ensure_output_dirs,
    generate_stats_output,
    validate_runtime_config,
)


if __name__ == "__main__":
    configure_logging()
    ensure_output_dirs()
    validate_runtime_config()
    generate_stats_output()
    embed_stats_in_html()
