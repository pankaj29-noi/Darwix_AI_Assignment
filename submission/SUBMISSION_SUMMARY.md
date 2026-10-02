# Darwix AI Engineer Assessment — Submission Summary

Candidate: Pankaj Bishnoi  
Project: Darwix AI Voice Intelligence Platform  
Scope: All four assessment questions

## Links to add before uploading

- GitHub repository: `https://github.com/pankaj29-noi/Darwix_AI_Assignment`
- Video walkthrough: `Not provided`

## What is included

### Q1 — Knowledge-grounded voice agent

- Health-insurance lead qualification flow with consent, discovery, qualification,
  FAQ/objection handling, preliminary eligibility, callback, summary, and escalation.
- Uses the Q2 knowledge base for business answers rather than policy facts in the
  system prompt.
- Safe fallback for unsupported questions and a human-escalation path.
- Web calling interface clearly labeled as mock/web mode, not a phone call.
- Executed transcripts: cooperative, objection, unsupported, incomplete, and
  conflicting-detail scenarios under `transcripts/q1/`.

### Q2 — Production-ready knowledge base

- Ingests PDF, TXT, Markdown, HTML, and CSV.
- Cleans boilerplate, normalizes terminology, removes duplicates/near-duplicates,
  redacts obvious PII, chunks by section, and stores traceable metadata.
- TF-IDF vectors in FAISS by default, reranking, confidence threshold, citations,
  and safe fallback.
- Six executed retrieval checks: product, policy, qualification, FAQ, objection,
  and out-of-scope. All six received the automated verdict `CORRECT`.

### Q3 — Native-language prototypes

- Philippines bancassurance flow: English, Filipino/Tagalog, and Taglish.
- Indonesia multifinance flow: formal and colloquial Bahasa Indonesia plus a
  Javanese-influenced text-normalization example.
- Market terminology, code-switching, localized objections, same-language fallback,
  and human escalation.
- Honest limitation: cloud ASR quality and Indonesian accent recognition were not
  measured because no ASR credential was configured.

### Q4 — Live insights and nudges

- Chunks are processed during a real-time-speed replay, not only after completion.
- WebSocket dashboard receives transcript chunks, signals, evidence-backed nudges,
  confidence, timestamps, and stage latency.
- Signals cover missed opportunity, compliance, buying intent, frustration,
  callback, payment difficulty, and topic shift.
- Confidence threshold, duplicate suppression, cooldown, priority, topic grouping,
  expiry, and repetition controls are implemented.

## Executed results

- Automated tests: **34 passed, 0 failed**.
- RAG evaluation: **6/6 CORRECT**, including safe out-of-scope fallback.
- Full real-time demo: **6 signals and 5 nudges**.
- False-positive checks: **0 nudges** for both neutral and noisy text scenarios.
- Latest local end-to-end latency over 7 chunks:
  - P50: **1.178541 ms**
  - P95: **1.426871 ms**
- LLM latency: **NOT MEASURED** because the default nudge path is rule/template
  based.
- Cloud ASR latency and quality: **NOT MEASURED**. The measured ASR stage is only
  mock aligned-text passthrough time.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
cd frontend && npm install && cd ..
PYTHONPATH=backend uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Evidence map

- Setup and overview: `README.md`
- Architecture: `docs/ARCHITECTURE.md`
- Q1 design: `docs/Q1_VOICE_AGENT.md`
- Q2 design and retrieval results: `docs/Q2_KNOWLEDGE_BASE.md`
- Q3 localization and ASR limitations: `docs/Q3_MULTILINGUAL.md`
- Q4 streaming design: `docs/Q4_REALTIME.md`
- Evaluation: `docs/EVALUATION.md` and `results/`
- Latency: `docs/LATENCY_REPORT.md` and `results/latency_results.json`
- Production plan: `docs/PRODUCTION_PLAN.md`
- Transcripts: `transcripts/`
- Audio disclosure: `recordings/MANIFEST.json`

## Known limitations

- No live telephony provider is connected; the UI is a web session.
- No cloud ASR/LLM credentials were used.
- Cloud ASR quality, accent accuracy, cloud latency, and native Filipino TTS quality
  are not claimed.
- Default retrieval uses lexical TF-IDF; sentence-transformers support exists but
  was not executed in this environment.
- Script speaker labels are used instead of acoustic diarization.
- The Javanese example is text normalization after transcription, not proof of
  acoustic accent recognition.
- Audio files in `recordings/` are labeled synthetic TTS samples, not customer calls.

## Production improvements

First production steps would be credentialed streaming ASR, authenticated
tenant-scoped APIs, Postgres/pgvector, queue-backed processing, encrypted PII,
observability, provider fallbacks, human review of multilingual copy, and load/noise
testing at 10x concurrency.
