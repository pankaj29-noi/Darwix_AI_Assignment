"""Document cleaning that preserves meaning and source identity."""

from __future__ import annotations

import re

from rag.textutil import content_tokens

HEADER_FOOTER = [
    re.compile(r"^page\s+\d+(\s+of\s+\d+)?$", re.I),
    re.compile(r"^confidential$", re.I),
    re.compile(r"^darwix internal header$", re.I),
    re.compile(r"^all rights reserved\.?$", re.I),
    re.compile(r"^copyright\b.*$", re.I),
    re.compile(r"^printed on\b.*$", re.I),
]

NAV_SPLIT = re.compile(r"\s*\|\s*")
NAV_WORDS = {"home", "products", "login", "contact", "about", "support", "faq"}

TERMINOLOGY = [
    (re.compile(r"\bsum assured\b", re.I), "sum insured"),
    (re.compile(r"\bpre existing\b", re.I), "pre-existing"),
    (re.compile(r"\bpreexisting\b", re.I), "pre-existing"),
    (re.compile(r"\bPECs?\b"), "pre-existing condition"),
]


def _is_nav(line: str) -> bool:
    parts = [part.strip().lower() for part in NAV_SPLIT.split(line) if part.strip()]
    return len(parts) >= 3 and all(part in NAV_WORDS for part in parts)


def remove_boilerplate(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append("")
            continue
        if any(pattern.match(stripped) for pattern in HEADER_FOOTER):
            continue
        if _is_nav(stripped):
            continue
        kept.append(stripped)
    return "\n".join(kept)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_headings(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            hashes, _, title = stripped.partition(" ")
            if set(hashes) == {"#"} and title:
                lines.append(f"{hashes} {title.strip().title() if title.isupper() else title.strip()}")
                continue
        if stripped.isupper() and 3 < len(stripped) < 80 and any(ch.isalpha() for ch in stripped):
            lines.append(stripped.title())
            continue
        lines.append(line)
    return "\n".join(lines)


def normalize_terminology(text: str) -> str:
    for pattern, replacement in TERMINOLOGY:
        text = pattern.sub(replacement, text)
    return text


def remove_repeated_paragraphs(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    seen: list[str] = []
    kept: list[str] = []
    for paragraph in paragraphs:
        key = " ".join(paragraph.lower().split())
        if len(key) > 20 and key in seen:
            continue
        seen.append(key)
        kept.append(paragraph)
    return "\n\n".join(kept)


def clean_text(text: str) -> str:
    text = remove_boilerplate(text)
    text = normalize_whitespace(text)
    text = normalize_headings(text)
    text = normalize_terminology(text)
    text = remove_repeated_paragraphs(text)
    return normalize_whitespace(text)


def shingles(text: str, size: int = 5) -> set[tuple[str, ...]]:
    tokens = content_tokens(text)
    if len(tokens) < size:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index : index + size]) for index in range(len(tokens) - size + 1)}


def jaccard(left: set, right: set) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def flag_extraction_issues(text: str) -> list[str]:
    issues: list[str] = []
    alnum = sum(ch.isalnum() for ch in text)
    if alnum < 40:
        issues.append("extraction_too_short")
    if "\ufffd" in text or text.count("?") > max(8, len(text) // 20):
        issues.append("possible_encoding_error")
    return issues
