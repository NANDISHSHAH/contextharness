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
    timing: bool = typer.Option(False, "--timing", help="Print verbose per-file timings"),
) -> None:
    """Scan, parse, graph, embed, and index repository."""
    from rich.table import Table

    project = Project(path)
    _run(project.init())
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
) -> None:
    """Ask using complete harvested agent context."""
    project = Project(path)
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
    """Watch repository and rebuild on changes."""
    from contextpack.watch.watcher import run_watch

    run_watch(path)


if __name__ == "__main__":
    app()
