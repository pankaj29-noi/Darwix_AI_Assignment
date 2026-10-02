"""Section-aware chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADING = re.compile(r"^(#{1,3})\s+(.+)$", re.M)


@dataclass
class ChunkDraft:
    section: str
    text: str
    index: int


def split_sections(text: str, default_section: str) -> list[tuple[str, str]]:
    matches = list(HEADING.finditer(text))
    if not matches:
        return [(default_section, text.strip())] if text.strip() else []
    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        preface = text[: matches[0].start()].strip()
        if preface:
            sections.append((default_section, preface))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        title = match.group(2).strip()
        if body:
            sections.append((title, body))
    return sections


def chunk_text(text: str, chunk_size: int, overlap: int, default_section: str = "Body") -> list[ChunkDraft]:
    if chunk_size < 20:
        raise ValueError("CHUNK_SIZE must be at least 20 words")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
    drafts: list[ChunkDraft] = []
    cursor = 0
    for section, body in split_sections(text, default_section):
        words = body.split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = min(len(words), start + chunk_size)
            piece = " ".join(words[start:end]).strip()
            if piece:
                drafts.append(ChunkDraft(section=section, text=piece, index=cursor))
                cursor += 1
            if end >= len(words):
                break
            next_start = end - overlap
            if next_start <= start:
                next_start = start + 1
            start = next_start
    return drafts
