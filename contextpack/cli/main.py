"""ContextPack CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

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
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
) -> None:
    """Initialize .contextpack workspace."""
    project = Project(path)
    _run(project.init())
    console.print(f"[green]✓[/green] initialized ContextPack at {project.context_dir}")


@app.command("build")
def build(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
    timing: bool = typer.Option(False, "--timing", help="Print language breakdown after build"),
    vibe: bool = typer.Option(False, "--vibe", help="Animated Pac-Man build display with token/cost tracking"),
) -> None:
    """Scan, parse, graph, embed, and index repository."""
    from contextpack.core.config import get_settings

    project = Project(path)
    _run(project.init())

    if vibe:
        from contextpack.cli.vibes import VibeBuild, vibe_build_footer
        from rich.table import Table

        provider = get_settings().embedding_provider
        with VibeBuild(console) as on_phase:
            pmap, stats = _run(project.build(on_phase=on_phase))
        vibe_build_footer(console, stats, provider)
    else:
        from rich.table import Table

        pmap, stats = _run(project.build())

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold cyan", width=8)
        table.add_column(style="dim", width=8)
        table.add_column()

        def _t(phase: str) -> str:
            return f"{stats.phase_times.get(phase, 0):.2f}s"

        table.add_row("scan",  _t("scan"),  f"{stats.files_scanned} files scanned  |  [yellow]{stats.files_skipped} skipped[/yellow]")
        table.add_row("parse", _t("parse"), f"{stats.entities} entities  (from {stats.files_indexed} files)")
        table.add_row(
            "graph", _t("graph"),
            f"{len(pmap.entities)} entities indexed  |  {stats.hub_entities} hub nodes",
        )
        table.add_row("chunk", _t("chunk"), f"{stats.chunks} chunks  ~{stats.estimated_tokens:,} tokens estimated")
        table.add_row(
            "embed", _t("embed"),
            f"{stats.embed_count} embedded  |  [dim]{stats.store_only_count} store-only[/dim]",
        )
        table.add_row("store", _t("store"), f"{stats.entities} entities → memory.db")
        table.add_row("[bold]total[/bold]", f"[bold]{stats.total_time:.2f}s[/bold]", "")

        console.print()
        console.print(Panel(table, title="[green]Build complete[/green]", border_style="green"))

    if timing:
        console.print(f"\n[dim]Languages: {pmap.languages}[/dim]")


@app.command("ask")
def ask(
    question: str = typer.Argument(..., help="Question about the codebase"),
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Branch name for Jira ticket extraction"),
    llm: bool = typer.Option(
        False,
        "--llm",
        help="Use configured LLM (Azure Foundry / OpenAI) instead of offline synthesis",
    ),
    vibe: bool = typer.Option(False, "--vibe", help="Show token usage and cost estimate after answer"),
) -> None:
    """Ask using complete harvested agent context."""
    import time as _time

    from contextpack.core.config import get_settings

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
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
    branch: Optional[str] = typer.Option(None, "--branch"),
) -> None:
    """Harvest and aggregate all context sources (meetup architecture)."""
    project = Project(path)
    agg = _run(project.harvest(query, branch_name=branch))
    console.print(agg.to_agent_prompt_block())


@app.command("graph")
def graph(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
    query: str = typer.Option("architecture", "--query", "-q"),
) -> None:
    """Show dependency graph excerpt."""
    project = Project(path)
    console.print(project.graph_summary() if project.context_dir.exists() else "Run context build first.")


harness_app = typer.Typer(help="Context Harness — workflow layer (hooks, MCP, validation)")
app.add_typer(harness_app, name="harness")


@harness_app.command("install")
def harness_install(
    path: Path = typer.Argument(Path.cwd(), help="Target repository"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing harness files"),
) -> None:
    """Install .cursor hooks, skills, .mcp.json, and AGENTS.md template."""
    written = install_harness(path, force=force)
    if written:
        console.print("[green]✓[/green] installed Context Harness:")
        for w in written:
            console.print(f"  - {w}")
    else:
        console.print("[yellow]![/yellow] nothing written (files exist; use --force)")


@harness_app.command("orient")
def harness_orient(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
    query: str = typer.Option("architecture", "--query", "-q"),
) -> None:
    """Print session orientation (same text as sessionStart hook)."""
    console.print(build_orientation(path.resolve(), query=query))


@harness_app.command("validate")
def harness_validate(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
) -> None:
    """Validate AGENTS.md / CLAUDE.md against graph hubs."""
    result = validate_harness_docs(path.resolve())
    console.print(result.to_markdown())
    if not result.ok:
        raise typer.Exit(code=1)


@harness_app.command("session-start")
def harness_session_start(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
) -> None:
    """Cursor sessionStart hook (JSON on stdin → JSON on stdout)."""
    from contextpack.cli.harness_hooks import session_start

    raise typer.Exit(code=session_start(path.resolve()))


@harness_app.command("stop-validate")
def harness_stop_validate(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
) -> None:
    """Cursor stop hook — doc/graph drift follow-up."""
    from contextpack.cli.harness_hooks import stop_validate

    raise typer.Exit(code=stop_validate(path.resolve()))


@app.command("watch")
def watch_cmd(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
) -> None:
    """Watch repository and rebuild incrementally on file changes."""
    from contextpack.watch.watcher import run_watch

    run_watch(path)


@app.command("changes")
def changes_cmd(
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
    limit: int = typer.Option(30, "--limit", "-n", help="Number of recent changes to show"),
) -> None:
    """Show file changes recorded by incremental builds (Phase 3)."""
    from rich.table import Table

    project = Project(path)
    rows = _run(project.recent_changes(limit=limit))
    if not rows:
        console.print("[dim]No change log yet — run `context watch` or `context build`.[/dim]")
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
    path: Path = typer.Argument(Path.cwd(), help="Repository path"),
) -> None:
    """List workflows extracted from the codebase (Phase 5)."""
    project = Project(path)
    wfs = _run(project.workflows())
    if not wfs:
        console.print("[dim]No workflows detected — codebase may be too small for pattern recognition, or run `context build` first.[/dim]")
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


if __name__ == "__main__":
    app()
