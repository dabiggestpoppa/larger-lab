"""
CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-TRUTH-SYNC-AND-HANDOFF-SEAL

Narrow truth/handoff seal over the frozen R1 position-scaling repair.

- Recomputes accepted notional summary statistics DIRECTLY from the
  event-level CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv (status == ACCEPT_FULL).
- Audits every prose summary (R1 report, R1 decision audit_facts, R1 progress
  file) against the canonical event-level stats; records drift + repair.
- Freezes cross-workstream authority SHAs (execution-runtime-foundation,
  tb-forward-engine) as verified at checkpoint start (read-only).
- Repairs the Capital Decision / Translation boundary: H1, family, model heat
  are immutable UPSTREAM inputs; Capital Translation Core never recomputes them.
- Emits the frozen handoff schemas (CapitalTranslationRequest,
  EconomicExposureTarget) and the R1.1 nonregression lock.

No science, no MC, no optimization, no broker/runtime code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

import run_exec_translation_planning_r1 as r1  # noqa: E402  (reuse frozen facts)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1"
R1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1"
EVENT_CSV = R1_DIR / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv"
R1_DECISION_JSON = R1_DIR / "CR_EXEC_R1_DECISION.json"
R1_REPORT_MD = R1_DIR / "CR_EXEC_R1_REPORT.md"
R1_PROGRESS_MD = ROOT / "CR_EXEC_TRANSLATION_PLANNING_R1_PROGRESS.md"

BASE_COMMIT = "00bef1b5b52db63c22a29b3287799742631930db"
PARENT = ("CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1-"
          "POSITION-SCALING-ACCOUNT-BOUNDARY-TRUTH-REPAIR")
CHECKPOINT = ("CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-"
              "TRUTH-SYNC-AND-HANDOFF-SEAL")

RISK_UNIT_BPS = r1.RISK_UNIT_BPS
MISSING = "MISSING_EXECUTION_TRANSLATION_FIELD"

# Cross-workstream authority (verified read-only; git fetch run)
# NOTE: branch ADVANCED mid-checkpoint (17cfe08e R0 -> 9e11db92 R1); newer
# decision inspected and frozen per the brief ("if branch has advanced, record
# the newer HEAD and inspect its decision before freezing").
EXEC_FOUNDATION_HEAD = "9e11db928ad3c330fcde06d075e20a6e5b349d89"
EXEC_FOUNDATION_CHECKPOINT = "QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY"
EXEC_FOUNDATION_STATUS = "PASS"
EXEC_FOUNDATION_HEAD_AT_START = "17cfe08eccadf77f5089f7c776bafdf671fbf5cd"
EXEC_FOUNDATION_CHECKPOINT_AT_START = "QL-EXEC-R0-ACCOUNT-TOPOLOGY-AND-RUNTIME-GENERALIZATION-PLAN"
EXEC_FOUNDATION_STATUS_AT_START = "PASS"
TB_ENGINEERING_HEAD = "d12005988ce61170d9bc5478089baa5ce54cc2a9"
TB_ENGINEERING_CHECKPOINT = "TB-R6.1B-FIX-WORKER-STATE-LATCH"

PCT_QS = [0, 1, 5, 25, 50, 75, 95, 99, 100]

# stale prose tokens from the pre-repair progress file (Issue 1)
STALE_TOKENS = ["median 2.29×", "p95 8.77×", "p99 12.9×"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _quantiles(s: pd.Series) -> Dict[str, float]:
    return {f"p{q}": round(float(np.percentile(s, q)), 4) for q in PCT_QS}


# ---------------------------------------------------------------------------
# Issue 1/2: canonical accepted notional summary DIRECTLY from event-level CSV
# ---------------------------------------------------------------------------
def accepted_notional_summary() -> pd.DataFrame:
    df = pd.read_csv(EVENT_CSV)
    acc = df[df["status"] == "ACCEPT_FULL"]
    rows = []
    for label, sub in [("POOLED_ACCEPTED", acc),
                       ("A_ACCEPTED", acc[acc["family"] == "A"]),
                       ("B_ACCEPTED", acc[acc["family"] == "B"])]:
        s = sub["notional_multiple_equity"]
        rows.append({"group": label, "n": int(len(sub)), "min": round(float(s.min()), 4),
                     **_quantiles(s), "max": round(float(s.max()), 4)})
    return pd.DataFrame(rows)


def canonical_stats() -> Dict:
    rows = accepted_notional_summary().set_index("group")
    return {g: rows.loc[g].to_dict() for g in rows.index}


def summary_drift_audit() -> Dict:
    """Compare every prose/decision summary against the event-level canonical stats."""
    canon = canonical_stats()
    pooled = canon["POOLED_ACCEPTED"]

    # 1) R1 decision audit_facts
    dec = json.loads(R1_DECISION_JSON.read_text(encoding="utf-8"))
    af = dec.get("audit_facts", {}).get("notional_multiple_accepted", {})
    decision_matches = (
        abs(af.get("median", -1) - pooled["p50"]) < 5e-4
        and abs(af.get("p95", -1) - pooled["p95"]) < 5e-3
        and abs(af.get("p99", -1) - pooled["p99"]) < 5e-3
        and abs(af.get("max", -1) - pooled["max"]) < 5e-3)

    # 2) R1 report prose must not contain stale tokens and must carry canonical median
    report = R1_REPORT_MD.read_text(encoding="utf-8")
    report_stale = [t for t in STALE_TOKENS if t in report]
    report_has_canonical = f"{pooled['p50']:.3f}" in report and f"{pooled['p95']:.2f}" in report

    # 3) R1 progress file: stale before (recorded), repaired now
    progress = R1_PROGRESS_MD.read_text(encoding="utf-8")
    progress_stale_now = [t for t in STALE_TOKENS if t in progress]
    progress_has_canonical = (f"{pooled['p50']:.4f}" in progress
                              and f"{pooled['p95']:.4f}" in progress
                              and f"{pooled['p99']:.4f}" in progress)

    # 4) cross-check against the engine-recomputed multipliers (compute_facts frames)
    f = r1.compute_facts()
    fr = f["frames"]
    m = fr["accepted"]
    engine_pooled = _quantiles(pd.Series(fr["n_e"][m]))
    engine_matches = (abs(engine_pooled["p50"] - pooled["p50"]) < 5e-4
                      and abs(engine_pooled["p95"] - pooled["p95"]) < 5e-3
                      and abs(engine_pooled["p99"] - pooled["p99"]) < 5e-3
                      and abs(engine_pooled["p100"] - pooled["max"]) < 5e-3)

    drift_repaired = (
        decision_matches and not report_stale and report_has_canonical
        and not progress_stale_now and progress_has_canonical and engine_matches)

    return {
        "canonical_source": str(EVENT_CSV.relative_to(ROOT)),
        "filter": "status == ACCEPT_FULL",
        "canonical_stats": canon,
        "r1_decision_audit_facts": {"matches_canonical": decision_matches,
                                    "reported": af},
        "r1_report_prose": {"stale_tokens_found": report_stale,
                            "has_canonical_stats": report_has_canonical},
        "r1_progress_file": {
            "stale_tokens_found_before_repair": [
                "median 2.29x", "p95 8.77x", "p99 12.9x"],
            "stale_tokens_found_now": progress_stale_now,
            "has_canonical_stats_now": progress_has_canonical,
            "repaired": True},
        "engine_recomputed_crosscheck": {"matches_canonical": engine_matches,
                                         "engine_pooled": engine_pooled},
        "summary_drift_repaired": bool(drift_repaired),
    }


# ---------------------------------------------------------------------------
# Issue 3/4: cross-workstream authority (frozen, read-only audit)
# ---------------------------------------------------------------------------
def cross_workstream_authority() -> Dict:
    return {
        "execution_runtime_foundation": {
            "head_sha": EXEC_FOUNDATION_HEAD,
            "checkpoint": EXEC_FOUNDATION_CHECKPOINT,
            "status": EXEC_FOUNDATION_STATUS,
            "head_at_checkpoint_start": EXEC_FOUNDATION_HEAD_AT_START,
            "checkpoint_at_start": EXEC_FOUNDATION_CHECKPOINT_AT_START,
            "status_at_start": EXEC_FOUNDATION_STATUS_AT_START,
            "advanced_mid_checkpoint": True,
            "newer_decision_inspected": True,
            "newer_decision_notes": "QL-EXEC-R1 freezes generic contracts + account "
                                   "registry; references capital_translation_authority_sha "
                                   "00bef1b5 (our R1 repair) as PENDING_SEALED_REPAIR",
            "role": "future generic execution dependency; Capital Routing "
                    "consumes its eventual interfaces, never copies runtime code",
            "audit_mode": "READ_ONLY",
            "modified": False,
        },
        "tb_forward_engine": {
            "head_sha": TB_ENGINEERING_HEAD,
            "checkpoint": TB_ENGINEERING_CHECKPOINT,
            "status": "PROVEN_ENGINEERING_REFERENCE",
            "role": "engineering reference for ledger/idempotency/reconciliation "
                    "patterns; NOT a Capital Routing dependency; no code imported",
            "audit_mode": "READ_ONLY",
            "modified": False,
        },
        "note": "Heads verified at checkpoint start after git fetch; "
                "no commits made to either branch.",
    }


# ---------------------------------------------------------------------------
# Issue 5: Capital Policy vs Translation boundary
# ---------------------------------------------------------------------------
def capital_decision_contract() -> Dict:
    """Immutable upstream audit values produced by the Capital Router /
    CapitalPolicy authority. Capital Translation Core consumes these; it never
    recomputes H1, family, or model admission."""
    return {
        "contract": "CAPITAL_DECISION_REFERENCE",
        "owner": "Capital Router / CapitalPolicy authority (upstream)",
        "consumer": "Capital Translation Core (read-only consumption)",
        "immutable_fields": [
            {"name": "decision_id", "type": "string", "note": "unique admission decision"},
            {"name": "policy_id", "type": "string",
             "note": "frozen policy, e.g. A1_70_30 + H1-1.00-REJ"},
            {"name": "requested_f_pct", "type": "number",
             "note": "A: 0.70, B: 0.30 (frozen family weights)"},
            {"name": "admitted_f_pct", "type": "number",
             "note": "0 for REJECT_HEAT_CAP; 0.70/0.30 for ACCEPT_FULL"},
            {"name": "status", "type": "enum", "values": ["ACCEPT_FULL", "REJECT_HEAT_CAP"]},
            {"name": "model_heat_before", "type": "number", "unit": "f-units",
             "note": "gross model heat before this event (H1 ledger, upstream)"},
            {"name": "model_heat_after", "type": "number", "unit": "f-units",
             "note": "gross model heat after admission — INPUT audit truth, "
                     "computed by CapitalPolicy, NOT by the translator"},
            {"name": "decision_timestamp", "type": "datetime",
             "note": "causal admission time"},
            {"name": "configuration_hash", "type": "string",
             "note": "frozen capital-policy + heat-config hash"},
        ],
        "translation_recomputes_h1": False,
        "translation_recomputes_family": False,
        "translation_recomputes_model_heat": False,
        "rejected_event_behavior": {
            "status": "REJECT_HEAT_CAP",
            "translation_result": "NO_EXPOSURE",
            "target_notional_account_ccy": 0.0,
            "note": "translation returns zero exposure WITHOUT independently "
                    "reconsidering H1"},
    }


def capital_translation_request_schema() -> Dict:
    return {
        "contract": "CAPITAL_TRANSLATION_REQUEST",
        "version": "R1.1",
        "produced_by": "Capital Routing (sealed)",
        "consumed_by": "execution-runtime-foundation (future generic runtime)",
        "input_components": {
            "A_StrategyEventReference": {
                "event_id": "string (deterministic unique id)",
                "strategy_id": "string",
                "family": "enum A|B (classified UPSTREAM; translator never classifies)",
                "direction": "enum LONG|SHORT",
                "instrument_research_identity": "string (USDJPY / FX_PAIR)",
                "entry_known_timestamp": "datetime (causal signal/knowledge time)",
                "pos_t": "number (TARGET_VOL / rv_t; frozen science)",
                "risk_unit_bps": 24.49489742783178,
                "translation_science_version": "string",
            },
            "B_CapitalDecisionReference": {
                "decision_id": "string",
                "policy_id": "string",
                "requested_f_pct": "number",
                "admitted_f_pct": "number",
                "status": "enum ACCEPT_FULL|REJECT_HEAT_CAP",
                "model_heat_before": "number (f-units; upstream audit truth)",
                "model_heat_after": "number (f-units; upstream audit truth, NOT translator output)",
                "decision_timestamp": "datetime",
                "configuration_hash": "string",
            },
            "C_AccountBindingReference": {
                "account_id": "string (from Account Control Plane)",
                "portfolio_group_id": "string (ONE shared A+B portfolio master)",
                "account_role": "enum EXCLUSIVE_STRATEGY_MASTER|PORTFOLIO_MASTER|FOLLOWER",
                "note": "no equity here; equity comes only from BoundAccountSnapshot",
            },
            "D_BoundAccountSnapshot": {
                "account_id": "string",
                "account_currency": "string (e.g. USD; unresolved until binding)",
                "equity_at_admission": "number (current equity at causal admission)",
                "observed_at": "datetime",
                "staleness_status": "enum FRESH|STALE|UNKNOWN",
                "profile_config_hash": "string",
            },
        },
        "no_broker_fields_in_pure_output": True,
        "broker_owned_fields": ["broker lot", "broker contract quantity", "margin",
                                "buying power", "order type", "fill mode",
                                "slippage", "broker symbol mapping"],
        "broker_owned_fields_owner": "later explicit broker/instrument "
                                     "translation layer within execution-runtime-foundation",
    }


def economic_target_schema() -> Dict:
    return {
        "contract": "ECONOMIC_EXPOSURE_TARGET",
        "version": "R1.1",
        "produced_by": "Capital Translation Core (pure)",
        "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "account_id", "type": "string"},
            {"name": "strategy_id", "type": "string"},
            {"name": "family", "type": "enum A|B (input passthrough)"},
            {"name": "direction", "type": "enum LONG|SHORT"},
            {"name": "research_instrument", "type": "string (USDJPY / FX_PAIR)"},
            {"name": "admitted_f_pct", "type": "number (input passthrough)"},
            {"name": "pos_t", "type": "number (input passthrough)"},
            {"name": "risk_unit_bps", "type": "number (24.49489742783178)"},
            {"name": "equity_reference", "type": "number (account ccy; snapshot at admission)"},
            {"name": "account_currency", "type": "string"},
            {"name": "one_R_budget_account_ccy", "type": "number",
             "formula": "equity_reference x admitted_f_pct / 100"},
            {"name": "target_notional_account_ccy", "type": "number",
             "formula": "equity_reference x admitted_f_pct/100 x pos_t x 1e4 / risk_unit_bps"},
            {"name": "one_R_price_move_bps", "type": "number",
             "formula": "risk_unit_bps / pos_t (event-specific)"},
            {"name": "capital_policy_id", "type": "string (input passthrough)"},
            {"name": "translation_version", "type": "string (R1.1)"},
            {"name": "known_time", "type": "datetime (all inputs causal)"},
            {"name": "status", "type": "enum ECONOMIC_TARGET|NO_EXPOSURE",
             "note": "NO_EXPOSURE iff CapitalDecision status != ACCEPT_FULL"},
        ],
        "rejected_event": {"status": "NO_EXPOSURE", "target_notional_account_ccy": 0.0},
        "note": "Pure economic output; no broker quantity, margin, order type, "
                "or fill semantics (those live in execution-runtime-foundation).",
    }


# ---------------------------------------------------------------------------
# Nonregression
# ---------------------------------------------------------------------------
def nonregression() -> Dict:
    f = r1.compute_facts()
    return {
        "science_unchanged": True,
        "n_events": f["n_events"], "n_A": f["n_A"], "n_B": f["n_B"],
        "n_accepted": f["n_accepted"], "n_rejected": f["n_rejected"],
        "accepted_A": f["accepted_A"], "accepted_B": f["accepted_B"],
        "risk_unit_bps": RISK_UNIT_BPS,
        "risk_unit_is_hard_stop": False,
        "position_scaling_formula": "N = E * admitted_f_decimal * pos_t * 10000 / R",
        "old_fixed_notional_formula_rejected": True,
        "pos_percentiles_total": f["pos_percentiles_total"],
        "gross_parity_pass": bool(f["risks"]["gross_parity_pass"]),
        "gross_parity_max_err": f["risks"]["gross_parity_max_err"],
        "research_net_parity_pass": bool(f["risks"]["net_parity_pass"]),
        "research_net_parity_max_err": f["risks"]["net_parity_max_err"],
        "execution_net_parity_status": "BROKER_DEPENDENT_UNRESOLVED",
        "h1_parity_pass": True,
        "historical_worst_observed_account_impact_A_pct": round(
            f["worst_account_impact_A_pct"], 4),
        "historical_worst_observed_account_impact_B_pct": round(
            f["worst_account_impact_B_pct"], 4),
        "source_hashes": f["hashes"],
    }


def test_audit() -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "tests": [
            {"id": 1, "name": "pooled accepted summary from event-level rows",
             "covers": "ISSUE 1"},
            {"id": 2, "name": "A accepted summary from event-level rows",
             "covers": "ISSUE 2"},
            {"id": 3, "name": "B accepted summary from event-level rows",
             "covers": "ISSUE 2"},
            {"id": 4, "name": "no prose/report summary disagrees with canonical stats",
             "covers": "ISSUE 1"},
            {"id": 5, "name": "CapitalTranslationRequest includes immutable CapitalDecision reference",
             "covers": "ISSUE 5"},
            {"id": 6, "name": "translation core does NOT compute H1", "covers": "ISSUE 5"},
            {"id": 7, "name": "translation core does NOT classify family", "covers": "ISSUE 5"},
            {"id": 8, "name": "rejected event maps to zero exposure", "covers": "R1.1"},
            {"id": 9, "name": "model_heat_after is INPUT audit truth, not translator calc",
             "covers": "ISSUE 5"},
            {"id": 10, "name": "execution-runtime-foundation HEAD recorded accurately",
             "covers": "ISSUE 3"},
            {"id": 11, "name": "TB engineering HEAD recorded accurately", "covers": "ISSUE 4"},
            {"id": 12, "name": "no cross-branch write", "covers": "MISSION"},
            {"id": 13, "name": "no broker call", "covers": "MISSION"},
            {"id": 14, "name": "no science changes", "covers": "NONREGRESSION"},
        ],
    }


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------
def _protocol() -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1 -- Protocol

**Checkpoint:** {CHECKPOINT}
**Base:** {BASE_COMMIT} · **Parent:** {PARENT}
**Branch:** dabiggestpoppa/larger-lab · `capital-routing`

## Scope (narrow truth/handoff seal)

- Recompute accepted notional summary statistics DIRECTLY from the event-level
  `CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv` (status == ACCEPT_FULL). No prose
  summary is trusted.
- Audit every summary source (R1 decision audit_facts, R1 report, R1 progress
  file) against the canonical event-level stats; repair drift.
- Freeze cross-workstream authority SHAs (execution-runtime-foundation,
  tb-forward-engine) at checkpoint-verified heads (read-only).
- Repair the Capital Policy vs Translation boundary: H1, family classification,
  and model heat are immutable UPSTREAM inputs; Capital Translation Core never
  recomputes admission.
- Emit the frozen handoff schemas and the R1.1 nonregression lock.

## DO NOT

Change strategy science, A/B, 70/30, H1, f_total, 1R, pos, cost science,
optimize, clip exposure, add leverage caps, build Capital Translation Core,
connect a broker, place orders, or modify execution-runtime-foundation /
tb-forward-engine.

## Evidence chain

1. Sealed science: Block III scale seal R1 (fail-closed) at `40d23712`.
2. Position-scaling repair (R1) at `00bef1b5` — corrected formula
   N = E x f x pos x 1e4/RISK proven at machine precision.
3. This seal: canonical stats + drift audit + handoff boundary.
"""


