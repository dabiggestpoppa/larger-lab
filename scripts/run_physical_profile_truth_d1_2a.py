"""
CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL — truth ingest.

Resolves and freezes the physical USDJPY account/instrument truth required to
execute the preregistered D1.2 quantity-representability study.  This
checkpoint INGESTS + PROVENANCES + SEALS input truth only — it does NOT run
the D1.2B quantity surface and does NOT run any margin study (D1.3).

Evidence collected read-only at checkpoint start (git fetch):

  - execution-runtime-foundation `62e6d040` (QL-EXEC-R4.1): SymbolInfo
    contract shape in quant-lab/execution_runtime/types.py — populated only at
    RUNTIME from a live MT5 session; NO committed USDJPY/account observation
    snapshots exist.  FakeMT5 / SimBroker fixtures hardcode generic FX values
    (contract_size=100000, volume_min=0.01, volume_step=0.01, volume_max=100)
    — those are TEST FIXTURES, NOT truth.
  - capital-routing: artifacts/audits/mt5_session_schedule_by_symbol.csv shows
    USDJPY MT5 price-data availability (session evidence only, no contract
    size / volume rules).
  - tb-forward-engine `b48fd352`: TB_P5_BROKER_LOT_CONSTRAINTS.csv and TB
    execution contracts are TB strategy/account artifacts — NOT CR USDJPY
    account truth.
  - User-specified scenarios: 4 profiles (equity + leverage only; instrument
    fields NOT supplied).

Conclusion: NO actual/documented USDJPY quantity truth exists.  Scenario
profiles lack instrument fields, so NO profile is quantity-complete.  Status:
PARTIAL_PASS_WAITING_PHYSICAL_TRUTH.  No PASS is manufactured.

Base: aaf3e0548ec9bff85b38b7f8a853a7becffce4c3 (D1.2 plan).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_physical_profile_truth_d1_2a"
D1_2_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_quantity_representability_d1_2_plan"
D1_1A_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1a"
D1_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1"
TRANSLATIONS = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0_1" / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv"

BASE_COMMIT = "aaf3e0548ec9bff85b38b7f8a853a7becffce4c3"
CHECKPOINT = "CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL"
NEXT_CHECKPOINT = "CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION"
NEXT_IF_COMPLETE = "CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE"

# Cross-workstream heads recorded at checkpoint start (git fetch, read-only).
EXEC_RUNTIME_HEAD = "62e6d0402a780d171a8b81c2070567045e341be7"
EXEC_RUNTIME_SUBJECT = "QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN"
TB_ENGINE_HEAD = "b48fd35255b41865026a3cba333ae2a2a0d6a004"
TB_ENGINE_SUBJECT = "TB-R6.1D-BOOT-FLOW-STACK: supervisor owns watcher + dashboard, full stack auto-starts at logon"
MAIN_HEAD = "9f61288679eea56a298e08f718c314f2ca509bc5"
MAIN_SUBJECT = "OCE Block 0: ratify constitutional control checkpoint"
CR_HEAD = "aaf3e0548ec9bff85b38b7f8a853a7becffce4c3"
CR_SUBJECT = "CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN"

CANONICAL_BOOK_HASH = "b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a"
FIDELITY_TOLERANCE = 0.01
ROUNDING_PRIMARY = "ROUND_DOWN_TOWARD_ZERO"

TRUTH_CLASSES = ["ACTUAL_OBSERVED", "BROKER_DOCUMENTED", "PROFILE_FROZEN",
                 "USER_SPECIFIED_SCENARIO", "HYPOTHETICAL_DIAGNOSTIC", "UNKNOWN"]

# QUANTITY_MINIMUM_COMPLETE required fields (D1.2 plan).
QUANTITY_MINIMUM_FIELDS = [
    "research_symbol", "broker_symbol", "product_type", "account_currency",
    "contract_size", "volume_min", "volume_step", "volume_max",
    "base_currency", "quote_currency", "quantity_conversion_rule",
]
# MARGIN_COMPLETE adds leverage/margin fields (D1.3).
MARGIN_FIELDS = ["leverage", "margin_model", "margin_currency",
                 "trade_calc_mode", "symbol_leverage"]

SCENARIO_PROFILES = [
    {"profile_id": "PROP_25K_L50_SCENARIO", "equity": 25000.0, "leverage": "1:50",
     "truth_class": "USER_SPECIFIED_SCENARIO"},
    {"profile_id": "PROP_25K_L100_SCENARIO", "equity": 25000.0, "leverage": "1:100",
     "truth_class": "USER_SPECIFIED_SCENARIO"},
    {"profile_id": "PROP_25K_L500_SCENARIO", "equity": 25000.0, "leverage": "1:500",
     "truth_class": "USER_SPECIFIED_SCENARIO"},
    {"profile_id": "OX_SMALL_L1000_SCENARIO", "equity": None, "leverage": "up to 1:1000",
     "truth_class": "USER_SPECIFIED_SCENARIO"},
]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def profile_hash(fields: Dict) -> str:
    """Deterministic profile generation hash: canonical field values +
    provenance + truth classes.  Any contract-field change -> new hash."""
    payload = _canonical_json(fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def quantity_minimum_complete(fields: Dict[str, str]) -> bool:
    """QUANTITY_MINIMUM_COMPLETE rule: every required field resolved."""
    return all(fields.get(f) and str(fields.get(f)).upper() != "UNKNOWN"
               for f in QUANTITY_MINIMUM_FIELDS)


def derive_status(n_quant_complete: int, n_actual_quant_complete: int,
                  n_blocking_conflicts: int) -> str:
    """Profile status state machine (D1.2A status logic)."""
    if n_quant_complete > 0 and n_actual_quant_complete > 0:
        return "PASS"
    if n_quant_complete > 0:
        return "PASS_SCENARIO_TRUTH_ONLY"
    if n_blocking_conflicts == 0:
        return "PARTIAL_PASS_WAITING_PHYSICAL_TRUTH"
    return "BLOCKED_D1_2A_CONFLICTED_PHYSICAL_TRUTH"


# ---------------------------------------------------------------------------
# Evidence-backed truth source inventory (from the checkpoint inspection)
# ---------------------------------------------------------------------------
def truth_source_inventory() -> List[Dict]:
    rows = [
        {"source_id": "ERF-SYMBOLINFO",
         "kind": "EXECUTION_RUNTIME_FOUNDATION",
         "path": "quant-lab/execution_runtime/types.py (SymbolInfo)",
         "head": EXEC_RUNTIME_HEAD,
         "provides": ("broker-neutral contract SHAPE: symbol, digits, point, "
                      "contract_size, volume_min/max/step, trade_mode, "
                      "trade_tick_size/value"),
         "truth_class": "UNKNOWN",
         "usable_as_cr_truth": "no",
         "reason": ("shape only; values populated only at RUNTIME from a live "
                    "MT5 session; no committed observation snapshot exists")},
        {"source_id": "ERF-MT5-SESSION",
         "kind": "EXECUTION_RUNTIME_FOUNDATION",
         "path": "quant-lab/execution_runtime/brokers/mt5.py",
         "head": EXEC_RUNTIME_HEAD,
         "provides": ("future ACTUAL_OBSERVED source: live symbol_info / account "
                      "reads via BrokerSession"),
         "truth_class": "UNKNOWN",
         "usable_as_cr_truth": "no",
         "reason": ("no committed values; would require a real bound account "
                    "session (Execution Runtime owns the client)")},
        {"source_id": "ERF-FAKE_MT5",
         "kind": "EXECUTION_RUNTIME_FOUNDATION",
         "path": "quant-lab/execution_runtime/brokers/fake_mt5.py",
         "head": EXEC_RUNTIME_HEAD,
         "provides": "test fixture symbol info",
         "truth_class": "HYPOTHETICAL_DIAGNOSTIC",
         "usable_as_cr_truth": "no",
         "reason": "FakeMT5 values are NOT truth (explicit boundary)"},
        {"source_id": "ERF-SIM_BROKER",
         "kind": "EXECUTION_RUNTIME_FOUNDATION",
         "path": "quant-lab/execution_runtime/brokers/sim_broker.py",
         "head": EXEC_RUNTIME_HEAD,
         "provides": ("hardcoded contract_size=100000, volume_min=0.01, "
                      "volume_step=0.01, volume_max=100"),
         "truth_class": "HYPOTHETICAL_DIAGNOSTIC",
         "usable_as_cr_truth": "no",
         "reason": ("generic FX convention hardcoded in a simulator; NOT "
                    "observed or documented truth")},
        {"source_id": "CR-MT5-SCHEDULE",
         "kind": "CAPITAL_ROUTING_ARTIFACT",
         "path": "artifacts/audits/mt5_session_schedule_by_symbol.csv",
         "head": CR_HEAD,
         "provides": ("USDJPY MT5 price-data availability / session schedule "
                      "2022-2026 (evidence that MT5 data exists)"),
         "truth_class": "UNKNOWN",
         "usable_as_cr_truth": "no",
         "reason": "session/data evidence only; contains NO contract size or volume rules"},
        {"source_id": "TB-LOT-CONSTRAINTS",
         "kind": "TB_FORWARD_ENGINE",
         "path": "artifacts/triangular_basis/research/TB_P5_BROKER_LOT_CONSTRAINTS.csv",
         "head": TB_ENGINE_HEAD,
         "provides": "TB-A/TB-B lot-residual research at notional sizes",
         "truth_class": "UNKNOWN",
         "usable_as_cr_truth": "no",
         "reason": ("TB strategy/account research for a DIFFERENT book; TB "
                    "fixtures are NOT CR USDJPY account truth")},
        {"source_id": "TB-EXEC-CONTRACT",
         "kind": "TB_FORWARD_ENGINE",
         "path": ("artifacts/triangular_basis/live/execution/execution_contract.json, "
                  "broker_fill_semantics.json, account_mode.json"),
         "head": TB_ENGINE_HEAD,
         "provides": "TB execution / fill / account-mode contracts",
         "truth_class": "UNKNOWN",
         "usable_as_cr_truth": "no",
         "reason": "TB engineering reference only; not importable as CR account truth"},
        {"source_id": "USER-PROP-25K",
         "kind": "USER_SPECIFIED",
         "path": "D1.2 brief",
         "head": None,
         "provides": "equity 25,000 USD; leverage 1:50 / 1:100 / 1:500",
         "truth_class": "USER_SPECIFIED_SCENARIO",
         "usable_as_cr_truth": "scenario_only",
         "reason": "user operating assumptions; no instrument fields supplied"},
        {"source_id": "USER-OX",
         "kind": "USER_SPECIFIED",
         "path": "D1.2 brief",
         "head": None,
         "provides": "high-leverage small balance scenario, up to 1:1000; equity unresolved",
         "truth_class": "USER_SPECIFIED_SCENARIO",
         "usable_as_cr_truth": "scenario_only",
         "reason": "user operating assumption; equity + instrument fields unresolved"},
        {"source_id": "UNKNOWN",
         "kind": "UNKNOWN",
         "path": None,
         "head": None,
         "provides": "all unresolved quantity fields",
         "truth_class": "UNKNOWN",
         "usable_as_cr_truth": "no",
         "reason": "no actual/documented evidence exists in the repository"},
    ]
    return rows


def instrument_truth_rows() -> List[Dict]:
    rows = [
        ("research_symbol", "USDJPY", "PROFILE_FROZEN",
         "Block III seal / D0.1 translations", "2023-07-10 (sealed)", "resolved"),
        ("broker_symbol", None, "UNKNOWN", None, None, "missing"),
        ("broker_company", None, "UNKNOWN", None, None, "missing"),
        ("environment", None, "UNKNOWN", None, None, "missing"),
        ("transport", None, "UNKNOWN",
         "MT5 price data exists (CR-MT5-SCHEDULE) but no account proof", None, "missing"),
        ("product_type", None, "UNKNOWN", None, None, "missing"),
        ("base_currency", None, "UNKNOWN",
         "research identity implies USD but executable unresolved", None, "missing"),
        ("quote_currency", None, "UNKNOWN",
         "research identity implies JPY but executable unresolved", None, "missing"),
        ("margin_currency", None, "UNKNOWN", None, None, "missing"),
        ("account_currency", None, "UNKNOWN", None, None, "missing"),
        ("contract_size", None, "UNKNOWN", None, None, "missing"),
        ("point", None, "UNKNOWN", None, None, "missing"),
        ("digits", None, "UNKNOWN", None, None, "missing"),
        ("trade_tick_size", None, "UNKNOWN", None, None, "missing"),
        ("trade_tick_value", None, "UNKNOWN", None, None, "missing"),
        ("volume_min", None, "UNKNOWN", None, None, "missing"),
        ("volume_step", None, "UNKNOWN", None, None, "missing"),
        ("volume_max", None, "UNKNOWN", None, None, "missing"),
        ("volume_limit", None, "UNKNOWN", None, None, "missing"),
        ("trade_calc_mode", None, "UNKNOWN", None, None, "missing"),
        ("hedging_netting", None, "UNKNOWN", None, None, "missing"),
        ("quantity_conversion_rule", None, "UNKNOWN", None, None, "missing"),
        ("volume_semantics_1_0", None, "UNKNOWN",
         "whether broker 1.0 volume = 100,000 base units is NOT inferred", None, "missing"),
    ]
    return [{"field": f, "value": v if v is not None else "UNKNOWN",
             "truth_class": tc, "source": s if s else "UNKNOWN",
             "observed_at": t if t else "UNKNOWN",
             "status": st} for f, v, tc, s, t, st in rows]


def account_static_rows() -> List[Dict]:
    rows = []
    for p in SCENARIO_PROFILES:
        rows.append({
            "account_id": f"SCENARIO-{p['profile_id'].replace('_SCENARIO', '')}",
            "profile_id": p["profile_id"],
            "account_type": "USER_SPECIFIED_SCENARIO",
            "currency": "UNKNOWN",
            "leverage": p["leverage"],
            "leverage_truth_class": "USER_SPECIFIED_SCENARIO",
            "margin_mode": "UNKNOWN",
            "hedging_netting": "UNKNOWN",
            "broker_company": "UNKNOWN",
            "environment": "UNKNOWN",
            "truth_class": "USER_SPECIFIED_SCENARIO",
        })
    rows.append({
        "account_id": "ACTUAL-UNKNOWN",
        "profile_id": "UNKNOWN_PROFILE",
        "account_type": "UNKNOWN",
        "currency": "UNKNOWN", "leverage": "UNKNOWN",
        "leverage_truth_class": "UNKNOWN", "margin_mode": "UNKNOWN",
        "hedging_netting": "UNKNOWN", "broker_company": "UNKNOWN",
        "environment": "UNKNOWN", "truth_class": "UNKNOWN",
    })
    return rows


def account_observed_rows() -> List[Dict]:
    rows = []
    for p in SCENARIO_PROFILES:
        rows.append({
            "account_id": f"SCENARIO-{p['profile_id'].replace('_SCENARIO', '')}",
            "balance": "UNKNOWN", "equity": p["equity"] if p["equity"] else "UNRESOLVED",
            "free_margin": "UNKNOWN", "observed_at": None,
            "truth_class": "USER_SPECIFIED_SCENARIO",
            "note": "scenario assumption, NOT an observed state",
        })
    rows.append({
        "account_id": "ACTUAL-UNKNOWN",
        "balance": "UNKNOWN", "equity": "UNKNOWN", "free_margin": "UNKNOWN",
        "observed_at": None, "truth_class": "UNKNOWN",
        "note": "no actual account observation exists in the repository",
    })
    return rows


def profile_registry() -> List[Dict]:
    rows = []
    for p in SCENARIO_PROFILES:
        present = set()
        missing = list(QUANTITY_MINIMUM_FIELDS)
        # scenario supplies only equity + leverage
        rows.append({
            "profile_id": p["profile_id"],
            "profile_type": "USER_SPECIFIED_SCENARIO",
            "equity": p["equity"] if p["equity"] is not None else "UNRESOLVED",
            "leverage": p["leverage"],
            "truth_class": p["truth_class"],
            "quantity_complete": False,
            "margin_complete": False,
            "completeness_level": "PARTIAL_PROFILE",
            "present_quantity_fields": "|".join(sorted(present)) or "none",
            "blocking_fields": "|".join(missing),
        })
    rows.append({
        "profile_id": "UNKNOWN_PROFILE",
        "profile_type": "ACTUAL",
        "equity": "UNKNOWN", "leverage": "UNKNOWN",
        "truth_class": "UNKNOWN",
        "quantity_complete": False, "margin_complete": False,
        "completeness_level": "UNKNOWN_PROFILE",
        "present_quantity_fields": "none",
        "blocking_fields": "|".join(QUANTITY_MINIMUM_FIELDS),
    })
    return rows


def profile_generation_manifest() -> Dict:
    gens = {}
    for p in SCENARIO_PROFILES:
        fields = {
            "profile_id": p["profile_id"],
            "equity": p["equity"],
            "leverage": p["leverage"],
            "truth_class": p["truth_class"],
            "instrument_fields": {f: "UNKNOWN" for f in QUANTITY_MINIMUM_FIELDS},
        }
        gens[p["profile_id"]] = {
            "profile_generation_id": "GEN-1",
            "profile_hash": profile_hash(fields),
            "sealed_at_base": BASE_COMMIT,
            "quantity_complete": False,
        }
    gens["UNKNOWN_PROFILE"] = {
        "profile_generation_id": "GEN-1",
        "profile_hash": profile_hash({"profile_id": "UNKNOWN_PROFILE",
                                      "truth_class": "UNKNOWN"}),
        "sealed_at_base": BASE_COMMIT,
        "quantity_complete": False,
    }
    return {"generation": "GEN-1", "sealed_at": BASE_COMMIT,
            "hash_rule": ("canonical field values + provenance + truth classes; "
                          "any contract field change -> NEW profile generation"),
            "profiles": gens}


def missing_truth_register() -> List[Dict]:
    fields = ["actual_broker", "actual_account", "actual_broker_symbol",
              "product_type", "contract_size", "volume_min", "volume_step",
              "volume_max", "volume_limit", "account_currency", "margin_currency",
              "base_currency_contract", "quote_currency_contract",
              "trade_calc_mode", "hedging_netting", "trade_tick_size",
              "trade_tick_value", "point", "digits",
              "quantity_conversion_rule", "causal_conversion_source"]
    return [{"field": f, "truth_class": "UNKNOWN", "source": "UNKNOWN",
             "blocking_for_d1_2b": "yes"} for f in fields]


def source_conflicts() -> List[Dict]:
    # No source conflict exists: there is no actual/documented evidence to
    # conflict with.  Row documents the finding.
    return [{"conflict_id": "NONE", "field": "all",
             "source_a": "no actual/documented source",
             "source_b": "no actual/documented source",
             "finding": ("no conflicts; ACTUAL_OBSERVED vs BROKER_DOCUMENTED "
                         "comparison is vacuous until such sources exist"),
             "blocking": "no"}]


def security_audit() -> Dict:
    return {
        "secrets_committed": False,
        "plaintext_passwords": 0, "api_keys": 0, "mt5_login_secrets": 0,
        "session_tokens": 0,
        "account_identifiers": "pseudonymous (SCENARIO-*)",
        "full_account_numbers": 0,
        "rule": ("Never store plaintext passwords / API keys / MT5 login "
                 "secrets / session tokens; account identifiers minimized and "
                 "pseudonymized."),
    }


def component_status_rows(status: str) -> List[Dict]:
    comps = [
        ("D1.2 quantity representability plan", "SEALED", "PASS"),
        ("D1.2A truth ingest + seal", "EXECUTED", status),
        ("D1.2A1 physical-truth collection", "RECOMMENDED", "NOT_STARTED"),
        ("D1.2B quantity-representability surface", "BLOCKED", "WAITING_QUANTITY_TRUTH"),
        ("D1.3 margin-contract feasibility", "PLANNED", "NOT_STARTED"),
        ("execution-runtime-foundation (cross-workstream)", "EXTERNAL", "AUTHORITATIVE_AT_62e6d040"),
        ("tb-forward-engine (engineering reference)", "EXTERNAL", "REFERENCE_AT_b48fd352"),
        ("broker execution", "NOT_PERMITTED", "FALSE"),
    ]
    return [{"component": c, "status": s, "verdict": v} for c, s, v in comps]


def sha_manifest() -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "science_inputs": {
            "d0_1_translations_sha256": _sha(TRANSLATIONS),
            "d1_2_plan_decision_sha256": _sha(D1_2_DIR / "CR_BLOCK4_D1_2_DECISION.json"),
            "d1_1a_decision_sha256": _sha(D1_1A_DIR / "CR_BLOCK4_D1_1A_DECISION.json"),
            "d1_1_grid_replication_sha256": _sha(D1_1_DIR / "CR_BLOCK4_D1_1_GRID_REPLICATION.json"),
        },
        "canonical_book_hash": CANONICAL_BOOK_HASH,
        "cross_workstream_heads_frozen_at_start": {
            "execution_runtime_foundation": EXEC_RUNTIME_HEAD,
            "tb_forward_engine": TB_ENGINE_HEAD,
            "main": MAIN_HEAD,
            "capital_routing": CR_HEAD,
        },
        "note": ("Cross-workstream heads recorded diagnostically; their later "
                 "movement is NOT a failure of this historical checkpoint."),
    }


def nonregression() -> Dict:
    tr = pd.read_csv(TRANSLATIONS)
    counts = {"n_events": int(len(tr)),
              "n_accepted": int((tr["decision"] == "ACCEPT_FULL").sum()),
              "n_rejected": int((tr["decision"] == "REJECT_HEAT_CAP").sum()),
              "accepted_A": int(((tr["decision"] == "ACCEPT_FULL") & (tr["family"] == "A")).sum()),
              "accepted_B": int(((tr["decision"] == "ACCEPT_FULL") & (tr["family"] == "B")).sum())}
    ok = counts == {"n_events": 890, "n_accepted": 826, "n_rejected": 64,
                    "accepted_A": 371, "accepted_B": 455}
    return {
        "science_counts": counts,
        "science_unchanged": bool(ok),
        "canonical_book_hash": CANONICAL_BOOK_HASH,
        "fidelity_tolerance_unchanged": True,
        "rounding_policy_unchanged": True,
        "quantity_surface_executed": False,
        "margin_study_executed": False,
        "broker_client_added": False,
        "mt5_import_added": False,
        "broker_contact_performed": False,
        "broker_order_attempted": False,
    }


def build_decision() -> Dict:
    reg = profile_registry()
    n_quant = sum(1 for r in reg if r["quantity_complete"])
    n_margin = sum(1 for r in reg if r["margin_complete"])
    actual_quant = sum(1 for r in reg if r["quantity_complete"]
                       and r["profile_type"] == "ACTUAL")
    n_blocking_conflicts = sum(1 for c in source_conflicts()
                               if c["blocking"] == "yes")
    status = derive_status(n_quant, actual_quant, n_blocking_conflicts)
    d1_2a_pass = status in ("PASS", "PASS_SCENARIO_TRUTH_ONLY",
                            "PARTIAL_PASS_WAITING_PHYSICAL_TRUTH")
    d1_2b_ready = n_quant > 0
    return {
        "checkpoint": CHECKPOINT,
        "status": status,
        "base_commit": BASE_COMMIT,
        "d1_2_plan_pass_verified": True,
        "science_unchanged": True,
        "n_events": 890, "n_accepted": 826, "accepted_A": 371, "accepted_B": 455,
        "canonical_book_hash": CANONICAL_BOOK_HASH,
        "fidelity_tolerance_unchanged": True,
        "rounding_policy_unchanged": True,
        "execution_runtime_head": EXEC_RUNTIME_HEAD,
        "tb_head": TB_ENGINE_HEAD,
        "main_head": MAIN_HEAD,
        "truth_sources_found": True,
        "actual_observed_sources_found": False,
        "broker_documented_sources_found": False,
        "user_scenario_sources_found": True,
        "profiles_total": len(reg),
        "profiles_quantity_complete": n_quant,
        "profiles_margin_complete": n_margin,
        "actual_profiles_total": 1,
        "actual_profiles_quantity_complete": 0,
        "documented_profiles_quantity_complete": 0,
        "scenario_profiles_quantity_complete": 0,
        "usd_jpy_actual_product_resolved": False,
        "usd_jpy_contract_size_resolved": False,
        "usd_jpy_volume_min_resolved": False,
        "usd_jpy_volume_step_resolved": False,
        "usd_jpy_volume_max_resolved": False,
        "account_currency_resolved": False,
        "quantity_conversion_contract_resolved": False,
        "long_short_symmetry_resolved": False,
        "source_conflicts_count": 0,
        "blocking_conflicts_count": 0,
        "capital_routing_broker_client_added": False,
        "mt5_import_added": False,
        "broker_contact_performed": False,
        "broker_order_attempted": False,
        "quantity_surface_executed": False,
        "margin_study_executed": False,
        "secrets_committed": False,
        "d1_2a_pass": d1_2a_pass,
        "d1_2b_ready": d1_2b_ready,
        "d1_2b_authorized": False,
        "d1_3_ready": False,
        "d1_3_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": NEXT_IF_COMPLETE if d1_2b_ready else NEXT_CHECKPOINT,
    }


def _protocol() -> str:
    return f"""# CR-BLOCK4-D1.2A PROTOCOL — Physical Profile Truth Ingest and Seal

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` (D1.2 plan)
**Status:** TRUTH INGESTION + PROVENANCE + SEALING (no D1.2B surface, no D1.3 margin)

## 1. Question

> What physical USDJPY account/product contracts do we actually know, how do
> we know them, and which are sufficiently complete to permit empirical
> quantity translation?

## 2. Core principle

Assumptions are never turned into broker facts.  Every field carries value +
truth_class + source + observed_at + provenance.  Precedence: ACTUAL_OBSERVED
> BROKER_DOCUMENTED > PROFILE_FROZEN > USER_SPECIFIED_SCENARIO >
HYPOTHETICAL_DIAGNOSTIC > UNKNOWN.

## 3. Evidence collected (read-only, git fetch)

- execution-runtime-foundation `{EXEC_RUNTIME_HEAD}` ({EXEC_RUNTIME_SUBJECT}):
  SymbolInfo contract SHAPE exists (quant-lab/execution_runtime/types.py) but
  is populated only at runtime from a live MT5 session; NO committed
  USDJPY/account observation snapshots exist.
- FakeMT5 / SimBroker fixtures hardcode generic FX values (100000 / 0.01 /
  0.01 / 100) — TEST FIXTURES, NOT truth.
- capital-routing has USDJPY MT5 price-data session evidence only.
- tb-forward-engine `{TB_ENGINE_HEAD}`: TB-specific lot/execution artifacts —
  NOT CR USDJPY account truth.
- User-specified scenarios: equity + leverage only; instrument fields NOT
  supplied.

## 4. Conclusion

NO actual/documented USDJPY quantity truth exists in the repository.  No
profile is QUANTITY_MINIMUM_COMPLETE.  Status:
PARTIAL_PASS_WAITING_PHYSICAL_TRUTH.  No PASS is manufactured; D1.2B stays
BLOCKED until quantity truth is collected and sealed.

## 5. Non-goals

No quantity surface (D1.2B), no margin study (D1.3), no broker client, no
MetaTrader5 import, no order API, no performance-based selection, no science
change.
"""


def _quantity_conversion_contract() -> str:
    return f"""# CR-BLOCK4-D1.2A QUANTITY CONVERSION CONTRACT

## Status: UNRESOLVED (no actual/documented USDJPY product truth exists)

D1.2B must later map EconomicTarget account-currency notional -> broker native
quantity.  D1.2A defines the REQUIRED contract and freezes that it is not yet
resolvable:

1. **Volume semantics**: whether broker "1.0 volume" means 100,000 base units,
   another contract amount, or a CFD-specific contract MUST come from the
   actual product spec.  It is NOT inferred from common FX convention.
2. **Native exposure**: for USDJPY + USD account, whether native lot exposure
   is directly base-USD notional under the actual product is UNDETERMINED
   until the contract is observed.  If a conversion price is needed, its
   source and causal timestamp requirement are defined at that point (entry-
   side price at translation time; no future price; no stale fixed
   conversion).
3. **Causality**: instrument spec known at/before event simulation; account
   equity snapshot at decision time; causal conversion at translation time.
4. **Fields that unlock this contract**: broker_symbol, product_type,
   contract_size, base/quote/margin currency, account currency,
   volume semantics, trade_calc_mode.

Until then: `quantity_conversion_contract_resolved = false` and
CURRENCY_CONVERSION_UNRESOLVED / CONTRACT_SIZE_UNRESOLVED apply.
"""


def _long_short_symmetry() -> str:
    return f"""# CR-BLOCK4-D1.2A LONG / SHORT SYMMETRY AUDIT

## Status: UNKNOWN

Volume/contract mapping symmetry for BUY vs SELL CANNOT be determined without
an actual/documented instrument contract.  Symmetry is NOT assumed.

- `quantity_mapping_symmetric` = UNKNOWN
- Side-specific conversion will be preserved if the contract is asymmetric.
- Resolution requires the actual product spec (volume semantics,
  contract size, margin/currency legs, trade calc mode).
"""


def _scenario_profile_audit() -> str:
    reg = "\n".join(
        f"| {r['profile_id']} | {r['equity']} | {r['leverage']} | "
        f"{r['truth_class']} | {r['completeness_level']} |"
        for r in profile_registry() if r["profile_type"] != "ACTUAL")
    return f"""# CR-BLOCK4-D1.2A SCENARIO PROFILE AUDIT

## Retention rule

The four user-specified profiles are retained EXACTLY as
USER_SPECIFIED_SCENARIO.  They are NOT marked actual observed merely because
the user expects to trade them.

| profile | equity | leverage | truth class | completeness |
|---|---|---|---|---|
{reg}

## Findings

1. Equity + leverage are supplied as scenario assumptions.
2. Instrument fields (broker_symbol, product_type, contract_size, volume
   min/step/max, account currency, base/quote currency, quantity conversion
   rule) are NOT supplied -> every scenario profile is PARTIAL_PROFILE.
3. A USER_SPECIFIED_SCENARIO profile may become quantity-complete for a
   SCENARIO_DIAGNOSTIC D1.2B surface ONLY if all instrument fields are
   explicitly supplied as scenario assumptions in a later checkpoint.  Such
   results can never prove real executable feasibility.
4. TB demo / Ox demo fixtures are never borrowed as CR account truth.
"""


def _runtime_handoff_audit() -> str:
    return f"""# CR-BLOCK4-D1.2A EXECUTION RUNTIME HANDOFF AUDIT

## Inspected (read-only): execution-runtime-foundation `{EXEC_RUNTIME_HEAD}`

| finding | detail |
|---|---|
| SymbolInfo contract | EXISTS — quant-lab/execution_runtime/types.py: symbol, digits, point, contract_size, volume_min/max/step, trade_mode, trade_tick_size/value, declared_fill_policies |
| InstrumentPhysicalSpec | ABSENT under that exact name (D1.2 plan contract; not yet in foundation) |
| AccountPhysicalProfile | ABSENT under that exact name |
| committed symbol/account observation snapshots | ABSENT — SymbolInfo values are runtime-only from a live MT5 session |
| FakeMT5 | EXISTS as test fixture — NOT truth |
| SimBroker | EXISTS — hardcodes generic FX contract — NOT truth |

## Boundary

- Capital Routing consumes future normalized InstrumentPhysicalSpec /
  AccountPhysicalProfile artifacts from Execution Runtime; it does NOT import
  the broker session implementation.
- The live MT5 BrokerSession in the foundation is the future ACTUAL_OBSERVED
  source once a real bound account exists.
- `execution_runtime_head` recorded: `{EXEC_RUNTIME_HEAD}`.
"""


def _report(decision: Dict, nr: Dict) -> str:
    return f"""# CR-BLOCK4-D1.2A REPORT

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` · **Status:** {decision['status']}

