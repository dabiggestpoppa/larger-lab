"""OCE B5-I8 — independent audit, evidence audit and gate closure (8 nodes).

The `G16` node is inherited verbatim and its disposition is RECOMPUTED from the
executed protocol rows: a protocol executed by one non-blind operator cannot
close an accessibility/usability gate, so the node proves the protocol ran and
that the recorded disposition matches the recomputation (OPEN with a precise
blocker), not that a claim was typed into a document.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import b5_i8_audit_support as S
from oce_console import panel

NODE_ID = "TestUsabilityProtocol::test_accessibility_and_usability_verified"
G16_SOURCE = "B5-I3 construction plan section 8; B5-I3 registry G16.deferred.planned_node"


class TestUsabilityProtocol:
    """B5I8-R39 — the inherited `G16` obligation at its frozen node id."""

    def test_accessibility_and_usability_verified(self):
        # The frozen id exists verbatim, exactly once, in the planned inventory.
        planned = S.planned_nodes()
        assert NODE_ID in planned
        assert planned.count(NODE_ID) == 1
        surface = next(
            entry["planned_surface"]
            for entry in S.registry()["entries"]
            if entry["id"] == "B5I8-R39"
        )
        assert surface.endswith("test_b5_i8_independent_audit.py::" + NODE_ID)
        assert G16_SOURCE  # provenance is carried, not invented here

        # The protocol executes (live), and the recorded rows are reproducible.
        live = S.run_protocol()
        bundle = S.evidence()
        assert len(live) == len(bundle["protocol"]["results"]) == 4
        assert all(row["completion"] is True for row in live)
        assert all(row["error"] == 0 for row in live)
        checks = S.accessibility_checks()
        assert len(checks) == 5 and all(row["result"] == "PASS" for row in checks)

        # The disposition is recomputed from the evidence, never trusted from prose.
        computed = S.gates(bundle)["G16"]
        assert bundle["gates"]["G16"] == computed
        assert computed["protocol_executed"] is True
        assert computed["attestation_class"] == [S.ATTESTATION_CLASS]
        assert computed["status"] == "OPEN"
        assert "independent operator" in computed["blocker"]
        assert S.registry()["p0"]["ratification"]["g16_status"] == computed["status"] == "OPEN"

        # Two-sided: forged independence flips the recomputation, so the check
        # is not a constant. The recorded disposition would then be inconsistent.
        forged = json.loads(json.dumps(bundle))
        for row in forged["protocol"]["results"]:
            row["recorded_by"] = "INDEPENDENT_HUMAN"
        assert S.gates(forged)["G16"]["status"] == "CLOSED"
        assert S.gates(forged)["G16"] != bundle["gates"]["G16"]


class TestEvidenceAudit:
    """B5I8-R29..R33 — citations, ids, green claims, manifests, termination."""

    def test_prior_stage_citations_resolve_to_commits(self):
        shas: set = set()
        for path in (S.CONTRACT, S.PLAN, S.FAILURE, S.ACCEPTANCE, S.REGISTRY):
            shas |= set(S.HEX40.findall(path.read_text(encoding="utf-8")))
        assert len(shas) >= 5, "no prior-stage citations found"
        ci = S.registry()["p0"]["implementation"]["evidence"].get("ci", {})
        merge_ref = ci.get("merge_ref")
        # A PR merge ref exists only on the server (refs/pull/N/merge); it is not a
        # history citation. It is exempt from local resolution ONLY while the artifact
        # that attests it is cited and both recorded parents resolve as real commits.
        if merge_ref:
            assert ci.get("status") == "GREEN", ci.get("status")
            assert ci.get("artifact"), "merge ref exempt without an attesting artifact"
            for parent_key in ("merge_ref_first_parent", "merge_ref_second_parent"):
                parent = ci.get(parent_key)
                assert parent and S.git("cat-file", "-e", parent).returncode == 0, parent_key
        for sha in sorted(shas):
            if sha in S.PRUNED_REFS:
                # A pruned ref is exempt ONLY while the exemption is recorded.
                assert sha in S.canonical(S.evidence()["limitations"]), sha
                continue
            if merge_ref and sha == merge_ref:
                assert S.git("cat-file", "-e", sha).returncode != 0, "exempt sha resolves locally"
                continue
            assert S.git("cat-file", "-e", sha).returncode == 0, sha
        # Discrimination: a fabricated sha does not resolve.
        assert S.git("cat-file", "-e", "0" * 40).returncode != 0
        assert (
            S.git(
                "cat-file", "-e",
                "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            ).returncode
            != 0
        )

    def test_run_and_artifact_ids_resolve_to_raw_evidence(self):
        bundle = S.evidence()
        ci = bundle["ci"]
        assert ci["status"] in {"NOT_EXECUTED", "OBSERVED"}
        if ci["status"] == "NOT_EXECUTED":
            for key in ("run_id", "check_run_id", "job_id", "artifact_id", "check_suite_id"):
                assert ci[key] is None, f"{key} recorded before the run existed"
            assert ci["parsed_from"] is None
            assert ci["tested_head"] is None
        else:
            for key in ("run_id", "check_run_id", "job_id", "artifact_id"):
                assert isinstance(ci[key], int) and ci[key] > 0, key
            assert ci["parsed_from"], "no parsed raw artifact cited"
            assert ci["tested_head"] and ci["tested_tree"]

        # The P0 CI identities that ARE cited carry their parseable artifact name.
        import re as _re

        p0 = S.registry()["p0"]["ratification"]["audit_ci"]
        assert isinstance(p0["run_id"], int)
        assert _re.fullmatch(r"b1-i1r-evidence-[0-9a-f]{12}", p0["artifact_name"])
        assert isinstance(p0["artifact_id"], int)
        assert p0["tested_tree"] != p0["tested_head"] != ""

    def test_no_all_green_claim_while_gate_pending(self):
        assert S.gates()["G16"]["status"] != "CLOSED"
        paths = [S.CONTRACT, S.PLAN, S.FAILURE, S.ACCEPTANCE]
        if S.EVIDENCE_DOC.exists():
            paths.append(S.EVIDENCE_DOC)
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        assert S.forbidden_hits(corpus) == []
        assert S.forbidden_hits(S.canonical(S.evidence())) == []
        # Discrimination: the detector is not vacuous.
        assert S.forbidden_hits("The audit reports ALL GATES PASSED today.")

    def test_manifest_rows_recompute_over_committed_bytes(self):
        doc = S.load(S.SUPERSEDING)
        rows = doc["artifacts"]
        assert len(rows) == 13
        ledger = next(r for r in rows if r["path"].endswith("LEDGER_v1.0.md"))
        assert ledger["sha256"] == S.LEDGER_PREFIX_SHA
        assert ledger["size_bytes"] == S.LEDGER_PREFIX_BYTES

        data = S.read_bytes(S.REPO_ROOT / ledger["path"])
        assert len(data) >= ledger["size_bytes"]
        assert S.sha256_bytes(data[: ledger["size_bytes"]]) == ledger["sha256"]

        checked = 0
        for row in rows:
            if row is ledger:
                continue
            path = S.REPO_ROOT / row["path"]
            assert path.exists(), row["path"]
            assert S.digest_file(path) == row["sha256"], row["path"]
            assert len(S.read_bytes(path)) == row["size_bytes"], row["path"]
            checked += 1
        assert checked == 12

        # A tampered historical byte breaks the prefix row (the law is live).
        tampered = bytearray(data)
        tampered[0] ^= 0x01
        assert (
            S.sha256_bytes(bytes(tampered)[: ledger["size_bytes"]]) != ledger["sha256"]
        )


class TestAuditVerdict:
    """B5I8-R34 — the verdict is recomputed from committed evidence."""

    def test_verdict_recomputable_from_committed_evidence(self):
        bundle = S.evidence()
        recorded = {key: value for key, value in bundle["verdict"].items() if key != "digest"}
        assert S.recompute_verdict(bundle) == recorded
        assert bundle["verdict"]["digest"] == S.verdict_digest(bundle)
        assert recorded["requirements_total"] == recorded["requirements_unique"] == 55
        assert recorded["planned_nodes"] == recorded["collected_nodes"] == 40
        assert recorded["node_closure"] is True
        assert recorded["g16_status"] == "OPEN"
        assert recorded["failure_classes"] == 18

        # Two-sided: a changed input changes the verdict, so it is not prose.
        mutated = json.loads(json.dumps(bundle))
        mutated["protocol"]["results"] = []
        assert S.recompute_verdict(mutated) != recorded
        assert S.digest_obj(S.recompute_verdict(mutated)) != bundle["verdict"]["digest"]


class TestGateClosure:
    """B5I8-R40..R41 — G14 adjacent population and G15 mutation discrimination."""

    def test_g14_adjacent_population_stays_green(self):
        adjacent = S.collect_adjacent()
        assert adjacent["returncode"] == 0
        assert adjacent["total"] >= 189, adjacent
        assert set(adjacent["counts"]) == set(S.adjacent_files())
        assert all(count > 0 for count in adjacent["counts"].values())
        assert adjacent["counts"]["test_b5_i7_evidence_laws.py"] == 15
        assert adjacent["counts"]["test_b5_i7_governed_change.py"] == 12

        # The authoritative workflow selects the WHOLE focused surface, so the
        # population above and the 40 nodes below are actually executed by CI.
        step = S.workflow_b5_i8_step()
        for name in S.planned_files():
            assert name in step, name
        assert "B5I8_FLOOR" in step and "40" in step
        assert "b5-i8-collect.txt" in step
        assert "b5-i8-junit.xml" in step
        assert "b5-i8-registry-proof.json" in step
        assert "PR_HEAD_SHA" in step
        assert "classname" in step  # every JUnit case is checked for module identity
        assert " -k " not in step  # whole-file selection, never a keyword subset
        assert "pytest" in step

    def test_g15_mutation_controls_discriminate(self):
        doc = S.mutations()
        rows = doc["mutations"]
        planned = set(S.planned_nodes())
        assert len(rows) >= S.registry()["p0"]["mutation_floor"] == 12
        assert len({row["mutation_id"] for row in rows}) == len(rows)

        for row in rows:
            assert row["red"] is True, row["mutation_id"]
            assert row["observed_node"] == row["expected_node"]
            assert row["expected_node"] in planned, row["expected_node"]
            assert row["pre_sha256"] == row["restored_sha256"], row["mutation_id"]
            assert row["mutated_sha256"] != row["pre_sha256"], row["mutation_id"]
            assert row["applied"] is True, row["mutation_id"]
            assert row["exit_status"] != 0, row["mutation_id"]
            assert row["verdict"] == "DISCRIMINATED"

        assert len({row["mutated_sha256"] for row in rows}) == len(rows)
        assert doc["pristine"]["restored_byte_exact"] is True
        assert doc["pristine"]["worktree_clean"] is True

        # Independent totals owner: the committed CI identity record and the registry,
        # NOT the bundle this stage is producing. G15's totals were previously removed
        # for self-reference (defect D2); they are restored here against a distinct
        # source and cross-checked against the registry's own arithmetic.
        identity = S.ci_identity()
        assert identity["status"] == "OBSERVED"
        planned_total = S.registry()["requirement_set"]["total"]
        assert len(planned) == 40 and planned_total == 55
        assert identity["collected"] == identity["executed"] == identity["passed"] == 40
        assert identity["failures"] == identity["errors"] == identity["skipped"] == 0
        assert identity["unique_nodes"] == 40
        assert identity["collected"] == len(planned) == identity["unique_nodes"]
        assert S.git("cat-file", "-e", identity["head_sha"]).returncode == 0
        assert S.git("cat-file", "-e", identity["tested_tree"]).returncode == 0
        assert identity["merge_ref_tree_equals_tested_tree"] is True

        # Machine-readable non-vacuity closure: every planned node is audited once,
        # names a real target and oracle, and any cited mutation exists in the battery.
        audit = json.loads(
            (S.DOCS / "OCE_B5_I8_NODE_NONVACUITY_AUDIT_v1.0.json").read_text(encoding="utf-8")
        )
        audited = [row["node"] for row in audit["nodes"]]
        assert len(audited) == 40 and len(set(audited)) == 40
        assert set(audited) == planned, sorted(set(planned) - set(audited))
        mutation_ids = {row["mutation_id"] for row in rows}
        for row in audit["nodes"]:
            assert row["verdict"] == "NON_VACUOUS", row["node"]
            assert row["target"] and row["oracle"] and row["requirement"], row["node"]
            if row["negative_control"].startswith("M"):
                assert row["negative_control"] in mutation_ids, row["node"]
        assert audit["totals"]["tautological"] == 0
        assert audit["totals"]["orphan_nodes"] == 0
        assert audit["totals"]["orphan_requirements"] == 0

        def check_totals(record: dict) -> None:
            assert record["collected"] == record["executed"] == record["passed"] == 40
            assert record["failures"] == record["errors"] == record["skipped"] == 0
            assert record["unique_nodes"] == 40

        check_totals(identity)
        for key, value in (("collected", 39), ("executed", 41), ("passed", 40),
                           ("failures", 1), ("unique_nodes", 39)):
            forged_identity = dict(identity)
            forged_identity[key] = value
            try:
                check_totals(forged_identity)
            except AssertionError:
                pass
            else:  # pragma: no cover
                raise AssertionError(f"totals check accepted forged {key}={value}")

        # Discrimination: a non-red row invalidates the battery.
        def check(document: dict) -> None:
            bad = [
                row["mutation_id"]
                for row in document["mutations"]
                if row["red"] is not True
                or row["pre_sha256"] != row["restored_sha256"]
                or row["mutated_sha256"] == row["pre_sha256"]
            ]
            assert not bad, f"non-discriminating mutations: {bad}"

        forged = json.loads(json.dumps(doc))
        forged["mutations"][0]["red"] = False
        try:
            check(forged)
        except AssertionError:
            pass
        else:  # pragma: no cover - the checker must raise
            raise AssertionError("battery checker failed to detect a non-red mutation")
        check(doc)
