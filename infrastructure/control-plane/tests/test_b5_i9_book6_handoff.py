"""B5-I9 Book 6 handoff and G16 — frozen nodes for HO-01..HO-05 and GA-01..GA-02."""
from __future__ import annotations

import json
import re

from oce_control import b5_i9_gate as gate

ROOT = gate.repo_root()
PACKET = ROOT / gate.PACKET_DIR


def handoff():
    return json.loads((PACKET / "handoff-input-readiness.json").read_bytes().decode("utf-8"))


def contract():
    return json.loads((PACKET / "handoff-contract.json").read_bytes().decode("utf-8"))


class TestHandoff:
    def test_seven_states_are_distinct(self):
        states = handoff()["seven_states"]
        assert len(states) == 7
        names = [s["state"] for s in states]
        assert len(set(names)) == 7
        values = {s["state"]: s["value"] for s in states}
        assert values["Book 5 evidence complete"] is True
        assert values["Book 5 implementation complete"] is True
        assert values["Book 5 governance complete"] is False
        assert values["B5-I9 complete"] is False
        assert values["Book 6 input-ready"] is True
        assert values["Book 6 authorized"] is False
        assert values["Book 6 started"] is False
        owners = {s["state"]: s["owner"] for s in states}
        assert owners["Book 6 authorized"] == "operator"
        assert owners["Book 5 governance complete"] == "operator"

    def test_book6_states_remain_false(self):
        gate.CHECKS["test_book6_states_remain_false"](gate.ctx(gate.Repo(ROOT)))
        authorization = contract()["authorization"]
        assert authorization["book_6_authorized"] is False
        assert authorization["book_6_started"] is False
        locks = gate.Repo(ROOT).registry()["locks"]
        assert locks["book_6_authorized"] is False
        assert locks["book_6_started"] is False

    def test_no_book6_artifact_exists(self):
        pattern = re.compile(r"(book[_-]?6|b6)[_-]", re.I)
        planned = {f["path"].split("/")[-1] for f in
                   gate.Repo(ROOT).registry()["planned_surface"]["files"]}
        exempt = planned | {str(p.name) for p in (ROOT / gate.PACKET_DIR).iterdir()}
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.name in exempt:
                continue
            if pattern.search(path.name):
                offenders.append(str(path.relative_to(ROOT)))
        assert not offenders, offenders
        assert pattern.search("book6-implementation.json"), "detector is vacuous"
        assert not pattern.search("OCE_BLOCK_06_REUSABLE_PLATFORM_SURFACES_PLAN_v1.0.md")
        assert contract()["authorization"]["book_6_started"] is False

    def test_consumable_evidence_list_is_complete(self):
        items = handoff()["consumable_evidence"]
        assert len(items) >= 10
        text = " ".join(i["item"].lower() for i in items)
        for token in ("charter", "lifecycle", "kernel", "evidence", "law", "limitation",
                      "g16", "hash", "identity"):
            assert token in text, token
        for item in items:
            assert (ROOT / gate.DOCS_DIR / item["path"]).exists(), item["path"]
        assert any("merged-main" in i["item"] for i in items)

    def test_start_requires_fresh_authorization(self):
        doc = handoff()
        assert doc["authorization_token_required"] == "AUTHORIZED_STAGE=B6-I0"
        assert any("AUTHORIZED_STAGE=B6-I0" in s for s in doc["start_conditions"])
        assert doc["seven_states"][5]["value"] is False
        for implication in doc["non_implications"]:
            assert implication
        assert "input-ready never implies authorized" in doc["non_implications"]


class TestG16:
    def test_g16_remains_open_with_owner(self):
        gate.CHECKS["test_g16_remains_open_with_owner"](gate.ctx(gate.Repo(ROOT)))
        g16 = handoff()["g16"]
        assert g16["status"] == "OPEN"
        assert g16["blocker"] == "B5I8-DF05"
        assert "independent auditor" in g16["owner"]
        doc = json.loads((PACKET / "g16-limitation.json").read_bytes().decode("utf-8"))
        assert doc["status_value"] == "OPEN"
        assert doc["blocker"] == "B5I8-DF05"

    def test_missing_condition_carried_forward(self):
        condition = handoff()["g16"]["condition"]
        assert condition
        carried = json.loads((PACKET / "g16-limitation.json").read_bytes().decode("utf-8"))
        assert carried["missing_condition"] == condition
        assert any("g16" in i["item"].lower() for i in handoff()["consumable_evidence"])
        registry = gate.Repo(ROOT).registry()
        assert registry["locks"]["g16"]["status"] == "OPEN"
        assert registry["locks"]["post_book_6_evaluation"] == "UNSTARTED"
