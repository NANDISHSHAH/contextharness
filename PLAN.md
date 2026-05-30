# ContextHarness + Membrane VSCode — Strategic Plan

_Date: 2026-05-30_

---

## TL;DR

Microsoft's AI Engineering Coach and ContextHarness **are not competitors**. They solve different problems:

| | AI Engineering Coach (Microsoft) | ContextHarness + Membrane |
|---|---|---|
| **Who it helps** | The human developer | The AI agents |
| **What it tracks** | Your AI usage habits & patterns | Codebase graph, agent conflicts, contracts |
| **Core value** | "How can YOU use AI better?" | "How can AGENTS safely edit YOUR code?" |
| **Data source** | Session logs from Claude/VS Code | Parsed AST + dependency graph |

You are building **agent governance infrastructure** — something Microsoft's tool doesn't touch. That's the right bet. But the extension is not yet working reliably enough to demonstrate the value. This plan fixes that.

---

## Problem Diagnosis

The membrane-vscode extension has 3 failure modes today:

1. **Backend fragility** — The lifecycle (detect uv → install → build env → spin MCP server) fails silently; tree views show placeholder text indefinitely.
2. **No feedback loop** — When the backend isn't ready, there's no user-facing status that guides them to fix it (no progress indicator, no "Run Build Index" prompt with one click).
3. **Feature-to-UI gap** — The Python backend (Phases 1–9) is largely complete, but the VS Code UI only exposes ~30% of it in a usable way.

---

## Phase 1 — Make It Actually Work (2–3 weeks)

**Goal:** A user can install the extension, run "Build Index", and see real data in every panel.

### 1.1 Fix Extension Lifecycle
- Add a status bar item that shows: `Membrane: Ready` / `Membrane: Building...` / `Membrane: Error (click for details)`
- Replace silent failures in `installer.ts` with explicit error messages piped to an Output Channel
- Add a "Setup Wizard" command that runs: check uv → install contextpack → build index → verify MCP connection

### 1.2 Fix Tree View Providers
- `playbookProvider.ts` and `trustScoresProvider.ts` are new/empty — implement data polling from MCP tools (`get_failure_patterns`, `get_context_debt`)
- All providers: replace "No project map found" with a button node that triggers `Build Index`
- Add loading states (spinning icon) while MCP calls are in-flight

### 1.3 Fix MCP Communication
- Add a health-check command that calls `project_outline` and shows the result in a notification
- Expose MCP errors in the Output Channel, not silently swallowed

**Success criterion:** Zero placeholder text when the index exists.

---

## Phase 2 — Surface the Unique Value (2–3 weeks)

These are the features nobody else has. Build them to be compelling and polished.

### 2.1 Skill Gate — Pre-commit Enforcement (your killer feature)
- Add a CodeLens on changed files: "Run Skill Gate" (calls `run_skill_gate`)
- Show gate results as VS Code Diagnostics (Problems panel) — red squiggles for violations
- Block `git commit` via a workspace task hook if skill gates fail
- Show blast radius score as an inline annotation

### 2.2 Agent Conflict Detection (live)
- `check_agent_conflicts` MCP tool → show as a status bar warning: `2 Agent Conflicts`
- Clicking opens a panel listing which files are locked by which agent and since when
- "Steal Lock" and "Release Lock" buttons

### 2.3 Context Debt Dashboard (lightweight)
- A WebView panel (not a third-party dependency) showing the top 5 most indebted modules
- Bar chart using VS Code's color tokens (no external charting library needed initially)
- Refresh button + auto-refresh on file save

### 2.4 Failure Pattern Warnings
- On file open: if `get_failure_patterns` returns patterns matching the current file, show a VS Code warning notification: "This file has 3 known failure patterns — click to review"
- Link to a simple panel listing each pattern with evidence

---

## Phase 3 — Take Inspiration from AI Engineering Coach (3–4 weeks)

Microsoft's best ideas that translate well to your domain:

### 3.1 Anti-Pattern Rules (adapted for agents, not humans)
- AI Coach has 45 rules for human AI usage. You can have rules for **agent behavior**: "Never edit more than N files per skill gate run", "Always harvest context before editing a hub file", etc.
- Editable rule set stored in `.contextpack/agent-rules.json`
- Membrane shows a Rules panel where users can enable/disable/edit rules

### 3.2 Trust Score Visualization
- AI Coach has XP tiers. You have trust scores per agent.
- Show per-agent trust in a leaderboard-style panel: skill gate pass %, merge quality, conflict incidents
- Not gamification — this is audit trail for teams using multiple AI agents

### 3.3 Session Briefing in Chat
- AI Coach analyzes session logs. You can add a VS Code Chat participant (`@membrane`) that responds to `@membrane status` with: current index staleness, top debt modules, open agent conflicts
- Requires VS Code Chat Participant API (same as GitHub Copilot extensions)

---

## Phase 4 — Differentiation Moat (ongoing)

Things Microsoft is unlikely to build because they conflict with their interests:

| Feature | Why it's yours |
|---|---|
| **Multi-agent conflict resolution** | Microsoft builds single-agent Copilot; multi-agent is your terrain |
| **Semantic contracts (AST-level)** | AI Coach looks at session logs, not code structure |
| **Coupling trend monitoring** | Architectural decay over time — nobody tracks this in real-time |
| **Harness hooks** (`sessionStart`/`stop`) | Pre/post-session governance — unique to your runtime model |
| **Jira-linked context harvest** | Bridging tickets ↔ code graph is a enterprise workflow nobody has nailed |

---

## Immediate Next Steps (this week)

1. **Fix the status bar + Output Channel** — so you can see what's failing during development
2. **Implement `playbookProvider.ts`** using `get_failure_patterns` MCP tool
3. **Implement `trustScoresProvider.ts`** using `get_context_debt` + agent trust data
4. **Test end-to-end**: install fresh, build index, verify all 7 panels show real data
5. **Add Skill Gate as VS Code Diagnostics** — this is the one demo that will make people say "I need this"

---

## What to Ignore (for now)

- Do **not** try to replicate AI Coach's session log analytics — you don't have access to Claude/VS Code logs the way Microsoft does (they have internal telemetry hooks)
- Do **not** build a full charting dashboard like AI Coach — start with tree views and simple WebViews
- Do **not** add Jira integration until the core graph features are working reliably

---

## Summary

Your tool is architecturally more sophisticated than AI Engineering Coach. The gap is polish and reliability of the VS Code extension layer. Fix the lifecycle, surface the 2–3 genuinely unique features (skill gates, agent conflict detection, failure pattern warnings) in a way that "just works", and you have something Microsoft doesn't offer.

