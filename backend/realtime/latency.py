"""Percentile helpers for measured latency samples."""

from __future__ import annotations

import math


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] + (ordered[high] - ordered[low]) * weight


def summarize(samples: list[dict]) -> dict:
    def column(name: str) -> list[float]:
        found = []
        for sample in samples:
            value = sample.get(name)
            if isinstance(value, (int, float)):
                found.append(float(value))
        return found

    report = {}
    for name in ("asr_ms", "signal_ms", "nudge_ms", "delivery_ms", "e2e_ms"):
        values = column(name)
        report[name] = {
            "p50": percentile(values, 50),
            "p95": percentile(values, 95),
            "n": len(values),
        }
    report["llm_ms"] = "NOT MEASURED"
    report["llm_reason"] = "No live LLM call is made in the default nudge path. Template nudges are timed as nudge_ms."
    report["asr_note"] = (
        "asr_ms is the measured time of the mock ASR passthrough on aligned text. "
        "Cloud speech-recognition latency is NOT MEASURED."
    )
    return report
