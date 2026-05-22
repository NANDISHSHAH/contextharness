"""Gamified vibe display — animated build + token/cost tracking."""

from __future__ import annotations

import itertools
import threading
import time
from collections.abc import Callable

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ── Phase metadata ─────────────────────────────────────────────────────────────

PHASES = ["scan", "parse", "graph", "chunk", "embed", "store"]

_LABEL = {
    "scan":  "SCAN  ",
    "parse": "PARSE ",
    "graph": "GRAPH ",
    "chunk": "CHUNK ",
    "embed": "EMBED ",
    "store": "STORE ",
}

_COLOR = {
    "scan":  "bright_cyan",
    "parse": "bright_blue",
    "graph": "bright_magenta",
    "chunk": "bright_yellow",
    "embed": "bright_green",
    "store": "green",
}

_FLAVOR = {
    "scan":  "sniffing the repo...",
    "parse": "chewing symbols...",
    "graph": "mapping connections...",
    "chunk": "slicing context...",
    "embed": "digesting vectors...",
    "store": "swallowing to memory...",
}

# Pac-Man eating dots animation — mouth open/close cycling rightward
_PAC_FRAMES = [
    "ᗧ·····◉",
    "ᗧ·····◉",
    " ᗧ····◉",
    "  ᗧ···◉",
    "   ᗧ··◉",
    "    ᗧ·◉",
    "     ᗧ◉",
    "      ᗧ",
    "     ᗧ·",
    "    ᗧ··",
    "   ᗧ···",
    "  ᗧ····",
    " ᗧ·····",
    "ᗧ·····◉",
]

# ── Cost table (per 1 K tokens) ────────────────────────────────────────────────

_COST: dict[str, dict[str, float]] = {
    "hash":          {"embed": 0.0,      "input": 0.0,    "output": 0.0},
    "openai":        {"embed": 0.00002,  "input": 0.005,  "output": 0.015},
    "azure_foundry": {"embed": 0.00002,  "input": 0.005,  "output": 0.015},
}


def _rate(provider: str, kind: str) -> float:
    return _COST.get(provider.lower(), _COST["hash"]).get(kind, 0.0)


def estimate_cost(tokens: int, provider: str, kind: str = "embed") -> float:
    return (tokens / 1000) * _rate(provider, kind)


def _fmt_cost(cost: float, provider: str) -> str:
    if cost == 0.0:
        return "[dim]$0.00[/dim]"
    if cost < 0.001:
        return f"[yellow]~${cost:.5f}[/yellow]"
    return f"[yellow]~${cost:.4f}[/yellow]"


def _tok(n: int) -> str:
    """Format token count with K suffix."""
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


# ── Animated build display ─────────────────────────────────────────────────────

