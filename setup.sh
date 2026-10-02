#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11 or newer is required."
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js and npm are required."
  exit 1
fi

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
if [[ ! -f .env ]]; then
  cp .env.example .env
fi
(
  cd frontend
  npm install
)
echo
echo "Setup complete. Start the system with ./run.sh"
echo "Then open http://127.0.0.1:5173"
