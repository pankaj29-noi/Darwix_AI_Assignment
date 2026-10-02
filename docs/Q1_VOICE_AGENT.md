# Q1 — Knowledge-grounded voice agent

Use case: health-insurance lead qualification on a web session.

## Flow

`GREETING` asks for consent. A refusal ends the session. After consent the agent collects insurance need, name, age, city, who is covered, current insurance, monthly budget, sum insured, urgency, and callback preference. Questions and objections are answered from the health knowledge base, then the missing field is asked again. Conflicting ages are held until the caller picks one. A request for a person sets `ESCALATED` and stops qualification. When the fields are present, eligibility is computed from `data/kb/health/rules.json` and the spoken explanation is retrieved. The call row stores a mock CRM summary. Nothing is posted to an external webhook.

## Grounding

Every knowledge lookup writes `retrieval_logs` with the question, confidence, fallback flag, and retrieved chunks. The system prompt does not contain the 36-month waiting period, the rate card rule, or the 5 lakh sum insured. A test locks that in.

If retrieval is below `CONFIDENCE_THRESHOLD` (0.12), the agent says it does not have verified information and offers a human. The unsupported scenario asks for the capital of France. The reply does not contain Paris.

## Scenarios executed

| Script | Result on the last run |
| --- | --- |
| Cooperative | Ends, Riya Sharma, age 32, Pune, preliminarily eligible, waiting period cited |
| Objection | Agent text includes the rate-card sentence from the objection record |
| Unsupported then human | Fallback, then `ESCALATED` |
| Incomplete | Age stored as `not provided` |
| Conflict | Both ages are repeated, then 45 is kept |

Transcripts: `transcripts/q1/`.

## Audio

`recordings/q1/synthetic_greeting_en_IN.aiff` is macOS `say` with the Aman `en_IN` voice reading one synthetic sentence. It is not a customer call. A full three-call microphone recording still requires the candidate. See `recordings/MANIFEST.json`.

## What is not claimed

The page can use browser speech recognition and `speechSynthesis`. That is local browser speech. `GET /health` labels the session `mock_web`.
