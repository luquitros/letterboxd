from pathlib import Path

from .config import CONFIG, AppConfig

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PAGE_TEMPLATES = ("index.html", "dashboard.html", "wrapped_generator.html")
STATS_PLACEHOLDER = "{{EMBEDDED_STATS}}"



def load_stats_payload(config: AppConfig = CONFIG) -> str:
    if config.stats_json.exists():
        return config.stats_json.read_text(encoding="utf-8")
    return "{}"



def render_docs_pages(stats_payload: str | None = None, *, config: AppConfig = CONFIG) -> None:
    payload = stats_payload if stats_payload is not None else load_stats_payload(config)

    for page_name in PAGE_TEMPLATES:
        template_path = TEMPLATE_DIR / page_name
        output_path = config.docs_dir / page_name
        html = template_path.read_text(encoding="utf-8")
        if STATS_PLACEHOLDER in html:
            html = html.replace(STATS_PLACEHOLDER, payload)
        output_path.write_text(html, encoding="utf-8")
