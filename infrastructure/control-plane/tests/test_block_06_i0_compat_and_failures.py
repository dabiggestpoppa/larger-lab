"""B6-I0 compatibility baseline, conformance vocabulary, failure and threat proofs."""
from __future__ import annotations

import hashlib
import json

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parent))
import block_06_i0_support as S  # noqa: E402


def _canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def test_matrix_25_rows_unproven():
    d = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")
    rows = d["compatibility_rows"]
    assert d["rows_total"] == len(rows) == 25
    assert [r["surface"] for r in rows] == [f"C{c}.S{s}" for c in range(1, 6) for s in range(1, 6)]
    assert all(r["state"] == "UNPROVEN" for r in rows)
    assert all(r["consumer_evidence"] == "none" for r in rows)
    assert d["observed"] == {"proven_rows": 0, "unproven_rows": 25, "consumer_available": False}


def test_unknown_version_fails_closed():
    d = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")
    assert d["refusal"]["unknown_version"] == "REFUSED"
    assert d["refusal"]["unsupported_version"].startswith("REFUSED")
    assert d["identifiers"]["api_version"] == "1.0.0-draft"
    # An unknown version is never mapped onto a supported one.
    assert "accept" not in d["refusal"]["unknown_version"].lower()


def test_no_silent_latest():
    d = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")
    assert d["refusal"]["silent_latest"] is False
    assert "latest" in d["refusal"]["rule"].lower()
    assert "never silently" in d["refusal"]["rule"]


def test_deprecation_and_removal_declared():
    d = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")
    assert d["deprecation"]["required_fields"] == ["surface", "since_version",
                                                   "removal_version", "replacement"]
    assert d["removal"]["requires_migration_evidence"] is True
    assert d["migration_evidence"] == {"required": True, "state": "ABSENT"}
    assert d["deprecation"]["state"] == "DECLARED_NOT_APPLIED"
    assert d["removal"]["state"] == "DECLARED_NOT_APPLIED"


def test_fingerprint_deterministic():
    d = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")
    rows = d["compatibility_rows"]
    assert d["structural_fingerprint"]["value"] == hashlib.sha256(_canonical(rows)).hexdigest()
    reordered = [dict(r) for r in rows]
    assert hashlib.sha256(_canonical(reordered)).hexdigest() == d["structural_fingerprint"]["value"]
    assert d["structural_fingerprint"]["algorithm"].startswith("sha256")


def test_conformance_vocabulary_closed():
    conf = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")["conformance"]
    assert conf["vocabulary"] == ["PASS", "FAIL", "UNPROVEN", "REFUSED"]
    assert conf["default_state"] == "UNPROVEN"
    assert conf["evidence_schema"]["closure"] == "unknown fields are rejected"
    assert set(conf["evidence_schema"]["required"]) == {"subject", "state", "evidence", "reason"}


def test_declaration_without_test_not_proven():
    conf = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")["conformance"]
    assert conf["declaration_without_test"] == "UNPROVEN"
    assert "discriminating test" in conf["pass_requires"]
    rows = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")["compatibility_rows"]
    assert all(r["discriminating_test"] is None for r in rows if r["state"] != "PROVEN")
    assert not [r for r in rows if r["state"] == "PROVEN" and not r["discriminating_test"]]


def test_schema_identifiers_pinned():
    d = S.load("COMPATIBILITY_AND_CONFORMANCE_BASELINE")
    codec = S.load("IMPLEMENTATION_CONTRACT")["schemas"]
    assert d["identifiers"]["schema_version"] == "1.0.0"
    assert d["identifiers"]["conformance_version"] == "1.0.0"
    assert d["identifiers"]["package_version_format"] == "semver"
    assert codec["compatibility"]["columns"] == ["surface", "version", "supported_from",
                                                 "supported_to", "consumer_evidence", "state"]
    assert codec["conformance"]["vocabulary"] == d["conformance"]["vocabulary"]


def test_failure_classes_six():
    d = S.load("FAILURE_AND_THREAT_PROOFS")
    assert d["failure_classes_total"] == 6 == len(d["failure_classes"])
    assert [r["id"] for r in d["failure_classes"]] == ["F01", "F02", "F03", "F04", "F17", "F20"]
    source = {f["id"]: f for f in S.p0("FAILURE_AND_THREAT_REGISTRY_v1.0.json")["failure_classes"]}
    for row in d["failure_classes"]:
        assert source[row["id"]]["stage"] == "B6-I0"
        assert row["name"] == source[row["id"]]["name"]


def test_each_failure_has_trigger_and_refusal():
    for row in S.load("FAILURE_AND_THREAT_PROOFS")["failure_classes"]:
        for field in ("trigger", "expected_refusal", "observable", "recovery",
                      "negative_control", "bound", "implemented_proof"):
            assert row[field] not in (None, "", []), (row["id"], field)
        assert row["proof_state"] == "BOUND_PENDING_EVIDENCE"
        assert row["negative_control"].strip().lower() != row["trigger"].strip().lower()


def test_threats_seven_bound():
    d = S.load("FAILURE_AND_THREAT_PROOFS")
    assert d["threats_total"] == 7 == len(d["threats"])
    assert [t["id"] for t in d["threats"]] == ["T04", "T05", "T07", "T08", "T09", "T14", "T20"]
    source = {t["id"]: t for t in S.p0("FAILURE_AND_THREAT_REGISTRY_v1.0.json")["threats"]}
    for row in d["threats"]:
        assert source[row["id"]]["stage"] == "B6-I0"
        assert row["trust_boundary"] and row["asset"] and row["required_refusal"]
        assert row["negative_control"]
        assert row["state"] == "BOUND_PENDING_EVIDENCE"


def test_later_threats_remain_planned():
    d = S.load("FAILURE_AND_THREAT_PROOFS")
    assert d["later_threat_state"] == "PLANNED_NOT_IMPLEMENTED"
    assert len(d["later_threats"]) == 13
    all_threats = {t["id"] for t in S.p0("FAILURE_AND_THREAT_REGISTRY_v1.0.json")["threats"]}
    assert set(d["later_threats"]) | {t["id"] for t in d["threats"]} == all_threats
    assert not (set(d["later_threats"]) & {t["id"] for t in d["threats"]})


def test_no_new_failure_ids():
    d = S.load("FAILURE_AND_THREAT_PROOFS")
    all_ids = {f["id"] for f in S.p0("FAILURE_AND_THREAT_REGISTRY_v1.0.json")["failure_classes"]}
    assert set(d["later_failure_classes"]) | {f["id"] for f in d["failure_classes"]} == all_ids
    assert len(d["later_failure_classes"]) == 17
    assert d["later_failure_state"] == "PLANNED_NOT_IMPLEMENTED"


def test_recovery_declared():
    markers = ("refus", "restore", "reset", "revert", "re-run", "rerun", "re-read", "stop")
    for row in S.load("FAILURE_AND_THREAT_PROOFS")["failure_classes"]:
        text = (row["expected_refusal"] + " " + row["recovery"]).lower()
        assert any(marker in text for marker in markers), row["id"]
        assert row["recovery"].strip()