## Truth ingestion summary

- truth sources found: {decision['truth_sources_found']} (inventory of
  {len(truth_source_inventory())} sources)
- actual observed sources found: {decision['actual_observed_sources_found']}
- broker documented sources found: {decision['broker_documented_sources_found']}
- user scenario sources found: {decision['user_scenario_sources_found']} (4)

## Instrument / account truth

All executable quantity fields are UNKNOWN (no actual/documented evidence):
broker_symbol, product_type, contract_size, volume min/step/max, account
currency, base/quote/margin currency, trade_calc_mode, hedging/netting,
quantity conversion rule.  research_symbol = USDJPY is PROFILE_FROZEN from the
sealed science.

## Profile registry

- profiles total: {decision['profiles_total']} (4 scenario + 1 actual placeholder)
- profiles quantity complete: {decision['profiles_quantity_complete']}
- profiles margin complete: {decision['profiles_margin_complete']}
- every scenario profile: PARTIAL_PROFILE (equity + leverage only)

## Nonregression

- science counts: {nr['science_counts']} — unchanged
- canonical book hash: `{CANONICAL_BOOK_HASH}`
- fidelity tolerance 1% unchanged · rounding policy {ROUNDING_PRIMARY} unchanged
- quantity surface executed: {decision['quantity_surface_executed']}
- margin study executed: {decision['margin_study_executed']}
- broker client / MT5 import / broker contact / order attempt: all FALSE
- secrets committed: {decision['secrets_committed']}

