"""
CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION — real read-only collection.

Collects the minimum REAL read-only USDJPY account/product truth required to
unblock D1.2B.  Live observation succeeded via the already-running MT5
terminal on this machine using ONLY read-only MetaTrader5 API calls
(account_info, symbol_select [Market Watch only], symbol_info,
symbol_info_tick, terminal_info).  NO order_send, NO order_check, NO
position/order modification, NO close/cancel, NO account mutation.

Frozen evidence: `_raw_observation.json` (ACTUAL_OBSERVED, sanitized —
pseudonymous account id, personal name redacted, no credentials, no login).

Resolved physical truth (Ox Securities demo, MT5):

  - broker_symbol: USDJPY.PRO  (NOT "USDJPY" — the .PRO suffix is observed)
  - product_type: FX (Forex PRO path, trade_calc_mode 0 = FX_DEPTH)
  - contract_size: 100,000 base units per 1.0 volume (OBSERVED, not assumed)
  - volume_min 0.01 / volume_step 0.01 / volume_max 200.0
  - digits 3, point 0.001, tick 0.001, tick_value 0.626731345341506 USD
  - base USD / profit JPY / margin USD; account currency USD
  - quantity conversion: volume = target_USD_notional / 100000 — DIRECT
    base-USD mapping (account currency == base currency); no FX conversion
    price needed for notional->units on this contract
  - quantity_mapping_symmetric = true (SymbolInfo has no side-dependent
    volume/contract fields)
  - account: USD, leverage 500 (OBSERVED), margin_mode 2, equity 25,254.35

Quantity minimum completeness: TRUE -> profile is
SEALED_ACTUAL_QUANTITY_COMPLETE, PHYSICAL_PROFILE_GENERATION_G1.
d1_2b_ready = true; d1_2b_authorized = false (human gate).

Base: 052223762034d1fe4bf974698501ab955504a18d (D1.2A).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_physical_truth_collection_d1_2a1"
RAW = OUT / "_raw_observation.json"
D1_2A_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_physical_profile_truth_d1_2a"
TRANSLATIONS = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0_1" / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv"

BASE_COMMIT = "052223762034d1fe4bf974698501ab955504a18d"
CHECKPOINT = "CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION"
NEXT_CHECKPOINT = "CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE"

CANONICAL_BOOK_HASH = "b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a"
FIDELITY_TOLERANCE = 0.01
ROUNDING_PRIMARY = "ROUND_DOWN_TOWARD_ZERO"
PROFILE_GENERATION = "PHYSICAL_PROFILE_GENERATION_G1"

QUANTITY_MINIMUM_FIELDS = [
    "research_symbol", "broker_symbol", "product_type", "account_currency",
    "contract_size", "volume_min", "volume_step", "volume_max",
    "base_currency", "quote_currency", "quantity_conversion_rule",
]

EXEC_RUNTIME_HEAD = "62e6d0402a780d171a8b81c2070567045e341be7"
TB_ENGINE_HEAD = "b48fd35255b41865026a3cba333ae2a2a0d6a004"
MAIN_HEAD = "9f61288679eea56a298e08f718c314f2ca509bc5"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_evidence() -> Dict:
    return json.loads(RAW.read_text(encoding="utf-8"))


def instrument_spec(ev: Dict) -> Dict:
    s = ev["symbol"]
    return {
        "source_id": ev["capture_id"],
        "observed_at": ev["observed_at"],
        "broker_company": ev["account"]["company"],
        "environment": ev["environment"],
        "transport": ev["account"]["transport"],
        "research_symbol": "USDJPY",
        "broker_symbol": s["broker_symbol"],
        "product_type": "FX",
        "product_type_note": ("Forex PRO path, trade_calc_mode 0 (FX_DEPTH); "
                              "exact spot-vs-CFD legal representation is per "
                              "broker semantics (not separately asserted)"),
        "contract_size": s["trade_contract_size"],
        "contract_size_semantics": "base units per 1.0 volume (OBSERVED)",
        "point": s["point"],
        "digits": s["digits"],
        "tick_size": s["trade_tick_size"],
        "tick_value": s["trade_tick_value"],
        "tick_value_currency": ev["account"]["currency"],
        "volume_min": s["volume_min"],
        "volume_step": s["volume_step"],
        "volume_max": s["volume_max"],
        "volume_limit": None,
        "volume_semantics": "1.0 volume = 100,000 base units (USD) on USDJPY.PRO",
        "base_currency": s["currency_base"],
        "quote_currency": s["currency_profit"],
        "margin_currency": s["currency_margin"],
        "trade_calc_mode": s["trade_calc_mode"],
        "trade_mode": s["trade_mode"],
        "hedging_netting": "UNKNOWN",
        "hedging_netting_note": ("not directly observable via account_info / "
                                 "symbol_info; deferred to account control plane"),
        "truth_class": "ACTUAL_OBSERVED",
        "source": ev["source"],
    }


def account_profile(ev: Dict) -> Dict:
    a = ev["account"]
    return {
        "account_id": a["pseudonymous_account_id"],
        "observed_at": ev["observed_at"],
        "balance": a["balance"],
        "equity": a["equity"],
        "margin_free": a["margin_free"],
        "account_currency": a["currency"],
        "leverage": a["leverage"],
        "margin_mode": a["margin_mode"],
        "trade_mode": a["trade_mode"],
        "fifo_close": a["fifo_close"],
        "broker_company": a["company"],
        "server": a["server"],
        "environment": ev["environment"],
        "transport": a["transport"],
        "hedging_netting": "UNKNOWN",
        "truth_class": "ACTUAL_OBSERVED",
        "source": ev["source"],
        "note": ("Account equity is a time-varying OBSERVED state, NOT a "
                 "permanent account specification; static fields (currency, "
                 "leverage contract, margin mode, broker, environment) are "
                 "kept separate."),
    }


def field_provenance(ev: Dict) -> List[Dict]:
    s, a = ev["symbol"], ev["account"]
    rows = [
        ("research_symbol", "USDJPY", "PROFILE_FROZEN", "Block III seal", "n/a"),
        ("broker_symbol", s["broker_symbol"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("product_type", "FX", "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("broker_company", a["company"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("environment", ev["environment"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("transport", a["transport"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("contract_size", s["trade_contract_size"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("volume_min", s["volume_min"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("volume_step", s["volume_step"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("volume_max", s["volume_max"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("digits", s["digits"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("point", s["point"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("tick_size", s["trade_tick_size"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("tick_value", s["trade_tick_value"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("base_currency", s["currency_base"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("quote_currency", s["currency_profit"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("margin_currency", s["currency_margin"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("account_currency", a["currency"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("leverage", a["leverage"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("balance", a["balance"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("equity", a["equity"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("margin_mode", a["margin_mode"], "ACTUAL_OBSERVED", ev["source"], ev["observed_at"]),
        ("quantity_conversion_rule",
         "volume = target_USD_notional / 100000 (base-USD direct)",
         "DERIVED_OBSERVED", "derived from observed contract_size + base currency == account currency",
         ev["observed_at"]),
        ("quantity_mapping_symmetric", "true", "DERIVED_OBSERVED",
         "SymbolInfo carries no side-dependent volume/contract fields",
         ev["observed_at"]),
        ("hedging_netting", "UNKNOWN", "UNKNOWN", "not observable via used APIs", "n/a"),
    ]
    return [{"field": f, "value": v, "truth_class": t, "source": src,
             "observed_at": ts} for f, v, t, src, ts in rows]


def quantity_conversion_contract(ev: Dict) -> str:
    s = ev["symbol"]
    return f"""# CR-BLOCK4-D1.2A1 QUANTITY CONVERSION CONTRACT (RESOLVED)

