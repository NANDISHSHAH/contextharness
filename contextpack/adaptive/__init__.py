"""Adaptive intelligence — failure patterns, playbook learning, snapshots, coupling monitor."""
from contextpack.adaptive.coupling import CouplingMonitor, CouplingSnapshot, CouplingTrend
from contextpack.adaptive.patterns import FailurePattern, FailurePatternStore
from contextpack.adaptive.playbook import PlaybookLearner, PlaybookProposal
from contextpack.adaptive.snapshots import ContextSnapshot, ContextSnapshotEngine, SnapshotDiff

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