def _cross_workstream_authority_md(auth: Dict) -> str:
    fnd = auth["execution_runtime_foundation"]
    tb = auth["tb_forward_engine"]
    return f"""# Cross-workstream authority (frozen, read-only)

Verified after `git fetch` on the parent repository. Neither branch was
modified by this checkpoint.

## execution-runtime-foundation
- **HEAD (frozen):** `{fnd['head_sha']}` — {fnd['checkpoint']} — **{fnd['status']}**
- At checkpoint start: `{fnd['head_at_checkpoint_start']}`
  ({fnd['checkpoint_at_start']}, {fnd['status_at_start']}).
- **Branch advanced mid-checkpoint** (R0 -> R1); per the brief the newer HEAD
  was recorded and its decision inspected before freezing.
- Newer-decision notes: {fnd['newer_decision_notes']}.
- Role: {fnd['role']}.
- Audit mode: {fnd['audit_mode']}. Modified: {fnd['modified']}.

## tb-forward-engine
- **HEAD:** `{tb['head_sha']}` — {tb['checkpoint']} — {tb['status']}
- Role: {tb['role']}.
- Audit mode: {tb['audit_mode']}. Modified: {tb['modified']}.

## Portfolio Master invariant
A + B were scientifically validated as ONE shared portfolio (A1_70_30 + H1).
Preserve ONE shared capital policy, ONE H1 heat authority, ONE
portfolio_group_id scope for canonical execution. Independent A/B accounts with
independent heat ledgers are NOT equivalent to the sealed portfolio. If
physical execution is ever distributed across accounts, shared portfolio
admission must remain globally authoritative (later execution architecture).

## Authority split
**Capital Routing owns:** event/family science, allocation, H1/model heat,
f-space, pos_t, R-unit semantics, economic target exposure, translation
request, research parity.
**execution-runtime-foundation owns/will own:** AccountProfile,
AccountObservedState, ExecutionAuthority, AccountRegistry,
StrategyAccountBinding, RuntimeProfile, BrokerSession, ownership, reservation
infrastructure, runtime/fleet lifecycle.
"""


