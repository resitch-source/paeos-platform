#!/bin/bash
# PAEOS SessionStart hook: provision the backend environment so tests and
# linters are runnable in Claude Code on the web. Idempotent and non-interactive.
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
BACKEND="$PROJECT_DIR/backend"

# Backend: create venv and install dev dependencies if missing.
if [ -d "$BACKEND" ]; then
  if [ ! -x "$BACKEND/.venv/bin/python" ]; then
    python3 -m venv "$BACKEND/.venv"
  fi
  "$BACKEND/.venv/bin/pip" install --quiet --upgrade pip
  "$BACKEND/.venv/bin/pip" install --quiet -e "$BACKEND[dev]"

  # Expose the backend venv on PATH for the session.
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export PATH=\"$BACKEND/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  fi
fi

echo "PAEOS session environment ready (backend venv provisioned)."
