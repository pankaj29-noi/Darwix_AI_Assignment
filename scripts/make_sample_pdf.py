"""Build a tiny text PDF and confirm pypdf can read it back."""

from pathlib import Path

from pypdf import PdfReader


def build_pdf(text: str) -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 700 Td ({safe}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        f"4 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    )
    return bytes(output)


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "data" / "kb" / "health" / "grace_period.pdf"
    sentence = "Darwix Health Shield renewal grace period is 15 days from the due date. Synthetic demo data."
    destination.write_bytes(build_pdf(sentence))
    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(str(destination)).pages)
    if "grace period" not in extracted:
        raise SystemExit(f"PDF text was not readable: {extracted!r}")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
