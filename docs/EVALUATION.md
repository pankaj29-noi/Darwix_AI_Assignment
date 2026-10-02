# Evaluation

## Tests

`results/test_summary.json` from the latest pytest run:

- tests: 34
- failures: 0
- errors: 0
- skipped: 0
- time: 0.85 seconds

Covered areas: cleaning, PII, chunk metadata, dedupe, citations, fallback, the five retrieval types, prompt isolation, cooperative and objection calls, unsupported questions, human escalation, incomplete and conflicting slots, localization examples, register detection, accent-report honesty, nudge evidence, duplicate suppression, neutral/noisy replays, API validation, WebSocket delivery, and the LLM client's refusal to answer without a key.

## Retrieval rubric

`results/rag_evaluation.json`. All six cases were `CORRECT` on the last run, including the France fallback. Scores are in `docs/Q2_KNOWLEDGE_BASE.md`. The rubric is automatic. It is not a human graded sheet.

## Multilingual

`results/multilingual_results.json`.

- Detector mismatches: 0 on the six labeled lines.
- Philippines and Indonesia cooperative scripts reached `END`.
- Both escalation scripts reached `ESCALATED`.
- ASR quality: NOT MEASURED.

## Nudges

`results/nudge_results.json`. Positive scenarios produced evidence-backed nudges. Neutral and noisy produced zero nudges.

## Secret scan

`PYTHONPATH=backend python scripts/check_secrets.py` printed `No secret patterns found.` This scan looks for common key shapes. It is not a substitute for reviewing the diff before you push.
