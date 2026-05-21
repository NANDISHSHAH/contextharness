# Tiny API — Context Harness demo app

A **minimal** multi-module Python app used to learn Context Harness on a repo small enough to build in seconds.

Parent walkthrough: [../USER-JOURNEY.md](../USER-JOURNEY.md)

## Layout

```text
tiny-api/
├── packages/core/models.py    # shared types
├── services/api/app.py        # HTTP entry + auth dependency
├── services/billing/invoices.py
├── tests/test_api.py
└── .pr-review/guidelines.md   # product rules for harvest
```

## Quick run (from monorepo root)

```bash
cd demo/tiny-api
../../scripts/demo-01-setup.sh
../../scripts/demo-02-build.sh
../../scripts/demo-03-harvest.sh "review billing and auth"
```
