"""B6-I0 stage contract: derived scope, requirement inventory, G16, holds and P0 immutability."""
from __future__ import annotations

import json
import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parent))
import block_06_i0_support as S  # noqa: E402


def test_contract_frozen_before_evidence():
    contract = S.load("IMPLEMENTATION_CONTRACT")
    assert contract["frozen_before_results"] is True
    assert contract["stage"] == "AUTHORIZED_STAGE=B6-I0"
    assert contract["base_sha"] == S.BASE_SHA
    assert contract["p0_ratification_sha"] == S.P0_SHA
    assert contract["mutation_floor"] == {"source": 0, "frozen": 12}
    ledger = (S.DOCS / "OCE_BLOCK_06_I0_PROGRESS_EVIDENCE_LEDGER_v1.0.md").read_text(encoding="utf-8")
    assert "READY_FOR_OPERATOR_REVIEW" in ledger
    assert "NOT MERGE AUTHORIZED" in ledger


def test_scope_bindings_match_p0_sources():
    scope = S.load("SCOPE_DERIVATION")
    seq = S.p0("CONSTRUCTION_SEQUENCE_v1.0.json")
    stage = {s["id"]: s for s in seq["stages"]}["B6-I0"]
    assert scope["stage_binding"]["sections"] == stage["sections"] == ["C1.S5"]
    assert scope["stage_binding"]["non_goals"] == stage["non_goals"] == ["extraction of code"]
    assert scope["stage_binding"]["outputs"] == ["frozen contract"]
    assert scope["stage_binding"]["source_mutation_floor"] == 0
    reg = S.p0("REQUIREMENT_TEST_REGISTRY_v1.0.json")
    expected = sorted(r["id"] for r in reg["requirements"] if r["future_stage"] == "B6-I0")
    assert scope["requirements"] == expected
    fail = S.p0("FAILURE_AND_THREAT_REGISTRY_v1.0.json")
    assert scope["failure_classes"] == ["F01", "F02", "F03", "F04", "F17", "F20"]
    assert scope["threats"] == ["T04", "T05", "T07", "T08", "T09", "T14", "T20"]
    assert len(scope["candidates"]) == 27 and len(scope["api_rows"]) == 30
    assert len(scope["compatibility_rows"]) == 25
    assert len(scope["provenance_obligations"]) == 15
    assert scope["counts"]["planned_tests"] == len(scope["planned_tests"]) == 72


def test_requirement_inventory_19():
    registry = S.load("REQUIREMENT_TEST_REGISTRY")
    rows = registry["requirements"]
    assert len(rows) == registry["requirements_total"] == 19
    assert len({r["id"] for r in rows}) == 19
    assert len({r["binding_node"] for r in rows}) == 19
    for row in rows:
        module, node = row["binding_node"].split("::")
        path = S.ROOT / module
        assert path.exists(), module
        assert f"def {node}(" in path.read_text(encoding="utf-8"), row["binding_node"]
        assert row["state"] in {"PLANNED", "DEFERRED_WITH_OWNER", "BLOCKED"}
        assert row["claim"].startswith("NONE")
    assert registry["arithmetic"]["pass_claims"] == 0


def test_g16_open_and_blocker():
    g16 = json.loads((S.EVIDENCE / "b5-i9" / "g16-limitation.json").read_text(encoding="utf-8"))
    handoff = json.loads((S.EVIDENCE / "b5-i9" / "handoff-input-readiness.json")
                         .read_text(encoding="utf-8"))
    assert g16["status_value"] == "OPEN"
    assert g16["blocker"] == "B5I8-DF05"
    assert handoff["g16"]["status"] == "OPEN"
    assert handoff["g16"]["blocker"] == "B5I8-DF05"


def test_g16_condition_verbatim():
    g16 = json.loads((S.EVIDENCE / "b5-i9" / "g16-limitation.json").read_text(encoding="utf-8"))
    handoff = json.loads((S.EVIDENCE / "b5-i9" / "handoff-input-readiness.json")
                         .read_text(encoding="utf-8"))
    assert g16["missing_condition"] == handoff["g16"]["condition"]
    assert "independent operator" in g16["missing_condition"]


