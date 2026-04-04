from pathlib import Path

from config import DOCS_DIR, STATS_JSON

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PAGE_TEMPLATES = ("index.html", "dashboard.html", "wrapped_generator.html")
STATS_PLACEHOLDER = "{{EMBEDDED_STATS}}"


def load_stats_payload() -> str:
    if STATS_JSON.exists():
        return STATS_JSON.read_text(encoding="utf-8")
    return "{}"


def render_docs_pages(stats_payload: str | None = None) -> None:
    payload = stats_payload if stats_payload is not None else load_stats_payload()

    for page_name in PAGE_TEMPLATES:
        template_path = TEMPLATE_DIR / page_name
        output_path = DOCS_DIR / page_name
        html = template_path.read_text(encoding="utf-8")
        if STATS_PLACEHOLDER in html:
            html = html.replace(STATS_PLACEHOLDER, payload)
        output_path.write_text(html, encoding="utf-8")