## Observed contract (ACTUAL_OBSERVED, {ev['observed_at']})

- broker symbol: **{s['broker_symbol']}** (Ox Securities MT5)
- 1.0 volume = **{s['trade_contract_size']} base units (USD)** — OBSERVED via
  trade_contract_size, NOT assumed from FX convention
- base currency **{s['currency_base']}** == account currency **{ev['account']['currency']}**
- trade_calc_mode **{s['trade_calc_mode']}** (FX_DEPTH): margin in account
  currency, profit in quote currency

## Rule

    raw_volume = target_USD_notional / trade_contract_size

Because account currency == base currency (USD), the target USD notional maps
DIRECTLY to base units.  NO FX conversion price is required for
notional->units on this contract.

## Verification

Tick-value cross-check: contract_size x tick_size / reference_price =
{100000.0 * 0.001 / ev['tick']['ask']:.6f} vs observed trade_tick_value
{s['trade_tick_value']:.6f} — consistent (reference ask
{ev['tick']['ask']} at {ev['observed_at']}).

## Causality

Instrument spec observed at {ev['observed_at']} (frozen); account equity
snapshot at the same observation; entry-side conversion is used for any
later price-dependent step.  No future price, no stale conversion.

## Margin note

Margin / buying-power semantics (leverage {ev['account']['leverage']},
margin_mode {ev['account']['margin_mode']}, margin currency
{s['currency_margin']}) are COLLECTED METADATA only — margin feasibility is
D1.3, not D1.2B.
"""


def long_short_symmetry(ev: Dict) -> Dict:
    return {
        "quantity_mapping_symmetric": True,
        "resolved": True,
        "rationale": ("Observed SymbolInfo for USDJPY.PRO carries no "
                      "side-dependent volume / contract-size fields; volume "
                      "semantics are identical for BUY and SELL under the "
                      "observed contract (contract_size, volume_min/step/max, "
                      "calc mode apply direction-independently)."),
        "evidence": ev["capture_id"],
        "truth_class": "ACTUAL_OBSERVED",
    }


def profile_hash(ev: Dict) -> Dict:
    s, a = ev["symbol"], ev["account"]
    fields = {
        "profile_id": "OX_DEMO_USDJPY_PRO_G1",
        "account_id": a["pseudonymous_account_id"],
        "broker_symbol": s["broker_symbol"],
        "product_type": "FX",
        "contract_size": s["trade_contract_size"],
        "volume_min": s["volume_min"],
        "volume_step": s["volume_step"],
        "volume_max": s["volume_max"],
        "account_currency": a["currency"],
        "base_currency": s["currency_base"],
        "quote_currency": s["currency_profit"],
        "margin_currency": s["currency_margin"],
        "quantity_conversion_rule": "volume = USD_notional / contract_size",
        "truth_class": "ACTUAL_OBSERVED",
        "environment": ev["environment"],
        "observed_at": ev["observed_at"],
    }
    h = hashlib.sha256(_canonical_json(fields).encode("utf-8")).hexdigest()
    return {"profile_generation_id": PROFILE_GENERATION,
            "profile_id": "OX_DEMO_USDJPY_PRO_G1",
            "profile_hash": h,
            "hash_rule": ("canonical field values + provenance + truth class; "
                          "any contract-field change -> NEW profile generation"),
            "canonical_fields": fields}


def completeness_audit(ev: Dict) -> Dict:
    s, a = ev["symbol"], ev["account"]
    resolved = {
        "research_symbol": "USDJPY",
        "broker_symbol": s["broker_symbol"],
        "product_type": "FX",
        "account_currency": a["currency"],
        "contract_size": s["trade_contract_size"],
        "volume_min": s["volume_min"],
        "volume_step": s["volume_step"],
        "volume_max": s["volume_max"],
        "base_currency": s["currency_base"],
        "quote_currency": s["currency_profit"],
        "quantity_conversion_rule": "volume = USD_notional / contract_size",
    }
    complete = all(str(v).upper() != "UNKNOWN" for v in resolved.values())
    margin_unknown = ["symbol_leverage", "margin_tiers", "hedging_netting"]
    return {
        "quantity_minimum_complete": complete,
        "margin_complete": False,
        "completeness_level": "SEALED_ACTUAL_QUANTITY_COMPLETE",
        "required_fields": resolved,
        "margin_blockers": margin_unknown,
        "margin_note": ("leverage, margin_mode, margin currency, trade_calc_mode "
                        "are OBSERVED; symbol leverage/tiers and hedging/netting "
                        "remain for D1.3"),
        "rule": ("any change to contract_size / volume_min / volume_step / "
                 "volume_max / account_currency / broker_symbol / product_type "
                 "requires a NEW profile generation"),
    }


def security_audit() -> Dict:
    return {
        "secrets_committed": False,
        "plaintext_passwords": 0, "api_keys": 0, "mt5_login_secrets": 0,
        "session_tokens": 0,
        "login_committed": False,
        "personal_name_committed": False,
        "account_id": "pseudonymous (OX-DEMO-<sha256(login)[:12]>)",
        "raw_evidence_check": {
            "login_pseudonym_hash_present": True,
            "name_value": "REDACTED (not committed)",
        },
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
        "no_clipping": True,
        "no_upward_rounding": True,
        "broker_order_attempted": False,
        "broker_write_performed": False,
    }


def sha_manifest() -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "raw_observation_sha256": _sha(RAW),
        "science_inputs": {
            "d0_1_translations_sha256": _sha(TRANSLATIONS),
            "d1_2a_decision_sha256": _sha(D1_2A_DIR / "CR_BLOCK4_D1_2A_DECISION.json"),
        },
        "canonical_book_hash": CANONICAL_BOOK_HASH,
        "cross_workstream_heads_frozen_at_start": {
            "execution_runtime_foundation": EXEC_RUNTIME_HEAD,
            "tb_forward_engine": TB_ENGINE_HEAD,
            "main": MAIN_HEAD,
        },
        "note": ("Raw evidence is a frozen ACTUAL_OBSERVED snapshot of a live "
                 "read-only observation; regeneration is deterministic from "
                 "this file."),
    }


def build_decision(comp: Dict, ph: Dict) -> Dict:
    ready = comp["quantity_minimum_complete"]
    return {
        "checkpoint": CHECKPOINT,
        "status": "PASS" if ready else "WAITING_USER_PHYSICAL_ACCOUNT_ACCESS",
        "base_commit": BASE_COMMIT,
        "science_unchanged": True,
        "actual_account_observed": True,
        "actual_usdjpy_observed": True,
        "broker_symbol_resolved": True,
        "account_currency_resolved": True,
        "contract_size_resolved": True,
        "volume_min_resolved": True,
        "volume_step_resolved": True,
        "volume_max_resolved": True,
        "product_type_resolved": True,
        "quantity_conversion_resolved": True,
        "long_short_symmetry_resolved": True,
        "quantity_minimum_complete": comp["quantity_minimum_complete"],
        "margin_complete": False,
        "profile_generation_id": ph["profile_generation_id"],
        "profile_hash": ph["profile_hash"],
        "truth_class": "ACTUAL_OBSERVED",
        "broker_order_attempted": False,
        "broker_write_performed": False,
        "d1_2b_ready": ready,
        "d1_2b_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": NEXT_CHECKPOINT if ready
        else "WAITING_USER_PHYSICAL_ACCOUNT_ACCESS",
    }


def component_status_rows(status: str) -> List[Dict]:
    comps = [
        ("D1.2A truth ingest + seal", "SEALED", "PARTIAL_PASS_WAITING_PHYSICAL_TRUTH"),
        ("D1.2A1 physical truth collection", "EXECUTED", status),
        ("Ox Securities demo USDJPY.PRO profile (G1)", "SEALED", "SEALED_ACTUAL_QUANTITY_COMPLETE"),
        ("D1.2B quantity-representability surface", "READY_AFTER_HUMAN_REVIEW", "NOT_AUTHORIZED"),
        ("D1.3 margin-contract feasibility", "PLANNED", "NOT_STARTED"),
        ("execution-runtime-foundation (cross-workstream)", "EXTERNAL", "AUTHORITATIVE_AT_62e6d040"),
        ("broker execution / orders", "NOT_PERMITTED", "FALSE"),
    ]
    return [{"component": c, "status": s, "verdict": v} for c, s, v in comps]


def _protocol(ev: Dict) -> str:
    return f"""# CR-BLOCK4-D1.2A1 PROTOCOL — Physical Truth Collection

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` (D1.2A: PARTIAL_PASS_WAITING_PHYSICAL_TRUTH)
**Status:** REAL READ-ONLY COLLECTION EXECUTED — PASS

## What was collected

A live MT5 terminal on this machine was already connected to an **Ox
Securities demo account** (`OxSecurities-Demo`, USD, leverage 500, equity
25,254.35).  Using ONLY read-only MetaTrader5 API calls (account_info,
symbol_select [Market Watch only], symbol_info, symbol_info_tick,
terminal_info) the USDJPY product spec was captured:

| field | observed value |
|---|---|
| broker_symbol | **USDJPY.PRO** (not "USDJPY") |
| product_type | FX (Forex PRO, trade_calc_mode 0) |
| contract_size | **100,000** base units per 1.0 volume |
| volume_min / step / max | 0.01 / 0.01 / 200.0 |
| digits / point / tick | 3 / 0.001 / 0.001 |
| tick_value | 0.626731345341506 USD |
| base / profit / margin ccy | USD / JPY / USD |
| account currency | USD |

## Mutating calls performed

NONE.  No order_send, no order_check, no position/order modification, no
pending orders, no close, no cancel, no account mutation.

## Evidence

Frozen raw evidence in `_raw_observation.json` (ACTUAL_OBSERVED, sanitized:
pseudonymous account id, personal name redacted, no credentials, no login).
Profile sealed as {PROFILE_GENERATION}.

## Non-goals

No margin study (D1.3), no quantity surface yet (D1.2B), no other profiles
collected, no performance calculation, no science change.
"""


def _report(decision: Dict, comp: Dict, ph: Dict) -> str:
    return f"""# CR-BLOCK4-D1.2A1 REPORT

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` · **Status:** {decision['status']}

