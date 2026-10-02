# Requirements map

Source of truth: `ai_assignment.pdf` (AI Engineer Assessment).

Executed status is in `docs/FINAL_CHECKLIST.md`. The table below is the original map. Where this file still says `IN PROGRESS`, the checklist is the later record.

This table is the implementation map for the Darwix AI Voice Intelligence Platform. `NOT MEASURED` means a metric was not invented.

| Requirement | Question | Implementation | Test/Evidence | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Working prototype, not a PRD | All | FastAPI + React app under `darwix-ai-assignment/` | Backend tests, frontend build, demo scripts | IN PROGRESS | Functional core over visual polish |
| Health-insurance lead qualification voice agent | Q1 | `backend/voice/orchestrator.py` state machine | `tests/test_voice.py`, `transcripts/q1/` | IN PROGRESS | Web call UI, not a PSTN number |
| Flow: greeting, consent, discovery, qualification, FAQ/objection, eligibility, callback/escalation, summary, end | Q1 | `VoiceOrchestrator` states | Voice scenario runner | IN PROGRESS | |
| Qualification fields: name, age, location, insurance requirement, family coverage, current insurance, budget, preferred coverage, urgency, callback | Q1 | Slot extractor + session record | `tests/test_voice.py` | IN PROGRESS | Only fields needed for this use case |
| Do not hardcode FAQs, objections, policies in the system prompt | Q1+Q2 | Generic prompt in `backend/voice/prompts.py`; facts live in `data/kb/` | `tests/test_voice.py` asserts prompt has no policy facts | IN PROGRESS | |
| Grounded answers with citation | Q1+Q2 | Retrieval then extractive or LLM answer | `retrieval_logs`, RAG eval | IN PROGRESS | |
| Safe fallback when knowledge is missing | Q1+Q2 | Confidence threshold in generator | Out-of-scope query test | IN PROGRESS | No invented answer |
| Human escalation | Q1 | Escalation state + mock CRM summary | Call 3 scenario | IN PROGRESS | |
| Cooperative, objection, incomplete, conflicting, out-of-scope, human-assistance coverage | Q1 | Scenarios in `data/voice/scenarios.json` | Transcripts and tests | IN PROGRESS | |
| At least 3 test calls with transcripts | Q1 | `scripts/run_voice_scenarios.py` | `transcripts/q1/` | IN PROGRESS | Audio only if synthesis actually runs |
| Web calling interface | Q1 | Frontend `/voice` | Browser check | IN PROGRESS | Mock telephony is labeled as such |
| Optional business action | Q1 | Preliminary eligibility + callback + mock CRM summary on the call row | Call summary JSON | IN PROGRESS | |
| Mixed input ingestion: PDF, TXT, Markdown, HTML, CSV | Q2 | `backend/rag/ingestion.py` | `tests/test_rag.py` | IN PROGRESS | |
| Cleaning: headers, footers, nav, repeats, whitespace, headings, terminology | Q2 | `backend/rag/cleaning.py` | Cleaning tests | IN PROGRESS | Meaning of source content is preserved |
| Duplicate and near-duplicate removal | Q2 | Jaccard shingles before index | Dedup test | IN PROGRESS | |
| PII identification and protection | Q2 | `backend/rag/pii.py` redacts before storage | PII test | IN PROGRESS | Synthetic PII only |
| Extraction failure handling | Q2 | Short/empty extracts flagged and skipped | Ingest report | IN PROGRESS | |
| Knowledge record schema | Q2 | `backend/rag/schemas.py` and SQLite `knowledge_records` | Record field test | IN PROGRESS | |
| Section-aware chunking with size and overlap | Q2 | `backend/rag/chunking.py` | Chunk metadata test | IN PROGRESS | `CHUNK_SIZE`, `CHUNK_OVERLAP` |
| Embedding, vector index, metadata filter, top-k, score | Q2 | `embeddings.py`, `retriever.py` | Retrieval tests | IN PROGRESS | Provider is reported, not assumed |
| Rerank, confidence threshold, citation | Q2 | `reranker.py`, `generator.py` | Citation and fallback tests | IN PROGRESS | |
| Structured answer payload | Q2 | `answer`, `confidence`, `sources`, `retrieved_chunks`, `fallback` | API `/kb/search` | IN PROGRESS | |
| At least 5 queries: product, policy, qualification, FAQ, objection | Q2 | `backend/rag/evaluation.py` | `results/rag_evaluation.json` | IN PROGRESS | Verdicts from executed retrieval |
| Traceable connection from voice agent to KB | Q1+Q2 | Every grounded turn writes `retrieval_logs` | Voice + log test | IN PROGRESS | |
| Philippines life/bancassurance bot | Q3 | `backend/multilingual/philippines.py` | `tests/test_multilingual.py` | IN PROGRESS | English, Filipino/Tagalog, Taglish |
| Natural local terms, not literal translation | Q3 | `data/philippines_config.json` and PH knowledge | Localization examples | IN PROGRESS | premium, policy, beneficiary, rider, lapse, coverage, bank referral |
| Indonesia multifinance bot | Q3 | `backend/multilingual/indonesia.py` | Multilingual tests | IN PROGRESS | Formal, colloquial, loanwords |
| Indonesian terms used naturally | Q3 | `data/indonesia_config.json` and ID knowledge | Localization examples | IN PROGRESS | cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan |
| Three localization examples per market with rationale | Q3 | Config `examples` + `docs/Q3_MULTILINGUAL.md` | Doc and API | IN PROGRESS | |
| Language-specific ASR report | Q3 | Provider abstraction; quality left `NOT MEASURED` without a key | `docs/Q3_MULTILINGUAL.md` | IN PROGRESS | No fabricated WER |
| Regional accent outside Jakarta | Q3 | Javanese-influenced text path + accent test endpoint | Accent test result | IN PROGRESS | Accent ASR accuracy is not claimed |
| Fallback stays in the customer language | Q3 | Locale fallback strings | Language fallback tests | IN PROGRESS | |
| Native TTS | Q3 | TTS provider + browser `speechSynthesis` | Voice actually selected is reported by the UI | IN PROGRESS | Compromises documented |
| Q3 tests: cooperative, objection, mixed, colloquial, escalation, accent | Q3 | Scenario runner | `transcripts/q3_*` | IN PROGRESS | |
| Real-time pipeline, not post-call only | Q4 | Chunk processor + WebSocket | `scripts/replay_call.py` | IN PROGRESS | Replay at real-time speed |
| Streaming transcript and speaker labels | Q4 | Chunk schema has `speaker` | Dashboard `/dashboard` | IN PROGRESS | Channel labels from the script; diarization is a stated limit |
| Signals: intent, compliance, frustration, buying, missed opportunity, callback | Q4 | `backend/realtime/signals.py` | `tests/test_realtime.py` | IN PROGRESS | |
| Nudges with evidence from the transcript | Q4 | `backend/realtime/nudges.py` | Evidence substring tests | IN PROGRESS | |
| Nudge control: threshold, duplicate suppression, cooldown, priority, expiry, topic grouping, repetition | Q4 | `NudgeEngine` | Suppression tests | IN PROGRESS | |
| Dashboard fields: status, transcript, speaker, signals, nudges, confidence, timestamp, latency | Q4 | `frontend` Live Intelligence page | Browser check | IN PROGRESS | |
| Latency P50/P95 by stage | Q4 | Measured in replay | `results/latency_results.json`, `docs/LATENCY_REPORT.md` | IN PROGRESS | Unmeasured stages stay `NOT MEASURED` |
| Noisy/ambiguous call avoids weak nudges | Q4 | Low-confidence path | Noisy scenario | IN PROGRESS | |
| False-positive notes | Q4 | Neutral scenario compared with positive scenarios | `results/nudge_results.json` | IN PROGRESS | |
| APIs: health, ingest, search, records, voice session/message, calls, transcript, evaluation, latency, websocket | All | `backend/app/routes/` | `tests/test_api.py` | IN PROGRESS | |
| SQLite tables listed in the brief | All | `backend/app/database.py` | Schema test | IN PROGRESS | |
| Provider abstractions for LLM, ASR, TTS, voice | All | `backend/providers/` | Health payload shows mode | IN PROGRESS | |
| Secrets stay out of git; secret scan | All | `.gitignore`, `.env.example`, `scripts/check_secrets.py` | Scan output | IN PROGRESS | |
| Input validation, safe logging, error handling | All | API bounds + redaction | Validation tests | IN PROGRESS | |
| Synthetic demo data only | All | `data/` marked synthetic | Review of fixtures | IN PROGRESS | |
| Documentation set and demo script | All | `docs/` | File presence | IN PROGRESS | |
| Video walkthrough script | Submission | `docs/DEMO_SCRIPT.md` | Manual recording by the candidate | REQUIRES MANUAL RECORDING | The agent cannot record the candidate's video |
| GitHub repository owned by the candidate | Submission | Local project ready to push | Push instructions | REQUIRES MANUAL ACTION | No remote is created on the candidate's behalf |

## Evaluation weights (from the PDF)

| Area | Weight |
| --- | --- |
| Business problem understanding | 15% |
| Research/domain understanding | 10% |
| End-to-end completeness | 15% |
| Output quality | 20% |
| Functional implementation | 15% |
| AI-tool usage and independent thinking | 10% |
| Feasibility, edge cases, technical depth | 10% |
| Presentation and communication | 5% |

## Rejection conditions to avoid

- Architecture notes only, or a missing major deliverable.
- A knowledge base that is not actually used by the voice agent.
- Invented answers or invented latency.
- Word-for-word translation presented as localization.
- Nudges that appear only after the call, or repeated low-value alerts.

## Implementation plan

1. Project skeleton, config, SQLite, provider interfaces, empty `.env.example`.
2. Q2 ingest, clean, chunk, embed, retrieve, cite, evaluate.
3. Q1 state machine on top of that retriever, with three runnable call scripts.
4. Philippines bot and knowledge, then Indonesia bot, register detection, and an honest accent test.
5. Real-time chunk pipeline, nudge controls, WebSocket, replay script.
6. React dashboard for every surface above.
7. Run tests, evaluation, latency, secret scan, and frontend build. Write only measured numbers into `results/`.
