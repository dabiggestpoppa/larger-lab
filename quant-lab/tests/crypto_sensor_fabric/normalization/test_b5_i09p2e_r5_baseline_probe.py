#!/usr/bin/env python3
"""
SENSOR-B5-I09P3-R5-BASELINE-PROBE — Executable R5 baseline comparison

Runs the same attack scenarios against R5 (ea1fdeb77) to document
the R5/R6 divergence. R5's CustodyAuthorityCapability has NO provider
field, NO _issue() classmethod, and IS frozen (no object.__setattr__
marker copy). R5's _custody_grant returns AUTHORIZED for ATTESTED_OPERATOR
basis — unlike R6 which requires the issuance marker.

R5 worktree path configuration (pick one):

  1. Environment variable:
     R5_WORKTREE_PATH=/c/tmp/wt-r5 python .../test_b5_i09p2e_r5_baseline_probe.py

  2. Command-line argument:
     python .../test_b5_i09p2e_r5_baseline_probe.py --r5-worktree /c/tmp/wt-r5

  3. Default: resolves relative to this file's parents (assumes sibling
     worktrees under a common parent directory).

The pinned R5 implementation commit is validated before any probe runs.
If the R5 worktree is unavailable or at the wrong commit, the probe reports
a clear setup requirement and does not silently substitute R6 code.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# R5 worktree resolution
# ---------------------------------------------------------------------------

PINNED_R5_COMMIT = "ea1fdeb7714b57f07085eb6dfadefafccd7658bb"
PINNED_R5_COMMIT_SHORT = PINNED_R5_COMMIT[:12]


def _resolve_r5_worktree(explicit: str | None) -> Path | None:
    """Resolve the R5 worktree path from explicit arg, env var, or default."""
    if explicit:
        return Path(explicit)
    env_path = os.environ.get("R5_WORKTREE_PATH")
    if env_path:
        return Path(env_path)
    # Default: assume sibling worktrees under a common parent directory.
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "wt-r5",
        here.parents[4] / "wt-r5",
        Path("/c/tmp/wt-r5"),
    ]
    for c in candidates:
        if c.exists() and (c / ".git").exists():
            return c
    return None


def _validate_r5_commit(worktree: Path) -> bool:
    """Validate that the R5 worktree is at the pinned commit.

    Returns True if the commit matches; False otherwise with a clear
    message printed to stderr.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        actual = result.stdout.strip()
        if actual == PINNED_R5_COMMIT or actual.startswith(PINNED_R5_COMMIT_SHORT):
            return True
        print(
            f"ERROR: R5 worktree at {worktree} is on commit {actual[:12]}, "
            f"expected pinned R5 commit {PINNED_R5_COMMIT_SHORT}. "
            f"Checkout {PINNED_R5_COMMIT_SHORT} before running this probe.",
            file=sys.stderr,
        )
        return False
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(
            f"ERROR: Cannot validate R5 worktree at {worktree}: {exc}. "
            f"Ensure the R5 worktree exists and is a valid git repository "
            f"checked out at {PINNED_R5_COMMIT_SHORT}.",
            file=sys.stderr,
        )
        return False


