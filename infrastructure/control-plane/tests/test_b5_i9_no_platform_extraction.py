"""B5-I9 no-platform law and authority firewall — frozen nodes for NP-01..NP-09."""
from __future__ import annotations

import json

import pytest

from oce_control import b5_i9_gate as gate

ROOT = gate.repo_root()
PACKET = ROOT / gate.PACKET_DIR


def contract():
    return json.loads((PACKET / "handoff-contract.json").read_bytes().decode("utf-8"))


def packet_texts():
    return {p.name: p.read_bytes().decode("utf-8", "replace")
            for p in sorted(PACKET.iterdir()) if p.is_file()}


FORBIDDEN_SYMBOLS = ("socket", "requests", "urllib", "httpx", "boto3", "broker", "order_id",
                     "wallet", "capital_allocation", "telemetry")


class TestNoPlatform:
    def test_no_reexport_of_control_plane_internals(self):
        doc = contract()
        assert doc["contains_extracted_source"] is False
        assert doc["files_copied"] == []
        assert doc["public_surface_paths"] == []
        for row in doc["allowed_design_inputs"]:
            assert row["class"] in gate.EXTRACTABLE
        assert not [r for r in doc["allowed_design_inputs"] if "infrastructure/" in json.dumps(r)]

    def test_no_private_module_in_public_surface(self):
        doc = contract()
        assert set(doc["allowed_classes"]) == set(gate.EXTRACTABLE)
        classes = {r["class"] for r in doc["excluded_candidates"]}
        assert {"PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED"} <= classes
        for row in doc["excluded_candidates"]:
            assert row["class"] not in gate.EXTRACTABLE

    def test_no_second_canonical_state(self):
        state = contract()["canonical_state"]
        assert state["owner"] == "control-plane"
        assert state["consumer_stores"] == []
        for name, body in packet_texts().items():
            if not name.endswith(".json"):
                continue
            doc = json.loads(body)
            for key in ("consumer_stores", "stores", "canonical_stores"):
                if key in doc and isinstance(doc[key], list):
                    assert doc[key] == [], (name, key)

    def test_no_duplicated_authority_decision(self):
        owners = contract()["authority_owners"]
        for function in ("admission", "refusal_reason", "recovery", "evidence", "configuration"):
            assert owners[function] and "control-plane" in owners[function], function
        for function in ("spend", "execution", "broker"):
            assert owners[function] is None, function
        excluded = {r["candidate"] for r in contract()["excluded_candidates"]}
        assert any("Admission / refusal decision" == name for name in excluded)

    def test_single_owner_per_authority_function(self):
        owners = contract()["authority_owners"]
        claimed = [v for v in owners.values() if v is not None]
        assert len(claimed) == len(set(claimed)), claimed
        assert len(owners) == 8
        assert sum(1 for v in owners.values() if v is None) == 3

    def test_single_configuration_truth(self):
        truth = contract()["configuration_truth"]
        assert isinstance(truth["source"], str) and truth["source"]
        assert truth["duplicates"] == []
        for row in contract()["allowed_design_inputs"]:
            assert "configuration default" not in row["candidate"].lower()

    def test_no_environment_or_host_embedded(self):
        gate.CHECKS["test_no_environment_specific_paths"](gate.ctx(gate.Repo(ROOT)))
        for name, body in packet_texts().items():
            assert not gate.DRIVE_PATH.search(body), name
            assert not gate.HOST_PATTERN.search(body), name
            assert "/home/" not in body and "\\\\" not in body, name

    def test_no_cloud_or_execution_surface(self):
        surface = json.dumps(contract()["allowed_design_inputs"]).lower()
        for symbol in FORBIDDEN_SYMBOLS:
            assert symbol not in surface, symbol
        hold = json.loads((PACKET / "operator-hold.json").read_bytes().decode("utf-8"))
        assert hold["capital_authority"] == "none"
        assert hold["cost_usd"] == 0
        assert hold["extraction"] == "NOT_PERFORMED"

    def test_no_cloud_or_provider_surface(self):
        for name, body in packet_texts().items():
            assert not gate.has_provider(body), "provider name in {}".format(name)
        assert gate.has_provider("deployed on AWS")
        assert not gate.has_provider("the evidence laws")
        provenance = json.loads((PACKET / "provenance.json").read_bytes().decode("utf-8"))
        assert provenance["network_access"] is False
        assert provenance["secrets_required"] is False