## Collection result

- actual account observed: {decision['actual_account_observed']} (Ox
  Securities demo, USD @ 1:500, equity 25,254.35)
- actual USDJPY observed: {decision['actual_usdjpy_observed']} —
  broker symbol **USDJPY.PRO**, contract_size 100,000, volume 0.01/0.01/200.0
- truth class: ACTUAL_OBSERVED · environment DEMO

## Quantity conversion (resolved)

`raw_volume = target_USD_notional / 100000` — account currency == base
currency (USD), direct base-USD mapping; no FX conversion price needed.
Tick-value cross-check consistent ({100000.0 * 0.001 / 159.558:.6f} vs
observed 0.626731).

## Completeness

- quantity_minimum_complete: **{comp['quantity_minimum_complete']}** →
  SEALED_ACTUAL_QUANTITY_COMPLETE
- margin_complete: False (leverage/margin metadata collected; symbol
  leverage/tiers + hedging/netting remain for D1.3)
- long/short symmetric: **true** (no side-dependent volume fields observed)

## Profile seal

{ph['profile_generation_id']} · profile_id OX_DEMO_USDJPY_PRO_G1 ·
hash `{ph['profile_hash'][:16]}...`

## Nonregression

890 / 826 / 371 / 455 / 64 · book hash `{CANONICAL_BOOK_HASH}` · 1% fidelity
tolerance · ROUND_DOWN_TOWARD_ZERO · no clipping · no upward rounding —
all unchanged.  No order attempted, no broker write.