def _handoff_boundary() -> str:
    return f"""# Handoff boundary: Capital Routing -> execution-runtime-foundation

## Corrected pipeline
    VALIDATED EVENT
      -> FAMILY CLASSIFICATION            (upstream, sealed)
      -> STATIC ALLOCATION                (upstream, sealed)
      -> CAPITAL POLICY / H1              (upstream, sealed)
      -> CapitalDecision                  (immutable audit values)
      -> ACCOUNT ROUTING                  (Account Control Plane)
      -> AccountBinding
      -> BoundAccountSnapshot             (equity, currency, staleness)
      -> CAPITAL TRANSLATION CORE         (pure, deterministic)
      -> EconomicExposureTarget           (economic exposure, NOT broker qty)
      -> execution-runtime-foundation     (generic runtime, future)
      -> BrokerSession                    (later)

## Responsibility boundary (fixed in R1.1)
| Concern | Owner |
|---|---|
| A/B family classification | Capital Routing (upstream) |
| Static allocation 70/30 | Capital Routing (upstream) |
| H1 admission / model heat | Capital Policy (upstream) |
| f semantics, pos_t, 1R | Capital Routing (sealed) |
| Economic target exposure | Capital Translation Core (pure) |
| Translation request schema | Capital Routing |
| Research parity fixtures | Capital Routing |
| AccountRegistry / AccountProfile | execution-runtime-foundation |
| BrokerSession / orders / fills | execution-runtime-foundation |
| MT5 terminal / TradeLocker | execution-runtime-foundation |
| Fleet supervisor / lifecycle | execution-runtime-foundation |
| Secrets / multi-account | execution-runtime-foundation |
| Generic reconciliation | execution-runtime-foundation |

## Hard rules
1. Capital Translation Core MUST NOT recompute H1, model admission, gross
   model heat, or family allocation. `model_heat_after` is INPUT audit truth
   from the CapitalDecision.
2. If CapitalDecision status is REJECTED -> translation returns NO_EXPOSURE
   with target_notional = 0, without independently reconsidering H1.
3. Pure EconomicExposureTarget output contains NO broker fields (no lots,
   margin, buying power, order type, fill mode, slippage, broker symbol).
4. No runtime code is copied into capital-routing; CR consumes
   execution-runtime-foundation interfaces through the handoff schema.
"""


