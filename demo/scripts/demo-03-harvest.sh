#!/usr/bin/env bash
# Demo step 3 — harvest agent context for a task
set -euo pipefail
QUERY="${1:-explain auth and billing flow}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO="$ROOT/demo/tiny-api"
cd "$ROOT"
uv run context harvest "$QUERY" "$DEMO" | head -80
echo ""
echo "... (truncated — pipe to file: context harvest \"$QUERY\" $DEMO > pack.md)"
