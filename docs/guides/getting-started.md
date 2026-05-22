# Getting started

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) recommended (or pip)
- Git repository to analyze

## Installation

```bash
git clone <repository-url>
cd contextharness

uv sync
uv pip install -e .

# Optional: Chroma vector backend (slow cold start)
uv sync --extra chroma

# Optional: dev tools (pytest, ruff, mypy, mkdocs)
uv sync --extra dev
```

Verify:

```bash
context --help
python -c "from contextpack import Project; print('OK')"
```

---

## First project in 60 seconds

```bash
# Use the bundled sample repo
context init examples/sample_repo
context build examples/sample_repo
context harvest "How does authentication work?" examples/sample_repo
```

You should see `<extra_instructions>` with **Code Context** and **Product Context (Team Guidelines)** sections.

---

## CLI workflow

| Step | Command | What happens |
|------|---------|--------------|
| 1 | `context init <path>` | Creates `.contextpack/` |
| 2 | `context build <path>` | Scan, parse, graph, embed, index |
| 2b | `context build <path> --vibe` | Same, with animated Pac-Man display + token/cost footer |
| 3 | `context harvest "<query>" <path>` | Full agent context pack |
| 4 | `context ask "<question>" <path>` | Offline synthesized answer |
| 4b | `context ask "..." <path> --vibe` | Same, with thinking spinner + token trace panel |
| 5 | `context ask "..." <path> --llm` | Azure/OpenAI answer (needs `.env`) |
| 6 | `context graph <path>` | Graph neighbourhood excerpt |

---

## Environment file

```bash
cp .env.example .env
```

Defaults work offline:

- `CONTEXTPACK_EMBEDDING_PROVIDER=hash`
- `CONTEXTPACK_VECTOR_STORE=sqlite`

---

## Optional: team guidelines

Add product context for agents:

```bash
mkdir -p my-repo/.pr-review
echo "# Rules\n- Use OAuth2 for auth" > my-repo/.pr-review/guidelines.md
context build my-repo
```

---

## Optional: Azure AI Foundry

See [Azure AI Foundry integration](azure-foundry.md).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Slow first run | Avoid `--all-extras`; don't import Chroma unless needed |
| `Project not built` | Run `context build` first |
| Empty code section | Check languages supported (py, ts, js) |
| Jira always skipped | Set `JIRA_*` and include `PROJ-123` in branch name |
| Too many files indexed | Add custom dirs to `.contextpackignore`; `.gitignore` is read automatically |
| Want to see phase timings | Run `context build --vibe` for live animated breakdown |

---

## Next steps

- [Package usage (SDK)](package-usage.md)
- [Agent integration](agent-integration.md)
- [Architecture overview](../architecture/overview.md)
