# Q4 — Live insights and nudges

## Pipeline

`data/realtime/scenarios.json` is split into timed turns. `RealtimePipeline.process_chunk` runs ASR, signal detection, nudge control, SQLite writes, and a WebSocket publish for every turn. `POST /realtime/replay` sleeps between turns when speed is greater than 0, so the dashboard receives events before `replay_complete`.

Speaker labels are the `speaker` field on each scripted turn. This is not audio diarization. Unknown audio would be labeled `unknown`.

## Signals

Detected types: `intent_shift`, `compliance`, `frustration`, `buying_signal`, `missed_opportunity`, `callback`, and `payment_difficulty`.

A nudge is emitted only when confidence is at least 0.62. The same type and topic is cooled down for 45 seconds of call time and capped at two emissions. Compliance outranks frustration, payment difficulty, missed opportunity, callback, buying, then intent shift. Each signal carries `expires_at`.

Family mentions share the topic `family_cover`. A second vehicle uses `multi_vehicle`. The nudge text is the signal's recommended action. The evidence field is the triggering line, or a sentence that quotes it for a missing disclosure.

## Last run

From `results/nudge_results.json`:

| Scenario | Signals | Nudges |
| --- | --- | --- |
| cross_sell | 1 | 1 missed opportunity |
| multi_vehicle | 2 | 2 missed opportunity (family and vehicle) |
| compliance | 3 | 2 (compliance and buying) |
| frustration | 1 | 1 |
| callback | 1 | 1 |
| payment | 1 | 1 |
| intent_shift | 1 | 1 |
| noisy | 0 | 0 |
| neutral | 0 | 0 |
| full_demo | 6 | 5 |

Neutral and noisy nudge counts are the false-positive check. Both were 0. Noisy text with `asdf` and `qwerty` does not clear the threshold. A repeated frustration inside the cooldown produces one nudge; a third repeat after the cap produces none. That is covered by `tests/test_realtime.py`.

## Noisy audio

The noisy scenario is ambiguous text, not a measured recording of a noisy room. Word error rate is NOT MEASURED. Expected behavior, which held on this run: no nudge.

## What would be wrong

A batch job that waits for a finished file and then summarizes it would not meet this question. The WebSocket events are produced per chunk.
