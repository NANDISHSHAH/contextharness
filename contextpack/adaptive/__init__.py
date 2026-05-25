"""Adaptive intelligence — failure patterns, playbook learning, snapshots, coupling monitor."""
from contextpack.adaptive.patterns import FailurePatternStore, FailurePattern
from contextpack.adaptive.playbook import PlaybookLearner, PlaybookProposal
from contextpack.adaptive.snapshots import ContextSnapshotEngine, ContextSnapshot, SnapshotDiff
from contextpack.adaptive.coupling import CouplingMonitor, CouplingSnapshot, CouplingTrend

__all__ = [
    "FailurePatternStore",
    "FailurePattern",
    "PlaybookLearner",
    "PlaybookProposal",
    "ContextSnapshotEngine",
    "ContextSnapshot",
    "SnapshotDiff",
    "CouplingMonitor",
    "CouplingSnapshot",
    "CouplingTrend",
]
