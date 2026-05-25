"""Example 06 — Semantic Contract Layer (Phase 7).

Demonstrates:
- ContractExtractor: AST-based extraction from Python source
- ContractRegistry: SQLite-backed store + context formatting
- InvariantGuard: architectural rule validation
- NegativeContextIndex: anti-pattern detection
- IntentPreserver: behavioral invariant check from test names

Run:
    python examples/06_contracts.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path

DB = Path("/tmp/contextharness_demo/memory.db")
DB.parent.mkdir(parents=True, exist_ok=True)

# Synthetic Python source for extraction demo
_AUTH_SOURCE = '''
def validate_token(token: str) -> str:
    """Validate a JWT token and return the user ID.

    Args:
        token: The signed JWT string to validate.
    Returns:
        user_id: The authenticated user identifier.
    Raises:
        TokenExpiredError: When the token has expired.
        TokenInvalidError: When the signature is tampered.
    """
    assert token, "token must not be empty"
    if _is_expired(token):
        raise TokenExpiredError("Token has expired")
    if not _verify_signature(token):
        raise TokenInvalidError("Signature invalid")
    return _decode_user_id(token)


def create_session(user_id: str, ttl: int = 3600) -> dict:
    """Create a new user session.

    Args:
        user_id: The user to create a session for.
        ttl: Session lifetime in seconds.
    Returns:
        Session dict with token and expiry.
    """
    assert user_id, "user_id required"
    assert ttl > 0, "ttl must be positive"
    return {"token": _sign(user_id, ttl), "expires_in": ttl}
'''

_TEST_SOURCE = '''
def test_validate_token_returns_user_id_on_success():
    assert validate_token(VALID_JWT) == "user_123"

def test_validate_token_raises_on_expired():
    with pytest.raises(TokenExpiredError):
        validate_token(EXPIRED_JWT)

def test_validate_token_raises_on_tampered():
    with pytest.raises(TokenInvalidError):
        validate_token(TAMPERED_JWT)

def test_create_session_success():
    sess = create_session("user_123", ttl=3600)
    assert "token" in sess

def test_create_session_fails_on_empty_user():
    with pytest.raises(AssertionError):
        create_session("")
'''


async def main() -> None:
    from contextpack.contracts import (
        ContractExtractor,
        ContractRegistry,
        InvariantGuard,
        InvariantConfig,
        ArchInvariant,
        NegativeContextIndex,
        NegativePattern,
        IntentPreserver,
    )

    # ── 1. Extract contracts from Python source ───────────────────────────────
    print("=" * 60)
    print("1.  ContractExtractor — AST-based extraction")
    print("=" * 60)
    extractor = ContractExtractor()
    contracts = extractor.extract_from_file(Path("src/auth/tokens.py"), _AUTH_SOURCE)
    for c in contracts:
        print(f"\n  {c.symbol_name}  (trust: {c.trust_score})")
        print(f"    Preconditions:  {c.preconditions[:3]}")
        print(f"    Postconditions: {c.postconditions[:3]}")
        print(f"    Invariants:     {c.invariants[:3]}")

    # ── 2. Store and query contracts ─────────────────────────────────────────
    print()
    print("=" * 60)
    print("2.  ContractRegistry — store and query")
    print("=" * 60)
    registry = ContractRegistry(DB)
    await registry.upsert_batch(contracts)
    found = await registry.search("validate_token", limit=5)
    print(f"  Found {len(found)} contract(s) for 'validate_token'")
    print(registry.format_for_context(found))

    # ── 3. Architectural invariant guard ─────────────────────────────────────
    print()
    print("=" * 60)
    print("3.  InvariantGuard — architectural rule validation")
    print("=" * 60)
    config = InvariantConfig(
        invariants=[
            ArchInvariant(
                name="payment_auth_isolation",
                description="Payment must never import auth directly",
                rule="no_direct_import",
                from_patterns=["src/payment/**"],
                to_patterns=["src/auth/**"],
                severity="error",
            )
        ]
    )
    guard = InvariantGuard(DB)
    # Simulate an import edge that violates the rule
    edges = [
        ("src/payment/processor.py", "src/auth/tokens"),   # VIOLATION
        ("src/api/routes.py", "src/auth/middleware"),       # OK (not from payment)
    ]
    violations = guard.check(config, edges)
    if violations:
        print(f"  ❌ {len(violations)} violation(s):")
        for v in violations:
            print(f"    {v.to_text()}")
    else:
        print("  ✅ No violations")

    # ── 4. Negative context index ─────────────────────────────────────────────
    print()
    print("=" * 60)
    print("4.  NegativeContextIndex — anti-pattern detection")
    print("=" * 60)
    index = NegativeContextIndex(DB)
    await index.add(NegativePattern(
        pattern_id="no_raw_jwt_decode",
        pattern="from jwt import decode",
        reason="Direct JWT decode bypasses expiry/rotation/revocation checks",
        severity="error",
        scope="**",
        remediation="Use auth.tokens.validate_token() instead",
        references=["docs/security/jwt-policy.md"],
    ))

    code_snippet = "from jwt import decode\ntoken_data = decode(token, SECRET)"
    found_patterns = await index.scan_code(code_snippet, "src/api/routes.py")
    print(index.format_findings(found_patterns))

    # ── 5. Intent preservation ────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("5.  IntentPreserver — behavioral invariants from tests")
    print("=" * 60)
    preserver = IntentPreserver()

    # Write temp test file for extraction
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tf:
        tf.write(_TEST_SOURCE)
        temp_path = tf.name

    invariants = preserver.extract_invariants([Path(temp_path)])
    os.unlink(temp_path)

    print(f"  Extracted {len(invariants)} invariant(s):")
    for inv in invariants:
        print(f"    [{inv.target_symbol}] {inv.description}")

    # Check a proposed patch for validate_token
    proposed_good = "def validate_token(token):\n    if expired: raise TokenExpiredError()\n    return user_id"
    proposed_bad  = "def validate_token(token):\n    return None  # simplified"

    result_good = preserver.check_preserved(invariants, proposed_good, "validate_token")
    result_bad  = preserver.check_preserved(invariants, proposed_bad,  "validate_token")

    print()
    print("  Good patch:")
    print(f"    ok={result_good.ok}  passed={result_good.passed}/{result_good.invariants_checked}")
    print("  Bad patch:")
    print(f"    ok={result_bad.ok}   passed={result_bad.passed}/{result_bad.invariants_checked}")
    for v in result_bad.violations:
        print(f"    ⚠ {v}")

    print()
    print(preserver.format_report([result_good, result_bad]))


if __name__ == "__main__":
    asyncio.run(main())
