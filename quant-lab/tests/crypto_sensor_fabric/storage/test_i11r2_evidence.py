"""SENSOR-B4-I11R2A/B - measured historical governance-test decoupling evidence.

Every non-counterfactual predicate here is MECHANICALLY OBSERVED from the real
repository: the real governance ledger, the real committed immutable artifacts
the two repaired tests now bind to, the real `git` state of `quant-lab/src`,
the real SHA-256 of all 131 pre-existing `bloc_04` evidence artifacts, and the
VERBATIM trailing summary lines of the real pytest runs recorded in
`BLOC_04_I11R2_REGRESSION_RUN_RECORD.txt`.

Suite results are PARSED out of that committed run record.  They are never
hand-typed into the matrix.

The one `counterfactual_*` row is explicitly synthetic: it re-evaluates the
PRE-I11R2 binding (a historical checkpoint test that reads the mutable
`## Current state` dashboard) against the present, legitimately-advanced
dashboard, and MUST evaluate FAIL.  It is the exact shape that broke.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from _sibling_import import extract_checkpoint_section

_QUANT_LAB = _HERE.parents[2]  # quant-lab/
EVIDENCE_DIR = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_04"
)
LEDGER = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md"
)
RUN_RECORD = EVIDENCE_DIR / "BLOC_04_I11R2_REGRESSION_RUN_RECORD.txt"
I10R2_MICROSEAL = EVIDENCE_DIR / "BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.md"
I07R1I_MATRIX = EVIDENCE_DIR / "BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json"

#: The I11R1 accepted start HEAD.  Production code must be identical to it.
I11R1_HEAD = "ccc6a7264fcf5ff560777c9c9a685f1877746987"

#: The five upstream I07 approval keys the I07R1I section proposed as held.
I07R1I_HOLD_KEYS = (
    "PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED",
    "PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED",
    "PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED",
    "PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED",
    "PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED",
)

#: The exact heading of the superseding ratification, byte-for-byte.
I07R1I_RATIFY_HEADING = (
    "## SENSOR-B4-I07R1I-RATIFY " + chr(0x2014) + " operator accepts the "
    "complete I07 chain, authorizes I08"
)


# ---------------------------------------------------------------------------
# The mutable dashboard, and the two PRE-I11R2 bindings that wrongly read it
# ---------------------------------------------------------------------------

#: A synthetic dashboard carrying a superseded checkpoint's PROPOSAL state.  It
#: exists only so the counterfactual can show that a dashboard-reading binding
#: changes when the dashboard changes.  It is never written to the repository.
_SCRAMBLED_DASHBOARD = (
    "## Current state" + chr(10)
    + chr(10)
    + "| Field | Value |" + chr(10)
    + "|---|---|" + chr(10)
    + "| Current checkpoint | SENSOR-B4-I10R2 |" + chr(10)
    + "| Operator review state | "
    + "PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED=OPERATOR_HOLD; "
    + "PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED=OPERATOR_HOLD; "
    + "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED=PENDING_OPERATOR_REVIEW; "
    + "G4-09_CATALOG_REBUILD_GATE=IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW; "
    + "next_checkpoint_authorized=FALSE; "
    + "recommended_next=OPERATOR REVIEW OF COMPLETE I10 -> I10R1 -> I10R2 CHAIN; "
    + "I11+ unauthorized; research frozen |" + chr(10)
    + "| historical | "
    + "SENSOR-B4-I07R1I; "
    + "PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED=OPERATOR_HOLD; "
    + "PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED=OPERATOR_HOLD; "
    + "PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED=OPERATOR_HOLD; "
    + "PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED=OPERATOR_HOLD; "
    + "PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED=OPERATOR_HOLD; "
    + "DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE; "
    + "RECOVERY_SCANNER_IMPLEMENTED=FALSE |" + chr(10)
    + chr(10)
)


def _dashboard_rows(text: str) -> list[list[str]]:
    """Ordinary rows of the ``| Field | Value |`` table under Current state."""
    lines = text.split(chr(10))
    start = lines.index("## Current state")
    rows: list[list[str]] = []
    for line in lines[start:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells == ["Field", "Value"]:
            continue
        if all(set(cell) <= {"-", " "} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _old_i07r1i_binding(text: str) -> bool:
    """The PRE-I11R2 I07R1I test, verbatim in substance: it reads the dashboard."""
    table = chr(10).join("|".join(row) for row in _dashboard_rows(text)).replace(
        " = ", "="
    )
    if not all(f"{key}=OPERATOR_HOLD" in table for key in I07R1I_HOLD_KEYS):
        return False
    return all(
        item in table
        for item in (
            "DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE",
            "RECOVERY_SCANNER_IMPLEMENTED=FALSE",
            "next_checkpoint_authorized=FALSE",
            "SENSOR-B4-I07R1I",
        )
    )


def _old_i10r2_binding(text: str) -> bool:
    """The PRE-I11R2 I10R2 helper, verbatim in substance: it reads the dashboard."""
    current = text.split("## Current state", 1)[1].split(
        "## Append-only SENSOR-B4-I10R1 / I10R2 checkpoint history", 1
    )[0]
    required = (
        "Current checkpoint | SENSOR-B4-I10R2",
        "PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED=OPERATOR_HOLD",
        "PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED=OPERATOR_HOLD",
        "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED=PENDING_OPERATOR_REVIEW",
        "G4-09_CATALOG_REBUILD_GATE=IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW",
        "next_checkpoint_authorized=FALSE",
        "recommended_next=OPERATOR REVIEW OF COMPLETE I10 -> I10R1 -> I10R2 CHAIN",
        "I11+ unauthorized; research frozen",
    )
    return all(item in current for item in required) and (
        "recommended_next=OPERATOR REVIEW OF SENSOR-B4-I10;" not in current
    )


def _scrambled(ledger_text: str) -> str:
    """The real ledger with its live dashboard replaced by an arbitrary one."""
    begin = ledger_text.index("## Current state")
    end = ledger_text.index(
        "## Append-only SENSOR-B4-I10R1 / I10R2 checkpoint history", begin
    )
    return ledger_text[:begin] + _SCRAMBLED_DASHBOARD + ledger_text[end:]


# ---------------------------------------------------------------------------
# The REPAIRED bindings: each reads exactly one immutable source, never the
# dashboard.  Note that neither function takes the ledger as an argument.
# ---------------------------------------------------------------------------


def _new_i07r1i_verdict() -> bool:
    matrix = json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))
    if matrix["checkpoint"] != "SENSOR-B4-I07R1I":
        return False
    cases = {row["case"]: row for row in matrix["cases"]}
    hold = cases.get("i07_hold_chain_truthful", {})
    resume = cases.get("durable_resume_pending_acceptance", {})
    following = cases.get("next_checkpoint_not_authorized", {})
    return (
        hold.get("result") == "PASS"
        and hold.get("proposal_pending") is True
        and tuple(hold.get("hold_keys", ())) == I07R1I_HOLD_KEYS
        and resume.get("durable_resume_implemented") == "PENDING_OPERATOR_ACCEPTANCE"
        and resume.get("recovery_scanner_implemented") is False
        and following.get("next_checkpoint_authorized") is False
    )


def _new_i10r2_verdict() -> bool:
    governance = extract_checkpoint_section(
        I10R2_MICROSEAL.read_text(encoding="utf-8"), "## Governance"
    )
    required = (
        "PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED = OPERATOR_HOLD",
        "PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED = OPERATOR_HOLD",
        "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED = PENDING_OPERATOR_REVIEW",
        "G4-09_CATALOG_REBUILD_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW",
        "next_checkpoint_authorized = FALSE",
        "recommended_next = OPERATOR REVIEW OF COMPLETE I10 -> I10R1 -> I10R2 CHAIN",
        "I11 = UNAUTHORIZED",
        "research = FROZEN",
    )
    forbidden = (
        "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED = OPERATOR_ACCEPTED",
        "G4-09_CATALOG_REBUILD_GATE = OPERATOR_ACCEPTED",
        "next_checkpoint_authorized = TRUE",
    )
    return all(item in governance for item in required) and not any(
        item in governance for item in forbidden
    )


# ---------------------------------------------------------------------------
# Historical evidence immutability, production diff, regression truth
# ---------------------------------------------------------------------------


def _files_read_by(action: Any) -> tuple[Any, set[Path]]:
    """Run ``action`` and report every file it actually read off disk.

    This is the instrument that turns "this test no longer depends on the
    mutable dashboard" from a claim into a falsifiable measurement: if the
    binding ever read the ledger, the ledger's resolved path would appear in
    the returned set.  No such set is hand-written.
    """
    seen: set[Path] = set()
    real_text = Path.read_text
    real_bytes = Path.read_bytes

    def spy_text(self: Path, *args: Any, **kwargs: Any) -> Any:
        seen.add(self)
        return real_text(self, *args, **kwargs)

    def spy_bytes(self: Path, *args: Any, **kwargs: Any) -> Any:
        seen.add(self)
        return real_bytes(self, *args, **kwargs)

    Path.read_text = spy_text  # type: ignore[method-assign]
    Path.read_bytes = spy_bytes  # type: ignore[method-assign]
    try:
        value = action()
    finally:
        Path.read_text = real_text  # type: ignore[method-assign]
        Path.read_bytes = real_bytes  # type: ignore[method-assign]
    return value, {path.resolve() for path in seen}


#: The closed, auditable set of artifacts that the ACCEPTED I04 evidence tests
#: re-write through ``Path.write_text`` on every run.  On this Windows host
#: that rewrites their LF line endings to CRLF.  SENSOR-B4-I11R2 does not fix
#: that I04 defect (it is out of scope) and does not pretend it is absent: a
#: rewrite is tolerated ONLY when the CONTENT is byte-identical after undoing
#: the line-ending rewrite AND the artifact is named below.  Any other byte
#: change, or a CRLF rewrite of an artifact not named below, is a real
#: historical rewrite and fails closed.
I04_CRLF_CHURN_ALLOWLIST = frozenset(
    {
        "BLOC_04_I03R1_ATOMIC_ORDER.json",
        "BLOC_04_I03R1_NAMESPACE_DURABILITY.json",
        "BLOC_04_I04R1_POINTER_SCHEMA.json",
        "BLOC_04_I04R1_PROVENANCE_MATRIX.json",
        "BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json",
        "BLOC_04_I04_CATALOG_SCHEMAS.json",
        "BLOC_04_I04_MANIFEST_CONCURRENCY.json",
    }
)


def _evidence_hashes_unchanged() -> dict[str, list[str]]:
    """Classify every pre-existing evidence artifact against its baseline hash.

    Returns ``mismatched`` (a real historical rewrite -- always fatal),
    ``missing``, and ``crlf_only`` (content identical, line endings rewritten by
    a named I04 writer -- recorded, never silently accepted).
    """
    mismatched: list[str] = []
    missing: list[str] = []
    crlf_only: list[str] = []
    for name, digest in HISTORICAL_EVIDENCE.items():
        path = EVIDENCE_DIR / name
        if not path.is_file():
            missing.append(name)
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() == digest:
            continue
        normalised = raw.replace(bytes((13, 10)), bytes((10,)))
        if hashlib.sha256(normalised).hexdigest() == digest:
            crlf_only.append(name)
        else:
            mismatched.append(name)
    return {"mismatched": mismatched, "missing": missing, "crlf_only": crlf_only}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=_QUANT_LAB,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def _production_untouched() -> list[str]:
    """Every way production source could have drifted, as one flat file list."""
    changed: list[str] = []
    for args in (
        ("diff", "--name-only", "HEAD", "--", "quant-lab/src"),
        ("diff", "--cached", "--name-only", "--", "quant-lab/src"),
        ("diff", "--name-only", I11R1_HEAD, "--", "quant-lab/src"),
        ("ls-files", "--others", "--exclude-standard", "quant-lab/src"),
    ):
        changed.extend(line for line in _git(*args).splitlines() if line.strip())
    return sorted(set(changed))


def _run_record() -> dict[str, dict[str, Any]]:
    """Parse the committed verbatim pytest summary lines.  Never hand-declared."""
    text = RUN_RECORD.read_text(encoding="utf-8")
    parsed: dict[str, dict[str, Any]] = {}
    for block in text.split("--- RUN ")[1:]:
        name = block.split(" ---", 1)[0].strip()
        exit_match = re.search(r"^exit_code:\s*(\d+)\s*$", block, re.M)
        summary = [
            line.strip()
            for line in block.splitlines()
            if re.match(r"^\d+ passed", line.strip())
        ]
        assert exit_match is not None, f"no exit_code for run {name}"
        assert summary, f"no summary line for run {name}"
        line = summary[0]
        counts = {
            key: int(value)
            for value, key in re.findall(r"(\d+) (passed|failed|skipped|error|warning)", line)
        }
        parsed[name] = {
            "exit_code": int(exit_match.group(1)),
            "summary_line": line,
            "counts": counts,
        }
    return parsed


#: SHA-256 of every `bloc_04` evidence artifact that existed BEFORE SENSOR-B4-I11R2
#: touched anything.  Captured at the mandatory start and re-compared after.
HISTORICAL_EVIDENCE: dict[str, str] = {
    'BLOC_04_I01R1_LINEAGE_SCHEMA_SEAL_EVIDENCE.md': '48f84e6dfa7d52ec51c698c091261945fd0eb8d2e9dfb0d0f9bcf48dcf50e2dd',
    'BLOC_04_I01_STORAGE_CONTRACTS_EVIDENCE.md': '7f1edb4e668b492d67f2b4799dbf7cccdf7e45a5ff35c31521e34441408a08f7',
    'BLOC_04_I02R1_CANONICAL_PATH_SEAL_EVIDENCE.md': 'd4d78d10fa5aa9ded6601e3d1a819f76b3d035bad14fee46310ee42f4e342820',
    'BLOC_04_I02R1_OPERATOR_RATIFICATION.md': 'd9e63d6d454fb2295be528bb905380c8b35b6ade448f43621210550e6651c881',
    'BLOC_04_I02_CONTENT_ADDRESSING_EVIDENCE.md': 'b15c3827262e2f395d5601b441a3dc2103ceda41283e73a596cb5bdd51165ebe',
    'BLOC_04_I03R1_ATOMIC_ORDER.json': '6c026371a92364645f1cf3c4bfbd23585fc362bd2985efac19d7c041fe355534',
    'BLOC_04_I03R1_DURABILITY_NAMESPACE_SEAL_EVIDENCE.md': '63b950b0983da1bafd923b531e5ca81df29b873cc5bb6982c6232d4840b5007d',
    'BLOC_04_I03R1_NAMESPACE_DURABILITY.json': 'c869786cb3c157a6c7ac37139444b3c7d797d454dc93895c8fe2e4324b474299',
    'BLOC_04_I03R1_OPERATOR_RATIFICATION.md': '4686e4358a0bb75fef10a35a1fb687f86eff538a023c4dbbda4e5cace471e6ef',
    'BLOC_04_I03_ATOMIC_FILESYSTEM_EVIDENCE.md': 'd66b56f9b34c39a65b6a3d8cd59f14d23a1bb48e37ed6f7b7223e602a09a0aef',
    'BLOC_04_I03_ATOMIC_ORDER.json': '73a170484c529f90aac1ea9c533cc067ce346035fa4bb889a183be04d1bf5bbd',
    'BLOC_04_I03_CRASH_MATRIX.json': '11f8182c19cda940c20b808d80584dd55444ed208966c9f2ed4ae45e0f792bf3',
    'BLOC_04_I04R1_POINTER_SCHEMA.json': '23d3b6d8aa95ea997784eed4ec82323333aa8811fc74297f2fc45b6ad2e95366',
    'BLOC_04_I04R1_PROVENANCE_INTEGRITY_SEAL_EVIDENCE.md': 'bbd315775d399febb09a221c012d6d0f8e8663f0a0d271659f8da3230ca95379',
    'BLOC_04_I04R1_PROVENANCE_MATRIX.json': '540850991a25dcd2ae53a829cdd594b4a3f77f886562ae267bf4f84c0d7f4ca2',
    'BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json': '05b5b025735ec3938f29deb5e416dd8fd4d50ad2b86da82a8fd9cce4c8f86075',
    'BLOC_04_I04R2_USABLE_PROVENANCE_SEAL_EVIDENCE.md': 'bb585e769b3741758b57f19767b394ed172dedc8afe234a9f6fc6329149fe2bc',
    'BLOC_04_I04_ACQUISITION_MANIFEST_EVIDENCE.md': 'c8d0e6ea726fabedcbda75ffbb04fec6120833c56953f5b5787b07d92a98806e',
    'BLOC_04_I04_AUTHORIZATION.md': '34055d5d2c25cf95c8174912af33c53b16dd30f5a78928adf6eaa88ee7598e01',
    'BLOC_04_I04_CATALOG_SCHEMAS.json': '6a8a56a650fa726c9d318942a05842f015631a543bb8e778507d519a2532aa62',
    'BLOC_04_I04_MANIFEST_CONCURRENCY.json': '14c59e6ab6ce271a6cf4c07461fdf4d42d059426149aa405211c2c7f9fc7b462',
    'BLOC_04_I05R1_DURABILITY_MATRIX.json': '08e303eb8d8ad4d138fc44a67d33bb000a14a50ad9821d06b61674beb5b56e55',
    'BLOC_04_I05R1_DURABLE_END_TO_END_LINEAGE_SEAL_EVIDENCE.md': '99bc162d9afa6d006bf218259d3a5c2df8de9ea3aaf1f09a941faf03f592d1f6',
    'BLOC_04_I05R1_END_TO_END_LINEAGE_MATRIX.json': '4ddc227731df21389396d8ea7e18c38e1ff2a769195d3e57fda9abd911bae019',
    'BLOC_04_I05R1_SCHEMA_FIDELITY_MATRIX.json': 'e85633b08ecaa9a4cbc6760006bf37c216538cb93b899d65f8d51b4ec0d2342a',
    'BLOC_04_I05R2_CRASH_BOUNDARY_MATRIX.json': '03819592cfcde3271a58fc1ea66794150b49842e9235d51df1dc058b34107b02',
    'BLOC_04_I05R2_FAIL_CLOSED_PUBLIC_API_SEAL_EVIDENCE.md': '147e3253236276f62c3a7ed1725e6d64ce7a0bbba1db1a86f7a5c2d439803c46',
    'BLOC_04_I05R2_PHYSICAL_SCHEMA_MATRIX.json': '4132a6b0cd80ca10a41b7b12c1b9dc5d8f4c772477fe448a97f83872dac8130c',
    'BLOC_04_I05R2_PUBLIC_API_MATRIX.json': 'e3bdb62ffcabfd75a269dfdf9c3ebb7d9ba80361664cd900ac5f40a12bbccbcd',
    'BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json': 'd8eef5dcc5a458dcae63f58f61757af184e1dc2e86c263a5981e1da64ef0dc19',
    'BLOC_04_I05R3_LINEAGE_IDENTITY_TIME_SEAL_EVIDENCE.md': '10dd8d625fc721ea89340e397f659a8e60388f58125cf35b01ddc6b10b22bb50',
    'BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json': '5119ce729e8ee99fadc8db5498ab8317739ed4c1ff1e13ef5578cd5796d02333',
    'BLOC_04_I05R4_EVIDENCE_IMMUTABILITY_MATRIX.json': 'd2f470a2b2e1ce251bf3811902cbe41fd0dbd3fc662f9c4bbf5e786eaa4d6ff3',
    'BLOC_04_I05R4_EVIDENCE_INTERFACE_RETRY_SEAL_EVIDENCE.md': '89d3e6ab0b766b68eb987cc50fba622a0c594acde57399100c46a25097a51594',
    'BLOC_04_I05R4_OPERATOR_RATIFICATION.md': '15bbf12bc2072de87f3d0d72efd80f5c08c19118199b34421e6640ea5a4baabc',
    'BLOC_04_I05R4_SERVICE_RETRY_MATRIX.json': '345d51a885b66d3318fee95abfefdfbac8c3f8399ac51b03c37b1f41c1ebcb40',
    'BLOC_04_I05R4_VERIFIER_INTERFACE_MATRIX.json': 'c127a7f46409919927ffc24f12d17c1ed231edbdeb14cc4193d9eafe0dd5d6f3',
    'BLOC_04_I05_LINEAGE_MATRIX.json': '4d97632c5f02cd84a935d4a5d3541281fe5db49cf4a2d045edb2338f022534cc',
    'BLOC_04_I05_PROJECTION_INTEGRITY.json': '674188260930c438810fb3e20cc38bcc1ecbb303ed664d715cf0b04d5055f587',
    'BLOC_04_I05_PROJECTION_SCHEMA_MATRIX.json': 'f1771c010cacbed9c7a1ff0ad5d7db247afeddf927e7e465589bfb6df8355aa7',
    'BLOC_04_I05_RAW_PROJECTION_LINEAGE_EVIDENCE.md': '72d5c857b3935f0eea52f9c67ed134b6847f180d8d3c682b08b29d3a75759d64',
    'BLOC_04_I06R1_CANONICAL_CONTRACT_DECLARATION_EVIDENCE.md': 'e01a81b2ea63268addec7043e1f83e9a6840d1c8c1ca8780cbaba14299e24327',
    'BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX.json': '29eb424b538cb3e92ead775fd8c56049e3024aea00fdb00d81dc7c121731ee5b',
    'BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX.json': '1c56015030830a7dc89148b2646d722da4cfe018654c3606d595bf19df777436',
    'BLOC_04_I06R1_IDENTITY_BINDING_MATRIX.json': '2e6350f62d712cc95d40335577d2257161bf8db5eef5a6448d46565eee0dc24c',
    'BLOC_04_I06_IDENTITY_MATRIX.json': '35fd2624387c11708e8d7f9506351e5bae67a8768d435a1126d15a281848c710',
    'BLOC_04_I06_MUTATION_MATRIX.json': '837f5ab553a6bc0aa5b50a5833b110a5a6668db9788226b309a20d70ad30f581',
    'BLOC_04_I06_RESOLUTION_MATRIX.json': '57772f95722d7f8dbfafa5f7b4e077e136d7eba5a3210e8cb0304e49041352e3',
    'BLOC_04_I06_SOURCE_REVISION_MUTATION_EVIDENCE.md': '51d34c2293378410db85368a258b9c18fd68f7239b916388385521d44fbdb909',
    'BLOC_04_I07R1F_CATALOG_CONCURRENCY_MATRIX.json': '62236e75aa707fbeabad678dd28f90b757fe588b7af0692128c21f8868576eb9',
    'BLOC_04_I07R1F_PERSISTED_FLOOR_CONCURRENCY_LEDGER_EVIDENCE.md': '752d5abe4433f15f5342303b930914524cb0155fab035298e67a5abed1e8d856',
    'BLOC_04_I07R1F_PERSISTED_FLOOR_MATRIX.json': '16bf1513328b48370fcf5f7179d1a374c072b8e07eb1a9f520bfa4e365a6b5a3',
    'BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_EVIDENCE.md': 'cc6cfa8e8fcf9ce07ea35282133f38a360cd50aa07a073b5af592ec8817e25b5',
    'BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json': 'bdb7c4b71aa8ebaa85a7bac194e63bb7d5d3322d08825e1d041a409d020d5ea4',
    'BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_MATRIX.json': '14462ebbe732efd97e08dfd43f72a3bf892af03f344874f3a0372fbec2b93e07',
    'BLOC_04_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_EVIDENCE.md': 'bc9388a54110cbcf1b187ed06bbcafa85e2b68d944e2ba7625da95b02dfe85cb',
    'BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_MATRIX.json': 'da742181d00f357e2ad41d6550c3da840b694e6f8b580f3c84dc0a77534b4df0',
    'BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_VALIDATED_READ_EVIDENCE.md': '6a5104bfe914459e4291fdaf8047aba32a04fcd7a09cf3ae2ad36557ad52869f',
    'BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json': '08c7973392bd618f6cce03aa2b9e9e865da764ca72a074b7eb6e23e80d3e2cb0',
    'BLOC_04_I07R1_CHECKPOINT_IDENTITY_MATRIX.json': '20049403eae6d8f9ab580d813f0530d70da36a1f35750837e79cac3fa4c36a06',
    'BLOC_04_I07R1_COORDINATION_MATRIX.json': 'd9c0741df5239d23e51ed5cbf4af80b06d9edd7cc321a00304ce52a0f18de44b',
    'BLOC_04_I07R1_GATE_IDENTITY_REPLAY_EVIDENCE.md': 'd1ac89a16b093e8fa12e0a0dfef5101dbeecdeb58ede6f59c7612905975e2311',
    'BLOC_04_I07R1_PUBLIC_API_MATRIX.json': '5ae3e8d04fe272b498797f9e88920832dfdf9ba10c86f06217f1d0cb2b23f57b',
    'BLOC_04_I07R1_RESTART_REPLAY_MATRIX.json': '8662790705d4313a00b40c1760bd5bf85a0daeb5174f2316fab4653347cd9642',
    'BLOC_04_I07_JOB_RESUME_EVIDENCE.md': '2d06756d82a197241611b88ae9b228d9b40461aaecc90be631e6999d4a167b0c',
    'BLOC_04_I07_JOB_STATE_MATRIX.json': 'e7c900cf506d72822d102c6e55eee922e119b2eb1702189519983bf52a57e7f4',
    'BLOC_04_I07_RESUME_COUPLING_MATRIX.json': '1f2286e565cca17425e83a200b0300b8597659be7ae1dd458e3102247ee7f743',
    'BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json': 'd951399cfdb09e5164be8a38515744baf3ebb3f56f6b07c48fb23d79579d829d',
    'BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json': '21b0ea691448fbe16a00982838864c0e064c0187808c2f3d4fe09c398fb29e35',
    'BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json': 'c71d06fe14f7c15137a8ae57529af51289cea4d1cbe823ce21e5976917efc8a8',
    'BLOC_04_I08R1_RECOVERY_TRUTH_ATOMICITY_EVIDENCE.md': '7a94623802e812843c304ad11ce12a6e284c05ab3b98679a87bf47e163e1956c',
    'BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json': '4f2146f415dfc5fed3b6f5e71d57b2f7ff55af9d415046f70de2c84cc5d37c06',
    'BLOC_04_I08R2R1_CANONICAL_RECORD_MATRIX.json': 'e2c26c422a5beabf311affadee09d46d4aceac5479ae86cf54b2acf823cc698e',
    'BLOC_04_I08R2R1_EVIDENCE_TRUTH_MATRIX.json': 'ae4d5a6afe0ba130b585113abc2150992d898553072640eb20a3a8146cd4d01e',
    'BLOC_04_I08R2R1_LOCK_CLEAR_RACE_MATRIX.json': 'a334ae9738e5d57d8eba351c995638ffd1c2ec257f0b6221fd5f95c6daaf3e6f',
    'BLOC_04_I08R2R1_MICROSEAL_EVIDENCE.md': 'f48aeff5b94d64ce49ff1041de5f8b5a73687a123e27c0706fcb490741ac2c6c',
    'BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json': 'a119bfa98367552ed77cc35015513532305a274d4c634df041c9cc65dd043713',
    'BLOC_04_I08R2_OPERATION_RECORD_INTEGRITY_MATRIX.json': 'c3983023de941edc220abb51d6bb2a9095ab34b44e8b3a7c822bed40b712beb3',
    'BLOC_04_I08R2_OPERATION_TERMINALITY_EVIDENCE.md': '64eea094aa1636dcaaf6319af2aef80d7cbae4e6a7572d6e72e499787e6b055a',
    'BLOC_04_I08R2_OPERATION_TERMINALITY_MATRIX.json': '86625d2df8ea329df61420f29f56e070f40bbafb149ca917c6855946c1d40ba8',
    'BLOC_04_I08_CHAIN_OPERATOR_RATIFICATION.md': '1951afff1f1d6806972d8e5d204f4204953890c0ded3eb240e7efa70380764ec',
    'BLOC_04_I08_CRASH_MATRIX.json': 'cc5c71694a9177314c2a872a28463c7c0d531a6805bc6a9f26083949f195d63f',
    'BLOC_04_I08_QUARANTINE_MATRIX.json': '4f501f64da491fb62003377fdd7999c35983b7f4119be70b44563bc713fcc9e0',
    'BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json': '7a82d6c52bd0acfd59e682684128d4f8c8b9f672ae7c7aa5399c303a57251913',
    'BLOC_04_I08_RECOVERY_QUARANTINE_EVIDENCE.md': '935f069a13b7b5fe717cfcf234fa55e067ab3e24c4a701e9455efb77e6dd1db0',
    'BLOC_04_I08_RECOVERY_SCAN_MATRIX.json': '8a288e8bbe6ddbd39a03480b08bc573e54b92a59b1cf08f72d8dc2817aabb237',
    'BLOC_04_I09R1_BACKFILL_ADMISSION_MATRIX.json': '0ebdc30ae9be6687e15ad5cdd2287a55319451368bd696c545bfe4eabcb76df8',
    'BLOC_04_I09R1_MICROSEAL_EVIDENCE.md': '9296378cb7b8a1e2a652ef127f4775ec93b78514af047f813ece78da91e44682',
    'BLOC_04_I09R1_PRIORITY_AUTHORITY_MATRIX.json': 'd9c9859c9d64686fd91e54a1fed0a060358f3dd73d31f70676cbebaa221b33a9',
    'BLOC_04_I09R1_RETENTION_CONFIG_SAFETY_MATRIX.json': '9d475f1ee70d1e21d219f2255f15864e0509d88c26abce1d98f122a4cb9ec880',
    'BLOC_04_I09R1_SIMULATION_TRUTH_MATRIX.json': '7f8f0582701d37c5fc952d17a2d75319f87732682982f0715609d32e78a69f1b',
    'BLOC_04_I09_CHAIN_OPERATOR_RATIFICATION.md': '9033e4ca80288b3e203089b5be9355345e298795a32a0ed8d34b5b781272a9f5',
    'BLOC_04_I09_NONDESTRUCTIVE_RETENTION_MATRIX.json': '3de1aaeda90f68664e3090f8c7b274d55357170c0a4aeb7bc9917b5c1a4296f7',
    'BLOC_04_I09_PRIORITY_PAUSE_MATRIX.json': '5635a53dc48e12b5f6091a3f43872d98742733865902b5ce7bc6505b71e59bad',
    'BLOC_04_I09_QUOTA_SIMULATION.json': '1baa5d44a2725b1e37b0d9a6483f6453c781227f76286d7ab065c16022e895b6',
    'BLOC_04_I09_QUOTA_STORAGE_ESTIMATOR_EVIDENCE.md': '724336539c9b4ef114e2d3e27e8ed86c3d99aa0039c4ec97224a1446399bb317',
    'BLOC_04_I09_STORAGE_ESTIMATOR_MATRIX.json': 'c5ca8981cd5d3f620db6879f467fcbe24b91795ea102465b5e4c8000d4c38c1f',
    'BLOC_04_I09_WATERMARK_BOUNDARY_MATRIX.json': '39646fa3e7e602fd01d4026e3b6a8167fefbcb62457f7862a196d8171fe4938d',
    'BLOC_04_I10R1_DISCOVERY_COST_MATRIX.json': 'b43ccc1c36b50548f26574f810f00c8eee50816c60ec02f9b61e41eece54825f',
    'BLOC_04_I10R1_DUCKDB_DISCOVERY_MICROSEAL.json': '0f5db0f982db43f25a1e0f31d2292013e0b048d5759011eaf25d3e6bd2786ffa',
    'BLOC_04_I10R1_DUCKDB_DISCOVERY_MICROSEAL.md': 'ace11dbd40d3ffd9ef727a0b1aa44e7a7e2a73b98501497d90a8c2237f8a53a7',
    'BLOC_04_I10R1_DURABLE_RELATION_MATRIX.json': 'f43fe18878cd5a2c5f84cd260d18f46ee482b4c16363d9482b1fb2d38afdeef0',
    'BLOC_04_I10R1_RUNTIME_EVIDENCE_TRUTH_MATRIX.json': '4654abb196bbbdbcd52a4ac2b9632aaf5276ecc7f7595ea8b81b63de13d09ea2',
    'BLOC_04_I10R1_SCHEMA_CONTRACT_MATRIX.json': 'b02f233dfa471c68025927f7ede374f213c673e29512193a846fc5c434e50f4a',
    'BLOC_04_I10R1_STORAGE_USAGE_DIMENSION_MATRIX.json': '89ce91cc18a1097016c65bf2a9562ae2a523a7ef1e9cfc7d09f43773b455591b',
    'BLOC_04_I10R2_LINEAGE_BINDING_MATRIX.json': '6b5202876944f48d351ed07a043377b64a93cdb8de7df90bd4d777adde633078',
    'BLOC_04_I10R2_MEASUREMENT_PARITY_MATRIX.json': '2e27b80b1936495121722a30b5ea7f85f896fefc82d4673bb2d226bb20071de5',
    'BLOC_04_I10R2_RECOVERY_ENVELOPE_MATRIX.json': '91649d1fc3e298df435a7dbb499bdec15ac9c22837bd9539465095319ecc5c04',
    'BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.json': 'e84b827ba62e834ee095da0bb86a00db9f34ab2e0839246017b7c758ef322e1c',
    'BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.md': '4401af2b45b75a340c2dc4ae2e59046cabb7cbb82cf16432bf3711b2f3821577',
    'BLOC_04_I10_CATALOG_REBUILD_MATRIX.json': 'eca261e85c468366b075414eefdc8e3268c62260b843d23ce2bbb7b65012e548',
    'BLOC_04_I10_CHAIN_OPERATOR_RATIFICATION.md': 'c1b3f41abae71b50cd8a40e90c6ecf80022c51ba642cab8f08c032f0fdedd23f',
    'BLOC_04_I10_CORRUPTION_DISCOVERY_MATRIX.json': '3883c7cad4076de57d581e812cab93f878927bd156741d505cb37249d01a8f85',
    'BLOC_04_I10_DUCKDB_REBUILD_EVIDENCE.md': '2df4f210f100f949f868ba8a830800fd8af9c5f80d4463197042ca979094ea74',
    'BLOC_04_I10_EVIDENCE_IMMUTABILITY_MATRIX.json': '6c069d3510a021409efd316c03fcb67b7b1bbbe9ec4c36ad62bce711a6276682',
    'BLOC_04_I10_PORTABILITY_MATRIX.json': '68fc87660e7c6607545b19f99b67727a728796324ac5634991542a6e879e409b',
    'BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json': 'e7aefdc79da06fe820f8f8fcc0c1dd4d51681768dff3782645b190bdb617917b',
    'BLOC_04_I11R1_AUTHORITY_FIREWALL_MATRIX.json': 'e8b74ca3d4fb9565057ef13fc2c424ef6af43efb2e4d37251a3c80d8143a036d',
    'BLOC_04_I11R1_EVIDENCE_TRUTH_MATRIX.json': '77156676e8c46adc37920ce0fc94c428c5347badf36c85997d59aec45dc2819d',
    'BLOC_04_I11R1_OPERATIONAL_STATE_MATRIX.json': 'aeebc5f29f85f21a2af11bb25f1792a87f310eceed4fb73a8cb7b9bd1a742eca',
    'BLOC_04_I11R1_POPULATED_RECONSTRUCTION_MATRIX.json': '79e88078d8c8bea5367b9b3811c4bfa46a39d40661daac727226e47760778d70',
    'BLOC_04_I11R1_POSTGRES_RUNTIME_MICROSEAL.md': 'da156e148656585ced8b0d6c0c5ca8f735fbec4b88dcf1a4fd3e3625e81341a4',
    'BLOC_04_I11R1_SCHEMA_RUNTIME_MATRIX.json': 'c370b2963e94803bd29e8fe9b5bbc3fdbafac84363cc6981a298e6f482738466',
    'BLOC_04_I11R1_TRANSACTION_CONCURRENCY_MATRIX.json': '381c19fd6b7f2c76f98728ffa2bb749945c2ce9d4fb8e55a1c2ebfba9875e8dd',
    'BLOC_04_I11_AUTHORITY_FIREWALL_MATRIX.json': '8fb62f54c3d63d7233ae8884310acaa38e6a7e15f6742e984fcf489eced60708',
    'BLOC_04_I11_POSTGRES_OPERATIONAL_METADATA_EVIDENCE.md': '2031d1602fc754e1f980e44e34aa56a11c77cf36fdea2e8ba9dd872c53e76060',
    'BLOC_04_I11_POSTGRES_SCHEMA_MATRIX.json': '0152ead6a64e79692128d94e80fcc6cddfbb753a25a1bdad7488d3053a456d51',
    'BLOC_04_I11_RECONSTRUCTION_MATRIX.json': 'e3c038dd46e3b3dd712b73df11dc36553b06c53f3bd7846f453de18a122321fc',
    'BLOC_04_I11_RUNTIME_INTEGRATION_MATRIX.json': '897339c6b8b35d711cba08dd8e96208c0abfe2bf232c909a2e06dd3d1818e888',
    'BLOC_04_I11_TRANSACTION_ATOMICITY_MATRIX.json': 'e02028cc07243ea3daaf253ca6e5a0e764e57c1152afd87c24cc26ee1417b5c8',
    'duckdb_rebuild.json': '677e23272be3055db83dd8b6a2cf8b2938b69ec3ebb5abbc6ed2f9ac70fbf5fd',
}


# ---------------------------------------------------------------------------
# Matrix construction
# ---------------------------------------------------------------------------


def _case(name: str, required: list[str], **values: Any) -> dict[str, Any]:
    row = {"case": name, **values, "required_invariants": required}
    row["result"] = "OK" if all(row.get(item) is True for item in required) else "FAIL"
    return row


def _matrix(name: str, rows: list[dict[str, Any]], **values: Any) -> dict[str, Any]:
    return {
        "checkpoint": "SENSOR-B4-I11R2",
        "matrix": name,
        "evidence_truth": (
            "Every non-counterfactual evidence predicate is mechanically observed "
            "from the real repository, the real committed immutable artifacts and "
            "the verbatim committed pytest run record; the single deliberate "
            "counterfactual predicate is explicitly synthetic and must evaluate FAIL."
        ),
        **values,
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "ok": sum(row["result"] == "OK" for row in rows),
            "fail": sum(row["result"] == "FAIL" for row in rows),
        },
    }


def build_i11r2_governance_regression_matrix() -> dict[str, Any]:
    ledger_text = LEDGER.read_text(encoding="utf-8")
    scrambled = _scrambled(ledger_text)
    runs = _run_record()
    production = _production_untouched()
    evidence = _evidence_hashes_unchanged()
    mismatched = evidence["mismatched"]
    missing = evidence["missing"]
    crlf_only = evidence["crlf_only"]
    rows = _dashboard_rows(ledger_text)
    checkpoint_rows = [row for row in rows if row[0] == "Current checkpoint"]
    governance_blob = chr(10).join("|".join(row) for row in rows).replace(" = ", "=")
    ratify = extract_checkpoint_section(ledger_text, I07R1I_RATIFY_HEADING)

    storage = runs["storage"]["counts"]
    non_storage = runs["non_storage"]["counts"]
    full = runs["full_project"]["counts"]

    i07r1i_value, i07r1i_files = _files_read_by(_new_i07r1i_verdict)
    i10r2_value, i10r2_files = _files_read_by(_new_i10r2_verdict)

    out: list[dict[str, Any]] = []

    out.append(
        _case(
            "i07r1i_historical_section_bound",
            [
                "i07r1i_matrix_file_present",
                "i07r1i_matrix_checkpoint_exact",
                "i07r1i_hold_case_exact",
                "i07r1i_hold_keys_exact",
                "i07r1i_hold_proposal_pending",
                "i07r1i_durable_resume_pending_acceptance",
                "i07r1i_recovery_scanner_false",
                "i07r1i_next_checkpoint_not_authorized",
                "i07r1i_bound_verdict_true",
            ],
            i07r1i_matrix_file_present=I07R1I_MATRIX.is_file(),
            i07r1i_matrix_checkpoint_exact=(
                json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))["checkpoint"]
                == "SENSOR-B4-I07R1I"
            ),
            i07r1i_hold_case_exact=(
                "i07_hold_chain_truthful"
                in {
                    row["case"]
                    for row in json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))[
                        "cases"
                    ]
                }
            ),
            i07r1i_hold_keys_exact=(
                tuple(
                    next(
                        row["hold_keys"]
                        for row in json.loads(
                            I07R1I_MATRIX.read_text(encoding="utf-8")
                        )["cases"]
                        if row["case"] == "i07_hold_chain_truthful"
                    )
                )
                == I07R1I_HOLD_KEYS
            ),
            i07r1i_hold_proposal_pending=(
                next(
                    row["proposal_pending"]
                    for row in json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))[
                        "cases"
                    ]
                    if row["case"] == "i07_hold_chain_truthful"
                )
                is True
            ),
            i07r1i_durable_resume_pending_acceptance=(
                next(
                    row["durable_resume_implemented"]
                    for row in json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))[
                        "cases"
                    ]
                    if row["case"] == "durable_resume_pending_acceptance"
                )
                == "PENDING_OPERATOR_ACCEPTANCE"
            ),
            i07r1i_recovery_scanner_false=(
                next(
                    row["recovery_scanner_implemented"]
                    for row in json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))[
                        "cases"
                    ]
                    if row["case"] == "durable_resume_pending_acceptance"
                )
                is False
            ),
            i07r1i_next_checkpoint_not_authorized=(
                next(
                    row["next_checkpoint_authorized"]
                    for row in json.loads(I07R1I_MATRIX.read_text(encoding="utf-8"))[
                        "cases"
                    ]
                    if row["case"] == "next_checkpoint_not_authorized"
                )
                is False
            ),
            i07r1i_bound_verdict_true=_new_i07r1i_verdict(),
        )
    )

    out.append(
        _case(
            "i07r1i_live_current_state_dependency_removed",
            [
                "i07r1i_bound_verdict_true",
                "i07r1i_binding_never_reads_the_ledger",
                "i07r1i_binding_reads_its_immutable_source",
                "old_i07r1i_binding_flips_with_dashboard",
                "old_i07r1i_binding_red_against_present_dashboard",
            ],
            i07r1i_bound_verdict_true=i07r1i_value,
            i07r1i_binding_never_reads_the_ledger=LEDGER.resolve()
            not in i07r1i_files,
            i07r1i_binding_reads_its_immutable_source=I07R1I_MATRIX.resolve()
            in i07r1i_files,
            old_i07r1i_binding_flips_with_dashboard=(
                _old_i07r1i_binding(ledger_text) != _old_i07r1i_binding(scrambled)
            ),
            old_i07r1i_binding_red_against_present_dashboard=(
                _old_i07r1i_binding(ledger_text) is False
            ),
        )
    )

    out.append(
        _case(
            "i10r2_historical_section_bound",
            [
                "i10r2_microseal_present",
                "i10r2_governance_section_exactly_one",
                "i10r2_proposed_verdicts_exact",
                "i10r2_never_self_ratified",
                "i10r2_bound_verdict_true",
            ],
            i10r2_microseal_present=I10R2_MICROSEAL.is_file(),
            i10r2_governance_section_exactly_one=(
                I10R2_MICROSEAL.read_text(encoding="utf-8").split(chr(10)).count(
                    "## Governance"
                )
                == 1
            ),
            i10r2_proposed_verdicts_exact=_new_i10r2_verdict(),
            i10r2_never_self_ratified=(
                "PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED = OPERATOR_ACCEPTED"
                not in extract_checkpoint_section(
                    I10R2_MICROSEAL.read_text(encoding="utf-8"), "## Governance"
                )
            ),
            i10r2_bound_verdict_true=_new_i10r2_verdict(),
        )
    )

    out.append(
        _case(
            "i10r2_live_current_state_dependency_removed",
            [
                "i10r2_bound_verdict_true",
                "i10r2_binding_never_reads_the_ledger",
                "i10r2_binding_reads_its_immutable_source",
                "old_i10r2_binding_flips_with_dashboard",
                "old_i10r2_binding_red_against_present_dashboard",
            ],
            i10r2_bound_verdict_true=i10r2_value,
            i10r2_binding_never_reads_the_ledger=LEDGER.resolve() not in i10r2_files,
            i10r2_binding_reads_its_immutable_source=I10R2_MICROSEAL.resolve()
            in i10r2_files,
            old_i10r2_binding_flips_with_dashboard=(
                _old_i10r2_binding(ledger_text) != _old_i10r2_binding(scrambled)
            ),
            old_i10r2_binding_red_against_present_dashboard=(
                _old_i10r2_binding(ledger_text) is False
            ),
        )
    )

    out.append(
        _case(
            "current_state_still_truthful",
            [
                "current_state_rows_two_columns",
                "current_checkpoint_row_exactly_one",
                "current_state_names_i11_chain",
                "current_state_g4_10_not_operator_accepted",
                "current_state_next_checkpoint_false",
                "current_state_i12_unauthorized",
                "current_state_research_frozen",
                "current_state_not_pinned_to_superseded_checkpoint",
                "i07r1i_ratification_still_recorded",
            ],
            current_state_rows_two_columns=all(len(row) == 2 for row in rows) and bool(rows),
            current_checkpoint_row_exactly_one=len(checkpoint_rows) == 1,
            current_state_names_i11_chain=(
                len(checkpoint_rows) == 1 and "SENSOR-B4-I11" in checkpoint_rows[0][1]
            ),
            current_state_g4_10_not_operator_accepted=(
                "G4-10_OPERATIONAL_METADATA_GATE=IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW"
                in governance_blob
                and "G4-10_OPERATIONAL_METADATA_GATE=OPERATOR_HOLD" not in governance_blob
                and "G4-10_OPERATIONAL_METADATA_GATE=PASS" not in governance_blob
            ),
            current_state_next_checkpoint_false=(
                "next_checkpoint_authorized=FALSE" in governance_blob
            ),
            current_state_i12_unauthorized=(
                "I12+ unauthorized" in governance_blob
                or "I12+ remain unauthorized" in governance_blob
            ),
            current_state_research_frozen=(
                "research frozen" in governance_blob
                or "research remains frozen" in governance_blob
            ),
            current_state_not_pinned_to_superseded_checkpoint=(
                len(checkpoint_rows) == 1
                and "SENSOR-B4-I07R1I" not in checkpoint_rows[0][1]
                and "SENSOR-B4-I10R2" not in checkpoint_rows[0][1]
                and "DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE"
                not in governance_blob
            ),
            i07r1i_ratification_still_recorded=(
                "OPERATOR_ACCEPTED" in ratify
                and "DURABLE_RESUME_IMPLEMENTED = TRUE" in ratify
                and "next_checkpoint_authorized = TRUE" in ratify
                and "SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY" in ratify
                and all(key in ratify for key in I07R1I_HOLD_KEYS)
            ),
        )
    )

    out.append(
        _case(
            "historical_evidence_unchanged",
            [
                "historical_evidence_count_is_131",
                "historical_evidence_all_present",
                "historical_evidence_zero_byte_mismatch",
                "historical_evidence_crlf_churn_is_allowlisted",
                "ledger_is_lf_only",
            ],
            historical_evidence_count_is_131=len(HISTORICAL_EVIDENCE) == 131,
            historical_evidence_all_present=not missing,
            historical_evidence_zero_byte_mismatch=not mismatched,
            historical_evidence_crlf_churn_is_allowlisted=set(crlf_only)
            <= I04_CRLF_CHURN_ALLOWLIST,
            ledger_is_lf_only=bytes((13,)) not in LEDGER.read_bytes(),
        )
    )

    out.append(
        _case(
            "production_diff_zero",
            [
                "no_production_files_changed_vs_head",
                "no_production_files_changed_vs_i11r1_head",
                "no_untracked_production_files",
                "postgres_metadata_untouched",
            ],
            no_production_files_changed_vs_head=(
                not _production_untouched()
            ),
            no_production_files_changed_vs_i11r1_head=not [
                line
                for line in _git(
                    "diff", "--name-only", I11R1_HEAD, "--", "quant-lab/src"
                ).splitlines()
                if line.strip()
            ],
            no_untracked_production_files=not [
                line
                for line in _git(
                    "ls-files", "--others", "--exclude-standard", "quant-lab/src"
                ).splitlines()
                if line.strip()
            ],
            postgres_metadata_untouched=(
                _git(
                    "diff",
                    "--name-only",
                    I11R1_HEAD,
                    "--",
                    "quant-lab/src/crypto_sensor_fabric/storage/postgres_metadata.py",
                ).strip()
                == ""
            ),
        )
    )

    out.append(
        _case(
            "storage_regression_green",
            [
                "storage_run_exit_zero",
                "storage_zero_failures",
                "storage_failures_absent",
                "storage_passed_measured",
                "storage_skips_reconcile",
            ],
            storage_run_exit_zero=runs["storage"]["exit_code"] == 0,
            storage_zero_failures=runs["storage"]["counts"].get("failed", 0) == 0,
            storage_failures_absent="failed" not in runs["storage"]["summary_line"],
            storage_passed_measured=storage.get("passed", 0) > 0,
            storage_skips_reconcile=(
                storage.get("skipped", 0)
                == 21 + 4
                and non_storage.get("skipped", 0) == 1
                and full.get("skipped", 0) == 26
            ),
        )
    )

    out.append(
        _case(
            "project_regression_green",
            [
                "full_run_exit_zero",
                "full_zero_failures",
                "non_storage_run_exit_zero",
                "non_storage_zero_failures",
                "focused_i11r2_run_exit_zero",
                "focused_i11r2_zero_failures",
                "full_totals_reconcile",
            ],
            full_run_exit_zero=runs["full_project"]["exit_code"] == 0,
            full_zero_failures=full.get("failed", 0) == 0,
            non_storage_run_exit_zero=runs["non_storage"]["exit_code"] == 0,
            non_storage_zero_failures=non_storage.get("failed", 0) == 0,
            focused_i11r2_run_exit_zero=runs["focused_i11r2"]["exit_code"] == 0,
            focused_i11r2_zero_failures=(
                runs["focused_i11r2"]["counts"].get("failed", 0) == 0
            ),
            full_totals_reconcile=(
                full.get("passed", 0) == storage.get("passed", 0) + non_storage.get("passed", 0)
                and full.get("skipped", 0)
                == storage.get("skipped", 0) + non_storage.get("skipped", 0)
            ),
        )
    )

    # The single deliberately synthetic counterfactual row: a historical
    # checkpoint test that reads the live dashboard, evaluated against the
    # present, legitimately advanced dashboard.  This is the exact shape that
    # failed, and it MUST be FAIL.
    out.append(
        _case(
            "counterfactual_historical_test_reads_live_dashboard",
            ["historical_test_reads_live_dashboard"],
            historical_test_reads_live_dashboard=(
                _old_i07r1i_binding(ledger_text) and _old_i10r2_binding(ledger_text)
            ),
        )
    )

    return _matrix(
        "I11R2_GOVERNANCE_REGRESSION",
        out,
        historical_sources={
            "i07r1i_proposal_truth": I07R1I_MATRIX.name,
            "i10r2_governance_truth": I10R2_MICROSEAL.name + " :: ## Governance",
            "i07r1i_ratification_truth": LEDGER.name + " :: " + I07R1I_RATIFY_HEADING,
        },
        measured_runs={
            name: {
                "exit_code": data["exit_code"],
                "summary_line": data["summary_line"],
            }
            for name, data in sorted(runs.items())
        },
        production_changed_files=production,
        postgres_rerun="BLOCKED_ENVIRONMENT",
    )


I11R2_BUILDERS = {
    "BLOC_04_I11R2_GOVERNANCE_REGRESSION_MATRIX.json": (
        build_i11r2_governance_regression_matrix
    ),
}


def _stable(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + chr(10)).encode("utf-8")


def test_i11r2_evidence_is_measured_and_committed() -> None:
    update = os.getenv("UPDATE_I11R2_EVIDENCE") == "1"
    for name, builder in I11R2_BUILDERS.items():
        payload = builder()
        for row in payload.get("rows", []):
            required = row["required_invariants"]
            assert row["result"] == (
                "OK" if all(row.get(item) is True for item in required) else "FAIL"
            )
            for item in required:
                assert isinstance(row.get(item), bool), (name, row["case"], item)
            if row["case"].startswith("counterfactual_"):
                assert row["result"] == "FAIL"
            else:
                assert row["result"] == "OK", (name, row["case"])
        expected = _stable(payload)
        committed = EVIDENCE_DIR / name
        if update:
            committed.write_bytes(expected)
        else:
            assert committed.exists(), f"missing committed I11R2 artifact: {name}"
            assert committed.read_bytes() == expected, f"I11R2 artifact drifted: {name}"


def test_i11r2_does_not_rewrite_historical_evidence() -> None:
    """The 131 pre-existing evidence artifacts are never regenerated."""
    evidence = _evidence_hashes_unchanged()
    assert not evidence["mismatched"], evidence["mismatched"]
    assert not evidence["missing"], evidence["missing"]
    # The documented I04 Path.write_text line-ending churn is recorded, and is
    # only ever tolerated for the exact, closed set of artifacts named above.
    assert set(evidence["crlf_only"]) <= I04_CRLF_CHURN_ALLOWLIST, evidence["crlf_only"]
