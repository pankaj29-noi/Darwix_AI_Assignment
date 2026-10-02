"""Load PDF, text, Markdown, HTML, and CSV into raw documents."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader


SUPPORTED = {".pdf", ".txt", ".md", ".html", ".htm", ".csv"}


@dataclass
class RawDocument:
    source: str
    source_url: str = ""
    text: str = ""
    title: str = ""
    metadata: dict = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    header = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
            cleaned = cleaned[1:-1]
        meta[key.strip().lower()] = cleaned
    return meta, body


def _html_to_text(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    return soup.get_text("\n")


def load_file(path: Path, relative: str) -> RawDocument:
    suffix = path.suffix.lower()
    document = RawDocument(source=relative)
    try:
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            document.text = "\n\n".join(pages)
            document.title = path.stem.replace("_", " ")
            if not document.text.strip():
                document.issues.append("extraction_empty_pdf")
        elif suffix in {".html", ".htm"}:
            document.text = _html_to_text(path.read_text(encoding="utf-8", errors="replace"))
            document.title = path.stem.replace("_", " ")
        elif suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                document.rows = [dict(row) for row in reader]
            document.title = path.stem.replace("_", " ")
            document.text = "\n".join(
                " ".join(str(value) for value in row.values() if value) for row in document.rows
            )
        else:
            raw = path.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(raw)
            document.metadata = meta
            document.text = body
            document.title = meta.get("title") or path.stem.replace("_", " ")
            document.source_url = meta.get("source_url", "")
    except Exception as exc:  # extraction must be visible, not fatal to the batch
        document.issues.append(f"extraction_failed:{type(exc).__name__}")
        document.text = ""
    return document


def discover_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED)
