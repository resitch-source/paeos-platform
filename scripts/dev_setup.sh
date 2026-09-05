#!/usr/bin/env bash
# One-shot local backend setup for PAEOS-FX development.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Creating backend virtualenv"
python3 -m venv backend/.venv

echo "==> Installing backend (dev extras)"
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -e "backend[dev]"

if [ ! -f backend/.env ]; then
  echo "==> Creating backend/.env from example"
  cp backend/.env.example backend/.env
fi

echo "==> Running lint, typecheck, and tests"
cd backend
.venv/bin/ruff check .
.venv/bin/mypy paeos_fx || true
.venv/bin/pytest

echo "==> Done. Start the API with: make run"
