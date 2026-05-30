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


@app.command("graphify")
def graphify(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    output: str = typer.Option(".membrane/graph.html", "--output", "-o", help="Output HTML path"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Also write graph.json"),  # noqa: B008
    stdout: bool = typer.Option(False, "--stdout", help="Print graph JSON to stdout and exit (for programmatic use)"),  # noqa: B008
) -> None:
    """Generate an interactive vis.js dependency graph HTML file."""
    import json as _json
    from pathlib import Path as _Path

    path = path or _Path.cwd()
    project = Project(path)

    if not project.context_dir.exists():
        if stdout:
            print(_json.dumps({"nodes": [], "edges": []}))
            return
        console.print("[red]✗[/red] No index found. Run [bold]context build[/bold] first.")
        raise typer.Exit(1)

    out_path = _Path(output) if not _Path(output).is_absolute() else _Path(output)
    if not out_path.is_absolute():
        out_path = path / out_path
    if not stdout:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build a file-level dependency graph from Python/TS imports
    try:
        import ast as _ast

        pm = project._load_project_map()
        all_files = pm.files or []

        # Index: module-path fragment → file path
        file_index: dict[str, str] = {}
        for f in all_files:
            fid = str(f) if isinstance(f, str) else str(getattr(f, "path", f))
            if not fid:
                continue
            # Register by path stem variants for import matching
            p2 = _Path(fid)
            key = str(p2.with_suffix("")).replace("/", ".").replace("\\", ".")
            file_index[key] = fid
            file_index[p2.stem] = fid
            # also register parent.stem
            if p2.parent.name:
                file_index[f"{p2.parent.name}.{p2.stem}"] = fid

        # Parse source files for import statements
        edge_set: set[tuple[str, str]] = set()
        in_degree: dict[str, int] = {}

        source_files = [
            f for f in all_files
            if not isinstance(f, str)
            and str(getattr(f, "path", "")).endswith((".py", ".ts", ".tsx", ".js", ".jsx"))
        ]
        # Also handle string-only file lists
        if not source_files:
            source_files_str = [
                str(f) for f in all_files
                if str(f).endswith((".py", ".ts", ".tsx", ".js", ".jsx"))
            ]
        else:
            source_files_str = [str(getattr(f, "path", f)) for f in source_files]

        for rel_path in source_files_str:
            abs_path = path / rel_path
            if not abs_path.exists():
                continue
            try:
                src = abs_path.read_text(encoding="utf-8", errors="ignore")
                if rel_path.endswith(".py"):
                    tree = _ast.parse(src, filename=rel_path)
                    for node in _ast.walk(tree):
                        mod = None
                        if isinstance(node, _ast.Import):
                            for alias in node.names:
                                mod = alias.name
                        elif isinstance(node, _ast.ImportFrom) and node.module:
                            mod = node.module
                        if not mod:
                            continue
                        # Match to a known file
                        target = (
                            file_index.get(mod)
                            or file_index.get(mod.split(".")[-1])
                            or file_index.get(".".join(mod.split(".")[-2:]))
                        )
                        if target and target != rel_path:
                            edge_set.add((rel_path, target))
                            in_degree[target] = in_degree.get(target, 0) + 1
            except Exception:
                pass

        # Count connections per file
        conn_count: dict[str, int] = {}
        for src_f, tgt_f in edge_set:
            conn_count[src_f] = conn_count.get(src_f, 0) + 1
            conn_count[tgt_f] = conn_count.get(tgt_f, 0) + 1

        # Also count entities per file as a proxy for importance
        entity_count: dict[str, int] = {}
        for e in (pm.entities or []):
            fp = str(getattr(e, "file_path", "") or "")
            if fp:
                entity_count[fp] = entity_count.get(fp, 0) + 1

        # Build node list — only include source files, cap at 400 most connected
        file_ids = list({
            str(f) if isinstance(f, str) else str(getattr(f, "path", f))
            for f in all_files
            if str(f if isinstance(f, str) else getattr(f, "path", f)).endswith(
                (".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".md")
            )
        })

        # Score = connections * 3 + entity_count
        def file_score(fid: str) -> int:
            return conn_count.get(fid, 0) * 3 + entity_count.get(fid, 0)

        file_ids.sort(key=file_score, reverse=True)
        file_ids = file_ids[:400]
        visible_set = set(file_ids)

        hub_threshold = max(3, int(len(file_ids) * 0.05))  # top 5% = hub

        graph_data: dict = {"nodes": [], "edges": []}
        for fid in file_ids:
            c = conn_count.get(fid, 0)
            ec = entity_count.get(fid, 0)
            graph_data["nodes"].append({
                "id": fid,
                "label": _Path(fid).name,
                "isHub": c >= hub_threshold,
                "type": "file",
                "filePath": fid,
                "connections": c,
                "entities": ec,
            })

        for src_f, tgt_f in edge_set:
            if src_f in visible_set and tgt_f in visible_set:
                graph_data["edges"].append({"from": src_f, "to": tgt_f})

    except Exception as exc:
        if not stdout:
            console.print(f"[yellow]Warning: could not extract full graph — {exc}[/yellow]")
        graph_data = {"nodes": [], "edges": []}

    graph_json = _json.dumps(graph_data)

    # --stdout: output JSON to stdout for programmatic use (e.g. VS Code extension)
    if stdout:
        print(graph_json)
        return

    # Write JSON if requested
    if json_output:
        json_path = out_path.with_suffix(".json")
        json_path.write_text(graph_json, encoding="utf-8")
        console.print(f"[green]✓[/green] graph.json → {json_path}")

    # Load vis.js — prefer local copy (offline/corporate), fall back to CDN
    vis_script_tag = '<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>'
    vis_candidates = [
        # Installed alongside membrane-vscode extension
        _Path.home() / ".vscode" / "extensions" / "membrane.membrane-vscode-0.1.0" / "media" / "vis-network.min.js",
        # Sibling install (dev)
        _Path(__file__).parent.parent.parent / "membrane-vscode" / "media" / "vis-network.min.js",
        # node_modules in cwd
        _Path.cwd() / "node_modules" / "vis-network" / "standalone" / "umd" / "vis-network.min.js",
    ]
    for candidate in vis_candidates:
        if candidate.exists():
            vis_js = candidate.read_text(encoding="utf-8")
            vis_script_tag = f"<script>{vis_js}</script>"
            break

    # Write self-contained vis.js HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Membrane — Dependency Graph</title>
{vis_script_tag}
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d0d0d;color:#c8c8c8;font-family:'JetBrains Mono',monospace;height:100vh;overflow:hidden}}
#graph{{width:100%;height:100vh}}
#info{{position:fixed;top:10px;right:10px;background:#141414;border:1px solid #2a2a2a;padding:12px 16px;font-size:11px;max-width:260px;display:none}}
#info h3{{font-size:12px;color:#e8e8e8;margin-bottom:8px}}
.k{{color:#666;font-size:9px;letter-spacing:.1em;text-transform:uppercase}}
.v{{color:#c8c8c8;word-break:break-all}}
#legend{{position:fixed;bottom:16px;left:16px;background:#141414;border:1px solid #2a2a2a;padding:10px 14px;font-size:10px}}
.ld{{display:flex;align-items:center;gap:8px;margin-bottom:4px}}
.lc{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
</style>
</head>
<body>
<div id="graph"></div>
<div id="info"><h3 id="i-name"></h3><div class="k">Type</div><div class="v" id="i-type"></div><br><div class="k">File</div><div class="v" id="i-file"></div><br><div class="k">Connections</div><div class="v" id="i-conns"></div></div>
<div id="legend">
  <div class="ld"><div class="lc" style="background:#e74c3c"></div>Hub node</div>
  <div class="ld"><div class="lc" style="background:#007acc"></div>File / Module</div>
  <div class="ld"><div class="lc" style="background:#2ecc71"></div>Function / Class</div>
</div>
<script>
const data={graph_json};
const nodes=new vis.DataSet(data.nodes.map(n=>{{
  const hub=n.isHub,c=n.connections||1;
  const t=(n.type||'').toLowerCase();
  const col=hub?'#e74c3c':t.match(/module|file/)?'#007acc':t.match(/class|function|method/)?'#2ecc71':'#3498db';
  return{{id:n.id,label:n.label,color:{{background:col,border:col,highlight:{{background:'#fff',border:col}}}},size:hub?Math.min(60,20+c*2):Math.min(40,14+c*1.2),font:{{color:'#e8e8e8',size:11}},_raw:n}};
}}));
const edges=new vis.DataSet(data.edges.map((e,i)=>{{return{{id:i,from:e.from||e.source,to:e.to||e.target,arrows:'to',color:{{color:'#333',highlight:'#007acc'}},width:1}};}}));
const nodeCount=data.nodes.length;
const net=new vis.Network(document.getElementById('graph'),{{nodes,edges}},{{
  physics:{{
    forceAtlas2Based:{{gravitationalConstant:-26,centralGravity:0.005,springLength:100,damping:0.5}},
    solver:'forceAtlas2Based',
    stabilization:{{iterations:nodeCount>150?50:150,updateInterval:25}},
    adaptiveTimestep:true,
  }},
  interaction:{{hover:true,navigationButtons:false,keyboard:true,tooltipDelay:300}},
}});
net.on('stabilizationIterationsDone',function(){{net.setOptions({{physics:{{enabled:false}}}});}});
net.on('click',p=>{{
  if(p.nodes.length){{
    const n=nodes.get(p.nodes[0]);const r=n._raw||{{}};
    document.getElementById('i-name').textContent=n.label;
    document.getElementById('i-type').textContent=r.type||'—';
    document.getElementById('i-file').textContent=r.filePath||'—';
    document.getElementById('i-conns').textContent=(r.connections||0)+' connections';
    document.getElementById('info').style.display='block';
  }}else{{document.getElementById('info').style.display='none';}}
}});
</script>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    console.print(f"[green]✓[/green] graph → {out_path} ({len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges)")


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
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show architectural coupling trend over time (Phase 9)."""
    import json

    from contextpack.adaptive.coupling import CouplingMonitor

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    monitor = CouplingMonitor(db)
    trend = _run(monitor.trend(days=days))

    if json_output:
        latest = trend.snapshots[-1] if trend.snapshots else None
        output = {
            "coupling_change_pct": trend.coupling_change_pct,
            "hub_change": trend.hub_change,
            "cycle_change": trend.cycle_change,
            "is_decaying": trend.is_decaying,
            "alert_message": trend.alert_message,
            "hotspot_modules": trend.hotspot_modules,
            "snapshot_count": len(trend.snapshots),
            "latest": {
                "edge_count": latest.edge_count,
                "node_count": latest.node_count,
                "hub_count": latest.hub_count,
                "cycle_count": latest.cycle_count,
                "avg_coupling": latest.avg_coupling,
            } if latest else None,
        }
        print(json.dumps(output))
    else:
        console.print(trend.to_text())


# ── Trust Scoring ─────────────────────────────────────────────────────────────

@app.command("trust")
def trust_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show trust scores for project files based on source type and freshness."""
    import json as json_mod
    import subprocess
    import time

    from contextpack.governance.trust import TrustScorer

    path = path or Path.cwd()
    pm_path = path / ".contextpack" / "project_map.json"
    if not pm_path.exists():
        if json_output:
            print(json_mod.dumps([]))
        else:
            console.print("[dim]Run 'context build' first to compute trust scores[/dim]")
        return

    with pm_path.open() as f:
        pm = json_mod.load(f)

    scorer = TrustScorer()
    results = []

    for file_info in pm.get("files", []):
        file_path = file_info.get("path", "")
        language = file_info.get("language", "")
        if not file_path:
            continue

        fp_lower = file_path.lower()
        if (
            "test_" in fp_lower
            or "_test" in fp_lower
            or ".spec." in fp_lower
            or ".test." in fp_lower
        ):
            source_type = "test"
        elif language in ("markdown", "rst") or fp_lower.endswith((".md", ".rst")):
            source_type = "docs"
        else:
            source_type = "code"

        days_old: float = 0.0
        try:
            git_result = subprocess.run(
                ["git", "log", "-1", "--format=%ct", "--", file_path],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if git_result.returncode == 0 and git_result.stdout.strip():
                ts_val = int(git_result.stdout.strip())
                days_old = (time.time() - ts_val) / 86400
        except Exception:
            pass

        ts = scorer.score_chunk(
            source_type=source_type,
            file_path=file_path,
            days_since_modified=days_old,
        )
        results.append(
            {
                "file": file_path,
                "tier": ts.tier,
                "score": ts.score,
                "label": ts.label,
                "source_type": source_type,
                "rationale": ts.rationale,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    if json_output:
        print(json_mod.dumps(results))
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("File", max_width=55)
        table.add_column("Tier", width=5, justify="right")
        table.add_column("Score", width=6, justify="right")
        table.add_column("Label", width=16)
        for r in results[:40]:
            color = (
                "green"
                if r["tier"] <= 2
                else "yellow"
                if r["tier"] == 3
                else "red"
            )
            table.add_row(
                r["file"],
                str(r["tier"]),
                f"{r['score']:.3f}",
                f"[{color}]{r['label']}[/{color}]",
            )
        console.print("\n[bold]Trust Scores[/bold]\n")
        console.print(table)


# ── Playbook Learning ─────────────────────────────────────────────────────────

@app.command("playbook")
def playbook_cmd(
    path: Path | None = typer.Argument(None, help="Repository path"),  # noqa: B008
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),  # noqa: B008
) -> None:
    """Show auto-learned playbook proposals from observed skill gate runs (Phase 9)."""
    import json as json_mod

    from contextpack.adaptive.playbook import PlaybookLearner
    from contextpack.skills.evidence import EvidenceStore

    path = path or Path.cwd()
    db = path / ".contextpack" / "memory.db"
    if not db.exists():
        if json_output:
            print(json_mod.dumps([]))
        else:
            console.print("[dim]No evidence bundles yet — run skill gates first[/dim]")
        return

    store = EvidenceStore(db)
    bundles = _run(store.list_recent(limit=100))

    records = [
        {
            "files_modified": b.files_modified,
            "skill_results": b.skill_results,
            "passed": b.passed,
        }
        for b in bundles
    ]

    learner = PlaybookLearner()
    proposals = learner.propose(records)

    if json_output:
        output = [
            {
                "policy_name": p.policy_name,
                "description": p.description,
                "file_pattern": p.file_pattern,
                "skills_to_add": p.skills_to_add,
                "confidence": p.confidence,
                "evidence": p.evidence,
                "yaml_block": p.to_yaml_block(),
            }
            for p in proposals
        ]
        print(json_mod.dumps(output))
    else:
        console.print(learner.format_proposals(proposals))


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
