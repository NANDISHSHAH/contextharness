"""Filesystem watcher for incremental context updates."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from contextpack.core.project import Project


class _RebuildHandler(FileSystemEventHandler):
    def __init__(self, project: Project, debounce_sec: float = 2.0) -> None:
        self._project = project
        self._debounce = debounce_sec
        self._last = 0.0

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        now = time.time()
        if now - self._last < self._debounce:
            return
        self._last = now
        asyncio.run(self._project.build())


def run_watch(path: Path) -> None:
    root = Path(path).resolve()
    project = Project(root)
    handler = _RebuildHandler(project)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()
    print(f"Watching {root} — Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
