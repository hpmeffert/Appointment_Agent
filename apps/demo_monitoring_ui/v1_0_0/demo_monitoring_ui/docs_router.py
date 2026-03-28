from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

def _resolve_docs_root() -> Path:
    project_root = Path(__file__).resolve().parents[4]
    for candidate in ("Docs", "docs"):
        candidate_path = project_root / candidate
        if candidate_path.exists():
            return candidate_path
    return project_root / "Docs"


DOCS_ROOT = _resolve_docs_root()

router = APIRouter(tags=["demo-docs-v1.0.2"])


DOC_MAP = {
    "demo": {
        "en": DOCS_ROOT / "demo" / "demo_guide_demo_monitoring_ui_v1_0_0.md",
        "de": DOCS_ROOT / "demo" / "demo_guide_demo_monitoring_ui_v1_0_0.md",
    },
    "user": {
        "en": DOCS_ROOT / "user" / "user_guide_demo_monitoring_ui_v1_0_0.md",
        "de": DOCS_ROOT / "user" / "user_guide_demo_monitoring_ui_v1_0_0.md",
    },
    "admin": {
        "en": DOCS_ROOT / "admin" / "demo_monitoring_ui_v1_0_0.md",
        "de": DOCS_ROOT / "admin" / "demo_monitoring_ui_v1_0_0.md",
    },
}


def _markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html: list[str] = []
    in_list = False
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            if in_list:
                html.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h1>{line[2:]}</h1>")
            continue
        if line.startswith("## "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h2>{line[3:]}</h2>")
            continue
        if line.startswith("### "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h3>{line[4:]}</h3>")
            continue
        if line.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{line[2:]}</li>")
            continue
        if raw_line.startswith("1. "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p><strong>{raw_line[:2]}</strong> {raw_line[3:]}</p>")
            continue
        html.append(f"<p>{line}</p>")
    if in_list:
        html.append("</ul>")
    return "\n".join(html)


def _render_doc(doc_type: str, lang: str) -> HTMLResponse:
    doc_path = DOC_MAP[doc_type][lang]
    content = doc_path.read_text(encoding="utf-8")
    html_content = _markdown_to_html(content)
    body = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{doc_type.title()} Guide</title>
        <style>
          body {{
            margin: 0;
            font-family: "Avenir Next", "Segoe UI", sans-serif;
            background: linear-gradient(135deg, #f3ead8 0%, #f8f6ef 48%, #dceee6 100%);
            color: #1d2b24;
          }}
          main {{
            max-width: 920px;
            margin: 32px auto;
            padding: 28px;
            background: rgba(255, 252, 247, 0.95);
            border: 1px solid #d3c6ab;
            border-radius: 24px;
            box-shadow: 0 18px 50px rgba(26, 44, 36, 0.12);
          }}
          h1, h2, h3 {{ line-height: 1.12; }}
          p, li {{ line-height: 1.65; font-size: 17px; }}
          .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            color: #59675f;
            font-size: 14px;
          }}
          .pill {{
            display: inline-block;
            padding: 8px 12px;
            background: #d3f1ea;
            color: #0f766e;
            border-radius: 999px;
          }}
        </style>
      </head>
      <body>
        <main>
          <div class="topbar">
            <div class="pill">Language: {lang.upper()}</div>
            <div>{doc_type.title()} Guide</div>
          </div>
          {html_content}
        </main>
      </body>
    </html>
    """
    return HTMLResponse(body)


@router.get("/docs/demo")
def demo_doc(lang: str = Query(default="en")) -> HTMLResponse:
    return _render_doc("demo", "de" if lang == "de" else "en")


@router.get("/docs/user")
def user_doc(lang: str = Query(default="en")) -> HTMLResponse:
    return _render_doc("user", "de" if lang == "de" else "en")


@router.get("/docs/admin")
def admin_doc(lang: str = Query(default="en")) -> HTMLResponse:
    return _render_doc("admin", "de" if lang == "de" else "en")
