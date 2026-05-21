#!/usr/bin/env bash
# Demo step 2 — build index (creates .contextpack/)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO="$ROOT/demo/tiny-api"
cd "$ROOT"
uv run context build "$DEMO" --timing
echo ""
echo "Artifacts:"
ls -lh "$DEMO/.contextpack/" 2>/dev/null || true
