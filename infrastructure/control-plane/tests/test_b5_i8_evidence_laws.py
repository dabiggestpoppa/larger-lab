"""OCE B5-I8 — audit evidence laws EL01–EL08 (8 frozen nodes).

Same design law as B5-I7's law suite: every law is a function that RAISES on
violation, executed twice — green on the real evidence bundle and red on a
falsified copy. A law that cannot fail would not be enforcement.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import b5_i8_audit_support as S

PREDICTIVE = ("will be ", "predicted sha", "expected sha", "placeholder sha")
OBSERVED_LABELS = {"OBSERVED", "NOT_OBSERVED"}
PLANNED_LABELS = {"EXPECTED", "FLOOR", "CEILING", "NOT_YET_OBSERVED"}


def _bundle() -> dict:
    return S.evidence()


def _falsified() -> dict:
    return json.loads(json.dumps(_bundle()))


def check_el01(bundle: dict) -> None:
    text = S.canonical(bundle)
    ci = bundle.get("ci", {})
    merge_ref = ci.get("merge_ref")
    for sha in set(S.HEX40.findall(text)):
        if merge_ref and sha == merge_ref:
            # A PR merge ref lives only on the server. Exempt ONLY while the parsed
            # artifact is cited and the ref genuinely does not resolve locally.
            assert ci.get("status") == "OBSERVED" and ci.get("parsed_from"), sha
            assert S.git("cat-file", "-e", sha).returncode != 0, "exempt sha resolves locally"
            continue
        if sha in S.PRUNED_REFS:
            # Exempt only because the exemption is recorded in the evidence.
            assert sha in S.canonical(bundle["limitations"]), sha
            continue
        assert S.git("cat-file", "-e", sha).returncode == 0, f"unresolvable sha: {sha}"
    lowered = text.lower()
    for phrase in PREDICTIVE:
        assert phrase not in lowered, f"predictive sha language: {phrase!r}"


class TestEL01:
    """B5I8-EL01 — no unverified SHA is recorded as fact."""

    def test_no_unverified_sha_recorded_as_fact(self):
        check_el01(_bundle())
        forged = _falsified()
        forged["tested"]["tree"] = "0" * 40
        with pytest.raises(AssertionError):
            check_el01(forged)
        forged2 = _falsified()
        forged2["limitations"].append("the merge sha will be recorded later")
        with pytest.raises(AssertionError):
            check_el01(forged2)


def check_el02(bundle: dict) -> None:
    ci = bundle["ci"]
    assert ci["status"] in {"NOT_EXECUTED", "OBSERVED"}, ci["status"]
    if ci["status"] == "NOT_EXECUTED":
        for key in ("run_id", "check_run_id", "job_id", "check_suite_id", "artifact_id"):
            assert ci[key] is None, f"{key} recorded before existence"
        assert ci["parsed_from"] is None
        assert ci["artifact_name"] is None
    else:
        for key in ("run_id", "check_run_id", "job_id", "artifact_id"):
            assert isinstance(ci[key], int) and ci[key] > 0, key
        assert ci["parsed_from"], "OBSERVED CI row without its parsed artifact"
        assert ci["tested_head"] and ci["tested_tree"] and ci["merge_ref"]
        # Every observed identity must equal the committed parsed record: an id that
        # no artifact attests cannot be recorded as fact.
        identity = S.ci_identity()
        assert identity.get("status") == "OBSERVED", "no committed CI identity record"
        for bundle_key, identity_key in (
            ("run_id", "run_id"),
            ("check_run_id", "check_run_id"),
            ("job_id", "job_id"),
            ("check_suite_id", "check_suite_id"),
            ("artifact_id", "artifact_id"),
            ("artifact_name", "artifact_name"),
            ("tested_head", "head_sha"),
            ("tested_tree", "tested_tree"),
            ("merge_ref", "merge_ref"),
        ):
            assert ci[bundle_key] == identity[identity_key], bundle_key
        assert identity["merge_ref_tree_equals_tested_tree"] is True


class TestEL02:
    """B5I8-EL02 — no run/check/artifact id is recorded before it exists."""

    def test_no_run_or_artifact_id_recorded_before_existence(self):
        check_el02(_bundle())
        forged = _falsified()
        forged["ci"]["run_id"] = 42043684359
        with pytest.raises(AssertionError):
            check_el02(forged)
        forged2 = _falsified()
        forged2["ci"]["status"] = "OBSERVED"
        forged2["ci"]["run_id"] = 1
        with pytest.raises(AssertionError):
            check_el02(forged2)


def check_el03(bundle: dict) -> None:
    planned = bundle["planned"]
    assert planned["label"] == "EXPECTED", planned["label"]
    assert planned["total"] == 40 and planned["floor"] == 40
    assert len(planned["nodes"]) == 40 and len(set(planned["nodes"])) == 40
    assert len(planned["files"]) == 5
    for name, row in bundle["measurements"].items():
        assert row["label"] in OBSERVED_LABELS, (name, row["label"])
    assert bundle["planned"]["label"] not in OBSERVED_LABELS


class TestEL03:
    """B5I8-EL03 — planned totals are EXPECTED/FLOOR, never OBSERVED."""

    def test_planned_totals_labeled_expected(self):
        check_el03(_bundle())
        forged = _falsified()
        forged["planned"]["label"] = "OBSERVED"
        with pytest.raises(AssertionError):
            check_el03(forged)
        forged2 = _falsified()
        forged2["measurements"]["tasks_defined"]["label"] = "FLOOR"
        with pytest.raises(AssertionError):
            check_el03(forged2)


def check_el04(bundle: dict) -> None:
    for name, row in bundle["measurements"].items():
        if row["label"] != "OBSERVED":
            continue
        assert row.get("value") is not None, name
        assert row.get("unit"), name
        assert row.get("command"), name
        assert row.get("tested_sha"), name
        assert row.get("environment"), name
        assert row.get("artifact"), name
        assert (S.REPO_ROOT / row["artifact"]).exists(), row["artifact"]
    results = bundle["protocol"]["results"]
    assert len(results) == 4
    recomputed = sum(int(row["navigation_steps"]) for row in results)
    assert bundle["measurements"]["navigation_steps_total"]["value"] == recomputed


class TestEL04:
    """B5I8-EL04 — observed totals are bound to a parsed raw source."""

    def test_observed_totals_bound_to_parsed_raw_artifact(self):
        check_el04(_bundle())
        forged = _falsified()
        forged["measurements"]["tasks_completed"]["command"] = ""
        with pytest.raises(AssertionError):
            check_el04(forged)
        forged2 = _falsified()
        forged2["measurements"]["navigation_steps_total"]["value"] = 999
        with pytest.raises(AssertionError):
            check_el04(forged2)


def check_el05(bundle: dict) -> None:
    labels = bundle["labels"]
    assert labels["audit"] == S.SAME_AGENT_LABEL
    assert labels["human_evidence"] == S.ATTESTATION_CLASS
    assert labels["blind"] is False
    assert labels["independent"] is False
    for row in bundle["protocol"]["results"]:
        assert row["recorded_by"] == S.ATTESTATION_CLASS, row["task_id"]
    text = S.canonical(bundle).lower()
    for claim in ("blind evaluation", "independent human", "double-blind"):
        assert claim not in text, claim


class TestEL05:
    """B5I8-EL05 — human evidence is labelled non-blind and same-agent."""

    def test_human_evidence_labeled_non_blind_not_independent(self):
        check_el05(_bundle())
        forged = _falsified()
        forged["labels"]["independent"] = True
        with pytest.raises(AssertionError):
            check_el05(forged)
        forged2 = _falsified()
        forged2["protocol"]["results"][0]["recorded_by"] = "INDEPENDENT_HUMAN"
        with pytest.raises(AssertionError):
            check_el05(forged2)


def check_el06(bundle: dict) -> None:
    pending = [
        name for name, gate in bundle["gates"].items() if gate["status"] != "CLOSED"
    ]
    assert pending, "no pending gate — the law is only meaningful while one is held"
    assert S.forbidden_hits(S.canonical(bundle)) == []
    paths = [S.CONTRACT, S.PLAN, S.FAILURE, S.ACCEPTANCE]
    if S.EVIDENCE_DOC.exists():
        paths.append(S.EVIDENCE_DOC)
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert S.forbidden_hits(corpus) == []


class TestEL06:
    """B5I8-EL06 — no 'all gates passed' language while a gate is pending."""

    def test_no_all_gates_passed_language_while_gate_pending(self):
        check_el06(_bundle())
        forged = _falsified()
        forged["limitations"].append("All gates passed, fully green.")
        with pytest.raises(AssertionError):
            check_el06(forged)


def check_el07(bundle: dict) -> None:
    verdict = bundle["verdict"]
    assert isinstance(verdict, dict), "the verdict must be machine-readable"
    required = {
        "requirements_total", "requirements_unique", "planned_nodes", "collected_nodes",
        "node_closure", "files", "mutations_required", "mutations_discriminated",
        "mutation_floor_met", "protocol_tasks", "protocol_results", "g16_status",
        "failure_classes", "digest",
    }
    assert required <= set(verdict), sorted(required - set(verdict))
    recorded = {key: value for key, value in verdict.items() if key != "digest"}
    assert S.recompute_verdict(bundle) == recorded
    assert verdict["digest"] == S.verdict_digest(bundle)


class TestEL07:
    """B5I8-EL07 — the verdict is recomputable, not free text."""

    def test_audit_verdict_recomputable_not_free_text(self):
        check_el07(_bundle())
        forged = _falsified()
        forged["verdict"] = "audit passed"
        with pytest.raises(AssertionError):
            check_el07(forged)
        forged2 = _falsified()
        forged2["verdict"]["node_closure"] = False
        with pytest.raises(AssertionError):
            check_el07(forged2)


def check_el08(bundle: dict) -> None:
    for row in bundle["protocol"]["results"]:
        assert row.get("command"), row["task_id"]
        assert row.get("artifact") and (S.REPO_ROOT / row["artifact"]).exists()
        assert row.get("executed_at") and row.get("environment")
        assert any(row["task_id"] == task["task_id"] for task in bundle["protocol"]["tasks"])
    for name, row in bundle["measurements"].items():
        assert row.get("artifact") and row.get("command"), name
    for row in bundle["accessibility"]:
        assert row.get("surface") and row.get("assertion") and row.get("finding")
    text = S.canonical(bundle)
    assert S.HEX40.findall(text), "evidence cites no source commit at all"


class TestEL08:
    """B5I8-EL08 — no evidence value is untraceable to a raw source."""

    def test_no_evidence_value_untraceable_to_raw_source(self):
        check_el08(_bundle())
        forged = _falsified()
        forged["protocol"]["results"][0]["artifact"] = "docs/does-not-exist.json"
        with pytest.raises(AssertionError):
            check_el08(forged)
        forged2 = _falsified()
        forged2["accessibility"][0]["finding"] = ""
        with pytest.raises(AssertionError):
            check_el08(forged2)
