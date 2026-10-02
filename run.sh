#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Run ./setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
PYTHONPATH=backend uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 &
backend_pid=$!
cleanup() {
  kill "$backend_pid" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "API:  http://127.0.0.1:8000/health"
echo "App:  http://127.0.0.1:5173"
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
