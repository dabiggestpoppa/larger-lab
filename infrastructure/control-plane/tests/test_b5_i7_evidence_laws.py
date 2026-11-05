"""OCE B5-I7 — executable enforcement of evidence laws EL01–EL15.

Frozen planned nodes executed VERBATIM here (construction plan §5), exactly
fifteen, one per law:

``TestEL01`` … ``TestEL15`` (see the class docstrings for the exact strings).

Design law: every check is written as a function that takes the parsed evidence
and RAISES when the law is violated, so it can be executed on the real evidence
(must pass) and on a falsified copy of it (must fail). A law that cannot fail is
not enforcement — each node below therefore runs its checker twice, once green
on the real artifact and once red on a deliberately falsified one.

The evidence artifacts are the ones the frozen contract §5 authorizes:
``OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md``,
``OCE_B5_I7_REUSE_INVENTORY_v1.0.md`` and
``OCE_B5_I7_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json`` (plus the machine-readable
mutation battery output it cites).
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
DOCS = REPO_ROOT / "docs" / "oce-golden-system"

RECORD = DOCS / "OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md"
REUSE = DOCS / "OCE_B5_I7_REUSE_INVENTORY_v1.0.md"
ADDENDUM = DOCS / "OCE_B5_I7_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json"
MUTATION = DOCS / "OCE_B5_I7_MUTATION_RESULTS_v1.0.json"
REGISTRY = DOCS / "OCE_B5_I7_REQUIREMENT_TEST_REGISTRY_v1.0.json"
LEDGER = DOCS / "OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "b1-i1r-validation.yml"

HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
#: Language that may never appear while any gate is unexecuted (EL15).
FORBIDDEN_ALL_GREEN = (
    "all gates passed",
    "all gates are green",
    "every gate passed",
    "fully green",
)


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=False
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(bytes((13, 10)), bytes((10,)))).hexdigest()


def addendum() -> dict:
    return json.loads(ADDENDUM.read_text(encoding="utf-8"))


def mutation() -> dict:
    return json.loads(MUTATION.read_text(encoding="utf-8"))


def record_text() -> str:
    return RECORD.read_text(encoding="utf-8")


# ── law checkers (each RAISES on violation) ─────────────────────────────────

def check_el01(doc: dict, text: str) -> None:
    """Every commit SHA in the evidence must be a real object (no predictions)."""
    for sha in set(HEX40.findall(text)) | set(HEX40.findall(json.dumps(doc))):
        assert _git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0 or \
            _git("cat-file", "-e", sha).returncode == 0, f"unresolvable sha cited: {sha}"
        assert _git("cat-file", "-e", sha).returncode == 0, f"sha does not exist: {sha}"
    for bad in ("will be ", "predicted sha", "expected sha", "placeholder sha"):
        lowered = (text + json.dumps(doc)).lower()
        assert bad not in lowered, f"predictive SHA language present: {bad!r}"


def check_el02(doc: dict) -> None:
    """No run/check/artifact id may be recorded before it exists."""
    ci = doc.get("ci", {})
    assert ci.get("status") in {"NOT_EXECUTED", "OBSERVED"}, ci.get("status")
    if ci.get("status") == "NOT_EXECUTED":
        for key in ("run_id", "check_run_id", "artifact_id", "suite_id"):
            assert not ci.get(key), f"{key} recorded while CI is NOT_EXECUTED"
        assert ci.get("observed_at_head") in (None, ""), "head recorded before a run"
    else:
        for key in ("run_id", "check_run_id", "artifact_id"):
            assert ci.get(key), f"{key} missing for an OBSERVED CI row"
        assert ci.get("parsed_from"), "no raw artifact cited for CI ids"


def check_el03(doc: dict) -> None:
    """Raw evidence blocks must hash to their recorded digest (no typed-in data)."""
    blocks = doc.get("raw_evidence", [])
    assert blocks, "no raw evidence embedded"
    for block in blocks:
        text = block["text"]
        assert isinstance(text, str) and text.strip(), "empty raw block"
        recomputed = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert recomputed == block["sha256"], (
            f"raw block {block['name']} digest {recomputed} != recorded {block['sha256']}"
        )
        assert block.get("command"), "raw block without its producing command"


def check_el04(doc: dict) -> None:
    """Planned totals are EXPECTED; only parsed runs may be OBSERVED."""
    planned = doc["planned_test_nodes"]
    assert planned["label"] == "EXPECTED", planned["label"]
    assert planned["expected"] == 27 and planned["floor"] == 27
    assert planned["split"] == {
        "test_b5_i7_governed_change.py": 12,
        "test_b5_i7_evidence_laws.py": 15,
    }
    for row in doc["observed"]:
        assert row["label"] in {"OBSERVED", "NOT_OBSERVED"}, row["label"]
        if row["label"] == "OBSERVED":
            assert row.get("parsed_from"), f"{row['name']} claims OBSERVED without a source"


def check_el05(doc: dict) -> None:
    """Every OBSERVED total must be re-derivable from its embedded raw output."""
    raw = {block["name"]: block["text"] for block in doc["raw_evidence"]}
    for row in doc["observed"]:
        if row["label"] != "OBSERVED":
            continue
        source = raw[row["parsed_from"]]
        pattern = row["extract"]
        found = [int(value) for value in re.findall(pattern, source)]
        assert found, f"{row['name']}: pattern {pattern!r} not found in raw output"
        assert row["value"] in found, (
            f"{row['name']}: recorded {row['value']} but raw output yields {found}"
        )


def check_el06(doc: dict) -> None:
    """A green claim needs a SHA and a tree binding that actually exist."""
    identities = doc["evidence_identities"]
    assert identities, "no evidence identity recorded"
    for name, row in identities.items():
        assert HEX40.fullmatch(row["head_sha"]), f"{name}: head_sha malformed"
        assert _git("cat-file", "-e", f"{row['head_sha']}^{{commit}}").returncode == 0, name
        actual = _git("rev-parse", f"{row['head_sha']}^{{tree}}").stdout.strip()
        assert actual == row["tree_sha"], f"{name}: tree {actual} != claimed {row['tree_sha']}"
        assert row["claim"] in {"OBSERVED", "NOT_EXECUTED"}, row["claim"]


def check_el07(doc: dict) -> None:
    """New-test-only execution cannot prove regression absence."""
    adjacent = doc["adjacent_population"]
    assert len(adjacent["files"]) == 9, adjacent["files"]
    ends = {run["end"] for run in adjacent["runs"]}
    assert ends == {"base", "head"}, f"both ends required, got {ends}"
    for run in adjacent["runs"]:
        assert run["parsed_from"], f"{run['end']} run without raw source"
        assert run["nodes"] > 0


def check_el08(doc: dict) -> None:
    """The common regression population must be nonzero and at/above the floor."""
    floor = doc["planned_test_nodes"]["floor"]
    for run in doc["adjacent_population"]["runs"]:
        assert run["nodes"] > 0, "regression population is zero"
        assert run["nodes"] >= floor, f"{run['end']} population {run['nodes']} < floor {floor}"


# ── EL09 X1: manifest verification modes ────────────────────────────────────
#
# The historical B5-I7 manifest attests the COMPLETE bytes of thirteen files at
# the B5-I7 evidence head. Twelve of them are immutable: any later edit must be
# refused by whole-file equality. The thirteenth is the Book 5 progress ledger,
# which is APPEND-ONLY by law — later authorized stages must preserve the B5-I7
# bytes exactly and add their own evidence after them. Permanent whole-file
# equality therefore contradicts the ledger law it was meant to protect; it is
# corrected here, without rewriting the historical row
# (see OCE_B5_I7_EL09_APPEND_ONLY_LEDGER_CORRECTION_v1.0.md).
#
# The durable invariant for that one path is
#
#     current_bytes[:size_bytes] == historical_bytes      (sha256 83a40ac7…)
#
# Exact path match — never a suffix, substring or extension heuristic. Suffix
# bytes appended by a later stage are that stage's own evidence and are never
# claimed as covered by the historical row.
LEDGER_ROW_PATH = "docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md"
VERIFIER_ROW_PATH = "infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py"
SUPERSEDING = DOCS / "OCE_B5_I7_EL09_X1_SUPERSEDING_MANIFEST_v1.0.json"

WHOLE_FILE = "whole_file"
APPEND_ONLY_PREFIX = "append_only_prefix"
VERIFICATION_MODES = frozenset({WHOLE_FILE, APPEND_ONLY_PREFIX})
DIGEST64 = re.compile(r"[0-9a-f]{64}")


def superseding_manifest() -> dict:
    return json.loads(SUPERSEDING.read_text(encoding="utf-8"))


def _normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(bytes((13, 10)), bytes((10,)))


def governed_mode(row: dict) -> str:
    """Classify a row: only the exact Book 5 ledger path may be prefix-bound."""
    path = row.get("path")
    assert isinstance(path, str) and path, "manifest row without a path"
    assert "\\" not in path and not path.startswith("/"), f"{path}: not a repository-relative path"
    governed = APPEND_ONLY_PREFIX if path == LEDGER_ROW_PATH else WHOLE_FILE
    declared = row.get("verification")
    if declared is not None:
        assert declared in VERIFICATION_MODES, f"{path}: unknown verification mode {declared!r}"
        assert declared == governed, (
            f"{path}: declared verification {declared!r} contradicts the governed mode {governed!r}"
        )
    return governed


def verify_manifest_row(row: dict, root: Path = REPO_ROOT) -> None:
    """Recompute one row from bytes under its governed verification mode."""
    path = row["path"]
    mode = governed_mode(row)
    digest, size = row.get("sha256"), row.get("size_bytes")
    assert isinstance(digest, str) and DIGEST64.fullmatch(digest), (
        f"{path}: digest {digest!r} is not 64 lowercase hex"
    )
    assert isinstance(size, int) and not isinstance(size, bool) and size >= 0, (
        f"{path}: size {size!r} is not a non-negative integer"
    )
    target = root / path
    assert target.is_file(), f"missing artifact {path}"
    data = _normalized_bytes(target)
    if mode == WHOLE_FILE:
        assert len(data) == size, f"{path}: size {len(data)} != recorded {size}"
        assert hashlib.sha256(data).hexdigest() == digest, f"{path}: hash mismatch"
        return
    assert len(data) >= size, (
        f"{path}: {len(data)} bytes is shorter than the historical prefix {size}"
    )
    assert hashlib.sha256(data[:size]).hexdigest() == digest, f"{path}: immutable prefix hash mismatch"


def check_el09(doc: dict, *, superseding: dict | None = None, root: Path = REPO_ROOT) -> None:
    """Manifest rows are recomputed from bytes; the Book 5 ledger is prefix-bound.

    The historical manifest is never rewritten. Twelve rows must still equal
    their historical bytes exactly; the ledger row must still begin with its
    historical bytes. The verifier itself is revisioned by this correction, so
    its current bytes are attested by the superseding manifest — which is in
    turn proven to be an exact copy of the historical manifest for every other
    row, so the correction cannot quietly weaken anything.
    """
    frozen = doc["manifest"]
    assert frozen["gated"], "manifest has no gated rows"
    frozen_rows = frozen["artifacts"]
    frozen_paths = [row["path"] for row in frozen_rows]
    assert len(frozen_paths) == len(set(frozen_paths)), "duplicate path in the historical manifest"
    assert frozen_paths.count(LEDGER_ROW_PATH) == 1, (
        "historical manifest must carry exactly one Book 5 ledger row"
    )

    revised = superseding if superseding is not None else superseding_manifest()
    revised_rows = revised["artifacts"]
    revised_paths = [row["path"] for row in revised_rows]
    assert len(revised_paths) == len(set(revised_paths)), "duplicate path in the superseding manifest"
    assert set(revised_paths) == set(frozen_paths), "superseding manifest changes the row population"
    assert revised_paths.count(LEDGER_ROW_PATH) == 1, (
        "superseding manifest must carry exactly one Book 5 ledger row"
    )

    for row in revised_rows:
        governed_mode(row)

    attested = {row["path"]: row for row in revised_rows}
    for row in frozen_rows:
        if row["path"] == VERIFIER_ROW_PATH:
            continue
        assert attested[row["path"]] == row, f"{row['path']}: historical manifest row was rewritten"

    for row in revised_rows:
        verify_manifest_row(row, root)


def check_el10(doc_mut: dict) -> None:
    """Mutation claims need real discrimination AND pristine restoration."""
    assert doc_mut["mutations"] >= doc_mut["floor"] >= 12, doc_mut["mutations"]
    assert doc_mut["verdict"] == "PASS", doc_mut["verdict"]
    for row in doc_mut["rows"]:
        assert row["result"] == "RED", f"{row['mutation_id']} not discriminated"
        assert row["observed_node"], f"{row['mutation_id']} has no observed failing node"
        assert row["pytest_rc"] not in (0, None), f"{row['mutation_id']} rc={row['pytest_rc']}"
        assert row["restoration_ok"] is True, f"{row['mutation_id']} restoration unproven"
        assert row["restored_sha256"] == row["pristine_sha256"], row["mutation_id"]
    assert doc_mut["restoration_verified"] is True


def check_el11(doc_mut: dict) -> None:
    """A cleanup claim needs machine-readable residual state."""
    assert doc_mut["worktree_clean_after"] is True, doc_mut["worktree_porcelain_after"]
    assert doc_mut["worktree_porcelain_after"] == "", "residual worktree state remains"
    # The claim is restoration of the MUTATED tree, so residual state is
    # measured over the production tree the battery touches; untracked
    # evidence files authored by this rung are not mutation residue.
    residual = _git("status", "--porcelain", "--", "infrastructure/console").stdout.strip()
    assert residual == "", f"residual state in the mutated tree: {residual}"


def check_el12(text: str) -> None:
    """Historical process defects stay visible after the technical repair."""
    for defect in ("D1", "D2", "D3", "D4", "D5"):
        assert re.search(rf"^\|\s*{defect}\s*\|", text, re.MULTILINE), f"defect {defect} removed"
    assert "Repaired" in text
    assert "removed from the record" not in text.lower()


def check_el13(text: str) -> None:
    """A same-agent audit is never labelled organisationally independent."""
    assert "same-agent" in text.lower()
    assert "not organizationally independent" in text.lower()
    for phrase in ("organizationally independent review was performed",
                   "independent review performed",
                   "is organizationally independent"):
        assert phrase not in text.lower(), f"false independence claim: {phrase!r}"


def check_el14(text: str) -> None:
    """Ratification cannot precede every mandatory gate."""
    assert "MERGE_AUTHORIZED=false" in text
    assert "RATIFIED_B5_I7" not in text
    assert "ratification complete" not in text.lower()


def check_el15(text: str, doc: dict) -> None:
    """No 'all gates passed' language while any gate is unexecuted."""
    pending = [gate for gate in doc["gates"] if gate["status"] != "OBSERVED"]
    lowered = text.lower()
    for phrase in FORBIDDEN_ALL_GREEN:
        assert phrase not in lowered, f"forbidden all-green language {phrase!r}"
    if pending:
        assert "NOT_EXECUTED" in text, "pending gates are not disclosed as NOT_EXECUTED"
        assert "not all exit gates are executed" in lowered, "omission of the pending set"


# ── the fifteen frozen nodes ────────────────────────────────────────────────

class TestEL01:
    def test_no_unverified_sha_recorded_as_fact(self):
        doc, text = addendum(), record_text()
        check_el01(doc, text)
        falsified = text + "\nsee 0123456789abcdef0123456789abcdef01234567\n"
        with pytest.raises(AssertionError):
            check_el01(doc, falsified)


class TestEL02:
    def test_no_run_or_artifact_id_recorded_before_existence(self):
        doc = addendum()
        check_el02(doc)
        bad = copy.deepcopy(doc)
        # The law forbids an id recorded BEFORE a run exists, so the
        # falsified evidence must claim the pre-existence shape.
        bad["ci"] = {"status": "NOT_EXECUTED", "observed_at_head": "0" * 40,
                     "run_id": "41345551281", "parsed_from": None}
        with pytest.raises(AssertionError):
            check_el02(bad)


class TestEL03:
    def test_manually_authored_json_not_presented_as_execution_evidence(self):
        doc = addendum()
        check_el03(doc)
        bad = copy.deepcopy(doc)
        bad["raw_evidence"][0]["text"] += "\nfabricated line\n"
        with pytest.raises(AssertionError):
            check_el03(bad)


class TestEL04:
    def test_planned_totals_labeled_expected_not_observed(self):
        doc = addendum()
        check_el04(doc)
        bad = copy.deepcopy(doc)
        bad["planned_test_nodes"]["label"] = "OBSERVED"
        with pytest.raises(AssertionError):
            check_el04(bad)


class TestEL05:
    def test_observed_totals_bound_to_parsed_raw_artifacts(self):
        doc = addendum()
        check_el05(doc)
        bad = copy.deepcopy(doc)
        for row in bad["observed"]:
            if row["label"] == "OBSERVED":
                row["value"] = row["value"] + 7
                break
        with pytest.raises(AssertionError):
            check_el05(bad)


class TestEL06:
    def test_green_claims_carry_sha_and_tree_binding(self):
        doc = addendum()
        check_el06(doc)
        bad = copy.deepcopy(doc)
        first = next(iter(bad["evidence_identities"]))
        bad["evidence_identities"][first]["tree_sha"] = "0" * 40
        with pytest.raises(AssertionError):
            check_el06(bad)


class TestEL07:
    def test_regression_absence_never_proven_by_new_tests_only(self):
        doc = addendum()
        check_el07(doc)
        bad = copy.deepcopy(doc)
        bad["adjacent_population"]["runs"] = [
            run for run in bad["adjacent_population"]["runs"] if run["end"] != "base"
        ]
        with pytest.raises(AssertionError):
            check_el07(bad)


class TestEL08:
    def test_common_regression_population_nonzero_and_at_floor(self):
        doc = addendum()
        check_el08(doc)
        bad = copy.deepcopy(doc)
        bad["adjacent_population"]["runs"][0]["nodes"] = 0
        with pytest.raises(AssertionError):
            check_el08(bad)


class TestEL09:
    def test_manifest_rows_recomputed_hash_and_size(self, tmp_path):
        """Law plus discriminating controls for the prefix invariant (X1).

        Every negative control is refused BY THE LAW — the assertion message is
        checked — never by a syntax, import or configuration error. Controls
        live inside this node so the frozen inventory stays at twenty-seven.
        """
        doc, revised = addendum(), superseding_manifest()
        check_el09(doc)  # positive: the real repository
        bad = copy.deepcopy(doc)
        bad["manifest"]["artifacts"][0]["sha256"] = "f" * 64
        with pytest.raises(AssertionError):
            check_el09(bad)  # the frozen falsification, unchanged

        frozen_ledger = next(r for r in doc["manifest"]["artifacts"] if r["path"] == LEDGER_ROW_PATH)
        historical_size = frozen_ledger["size_bytes"]
        historical = _normalized_bytes(LEDGER)[:historical_size]
        assert hashlib.sha256(historical).hexdigest() == frozen_ledger["sha256"]
        assert revised["artifacts"][0] == doc["manifest"]["artifacts"][0]

        immutable_bytes = b"# immutable B5-I7 evidence\n"
        immutable_row = {
            "path": "docs/immutable.md",
            "sha256": hashlib.sha256(immutable_bytes).hexdigest(),
            "size_bytes": len(immutable_bytes),
        }
        ledger_row = dict(frozen_ledger)

        def materialize(name, ledger_bytes, *, rows, immutable=immutable_bytes, extra=None):
            root = tmp_path / name
            target = root / LEDGER_ROW_PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(ledger_bytes)
            other = root / "docs" / "immutable.md"
            other.parent.mkdir(parents=True, exist_ok=True)
            other.write_bytes(immutable)
            for relative, payload in (extra or {}).items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            return (
                {"manifest": {"gated": True, "artifacts": list(rows)}},
                {"artifacts": list(rows)},
                root,
            )

        def accepts(name, ledger_bytes, *, rows, **kwargs):
            frozen_doc, revised_doc, root = materialize(name, ledger_bytes, rows=rows, **kwargs)
            check_el09(frozen_doc, superseding=revised_doc, root=root)

        def refuses(name, ledger_bytes, *, rows, fragment, **kwargs):
            frozen_doc, revised_doc, root = materialize(name, ledger_bytes, rows=rows, **kwargs)
            with pytest.raises(AssertionError) as raised:
                check_el09(frozen_doc, superseding=revised_doc, root=root)
            assert fragment in str(raised.value), f"{name}: {raised.value}"

        # ── positives ──────────────────────────────────────────────────────
        accepts("historical", historical, rows=[ledger_row, immutable_row])
        accepts("one-suffix", historical + b"\nstage suffix\n", rows=[ledger_row, immutable_row])
        accepts("multi-suffix", historical + b"\nfirst\n" + b"second\n", rows=[ledger_row, immutable_row])
        accepts("immutable-exact", historical, rows=[ledger_row, immutable_row])

        # ── negatives: prefix mutation ─────────────────────────────────────
        flipped = bytearray(historical)
        flipped[historical_size // 2] ^= 0x20
        refuses(
            "prefix-byte-same-size", bytes(flipped), rows=[ledger_row, immutable_row],
            fragment="immutable prefix hash mismatch",
        )
        newline_at = historical.index(b"\n")
        refuses(
            "prefix-newline",
            historical[:newline_at] + b"\r" + historical[newline_at + 1:],
            rows=[ledger_row, immutable_row], fragment="immutable prefix hash mismatch",
        )
        refuses(
            "prefix-insert", historical[:100] + b"INSERTED" + historical[100:],
            rows=[ledger_row, immutable_row], fragment="immutable prefix hash mismatch",
        )
        refuses(
            "prefix-delete", historical[:100] + historical[101:],
            rows=[ledger_row, immutable_row], fragment="shorter than the historical prefix",
        )
        refuses(
            "truncate", historical[:-10], rows=[ledger_row, immutable_row],
            fragment="shorter than the historical prefix",
        )
        refuses(
            "reorder", historical[::-1], rows=[ledger_row, immutable_row],
            fragment="immutable prefix hash mismatch",
        )

        # ── negatives: row integrity ───────────────────────────────────────
        refuses(
            "wrong-digest", historical,
            rows=[dict(ledger_row, sha256="f" * 64), immutable_row],
            fragment="immutable prefix hash mismatch",
        )
        refuses(
            "wrong-size", historical,
            rows=[dict(ledger_row, size_bytes=historical_size + 1), immutable_row],
            fragment="shorter than the historical prefix",
        )
        refuses(
            "malformed-digest", historical,
            rows=[dict(ledger_row, sha256="F" * 64), immutable_row],
            fragment="not 64 lowercase hex",
        )
        refuses(
            "unknown-mode", historical,
            rows=[dict(ledger_row, verification="prefix_v2"), immutable_row],
            fragment="unknown verification mode",
        )

        # ── negatives: classification and population ───────────────────────
        refuses(
            "missing-ledger-row", historical, rows=[immutable_row],
            fragment="exactly one Book 5 ledger row",
        )
        refuses(
            "duplicate-ledger-row", historical,
            rows=[ledger_row, dict(ledger_row), immutable_row], fragment="duplicate path",
        )
        refuses(
            "false-append-only", historical,
            rows=[ledger_row, dict(immutable_row, verification=APPEND_ONLY_PREFIX)],
            fragment="contradicts the governed mode",
        )
        refuses(
            "append-to-immutable", historical,
            rows=[ledger_row, immutable_row],
            immutable=immutable_bytes + b"suffix\n", fragment="docs/immutable.md: size",
        )
        copy_row = {
            "path": "docs/ledger-copy.md",
            "sha256": ledger_row["sha256"],
            "size_bytes": historical_size,
        }
        refuses(
            "different-path-same-bytes", historical,
            rows=[ledger_row, immutable_row, copy_row], fragment="docs/ledger-copy.md: size",
            extra={"docs/ledger-copy.md": historical + b"\nsuffix\n"},
        )


class TestEL10:
    def test_mutation_claims_require_discrimination_and_restoration(self):
        check_el10(mutation())
        bad = mutation()
        bad["rows"][0]["result"] = "NOT_DISCRIMINATED"
        with pytest.raises(AssertionError):
            check_el10(bad)
        bad2 = mutation()
        bad2["rows"][0]["restored_sha256"] = "0" * 64
        with pytest.raises(AssertionError):
            check_el10(bad2)


class TestEL11:
    def test_cleanup_claims_require_machine_readable_residual_state(self):
        check_el11(mutation())
        bad = mutation()
        bad["worktree_porcelain_after"] = " M infra/console/src/oce_console/panel.py"
        bad["worktree_clean_after"] = False
        with pytest.raises(AssertionError):
            check_el11(bad)


class TestEL12:
    def test_historical_process_defects_remain_visible(self):
        text = record_text()
        check_el12(text)
        with pytest.raises(AssertionError):
            check_el12(re.sub(r"^\|\s*D2\s*\|.*$", "", text, count=1, flags=re.MULTILINE))


class TestEL13:
    def test_same_agent_audit_not_labeled_independent(self):
        text = record_text()
        check_el13(text)
        with pytest.raises(AssertionError):
            check_el13(text + "\nThis review is organizationally independent.\n")


class TestEL14:
    def test_no_ratification_before_all_mandatory_gates(self):
        text = record_text()
        check_el14(text)
        with pytest.raises(AssertionError):
            check_el14(text + "\nRATIFIED_B5_I7\n")


class TestEL15:
    def test_no_all_gates_passed_language_while_any_gate_pending(self):
        doc, text = addendum(), record_text()
        check_el15(text, doc)
        with pytest.raises(AssertionError):
            check_el15(text + "\nAll gates passed.\n", doc)
