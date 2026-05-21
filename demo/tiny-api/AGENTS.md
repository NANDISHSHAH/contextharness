# Tiny API — agent notes

Demo app for [Context Harness](../../HARNESS.md). Critical types: `User`, `Invoice`.

| Module | Role |
|--------|------|
| `services/api/app.py` | Auth + invoice listing |
| `services/billing/invoices.py` | Billing logic |

Run from repo root: `context build demo/tiny-api` then `context harvest "<task>" demo/tiny-api`.
