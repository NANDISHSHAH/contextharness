"""ContextPack CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from contextpack.core.project import Project
from contextpack.harness.install import install_harness
from contextpack.harness.orientation import build_orientation
from contextpack.harness.validate import validate_harness_docs

app = typer.Typer(
    name="context",
    help="ContextPack — universal AI context runtime",
    no_args_is_help=True,
)
console = Console()


def _run(coro):
    return asyncio.run(coro)


@app.command("init")
def init(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Initialize .contextpack workspace."""
    path = path or Path.cwd()
    project = Project(path)
    _run(project.init())
    console.print(f"[green]✓[/green] initialized ContextPack at {project.context_dir}")


@app.command("build")
def build(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    timing: bool = typer.Option(  # noqa: B008
        False, "--timing", help="Print language breakdown after build"
    ),
    vibe: bool = typer.Option(  # noqa: B008
        False,
        "--vibe",
        help="Animated Pac-Man build display with token/cost tracking",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output build stats"),  # noqa: B008
) -> None:
    """Scan, parse, graph, embed, and index repository."""
    import json

    from contextpack.core.config import get_settings

    path = path or Path.cwd()
    project = Project(path)
    _run(project.init())

    pmap, stats = _run(project.build())

    if json_output:
        import dataclasses
        output = {
            "entities": len(pmap.entities),
            "hub_entities": stats.hub_entities,
            "chunks": stats.chunks,
            "estimated_tokens": stats.estimated_tokens,
            "phase_times": (
                dataclasses.asdict(stats.phase_times)
                if hasattr(stats, 'phase_times')
                else {}
            ),
            "total_time": stats.total_time,
        }
        print(json.dumps(output))
    elif vibe:
        from rich.table import Table

        from contextpack.cli.vibes import vibe_build_footer

        provider = get_settings().embedding_provider
        vibe_build_footer(console, stats, provider)
    else:
        from rich.table import Table

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan", width=8)
        table.add_column(style="dim", width=8)
        table.add_column()

        def _t(phase: str) -> str:
            if hasattr(stats, 'phase_times'):
                return f"{stats.phase_times.get(phase, 0):.2f}s"
            return "0.00s"

        table.add_row(
            "scan",
            _t("scan"),
            (
                f"{stats.files_scanned} files scanned  |  "
                f"[yellow]{stats.files_skipped} skipped[/yellow]"
            ),
        )
        table.add_row(
            "parse",
            _t("parse"),
            f"{stats.entities} entities  (from {stats.files_indexed} files)",
        )
        table.add_row(
            "graph",
            _t("graph"),
            (
                f"{len(pmap.entities)} entities indexed  |  "
                f"{stats.hub_entities} hub nodes"
            ),
        )
        table.add_row(
            "chunk",
            _t("chunk"),
            (
                f"{stats.chunks} chunks  ~{stats.estimated_tokens:,} "
                "tokens estimated"
            ),
        )
        table.add_row(
            "embed",
            _t("embed"),
            (
                f"{stats.embed_count} embedded  |  "
                f"[dim]{stats.store_only_count} store-only[/dim]"
            ),
        )
        table.add_row("store", _t("store"), f"{stats.entities} entities → memory.db")
        table.add_row("[bold]total[/bold]", f"[bold]{stats.total_time:.2f}s[/bold]", "")

        console.print()
        console.print(
            Panel(
                table, title="[green]Build complete[/green]", border_style="green"
            )
        )

    if timing:
        console.print(f"\n[dim]Languages: {pmap.languages}[/dim]")


@app.command("ask")
def ask(
    question: str = typer.Argument(..., help="Question about the codebase"),
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    branch: str | None = typer.Option(  # noqa: B008
        None, "--branch", help="Branch name for Jira ticket extraction"
    ),
    llm: bool = typer.Option(  # noqa: B008
        False,
        "--llm",
        help="Use configured LLM (Azure Foundry / OpenAI) instead of offline synthesis",
    ),
    vibe: bool = typer.Option(  # noqa: B008
        False, "--vibe", help="Show token usage and cost estimate after answer"
    ),
) -> None:
    """Ask using complete harvested agent context."""
    import time as _time

    from contextpack.core.config import get_settings

    path = path or Path.cwd()
    project = Project(path)

    if vibe:
        from contextpack.cli.vibes import vibe_ask_summary

        console.print()
        with console.status("[yellow]ᗧ·····  thinking...[/yellow]", spinner="dots"):
            t0 = _time.perf_counter()
            answer = _run(project.ask(question, branch_name=branch, use_llm=llm))
            elapsed = _time.perf_counter() - t0

        console.print(answer)
        settings = get_settings()
        context_tokens = settings.default_token_budget
        vibe_ask_summary(
            console,
            question=question,
            answer=answer,
            context_tokens=context_tokens,
            provider=settings.llm_provider or "hash",
            elapsed=elapsed,
        )
    else:
        answer = _run(project.ask(question, branch_name=branch, use_llm=llm))
        console.print(answer)


@app.command("harvest")
def harvest(
    query: str = typer.Argument(..., help="Query to harvest context for"),
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    branch: str | None = typer.Option(None, "--branch"),  # noqa: B008
) -> None:
    """Harvest and aggregate all context sources (meetup architecture)."""
    path = path or Path.cwd()
    project = Project(path)
    agg = _run(project.harvest(query, branch_name=branch))
    console.print(agg.to_agent_prompt_block())


@app.command("graph")
def graph(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    query: str = typer.Option("architecture", "--query", "-q"),  # noqa: B008
) -> None:
    """Show dependency graph excerpt."""
    path = path or Path.cwd()
    project = Project(path)
    msg = (
        project.graph_summary()
        if project.context_dir.exists()
        else "Run context build first."
    )
    console.print(msg)


harness_app = typer.Typer(help="Context Harness — workflow layer (hooks, MCP, validation)")
app.add_typer(harness_app, name="harness")


@harness_app.command("install")
def harness_install(
    path: Path | None = typer.Argument(None, help="Target repository"),  # noqa: B008
    force: bool = typer.Option(False, "--force", help="Overwrite existing harness files"),  # noqa: B008
) -> None:
    """Install .cursor hooks, skills, .mcp.json, and AGENTS.md template."""
    path = path or Path.cwd()
    written = install_harness(path, force=force)
    if written:
        console.print("[green]✓[/green] installed Context Harness:")
        for w in written:
            console.print(f"  - {w}")
    else:
        msg = "[yellow]![/yellow] nothing written (files exist; use --force)"
        console.print(msg)


@harness_app.command("orient")
def harness_orient(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    query: str = typer.Option("architecture", "--query", "-q"),  # noqa: B008
) -> None:
    """Print session orientation (same text as sessionStart hook)."""
    path = path or Path.cwd()
    console.print(build_orientation(path.resolve(), query=query))


@harness_app.command("validate")
def harness_validate(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Validate AGENTS.md / CLAUDE.md against graph hubs."""
    path = path or Path.cwd()
    result = validate_harness_docs(path.resolve())
    console.print(result.to_markdown())
    if not result.ok:
        raise typer.Exit(code=1)


@harness_app.command("session-start")
def harness_session_start(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Cursor sessionStart hook (JSON on stdin → JSON on stdout)."""
    from contextpack.cli.harness_hooks import session_start

    path = path or Path.cwd()
    raise typer.Exit(code=session_start(path.resolve()))


@harness_app.command("stop-validate")
def harness_stop_validate(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Cursor stop hook — doc/graph drift follow-up."""
    from contextpack.cli.harness_hooks import stop_validate

    path = path or Path.cwd()
    raise typer.Exit(code=stop_validate(path.resolve()))


@app.command("watch")
def watch_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Watch repository and rebuild incrementally on file changes."""
    from contextpack.watch.watcher import run_watch

    path = path or Path.cwd()
    run_watch(path)


@app.command("changes")
def changes_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    limit: int = typer.Option(  # noqa: B008
        30, "--limit", "-n", help="Number of recent changes to show"
    ),
) -> None:
    """Show file changes recorded by incremental builds (Phase 3)."""
    from rich.table import Table

    path = path or Path.cwd()
    project = Project(path)
    rows = _run(project.recent_changes(limit=limit))
    if not rows:
        msg = (
            "[dim]No change log yet — run `context watch` or `context build`."
            "[/dim]"
        )
        console.print(msg)
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Build", style="dim", width=10)
    table.add_column("Type", width=8)
    table.add_column("File")
    table.add_column("Commit", style="dim", width=10)

    type_colors = {"added": "green", "modified": "yellow", "deleted": "red"}
    for r in rows:
        ctype = r.get("change_type", "?")
        color = type_colors.get(ctype, "white")
        table.add_row(
            r.get("build_id", "?"),
            f"[{color}]{ctype}[/{color}]",
            r.get("path", "?"),
            r.get("git_commit", "") or "—",
        )

    console.print(table)


@app.command("workflows")
def workflows_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """List workflows extracted from the codebase (Phase 5)."""
    path = path or Path.cwd()
    project = Project(path)
    wfs = _run(project.workflows())
    if not wfs:
        msg = "[dim]No workflows yet — run `context build` first.[/dim]"
        console.print(msg)
        return

    console.print(f"\n[bold]Extracted workflows[/bold] ({len(wfs)})\n")
    for wf in wfs:
        name = wf.get("name", "?")
        summary = wf.get("summary", "")
        steps = wf.get("steps", [])
        console.print(f"[bold cyan]{name}[/bold cyan]")
        if summary:
            console.print(f"  [dim]{summary}[/dim]")
        if steps:
            console.print("  " + " → ".join(steps[:8]))
        console.print()


# ── Phase 6: Pre-Skill Engine ────────────────────────────────────────────────

skills_app = typer.Typer(help="Skill gates — pre-edit verification engine (Phase 6)")
app.add_typer(skills_app, name="skills")


@skills_app.command("plan")
def skills_plan(
    files: str = typer.Argument(..., help="Comma-separated changed file paths"),
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    blast_radius: int = typer.Option(  # noqa: B008
        0, "--blast-radius", "-b", help="Known blast radius"
    ),
) -> None:
    """Compute a SkillPlan for the given changed files."""
    from contextpack.skills.manifest import SkillManifest
    from contextpack.skills.router import SkillRouter

    path = path or Path.cwd()
    changed = [f.strip() for f in files.split(",") if f.strip()]
    manifest = SkillManifest.load(path)
    plan = SkillRouter(manifest).route(changed, blast_radius=blast_radius)
    console.print(f"\n[bold]Skill Plan[/bold] for {len(changed)} file(s):\n")
    console.print(plan.summary())


@skills_app.command("run")
def skills_run(
    files: str = typer.Argument(..., help="Comma-separated changed file paths"),
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    blast_radius: int = typer.Option(0, "--blast-radius", "-b"),  # noqa: B008
    agent_id: str = typer.Option("default", "--agent-id"),  # noqa: B008
) -> None:
    """Run the full skill verification gate (plan → enforce → execute → record)."""
    from contextpack.skills.manifest import SkillManifest
    from contextpack.skills.verifier import SkillVerifierLoop

    path = path or Path.cwd()
    changed = [f.strip() for f in files.split(",") if f.strip()]
    manifest = SkillManifest.load(path)
    db = path / ".contextpack" / "memory.db"
    loop = SkillVerifierLoop(db)
    result = _run(
        loop.verify(
            changed, path, manifest, blast_radius=blast_radius, agent_id=agent_id
        )
    )
    console.print()
    console.print(result.to_text())
    if not result.allowed:
        raise typer.Exit(code=1)


@skills_app.command("history")
def skills_history(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    limit: int = typer.Option(10, "--limit", "-n"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show recent evidence bundles (skill gate audit trail)."""
    import json

    from rich.table import Table

    from contextpack.skills.evidence import EvidenceStore

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    if not db.exists():
        if json_output:
            print(json.dumps([]))
        else:
            console.print("[dim]No evidence bundles yet. Run `context skills run` first.[/dim]")
        return

    store = EvidenceStore(db)
    bundles = _run(store.list_recent(limit=limit))

    if json_output:
        output = [
            {
                "action_id": b.action_id,
                "agent_id": b.agent_id,
                "files": b.files_modified,
                "files_modified": b.files_modified,
                "skill_results": b.skill_results if hasattr(b, 'skill_results') else [],
                "passed": b.passed,
            }
            for b in bundles
        ]
        print(json.dumps(output))
    else:
        if not bundles:
            msg = (
                "[dim]No evidence bundles yet. Run `context skills run` first."
                "[/dim]"
            )
            console.print(msg)
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Action ID", style="dim", width=14)
        table.add_column("Agent", width=10)
        table.add_column("Files")
        table.add_column("Skills", width=30)
        table.add_column("Result", width=8)
        for b in bundles:
            icon = "[green]✅[/green]" if b.passed else "[red]❌[/red]"
            skills_str = " ".join(
                (("✅" if r.get("passed") else "❌") + r["skill"])
                for r in b.skill_results[:4]
            )
            table.add_row(
                b.action_id,
                b.agent_id,
                ", ".join(b.files_modified[:2]),
                skills_str,
                icon,
            )
        console.print(table)


# ── Phase 7: Contracts ────────────────────────────────────────────────────────

contracts_app = typer.Typer(help="Semantic contracts — symbol contracts & invariants (Phase 7)")
app.add_typer(contracts_app, name="contracts")


@contracts_app.command("show")
def contracts_show(
    symbol: str = typer.Argument("", help="Symbol name to look up (empty = all)"),
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Show extracted contracts for a symbol."""
    from contextpack.contracts.registry import ContractRegistry

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    reg = ContractRegistry(db)
    if symbol:
        results = _run(reg.search(symbol, limit=20))
    else:
        results = _run(reg.list_all(limit=30))
    if not results:
        msg = "[dim]No contracts indexed. Run `context build` first.[/dim]"
        console.print(msg)
        return
    console.print(reg.format_for_context(results))


@contracts_app.command("check")
def contracts_check(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
) -> None:
    """Check architectural invariants against the current codebase."""
    from contextpack.contracts.invariants import InvariantConfig, InvariantGuard

    path = path or Path.cwd()
    config = InvariantConfig.load(path)
    if not config.invariants:
        msg = (
            "[yellow]No invariants.yml found. "
            "Create .contextpack/invariants.yml[/yellow]"
        )
        console.print(msg)
        return
    db = path / ".contextpack" / "memory.db"
    guard = InvariantGuard(db)
    violations = guard.check(config, [])  # full check without specific diff
    if not violations:
        console.print("[green]✅ No invariant violations[/green]")
    else:
        console.print(f"[red]❌ {len(violations)} violation(s):[/red]")
        for v in violations:
            console.print(v.to_text())
        raise typer.Exit(code=1)


# ── Phase 8: Governance ───────────────────────────────────────────────────────

@app.command("debt")
def debt_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    limit: int = typer.Option(30, "--limit", "-n"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show per-module context debt scores (Phase 8)."""
    import json

    from contextpack.governance.debt import ContextDebtTracker

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    if not db.exists():
        if json_output:
            print(json.dumps([]))
        else:
            console.print("[dim]Run 'context build' first to analyze context debt[/dim]")
        return

    tracker = ContextDebtTracker(db)
    records = _run(tracker.list_all(limit=limit))

    if json_output:
        output = [
            {
                "module": r.file_path,
                "score": r.debt_score,
                "tier": r.action,
                "days_stale": r.days_stale,
                "churn": r.churn_rate,
                "hub_centrality": r.hub_centrality,
            }
            for r in records
        ]
        print(json.dumps(output))
    else:
        console.print(tracker.format_report(records))


@app.command("locks")
def locks_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show active agent locks (multi-agent conflict table) (Phase 8)."""
    import datetime
    import json

    from rich.table import Table

    from contextpack.governance.locks import AgentLockTable

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    if not db.exists():
        if json_output:
            print(json.dumps([]))
        else:
            console.print("[dim]No active locks.[/dim]")
        return

    lock_table = AgentLockTable(db)
    active = _run(lock_table.list_active())

    if json_output:
        output = [
            {
                "lock_id": lock.lock_id,
                "agent_id": lock.agent_id,
                "files": lock.files,
                "acquired_at": (
                    datetime.datetime.fromtimestamp(
                        lock.acquired_at
                    ).isoformat()
                    if hasattr(lock, 'acquired_at')
                    else None
                ),
                "expires_at": datetime.datetime.fromtimestamp(
                    lock.expires_at
                ).isoformat(),
            }
            for lock in active
        ]
        print(json.dumps(output))
    else:
        if not active:
            console.print("[dim]No active locks.[/dim]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Lock ID", style="dim", width=14)
        table.add_column("Agent", width=12)
        table.add_column("Files")
        table.add_column("Expires", width=10)
        for lock in active:
            exp = (
                datetime.datetime.fromtimestamp(lock.expires_at).strftime(
                    "%H:%M:%S"
                )
            )
            table.add_row(
                lock.lock_id,
                lock.agent_id,
                ", ".join(lock.files[:3]),
                exp,
            )
        console.print(table)


# ── Phase 9: Adaptive Intelligence ───────────────────────────────────────────

@app.command("patterns")
def patterns_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    limit: int = typer.Option(20, "--limit", "-n"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show recurring failure patterns (Phase 9)."""
    import json

    from contextpack.adaptive.patterns import FailurePatternStore

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    if not db.exists():
        if json_output:
            print(json.dumps([]))
        else:
            console.print("[dim]No failure patterns recorded yet.[/dim]")
        return

    store = FailurePatternStore(db)
    patterns = _run(store.list_all(limit=limit))

    if json_output:
        output = [
            {
                "pattern_id": (
                    p.pattern_id
                    if hasattr(p, 'pattern_id')
                    else f"{p.failure_class}_{p.file_pattern}"
                ),
                "failure_class": p.failure_class,
                "category": p.failure_class,
                "glob": p.file_pattern,
                "frequency": p.frequency,
                "count": p.frequency,
                "skill": p.skill if hasattr(p, 'skill') else None,
                "remediation_hint": (
                    p.remediation_hint
                    if hasattr(p, 'remediation_hint')
                    else None
                ),
            }
            for p in patterns
        ]
        print(json.dumps(output))
    else:
        if not patterns:
            msg = "[dim]No failure patterns recorded yet.[/dim]"
            console.print(msg)
            return
        console.print(f"\n[bold]Failure Patterns[/bold] ({len(patterns)})\n")
        for p in patterns:
            color = "red" if p.frequency >= 5 else "yellow"
            console.print(
                f"[{color}]{p.failure_class}[/{color}]  ×{p.frequency}  "
                f"[{p.skill}]  {p.file_pattern}"
            )
            if p.remediation_hint:
                console.print(f"  [dim]{p.remediation_hint}[/dim]")


@app.command("coupling")
def coupling_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    days: int = typer.Option(30, "--days", "-d", help="Trend window in days"),  # noqa: B008
) -> None:
    """Show architectural coupling trend over time (Phase 9)."""
    from contextpack.adaptive.coupling import CouplingMonitor

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    monitor = CouplingMonitor(db)
    trend = _run(monitor.trend(days=days))
    console.print(trend.to_text())


@app.command("snapshots")
def snapshots_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    limit: int = typer.Option(10, "--limit", "-n"),  # noqa: B008
    diff: str | None = typer.Option(  # noqa: B008
        None, "--diff", help="Diff two snapshot IDs: before,after"
    ),
) -> None:
    """List or diff context snapshots (Phase 9)."""
    from contextpack.adaptive.snapshots import ContextSnapshotEngine

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    engine = ContextSnapshotEngine(db)

    if diff:
        parts = diff.split(",")
        if len(parts) != 2:
            msg = (
                "[red]--diff requires two snapshot IDs: "
                "before_id,after_id[/red]"
            )
            console.print(msg)
            raise typer.Exit(code=1)
        before = _run(engine.get(parts[0].strip()))
        after = _run(engine.get(parts[1].strip()))
        if not before or not after:
            msg = "[red]One or both snapshot IDs not found.[/red]"
            console.print(msg)
            raise typer.Exit(code=1)
        result = engine.diff(before, after)
        console.print(result.to_text())
    else:
        snaps = _run(engine.list_recent(limit=limit))
        if not snaps:
            console.print("[dim]No snapshots yet.[/dim]")
            return
        console.print(f"\n[bold]Context Snapshots[/bold] ({len(snaps)})\n")
        import datetime
        for s in snaps:
            dt = datetime.datetime.fromtimestamp(s.timestamp).strftime(
                "%Y-%m-%d %H:%M"
            )
            nodes = s.graph_state.get("nodes", "?")
            console.print(
                f"[cyan]{s.snapshot_id}[/cyan]  {dt}  [{s.agent_id}]  "
                f"nodes={nodes}  {s.task[:50]}"
            )


if __name__ == "__main__":
    app()
