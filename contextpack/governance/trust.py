"""Trust scorer — 5-tier trust scoring for context chunks."""
from __future__ import annotations

import time
from enum import IntEnum
from pathlib import Path

from pydantic import BaseModel, Field


class TrustTier(IntEnum):
    GROUND_TRUTH = 1   # type sigs, asserts, passing CI tests
    HIGH         = 2   # unit tests, test bodies
    MEDIUM       = 3   # docstrings, inline comments < 30 days
    LOW          = 4   # README, docs/, wiki
    UNVERIFIED   = 5   # Jira comments, Slack threads


_TIER_RANGES = {
    TrustTier.GROUND_TRUTH: (0.95, 1.00),
    TrustTier.HIGH:         (0.80, 0.94),
    TrustTier.MEDIUM:       (0.60, 0.79),
    TrustTier.LOW:          (0.30, 0.59),
    TrustTier.UNVERIFIED:   (0.10, 0.29),
}

_TIER_LABELS = {
    TrustTier.GROUND_TRUTH: "T1:GroundTruth",
    TrustTier.HIGH:         "T2:High",
    TrustTier.MEDIUM:       "T3:Medium",
    TrustTier.LOW:          "T4:Low",
    TrustTier.UNVERIFIED:   "T5:Unverified",
}


class TrustScore(BaseModel):
    tier: int
    score: float
    label: str
    rationale: str = ""

    def is_safe_for_high_risk(self) -> bool:
        """Only Tier 1-2 is safe for high-risk tasks (risk_score > 0.7)."""
        return self.tier <= TrustTier.HIGH


class TrustScorer:
    """Assign trust tier and score to a context source."""

    def score_chunk(
        self,
        source_type: str,        # "code", "test", "docstring", "docs", "jira", "comment"
        file_path: str,
        days_since_modified: float = 0,
        ci_verified: bool = False,
        test_coverage: float = 0.0,
    ) -> TrustScore:
        tier = self._infer_tier(
            source_type, file_path, days_since_modified, ci_verified, test_coverage
        )
        lo, hi = _TIER_RANGES[tier]
        # Fine-tune score within tier range
        score = self._fine_score(tier, lo, hi, days_since_modified, ci_verified, test_coverage)
        return TrustScore(
            tier=int(tier),
            score=round(score, 3),
            label=_TIER_LABELS[tier],
            rationale=self._rationale(source_type, tier, days_since_modified, ci_verified),
        )

    def _infer_tier(
        self,
        source_type: str,
        file_path: str,
        days_since_modified: float,
        ci_verified: bool,
        test_coverage: float,
    ) -> TrustTier:
        st = source_type.lower()
        fp = file_path.lower()

        # Tier 1: machine-verifiable
        if st in ("type_signature", "assertion", "type_hint"):
            return TrustTier.GROUND_TRUTH
        if ci_verified and st == "test" and test_coverage > 0.8:
            return TrustTier.GROUND_TRUTH

        # Tier 2: CI-verified tests
        if st == "test" or "test_" in fp or fp.endswith(("_test.py", ".spec.ts", ".test.ts")):
            return TrustTier.HIGH
        if st == "code" and ci_verified:
            return TrustTier.HIGH

        # Tier 3: reasonably fresh docstrings / inline comments
        if st in ("docstring", "comment", "code") and days_since_modified <= 30:
            return TrustTier.MEDIUM

        # Tier 4: docs, README (stale or external)
        if st in ("docs", "readme", "markdown") or any(
            fp.startswith(p) for p in ("docs/", "readme", "wiki")
        ):
            return TrustTier.LOW
        if st == "code" and days_since_modified > 30:
            return TrustTier.MEDIUM  # still code, just a bit stale

        # Tier 5: informal / unreviewed
        if st in ("jira", "slack", "email", "comment_external"):
            return TrustTier.UNVERIFIED

        return TrustTier.MEDIUM

    def _fine_score(
        self,
        tier: TrustTier,
        lo: float,
        hi: float,
        days_since_modified: float,
        ci_verified: bool,
        test_coverage: float,
    ) -> float:
        base = (lo + hi) / 2
        if ci_verified:
            base = min(hi, base + 0.05)
        if test_coverage > 0.9:
            base = min(hi, base + 0.03)
        if days_since_modified > 90:
            base = max(lo, base - 0.05)
        elif days_since_modified > 30:
            base = max(lo, base - 0.02)
        return base

    def _rationale(
        self,
        source_type: str,
        tier: TrustTier,
        days_since_modified: float,
        ci_verified: bool,
    ) -> str:
        parts: list[str] = [f"source={source_type}"]
        if ci_verified:
            parts.append("CI-verified")
        if days_since_modified > 0:
            parts.append(f"{days_since_modified:.0f}d old")
        parts.append(_TIER_LABELS[tier])
        return "; ".join(parts)

    def filter_for_risk(
        self,
        chunks: list[dict],
        risk_score: float,
    ) -> tuple[list[dict], list[dict]]:
        """Split chunks into (included, excluded) based on risk score + trust tier.

        High risk (>0.7) → only Tier 1-2.
        Medium risk (0.4-0.7) → Tier 1-3.
        Low risk (<0.4) → all tiers.
        """
        if risk_score > 0.7:
            max_tier = TrustTier.HIGH
        elif risk_score > 0.4:
            max_tier = TrustTier.MEDIUM
        else:
            max_tier = TrustTier.UNVERIFIED

        included: list[dict] = []
        excluded: list[dict] = []
        for chunk in chunks:
            tier = chunk.get("trust_tier", TrustTier.MEDIUM)
            if tier <= max_tier:
                included.append(chunk)
            else:
                excluded.append(chunk)
        return included, excluded
