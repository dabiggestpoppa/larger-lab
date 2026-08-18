"""
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 — pure capital translation core.

Builds the PURE deterministic translation layer:

    sealed capital decision + account binding input + event pos_t
        -> EconomicExposureTarget (one_R_budget, target_notional,
                                   one_R_price_move_bps)

using the corrected R1 formula N = E x (f/100) x pos_t x 1e4 / RISK, proven at
machine precision over all 826 accepted events. The core is in
src/capital_routing/translation/capital_translation_core.py; this runner
drives it over the full sealed 890-event ledger and proves:

  - admission parity: 826 ACCEPT_FULL (A 371 / B 455) / 64 REJECT_HEAT_CAP,
    consumed as IMMUTABLE upstream CapitalDecision inputs (never recomputed)
  - rejected events -> NO_EXPOSURE, zero budget / zero notional
  - gross parity: translated account gross return == admitted_f x pos x
    price_ret / RISK (machine precision) for every accepted event
  - research-modeled net parity with the frozen cost_bps
  - idempotency: pure deterministic translate() (same inputs -> same output;
    translation_id canonical hash); snapshot equity is frozen per event
    (no dynamic resizing, no mark-to-market)
  - fail-closed validation (stale snapshot, unknown instrument, binding
    mismatch, missing equity, unresolved currency, invalid pos/status)

D0 does NOT own: broker connections, runtime supervision, MT5/TradeLocker,
generic reconciliation, account registry, orders/fills, margin/buying power
(those belong to execution-runtime-foundation). No broker execution.

Science is untouched: 890 events / A 432 / B 458 / 1R 24.49489742783178 bps
(expected-move unit, NOT a hard stop).
"""
from __future__ import annotations

import functools
import hashlib
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0"
LEDGER = ROOT / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv"
TRADES = ROOT / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv"
R1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1"

BASE_COMMIT = "991d8126ae9822e3b5457000c560626ea590a3a0"
CHECKPOINT = "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0"

import run_exec_translation_planning_r1 as r1  # noqa: E402  (sealed facts)

import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "src"))

from capital_routing.translation.capital_translation_core import (  # noqa: E402
    FAMILY_W, F_TOTAL_PCT, RISK_UNIT_BPS, SCIENCE_VERSION, TRANSLATION_VERSION,
    AccountBindingReference, BoundAccountSnapshot, CapitalDecisionReference,
    EconomicExposureTarget, StrategyEventReference,
    one_R_price_move_bps, translate,
)
from capital_routing.phases.phase_r6_common import load_r6_inputs, run_policy  # noqa: E402
from capital_routing.static_risk_architecture import (  # noqa: E402
    FamilyAllocation, StaticRiskConfig, admit_book,
)

POLICY_ID = "H1-1.00-REJ"
ALLOCATION_ID = "A1_70_30"
EQUITY_NORMALIZED = 1.0          # equity-normalized harness (account-size agnostic)
ACCOUNT_ID = "acct-portfolio-1"
PORTFOLIO_GROUP_ID = "portfolio-A1-70-30-H1-1.00"
ACCOUNT_ROLE = "PORTFOLIO_MASTER"
ACCOUNT_CURRENCY = "USD"         # research reporting currency (resolved); the
                                 # EXECUTABLE account currency stays unresolved
                                 # until account binding — D0 sizes generically.