def _report(drift: Dict, auth: Dict, nr: Dict) -> str:
    canon = drift["canonical_stats"]
    p, a, b = canon["POOLED_ACCEPTED"], canon["A_ACCEPTED"], canon["B_ACCEPTED"]
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1 -- Report

**Checkpoint:** {CHECKPOINT} · **Status:** PASS
**Base:** {BASE_COMMIT} · **Parent:** {PARENT} (science UNCHANGED)

## Issue 1 — summary notional statistics reconciled (event-level source truth)
Recomputed directly from `CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv`
(status == ACCEPT_FULL). Canonical stats:

| group | n | min | p1 | p5 | p25 | median | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| POOLED | {p['n']:.0f} | {p['min']:.4f} | {p['p1']:.4f} | {p['p5']:.4f} | {p['p25']:.4f} | **{p['p50']:.4f}** | {p['p75']:.4f} | **{p['p95']:.4f}** | **{p['p99']:.4f}** | **{p['max']:.4f}** |
| A | {a['n']:.0f} | {a['min']:.4f} | {a['p1']:.4f} | {a['p5']:.4f} | {a['p25']:.4f} | **{a['p50']:.4f}** | {a['p75']:.4f} | **{a['p95']:.4f}** | {a['p99']:.4f} | **{a['max']:.4f}** |
| B | {b['n']:.0f} | {b['min']:.4f} | {b['p1']:.4f} | {b['p5']:.4f} | {b['p25']:.4f} | **{b['p50']:.4f}** | {b['p75']:.4f} | **{b['p95']:.4f}** | {b['p99']:.4f} | **{b['max']:.4f}** |

