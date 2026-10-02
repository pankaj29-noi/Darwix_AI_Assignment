# Q2 — Knowledge base

## Pipeline

Load PDF, text, Markdown, HTML, or CSV. HTML drops `nav`, `header`, `footer`, `script`, and `style`. Cleaning removes page lines, the internal header, pipe navigation, repeated paragraphs, and normalizes `sum assured` to `sum insured` and `PEC` to `pre-existing condition`. Near-duplicates use 5-word Jaccard similarity at 0.75. Obvious emails, phone numbers, Aadhaar-like groups, cards, SSNs, and labeled dates of birth are redacted before storage. The record stays, with `pii` true. Files that are too short, such as `broken_extract.txt`, are skipped and listed in the ingest report.

Chunks follow Markdown headings, then pack words to `CHUNK_SIZE` with `CHUNK_OVERLAP`. Each chunk keeps title, section, source, version, language, category, and hash.

## Index

Default embedder: TF-IDF, L2 normalized, searched with FAISS inner product, then blended with lexical Jaccard (0.8 embedding, 0.2 lexical). Metadata filters cover source prefix, category, language, and document type.

`sentence-transformers/all-MiniLM-L6-v2` is coded in `backend/rag/embeddings.py`. Set `EMBEDDING_PROVIDER=sentence-transformers` after `pip install -r backend/requirements-ml.txt`. That package was not installed for this run, so no MiniLM score is reported.

## Answer contract

```json
{
  "answer": "...",
  "confidence": 0.0,
  "sources": [],
  "retrieved_chunks": [],
  "fallback": false
}
```

Below the threshold, `sources` is empty, `fallback` is true, and the answer is the fixed safe sentence. Retrieved chunks are still returned so the miss can be audited.

## Last rubric run

Source: `results/rag_evaluation.json`. Automated rule: the top record prefix or category must match, and the answer must contain a phrase that is in the source. The out-of-scope item must fall back.

| Type | Verdict | Score | Record |
| --- | --- | --- | --- |
| Product | CORRECT | 0.4464 | `kb_health_product_c001` |
| Policy | CORRECT | 0.4166 | `kb_health_policy_c001` |
| Qualification | CORRECT | 0.2743 | `kb_health_qualification_c001` |
| FAQ | CORRECT | 0.371 | `kb_health_faq_c001` |
| Objection | CORRECT | 0.3078 | `kb_health_objection_c001` |
| Out of scope | CORRECT | 0.0 | fallback, no Paris |

The voice agent calls the same `KnowledgeBase.answer` method. It does not keep a second copy of the FAQ text.
