"""Automated retrieval rubric for the five required question types.

Verdicts come from this rubric after a real search. They are not hand-written.
"""

from __future__ import annotations

CASES = [
    {
        "id": "product",
        "question_type": "product",
        "question": "What is the Darwix Health Shield product and the base sum insured?",
        "expected_record_prefix": "kb_health_product",
        "expected_category": "product",
        "answer_must_include": "5 lakh",
        "expect_fallback": False,
    },
    {
        "id": "policy",
        "question_type": "policy",
        "question": "What is the waiting period for pre-existing conditions and the room rent cap?",
        "expected_record_prefix": "kb_health_policy",
        "expected_category": "coverage",
        "answer_must_include": "36 months",
        "expect_fallback": False,
    },
    {
        "id": "qualification",
        "question_type": "qualification",
        "question": "Who qualifies for Darwix Health Shield by age, city, and monthly budget?",
        "expected_record_prefix": "kb_health_qualification",
        "expected_category": "qualification",
        "answer_must_include": "18",
        "expect_fallback": False,
    },
    {
        "id": "faq",
        "question_type": "faq",
        "question": "How does cashless treatment work at network hospitals?",
        "expected_record_prefix": "kb_health_faq",
        "expected_category": "faq",
        "answer_must_include": "cashless",
        "expect_fallback": False,
    },
    {
        "id": "objection",
        "question_type": "objection",
        "question": "The customer says the premium is too expensive. How should the agent respond?",
        "expected_record_prefix": "kb_health_objection",
        "expected_category": "objection",
        "answer_must_include": "rate card",
        "expect_fallback": False,
    },
    {
        "id": "out_of_scope",
        "question_type": "out_of_scope",
        "question": "What is the capital of France?",
        "expected_record_prefix": "",
        "expected_category": "",
        "answer_must_include": "knowledge base",
        "expect_fallback": True,
    },
]


def judge(case: dict, result: dict) -> str:
    if case["expect_fallback"]:
        return "CORRECT" if result["fallback"] else "INCORRECT"
    chunks = result.get("retrieved_chunks") or []
    if result.get("fallback") or not chunks:
        return "INCORRECT"
    top = chunks[0]
    phrase = case["answer_must_include"].lower()
    answer_ok = phrase in result.get("answer", "").lower()
    identity_ok = top["record_id"].startswith(case["expected_record_prefix"]) or top.get("category") == case["expected_category"]
    if identity_ok and answer_ok:
        return "CORRECT"
    category_hit = any(chunk.get("category") == case["expected_category"] for chunk in chunks[:3])
    if category_hit or identity_ok or answer_ok:
        return "PARTIALLY_CORRECT"
    return "INCORRECT"


def run_evaluation(knowledge_base, source_prefix: str = "health/") -> dict:
    rows = []
    for case in CASES:
        filters = {"source_prefix": source_prefix}
        result = knowledge_base.answer(case["question"], filters=filters)
        payload = result.model_dump()
        top = payload["retrieved_chunks"][0] if payload["retrieved_chunks"] else {}
        rows.append(
            {
                "question": case["question"],
                "question_type": case["question_type"],
                "retrieved_record": top.get("record_id", ""),
                "retrieved_chunk": top.get("chunk_id", ""),
                "source": top.get("source", ""),
                "relevance_score": payload["confidence"],
                "expected_answer": case["answer_must_include"] if not case["expect_fallback"] else "safe fallback",
                "actual_answer": payload["answer"],
                "verdict": judge(case, payload),
                "fallback": payload["fallback"],
                "generation_mode": payload["generation_mode"],
            }
        )
    return {
        "embedding_model": knowledge_base.embedder.name,
        "vector_backend": knowledge_base.index.backend,
        "confidence_threshold": knowledge_base.settings.confidence_threshold,
        "rubric": "Top chunk category or record prefix, plus a required source phrase. Fallback cases must fallback.",
        "results": rows,
    }
