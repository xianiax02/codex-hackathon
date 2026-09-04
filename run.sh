#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x .venv/bin/uvicorn ]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv .venv
    uv pip install --python .venv/bin/python -r requirements.txt
  else
    python3 -m venv .venv
    .venv/bin/python -m ensurepip --upgrade
    .venv/bin/python -m pip install -q -r requirements.txt
  fi
fi

exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8000}"
