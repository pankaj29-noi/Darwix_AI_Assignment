# Latency report

Source file: `results/latency_results.json`.

Scenario: `full_demo`. Chunks: 7. Replay speed for this measurement: 0, so the figures exclude the intentional wait between turns. Clock: `time.perf_counter` around each stage in `RealtimePipeline.process_chunk`.

## Component times in milliseconds

| Stage | P50 | P95 | n | Meaning |
| --- | --- | --- | --- | --- |
| ASR passthrough | 0.001584 | 0.001921 | 7 | Mock ASR on text that was already known. Cloud ASR is NOT MEASURED. |
| Signal extraction | 0.028541 | 0.039529 | 7 | Rule detector. |
| LLM | NOT MEASURED | NOT MEASURED | 0 | No model call is made for nudges. |
| Nudge generation | 0.005584 | 0.008488 | 7 | Threshold, cooldown, and copy. |
| Delivery | 1.130834 | 1.381591 | 7 | SQLite writes for the transcript, signals, nudges, and latency row. |
| End to end | 1.178541 | 1.426871 | 7 | Sum of the measured local stages above. LLM is excluded. |

These are local CPU and SQLite times. They are not a claim about a streaming speech vendor, a network round trip to a browser, or a hosted model. A production P50 would be dominated by ASR and the model. Those stages stay `NOT MEASURED` until a credentialed run is timed the same way.

The Live Intelligence page shows the per-chunk `latency_ms` object from the WebSocket event, including the string `NOT MEASURED` for the LLM field.
