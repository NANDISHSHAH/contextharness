"""Semantic contract layer — contracts, invariants, negative patterns, intent preservation."""
from contextpack.contracts.extractor import Contract, ContractExtractor
from contextpack.contracts.invariants import (
    ArchInvariant,
    InvariantConfig,
    InvariantGuard,
    InvariantViolation,
)
from contextpack.contracts.negative import NegativeContextIndex, NegativePattern
from contextpack.contracts.preserver import BehaviorInvariant, IntentPreserver, InvariantCheckResult
from contextpack.contracts.registry import ContractRegistry

__all__ = [
    "ContractExtractor",
    "Contract",
    "ContractRegistry",
    "InvariantGuard",
    "ArchInvariant",
    "InvariantViolation",
    "InvariantConfig",
    "NegativeContextIndex",
    "NegativePattern",
    "IntentPreserver",
    "BehaviorInvariant",
    "InvariantCheckResult",
]