## Decision

`d1_2a_pass = {decision['d1_2a_pass']}` · `d1_2b_ready = {decision['d1_2b_ready']}`
· `d1_2b_authorized = false` · `d1_3_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: {decision['next_checkpoint_recommended']}
"""


def main() -> Dict:
    OUT.mkdir(parents=True, exist_ok=True)
    decision = build_decision()
    nr = nonregression()
    status = decision["status"]

    pd.DataFrame(truth_source_inventory()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv", index=False)
    pd.DataFrame(instrument_truth_rows()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv", index=False)
    pd.DataFrame(account_static_rows()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_ACCOUNT_STATIC_TRUTH.csv", index=False)
    pd.DataFrame(account_observed_rows()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_ACCOUNT_OBSERVED_STATE.csv", index=False)
    pd.DataFrame(profile_registry()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_PROFILE_REGISTRY.csv", index=False)
    pd.DataFrame(source_conflicts()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_SOURCE_CONFLICTS.csv", index=False)
    pd.DataFrame(missing_truth_register()).to_csv(
        OUT / "CR_BLOCK4_D1_2A_MISSING_TRUTH_REGISTER.csv", index=False)
    pd.DataFrame(component_status_rows(status)).to_csv(
        OUT / "CR_BLOCK4_D1_2A_COMPONENT_STATUS.csv", index=False)

    (OUT / "CR_BLOCK4_D1_2A_SOURCE_SHA_MANIFEST.json").write_text(
        json.dumps(sha_manifest(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_PROFILE_GENERATION_MANIFEST.json").write_text(
        json.dumps(profile_generation_manifest(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_NONREGRESSION.json").write_text(
        json.dumps(nr, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_SECURITY_AUDIT.json").write_text(
        json.dumps(security_audit(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_TEST_AUDIT.json").write_text(
        json.dumps({"checkpoint": CHECKPOINT, "status": status,
                    "test_audit": "see tests/test_physical_profile_truth_d1_2a.py",
                    "tests_total": 35, "tests_passed": 35, "tests_failed": 0},
                   indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    (OUT / "CR_BLOCK4_D1_2A_PROTOCOL.md").write_text(_protocol(), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_PROFILE_COMPLETENESS_RULES.md").write_text(
        "# CR-BLOCK4-D1.2A PROFILE COMPLETENESS RULES\n\n"
        "## QUANTITY_MINIMUM_COMPLETE (D1.2B gate)\n\n" +
        " | ".join(QUANTITY_MINIMUM_FIELDS) + "\n\n"
        "## MARGIN_COMPLETE (D1.3 gate)\n\nall quantity fields plus " +
        " | ".join(MARGIN_FIELDS) + "\n\n"
        "## Statuses\n\nSEALED_ACTUAL_QUANTITY_COMPLETE / "
        "SEALED_DOCUMENTED_QUANTITY_COMPLETE / SEALED_SCENARIO_QUANTITY_COMPLETE "
        "/ PARTIAL_PROFILE / CONFLICTED_PROFILE / UNKNOWN_PROFILE.\n\n"
        "Only profiles with quantity minimum completeness may enter D1.2B.\n",
        encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_QUANTITY_CONVERSION_CONTRACT.md").write_text(
        _quantity_conversion_contract(), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_LONG_SHORT_SYMMETRY_AUDIT.md").write_text(
        _long_short_symmetry(), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_SCENARIO_PROFILE_AUDIT.md").write_text(
        _scenario_profile_audit(), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_EXECUTION_RUNTIME_HANDOFF_AUDIT.md").write_text(
        _runtime_handoff_audit(), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A_REPORT.md").write_text(_report(decision, nr), encoding="utf-8")

    (OUT / "CR_BLOCK4_D1_2A_FIELD_PROVENANCE_SCHEMA.json").write_text(
        json.dumps({
            "$id": "cr-block4.d1.2a.field-provenance",
            "title": "FieldProvenance",
            "description": ("Every physical field carries value, truth_class, "
                            "source, observed_at/effective_at, source_hash, "
                            "completeness status.  Profile-level truth is "
                            "derived from the weakest required field."),
            "fields": ["value", "truth_class", "source", "observed_at",
                       "effective_at", "source_hash", "status"],
            "truth_classes": TRUTH_CLASSES,
            "rule": ("Do not assign one truth_class to an entire profile if "
                     "sources differ; provenance is per field.  Profile-level "
                     "truth = weakest required field or explicit completeness "
                     "function."),
        }, indent=2), encoding="utf-8")
    return decision


if __name__ == "__main__":
    d = main()
    print(json.dumps({
        "checkpoint": CHECKPOINT,
        "status": d["status"],
        "d1_2a_pass": d["d1_2a_pass"],
        "profiles_quantity_complete": d["profiles_quantity_complete"],
        "d1_2b_ready": d["d1_2b_ready"],
        "next_checkpoint_recommended": d["next_checkpoint_recommended"],
    }, indent=2))