def _load_r5_module(worktree: Path):
    """Load the R5 trust consumer module from the given worktree."""
    r5_src = worktree / "quant-lab" / "src"
    r5_tcp_path = (
        worktree
        / "quant-lab"
        / "tests"
        / "crypto_sensor_fabric"
        / "normalization"
        / "test_b5_i09p2e_trust_consumer.py"
    )
    if not r5_tcp_path.exists():
        print(
            f"ERROR: R5 trust consumer module not found at {r5_tcp_path}. "
            f"Ensure the R5 worktree contains the expected source tree.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.path.insert(0, str(r5_src))

    spec = importlib.util.spec_from_file_location("r5_tcp", str(r5_tcp_path))
    r5tcp = importlib.util.module_from_spec(spec)
    sys.modules["r5_tcp"] = r5tcp
    spec.loader.exec_module(r5tcp)
    return r5tcp


# ---------------------------------------------------------------------------
# Parse arguments and resolve R5 worktree
# ---------------------------------------------------------------------------

_parser = argparse.ArgumentParser(
    description="R5 baseline comparison probe for SENSOR-B5-I09P3-R6"
)
_parser.add_argument(
    "--r5-worktree",
    help="Path to the R5 worktree (overrides R5_WORKTREE_PATH env var)",
)
_parser.add_argument(
    "--write-results",
    help="Write machine-readable results JSON to this explicit path",
)
_args, _remaining = _parser.parse_known_args()

_r5_worktree = _resolve_r5_worktree(_args.r5_worktree)

if _r5_worktree is None:
    print(
        "ERROR: R5 worktree path not configured. Set R5_WORKTREE_PATH or "
        "pass --r5-worktree /path/to/r5/worktree before running this probe.",
        file=sys.stderr,
    )
    sys.exit(2)

if not _validate_r5_commit(_r5_worktree):
    sys.exit(2)

r5tcp = _load_r5_module(_r5_worktree)

# ---------------------------------------------------------------------------
# Re-export R5 helpers
# ---------------------------------------------------------------------------

ConsumerPolicy = r5tcp.ConsumerPolicy
CustodyAuthorityCapability = r5tcp.CustodyAuthorityCapability
AuthorityBasis = r5tcp.AuthorityBasis
ConsumerDecision = r5tcp.ConsumerDecision
ConsumerRefusalReason = r5tcp.ConsumerRefusalReason
RecordVerification = r5tcp.RecordVerification
TRUSTED_MANIFEST_SHA256 = "dummy-manifest-sha256"  # R5 does not check manifest_sha256
_replay_evaluation = r5tcp._replay_evaluation
_store_with_evidence = r5tcp._store_with_evidence
CUTOFF = r5tcp.CUTOFF
REF = r5tcp.REF
DOC_SHA = r5tcp.DOC_SHA

ARTIFACT_ID = r5tcp.ARTIFACT_ID
APPROVAL_ID = r5tcp.APPROVAL_ID
REGISTRY_DIGEST = r5tcp.REGISTRY_DIGEST


def _base_verdict(**overrides):
    return r5tcp._base_verdict(**overrides)


def _synthetic_capability(**overrides):
    return r5tcp._synthetic_capability(**overrides)


# ---------------------------------------------------------------------------
# Results container
# ---------------------------------------------------------------------------

RESULTS: list[dict] = []


def record(name, vuln, decision, refusal, status, detail=""):
    RESULTS.append(
        {
            "name": name,
            "vulnerable": vuln,
            "decision": decision,
            "refusal": refusal,
            "status": status,
            "detail": detail,
        }
    )


def is_unauthorized_trusted(outcome):
    """True only if ACCEPT_FIELD_BINDING with custody_source_authorized=True
    or custody_source_authorization_status=AUTHORIZED."""
    return (
        outcome.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
        and (
            outcome.custody_source_authorized is True
            or outcome.custody_source_authorization_status == "AUTHORIZED"
        )
    )


# ============================================================================
# R5: Direct ATTESTED_OPERATOR construction — R5 GRANTS AUTHORIZED
# ============================================================================

def test_r5_direct_attested_operator():
    """R5: Direct CustodyAuthorityCapability with ATTESTED_OPERATOR basis.

    R5 constructs this directly (no _issue() required). _custody_grant returns
    (True, "AUTHORIZED") for ATTESTED_OPERATOR basis. R5 VULNERABLE.
    """
    cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.ATTESTED_OPERATOR,
        artifact_id=ARTIFACT_ID,
        approval_id=APPROVAL_ID,
        registry_digest=REGISTRY_DIGEST,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
        manifest_sha256=TRUSTED_MANIFEST_SHA256,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorized is True
    assert out.custody_source_authorization_status == "AUTHORIZED"
    record(
        "R5 direct ATTESTED_OPERATOR construction -> AUTHORIZED", True,
        decision=out.decision.value,
        refusal=out.refusal_reason.value if out.refusal_reason else None,
        status=out.custody_source_authorization_status,
        detail="R5 grants AUTHORIZED for direct ATTESTED_OPERATOR construction",
    )


# ============================================================================
# R5: SYNTHETIC_TEST_ONLY — ACCEPT_FIELD_BINDING but NOT AUTHORIZED
# ============================================================================

def test_r5_synthetic_test_only():
    """R5: SYNTHETIC_TEST_ONLY capability -> ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY.

    custody_source_authorized=False (because status != "AUTHORIZED"),
    custody_source_authorization_status="SYNTHETIC_TEST_ONLY".
    Not an unauthorized trusted outcome.
    """
    cap = _synthetic_capability(
        knowledge_cutoff=CUTOFF,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorized is False
    assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY"
    record(
        "R5 SYNTHETIC_TEST_ONLY -> ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
        detail="Not AUTHORIZED — not an unauthorized trusted outcome",
    )


# ============================================================================
# R5: No provider field — provider mismatch not checkable
# ============================================================================

def test_r5_no_provider_field():
    """R5: CustodyAuthorityCapability has NO provider field.

    Provider substitution attack is not expressible in R5's data model.
    """
    cap = CustodyAuthorityCapability(
        basis=AuthorityBasis.SYNTHETIC_TEST_ONLY,
        artifact_id=ARTIFACT_ID,
        approval_id=APPROVAL_ID,
        registry_digest=REGISTRY_DIGEST,
        record_kind="TRADE",
        knowledge_cutoff=CUTOFF,
    )
    # Verify no provider field exists
    assert not hasattr(cap, "provider"), "R5 capability must not have provider field"
    record(
        "R5 no provider field in capability", False,
        decision="N/A", refusal=None, status="N/A",
        detail="R5 data model lacks provider field — provider-mismatch attack not expressible",
    )


# ============================================================================
# R5: Frozen dataclass — no object.__setattr__ marker copy
# ============================================================================

def test_r5_frozen_no_marker_copy():
    """R5: Marker-copy attack is not possible because R5 has no _issued marker.

    Python's frozen dataclass only prevents ``instance.attr = value`` syntax;
    ``object.__setattr__`` can still add arbitrary attributes. However, R5's
    ``CustodyAuthorityCapability`` has NO ``_issued`` field at all, and
    ``_custody_grant`` authorizes based on the ``basis`` field, not on any
    marker. Adding ``_issued`` via ``object.__setattr__`` does not grant
    authority in R5.

    Threat class C marker-copy (as in R6) is not expressible because R5's
    data model lacks the marker entirely.
    """
    cap = _synthetic_capability(knowledge_cutoff=CUTOFF)

    # object.__setattr__ can add attributes even on frozen dataclasses.
    # This is Python behavior, not an R5 vulnerability.
    object.__setattr__(cap, "_issued", object())
    assert getattr(cap, "_issued", None) is not None

    # But R5's _custody_grant does not check _issued — it checks basis.
    # A SYNTHETIC_TEST_ONLY capability with _issued added is still not AUTHORIZED.
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.custody_source_authorization_status != "AUTHORIZED"

    record(
        "R5 marker-copy via object.__setattr__ not effective", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
        detail="object.__setattr__ can add _issued, but R5 does not check it — authorization is basis-based",
    )


# ============================================================================
# R5: No _issue() classmethod
# ============================================================================

def test_r5_no_issue_classmethod():
    """R5: CustodyAuthorityCapability has no _issue() classmethod.

    Direct _issue() attack is not expressible in R5.
    """
    assert not hasattr(CustodyAuthorityCapability, "_issue"), \
        "R5 capability must not have _issue() classmethod"
    record(
        "R5 no _issue() classmethod", False,
        decision="N/A", refusal=None, status="N/A",
        detail="R5 lacks _issue() — direct _issue() attack not expressible",
    )


# ============================================================================
# R5: Rederivation with SYNTHETIC_TEST_ONLY — ACCEPT_FIELD_BINDING but not AUTHORIZED
# ============================================================================

def test_r5_rederive_synthetic():
    """R5: Rederivation with SYNTHETIC_TEST_ONLY capability.

    Returns ACCEPT_FIELD_BINDING with SYNTHETIC_TEST_ONLY status —
    not an unauthorized trusted outcome.
    """
    policy = ConsumerPolicy(
        store=_store_with_evidence(),
        custody_authority=_synthetic_capability(knowledge_cutoff=CUTOFF),
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.ACCEPT_FIELD_BINDING
    assert out.custody_source_authorization_status == "SYNTHETIC_TEST_ONLY"
    record(
        "R5 rederive with SYNTHETIC_TEST_ONLY -> ACCEPT_FIELD_BINDING/SYNTHETIC_TEST_ONLY", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
        detail="Not AUTHORIZED — not an unauthorized trusted outcome",
    )


# ============================================================================
# R5: Wrong knowledge_cutoff → INTEGRATION_REQUIRED
# ============================================================================

def test_r5_wrong_knowledge_cutoff():
    """R5: Wrong knowledge_cutoff → INTEGRATION_REQUIRED."""
    cap = _synthetic_capability(knowledge_cutoff=CUTOFF + timedelta(days=1))
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
    record(
        "R5 wrong knowledge_cutoff -> INTEGRATION_REQUIRED", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


# ============================================================================
# R5: Wrong record_kind → INTEGRATION_REQUIRED
# ============================================================================

def test_r5_wrong_record_kind():
    """R5: record_kind mismatch → INTEGRATION_REQUIRED."""
    cap = _synthetic_capability(
        record_kind="LIQUIDATION", knowledge_cutoff=CUTOFF,
    )
    policy = ConsumerPolicy(
        store=_store_with_evidence(), custody_authority=cap,
    )
    v = _base_verdict(custody_source_authorized=True, record_kind="TRADE")
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
    record(
        "R5 wrong record_kind -> INTEGRATION_REQUIRED", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


# ============================================================================
# R5: No capability → INTEGRATION_REQUIRED
# ============================================================================

def test_r5_no_capability():
    """R5: No custody_authority → INTEGRATION_REQUIRED."""
    policy = ConsumerPolicy(store=_store_with_evidence())
    v = _base_verdict(custody_source_authorized=True)
    out = policy.evaluate(
        v, rederive=lambda: v, required_fields=("trade_price",),
        knowledge_cutoff=CUTOFF,
    )
    assert out.decision == ConsumerDecision.INTEGRATION_REQUIRED
    record(
        "R5 no custody_authority -> INTEGRATION_REQUIRED", False,
        decision=out.decision.value,
        refusal=None,
        status=out.custody_source_authorization_status,
    )


# ---------------------------------------------------------------------------
# Machine-readable results JSON writer
# ---------------------------------------------------------------------------

def _write_results_json(results: list[dict], path: str) -> None:
    """Write machine-readable results JSON to an explicit path."""
    output = {
        "schema": "sensor-b5-i09p3-r5-baseline-probe/v1",
        "r5_sha": PINNED_R5_COMMIT,
        "r5_worktree": str(_r5_worktree),
        "total": len(results),
        "vulnerable_count": sum(1 for r in results if r["vulnerable"]),
        "results": results,
    }
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entry point — explicit, opt-in execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import inspect
    import pytest

    # Run pytest first for standard test reporting
    exit_code = pytest.main(
        [__file__, "-v", "--tb=short"] + _remaining
    )

    # For --write-results, directly invoke test functions so RESULTS
    # is populated in THIS module's namespace (pytest.main() runs tests
    # in an imported copy of the module, so its RESULTS list is not
    # visible here).
    if _args.write_results:
        test_functions = [
            obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if name.startswith("test_") and inspect.isfunction(obj)
        ]
        RESULTS.clear()
        for tf in test_functions:
            tf()
        _write_results_json(RESULTS, _args.write_results)

    sys.exit(exit_code)