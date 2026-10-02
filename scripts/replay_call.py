"""Replay a labeled call through the API at a chosen speed.

Example:
  python scripts/replay_call.py --scenario full_demo --speed 1
"""

from __future__ import annotations

import argparse
import json
import time
from urllib.request import Request, urlopen


def post(base: str, path: str, payload: dict) -> dict:
    request = Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request) as response:
        return json.loads(response.read().decode())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenario", default="full_demo")
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()
    created = post(args.base_url, "/realtime/session", {})
    started = time.perf_counter()
    result = post(
        args.base_url,
        "/realtime/replay",
        {"call_id": created["call_id"], "scenario": args.scenario, "speed": args.speed},
    )
    print(json.dumps({"started_at_s": time.perf_counter() - started, **created, **result}, indent=2))
    print("Open the Live Intelligence page and connect this call id to watch events.")
    print("This command starts the server-side replay. It does not invent latency numbers.")


if __name__ == "__main__":
    main()