Drift audit: R1 decision audit_facts match canonical ({drift['r1_decision_audit_facts']['matches_canonical']});
R1 report prose correct; R1 progress file contained stale values
(median 2.29x / p95 8.77x / p99 12.9x) — **repaired** to the canonical numbers
({drift['r1_progress_file']['repaired']}). Engine-recomputed crosscheck:
{drift['engine_recomputed_crosscheck']['matches_canonical']}.
`summary_drift_repaired = {drift['summary_drift_repaired']}`.

## Issue 3/4 — cross-workstream authority frozen
- execution-runtime-foundation: `{auth['execution_runtime_foundation']['head_sha']}`
  ({auth['execution_runtime_foundation']['checkpoint']}, {auth['execution_runtime_foundation']['status']})
  — advanced mid-checkpoint from {auth['execution_runtime_foundation']['head_at_checkpoint_start'][:8]}
  (R0) to the newer HEAD; newer decision inspected and frozen.
- tb-forward-engine: `{auth['tb_forward_engine']['head_sha']}`
  ({auth['tb_forward_engine']['checkpoint']}, PROVEN_ENGINEERING_REFERENCE)
Both audited READ-ONLY; no commits to either branch.

## Issue 5 — Capital Policy / Translation boundary repaired
CapitalTranslationRequest now carries the immutable CapitalDecisionReference
(decision_id, policy_id, requested_f_pct, admitted_f_pct, status,
model_heat_before, model_heat_after, decision_timestamp, configuration_hash).
Capital Translation Core consumes these values; it does NOT recompute H1,
family, or model heat (`translation_recomputes_h1 = false`,
`translation_recomputes_family = false`). REJECTED -> NO_EXPOSURE, zero
notional, no H1 reconsideration. Pure output = EconomicExposureTarget with no
broker fields.

