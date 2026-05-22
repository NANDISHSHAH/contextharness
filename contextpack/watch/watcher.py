"""Filesystem watcher — incremental context updates on file change."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from contextpack.core.project import Project


_SOURCE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".md", ".yaml", ".yml",
}


class _IncrementalHandler(FileSystemEventHandler):
    def __init__(self, project: Project, debounce_sec: float = 1.5) -> None:
        self._project = project
        self._debounce = debounce_sec
        self._last = 0.0
        self._pending = False

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = str(getattr(event, "src_path", ""))
        if not any(src.endswith(ext) for ext in _SOURCE_EXTS):
            return
        if ".contextpack" in src:
            return
        now = time.time()
        if now - self._last < self._debounce:
            return
        self._last = now
        self._trigger()

    def _trigger(self) -> None:
        from contextpack.memory.store import format_changeset
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        async def _run() -> None:
            try:
                _, stats, changeset = await self._project.incremental_build()
                if changeset.total_changes == 0:
                    console.print("[dim]watch: no source changes — index up to date[/dim]")
                    return
                lines = [f"[green]✓[/green] incremental build  ({stats.total_time:.2f}s)"]
                lines.append(format_changeset(changeset))
                if stats.entities:
                    lines.append(
                        f"[dim]{stats.entities} entities total | "
                        f"{stats.embed_count} re-embedded[/dim]"
                    )
                console.print(Panel("\n".join(lines), border_style="green"))
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]watch error:[/red] {exc}")

        asyncio.run(_run())


def run_watch(path: Path) -> None:
    root = Path(path).resolve()
    project = Project(root)
    handler = _IncrementalHandler(project)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()

    from rich.console import Console
    Console().print(
        f"[green]Watching[/green] {root}  "
        f"[dim](incremental mode — Ctrl+C to stop)[/dim]"
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
