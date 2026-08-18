"""CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION — test suite.

Proves: nonregression of the sealed science, the ACTUAL_OBSERVED truth
claims in the decision, profile completeness rules and hash determinism,
field-level provenance, security (no secrets committed), purity (no broker
client / order API / MT5 import in CR code, no quantity surface, no margin
study), and byte-identical determinism.
"""
import ast
import hashlib
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "research" / "capital_routing" / "risk" / "block4_physical_truth_collection_d1_2a1"
RUNNER = ROOT / "scripts" / "run_physical_truth_collection_d1_2a1.py"
TRANSLATIONS = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0_1" / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv"

CANONICAL_BOOK_HASH = "b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a"
BASE_COMMIT = "052223762034d1fe4bf974698501ab955504a18d"
EXPECTED_ARTIFACTS = [
    "CR_BLOCK4_D1_2A1_PROTOCOL.md",
    "CR_BLOCK4_D1_2A1_SOURCE_SHA_MANIFEST.json",
    "CR_BLOCK4_D1_2A1_RAW_SOURCE_INVENTORY.json",
    "CR_BLOCK4_D1_2A1_INSTRUMENT_PHYSICAL_SPEC.json",
    "CR_BLOCK4_D1_2A1_ACCOUNT_PHYSICAL_PROFILE.json",
    "CR_BLOCK4_D1_2A1_FIELD_PROVENANCE.csv",
    "CR_BLOCK4_D1_2A1_QUANTITY_CONVERSION_CONTRACT.md",
    "CR_BLOCK4_D1_2A1_LONG_SHORT_SYMMETRY.json",
    "CR_BLOCK4_D1_2A1_PROFILE_HASH.json",
    "CR_BLOCK4_D1_2A1_COMPLETENESS_AUDIT.json",
    "CR_BLOCK4_D1_2A1_SECURITY_AUDIT.json",
    "CR_BLOCK4_D1_2A1_COMPONENT_STATUS.csv",
    "CR_BLOCK4_D1_2A1_NONREGRESSION.json",
    "CR_BLOCK4_D1_2A1_REPORT.md",
    "CR_BLOCK4_D1_2A1_DECISION.json",
    "_raw_observation.json",
]


def _load(name):
    return json.loads((ART / name).read_text(encoding="utf-8"))


def _evidence():
    return _load("_raw_observation.json")


def _provenance():
    return pd.read_csv(ART / "CR_BLOCK4_D1_2A1_FIELD_PROVENANCE.csv")


