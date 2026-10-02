# Production plan

The local app is a single process with SQLite and an in-memory WebSocket hub. That is the right shape for a demo and the wrong shape for a contact center.

## Scale

At roughly 10x the demo's concurrent calls, move session state and nudge cooldowns to Redis, move records to Postgres with pgvector, and put audio chunks on a queue (SQS, Pub/Sub, or NATS). Run stateless API workers behind a load balancer. Keep FAISS only for small offline indexes. Rebuild or upsert embeddings in a worker, not in the request that answers the caller.

The in-process hub does not span machines. Replace it with Redis pub/sub or the telephony vendor's event stream.

## Observability

Trace one `call_id` across ASR, retrieval, and nudge generation. Log record ids and confidences, not raw policyholder text. Export P50 and P95 for each stage, queue depth, fallback rate, escalation rate, and nudge suppression rate. Alert when fallback rate jumps or when disclosure nudges stop firing on purchase language.

## Security

Put the API behind authentication. Rate-limit session creation and search. Encrypt audio and transcripts at rest. Keep PII redaction, but treat the regex detector as a backstop, not the control. Separate demo data from any future real recordings. Secrets stay in a manager, not in the image. Tighten CORS to the dashboard origin. The current `*` CORS is for local development.

## Provider fallback

Try the primary ASR, then a second vendor, then a "please repeat" prompt in the caller's language. Do the same for TTS. For the LLM, fall back from the larger model to a smaller one, then to the extractive answer, then to a human. Never fill a provider failure with an ungrounded answer. Escalation already stops the pitch and stores a mock CRM row. In production that row becomes a signed webhook to the real CRM, with retries.

## Cost

Cache embeddings for unchanged chunks. Cache retrieval for repeated FAQ wordings. Skip the LLM on high-confidence extractive answers and on nudge templates that are already specific. Sample audio at the vendor's recommended rate instead of sending raw browser audio twice.

## Noisy audio and multilingual quality

Keep the confidence gate. Add a real diarizer only after measuring its error on agent/customer overlap. For Filipino and Indonesian, evaluate with native speakers on code-switching and on at least one non-Jakarta accent, and publish the WER instead of a detector accuracy number. Do not ship a Javanese lexicon as if it were an acoustic model. Compliance copy for insurance and collections needs a local reviewer before a customer hears it.
