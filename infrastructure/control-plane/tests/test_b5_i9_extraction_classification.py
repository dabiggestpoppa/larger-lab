"""B5-I9 extraction classification — frozen nodes for EX-01..EX-07."""
from __future__ import annotations

import json

import pytest

from oce_control import b5_i9_gate as gate

ROOT = gate.repo_root()
PACKET = ROOT / gate.PACKET_DIR


def census():
    return json.loads((PACKET / "classification-census.json").read_bytes().decode("utf-8"))


def rows():
    return census()["rows"]


def by_source(fragment):
    return [r for r in rows() if fragment in r["source"]]


class TestClassification:
    def test_every_candidate_classified_once(self):
        doc = census()
        assert doc["total"] == 27
        assert len({r["id"] for r in doc["rows"]}) == 27
        counts = {name: 0 for name in gate.CLASSES}
        for row in doc["rows"]:
            assert row["class"] in gate.CLASSES
            counts[row["class"]] += 1
        assert counts == gate.FROZEN_COUNTS
        assert sum(counts.values()) == 27

    def test_authority_bearing_items_are_never_extractable(self):
        gate.CHECKS["test_authority_bearing_items_are_never_extractable"](gate.ctx(gate.Repo(ROOT)))
        authority = [r for r in rows() if r["class"] == "AUTHORITY_BEARING"]
        assert len(authority) == 3
        for row in authority:
            assert "Decides" in row["authority_impact"]
            assert row["book6_disposition"] == "excluded; never extracted"
        prohibited = [r for r in rows() if r["class"] == "PROHIBITED"]
        assert len(prohibited) == 1
        assert prohibited[0]["book6_disposition"] == "excluded; never extracted"

    def test_private_interfaces_never_promoted(self):
        gate.CHECKS["test_private_interfaces_never_promoted"](gate.ctx(gate.Repo(ROOT)))
        for fragment in ("job_store.py", "pg_store.py", "recovery.py"):
            assert [r["class"] for r in by_source(fragment)][0] == "PLATFORM_INTERNAL"
        for fragment in ("health.py", "b5_i8_audit_support.py"):
            assert [r["class"] for r in by_source(fragment)][0] == "PRIVATE_API"
        contract = json.loads((PACKET / "handoff-contract.json").read_bytes().decode("utf-8"))
        assert contract["public_surface_paths"] == []

    def test_extractable_items_declare_refusal_behaviour(self):
        extractable = [r for r in rows() if r["class"] in gate.EXTRACTABLE]
        assert len(extractable) == 12
        for row in extractable:
            assert row["refusal"]
            assert "refuse" in row["refusal"]

    def test_extractable_items_declare_recovery_behaviour(self):
        for row in [r for r in rows() if r["class"] in gate.EXTRACTABLE]:
            assert row["recovery"]
            assert "recover" in row["recovery"] or "regenerat" in row["recovery"]

    def test_extractable_items_declare_provenance_and_limits(self):
        boundary_sha = gate.sha256((ROOT / gate.DOCS_DIR / gate.BOUNDARY).read_bytes()
                                   .replace(b"\r\n", b"\n"))
        for row in [r for r in rows() if r["class"] in gate.EXTRACTABLE]:
            assert row["provenance"]["sha256"] == boundary_sha
            assert row["provenance"]["row"] >= 1
            if row["class"] == "EXTRACTABLE_WITH_LIMITATION":
                assert row["limitation"] and row["limitation"] != "none"
            else:
                assert row["limitation"] == "none"

    def test_negative_control_rejects_reusable_looking_component(self):
        kernel = by_source("oce_console/kernel.py")[0]
        assert kernel["class"] == "EXTRACTABLE_WITH_LIMITATION"
        assert "stdlib" in kernel["limitation"].lower()
        job_store = by_source("job_store.py")[0]
        assert job_store["class"] == "PLATFORM_INTERNAL"
        ctx = gate.ctx(gate.Repo(ROOT))
        promoted = [dict(r) for r in ctx["rows"]]
        for row in promoted:
            if "job_store.py" in row["source"]:
                row["class"] = "EXTRACTABLE_PATTERN"
        with pytest.raises(gate.GateViolation) as exc:
            gate.test_private_interfaces_never_promoted(dict(ctx, rows=promoted))
        assert exc.value.check == "test_private_interfaces_never_promoted"
