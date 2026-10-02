"""Build a clean offline assessment ZIP without secrets or generated dependencies."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT.parent / "Pankaj_Bishnoi_Darwix_AI_Assignment.zip"
ARCHIVE_ROOT = "Pankaj_Bishnoi_Darwix_AI_Assignment"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
    "dist",
    ".vite",
    "coverage",
}
EXCLUDED_FILES = {
    ".env",
    ".DS_Store",
}
EXCLUDED_SUFFIXES = {
    ".db",
    ".pyc",
    ".pyo",
    ".zip",
}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if relative.parts[:2] == ("data", "vector"):
        return False
    if path.name in EXCLUDED_FILES:
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def build(output: Path) -> tuple[int, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in ROOT.rglob("*") if should_include(path))
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            info = zipfile.ZipInfo.from_file(path, Path(ARCHIVE_ROOT) / relative)
            mode = 0o100755 if path.suffix == ".sh" else 0o100644
            info.external_attr = mode << 16
            archive.writestr(info, path.read_bytes())
    return len(files), output.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    count, size = build(args.output)
    print(f"{args.output}\nfiles={count}\nbytes={size}")


if __name__ == "__main__":
    main()
