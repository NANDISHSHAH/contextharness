#!/usr/bin/env bash
# Demo step 1 — install harness on tiny-api
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO="$ROOT/demo/tiny-api"
cd "$ROOT"
uv sync --extra harness
uv run context init "$DEMO"
uv run context harness install "$DEMO" --force 2>/dev/null || uv run context harness install "$DEMO"
echo "✓ tiny-api initialized (see demo/tiny-api/.cursor and AGENTS.md)"
