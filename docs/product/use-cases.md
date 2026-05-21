# Use cases

## 1. Domain-aware PR review

**Actors:** Platform team, reviewers, GitLab/GitHub

**Flow:**

1. MR opened on branch `feature/PAY-442-refunds`
2. CI runs `context build` (cached)
3. `context harvest "functional review of refund changes" --branch feature/PAY-442-refunds`
4. LLM receives code graph + Jira AC + guidelines + test behaviour
5. Bot comment: AC gaps, behavioural mismatches, code smells

**Value:** Catches “ticket says X, code does Y” before human review.

---

## 2. Onboarding copilot

**Actors:** New engineer, internal docs

**Flow:**

1. `context build` on monorepo once per day
2. Developer asks: “How does billing integrate with auth?”
3. `context ask` returns dependency-aware answer with real module names

**Value:** Reduces weeks of architecture tours.

---

## 3. Security-sensitive change analysis

**Actors:** Security champion, release manager

**Flow:**

1. Harvest query: “auth token handling and session storage”
2. Guardrails flag missing security guidelines if `SECURITY.md` not in search paths
3. LLM review focused on auth subgraph

**Value:** Repeatable security pass without manual file hunting.

---

## 4. Azure Foundry enterprise agent

**Actors:** ML platform, regulated industry customer

**Flow:**

1. Agent in VNet calls ContextPack locally on repo
2. `ask(..., use_llm=True)` → Azure deployment only
3. Embeddings also on Azure — no OpenAI.com data path

**Value:** Compliance + rich context in one pipeline.

---

## 5. Cursor / IDE augmentation

**Actors:** Individual developer

**Flow:**

1. `harvest` for current task
2. `CursorAdapter.inject` → attach to Composer session

**Value:** Same context engine as headless agents, better than manual @file selection.

---

## 6. LangGraph multi-step workflow

**Actors:** Automation team

**Flow:**

1. Node `load_context` → harvest
2. Node `plan` → LLM with pack
3. Node `implement` → tools with smaller follow-up packs

**Value:** Separation of context building from orchestration logic.

---

## Related

- [Vision & benefits](vision-and-benefits.md)
- [Agent integration](../guides/agent-integration.md)