class VibeBuild:
    """Context manager: wraps project.build() with an animated Pac-Man display.

    Usage::

        with VibeBuild(console) as on_phase:
            pmap, stats = await project.build(on_phase=on_phase)
        vibe_build_footer(console, stats, embedding_provider)
    """

    def __init__(self, console: Console) -> None:
        self._console = console
        self._state: dict[str, str] = {p: "pending" for p in PHASES}
        self._start_t: dict[str, float] = {}
        self._elapsed: dict[str, float] = {}
        self._detail: dict[str, str] = {}
        self._current: str | None = None
        self._pac_iter = itertools.cycle(_PAC_FRAMES)
        self._pac_frame = _PAC_FRAMES[0]
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._live: Live | None = None

    # Called by project.build() at phase boundaries
    def on_phase(self, phase: str, event: str, detail: str = "") -> None:
        with self._lock:
            if event == "start":
                self._current = phase
                self._state[phase] = "running"
                self._start_t[phase] = time.perf_counter()
            elif event == "done":
                elapsed = time.perf_counter() - self._start_t.get(phase, time.perf_counter())
                self._state[phase] = "done"
                self._elapsed[phase] = elapsed
                self._detail[phase] = detail
                if self._current == phase:
                    self._current = None

    def _render(self) -> Panel:
        with self._lock:
            pac = self._pac_frame
            state = dict(self._state)
            elapsed = dict(self._elapsed)
            detail = dict(self._detail)
            current = self._current

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(width=2)   # icon
        table.add_column(width=8)   # label
        table.add_column(width=9)   # time
        table.add_column()          # detail

        for phase in PHASES:
            s = state[phase]
            color = _COLOR[phase]

            if s == "pending":
                table.add_row(
                    "[dim]·[/dim]",
                    f"[dim]{_LABEL[phase]}[/dim]",
                    "[dim]  --  [/dim]",
                    "[dim]waiting[/dim]",
                )
            elif s == "running":
                table.add_row(
                    f"[bold {color}]{pac[0]}[/bold {color}]",
                    f"[bold {color}]{_LABEL[phase]}[/bold {color}]",
                    f"[{color}] ···[/{color}]",
                    f"[{color} italic]{_FLAVOR[phase]}[/{color} italic]",
                )
            else:
                t = elapsed.get(phase, 0.0)
                table.add_row(
                    f"[{color}]●[/{color}]",
                    f"[{color}]{_LABEL[phase]}[/{color}]",
                    f"[{color}]{t:.2f}s[/{color}]",
                    detail.get(phase, ""),
                )

        title = Text()
        title.append("ContextPack  ", style="bold white")
        title.append(pac, style="bold yellow")
        title.append("  nom nom nom", style="dim italic yellow")

        return Panel(table, title=title, border_style="yellow", padding=(0, 1))

    def _animate(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                self._pac_frame = next(self._pac_iter)
            if self._live:
                self._live.update(self._render())
            time.sleep(0.13)

    def __enter__(self) -> Callable[[str, str, str], None]:
        self._console.print()
        self._live = Live(
            self._render(),
            console=self._console,
            refresh_per_second=10,
            transient=False,
        )
        self._live.__enter__()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self.on_phase

    def __exit__(self, *args: object) -> None:
        self._stop.set()
        self._thread.join(timeout=0.5)
        if self._live:
            self._live.update(self._render())
            self._live.__exit__(*args)


def vibe_build_footer(console: Console, stats: object, embed_provider: str) -> None:
    """Print token/cost summary after a vibe build completes."""
    tokens: int = getattr(stats, "estimated_tokens", 0)
    embed_count: int = getattr(stats, "embed_count", 0)
    store_only: int = getattr(stats, "store_only_count", 0)
    total_t: float = getattr(stats, "total_time", 0.0)
    files_scanned: int = getattr(stats, "files_scanned", 0)
    files_skipped: int = getattr(stats, "files_skipped", 0)

    embed_cost = estimate_cost(tokens, embed_provider, "embed")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", width=22)
    table.add_column(justify="right", width=12)
    table.add_column(style="dim")

    provider_label = f"[dim]{embed_provider}[/dim]"
    table.add_row("files scanned",    f"[cyan]{files_scanned:,}[/cyan]",                 f"[dim]{files_skipped:,} skipped[/dim]")
    table.add_row("entities embedded", f"[bright_green]{embed_count:,}[/bright_green]",  f"[dim]{store_only:,} store-only[/dim]")
    table.add_row("tokens indexed",   f"[yellow]~{_tok(tokens)}[/yellow]",               "[dim]estimated[/dim]")
    table.add_row("embed cost",       _fmt_cost(embed_cost, embed_provider),              provider_label)
    table.add_row("total time",       f"[bold white]{total_t:.2f}s[/bold white]",        "")

    console.print()
    console.print(Panel(
        table,
        title="[yellow]ᗧ◉  build stats[/yellow]",
        border_style="yellow",
        padding=(0, 1),
    ))


# ── Ask / harvest token summary ────────────────────────────────────────────────

def vibe_ask_summary(
    console: Console,
    question: str,
    answer: str,
    context_tokens: int,
    provider: str,
    elapsed: float,
) -> None:
    """Print token usage + cost after an ask/harvest in vibe mode."""
    q_tokens = max(1, len(question) // 4)
    a_tokens = max(1, len(answer) // 4)
    total_in = q_tokens + context_tokens
    total = total_in + a_tokens

    in_cost = estimate_cost(total_in, provider, "input")
    out_cost = estimate_cost(a_tokens, provider, "output")
    total_cost = in_cost + out_cost

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", width=22)
    table.add_column(justify="right", width=12)
    table.add_column(style="dim")

    table.add_row("question",      f"[cyan]~{_tok(q_tokens)}[/cyan]",       "tokens (estimated)")
    table.add_row("context",       f"[blue]~{_tok(context_tokens)}[/blue]", "tokens (compiled pack)")
    table.add_row("response",      f"[green]~{_tok(a_tokens)}[/green]",     "tokens (estimated)")
    table.add_row("[bold]total[/bold]", f"[bold white]~{_tok(total)}[/bold white]", "")
    table.add_row("", "", "")
    table.add_row("provider",      f"[dim]{provider}[/dim]", "")
    table.add_row("est. cost",     _fmt_cost(total_cost, provider), "")
    table.add_row("elapsed",       f"[dim]{elapsed:.2f}s[/dim]", "")

    console.print()
    console.print(Panel(
        table,
        title="[yellow]ᗧ◉  token trace[/yellow]",
        border_style="yellow",
        padding=(0, 1),
    ))
