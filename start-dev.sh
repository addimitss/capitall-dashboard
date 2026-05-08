#!/usr/bin/env bash
# Dev launcher: starts backend (uvicorn) and frontend (vite) concurrently.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() { echo; echo "Shutting down…"; jobs -p | xargs -r kill 2>/dev/null || true; }
trap cleanup EXIT INT TERM

# Backend
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
fi
[ -f .env ] || cp .env.example .env
echo "▶ Backend: http://localhost:8000  (docs: /docs)"
./.venv/bin/uvicorn app.main:app --reload --port 8000 &

# Frontend
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then npm install --no-audit --no-fund; fi
echo "▶ Frontend: http://localhost:5173"
npm run dev &

wait
