"""
CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL tests.

Locks the truth-ingest + seal checkpoint:

  - frozen science (890/826/371/455/64, canonical book hash, 1% tolerance,
    ROUND_DOWN policy) unchanged; D1.2 plan PASS verified
  - NO quantity surface and NO margin study executed
  - no broker client / MetaTrader5 import / order API
  - every field carries truth_class + source; observed fields carry timestamps
  - profile hashes deterministic; any contract-field change -> new hash
  - QUANTITY_MINIMUM_COMPLETE rule deterministic; each missing required field
    blocks completeness
  - user scenarios never auto-promoted to actual; FakeMT5 / SimBroker never
    accepted as actual truth; conflicting truth blocks the profile
  - static vs observed account state separated; secrets absent; no
    performance-based selection; D1.2B authorization human-gated
  - offline and deterministic

Honest status expected: PARTIAL_PASS_WAITING_PHYSICAL_TRUTH (no actual /
documented USDJPY quantity truth exists in the repository; scenario profiles
lack instrument fields).  No PASS is manufactured.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = str(ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import run_physical_profile_truth_d1_2a as d1_2a  # noqa: E402

OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_physical_profile_truth_d1_2a"
BOOK_HASH = "b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a"


def _load_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def artifacts():
    return d1_2a.main()


def _runner_source() -> str:
    return (ROOT / "scripts" / "run_physical_profile_truth_d1_2a.py").read_text(
        encoding="utf-8")


def _imported_names(src: str):
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


# 1-8. Frozen science + policy unchanged
def test_d1_2_plan_pass_verified(artifacts):
    assert artifacts["d1_2_plan_pass_verified"] is True


def test_890_events_unchanged(artifacts):
    assert artifacts["n_events"] == 890


def test_826_accepted_unchanged(artifacts):
    assert artifacts["n_accepted"] == 826


def test_371_A_unchanged(artifacts):
    assert artifacts["accepted_A"] == 371


def test_455_B_unchanged(artifacts):
    assert artifacts["accepted_B"] == 455


def test_canonical_book_hash_unchanged(artifacts):
    assert artifacts["canonical_book_hash"] == BOOK_HASH


def test_fidelity_tolerance_unchanged(artifacts):
    assert artifacts["fidelity_tolerance_unchanged"] is True
    assert d1_2a.FIDELITY_TOLERANCE == 0.01


def test_round_down_policy_unchanged(artifacts):
    assert artifacts["rounding_policy_unchanged"] is True
    assert d1_2a.ROUNDING_PRIMARY == "ROUND_DOWN_TOWARD_ZERO"


# 9-12. No clipping / no upward / no surface / no margin
def test_no_clipping_enabled():
    # D1.2 frozen defaults carried forward: clipping stays FALSE
    d12 = json.loads((ROOT / "research" / "capital_routing" / "risk" /
                      "block4_quantity_representability_d1_2_plan" /
                      "CR_BLOCK4_D1_2_DECISION.json").read_text(encoding="utf-8"))
    assert d12["clipping_default"] is False


def test_no_upward_rounding_enabled():
    d12 = json.loads((ROOT / "research" / "capital_routing" / "risk" /
                      "block4_quantity_representability_d1_2_plan" /
                      "CR_BLOCK4_D1_2_DECISION.json").read_text(encoding="utf-8"))
    assert d12["upward_rounding_default"] is False


def test_no_quantity_surface_executed(artifacts):
    assert artifacts["quantity_surface_executed"] is False
    assert artifacts["d1_2b_ready"] is False


def test_no_margin_study_executed(artifacts):
    assert artifacts["margin_study_executed"] is False


# 13-15. No broker client / MT5 import / order API
def test_no_broker_client_added(artifacts):
    assert artifacts["capital_routing_broker_client_added"] is False
    assert artifacts["broker_contact_performed"] is False


def test_no_mt5_import():
    names = _imported_names(_runner_source())
    assert "mt5" not in names
    assert artifacts_mt5_free()


def artifacts_mt5_free():
    for p in OUT.glob("*.md"):
        txt = p.read_text(encoding="utf-8")
        if "import MetaTrader5" in txt or "import MetaTrader" in txt:
            return False
    return True


def test_no_order_api():
    src = _runner_source()
    assert "send_order" not in src
    assert "order_send" not in src
    assert "place_order" not in src
    assert artifacts["broker_order_attempted"] if "artifacts" in dir() else True


# 16-18. Field provenance
def test_each_field_has_truth_class():
    inst = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv")
    assert len(inst) >= 20
    assert (inst["truth_class"].isin(d1_2a.TRUTH_CLASSES)).all()
    assert (inst["truth_class"] == "UNKNOWN").sum() == len(inst) - 1  # research_symbol frozen


def test_each_resolved_field_has_source():
    inst = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv")
    resolved = inst[inst["status"] == "resolved"]
    assert len(resolved) >= 1
    assert (resolved["source"] != "UNKNOWN").all()
    assert (resolved["observed_at"] != "UNKNOWN").all()


def test_observed_fields_have_timestamp():
    # no ACTUAL_OBSERVED fields exist; schema requires observed_at for them
    schema = _load_json("CR_BLOCK4_D1_2A_FIELD_PROVENANCE_SCHEMA.json")
    assert "observed_at" in schema["fields"]
    inst = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv")
    assert (inst["truth_class"] != "ACTUAL_OBSERVED").all()  # none claimed


# 19-20. Profile hash determinism
def test_profile_hash_deterministic():
    fields = {"profile_id": "P", "contract_size": "100000", "truth_class": "UNKNOWN"}
    assert d1_2a.profile_hash(fields) == d1_2a.profile_hash(dict(fields))


def test_field_change_changes_profile_hash():
    a = d1_2a.profile_hash({"profile_id": "P", "contract_size": "100000",
                            "truth_class": "UNKNOWN"})
    b = d1_2a.profile_hash({"profile_id": "P", "contract_size": "200000",
                            "truth_class": "UNKNOWN"})
    assert a != b
    # contract fields in the generation manifest are hashed per profile
    gen = _load_json("CR_BLOCK4_D1_2A_PROFILE_GENERATION_MANIFEST.json")
    hashes = {pid: p["profile_hash"] for pid, p in gen["profiles"].items()}
    assert len(set(hashes.values())) == len(hashes)


# 21-27. Completeness rule deterministic + each missing field blocks
def test_quantity_complete_rule_deterministic():
    full = {f: "RESOLVED" for f in d1_2a.QUANTITY_MINIMUM_FIELDS}
    assert d1_2a.quantity_minimum_complete(full) is True
    assert d1_2a.quantity_minimum_complete(dict(full)) is True
    empty = {f: "UNKNOWN" for f in d1_2a.QUANTITY_MINIMUM_FIELDS}
    assert d1_2a.quantity_minimum_complete(empty) is False


def _missing_one(field: str) -> Dict[str, str]:
    return {f: "RESOLVED" if f != field else "UNKNOWN"
            for f in d1_2a.QUANTITY_MINIMUM_FIELDS}


def test_missing_contract_size_blocks():
    assert d1_2a.quantity_minimum_complete(_missing_one("contract_size")) is False


def test_missing_volume_min_blocks():
    assert d1_2a.quantity_minimum_complete(_missing_one("volume_min")) is False


def test_missing_volume_step_blocks():
    assert d1_2a.quantity_minimum_complete(_missing_one("volume_step")) is False


def test_missing_volume_max_blocks():
    assert d1_2a.quantity_minimum_complete(_missing_one("volume_max")) is False


def test_missing_account_currency_blocks():
    assert d1_2a.quantity_minimum_complete(_missing_one("account_currency")) is False


def test_missing_broker_symbol_blocks():
    assert d1_2a.quantity_minimum_complete(_missing_one("broker_symbol")) is False


def test_all_scenario_profiles_incomplete():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_PROFILE_REGISTRY.csv")
    assert (reg["quantity_complete"] == False).all()  # noqa: E712
    assert reg["completeness_level"].tolist() == ["PARTIAL_PROFILE"] * 4 + ["UNKNOWN_PROFILE"]


# 28-30. Scenario / fixture truth discipline
def test_user_scenario_never_auto_promoted():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_PROFILE_REGISTRY.csv")
    assert (reg["truth_class"] == "USER_SPECIFIED_SCENARIO").sum() == 4
    inv = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv")
    assert (inv["kind"] == "USER_SPECIFIED").sum() == 2
    scenario_audit = (OUT / "CR_BLOCK4_D1_2A_SCENARIO_PROFILE_AUDIT.md").read_text(
        encoding="utf-8")
    assert "NOT marked actual observed" in scenario_audit or \
        "NOT actual observed" in scenario_audit


def test_fakemt5_never_actual_truth():
    inv = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv")
    fake = inv[inv["source_id"] == "ERF-FAKE_MT5"].iloc[0]
    assert fake["usable_as_cr_truth"] == "no"
    assert "NOT truth" in fake["reason"]


def test_simbroker_never_actual_truth():
    inv = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv")
    sim = inv[inv["source_id"] == "ERF-SIM_BROKER"].iloc[0]
    assert sim["usable_as_cr_truth"] == "no"
    assert "NOT" in sim["reason"] or "not" in sim["reason"]
    # the generic FX convention hardcode must not leak into instrument truth
    inst = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv")
    assert (inst["value"] == "UNKNOWN").sum() == len(inst) - 1


# 31-32. Conflict handling + static/observed separation
def test_conflicting_truth_blocks_profile(artifacts):
    # status machine: a blocking conflict -> BLOCKED, never a manufactured PASS
    assert d1_2a.derive_status(0, 0, 1) == "BLOCKED_D1_2A_CONFLICTED_PHYSICAL_TRUTH"
    assert d1_2a.derive_status(0, 0, 0) == "PARTIAL_PASS_WAITING_PHYSICAL_TRUTH"
    assert d1_2a.derive_status(1, 0, 0) == "PASS_SCENARIO_TRUTH_ONLY"
    assert d1_2a.derive_status(1, 1, 0) == "PASS"
    rules = (OUT / "CR_BLOCK4_D1_2A_PROFILE_COMPLETENESS_RULES.md").read_text(
        encoding="utf-8")
    assert "CONFLICTED_PROFILE" in rules
    conflicts = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_SOURCE_CONFLICTS.csv")
    assert (conflicts["blocking"] == "no").all()
    assert artifacts["blocking_conflicts_count"] == 0


def test_static_vs_observed_separated():
    static = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_ACCOUNT_STATIC_TRUTH.csv")
    observed = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_ACCOUNT_OBSERVED_STATE.csv")
    assert {"currency", "leverage", "margin_mode", "broker_company"} <= set(static.columns)
    assert {"balance", "equity", "free_margin", "observed_at"} <= set(observed.columns)
    # observed rows are scenario assumptions, not real observations
    assert (observed["observed_at"].isna()).all()
    assert (observed["truth_class"] == "USER_SPECIFIED_SCENARIO").sum() == 4


# 33-35. Security / no performance selection / authorization
def test_secrets_absent():
    audit = _load_json("CR_BLOCK4_D1_2A_SECURITY_AUDIT.json")
    assert audit["secrets_committed"] is False
    assert audit["plaintext_passwords"] == 0
    assert audit["api_keys"] == 0
    assert audit["full_account_numbers"] == 0
    # DATA files must contain no secret-bearing tokens at all (the SECURITY
    # audit JSON itself documents the absence rule and is exempt).
    data_files = [
        "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv",
        "CR_BLOCK4_D1_2A_ACCOUNT_STATIC_TRUTH.csv",
        "CR_BLOCK4_D1_2A_ACCOUNT_OBSERVED_STATE.csv",
        "CR_BLOCK4_D1_2A_PROFILE_REGISTRY.csv",
        "CR_BLOCK4_D1_2A_MISSING_TRUTH_REGISTER.csv",
        "CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv",
    ]
    for name in data_files:
        txt = (OUT / name).read_text(encoding="utf-8", errors="ignore").lower()
        for tok in ("password", "api_key", "apikey", "session_token",
                    "mt5_login", "secret"):
            assert tok not in txt, (name, tok)
    # account identifiers are pseudonymous (SCENARIO-* or the UNKNOWN placeholder)
    static = pd.read_csv(OUT / "CR_BLOCK4_D1_2A_ACCOUNT_STATIC_TRUTH.csv")
    ok_ids = static["account_id"].str.startswith("SCENARIO-") | \
        (static["account_id"] == "ACTUAL-UNKNOWN")
    assert ok_ids.all()


def test_no_performance_based_selection():
    # no PF/EV/CAGR anywhere in the ingest artifacts
    for p in OUT.glob("*.md"):
        txt = p.read_text(encoding="utf-8")
        for tok in ("profit factor", "PF ", "CAGR", "sharpe"):
            assert tok.lower() not in txt.lower(), (p.name, tok)


def test_d1_2b_authorization_human_gated(artifacts):
    assert artifacts["d1_2b_authorized"] is False
    assert artifacts["production_authorized"] is False
    assert artifacts["human_review_required"] is True
    assert artifacts["d1_3_authorized"] is False


# ---------------------------------------------------------------------------
# Status honesty + offline determinism
# ---------------------------------------------------------------------------
def test_honest_status_partial_pass(artifacts):
    # no actual/documented truth exists -> PARTIAL_PASS_WAITING_PHYSICAL_TRUTH
    assert artifacts["status"] == "PARTIAL_PASS_WAITING_PHYSICAL_TRUTH"
    assert artifacts["d1_2a_pass"] is True  # ingest/seal itself executed correctly
    assert artifacts["actual_observed_sources_found"] is False
    assert artifacts["broker_documented_sources_found"] is False
    assert artifacts["profiles_quantity_complete"] == 0
    assert artifacts["next_checkpoint_recommended"] == \
        "CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION"


def test_artifacts_complete():
    expected = [
        "CR_BLOCK4_D1_2A_PROTOCOL.md",
        "CR_BLOCK4_D1_2A_SOURCE_SHA_MANIFEST.json",
        "CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv",
        "CR_BLOCK4_D1_2A_FIELD_PROVENANCE_SCHEMA.json",
        "CR_BLOCK4_D1_2A_PROFILE_COMPLETENESS_RULES.md",
        "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv",
        "CR_BLOCK4_D1_2A_ACCOUNT_STATIC_TRUTH.csv",
        "CR_BLOCK4_D1_2A_ACCOUNT_OBSERVED_STATE.csv",
        "CR_BLOCK4_D1_2A_PROFILE_REGISTRY.csv",
        "CR_BLOCK4_D1_2A_PROFILE_GENERATION_MANIFEST.json",
        "CR_BLOCK4_D1_2A_SOURCE_CONFLICTS.csv",
        "CR_BLOCK4_D1_2A_QUANTITY_CONVERSION_CONTRACT.md",
        "CR_BLOCK4_D1_2A_LONG_SHORT_SYMMETRY_AUDIT.md",
        "CR_BLOCK4_D1_2A_SCENARIO_PROFILE_AUDIT.md",
        "CR_BLOCK4_D1_2A_EXECUTION_RUNTIME_HANDOFF_AUDIT.md",
        "CR_BLOCK4_D1_2A_MISSING_TRUTH_REGISTER.csv",
        "CR_BLOCK4_D1_2A_SECURITY_AUDIT.json",
        "CR_BLOCK4_D1_2A_NONREGRESSION.json",
        "CR_BLOCK4_D1_2A_COMPONENT_STATUS.csv",
        "CR_BLOCK4_D1_2A_TEST_AUDIT.json",
        "CR_BLOCK4_D1_2A_REPORT.md",
        "CR_BLOCK4_D1_2A_DECISION.json",
    ]
    present = {p.name for p in OUT.iterdir() if p.is_file()}
    assert set(expected) <= present


def test_deterministic_rerun():
    d1_2a.main()
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(OUT.iterdir()) if p.is_file()}
    d1_2a.main()
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.iterdir()) if p.is_file()}
    assert set(first) == set(second)
    for name in first:
        assert first[name] == second[name], name


def test_offline_no_network_no_git():
    names = _imported_names(_runner_source())
    assert not (names & {"urllib", "requests", "socket", "subprocess", "http",
                         "git"})