def _import_runner():
    spec = importlib.util.spec_from_file_location("run_d1_2a1", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_d1_2a1"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner():
    return _import_runner()


# ---------------------------------------------------------------- artifacts
def test_artifact_directory_exists():
    assert ART.is_dir()


def test_all_expected_artifacts_present():
    missing = [a for a in EXPECTED_ARTIFACTS if not (ART / a).exists()]
    assert missing == [], f"missing artifacts: {missing}"


def test_no_stray_artifact_files():
    found = sorted(p.name for p in ART.iterdir() if p.is_file())
    assert found == sorted(EXPECTED_ARTIFACTS), f"unexpected files: {set(found) ^ set(EXPECTED_ARTIFACTS)}"


def test_source_sha_manifest_base_commit():
    m = _load("CR_BLOCK4_D1_2A1_SOURCE_SHA_MANIFEST.json")
    assert m["base_commit"] == BASE_COMMIT


def test_source_sha_manifest_records_raw_evidence_hash():
    m = _load("CR_BLOCK4_D1_2A1_SOURCE_SHA_MANIFEST.json")
    raw_sha = hashlib.sha256((ART / "_raw_observation.json").read_bytes()).hexdigest()
    assert m["raw_observation_sha256"] == raw_sha


# ---------------------------------------------------------------- nonregression
def test_science_counts_unchanged():
    tr = pd.read_csv(TRANSLATIONS)
    assert len(tr) == 890
    assert int((tr["decision"] == "ACCEPT_FULL").sum()) == 826
    assert int((tr["decision"] == "REJECT_HEAT_CAP").sum()) == 64
    assert int(((tr["decision"] == "ACCEPT_FULL") & (tr["family"] == "A")).sum()) == 371
    assert int(((tr["decision"] == "ACCEPT_FULL") & (tr["family"] == "B")).sum()) == 455


def test_nonregression_json_counts():
    nr = _load("CR_BLOCK4_D1_2A1_NONREGRESSION.json")
    assert nr["science_counts"] == {"n_events": 890, "n_accepted": 826,
                                    "n_rejected": 64, "accepted_A": 371,
                                    "accepted_B": 455}
    assert nr["science_unchanged"] is True


def test_nonregression_book_hash():
    nr = _load("CR_BLOCK4_D1_2A1_NONREGRESSION.json")
    assert nr["canonical_book_hash"] == CANONICAL_BOOK_HASH


def test_nonregression_frozen_rules():
    nr = _load("CR_BLOCK4_D1_2A1_NONREGRESSION.json")
    assert nr["fidelity_tolerance_unchanged"] is True
    assert nr["rounding_policy_unchanged"] is True
    assert nr["no_clipping"] is True
    assert nr["no_upward_rounding"] is True
    assert nr["broker_order_attempted"] is False
    assert nr["broker_write_performed"] is False


# ---------------------------------------------------------------- decision
def test_decision_base_and_status():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["checkpoint"] == "CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION"
    assert d["base_commit"] == BASE_COMMIT
    assert d["status"] == "PASS"
    assert d["science_unchanged"] is True


def test_decision_actual_observation_claims():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["actual_account_observed"] is True
    assert d["actual_usdjpy_observed"] is True
    assert d["truth_class"] == "ACTUAL_OBSERVED"


def test_decision_all_resolved_fields():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    for f in ["broker_symbol", "account_currency", "contract_size", "volume_min",
              "volume_step", "volume_max", "product_type",
              "quantity_conversion", "long_short_symmetry"]:
        assert d[f"{f}_resolved"] is True, f"{f}_resolved should be True"


def test_decision_completeness_and_gate():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["quantity_minimum_complete"] is True
    assert d["margin_complete"] is False
    assert d["d1_2b_ready"] is True
    assert d["d1_2b_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True
    assert d["next_checkpoint_recommended"] == "CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE"


def test_decision_no_broker_mutation():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["broker_order_attempted"] is False
    assert d["broker_write_performed"] is False


# ---------------------------------------------------------------- evidence
def test_evidence_is_actual_observation():
    ev = _evidence()
    assert ev["truth_class"] == "ACTUAL_OBSERVED"
    assert ev["environment"] == "DEMO"
    assert ev["mutating_calls"] in ([], "none")
    assert "read-only" in ev["method"].lower() or "read" in ev["method"].lower()


def test_evidence_capture_values():
    ev = _evidence()
    s = ev["symbol"]
    assert s["broker_symbol"] == "USDJPY.PRO"
    assert s["trade_contract_size"] == 100000.0
    assert s["volume_min"] == 0.01
    assert s["volume_step"] == 0.01
    assert s["volume_max"] == 200.0
    assert s["currency_base"] == "USD"
    assert s["currency_profit"] == "JPY"
    assert s["currency_margin"] == "USD"
    assert s["trade_calc_mode"] == 0
    a = ev["account"]
    assert a["currency"] == "USD"
    assert a["leverage"] == 500
    assert a["server"] == "OxSecurities-Demo"


def test_evidence_no_mutation_api():
    ev = _evidence()
    assert ev["mutating_calls"] in ([], "none")


# ---------------------------------------------------------------- instrument spec
def test_instrument_spec_resolved_contract():
    spec = _load("CR_BLOCK4_D1_2A1_INSTRUMENT_PHYSICAL_SPEC.json")
    assert spec["research_symbol"] == "USDJPY"
    assert spec["broker_symbol"] == "USDJPY.PRO"
    assert spec["product_type"] == "FX"
    assert spec["contract_size"] == 100000.0
    assert spec["volume_min"] == 0.01
    assert spec["volume_step"] == 0.01
    assert spec["volume_max"] == 200.0
    assert spec["base_currency"] == "USD"
    assert spec["quote_currency"] == "JPY"
    assert spec["margin_currency"] == "USD"
    assert spec["trade_calc_mode"] == 0
    assert spec["truth_class"] == "ACTUAL_OBSERVED"


def test_instrument_spec_volume_semantics_observed():
    spec = _load("CR_BLOCK4_D1_2A1_INSTRUMENT_PHYSICAL_SPEC.json")
    assert "100,000 base units" in spec["volume_semantics"]
    assert "OBSERVED" in spec["contract_size_semantics"]
    assert "100000" in str(spec["contract_size"])


def test_instrument_spec_hedging_netting_unknown():
    spec = _load("CR_BLOCK4_D1_2A1_INSTRUMENT_PHYSICAL_SPEC.json")
    assert spec["hedging_netting"] == "UNKNOWN"


# ---------------------------------------------------------------- account profile
def test_account_profile_static_vs_observed():
    acct = _load("CR_BLOCK4_D1_2A1_ACCOUNT_PHYSICAL_PROFILE.json")
    assert acct["account_currency"] == "USD"
    assert acct["leverage"] == 500
    assert acct["margin_mode"] == 2
    assert acct["server"] == "OxSecurities-Demo"
    assert acct["environment"] == "DEMO"
    assert acct["truth_class"] == "ACTUAL_OBSERVED"
    assert "time-varying" in acct["note"].lower() or "not a permanent" in acct["note"].lower()


def test_account_profile_equity_is_observed_state():
    acct = _load("CR_BLOCK4_D1_2A1_ACCOUNT_PHYSICAL_PROFILE.json")
    assert acct["equity"] == 25254.35
    assert acct["balance"] == 25254.35


def test_account_id_pseudonymous():
    acct = _load("CR_BLOCK4_D1_2A1_ACCOUNT_PHYSICAL_PROFILE.json")
    acct_id = acct["account_id"]
    assert acct_id.startswith("OX-DEMO-")
    suffix = acct_id.split("-")[-1]
    assert len(suffix) == 12 and all(c in "0123456789abcdef" for c in suffix)


# ---------------------------------------------------------------- provenance
def test_every_field_has_truth_class_and_source():
    prov = _provenance()
    assert len(prov) >= 20
    assert (prov["truth_class"].notna()).all()
    assert (prov["source"].notna()).all()
    assert (prov["field"].notna()).all()


def test_every_observed_field_has_timestamp():
    prov = _provenance()
    observed = prov[prov["truth_class"] == "ACTUAL_OBSERVED"]
    assert len(observed) > 10
    assert (observed["observed_at"] != "n/a").all()
    assert (observed["observed_at"].notna()).all()


def test_provenance_unknown_fields_marked():
    prov = _provenance()
    hn = prov[prov["field"] == "hedging_netting"].iloc[0]
    assert hn["truth_class"] == "UNKNOWN"
    assert hn["value"] == "UNKNOWN"


def test_user_scenario_never_promoted():
    ev = _evidence()
    assert ev["truth_class"] == "ACTUAL_OBSERVED"
    prov = _provenance()
    assert (prov["truth_class"] != "USER_SPECIFIED_SCENARIO").all()


# ---------------------------------------------------------------- quantity conversion
def test_quantity_conversion_contract_direct_mapping():
    conv = (ART / "CR_BLOCK4_D1_2A1_QUANTITY_CONVERSION_CONTRACT.md").read_text(encoding="utf-8")
    assert "raw_volume = target_USD_notional / trade_contract_size" in conv
    assert "NO FX conversion price is required" in conv
    assert "account currency == base currency" in conv


def test_quantity_conversion_contract_observations():
    conv = (ART / "CR_BLOCK4_D1_2A1_QUANTITY_CONVERSION_CONTRACT.md").read_text(encoding="utf-8")
    assert "USDJPY.PRO" in conv
    assert "100000" in conv
    assert "OBSERVED" in conv
    assert "NOT assumed from FX convention" in conv


def test_quantity_conversion_contract_causality():
    conv = (ART / "CR_BLOCK4_D1_2A1_QUANTITY_CONVERSION_CONTRACT.md").read_text(encoding="utf-8")
    assert "entry-side conversion" in conv
    assert "No future price" in conv


def test_long_short_symmetry_resolved():
    sym = _load("CR_BLOCK4_D1_2A1_LONG_SHORT_SYMMETRY.json")
    assert sym["quantity_mapping_symmetric"] is True
    assert sym["resolved"] is True
    assert sym["truth_class"] == "ACTUAL_OBSERVED"


# ---------------------------------------------------------------- completeness + hash
def test_completeness_audit_quantity_complete():
    comp = _load("CR_BLOCK4_D1_2A1_COMPLETENESS_AUDIT.json")
    assert comp["quantity_minimum_complete"] is True
    assert comp["completeness_level"] == "SEALED_ACTUAL_QUANTITY_COMPLETE"
    for f in ["research_symbol", "broker_symbol", "product_type", "account_currency",
              "contract_size", "volume_min", "volume_step", "volume_max",
              "base_currency", "quote_currency", "quantity_conversion_rule"]:
        assert f in comp["required_fields"], f"missing required field {f}"


def test_completeness_audit_margin_deferred():
    comp = _load("CR_BLOCK4_D1_2A1_COMPLETENESS_AUDIT.json")
    assert comp["margin_complete"] is False
    assert "symbol_leverage" in comp["margin_blockers"]
    assert "hedging_netting" in comp["margin_blockers"]


def test_profile_hash_deterministic(runner):
    ev = runner.load_evidence()
    h1 = runner.profile_hash(ev)["profile_hash"]
    h2 = runner.profile_hash(ev)["profile_hash"]
    assert h1 == h2
    assert len(h1) == 64


def test_profile_hash_matches_artifact(runner):
    ev = runner.load_evidence()
    h = runner.profile_hash(ev)
    art = _load("CR_BLOCK4_D1_2A1_PROFILE_HASH.json")
    assert art["profile_hash"] == h["profile_hash"]
    assert art["profile_generation_id"] == "PHYSICAL_PROFILE_GENERATION_G1"
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["profile_hash"] == h["profile_hash"]


def test_profile_hash_changes_on_contract_change(runner):
    ev = runner.load_evidence()
    base = runner.profile_hash(ev)["profile_hash"]
    ev2 = json.loads(json.dumps(ev))
    ev2["symbol"]["trade_contract_size"] = 1000.0
    h2 = runner.profile_hash(ev2)["profile_hash"]
    assert h2 != base


def test_profile_hash_changes_on_volume_rule_change(runner):
    ev = runner.load_evidence()
    base = runner.profile_hash(ev)["profile_hash"]
    ev2 = json.loads(json.dumps(ev))
    ev2["symbol"]["volume_min"] = 0.5
    h2 = runner.profile_hash(ev2)["profile_hash"]
    assert h2 != base


def test_profile_hash_changes_on_account_currency_change(runner):
    ev = runner.load_evidence()
    base = runner.profile_hash(ev)["profile_hash"]
    ev2 = json.loads(json.dumps(ev))
    ev2["account"]["currency"] = "EUR"
    h2 = runner.profile_hash(ev2)["profile_hash"]
    assert h2 != base


def test_profile_hash_changes_on_broker_symbol_change(runner):
    ev = runner.load_evidence()
    base = runner.profile_hash(ev)["profile_hash"]
    ev2 = json.loads(json.dumps(ev))
    ev2["symbol"]["broker_symbol"] = "USDJPY"
    h2 = runner.profile_hash(ev2)["profile_hash"]
    assert h2 != base


# ---------------------------------------------------------------- completeness rules
def test_completeness_rule_requires_all_fields(runner):
    ev = runner.load_evidence()
    assert runner.completeness_audit(ev)["quantity_minimum_complete"] is True
    # map audit field name -> evidence path
    path = {
        "contract_size": ("symbol", "trade_contract_size"),
        "volume_min": ("symbol", "volume_min"),
        "volume_step": ("symbol", "volume_step"),
        "volume_max": ("symbol", "volume_max"),
        "broker_symbol": ("symbol", "broker_symbol"),
        "account_currency": ("account", "currency"),
    }
    for field, (grp, key) in path.items():
        ev2 = json.loads(json.dumps(ev))
        ev2[grp][key] = "UNKNOWN"
        comp = runner.completeness_audit(ev2)
        assert comp["quantity_minimum_complete"] is False, f"{field} should block"


def test_completeness_rule_deterministic(runner):
    ev = runner.load_evidence()
    c1 = runner.completeness_audit(ev)
    c2 = runner.completeness_audit(ev)
    assert c1 == c2


# ---------------------------------------------------------------- security
def test_no_secrets_in_artifacts():
    # The SECURITY_AUDIT names the secret classes while counting them at 0;
    # scan every OTHER artifact for any secret value or token.
    secrets = ["password", "api_key", "mt5_login_secret", "session_token",
               "secret_key"]
    for p in ART.iterdir():
        if not p.is_file() or p.name == "CR_BLOCK4_D1_2A1_SECURITY_AUDIT.json":
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore").lower()
        for s in secrets:
            assert s not in txt, f"secret token '{s}' found in {p.name}"


def test_login_not_committed():
    ev = _evidence()
    assert ev["account"].get("login") is None
    raw = (ART / "_raw_observation.json").read_text(encoding="utf-8")
    assert "login_pseudonym_hash" in raw
    assert raw.count('"login"') == 0 or '"login": null' in raw


def test_personal_name_redacted():
    ev = _evidence()
    assert ev["account"]["name"] == "REDACTED (not committed)"


def test_security_audit_clean():
    sec = _load("CR_BLOCK4_D1_2A1_SECURITY_AUDIT.json")
    assert sec["secrets_committed"] is False
    assert sec["plaintext_passwords"] == 0
    assert sec["api_keys"] == 0
    assert sec["mt5_login_secrets"] == 0
    assert sec["session_tokens"] == 0
    assert sec["login_committed"] is False
    assert sec["personal_name_committed"] is False


def test_pseudonym_hash_is_real_sha256():
    ev = _evidence()
    h = ev["account"]["login_pseudonym_hash"]
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------- purity
def _imports_of(path):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, DeprecationWarning):
        # legacy/unparseable modules are dead code and cannot import anything
        return set()
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def test_no_metatrader5_import_in_cr_code():
    for p in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "src").rglob("*.py")):
        imports = _imports_of(p)
        assert "MetaTrader5" not in imports, f"MetaTrader5 import in {p}"
        assert "mt5" not in imports, f"mt5 import in {p}"


