"""Fail if likely secrets are present. Empty templates are allowed."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".venv", "node_modules", "dist", ".git", "__pycache__"}
PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api_key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]


def main() -> int:
    findings = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() in {".png", ".aiff", ".wav", ".mp3", ".pdf", ".faiss", ".npy"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)} matched {pattern.pattern}")
    if findings:
        print("\n".join(findings))
        return 1
    print("No secret patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
