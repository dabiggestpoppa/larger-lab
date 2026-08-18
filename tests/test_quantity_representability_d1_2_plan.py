"""
CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN
tests — plan / preregistration integrity (Lane B).

Proves the D1.2 PLAN is a valid preregistration:

  - D1.1A PASS verified; 890/826/371/455/64 and the D1.1 grid unchanged
  - same canonical book hash; D1 descriptive quantiles vs D1.1 rank bin edges
    kept distinct
  - physical profiles carry truth classes; user-supplied leverage is
    USER_SPECIFIED_SCENARIO; account size distinct from leverage
  - Lane B (quantity) distinct from Lane C (margin); EconomicTarget distinct
    from broker quantity
  - min/max quantity BLOCK by default; clipping / upward rounding / multi-
    ticket split default false; primary rounding toward zero; nearest is
    comparator only
  - fidelity metrics defined; materiality tolerance preregistered
  - account-size scenarios frozen; instrument/account schemas immutable +
    hashable; runtime handoff schema defined
  - no broker client, no execution API, no MT5 import, no order logic, no
    margin engine, no performance-based profile selection
  - missing truth blocks empirical D1.2; production authorization false
  - offline and deterministic

No empirical quantity study exists yet and none is run here.
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

import run_quantity_representability_d1_2_plan as d1_2  # noqa: E402

OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_quantity_representability_d1_2_plan"
BOOK_HASH = "b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a"


def _load_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def artifacts():
    return d1_2.main()


def _runner_source() -> str:
    return (ROOT / "scripts" / "run_quantity_representability_d1_2_plan.py").read_text(
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


# 1-4. Frozen science + D1.1 truth
def test_d1_1a_pass_verified(artifacts):
    assert artifacts["d1_1a_pass_verified"] is True
    assert artifacts["status"] == "PASS"


def test_counts_frozen(artifacts):
    assert artifacts["n_events"] == 890
    assert artifacts["n_accepted"] == 826
    assert artifacts["accepted_A"] == 371
    assert artifacts["accepted_B"] == 455
    assert artifacts["science_unchanged"] is True


def test_d1_1_grid_unchanged():
    facts = d1_2.verify_frozen_facts()
    assert facts["grid_replication_pass"] is True
    assert facts["verified"] is True


def test_same_canonical_book_hash(artifacts):
    assert artifacts["canonical_book_hash"] == BOOK_HASH
    facts = d1_2.verify_frozen_facts()
    assert facts["canonical_book_hash"] == BOOK_HASH


def test_quantile_definitions_kept_distinct():
    # D1 descriptive vs D1.1 rank bin edges remain separately named
    quant_doc = (OUT / "CR_BLOCK4_D1_2_QUANTILE_DISTORTION_PLAN.md").read_text(
        encoding="utf-8")
    assert "RANK_BIN_EDGE" in quant_doc
    assert "DESCRIPTIVE_DISTRIBUTION_QUANTILE" in quant_doc
    assert "NOT recomputed" in quant_doc


# 5-8. Truth classes + profiles
def test_profiles_carry_truth_class():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv")
    assert len(reg) == 4
    assert (reg["truth_class"] == "USER_SPECIFIED_SCENARIO").all()


def test_no_profile_silently_actual():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv")
    assert "ACTUAL_OBSERVED" not in reg["truth_class"].values
    assert "BROKER_DOCUMENTED" not in reg["truth_class"].values
    for pid in ("PROP_25K_L50_SCENARIO", "PROP_25K_L100_SCENARIO",
                "PROP_25K_L500_SCENARIO", "OX_SMALL_L1000_SCENARIO"):
        assert pid in set(reg["profile_id"])


def test_user_leverage_labeled_user_specified():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv")
    lev = reg.set_index("profile_id")["leverage"].to_dict()
    assert lev["PROP_25K_L50_SCENARIO"] == "1:50"
    assert lev["PROP_25K_L100_SCENARIO"] == "1:100"
    assert lev["PROP_25K_L500_SCENARIO"] == "1:500"
    assert lev["OX_SMALL_L1000_SCENARIO"].startswith("up to 1:1000")
    hierarchy = (OUT / "CR_BLOCK4_D1_2_TRUTH_HIERARCHY.md").read_text(encoding="utf-8")
    assert "USER_SPECIFIED_SCENARIO" in hierarchy
    assert "NOT ACTUAL_OBSERVED" in hierarchy


def test_account_size_distinct_from_leverage():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv")
    assert "equity" in reg.columns and "leverage" in reg.columns
    # OX profile: equity UNRESOLVED while leverage is user-specified
    ox = reg[reg["profile_id"] == "OX_SMALL_L1000_SCENARIO"].iloc[0]
    assert ox["equity"] == "UNRESOLVED"
    assert ox["leverage"].startswith("up to 1:1000")


# 9-10. Lane separation
def test_lane_b_distinct_from_margin_lane_c(artifacts):
    assert artifacts["lane_b_defined"] is True
    assert artifacts["lane_c_excluded"] is True
    assert artifacts["margin_engine_added"] is False
    states = _load_json("CR_BLOCK4_D1_2_FEASIBILITY_STATE_SCHEMA.json")
    prim = states["primary_states"]
    assert "MARGIN_BLOCKED" not in prim
    assert "BUYING_POWER_BLOCKED" not in prim
    assert "MIN_QUANTITY_BLOCKED" in prim
    assert "MAX_QUANTITY_BLOCKED" in prim


def test_economic_target_distinct_from_broker_quantity():
    q = (OUT / "CR_BLOCK4_D1_2_SCIENTIFIC_QUESTION.md").read_text(encoding="utf-8")
    assert "EconomicTarget" in q
    assert "broker-native quantity" in q or "broker quantity" in q
    flat = q.replace("\n", " ")
    assert "scientific exposure" in q
    assert "silently treating" in flat or "faithfully" in flat


# 11-18. Rounding / fidelity
def test_min_quantity_default_block(artifacts):
    assert artifacts["min_quantity_default_block"] is True
    assert d1_2.MIN_QUANTITY_DEFAULT == "MIN_QUANTITY_BLOCKED"
    rp = (OUT / "CR_BLOCK4_D1_2_ROUNDING_POLICY.md").read_text(encoding="utf-8")
    assert "MIN_QUANTITY_BLOCKED" in rp


def test_max_quantity_default_block(artifacts):
    assert artifacts["max_quantity_default_block"] is True
    assert d1_2.MAX_QUANTITY_DEFAULT == "MAX_QUANTITY_BLOCKED"


def test_clipping_default_false(artifacts):
    assert artifacts["clipping_default"] is False
    assert d1_2.CLIPPING_DEFAULT is False


def test_upward_rounding_default_false(artifacts):
    assert artifacts["upward_rounding_default"] is False
    assert d1_2.UPWARD_ROUNDING_DEFAULT is False


def test_primary_rounding_toward_zero():
    assert d1_2.ROUNDING_PRIMARY == "ROUND_DOWN_TOWARD_ZERO"
    rp = (OUT / "CR_BLOCK4_D1_2_ROUNDING_POLICY.md").read_text(encoding="utf-8")
    assert "floor_toward_zero" in rp
    assert "never exceeds the approved target" in rp


def test_nearest_comparator_only():
    assert d1_2.ROUNDING_COMPARATOR == "NEAREST_STEP"
    doc = (OUT / "CR_BLOCK4_D1_2_ROUNDING_POLICY.md").read_text(encoding="utf-8")
    assert "diagnostic only" in doc


def test_relative_exposure_error_defined():
    fm = (OUT / "CR_BLOCK4_D1_2_FIDELITY_METRICS.md").read_text(encoding="utf-8")
    for tok in ("relative_exposure_error", "exposure_ratio",
                "signed_exposure_error", "represented_notional"):
        assert tok in fm


def test_tolerance_preregistered(artifacts):
    assert artifacts["rounding_tolerance_preregistered"] is True
    fm = (OUT / "CR_BLOCK4_D1_2_FIDELITY_METRICS.md").read_text(encoding="utf-8")
    assert "1%" in fm  # immaterial band (rendered from 0.01)
    assert "preregistered" in fm
    assert "never chosen from performance" in fm or "independent of PF/EV" in fm


# 19-21. Account sizes + immutability
def test_account_size_scenarios_frozen():
    ap = (OUT / "CR_BLOCK4_D1_2_ACCOUNT_SIZE_PLAN.md").read_text(encoding="utf-8")
    for size in ("5,000", "10,000", "25,000", "50,000", "100,000"):
        assert size in ap


def test_instrument_spec_immutable_hashable():
    spec = _load_json("CR_BLOCK4_D1_2_INSTRUMENT_SPEC_SCHEMA.json")
    assert spec["$id"].endswith("instrument-spec")
    assert spec["required"] == ["research_symbol", "broker_symbol", "product_type",
                                "contract_size", "volume_min", "volume_step",
                                "volume_max", "base_currency", "quote_currency",
                                "truth_class", "source"]
    # a profile hashes instrument_spec_hash; changing spec requires new generation
    prof = _load_json("CR_BLOCK4_D1_2_PHYSICAL_PROFILE_SCHEMA.json")
    assert "instrument_spec_hash" in [f["name"] for f in prof["fields"]]
    assert "No silent mutable profile" in prof["rule"]


def test_account_profile_immutable_hashable():
    prof = _load_json("CR_BLOCK4_D1_2_ACCOUNT_PROFILE_SCHEMA.json")
    assert prof["$id"].endswith("account-profile")
    names = [f["name"] for f in prof["fields"]]
    for f in ("account_id", "equity", "account_currency", "leverage",
              "hedging_netting", "truth_class", "source"):
        assert f in names


# 22. Runtime handoff
def test_runtime_handoff_schema_defined():
    h = (OUT / "CR_BLOCK4_D1_2_RUNTIME_HANDOFF_CONTRACT.md").read_text(encoding="utf-8")
    assert "InstrumentPhysicalSpec" in h
    assert "AccountPhysicalProfile" in h
    assert "contract_size" in h and "volume_min" in h and "volume_step" in h
    assert "volume_max" in h and "broker_symbol" in h
    assert "Capital Routing must NOT build a broker client" in h


# 23-26. Purity
def test_no_broker_client():
    names = _imported_names(_runner_source())
    assert not (names & {"broker", "mt5", "tradelocker"})
    # executable code (docstring stripped) must not contain broker-client logic.
    # NB: "MT5 / other transport unresolved" appears as SCHEMA DATA (recording
    # an unresolved field), which is required, not broker logic.
    import ast as _ast
    src = _runner_source()
    tree = _ast.parse(src)
    doc = _ast.get_docstring(tree)
    code = src.replace(doc, "") if doc else src
    assert "import broker" not in code
    assert "import mt5" not in code.lower()
    assert "from mt5" not in code.lower()
    assert "import tradelocker" not in code.lower()


def test_no_execution_api():
    names = _imported_names(_runner_source())
    assert not (names & {"execution_runtime", "brokersession"})


def test_no_mt5_import():
    assert "mt5" not in _imported_names(_runner_source())


def test_no_order_logic():
    src = _runner_source()
    assert "send_order" not in src
    assert "place_order" not in src
    assert "order_ticket" not in src
    dec = _load_json("CR_BLOCK4_D1_2_DECISION.json")
    assert dec["execution_logic_added"] is False


# 27-28. No performance selection; margin deferred
def test_no_performance_based_profile_selection():
    dec = _load_json("CR_BLOCK4_D1_2_DECISION.json")
    assert dec["d1_2_plan_pass"] is True
    q = (OUT / "CR_BLOCK4_D1_2_SCIENTIFIC_QUESTION.md").read_text(encoding="utf-8")
    assert "never" in q.lower()
    cf = (OUT / "CR_BLOCK4_D1_2_COUNTERFACTUAL_PLAN.md").read_text(encoding="utf-8")
    assert "ALTERED_BOOK_DIAGNOSTIC" in cf
    assert "never" in cf and "equivalent" in cf
    assert "never treated as equivalent" in cf.replace("\n", " ")


def test_d1_3_margin_deferred():
    seq = (OUT / "CR_BLOCK4_D1_2_IMPLEMENTATION_SEQUENCE.md").read_text(encoding="utf-8")
    assert "D1.3" in seq
    assert "D1.2A" in seq and "D1.2B" in seq
    assert "D1.2A must precede D1.2B" in seq
    dec = _load_json("CR_BLOCK4_D1_2_DECISION.json")
    assert dec["d1_3_authorized"] is False
    assert dec["margin_engine_added"] is False


# 29-30. Missing truth blocks empirical; authorization false
def test_missing_truth_blocks_empirical():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_2_MISSING_TRUTH_REGISTER.csv")
    assert len(reg) >= 12
    assert (reg["blocking_for_d1_2_empirical"] == "yes").all()
    dec = _load_json("CR_BLOCK4_D1_2_DECISION.json")
    assert dec["missing_truth_register_complete"] is True
    assert dec["d1_2_empirical_ready"] is False
    assert dec["d1_2_empirical_authorized"] is False
    proto = (OUT / "CR_BLOCK4_D1_2_PROTOCOL.md").read_text(encoding="utf-8")
    assert "BLOCKED" in proto


def test_production_authorization_false(artifacts):
    assert artifacts["production_authorized"] is False
    assert artifacts["human_review_required"] is True
    assert artifacts["next_checkpoint_recommended"] == "CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL"


# ---------------------------------------------------------------------------
# Extras: schema completeness + offline determinism
# ---------------------------------------------------------------------------
def test_instrument_spec_no_generic_fx_defaults():
    spec = _load_json("CR_BLOCK4_D1_2_INSTRUMENT_SPEC_SCHEMA.json")
    assert "NO generic FX defaults" in spec["description"]
    assert "HYPOTHETICAL_DIAGNOSTIC_PROFILE" in spec["description"]


def test_feasibility_states_closed_set():
    states = _load_json("CR_BLOCK4_D1_2_FEASIBILITY_STATE_SCHEMA.json")
    assert states["fail_closed_default"] == "OTHER_FAIL_CLOSED"
    assert "ROUNDING_DISTORTED" in states["primary_states"]
    assert "REPRESENTABLE_WITH_IMMATERIAL_ROUNDING" in states["primary_states"]
    for u in ("BROKER_SYMBOL_UNRESOLVED", "CONTRACT_SIZE_UNRESOLVED",
              "VOLUME_RULE_UNRESOLVED", "ACCOUNT_CURRENCY_UNRESOLVED",
              "CURRENCY_CONVERSION_UNRESOLVED", "ACCOUNT_PROFILE_UNRESOLVED"):
        assert u in states["primary_states"]


def test_artifacts_complete():
    expected = [
        "CR_BLOCK4_D1_2_PROTOCOL.md",
        "CR_BLOCK4_D1_2_SOURCE_SHA_MANIFEST.json",
        "CR_BLOCK4_D1_2_SCIENTIFIC_QUESTION.md",
        "CR_BLOCK4_D1_2_TRUTH_HIERARCHY.md",
        "CR_BLOCK4_D1_2_PHYSICAL_PROFILE_SCHEMA.json",
        "CR_BLOCK4_D1_2_INSTRUMENT_SPEC_SCHEMA.json",
        "CR_BLOCK4_D1_2_ACCOUNT_PROFILE_SCHEMA.json",
        "CR_BLOCK4_D1_2_RUNTIME_HANDOFF_CONTRACT.md",
        "CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv",
        "CR_BLOCK4_D1_2_QUANTITY_PIPELINE.md",
        "CR_BLOCK4_D1_2_ROUNDING_POLICY.md",
        "CR_BLOCK4_D1_2_FIDELITY_METRICS.md",
        "CR_BLOCK4_D1_2_FEASIBILITY_STATE_SCHEMA.json",
        "CR_BLOCK4_D1_2_ACCOUNT_SIZE_PLAN.md",
        "CR_BLOCK4_D1_2_CURRENCY_CONVERSION_PLAN.md",
        "CR_BLOCK4_D1_2_FAMILY_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_2_POS_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_2_QUANTILE_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_2_SUBPERIOD_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_2_COUNTERFACTUAL_PLAN.md",
        "CR_BLOCK4_D1_2_MISSING_TRUTH_REGISTER.csv",
        "CR_BLOCK4_D1_2_IMPLEMENTATION_SEQUENCE.md",
        "CR_BLOCK4_D1_2_TEST_PLAN.md",
        "CR_BLOCK4_D1_2_COMPONENT_STATUS.csv",
        "CR_BLOCK4_D1_2_REPORT.md",
        "CR_BLOCK4_D1_2_DECISION.json",
    ]
    present = {p.name for p in OUT.iterdir() if p.is_file()}
    assert set(expected) <= present


def test_deterministic_rerun():
    d1_2.main()
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(OUT.iterdir()) if p.is_file()}
    d1_2.main()
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.iterdir()) if p.is_file()}
    assert set(first) == set(second)
    for name in first:
        assert first[name] == second[name], name


def test_offline_no_network_no_git():
    names = _imported_names(_runner_source())
    assert not (names & {"urllib", "requests", "socket", "subprocess", "http",
                         "git"})