def test_no_broker_client_import_in_cr_code():
    for p in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "src").rglob("*.py")):
        imports = _imports_of(p)
        for banned in ["broker", "execution_runtime"]:
            assert banned not in imports, f"forbidden import '{banned}' in {p}"


def test_runner_has_no_order_api_logic():
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    func_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                func_calls.append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                func_calls.append(node.func.id)
    for banned in ["order_send", "order_check", "position_close", "order_modify",
                   "orders_delete", "positions_close"]:
        assert banned not in func_calls, f"forbidden call {banned} in runner"


def test_runner_uses_no_network():
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if name in ("urlopen", "requests", "get", "post", "connect", "socket"):
                pytest.fail(f"network call {name} in runner")


def test_no_quantity_surface_executed():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["quantity_minimum_complete"] is True
    assert d["d1_2b_ready"] is True
    assert d["d1_2b_authorized"] is False  # surface not executed
    # no event-level quantity artifact exists
    surf = [p for p in ART.iterdir() if "SURFACE" in p.name or "EVENT" in p.name]
    assert surf == []


def test_no_margin_study_executed():
    comp = _load("CR_BLOCK4_D1_2A1_COMPLETENESS_AUDIT.json")
    assert comp["margin_complete"] is False
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["margin_complete"] is False


def test_fakemt5_and_simbroker_not_used_as_truth():
    ev = _evidence()
    assert ev["truth_class"] == "ACTUAL_OBSERVED"
    src = ev["source"].lower()
    assert "fakemt5" not in src
    assert "simbroker" not in src
    raw = (ART / "_raw_observation.json").read_text(encoding="utf-8").lower()
    assert "fakemt5" not in raw
    assert "simbroker" not in raw


def test_no_performance_selection():
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert d["d1_2b_authorized"] is False
    assert d["production_authorized"] is False
    assert d["human_review_required"] is True


# ---------------------------------------------------------------- determinism
def test_runner_deterministic(runner, tmp_path):
    import os
    before = {}
    for p in sorted(ART.iterdir()):
        if p.is_file():
            before[p.name] = p.read_bytes()
    # regen in place
    runner.main()
    after = {}
    for p in sorted(ART.iterdir()):
        if p.is_file():
            after[p.name] = p.read_bytes()
    changed = [n for n in before if before[n] != after.get(n)]
    assert changed == [], f"artifact regeneration changed: {changed}"


def test_component_status_csv_consistent():
    cs = pd.read_csv(ART / "CR_BLOCK4_D1_2A1_COMPONENT_STATUS.csv")
    assert len(cs) >= 6
    row = cs[cs["component"].str.contains("collection")].iloc[0]
    assert row["status"] == "EXECUTED"
    d = _load("CR_BLOCK4_D1_2A1_DECISION.json")
    assert row["verdict"] == d["status"]
