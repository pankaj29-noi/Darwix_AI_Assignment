"""Retrieval, cleaning, citation, and fallback tests."""

from rag.cleaning import clean_text, jaccard, shingles
from rag.chunking import chunk_text
from rag.evaluation import run_evaluation
from rag.pii import redact


def test_cleaning_removes_boilerplate_and_normalizes_terms():
    raw = "Darwix Internal Header\nPage 1 of 2\nHome | Products | Login | Contact\n\nThe sum assured is fixed.\n\nThe sum assured is fixed.\n"
    cleaned = clean_text(raw)
    assert "Darwix Internal Header" not in cleaned
    assert "Page 1 of 2" not in cleaned
    assert "Home | Products" not in cleaned
    assert "sum insured" in cleaned
    assert cleaned.lower().count("sum insured") == 1


def test_pii_redaction_keeps_the_operational_sentence():
    redacted, flagged, types = redact(
        "Reach alex.demo@example.com or +91 98765 43210. Staff file demo card-loss notes within 15 days."
    )
    assert flagged is True
    assert "email" in types
    assert "phone" in types
    assert "alex.demo@example.com" not in redacted
    assert "15 days" in redacted


def test_chunking_is_section_aware_and_keeps_overlap():
    text = "# Coverage\n" + ("coverage " * 50) + "\n# Exclusions\n" + ("exclusion " * 30)
    chunks = chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) >= 2
    assert chunks[0].section == "Coverage"
    assert any(chunk.section == "Exclusions" for chunk in chunks)


def test_near_duplicate_jaccard_is_high_for_tiny_edits():
    left = "Pre-existing conditions are covered after a waiting period of 36 months in the base plan."
    right = left + " Please note this reminder."
    assert jaccard(shingles(left), shingles(right)) >= 0.68


def test_ingest_indexes_schema_and_skips_bad_or_duplicate_files(app):
    report = app.state.kb.ingest_report
    assert report["vector_backend"] == "faiss"
    assert any(item["source"].endswith("synthetic_pii.md") for item in report["pii_flagged"])
    assert any(item["source"].endswith("coverage_policy_duplicate.md") for item in report["skipped_duplicates"])
    assert any(item["source"].endswith("broken_extract.txt") for item in report["skipped_extraction"])
    records = app.state.db.list_knowledge()
    required = {
        "record_id",
        "title",
        "content",
        "category",
        "source",
        "source_url",
        "section",
        "version",
        "created_at",
        "updated_at",
        "pii",
        "language",
        "document_type",
        "chunk_id",
        "hash",
    }
    assert required <= set(records[0])
    pii_rows = [row for row in records if row["pii"]]
    assert pii_rows
    assert "example.com" not in pii_rows[0]["content"]
    product = next(row for row in records if row["record_id"].startswith("kb_health_product"))
    assert "sum insured" in product["content"]
    assert "sum assured" not in product["content"]


def test_product_policy_and_fallback(app):
    product = app.state.kb.answer(
        "What is the Darwix Health Shield product and the base sum insured?",
        filters={"source_prefix": "health/"},
    )
    assert product.fallback is False
    assert "5 lakh" in product.answer
    assert product.sources[0]["source"]
    policy = app.state.kb.answer(
        "What is the waiting period for pre-existing conditions?",
        filters={"source_prefix": "health/"},
    )
    assert "36 months" in policy.answer
    assert policy.sources
    unknown = app.state.kb.answer("What is the capital of France?", filters={"source_prefix": "health/"})
    assert unknown.fallback is True
    assert "Paris" not in unknown.answer
    assert unknown.sources == []


def test_evaluation_rubric_covers_five_question_types(app):
    payload = run_evaluation(app.state.kb)
    kinds = {row["question_type"] for row in payload["results"]}
    assert {"product", "policy", "qualification", "faq", "objection"} <= kinds
    assert all(row["verdict"] == "CORRECT" for row in payload["results"])