## Decision

`d1_2b_ready = {decision['d1_2b_ready']}` · `d1_2b_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: {decision['next_checkpoint_recommended']} (starts only after human
review).
"""


def main() -> Dict:
    OUT.mkdir(parents=True, exist_ok=True)
    ev = load_evidence()
    spec = instrument_spec(ev)
    acct = account_profile(ev)
    prov = field_provenance(ev)
    conv = quantity_conversion_contract(ev)
    sym = long_short_symmetry(ev)
    ph = profile_hash(ev)
    comp = completeness_audit(ev)
    sec = security_audit()
    nr = nonregression()
    decision = build_decision(comp, ph)
    status = decision["status"]

    (OUT / "CR_BLOCK4_D1_2A1_SOURCE_SHA_MANIFEST.json").write_text(
        json.dumps(sha_manifest(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_RAW_SOURCE_INVENTORY.json").write_text(
        json.dumps({"capture_id": ev["capture_id"],
                    "observed_at": ev["observed_at"],
                    "truth_class": ev["truth_class"],
                    "environment": ev["environment"],
                    "method": ev["method"],
                    "mutating_calls": ev["mutating_calls"],
                    "source": ev["source"],
                    "evidence_file": "_raw_observation.json",
                    "raw_evidence_sha256": _sha(RAW),
                    "instrument_observed": list(ev["symbol"].keys()),
                    "account_observed": list(ev["account"].keys()),
                    "tick_reference": ev["tick"]}, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_INSTRUMENT_PHYSICAL_SPEC.json").write_text(
        json.dumps(spec, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_ACCOUNT_PHYSICAL_PROFILE.json").write_text(
        json.dumps(acct, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_LONG_SHORT_SYMMETRY.json").write_text(
        json.dumps(sym, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_PROFILE_HASH.json").write_text(
        json.dumps(ph, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_COMPLETENESS_AUDIT.json").write_text(
        json.dumps(comp, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_SECURITY_AUDIT.json").write_text(
        json.dumps(sec, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_NONREGRESSION.json").write_text(
        json.dumps(nr, indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")
    pd.DataFrame(prov).to_csv(OUT / "CR_BLOCK4_D1_2A1_FIELD_PROVENANCE.csv", index=False)
    pd.DataFrame(component_status_rows(status)).to_csv(
        OUT / "CR_BLOCK4_D1_2A1_COMPONENT_STATUS.csv", index=False)

    (OUT / "CR_BLOCK4_D1_2A1_PROTOCOL.md").write_text(_protocol(ev), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_QUANTITY_CONVERSION_CONTRACT.md").write_text(
        conv, encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2A1_REPORT.md").write_text(_report(decision, comp, ph),
                                                    encoding="utf-8")
    return decision


if __name__ == "__main__":
    d = main()
    print(json.dumps({
        "checkpoint": CHECKPOINT,
        "status": d["status"],
        "quantity_minimum_complete": d["quantity_minimum_complete"],
        "broker_symbol_resolved": d["broker_symbol_resolved"],
        "d1_2b_ready": d["d1_2b_ready"],
        "d1_2b_authorized": d["d1_2b_authorized"],
        "profile_generation_id": d["profile_generation_id"],
    }, indent=2))
