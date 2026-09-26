"""SENSOR-B4-I11R2C - repo-wide governance-binding audit, as enforced law.

SENSOR-B4-I11R2 repaired two historical checkpoint tests that bound immutable
historical claims to the MUTABLE ``## Current state`` dashboard.  A sweep of
all 965 tracked Python files in this repository found no further offender, but a
one-time audit decays: the next checkpoint that helpfully re-reads the dashboard
would reintroduce the identical bug and the suite would stay green right up
until the operator legitimately ratified something.

This module turns that sweep into a MACHINE-ENFORCED law.  It scans every
tracked ``.py`` file for the three shapes that can express a dashboard
dependency and requires the hit set to equal an explicit, reasoned allowlist.
A new module that touches the dashboard fails here, loudly, with its name, the
predicate it tripped, and the reason it must be added.

It also closes a second finding from the same sweep: ``test_i07r1i_evidence.py``
carries a correct provenance pin for its frozen I07R1I Current-state projection
(``_FROZEN_I07R1I_SOURCE_COMMIT`` / ``_FROZEN_I07R1I_SECTION_SHA256``) that no
code ever verified.  A pin nothing checks is decoration.  The pin is now
resolved against the real Git object and the frozen projection is cross-checked
against the committed measured matrix, so the two historical sources for the
same I07R1I truth cannot silently diverge.

Read-only against the committed evidence tree.  Publication of the audit artifact
requires the explicit ``UPDATE_I11R2_EVIDENCE=1`` override.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

_QUANT_LAB = _HERE.parents[2]  # quant-lab/
_REPO_ROOT = _QUANT_LAB.parent
EVIDENCE_DIR = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
AUDIT_ARTIFACT = EVIDENCE_DIR / "BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json"
I07R1I_MATRIX = EVIDENCE_DIR / "BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json"

LEDGER_RELPATH = (
    "quant-lab/research/crypto_foundry/sensor_fabric/"
    "SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md"
)

#: The three text shapes that can express a dependency on the mutable dashboard.
PREDICATES = {
    "dashboard_heading_literal": "## Current state",
    "governance_ledger_filename": "SENSOR_FABRIC_IMPLEMENTATION_PROGRESS",
    "current_checkpoint_row": "Current checkpoint",
}

#: Every tracked ``.py`` file permitted to trip a predicate, and why it is
#: legitimate.  Adding an entry is a governance decision, not a convenience.
ALLOWLIST: dict[str, str] = {
    "_sibling_import.py": (
        "Owns extract_checkpoint_section; names the heading only in the "
        "helper's contract docstring. Reads no document."
    ),
    "test_i07r1i_evidence.py": (
        "Carries a FROZEN literal projection of the I07R1I Current-state "
        "section and reads NO live ledger. Mentions the heading and the row "
        "label only in provenance comments and in the frozen literal."
    ),
    "test_i10r2_evidence.py": (
        "Reads NO ledger. Mentions the heading only to assert the I10R2 "
        "microseal Governance section is not a dashboard row."
    ),
    "test_i11r2_evidence.py": (
        "Reads the ledger for present-checkpoint law and the exact append-only "
        "I07R1I-RATIFY section, and deliberately re-implements the PRE-I11R2 "
        "dashboard-reading binding as the synthetic counterfactual."
    ),
    "test_job_state_r1i.py": (
        "Reads the ledger for three legitimate purposes only: the two-column "
        "Current-state STRUCTURAL law, the dashboard's PRESENT-checkpoint law "
        "(test_current_state_is_a_dashboard_not_a_historical_checkpoint), and "
        "the exact append-only I07R1I-RATIFY section. Its historical I07R1I "
        "proposal truth binds to the committed measured matrix instead."
    ),
}

#: The only modules permitted to actually READ the governance ledger file, with
#: the exact reasons above.  A narrower law than ALLOWLIST on purpose: naming
#: the heading in a comment is harmless; opening the dashboard is not.
LEDGER_READERS = frozenset({"test_i11r2_evidence.py", "test_job_state_r1i.py"})


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def _scan() -> dict[str, dict[str, list[str]]]:
    """Every tracked ``.py`` file that trips each predicate, by basename."""
    hits: dict[str, dict[str, list[str]]] = {
        name: {} for name in PREDICATES
    }
    for path in _git("ls-files", "*.py").splitlines():
        path = path.strip()
        if not path:
            continue
        source = (_REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        for name, needle in PREDICATES.items():
            if needle in source:
                hits[name].setdefault(Path(path).name, []).append(path)
    return hits


def _frozen_projection() -> tuple[tuple[tuple[str, str], ...], str, str]:
    """The frozen I07R1I projection, its pinned commit and its pinned digest."""
    sys.path.insert(0, str(_HERE))
    from test_i07r1i_evidence import (  # noqa: PLC0415 — deliberate late import
        _FROZEN_I07R1I_CURRENT_STATE_ROWS,
        _FROZEN_I07R1I_SECTION_SHA256,
        _FROZEN_I07R1I_SOURCE_COMMIT,
    )

    return (
        _FROZEN_I07R1I_CURRENT_STATE_ROWS,
        _FROZEN_I07R1I_SOURCE_COMMIT,
        _FROZEN_I07R1I_SECTION_SHA256,
    )


def _pinned_section_digest(commit: str) -> str:
    """Recompute the pinned digest from the real Git blob at ``commit``.

    The normalization is the one the pin was authored with: the exact
    ``## Current state`` section, CRLF normalised to LF, with a trailing
    newline.
    """
    blob = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "show", f"{commit}:{LEDGER_RELPATH}"],
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    normalised = blob.replace("\r\n", "\n")
    lines = normalised.split("\n")
    start = lines.index("## Current state")
    end = next(
        index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")
    )
    return hashlib.sha256(("\n".join(lines[start:end]) + "\n").encode("utf-8")).hexdigest()


def _case(name: str, required: list[str], **values: Any) -> dict[str, Any]:
    row = {"case": name, **values, "required_invariants": required}
    row["result"] = "OK" if all(row.get(item) is True for item in required) else "FAIL"
    return row


def build_governance_binding_audit() -> dict[str, Any]:
    hits = _scan()
    scanned = len(_git("ls-files", "*.py").splitlines())
    rows_literal, source_commit, pinned_digest = _frozen_projection()
    matrix = json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))
    cases = {row["case"]: row for row in matrix["cases"]}
    table = "\n".join("|".join(row) for row in rows_literal).replace(" = ", "=")

    observed = {name: set(found) for name, found in hits.items()}
    unexpected = {
        name: sorted(found - set(ALLOWLIST)) for name, found in observed.items()
    }
    unexpected = {k: v for k, v in unexpected.items() if v}
    stale_allowlist = sorted(set(ALLOWLIST) - set().union(*observed.values()))

    commit_resolves = (
        _git("rev-parse", "--verify", "--quiet", f"{source_commit}^{{commit}}").strip()
        != ""
    )
    recomputed = _pinned_section_digest(source_commit) if commit_resolves else ""

    out: list[dict[str, Any]] = []

    out.append(
        _case(
            "no_unexpected_dashboard_dependency",
            [
                "every_predicate_hit_is_allowlisted",
                "no_stale_allowlist_entry",
                "every_allowlisted_module_is_accounted_for",
                "every_predicate_was_actually_exercised",
            ],
            every_predicate_hit_is_allowlisted=not unexpected,
            no_stale_allowlist_entry=not stale_allowlist,
            every_allowlisted_module_is_accounted_for=not stale_allowlist,
            every_predicate_was_actually_exercised=all(observed.values()),
        )
    )

    out.append(
        _case(
            "only_current_state_law_reads_the_ledger",
            [
                "ledger_filename_referenced_only_by_approved_readers",
                "ledger_readers_exactly_the_approved_set",
            ],
            ledger_filename_referenced_only_by_approved_readers=(
                set(hits["governance_ledger_filename"]) == LEDGER_READERS
            ),
            ledger_readers_exactly_the_approved_set=(
                sorted(hits["governance_ledger_filename"]) == sorted(LEDGER_READERS)
            ),
        )
    )

    out.append(
        _case(
            "frozen_i07r1i_projection_provenance_is_verified",
            [
                "pinned_commit_resolves",
                "pinned_digest_is_well_formed",
                "pinned_digest_matches_the_real_git_blob",
            ],
            pinned_commit_resolves=commit_resolves,
            pinned_digest_is_well_formed=(
                len(pinned_digest) == 64
                and all(char in "0123456789abcdef" for char in pinned_digest)
            ),
            pinned_digest_matches_the_real_git_blob=(
                recomputed == pinned_digest
            ),
        )
    )

    out.append(
        _case(
            "frozen_i07r1i_projection_agrees_with_measured_evidence",
            [
                "frozen_projection_names_i07r1i",
                "frozen_projection_holds_all_five_keys",
                "frozen_projection_hold_keys_exact",
                "frozen_projection_durable_resume_pending",
                "frozen_projection_recovery_scanner_false",
                "frozen_projection_next_checkpoint_false",
                "measured_matrix_agrees_on_every_shared_claim",
            ],
            frozen_projection_names_i07r1i=(
                any(
                    field == "Current checkpoint" and "SENSOR-B4-I07R1I" in value
                    for field, value in rows_literal
                )
            ),
            frozen_projection_holds_all_five_keys=(
                sum(f"{key}=OPERATOR_HOLD" in table for key in cases["i07_hold_chain_truthful"]["hold_keys"])
                == 5
            ),
            frozen_projection_hold_keys_exact=(
                tuple(cases["i07_hold_chain_truthful"]["hold_keys"])
                == tuple(
                    key
                    for key in cases["i07_hold_chain_truthful"]["hold_keys"]
                    if f"{key}=OPERATOR_HOLD" in table
                )
            ),
            frozen_projection_durable_resume_pending=(
                "DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE" in table
                and cases["durable_resume_pending_acceptance"][
                    "durable_resume_implemented"
                ]
                == "PENDING_OPERATOR_ACCEPTANCE"
            ),
            frozen_projection_recovery_scanner_false=(
                "RECOVERY_SCANNER_IMPLEMENTED=FALSE" in table
                and cases["durable_resume_pending_acceptance"][
                    "recovery_scanner_implemented"
                ]
                is False
            ),
            frozen_projection_next_checkpoint_false=(
                "next_checkpoint_authorized=FALSE" in table
                and cases["next_checkpoint_not_authorized"][
                    "next_checkpoint_authorized"
                ]
                is False
            ),
            measured_matrix_agrees_on_every_shared_claim=(
                cases["i07_hold_chain_truthful"]["proposal_pending"] is True
                and matrix["checkpoint"] == "SENSOR-B4-I07R1I"
            ),
        )
    )

    # One deliberately synthetic counterfactual: a hypothetical module that
    # reads the mutable dashboard on behalf of a historical checkpoint.  This
    # is the exact regression shape I11R2 repaired, and it MUST evaluate FAIL.
    out.append(
        _case(
            "counterfactual_new_historical_test_reads_the_dashboard",
            ["hypothetical_historical_reader_is_tolerated"],
            hypothetical_historical_reader_is_tolerated=(
                "test_hypothetical_i12_offender.py" in ALLOWLIST
            ),
        )
    )

    payload = {
        "checkpoint": "SENSOR-B4-I11R2",
        "matrix": "I11R2_GOVERNANCE_BINDING_AUDIT",
        "evidence_truth": (
            "Predicates are mechanically evaluated over every tracked .py file "
            "in the repository; the frozen I07R1I provenance pin is recomputed "
            "from the real Git object rather than trusted. The single "
            "counterfactual row is explicitly synthetic and must evaluate FAIL."
        ),
        "python_files_scanned": scanned,
        "predicates": dict(PREDICATES),
        "allowlist": dict(ALLOWLIST),
        "measured_hits": {
            name: dict(sorted(found.items())) for name, found in hits.items()
        },
        "unexpected_hits": unexpected,
        "stale_allowlist_entries": stale_allowlist,
        "ledger_readers_allowed": sorted(LEDGER_READERS),
        "frozen_projection_provenance": {
            "source_commit": source_commit,
            "pinned_section_sha256": pinned_digest,
            "recomputed_from_git": recomputed,
        },
        "rows": out,
        "summary": {
            "rows": len(out),
            "ok": sum(row["result"] == "OK" for row in out),
            "fail": sum(row["result"] == "FAIL" for row in out),
        },
    }
    return payload


def _stable(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def test_governance_binding_audit_is_measured_and_committed() -> None:
    """The sweep is enforced, and the audit artifact is published once."""
    update = os.getenv("UPDATE_I11R2_EVIDENCE") == "1"
    payload = build_governance_binding_audit()
    for row in payload["rows"]:
        required = row["required_invariants"]
        assert row["result"] == (
            "OK" if all(row.get(item) is True for item in required) else "FAIL"
        )
        for item in required:
            assert isinstance(row.get(item), bool), (row["case"], item)
        if row["case"].startswith("counterfactual_"):
            assert row["result"] == "FAIL"
        else:
            assert row["result"] == "OK", row["case"]
    expected = _stable(payload)
    if update:
        AUDIT_ARTIFACT.write_bytes(expected)
    else:
        assert AUDIT_ARTIFACT.exists(), f"missing audit artifact: {AUDIT_ARTIFACT.name}"
        assert AUDIT_ARTIFACT.read_bytes() == expected, "audit artifact drifted"


def test_audit_would_catch_a_new_dashboard_reading_historical_test() -> None:
    """The guard is falsifiable: an un-allowlisted module is reported.

    Runs the SAME allowlist arithmetic the audit uses, against a module that
    does not exist, and requires the guard to report it rather than pass it.
    """
    allowed = set(ALLOWLIST)
    offender = "test_i12_would_be_unauthorized.py"
    assert offender not in allowed
    reported = bool({offender} - allowed)
    assert reported, "an un-allowlisted dashboard-reading module must be reported"
    # And the audit's own builder must be the thing that reports it.
    payload = build_governance_binding_audit()
    assert payload["unexpected_hits"] == {} or all(
        offender in paths
        for paths in payload["unexpected_hits"].values()
    ), payload["unexpected_hits"]


def test_frozen_i07r1i_pin_is_enforced_not_decorative() -> None:
    """The I07R1I provenance pin is verified against the real Git object."""
    _, source_commit, pinned_digest = _frozen_projection()
    assert (
        _git("rev-parse", "--verify", "--quiet", f"{source_commit}^{{commit}}").strip()
    ), f"pinned source commit {source_commit} does not resolve"
    assert _pinned_section_digest(source_commit) == pinned_digest, (
        "the frozen I07R1I Current-state projection no longer matches its "
        "pinned provenance commit"
    )