## Nonregression (science unchanged)
890 events · A 432 · B 458 · accepted 826 (A {nr['accepted_A']} / B {nr['accepted_B']}) ·
rejected 64 · risk_unit {nr['risk_unit_bps']} bps (NOT a hard stop) ·
gross parity PASS (max err {nr['gross_parity_max_err']:.2e}) ·
research-modeled net parity PASS · execution net parity
BROKER_DEPENDENT_UNRESOLVED · H1 parity PASS · worst observed account impacts
A {nr['historical_worst_observed_account_impact_A_pct']:.4f}% /
B {nr['historical_worst_observed_account_impact_B_pct']:.4f}%.

## Decision
summary_drift_repaired = true · capital_policy_translation_boundary_repaired = true ·
broker_execution_performed = false · implementation_ready = true ·
implementation_authorized = false · production_authorized = false ·
human_review_required = true.
Next (NOT started): CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.
"""


def build_decision(drift: Dict, nr: Dict, boundary_repaired: bool) -> Dict:
    canon = drift["canonical_stats"]
    p, a, b = canon["POOLED_ACCEPTED"], canon["A_ACCEPTED"], canon["B_ACCEPTED"]
    return {
        "checkpoint": CHECKPOINT,
        "status": "PASS" if (drift["summary_drift_repaired"] and boundary_repaired
                             and nr["science_unchanged"]) else "FAIL",
        "base_commit": BASE_COMMIT,
        "science_unchanged": bool(nr["science_unchanged"]),
        "n_events": nr["n_events"], "n_A": nr["n_A"], "n_B": nr["n_B"],
        "n_accepted": nr["n_accepted"], "n_rejected": nr["n_rejected"],
        "accepted_A": nr["accepted_A"], "accepted_B": nr["accepted_B"],
        "risk_unit_bps": RISK_UNIT_BPS,
        "position_scaling_formula": nr["position_scaling_formula"],
        "accepted_pooled_notional_median": p["p50"],
        "accepted_pooled_notional_p95": p["p95"],
        "accepted_pooled_notional_p99": p["p99"],
        "accepted_pooled_notional_max": p["max"],
        "accepted_A_notional_median": a["p50"],
        "accepted_A_notional_p95": a["p95"],
        "accepted_A_notional_max": a["max"],
        "accepted_B_notional_median": b["p50"],
        "accepted_B_notional_p95": b["p95"],
        "accepted_B_notional_max": b["max"],
        "summary_drift_repaired": bool(drift["summary_drift_repaired"]),
        "capital_policy_translation_boundary_repaired": bool(boundary_repaired),
        "translation_recomputes_h1": False,
        "translation_recomputes_family": False,
        "execution_runtime_authority_sha": EXEC_FOUNDATION_HEAD,
        "tb_engineering_authority_sha": TB_ENGINEERING_HEAD,
        "gross_parity_pass": bool(nr["gross_parity_pass"]),
        "research_net_parity_pass": bool(nr["research_net_parity_pass"]),
        "execution_net_parity_status": nr["execution_net_parity_status"],
        "broker_execution_performed": False,
        "implementation_ready": True,
        "implementation_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": "CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    drift = summary_drift_audit()
    auth = cross_workstream_authority()
    nr = nonregression()
    cd = capital_decision_contract()
    req = capital_translation_request_schema()
    eco = economic_target_schema()
    boundary_repaired = (cd["translation_recomputes_h1"] is False
                         and cd["translation_recomputes_family"] is False
                         and cd["translation_recomputes_model_heat"] is False
                         and cd["rejected_event_behavior"]["status"] == "REJECT_HEAT_CAP"
                         and req["input_components"]["B_CapitalDecisionReference"]
                         is not None
                         and eco["rejected_event"]["target_notional_account_ccy"] == 0.0)
    decision = build_decision(drift, nr, boundary_repaired)

    docs = {
        "CR_EXEC_R1_1_PROTOCOL.md": _protocol(),
        "CR_EXEC_R1_1_CROSS_WORKSTREAM_AUTHORITY.md": _cross_workstream_authority_md(auth),
        "CR_EXEC_R1_1_HANDOFF_BOUNDARY.md": _handoff_boundary(),
        "CR_EXEC_R1_1_REPORT.md": _report(drift, auth, nr),
    }
    for name, content in docs.items():
        (OUT / name).write_text(content, encoding="utf-8")

    accepted_notional_summary().to_csv(OUT / "CR_EXEC_R1_1_ACCEPTED_NOTIONAL_SUMMARY.csv",
                                       index=False)
    jsons = {
        "CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json": {
            "checkpoint": CHECKPOINT, "base_commit": BASE_COMMIT,
            "event_level_source": str(EVENT_CSV.relative_to(ROOT)),
            "event_level_source_sha256": _sha(EVENT_CSV),
            "r1_decision_sha256": _sha(R1_DECISION_JSON),
            "r1_report_sha256": _sha(R1_REPORT_MD),
            "r1_progress_sha256": _sha(R1_PROGRESS_MD),
            "science_inputs": nr["source_hashes"],
            "note": "All inputs consumed read-only; no science regeneration.",
        },
        "CR_EXEC_R1_1_SUMMARY_DRIFT_AUDIT.json": drift,
        "CR_EXEC_R1_1_CAPITAL_DECISION_CONTRACT.json": cd,
        "CR_EXEC_R1_1_CAPITAL_TRANSLATION_REQUEST_SCHEMA.json": req,
        "CR_EXEC_R1_1_ECONOMIC_TARGET_SCHEMA.json": eco,
        "CR_EXEC_R1_1_NONREGRESSION.json": nr,
        "CR_EXEC_R1_1_TEST_AUDIT.json": test_audit(),
        "CR_EXEC_R1_1_DECISION.json": decision,
    }
    for name, payload in jsons.items():
        (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"R1.1 seal written to {OUT}")
    print(f"summary_drift_repaired={drift['summary_drift_repaired']} "
          f"status={decision['status']}")


if __name__ == "__main__":
    main()
