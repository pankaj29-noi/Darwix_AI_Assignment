# Demo script

Aim for a short screen recording. Say when a number comes from `results/` and when something was not measured.

1. Show the README map and `GET /health`, including the mock-mode sentence.
2. Show the two mermaid diagrams in `docs/ARCHITECTURE.md`.
3. On Knowledge Base, click rebuild if you want, then search the waiting-period question. Point at the source file and the score.
4. Search `What is the capital of France?` and show the fallback with no Paris and no citation.
5. Open Voice Agent and run `cooperative`. Show the qualification fields, the 36-month citation, and the preliminary eligibility line.
6. Run `unsupported`. Show the fallback, then the human escalation and the stopped pitch.
7. Open Philippines and run `taglish` and `objection`. Read one localization example and its "why" from the side panel.
8. Open Indonesia, run `colloquial`, then read the accent panel: actual transcript `NOT MEASURED`, and the repeat-slowly fallback.
9. Mention Damayanti for Indonesian TTS and the missing Filipino voice.
10. Open Live Intelligence, scenario `full_demo`, speed `1`. Let the family line, the missing waiting-period line, and the frustration line produce nudges before the replay completes. Point at evidence text.
11. Open Latency and say the local P50/P95, then say cloud ASR and LLM are `NOT MEASURED`.
12. Open Evaluation and the test summary: 34 passed.
13. State the limits: lexical embeddings, no diarization, no phone call, lexicon is not accent ASR.
14. Close with one production change you would make first: pgvector plus a real ASR vendor, still behind the same interfaces, still failing closed.

Do not play the `.aiff` files as if they were customers.