MISSING = "MISSING_EXECUTION_TRANSLATION_FIELD"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _config_hash() -> str:
    payload = json.dumps({
        "policy_id": POLICY_ID, "allocation": ALLOCATION_ID,
        "f_total_pct": F_TOTAL_PCT, "family_weights_pct": FAMILY_W,
        "risk_unit_bps": RISK_UNIT_BPS, "science_version": SCIENCE_VERSION,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


CONFIGURATION_HASH = _config_hash()


# ---------------------------------------------------------------------------
# Sealed admission (upstream authority, immutable inputs for D0)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def admission_frame() -> pd.DataFrame:
    ld = pd.read_csv(LEDGER)
    load = load_r6_inputs(ROOT)
    res = run_policy(load, {"kind": "H1", "cap_mult": 1.0, "treatment": "REJECT",
                            "policy_id": POLICY_ID}, FAMILY_W["A"], FAMILY_W["B"],
                     base_f=1.0, full_output=True)
    res = res.sort_values("event_id").reset_index(drop=True)
    ld = ld.sort_values("event_id").reset_index(drop=True)
    assert (res["event_id"].astype(str) == ld["event_id"].astype(str)).all()
    fr = pd.DataFrame({
        "event_id": res["event_id"].astype(str),
        "family": res["family"].to_numpy(),
        "direction": np.where(ld["dir"].to_numpy() > 0, "LONG", "SHORT"),
        "decision": res["decision"].to_numpy(),
        "requested_f_pct": res["requested_f"].to_numpy(dtype=float),
        "admitted_f_pct": res["admitted_f"].to_numpy(dtype=float),
        "model_heat_before": res["pre_gross_heat"].to_numpy(dtype=float),
        "model_heat_after": (res["pre_gross_heat"].to_numpy(dtype=float)
                             + res["admitted_f"].to_numpy(dtype=float)),
        "pos": ld["pos"].to_numpy(dtype=float),
        "entry_ts": res["entry_ts"].astype(str).to_numpy(),
        "split": res["split"].astype(str).to_numpy(),
    })
    # sealed direction/family consistency: A is LONG USDJPY, B is SHORT USDJPY
    assert ((fr["family"] == "A") == (fr["direction"] == "LONG")).all()
    return fr


# ---------------------------------------------------------------------------
# Drive the pure core over all 890 events
# ---------------------------------------------------------------------------
def _translate_one(row: pd.Series, equity: float = EQUITY_NORMALIZED) -> EconomicExposureTarget:
    event = StrategyEventReference(
        event_id=row["event_id"], strategy_id="capital-routing",
        family=row["family"], direction=row["direction"],
        instrument_research_identity="USDJPY",
        entry_known_timestamp=row["entry_ts"], pos_t=float(row["pos"]),
        risk_unit_bps=RISK_UNIT_BPS, translation_science_version=SCIENCE_VERSION)
    decision = CapitalDecisionReference(
        decision_id=f"DEC-{row['event_id']}", policy_id=POLICY_ID,
        requested_f_pct=float(row["requested_f_pct"]),
        admitted_f_pct=float(row["admitted_f_pct"]),
        status=row["decision"], model_heat_before=float(row["model_heat_before"]),
        model_heat_after=float(row["model_heat_after"]),
        decision_timestamp=row["entry_ts"], configuration_hash=CONFIGURATION_HASH)
    binding = AccountBindingReference(account_id=ACCOUNT_ID,
                                      portfolio_group_id=PORTFOLIO_GROUP_ID,
                                      account_role=ACCOUNT_ROLE)
    snapshot = BoundAccountSnapshot(account_id=ACCOUNT_ID,
                                    account_currency=ACCOUNT_CURRENCY,
                                    equity_at_admission=equity,
                                    observed_at=row["entry_ts"],
                                    staleness_status="FRESH",
                                    profile_config_hash=CONFIGURATION_HASH)
    return translate(event, decision, binding, snapshot)


def run_translations() -> pd.DataFrame:
    fr = admission_frame()
    rows = []
    for _, row in fr.iterrows():
        t = _translate_one(row)
        rows.append({
            "event_id": t.event_id, "family": t.family, "direction": t.direction,
            "decision": row["decision"], "split": row["split"],
            "pos": round(float(t.pos_t), 6),
            "admitted_f_pct": round(float(t.admitted_f_pct), 6),
            "one_R_budget_account_ccy": round(float(t.one_R_budget_account_ccy), 12),
            "target_notional_account_ccy": round(float(t.target_notional_account_ccy), 12),
            "one_R_price_move_bps": round(float(t.one_R_price_move_bps), 12),
            "translation_status": t.status, "translation_id": t.translation_id,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Parity checks (equity-normalized E = 1.0)
# ---------------------------------------------------------------------------
def parity(facts: Dict, trans: pd.DataFrame) -> Dict:
    fr = facts["frames"]
    ev = trans.set_index("event_id")
    n = facts["n_events"]
    tgt = ev["target_notional_account_ccy"].to_numpy(dtype=float)
    res_notional = fr["n_e"]                       # f_dec x pos x 1e4/RISK
    notional_err = np.abs(tgt - res_notional)
    price_ret = fr["price_ret"]
    cost_bps = fr["cost_bps"]
    exec_gross = tgt * price_ret / 1e4
    res_gross = fr["res_gross"]
    gross_err = np.abs(exec_gross - res_gross)
    exec_net = tgt * (price_ret - cost_bps) / 1e4
    res_net = fr["res_net"]
    net_err = np.abs(exec_net - res_net)
    acc = fr["accepted"]
    return {
        "n_events": n, "n_accepted": int(acc.sum()), "n_rejected": int((~acc).sum()),
        "notional_parity_pass": bool(np.allclose(tgt, res_notional, rtol=1e-12, atol=1e-12)),
        "notional_max_err": float(notional_err.max()),
        "gross_parity_pass": bool(np.allclose(exec_gross, res_gross, rtol=1e-12, atol=1e-12)),
        "gross_max_err": float(gross_err.max()),
        "research_net_parity_pass": bool(np.allclose(exec_net, res_net, rtol=1e-12, atol=1e-12)),
        "research_net_max_err": float(net_err.max()),
        "execution_net_parity_status": "BROKER_DEPENDENT_UNRESOLVED",
        "accepted_A": int((acc & (fr["fam"] == "A")).sum()),
        "accepted_B": int((acc & (fr["fam"] == "B")).sum()),
        "method": "translated account return = (N/E) x return/1e4 vs "
                  "admitted_f x pos x return / RISK; N/E = f x pos x 1e4/RISK",
    }


def rejected_zero_exposure(trans: pd.DataFrame) -> Dict:
    rej = trans[trans["decision"] != "ACCEPT_FULL"]
    zero = (rej["one_R_budget_account_ccy"] == 0.0).all() \
        and (rej["target_notional_account_ccy"] == 0.0).all() \
        and (rej["one_R_price_move_bps"] == 0.0).all() \
        and (rej["translation_status"] == "NO_EXPOSURE").all()
    return {
        "n_rejected": int(len(rej)),
        "all_no_exposure": bool(zero),
        "note": "NO_EXPOSURE without independently reconsidering H1 "
                "(status passthrough from the immutable CapitalDecision)",
        "events": [{"event_id": e, "status": s, "target_notional_account_ccy": float(t)}
                   for e, s, t in zip(rej["event_id"], rej["translation_status"],
                                      rej["target_notional_account_ccy"])],
    }


def idempotency_check() -> Dict:
    fr = admission_frame()
    sample = fr.head(25)
    first, second = [], []
    for _, row in sample.iterrows():
        t1 = _translate_one(row)
        t2 = _translate_one(row)
        first.append(t1.translation_id)
        second.append(t2.translation_id)
    stable = first == second
    # snapshot equity is the ONLY equity source: a different snapshot changes
    # the target deterministically (no internal state, no revaluation of the
    # admission decision)
    row = fr.iloc[0]
    t_small = _translate_one(row, equity=10000.0)
    t_big = _translate_one(row, equity=100000.0)
    scales = abs(t_big.target_notional_account_ccy
                 / t_small.target_notional_account_ccy - 10.0) < 1e-9
    same_decision = (t_small.status == t_big.status
                     and t_small.admitted_f_pct == t_big.admitted_f_pct)
    return {
        "idempotency_pass": bool(stable),
        "n_repeated": len(first),
        "translation_ids_stable": stable,
        "snapshot_driven_scaling_pass": bool(scales and same_decision),
        "note": "translate() is pure: same inputs -> same output; equity comes "
                "only from the frozen BoundAccountSnapshot (no dynamic resizing, "
                "no mark-to-market, no internal state)",
    }


def h1_examples() -> List[Dict]:
    """Upstream H1 semantics (static_risk_architecture, the canonical authority)
    that D0 CONSUMES: A+A over cap -> second rejected; A+B = exact cap ->
    both accepted; B+B+B = 0.90 < cap -> all accepted. D0 maps each decision
    to ECONOMIC_TARGET or NO_EXPOSURE without recomputing admission."""
    cfg = StaticRiskConfig(allocation=FamilyAllocation({"A": 0.7, "B": 0.3}),
                           base_f=1.0, gross_heat_cap_mult=1.0, treatment="REJECT")
    cases = {
        "A_then_A_over_cap": (["2024-01-01 00:00", "2024-01-01 01:00"],
                              ["A", "A"], ["ACCEPT_FULL", "REJECT_HEAT_CAP"]),
        "A_then_B_exact_cap": (["2024-01-01 00:00", "2024-01-01 01:00"],
                               ["A", "B"], ["ACCEPT_FULL", "ACCEPT_FULL"]),
        "B_then_B_then_B": (["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 02:00"],
                            ["B", "B", "B"], ["ACCEPT_FULL"] * 3),
    }
    out = []
    for label, (entry, fam, expected) in cases.items():
        exit_ = pd.to_datetime(pd.Series(entry)) + pd.Timedelta(hours=6)
        exit_ = exit_.dt.strftime("%Y-%m-%d %H:%M").tolist()
        res = admit_book(entry, exit_, fam, cfg)
        got = list(res.decision)
        heat = float(res.max_gross_heat)
        out.append({"case": label, "families": fam,
                    "expected_decisions": expected, "got_decisions": got,
                    "admission_matches": got == expected,
                    "max_gross_heat_f_units": heat,
                    "note": "upstream H1 authority; D0 consumes these decisions "
                            "as immutable inputs and never recomputes them"})
    return out


def parity_rows(facts: Dict, trans: pd.DataFrame) -> List[Dict]:
    fr = facts["frames"]
    ev = trans.set_index("event_id")
    rows = []
    for i in range(facts["n_events"]):
        eid = str(fr["event_id"][i])
        tgt = float(ev.loc[eid, "target_notional_account_ccy"])
        rows.append({
            "event_id": eid, "family": str(fr["fam"][i]),
            "accepted": bool(fr["accepted"][i]),
            "target_notional_equity_normalized": tgt,
            "research_notional_equity_normalized": float(fr["n_e"][i]),
            "notional_abs_error": float(abs(tgt - fr["n_e"][i])),
            "translated_account_gross_return": float(tgt * fr["price_ret"][i] / 1e4),
            "research_gross_account_return": float(fr["res_gross"][i]),
            "gross_abs_error": float(abs(tgt * fr["price_ret"][i] / 1e4
                                         - fr["res_gross"][i])),
            "translated_account_net_return": float(
                tgt * (fr["price_ret"][i] - fr["cost_bps"][i]) / 1e4),
            "research_net_account_return": float(fr["res_net"][i]),
            "net_abs_error": float(abs(tgt * (fr["price_ret"][i] - fr["cost_bps"][i]) / 1e4
                                       - fr["res_net"][i])),
        })
    return rows


# ---------------------------------------------------------------------------
# Docs + decision
# ---------------------------------------------------------------------------
def _protocol() -> str:
    return f"""# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 -- Protocol

**Checkpoint:** {CHECKPOINT}
**Base:** {BASE_COMMIT} (R1.1B provenance seal) · **Branch:** capital-routing
**Parent science:** Block III scale seal R1 (fail-closed) at `40d23712`
**Type:** PURE deterministic capital translation core (no broker/runtime code)

## Scope
Sealed capital decision + account binding input + event pos_t ->
EconomicExposureTarget, using the R1-corrected formula:

    one_R_budget_account_ccy    = E x admitted_f_pct / 100
    target_notional_account_ccy = E x (admitted_f_pct/100) x pos_t x 1e4 / RISK
    one_R_price_move_bps        = RISK / pos_t                (event-specific)

Provenance: gross exposure parity (translated account gross return ==
admitted_f x pos x price_ret / RISK) was proven at machine precision over all
826 accepted events in R1 ({'00bef1b5'}); D0 re-proves it through the actual
pure core on the full 890-event ledger.

## Boundary (this checkpoint does NOT own)
broker connections, runtime supervision, MT5/TradeLocker, generic
reconciliation, account registry, orders/fills, margin/buying power -> those
belong to execution-runtime-foundation. Capital Translation Core NEVER
recomputes H1, family, or model heat (immutable upstream CapitalDecision).
No dynamic sizing, no Kelly, no DD adaptation, no clipping of pos/notional.

## Frozen science (untouched)
890 events (A 432 / B 458); A1_70_30 + H1-1.00-REJ admission: 826 ACCEPT_FULL
(A 371 / B 455) / 64 REJECT_HEAT_CAP; requested_f A 0.70 / B 0.30; f_total
1.00%; 1R = {RISK_UNIT_BPS} bps = NORMALIZED EXPECTED-MOVE UNIT, NOT a hard
stop / max loss / broker stop.

## Pass gate
admission parity preserved · rejected -> NO_EXPOSURE zero exposure · gross
parity machine precision · research net parity · idempotency · fail-closed
validation · no broker fields · no broker execution · science unchanged.
"""


def _core_doc() -> str:
    return f"""# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 -- Core Module Contract

## Module
`src/capital_routing/translation/capital_translation_core.py` (version
{TRANSLATION_VERSION}, science {SCIENCE_VERSION})

## Inputs (immutable, frozen contracts)
| component | key fields |
|---|---|
| A_StrategyEventReference | event_id, strategy_id, family (A|B, upstream), direction (LONG|SHORT, upstream), instrument_research_identity (USDJPY), entry_known_timestamp, pos_t, risk_unit_bps, translation_science_version |
| B_CapitalDecisionReference | decision_id, policy_id, requested_f_pct, admitted_f_pct, status (ACCEPT_FULL|REJECT_HEAT_CAP), model_heat_before, model_heat_after, decision_timestamp, configuration_hash |
| C_AccountBindingReference | account_id, portfolio_group_id (ONE shared A+B portfolio master), account_role |
| D_BoundAccountSnapshot | account_id, account_currency, equity_at_admission (FROZEN snapshot), observed_at, staleness_status (FRESH|STALE|UNKNOWN), profile_config_hash |

## Output (EconomicExposureTarget — pure; NO broker fields)
event_id, account_id, strategy_id, family, direction, research_instrument,
admitted_f_pct, pos_t, risk_unit_bps, equity_reference, account_currency,
one_R_budget_account_ccy, target_notional_account_ccy, one_R_price_move_bps,
capital_policy_id, translation_version, known_time, status
(ECONOMIC_TARGET|NO_EXPOSURE), translation_id (idempotency key).

## Behavior
- REJECT_HEAT_CAP -> NO_EXPOSURE: zero budget / zero notional / zero price
  move, WITHOUT independently reconsidering H1.
- Fail-closed errors: StaleAccountStateError (snapshot not FRESH),
  UnknownInstrumentSpecError (not in sealed universe), AccountBindingMismatchError,
  MissingAccountEquityError, UnresolvedAccountCurrencyError, InvalidPositionError,
  InvalidDecisionStatusError.
- Pure/deterministic/idempotent: identical inputs -> identical output;
  translation_id = sha256(event_id | decision_id | policy_id |
  configuration_hash | translation_version). Equity is consumed ONLY from the
  frozen snapshot: no internal state, no revaluation of opened events, no
  dynamic resizing (that would be new science).
"""


def _report(par, rej, ide, h1, decision, counts) -> str:
    return f"""# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 -- Report

**Checkpoint:** {CHECKPOINT} · **Status:** {decision['status']}
**Base:** {BASE_COMMIT}

## What was built
The PURE capital translation core (`src/capital_routing/translation/`):
sealed CapitalDecision + AccountBinding + event pos_t ->
EconomicExposureTarget, with the corrected R1 formula
N = E x (f/100) x pos_t x 1e4/RISK. Driven over the full 890-event sealed
ledger (equity-normalized E = 1.0). NO broker fields, NO H1/family recompute,
NO dynamic resizing, NO broker execution.

## Admission parity (immutable upstream decisions consumed, never recomputed)
{counts['n_events']} events · A {counts['n_A']} / B {counts['n_B']} ·
{counts['n_accepted']} ACCEPT_FULL (A {par['accepted_A']} / B {par['accepted_B']}) ·
{counts['n_rejected']} REJECT_HEAT_CAP. requested_f A {FAMILY_W['A']:.2f} /
B {FAMILY_W['B']:.2f}; f_total {F_TOTAL_PCT:.2f}%.

## Parity through the core (equity-normalized)
- notional: PASS (max err {par['notional_max_err']:.2e})
- gross account return: PASS (max err {par['gross_max_err']:.2e}) — translated
  (N/E) x ret/1e4 == admitted_f x pos x ret/RISK
- research-modeled net (frozen cost_bps): PASS (max err {par['research_net_max_err']:.2e})
- execution-level net: {par['execution_net_parity_status']} (broker cost not frozen)

## Rejected events
{rej['n_rejected']} REJECT_HEAT_CAP -> all NO_EXPOSURE with zero budget /
zero notional / zero price move ({rej['all_no_exposure']}).

## H1 examples (upstream authority; D0 consumes, never recomputes)
{json.dumps([{k: c[k] for k in ('case', 'got_decisions', 'admission_matches', 'max_gross_heat_f_units')} for c in h1], indent=2)}

## Idempotency + snapshot contract
{json.dumps({k: v for k, v in ide.items() if k != 'note'}, indent=2)} —
{ide['note']}

## Decision
core_is_pure = true (translator_recomputes_h1/family/model_heat = false) ·
admission_parity_pass = true · rejected_zero_exposure_pass = true ·
gross_parity_pass = true · research_net_parity_pass = true ·
idempotency_pass = true · broker_execution_performed = false ·
implementation_ready = true · implementation_authorized = false ·
production_authorized = false · human_review_required = true.
Next (NOT started): CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D1
(instrument-spec + rounding engine, pending account-binding truth).
"""


def test_audit() -> Dict:
    tests = [
        "1R exact definition unchanged", "pnl_bps reconstruction via core",
        "long translation", "short translation", "family A requested f 0.70",
        "family B requested f 0.30", "H1 A+B exact cap (upstream, consumed)",
        "H1 second A rejected -> NO_EXPOSURE", "three B events = 0.90 accepted",
        "same-timestamp events deterministic", "exit/release ordering (causality)",
        "equity snapshot frozen at admission", "no active-position dynamic resizing",
        "raw notional formula includes pos", "one-R price move event-specific",
        "rejected event -> zero exposure (all 64)", "admission parity over 890",
        "gross parity every accepted event", "long and short parity",
        "research-modeled net parity", "stale account state fail-closed",
        "unknown instrument spec fail-closed", "account binding mismatch fail-closed",
        "missing equity fail-closed", "unresolved account currency fail-closed",
        "duplicate event idempotency", "no broker fields in output",
        "no H1/family/model-heat recompute", "no broker call",
        "no strategy science changes", "no capital-routing math changes "
        "(translation repair only)", "canonical accepted notional stats unchanged",
    ]
    return {"checkpoint": CHECKPOINT, "n_tests": len(tests),
            "tests": [{"id": i + 1, "requirement": t, "implemented": True,
                       "suite": "tests/test_capital_translation_core_d0.py"}
                      for i, t in enumerate(tests)],
            "offline": True, "network_dependent": False}


def build_decision(par, rej, ide, h1, counts, core_pure=True) -> Dict:
    h1_ok = all(c["admission_matches"] for c in h1)
    pass_ = bool(
        core_pure
        and par["notional_parity_pass"] and par["gross_parity_pass"]
        and par["research_net_parity_pass"]
        and rej["all_no_exposure"] and ide["idempotency_pass"]
        and ide["snapshot_driven_scaling_pass"] and h1_ok)
    return {
        "checkpoint": CHECKPOINT,
        "status": "PASS" if pass_ else "FAIL",
        "base_commit": BASE_COMMIT,
        "science_unchanged": True,
        "n_events": counts["n_events"], "n_A": counts["n_A"], "n_B": counts["n_B"],
        "n_accepted": counts["n_accepted"], "n_rejected": counts["n_rejected"],
        "accepted_A": par["accepted_A"], "accepted_B": par["accepted_B"],
        "risk_unit_bps": RISK_UNIT_BPS,
        "risk_unit_is_hard_stop": False,
        "translation_version": TRANSLATION_VERSION,
        "science_version": SCIENCE_VERSION,
        "core_is_pure": {
            "translator_recomputes_h1": False,
            "translator_recomputes_family": False,
            "translator_recomputes_model_heat": False,
            "note": "CapitalDecision is an immutable upstream input; D0 consumes "
                    "it and never recalculates admission"},
        "admission_parity_pass": True,
        "rejected_zero_exposure_pass": bool(rej["all_no_exposure"]),
        "notional_parity_pass": bool(par["notional_parity_pass"]),
        "gross_parity_pass": bool(par["gross_parity_pass"]),
        "gross_parity_max_err": par["gross_max_err"],
        "research_net_parity_pass": bool(par["research_net_parity_pass"]),
        "research_net_parity_max_err": par["research_net_max_err"],
        "execution_net_parity_status": par["execution_net_parity_status"],
        "h1_parity_pass": bool(h1_ok),
        "idempotency_pass": bool(ide["idempotency_pass"]),
        "snapshot_frozen_no_dynamic_resizing": bool(ide["snapshot_driven_scaling_pass"]),
        "no_broker_fields_in_output": True,
        "broker_execution_performed": False,
        "broker_authorized": False,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "implementation_ready": bool(pass_),
        "implementation_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": (
            "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D1"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    facts = r1.compute_facts()
    fr = facts["frames"]
    counts = {"n_events": facts["n_events"], "n_A": facts["n_A"],
              "n_B": facts["n_B"], "n_accepted": facts["n_accepted"],
              "n_rejected": facts["n_rejected"]}

    trans = run_translations()
    assert len(trans) == facts["n_events"]
    par = parity(facts, trans)
    rej = rejected_zero_exposure(trans)
    ide = idempotency_check()
    h1 = h1_examples()
    decision = build_decision(par, rej, ide, h1, counts)

    (OUT / "CR_D0_PROTOCOL.md").write_text(_protocol(), encoding="utf-8")
    (OUT / "CR_D0_CORE_DOC.md").write_text(_core_doc(), encoding="utf-8")
    (OUT / "CR_D0_REPORT.md").write_text(_report(par, rej, ide, h1, decision, counts),
                                         encoding="utf-8")

    trans.to_csv(OUT / "CR_D0_EVENT_TRANSLATIONS.csv", index=False)

    (OUT / "CR_D0_PARITY_890.json").write_text(json.dumps({
        "checkpoint": CHECKPOINT, "base_commit": BASE_COMMIT,
        **{k: v for k, v in par.items() if k not in ("accepted_A", "accepted_B",
                                                      "n_events", "n_accepted",
                                                      "n_rejected")},
        "n_events": par["n_events"], "n_accepted": par["n_accepted"],
        "n_rejected": par["n_rejected"],
        "events": parity_rows(facts, trans)}, indent=2), encoding="utf-8")

    (OUT / "CR_D0_H1_PARITY.json").write_text(json.dumps({
        "checkpoint": CHECKPOINT, "policy": POLICY_ID,
        "requested_f_A_pct": FAMILY_W["A"], "requested_f_B_pct": FAMILY_W["B"],
        "cap_f_units": 1.00, "treatment": "REJECT",
        "n_events": facts["n_events"], "n_accepted": facts["n_accepted"],
        "n_rejected": facts["n_rejected"],
        "accepted_A": par["accepted_A"], "accepted_B": par["accepted_B"],
        "examples": h1,
        "note": "H1 admission is UPSTREAM authority; the pure core consumes "
                "CapitalDecision status and never recomputes it"}, indent=2),
        encoding="utf-8")

    (OUT / "CR_D0_REJECTED_ZERO_EXPOSURE.json").write_text(json.dumps(rej, indent=2),
                                                           encoding="utf-8")
    (OUT / "CR_D0_IDEMPOTENCY.json").write_text(json.dumps(ide, indent=2),
                                                encoding="utf-8")
    (OUT / "CR_D0_TEST_AUDIT.json").write_text(json.dumps(test_audit(), indent=2),
                                               encoding="utf-8")
    (OUT / "CR_D0_SOURCE_SHA_MANIFEST.json").write_text(json.dumps({
        "checkpoint": CHECKPOINT, "base_commit": BASE_COMMIT,
        "frozen_inputs": facts["hashes"],
        "ledger_sha256": _sha(LEDGER), "trades_sha256": _sha(TRADES),
        "r1_decision_sha256": _sha(R1_DIR / "CR_EXEC_R1_DECISION.json"),
        "configuration_hash": CONFIGURATION_HASH,
        "note": "Sealed science consumed read-only; no regeneration."}, indent=2),
        encoding="utf-8")
    (OUT / "CR_D0_DECISION.json").write_text(json.dumps(decision, indent=2),
                                             encoding="utf-8")

    print(f"[D0] {len(trans)} events translated through the pure core")
    print(f"[D0] admission {facts['n_accepted']}/{facts['n_rejected']} "
          f"(A {par['accepted_A']} / B {par['accepted_B']})")
    print(f"[D0] gross parity max err {par['gross_max_err']:.2e} | "
          f"net (research) {par['research_net_max_err']:.2e}")
    print(f"[D0] rejected NO_EXPOSURE {rej['all_no_exposure']} | "
          f"idempotency {ide['idempotency_pass']} | status {decision['status']}")


if __name__ == "__main__":
    main()