def test_no_independence_claim():
    forbidden = ("ORGANIZATIONALLY INDEPENDENT", "INDEPENDENT AUDIT COMPLETE",
                 "INDEPENDENCE PROVEN")
    for name in ("IMPLEMENTATION_CONTRACT", "SCOPE_DERIVATION", "FAILURE_AND_THREAT_PROOFS",
                 "REQUIREMENT_TEST_REGISTRY"):
        text = json.dumps(S.load(name))
        assert not any(token in text for token in forbidden), name
    registry = S.load("REQUIREMENT_TEST_REGISTRY")
    blocked = [r for r in registry["requirements"] if r["id"] == "B6-P0-G16-03"]
    assert len(blocked) == 1 and blocked[0]["state"] == "BLOCKED"


def test_g16_states_distinct():
    g16 = json.loads((S.EVIDENCE / "b5-i9" / "g16-limitation.json").read_text(encoding="utf-8"))
    assert g16["status_value"] == "OPEN"
    assert g16["status"] != "COMPLETE"
    assert g16["status_value"] != "CLOSED"
    contract = S.load("IMPLEMENTATION_CONTRACT")
    assert contract["operator_hold"]["state"] == "HELD"


def test_no_implementation_or_package():
    added = S.changed_since(S.BASE_SHA)
    assert not [p for p in added if p.startswith(("packages/", "dist/", "build/"))]
    assert not [p for p in added if p.startswith("infrastructure/control-plane/src/")]
    if S.stage_mode() in ("later", "i2"):
        # Later-stage mode: modules are admitted only on the contract paths of the stage chain.
        allowed = S.stage_scope_identity()["i1_allowed"]
        assert not [p for p in added if p.startswith("oce/") and not p.startswith(allowed)]
    else:
        # Strict B6-I0 mode keeps the original law: no module of any kind.
        assert not [p for p in added if p.startswith("oce/")]
    for script in S.SCRIPTS_I0:
        assert (S.SCRIPTS / script).exists()


def test_operator_hold_intact():
    hold = S.load("IMPLEMENTATION_CONTRACT")["operator_hold"]
    assert hold["b6_i0_ratification_authorized"] is False
    assert hold["b6_i0_merge_authorized"] is False
    assert hold["b6_i1_through_i9_authorized"] is False
    assert hold["package_publication_authorized"] is False
    assert hold["evaluation_authorized"] is False
    assert hold["cost_usd"] == 0
    assert hold["capital_authority"] == "none"


def test_no_packaging_artifacts():
    added = S.changed_since(S.BASE_SHA)
    banned = (".whl", ".egg-info", ".tar.gz", "pyproject.toml", "setup.py", "package.json")
    assert not [p for p in added if p.endswith(banned) or p.rsplit("/", 1)[-1] in banned]
    assert not [p for p in S.git("ls-files").stdout.splitlines()
                if p.startswith(("packages/", "dist/", "build/"))]


def test_p0_packet_unchanged():
    diff = S.git("diff", "--name-only", S.P0_SHA, "--", "docs/oce-golden-system")
    p0_changes = [p for p in diff.stdout.splitlines()
                  if p.strip() and "OCE_BLOCK_06_P0_" in p]
    assert p0_changes == []
    validator_diff = S.git("diff", "--name-only", S.P0_SHA, "--",
                           "infrastructure/control-plane/scripts/block_06_p0_validate.py")
    assert validator_diff.stdout.strip() == ""


def test_contract_declares_zero_extraction():
    decision = S.load("IMPLEMENTATION_CONTRACT")["decision"]
    assert decision["permits_code_extraction"] is False
    assert decision["creates_experimental_interfaces"] is False
    assert decision["extracted_source_files"] == 0
    assert decision["mode"] == "decision_artifacts_plus_conformance_tooling"
    rows = S.load("EXTRACTION_DECISION_FREEZE")["candidates"]
    assert all(r["extracted_at_b6_i0"] is False and r["copied_files"] == 0 for r in rows)
