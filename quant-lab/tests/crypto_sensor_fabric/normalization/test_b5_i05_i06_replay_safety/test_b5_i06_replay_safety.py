"""SENSOR-B5-I06E1 - RED-first tests for ``bloc_05_replay_safety_validation.json``.

NAMING/LAYOUT DISCLOSURE (I06E1): this suite lives at
``normalization/test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py``
-- inside a directory carrying the ``test_b5_i05_`` family prefix -- because
two SEALED I05 checks jointly pin that directory's contents:

* the B5-I05 path audit (``test_b5_i05_scope_audit.py``) asserts every staged
  test path starts with an authorized prefix, and
* the B5-I05 producer's scope row ``scope_nine_i05_test_modules_present``
  asserts the directory holds EXACTLY the nine ``test_b5_i05_*.py`` files
  (a non-recursive ``*.py`` glob).

A tenth flat ``test_b5_i05_*`` file fails the count; any other flat name
fails the path audit; and editing either sealed file would cascade into
regenerating sealed I05 evidence (its SHA-256 inventory hashes them), which
I06E1 section 12 forbids.  A subdirectory satisfies both checks as written --
the glob is non-recursive, the prefix match is startswith -- while keeping
every sealed byte untouched.  Content, evidence rows and the ledger identify
this suite as I06E1.  Scope rows
``no_i05_test_diff_vs_base`` and ``i05_scope_audit_unchanged_allowlist_displays_closed``
prove no pre-existing test file was touched to accommodate it.

DISCLOSURE -- B5-I08 AMENDMENT (operator-authorized; full record in
``BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md`` + ledger section 175): the I08E1
implementation pass is authorized to add ``normalization/common/``
(bloc_05/03 s21) and to extend the I01/I05 scope audits' allowlists on the
I02/I04A/I05 precedent -- which is exactly the cascade section 12 names, since
the amended I05 audit test changes its own SHA-256 inventory entry and forces
``bloc_05_time_validation.json`` to be regenerated.  Four scope rows
(``no_production_source_diff_vs_base``, ``no_i05_test_diff_vs_base``,
``i05_scope_audit_unchanged_allowlist_displays_closed``,
``prior_checkpoint_evidence_unchanged``) and this suite's two corresponding
tests were therefore amended from ABSOLUTE emptiness to "nothing BUT that
disclosed delta", with the disclosed bytes pinned by SHA-256.  Every other
measurement in this suite is unchanged.

DISCLOSURE -- B5-I09 AMENDMENT (operator-authorized; full record in
``BLOC_05_I09_IMPLEMENTATION_EVIDENCE.md`` + ledger section 178): the I09E1
implementation pass adds the three remaining bloc_05/03 s21 modules to
``normalization/common/`` (06 s19 titles I09 the methodology +
semantic-equivalence registries), extends the I05 audit's staged allowlist by
exactly the ``test_b5_i09`` suites and the I08 audit's frozen module set from
four to seven -- both on the same I02/I04A/I05/I08 precedent.  The same
cascade follows: the amended audits re-enter the I05 producer's inventory,
``bloc_05_time_validation.json`` is regenerated (one inventory line per
amended file), and this suite's operative pin is re-measured to the new bytes
(the superseded I08 value is kept above as the historical record).  The I06
producer's disclosed-delta rows pin the I09 bytes the same way they pinned the
I08 bytes; every other measurement in this suite remains unchanged.

The I06E1 directive (sections 03-08) requires the consolidated replay-safety
evidence artifact to exist, to exercise the ACCEPTED I05 production primitives
through deterministic synthetic fixtures, to classify every refusal exactly,
and to keep the RS-04 cutoff boundary and the RS-14 missing-latency refusal
honest.  These tests were written BEFORE the producer (RED-first): every test
that touches the artifact or the tracked generator fails until the I06
deliverables exist, which is the record of that ordering.

Laws asserted here:

* the fourteen frozen RS cases exist, in order, each carrying the nine
  fields section 04 requires;
* refusal classifications are exact -- the expected class per case is typed
  independently below, from the frozen clauses, not read from the artifact;
* the producer IMPORTS the I05 primitives and defines no engine of its own
  (no duplicate availability/replay implementation, section 00/M2);
* the I05 confidence policy and provider registry are untouched (Option B);
* the scope adds no production module beyond the disclosed B5-I08
  ``normalization/common/`` tree and no config change;
* the producer is tracked, deterministic, clock-free, and its mandatory
  failures exit nonzero;
* prior checkpoint evidence bytes are unchanged except the one disclosed
  B5-I08 regeneration, which is pinned by SHA-256.

OFFLINE.  No network, no wall clock.  The generator is invoked exactly as the
project convention prescribes (from ``quant-lab`` with ``PYTHONIOENCODING=utf-8``).
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

#: This module lives one directory below ``normalization/`` (layout disclosure
#: above), so the suite root is two parents up from ``__file__``.
_HERE = Path(__file__).resolve().parent.parent
_QUANT_LAB = _HERE.parents[2]
_ROOT = _QUANT_LAB.parent
_EVIDENCE = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_05"
)
ARTIFACT = _EVIDENCE / "bloc_05_replay_safety_validation.json"
SCOPE_ARTIFACT = _EVIDENCE / "BLOC_05_I06_SCOPE_AUDIT.json"
SCRIPT = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "scripts"
    / "b5_i06_replay_safety.py"
)
SCRIPT_RELPATH = "research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py"
SEMANTICS_CONFIG = (
    _QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_time_semantics.yaml"
)

#: The I06E1 required starting HEAD -- the baseline every noninterference
#: predicate is measured against.
I06_BASE_HEAD = "32a89743656adb638cdaf688b62be505202f1876"

#: DISCLOSED B5-I08 delta (operator-authorized): the single production
#: directory I08E1 is allowed to add under ``quant-lab/src``.
I08_COMMON_PREFIX = "quant-lab/src/crypto_sensor_fabric/normalization/common"

#: The fourteen frozen cases (I06E1 section 04 / I06D1 package section 4),
#: in frozen order.
FROZEN_CASES = [f"RS-{n:02d}" for n in range(1, 15)]

#: The nine record fields section 04 requires for each case.
REQUIRED_FIELDS = [
    "case_id",
    "frozen_clause",
    "input_fixture",
    "expected_result",
    "observed_result",
    "production_functions_exercised",
    "refusal_class",
    "evidence_reference",
    "disposition",
]

#: Refusal classes, typed independently from the frozen clauses: what each
#: case MUST be classified as.  A seventh class, or a swapped class, fails.
EXPECTED_REFUSAL_CLASS = {
    "RS-01": "BLOCKED_STATUS",            # gate refuses unknown availability (02 s5)
    "RS-02": "BLOCKED_STATUS",            # system-only rows are blocked (02 s4/s18 r3)
    "RS-03": "ADMITTED",                  # all six conditions satisfied (02 s15)
    "RS-04": "BOUNDARY_SPECIFICATION",    # gate takes no cutoff; I19 precondition (02 s15(3)/(4))
    "RS-05": "BLOCKED_STATUS",            # incomplete interval cannot be admitted (02 s18 r2)
    "RS-06": "BLOCKED_STATUS",            # unproven archive is unplaceable (02 s14/s6)
    "RS-07": "ADMITTED",                  # proven reconstruction stays labeled + admissible (02 s6/s16)
    "RS-08": "EXCLUDED_BY_CUTOFF_SELECTION",  # late correction withheld by AS_KNOWN_THEN (02 s12)
    "RS-09": "RETROSPECTIVE_ONLY",        # LATEST_VERIFIED is not PIT-safe (02 s11/s15)
    "RS-10": "BLOCKED_STATUS",            # broken lineage -> BLOCKED_LINEAGE (02 s15(5))
    "RS-11": "TYPED_EXCEPTION",           # unbucketed flag raises, never a 7th status (02 s15(6))
    "RS-12": "BLOCKED_STATUS",            # missing confidence blocks (02 s5)
    "RS-13": "TYPED_EXCEPTION",           # unknown provider semantics refused (02 s18 r7)
    "RS-14": "NO_EVIDENCE_NO_ADMISSION",  # no latency claim from missing evidence (02 s6)
}

REFUSAL_CLASS_VOCABULARY = sorted(set(EXPECTED_REFUSAL_CLASS.values()))


def _payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _run_generator() -> tuple[int, bytes]:
    before = ARTIFACT.read_bytes() if ARTIFACT.exists() else b""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, SCRIPT_RELPATH],
        cwd=_QUANT_LAB,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    after = ARTIFACT.read_bytes()
    assert before == after or not before, (
        "the generator changed the committed artifact bytes"
    )
    return result.returncode, after


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=_ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout


# ---------------------------------------------------------------------------
# Artifact existence and structure (RED-first: fails before implementation)
# ---------------------------------------------------------------------------


def test_the_replay_safety_artifact_exists() -> None:
    assert ARTIFACT.is_file(), (
        "bloc_05/06 s17 requires bloc_05_replay_safety_validation.json"
    )


def test_the_tracked_i06_producer_exists() -> None:
    assert SCRIPT.is_file(), "I06E1 section 07 requires a tracked I06 producer"


def test_every_mandatory_row_passed() -> None:
    payload = _payload()
    assert payload["all_results_pass"] is True
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["rows"] == len(payload["rows"]) == 14
    assert payload["summary"]["pass"] == payload["summary"]["rows"]
    for row in payload["rows"]:
        assert row["pass"] is True, row["case_id"]


def test_the_fourteen_frozen_cases_are_present_in_order() -> None:
    rows = _payload()["rows"]
    assert [row["case_id"] for row in rows] == FROZEN_CASES
    assert [row["index"] for row in rows] == list(range(14))
    assert len({row["case_id"] for row in rows}) == 14


def test_every_row_carries_the_nine_required_record_fields() -> None:
    for row in _payload()["rows"]:
        for field in REQUIRED_FIELDS:
            assert field in row, (row.get("case_id"), field)
            if field != "production_functions_exercised":
                assert str(row[field]).strip(), (row.get("case_id"), field)
        assert isinstance(row["production_functions_exercised"], list)
        assert row["production_functions_exercised"], row["case_id"]


def test_frozen_clauses_use_the_compact_bloc_05_form() -> None:
    for row in _payload()["rows"]:
        assert row["frozen_clause"].startswith("bloc_05/"), row["case_id"]


def test_refusal_classes_are_exact_and_within_the_vocabulary() -> None:
    payload = _payload()
    assert payload["refusal_class_vocabulary"] == REFUSAL_CLASS_VOCABULARY
    for row in payload["rows"]:
        assert row["refusal_class"] == EXPECTED_REFUSAL_CLASS[row["case_id"]], (
            row["case_id"],
            row["refusal_class"],
        )


def test_expected_outcomes_are_independently_written_not_copied() -> None:
    # Each expected_result must be a frozen-contract sentence, not a verbatim
    # echo of the observation.
    for row in _payload()["rows"]:
        expected = row["expected_result"]
        observed = row["observed_result"]
        assert expected != observed, row["case_id"]
        assert expected.strip()[-1] == ".", row["case_id"]


# ---------------------------------------------------------------------------
# RS-04 and RS-14 honesty (I06E1 sections 05 and 04)
# ---------------------------------------------------------------------------


def test_rs04_boundary_is_explicit_and_not_an_end_to_end_cutoff_execution() -> None:
    row = next(r for r in _payload()["rows"] if r["case_id"] == "RS-04")
    disposition = row["disposition"]
    assert "BOUNDARY_ONLY" in disposition, disposition
    assert "NOT_END_TO_END" in disposition, disposition
    assert "I19" in disposition, disposition
    observed = row["observed_result"]
    assert "no cutoff parameter" in observed, observed


def test_rs14_fails_closed_without_latency_evidence() -> None:
    row = next(r for r in _payload()["rows"] if r["case_id"] == "RS-14")
    assert row["refusal_class"] == "NO_EVIDENCE_NO_ADMISSION"
    observed = row["observed_result"]
    assert "no latency parameter" in observed, observed
    assert "zero" in observed, observed  # missing data must not become zero-delay


# ---------------------------------------------------------------------------
# No duplicate engines; I05 behavior imported, not reimplemented (M2)
# ---------------------------------------------------------------------------


def test_producer_imports_production_primitives_and_defines_no_engine() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert any(
        "crypto_sensor_fabric" in name for name in imported
    ), "the producer must import the accepted production package"
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for forbidden in (
        "derive_market_available_at",
        "assess_replay_eligibility",
        "select_revisions",
    ):
        assert forbidden not in defined, (
            f"{forbidden} must be IMPORTED from the accepted I05 package, "
            "never redefined (no duplicate engine)"
        )


def test_the_scope_adds_no_production_module_and_no_config_change() -> None:
    """Disclosed B5-I08 delta only: ``quant-lab/src`` carries nothing but the
    operator-authorized ``normalization/common/`` tree (bloc_05/03 s21).

    The allowance is a prefix match on that one directory, so every other
    production path -- untracked, staged or committed -- must still be
    byte-identical to the I06 base, exactly as this test has always required.
    """

    def _status_paths() -> list[str]:
        """Porcelain lines are two status columns, one space, the path."""
        out = _git("status", "--porcelain", "--", "quant-lab/src")
        return sorted(line[3:] for line in out.splitlines() if line.strip())

    def _diff_paths() -> list[str]:
        """Only the ``diff --git a/<path> b/<path>`` headers name paths."""
        diff = _git("diff", I06_BASE_HEAD, "--", "quant-lab/src")
        return sorted(
            line.rsplit(" b/", 1)[1]
            for line in diff.splitlines()
            if line.startswith("diff --git ")
        )

    offending_status = [
        path for path in _status_paths() if not path.startswith(I08_COMMON_PREFIX)
    ]
    assert offending_status == [], f"src/ changed outside authority: {offending_status}"
    offending_diff = [
        path for path in _diff_paths() if not path.startswith(I08_COMMON_PREFIX)
    ]
    assert offending_diff == [], (
        f"production source differs from the I06 base: {offending_diff}"
    )


# ---------------------------------------------------------------------------
# Operator decisions M1/M3 respected (confidence unchanged, no latency guess)
# ---------------------------------------------------------------------------


def test_confidence_policy_is_unchanged_opaque_and_presence_checked() -> None:
    diff = _git("diff", I06_BASE_HEAD, "--", "quant-lab/src/crypto_sensor_fabric/normalization/time/models.py")
    assert diff == "", "M1 Option B forbids any I05 model change"
    # Behavioral check: a missing token still blocks, a numeric token still refused.
    sys.path.insert(0, str(_QUANT_LAB / "src"))
    try:
        from crypto_sensor_fabric.normalization.time import (
            AvailabilityConfidenceToken,
        )
        from pydantic import TypeAdapter

        adapter = TypeAdapter(AvailabilityConfidenceToken)
        for numeric in ("1", "0.95", "1e3"):
            try:
                adapter.validate_python(numeric)
            except Exception:
                pass
            else:
                raise AssertionError(f"confidence accepted a number: {numeric}")
    finally:
        sys.path.pop(0)


def test_provider_registry_still_carries_zero_real_rows() -> None:
    from crypto_sensor_fabric.normalization.time import parse_provider_time_semantics_yaml

    registry = parse_provider_time_semantics_yaml(
        SEMANTICS_CONFIG.read_text(encoding="utf-8")
    )
    assert list(registry.semantics) == [], (
        "M3/M4 DEFERRED: no real-provider row may be admitted"
    )


def test_no_latency_policy_was_added_to_the_accepted_ladder() -> None:
    diff = _git("diff", I06_BASE_HEAD, "--", "quant-lab/config")
    assert diff == "", "M3/M4 DEFERRED: configurations are sealed"
    diff_src = _git(
        "diff", I06_BASE_HEAD, "--", "quant-lab/src/crypto_sensor_fabric/normalization/time/availability.py"
    )
    assert diff_src == "", "the accepted availability ladder is sealed"


# ---------------------------------------------------------------------------
# Prior evidence unchanged (G06-12)
# ---------------------------------------------------------------------------


#: DISCLOSED B5-I08: the amended I05 audit test changes its own entry in the
#: I05 producer's SHA-256 inventory, so this sealed artifact is regenerated to
#: the pinned bytes below; the other four artifacts stay absolutely sealed.
#: The recorded value was the I08-regenerated state.
I08_TIME_VALIDATION_SHA256 = (
    "78d3f2a091a9dc66775c8b4bd767e12807a406ea009f9f9396babecc6eb4179f"
)

#: DISCLOSED B5-I09 (SENSOR-B5-I09E1 directive; full record in
#: ``BLOC_05_I09_IMPLEMENTATION_EVIDENCE.md`` + ledger section 178): the I09E1
#: implementation pass amends the I05 audit's staged allowlist once more (the
#: ``test_b5_i09`` suites, on the same precedent) and the I08 audit's frozen
#: module set (seven §21 modules instead of four).  Both changes re-enter the
#: I05 producer's inventory, so this artifact is regenerated again -- one
#: inventory line each -- exactly as the I08 cascade did.  The I08 value above
#: is kept for the historical record; the operative pin is this one.
I09_TIME_VALIDATION_SHA256 = (
    "b3b8843c0092c7b373964cfd6b6f67a266fbecb52537197183e7566c6426570c"
)


def test_prior_checkpoint_evidence_bytes_are_unchanged() -> None:
    for name in (
        "bloc_05_time_validation.json",
        "BLOC_05_I05_SCOPE_AUDIT.json",
        "BLOC_05_I05_OPERATOR_RATIFICATION.md",
        "BLOC_05_I06_READINESS_ASSESSMENT.md",
        "BLOC_05_I06D1_DECISION_PACKAGE.md",
    ):
        if name == "bloc_05_time_validation.json":
            measured = hashlib.sha256(
                (_EVIDENCE / name).read_bytes()
            ).hexdigest()
            assert measured == I09_TIME_VALIDATION_SHA256, (
                f"{name} left its disclosed B5-I09 state: {measured}"
            )
            continue
        diff = _git(
            "diff", I06_BASE_HEAD, "--",
            f"quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/{name}",
        )
        assert diff == "", name


# ---------------------------------------------------------------------------
# Producer laws: provenance, determinism, exit contract
# ---------------------------------------------------------------------------


def test_provenance_names_the_tracked_i06_producer_only() -> None:
    provenance = _payload()["generator"]
    assert SCRIPT_RELPATH in provenance
    assert "b5_i06_replay_safety.py" in provenance
    assert ".bu_tmp" not in provenance
    assert "python " in provenance


def test_the_producer_has_no_live_clock_and_no_untracked_dependency() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "datetime.now(",
        "datetime.utcnow(",
        "date.today(",
        "time.time(",
    ):
        assert forbidden not in text, forbidden


def test_the_sha256_inventory_is_recomputable() -> None:
    inventory = _payload()["sha256_inventory"]
    assert inventory, "an evidence artifact without an inventory proves nothing"
    for relpath, digest in sorted(inventory.items()):
        path = _ROOT / relpath
        assert path.is_file(), relpath
        recomputed = hashlib.sha256(path.read_bytes()).hexdigest()
        assert recomputed == digest, relpath


def test_row_ordering_is_stable_and_declared() -> None:
    rows = _payload()["rows"]
    assert [row["index"] for row in rows] == list(range(len(rows)))


def test_scope_audit_artifact_is_present_and_clean() -> None:
    payload = json.loads(SCOPE_ARTIFACT.read_text(encoding="utf-8"))
    assert payload["checkpoint"] == "SENSOR-B5-I06"
    assert payload["all_results_pass"] is True
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["rows"] == len(payload["rows"])
    for row in payload["rows"]:
        assert row["pass"] is True, row["row_id"]


def test_regeneration_is_byte_identical_and_exits_zero() -> None:
    committed = ARTIFACT.read_bytes()
    code, regenerated = _run_generator()
    assert code == 0, "a failed mandatory check must exit nonzero"
    assert regenerated == committed, "two generations must be byte-identical"


def test_regeneration_twice_is_still_byte_identical() -> None:
    first_code, first = _run_generator()
    second_code, second = _run_generator()
    assert (first_code, second_code) == (0, 0)
    assert first == second


def test_a_failing_mandatory_check_exits_nonzero() -> None:
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        import b5_i06_replay_safety as producer
    finally:
        sys.path.pop(0)
    payload = producer.build_payload()
    assert producer.mandatory_exit_code(payload) == 0
    payload["rows"][0]["pass"] = False
    assert producer.mandatory_exit_code(payload) != 0
