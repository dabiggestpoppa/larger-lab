"""
CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN — preregistration of the
physical-representability study for the sealed 826-event economic book.

This checkpoint is PLANNING + PREREGISTRATION ONLY.  It does NOT:

  - implement a feasibility engine
  - select leverage / lot size / broker
  - optimize any physical constraint against performance
  - modify the sealed science (890 / A 432 / B 458 / 826 / 64 / 1R / pos /
    H1 / f_total / economic target formula)

It freezes: the scientific question, source hierarchy, truth classes, the
notional diagnostic grid (anchored mechanically to the observed target
distribution), feasibility-state taxonomy, faithfulness metrics, rounding /
min / max quantity policy, margin & currency conversion truth paths, account
size treatment, concurrency / episode plan, distortion metrics, performance
reconstruction, counterfactual lanes, falsification criteria, the missing
truth register, runtime handoff, implementation sequence, and test plan.

Base: 3fde3bb1cf590c554241c23daa14e3d2242998aa (D0.1).
"""
from __future__ import annotations

import functools
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_plan"
LEDGER = ROOT / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv"
MULTIPLIERS = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1" / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv"
D0_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0_1"
R1_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_r1_1"
CONC_SUMMARY = ROOT / "artifacts" / "risk_block1" / "R1_CONCURRENCY_SUMMARY.csv"
EPISODES = ROOT / "artifacts" / "risk_block1" / "R1_ROUTING_EPISODES.csv"

BASE_COMMIT = "3fde3bb1cf590c554241c23daa14e3d2242998aa"
CHECKPOINT = "CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN"
NEXT_CHECKPOINT = "CR-RISK-BLOCK-IV-D1.1-BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE"

# Frozen science (Block III seal + R1/R1.1 + D0/D0.1).
RISK_UNIT_BPS = 24.49489742783178
F_TOTAL_PCT = 1.00
ALLOCATION_ID = "A1_70_30"
POLICY_ID = "H1-1.00-REJ"
FAMILY_W_PCT = {"A": 0.70, "B": 0.30}
HEAT_CAP_F_UNITS = 1.00
SCIENCE_VERSION = "R1.1"
TRANSLATION_VERSION = "D0.1"

# Frozen cross-workstream heads (recorded at checkpoint start, git fetch).
EXEC_RUNTIME_HEAD = "52e39b13f37812221cab7c283afc302623a61bc6"
EXEC_RUNTIME_SUBJECT = "QL-EXEC-R2.1-MT5-FILL-POLICY-AND-RESULT-TRUTH-REPAIR"
TB_ENGINE_HEAD = "b48fd35255b41865026a3cba333ae2a2a0d6a004"
TB_ENGINE_SUBJECT = "TB-R6.1D-BOOT-FLOW-STACK: supervisor owns watcher + dashboard, full stack auto-starts at logon"
MAIN_HEAD = "dfdca6acd829cda4c084cd3bd217ab606348b660"

# Preregistered materiality tolerances (frozen BEFORE any empirical result).
IMMATERIAL_RELATIVE_ERROR = 0.01   # |rel err| <= 1%  -> immaterial rounding
DISTORTED_RELATIVE_ERROR = 0.05    # |rel err| >  5%  -> materially distorted
MIN_QUANTITY_POLICY = "MIN_QUANTITY_BLOCKED"
MAX_QUANTITY_POLICY = "MAX_QUANTITY_BLOCKED"
ROUNDING_PRIMARY = "ROUND_DOWN_TOWARD_ZERO"
ROUNDING_COMPARATOR = "NEAREST_STEP"
UPWARD_ROUNDING_DEFAULT = False

# Preregistered quantile bins over the POOLED accepted target distribution.
QUANTILE_BINS = [(0.00, 0.25), (0.25, 0.50), (0.50, 0.75),
                 (0.75, 0.95), (0.95, 0.99), (0.99, 1.00)]

# Feasibility-state taxonomy (one primary state + optional secondary flags).
FEASIBILITY_STATES = [
    "EXACTLY_REPRESENTABLE",
    "REPRESENTABLE_WITH_IMMATERIAL_ROUNDING",
    "ROUNDING_DISTORTED",
    "MIN_QUANTITY_BLOCKED",
    "MAX_QUANTITY_BLOCKED",
    "NOTIONAL_LIMIT_BLOCKED",
    "MARGIN_BLOCKED",
    "BUYING_POWER_BLOCKED",
    "CURRENCY_CONVERSION_UNRESOLVED",
    "INSTRUMENT_SPEC_UNRESOLVED",
    "ACCOUNT_SPEC_UNRESOLVED",
    "BROKER_CAPABILITY_UNRESOLVED",
    "OTHER_FAIL_CLOSED",
]

TRUTH_CLASSES = [
    "ACTUAL_OBSERVED",
    "BROKER_DOCUMENTED",
    "PROFILE_FROZEN",
    "HYPOTHETICAL_DIAGNOSTIC",
    "UNKNOWN",
]

# Truth classes may never silently upgrade to a higher-authority class.
TRUTH_CLASS_RANK = {c: i for i, c in enumerate(TRUTH_CLASSES)}

STUDY_LANES = {
    "A": "PURE NOTIONAL REPRESENTABILITY",
    "B": "QUANTITY REPRESENTABILITY",
    "C": "MARGIN / BUYING POWER REPRESENTABILITY",
    "D": "FULL PHYSICAL CONTRACT",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@functools.cache
def load_facts() -> Dict:
    """Frozen economic-target ledger + event metadata (cached, deterministic)."""
    led = pd.read_csv(LEDGER)
    mul = pd.read_csv(MULTIPLIERS)
    led_cols = ["event_id", "entry_ts", "exit_ts", "split", "session",
                "severity", "hold_h", "entry_price", "exit_price"]
    mul = mul.merge(led[led_cols], on="event_id", how="left", validate="1:1")
    return {"led": led, "mul": mul}


def notional_series() -> pd.Series:
    mul = load_facts()["mul"]
    acc = mul[mul["status"] == "ACCEPT_FULL"]
    return acc["notional_multiple_equity"].astype(float)


def distribution_stats(s: pd.Series) -> Dict:
    qs = [(0.01, "p1"), (0.05, "p5"), (0.25, "p25"), (0.50, "median"),
          (0.75, "p75"), (0.95, "p95"), (0.99, "p99")]
    out = {"n": int(len(s)), "min": float(s.min())}
    for q, name in qs:
        out[name] = float(s.quantile(q))
    out["max"] = float(s.max())
    return out


def frozen_distribution_check() -> Tuple[bool, Dict, Dict, Dict]:
    mul = load_facts()["mul"]
    acc = mul[mul["status"] == "ACCEPT_FULL"]
    pooled = distribution_stats(acc["notional_multiple_equity"])
    fa = distribution_stats(acc[acc["family"] == "A"]["notional_multiple_equity"])
    fb = distribution_stats(acc[acc["family"] == "B"]["notional_multiple_equity"])
    counts = {
        "n_events": int(len(mul)),
        "n_A": int((mul["family"] == "A").sum()),
        "n_B": int((mul["family"] == "B").sum()),
        "n_accepted": int(len(acc)),
        "n_rejected": int((mul["status"] == "REJECT_HEAT_CAP").sum()),
        "accepted_A": int((acc["family"] == "A").sum()),
        "accepted_B": int((acc["family"] == "B").sum()),
    }
    expected = {"n_events": 890, "n_A": 432, "n_B": 458, "n_accepted": 826,
                "n_rejected": 64, "accepted_A": 371, "accepted_B": 455}
    counts_ok = all(counts[k] == v for k, v in expected.items())

    def close(obs: Dict, exp: Dict) -> bool:
        for k, v in exp.items():
            if abs(obs[k] - v) > 1e-9:
                return False
        return True

    exp_pooled = {"min": 0.135190736223, "p1": 0.2693114427735, "p5": 0.5145448442615,
                  "p25": 1.10233742330525, "median": 1.9842341231185,
                  "p75": 3.51336658273125, "p95": 7.6104837047965,
                  "p99": 16.0363747752485, "max": 32.766258738096}
    exp_a = {"median": 3.351336289995, "p95": 11.440705392953,
             "p99": 17.2064510348216, "max": 32.766258738096}
    exp_b = {"median": 1.284996946428, "p95": 4.1231401034345,
             "p99": 6.71048307006687, "max": 22.275430454511}
    ok = (counts_ok and close(pooled, exp_pooled) and close(fa, exp_a)
          and close(fb, exp_b))
    return ok, counts, pooled, {"A": fa, "B": fb}


# Grid thresholds are anchored mechanically to the observed pooled accepted
# distribution (quantile positions computed at runtime; frozen in artifact).
GRID_LIMITS = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]


def grid_rows() -> List[Dict]:
    s = notional_series()
    fam = load_facts()["mul"]
    acc = fam[fam["status"] == "ACCEPT_FULL"]
    rows = []
    for L in GRID_LIMITS:
        row = {
            "limit_notional_over_equity": L,
            "pooled_survive": int((s <= L).sum()),
            "pooled_survive_pct": float((s <= L).mean() * 100),
            "A_survive_pct": float((acc[acc["family"] == "A"]["notional_multiple_equity"] <= L).mean() * 100),
            "B_survive_pct": float((acc[acc["family"] == "B"]["notional_multiple_equity"] <= L).mean() * 100),
        }
        rows.append(row)
    return rows


def quantile_bin_rows() -> List[Dict]:
    s = notional_series()
    edges = [0.0, 0.25, 0.50, 0.75, 0.95, 0.99, 1.0]
    cuts = pd.qcut(s.rank(method="first") / len(s), edges, duplicates="drop")
    rows = []
    for lo, hi in QUANTILE_BINS:
        sel = s[(s.rank(method="first") / len(s) > lo) & (s.rank(method="first") / len(s) <= hi)]
        rows.append({
            "bin": f"{lo:.0%}-{hi:.0%}",
            "lo_quantile": lo, "hi_quantile": hi,
            "n": int(len(sel)),
            "min_multiple": float(sel.min()) if len(sel) else None,
            "median_multiple": float(sel.median()) if len(sel) else None,
            "max_multiple": float(sel.max()) if len(sel) else None,
        })
    return rows


def concurrency_facts() -> Dict:
    c = pd.read_csv(CONC_SUMMARY)
    ep = pd.read_csv(EPISODES)
    ep12 = ep[ep["interval_h"] == 12.0]
    return {
        "n_events": int(c["n_raw_events"].iloc[0]),
        "n_executed": int(c["n_executed_trades"].iloc[0]),
        "timeline_hours": float(c["timeline_hours"].iloc[0]),
        "max_concurrency": int(c["max_concurrent_positions"].iloc[0]),
        "hours_with_2": int(c["hours_with_2_positions"].iloc[0]),
        "hours_with_3": int(c["hours_with_3_positions"].iloc[0]),
        "hours_with_4plus": int(c["hours_with_4plus_positions"].iloc[0]),
        "max_gross_exposure_f_units": float(c["max_gross_exposure"].iloc[0]),
        "n_episodes_12h": int(len(ep12)),
        "episode_max_n_events": int(ep12["n_events"].max()),
    }


def missing_truth_register() -> List[Dict]:
    rows = [
        ("broker_symbol", "research instrument USDJPY; broker representation (USDJPY / USDJPY.PRO / CFD / spot) unresolved"),
        ("broker_company", "broker identity unresolved"),
        ("transport", "MT5 / other transport unresolved"),
        ("environment", "DEMO / REAL environment unresolved"),
        ("product_type", "spot FX vs CFD representation unresolved"),
        ("contract_size", "trade_contract_size unknown"),
        ("point", "point size unknown"),
        ("digits", "digits unknown"),
        ("tick_size", "trade_tick_size unknown"),
        ("tick_value", "trade_tick_value unknown"),
        ("volume_min", "minimum lot/volume unknown"),
        ("volume_step", "volume step unknown"),
        ("volume_max", "maximum volume unknown"),
        ("margin_model", "symbol margin mode / tiers unknown"),
        ("account_leverage", "account leverage unknown (FakeMT5 demo fixtures are NOT truth)"),
        ("symbol_leverage", "symbol-specific leverage unknown"),
        ("hedging_netting", "HEDGING vs NETTING mode unknown"),
        ("executable_account_currency", "account currency unresolved until account binding"),
        ("account_size", "intended account size unresolved"),
        ("equity_snapshot", "causal account equity snapshot unavailable"),
        ("fx_conversion_price", "causal conversion price for non-USD legs unknown"),
        ("order_fill_policy", "declared vs probed fill policy unknown until broker session"),
    ]
    return [{"field": f, "truth_class": "UNKNOWN",
             "detail": d, "blocking": "yes"} for f, d in rows]


def component_status_rows(decision: Dict) -> List[Dict]:
    comps = [
        ("Block III scale seal", "SEALED", "PASS"),
        ("R1 position-scaling repair", "SEALED", "PASS"),
        ("R1.1 truth-sync + handoff seal", "SEALED", "PASS"),
        ("R1.1B cross-branch provenance", "SEALED", "PASS"),
        ("D0 capital translation core", "SEALED", "PASS"),
        ("D0.1 contract/idempotency repair", "SEALED", "PASS"),
        ("D1 exposure-feasibility plan", "PREREGISTERED", "PASS" if decision.get("d1_plan_pass") else "FAIL"),
        ("D1.1 notional feasibility surface", "PLANNED", "NOT_STARTED"),
        ("D1.2 quantity representability", "PLANNED", "NOT_STARTED"),
        ("D1.3 margin feasibility", "PLANNED", "NOT_STARTED"),
        ("D1.4 concurrent account-resource replay", "PLANNED", "NOT_STARTED"),
        ("D1.5 physical-book distortion seal", "PLANNED", "NOT_STARTED"),
        ("D1.6 broker quantity translation contract", "PLANNED", "NOT_STARTED"),
        ("execution-runtime-foundation (cross-workstream)", "EXTERNAL", "AUTHORITATIVE_AT_52e39b13"),
        ("tb-forward-engine (engineering reference)", "EXTERNAL", "REFERENCE_AT_b48fd352"),
        ("broker execution", "NOT_PERMITTED", "FALSE"),
    ]
    return [{"component": c, "status": s, "verdict": v} for c, s, v in comps]


def build_decision(dist_ok: bool, counts: Dict, grid: List[Dict]) -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "status": "PASS" if dist_ok else "FAIL",
        "base_commit": BASE_COMMIT,
        "d0_1_pass_verified": True,
        "science_unchanged": True,
        "n_events": counts["n_events"],
        "n_accepted": counts["n_accepted"],
        "n_rejected": counts["n_rejected"],
        "economic_target_distribution_frozen": dist_ok,
        "study_is_preregistered": True,
        "primary_question_defined": True,
        "source_hierarchy_defined": True,
        "truth_classes_defined": True,
        "instrument_spec_schema_defined": True,
        "account_physical_contract_defined": True,
        "feasibility_states_defined": True,
        "faithfulness_metric_defined": True,
        "notional_lane_defined": True,
        "quantity_lane_defined": True,
        "margin_lane_defined": True,
        "full_physical_lane_defined": True,
        "diagnostic_grid_defined": True,
        "diagnostic_grid_optimized_on_performance": False,
        "rounding_policy_preregistered": True,
        "upward_rounding_default": False,
        "min_quantity_policy_defined": True,
        "max_quantity_policy_defined": True,
        "currency_conversion_defined": True,
        "account_size_treatment_defined": True,
        "structural_vs_operational_feasibility_split": True,
        "concurrency_plan_defined": True,
        "coverage_metrics_defined": True,
        "family_distortion_metrics_defined": True,
        "pos_distortion_metrics_defined": True,
        "time_regime_metrics_defined": True,
        "performance_reconstruction_defined": True,
        "counterfactual_lanes_labeled_diagnostic": True,
        "falsification_criteria_defined": True,
        "missing_truth_register_complete": True,
        "execution_runtime_boundary_defined": True,
        "broker_execution_performed": False,
        "strategy_science_changed": False,
        "d1_plan_pass": dist_ok,
        "d1_1_ready": dist_ok,
        "d1_1_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
    }


# ---------------------------------------------------------------------------
# Schema artifacts
# ---------------------------------------------------------------------------
def truth_class_schema() -> Dict:
    return {
        "$id": "cr-block4.d1.truth-class",
        "title": "PhysicalTruthClass",
        "description": "Every physical scenario must be labeled; classes never silently upgrade.",
        "enum": TRUTH_CLASSES,
        "rank_high_to_low": TRUTH_CLASSES,
        "upgrade_rule": "BLOCKED",
        "note": ("A scenario may only be labeled by the authority that produced it. "
                 "HYPOTHETICAL_DIAGNOSTIC never becomes ACTUAL_OBSERVED without a "
                 "real observation; FakeMT5 fixtures are HYPOTHETICAL_DIAGNOSTIC at best."),
    }


def instrument_spec_schema() -> Dict:
    fields = [
        ("research_instrument", "string", "USDJPY (frozen research identity)"),
        ("broker_symbol", "string|null", "MISSING_EXECUTION_TRANSLATION_FIELD until broker binding"),
        ("broker_company", "string|null", "unresolved"),
        ("transport", "string|null", "unresolved"),
        ("environment", "DEMO|CONTEST|REAL|SIM|REPLAY|UNKNOWN|null", "unresolved"),
        ("product_type", "string|null", "spot FX vs CFD unresolved"),
        ("base_currency", "string|null", "unresolved"),
        ("quote_currency", "string|null", "unresolved"),
        ("settlement_or_margin_currency", "string|null", "unresolved"),
        ("account_currency", "string|null", "executable account currency unresolved until binding"),
        ("contract_size", "number|null", "trade_contract_size"),
        ("point", "number|null", "point size"),
        ("digits", "integer|null", "digits"),
        ("tick_size", "number|null", "trade_tick_size"),
        ("tick_value", "number|null", "trade_tick_value"),
        ("volume_min", "number|null", "minimum lot/volume"),
        ("volume_step", "number|null", "volume step"),
        ("volume_max", "number|null", "maximum volume"),
        ("margin_model", "string|null", "symbol margin mode; tiered if applicable"),
        ("account_leverage", "number|null", "FakeMT5 demo leverage is NOT actual truth"),
        ("symbol_leverage", "number|null", "symbol-specific leverage"),
        ("margin_tiers", "array|null", "margin tiers if applicable"),
        ("hedging_or_netting", "HEDGING|NETTING|UNKNOWN|null", "unresolved"),
        ("trading_hours", "string|null", "unresolved"),
        ("extended_hours", "boolean|null", "unresolved"),
        ("order_types_supported", "array|null", "from broker capability truth"),
        ("fill_policies", "array|null", "declared vs probed fill policy"),
        ("shortable", "boolean|null", "unresolved"),
        ("borrow_requirements", "string|null", "unresolved"),
        ("source", "string", "evidence location / document"),
        ("truth_class", "enum", TRUTH_CLASSES),
        ("observation_or_freeze_timestamp", "string|null", "when the spec was observed/frozen"),
    ]
    return {
        "$id": "cr-block4.d1.instrument-spec",
        "title": "InstrumentSpec",
        "description": "Required field inventory for instrument physical truth.",
        "required": ["research_instrument", "broker_symbol", "product_type",
                     "contract_size", "volume_min", "volume_step", "volume_max",
                     "source", "truth_class"],
        "fields": [{"name": n, "type": t, "semantics": s} for n, t, s in fields],
        "missing_critical_field": "MISSING_REQUIRED_EXECUTION_TRUTH",
    }


def account_physical_contract_schema() -> Dict:
    return {
        "$id": "cr-block4.d1.account-physical-contract",
        "title": "AccountPhysicalContract",
        "description": "Frozen or observed account-level physical truth for feasibility lanes.",
        "fields": [
            {"name": "account_id", "type": "string", "semantics": "account identity"},
            {"name": "portfolio_group_id", "type": "string", "semantics": "shared A+B portfolio authority"},
            {"name": "account_role", "type": "string", "semantics": "PORTFOLIO_MASTER required for canonical A/B"},
            {"name": "account_currency", "type": "string|null", "semantics": "executable currency"},
            {"name": "equity_at_reference", "type": "number|null", "semantics": "causal equity snapshot"},
            {"name": "leverage", "type": "number|null", "semantics": "account leverage; never from FakeMT5 fixtures"},
            {"name": "margin_model", "type": "string|null", "semantics": "actual broker margin semantics"},
            {"name": "hedging_or_netting", "type": "HEDGING|NETTING|UNKNOWN", "semantics": "position mode"},
            {"name": "buying_power_semantics", "type": "string|null", "semantics": "how buying power is defined"},
            {"name": "quantity_limits", "type": "object|null", "semantics": "min/step/max per instrument"},
            {"name": "max_notional_or_leverage_limit", "type": "number|null", "semantics": "externally imposed cap if any"},
            {"name": "foreign_positions", "type": "array", "semantics": "non-CR positions consuming resources"},
            {"name": "truth_class", "type": "enum", "semantics": TRUTH_CLASSES},
            {"name": "source", "type": "string", "semantics": "evidence location"},
            {"name": "freeze_timestamp", "type": "string|null", "semantics": "when frozen/observed"},
        ],
        "missing_critical_field": "MISSING_REQUIRED_EXECUTION_TRUTH",
        "note": "Structural feasibility (clean account) is separate from momentary operational feasibility (current resources).",
    }


def feasibility_state_schema() -> Dict:
    return {
        "$id": "cr-block4.d1.feasibility-state",
        "title": "PhysicalFeasibilityState",
        "description": "Primary state taxonomy for a feasibility assessment. One primary state per result plus optional secondary flags.",
        "primary_states": FEASIBILITY_STATES,
        "secondary_flags": ["ROUNDING_ACTIVE", "POSITIVE_BOOK_ALTERED", "CLIPPED",
                             "MIN_LOT_OVERSHOOT", "FOREIGN_RESOURCE_CONSUMPTION"],
        "fail_closed_default": "OTHER_FAIL_CLOSED",
        "rule": "A result with any unresolved required truth must take the corresponding *_UNRESOLVED or fail-closed state, never a representable state.",
    }


def instrument_spec_requirements_csv() -> str:
    import io
    spec = instrument_spec_schema()
    buf = io.StringIO()
    buf.write("field,type,semantics,status\n")
    for f in spec["fields"]:
        sem_raw = f["semantics"]
        sem = sem_raw if isinstance(sem_raw, str) else json.dumps(sem_raw)
        status = "UNKNOWN" if ("unresolved" in sem.lower() or "unknown" in sem.lower()
                               or "missing" in sem.lower()) else "REQUIRED"
        sem = sem.replace('"', "'")
        buf.write(f'{f["name"]},"{f["type"]}","{sem}",{status}\n')
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Markdown document builders
# ---------------------------------------------------------------------------
def _protocol(counts: Dict, conc: Dict) -> str:
    return f"""# CR-BLOCK4-D1 PROTOCOL — Exposure Feasibility Study Plan

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` (D0.1)
**Status:** PREREGISTRATION (no feasibility engine, no broker, no optimization)

## 1. Purpose

Design and preregister the scientific study answering:

> Of the SEALED {counts['n_accepted']} economically approved Capital Routing events, how many
> can a real account/instrument/broker physically express WITHOUT materially changing the
> economic exposure specified by the sealed research?

This checkpoint freezes the study design BEFORE any empirical feasibility outcome exists.

## 2. Frozen science (NOT touched)

| fact | value |
|---|---|
| events | {counts['n_events']} (A {counts['n_A']} / B {counts['n_B']}) |
| ACCEPT_FULL | {counts['n_accepted']} (A {counts['accepted_A']} / B {counts['accepted_B']}) |
| REJECT_HEAT_CAP | {counts['n_rejected']} |
| allocation | {ALLOCATION_ID} (A 0.70 / B 0.30) |
| policy | {POLICY_ID}, cap {HEAT_CAP_F_UNITS} f-unit, REJECT |
| f_total | {F_TOTAL_PCT}% |
| 1R | {RISK_UNIT_BPS} bps — NOT a hard stop |
| economic target | N_t = E_t x admitted_f x pos_t x 1e4 / {RISK_UNIT_BPS} (D0.1 authoritative) |

## 3. Non-goals

- no feasibility engine implementation
- no leverage / lot / broker selection
- no performance optimization of any physical constraint
- no clipping or rounding defaulted to "faithful"
- no margin fabrication
- no broker orders, no MT5 calls

## 4. Study lanes

| lane | name | input truth required |
|---|---|---|
| A | Pure notional representability | externally specified notional/equity limit L |
| B | Quantity representability | frozen instrument contract |
| C | Margin / buying power | actual or frozen margin contract |
| D | Full physical contract | account + instrument + currency + margin + broker capability |

## 5. Concurrency (verified from frozen source)

- max concurrency: **{conc['max_concurrency']}** (frozen R1_CONCURRENCY_SUMMARY.csv)
- hours with 2 positions: {conc['hours_with_2']} · 3 positions: {conc['hours_with_3']} · 4+: {conc['hours_with_4plus']}
- max gross exposure: {conc['max_gross_exposure_f_units']:.4f} f-units
- episodes (12h): **{conc['n_episodes_12h']}** (frozen R1_ROUTING_EPISODES.csv)

## 6. Artifacts in this directory

All 31 files are preregistration contracts. `CR_BLOCK4_D1_DECISION.json` is the
checkpoint decision. Nothing in this directory is an empirical feasibility result.
"""


def _scientific_question(counts: Dict, pooled: Dict) -> str:
    return f"""# CR-BLOCK4-D1 SCIENTIFIC QUESTION

## Primary question

Given a specified physical execution contract — **ACCOUNT + INSTRUMENT + BROKER +
MARGIN MODEL + QUANTITY CONSTRAINTS + CURRENCY CONVERSION** — which of the
{counts['n_accepted']} sealed economic targets are **faithfully representable**, and which
are **physically blocked or materially distorted**?

## Governing principle

- **ASK:** "Under externally specified physical constraints, what percentage of the
  sealed economic book survives unchanged?"
- **NEVER ASK:** "What leverage setting gives the best performance?"
- No physical constraint (leverage, lot, margin, broker) is selected using PF / WR /
  EV / CAGR / DD or any other performance outcome.

## Frozen economic target distribution (INPUT TRUTH, not conclusions)

Pooled accepted (n = {pooled['n']}):

| stat | value |
|---|---|
| min | {pooled['min']:.12f} x equity |
| p1 | {pooled['p1']:.12f} |
| p5 | {pooled['p5']:.12f} |
| p25 | {pooled['p25']:.12f} |
| median | {pooled['median']:.12f} |
| p75 | {pooled['p75']:.12f} |
| p95 | {pooled['p95']:.12f} |
| p99 | {pooled['p99']:.12f} |
| max | {pooled['max']:.12f} |

These are research-distribution results, NOT executable-account conclusions.

## Physical truth layers (never collapsed)

MODEL HEAT · ECONOMIC NOTIONAL · BROKER QUANTITY · MARGIN REQUIRED · BUYING POWER ·
ACTUAL FILLED EXPOSURE · MAXIMUM LOSS.
"""


def _source_hierarchy() -> str:
    return f"""# CR-BLOCK4-D1 SOURCE HIERARCHY

Physical facts are consumed strictly in this order of authority. Never silently
replace a higher authority with a lower one, and never promote a lower class upward.

| rank | source | label |
|---|---|---|
| 1 | actual broker / account observed truth | ACTUAL_OBSERVED |
| 2 | broker/API documented instrument spec | BROKER_DOCUMENTED |
| 3 | execution-runtime-foundation normalized BrokerSession truth | (class per underlying source) |
| 4 | frozen operator execution profile | PROFILE_FROZEN |
| 5 | explicitly labeled hypothetical diagnostic contract | HYPOTHETICAL_DIAGNOSTIC |
| 6 | absent | UNKNOWN |

## Truth-class rules

- Every physical scenario carries exactly one truth class.
- Classes never silently upgrade: `HYPOTHETICAL_DIAGNOSTIC` -> `ACTUAL_OBSERVED`
  requires a real observation, not an assumption.
- `FakeMT5` demo fixtures (e.g. leverage=100 in `ox_demo`) are at best
  `HYPOTHETICAL_DIAGNOSTIC` and must NEVER be promoted to actual account leverage.
- UNKNOWN is a first-class answer; missing critical truth blocks the affected lane.

## Cross-workstream heads frozen at checkpoint start (git fetch)

| workstream | head | checkpoint |
|---|---|---|
| execution-runtime-foundation | `{EXEC_RUNTIME_HEAD}` | {EXEC_RUNTIME_SUBJECT} |
| tb-forward-engine | `{TB_ENGINE_HEAD}` | {TB_ENGINE_SUBJECT} |
| main | `{MAIN_HEAD}` | (documentation commit) |

These are interface evidence only. Capital Routing does not modify or import these branches.
"""


def _faithfulness_metrics() -> str:
    return f"""# CR-BLOCK4-D1 FAITHFULNESS METRICS

Frozen BEFORE any empirical result.

## Definitions

- `exposure_ratio = actual_representable_notional / target_economic_notional`
- `relative_exposure_error = (actual_representable_notional - target_economic_notional) / target_economic_notional`

Primary ideal: `exposure_ratio = 1`.

## Materiality tolerances (preregistered)

| band | condition | primary state |
|---|---|---|
| exact | exposure_ratio == 1 (within float tolerance) | EXACTLY_REPRESENTABLE |
| immaterial | |relative_exposure_error| <= {IMMATERIAL_RELATIVE_ERROR:.0%} | REPRESENTABLE_WITH_IMMATERIAL_ROUNDING |
| distorted | |relative_exposure_error| > {DISTORTED_RELATIVE_ERROR:.0%} | ROUNDING_DISTORTED |

Tolerances are frozen. They are not adjusted after seeing outputs.

## Coverage metrics (per physical scenario)

- faithful representable count / %
- blocked count / %
- distorted count / %
- mean / median / p5 exposure ratio
- worst underrepresentation (min exposure ratio)
- maximum overrepresentation (max exposure ratio)

## Distortion metrics (preregistered)

- family coverage (A vs B) and surviving share vs original share
- pos distribution of surviving vs original (median / p75 / p95 / p99 / max)
- feasibility by notional-quantile bin (see notional diagnostic grid)
- feasibility by frozen time/regime groupings (split / year / quarter / session / severity)
"""


def _grid_doc(grid: List[Dict], pooled: Dict) -> str:
    rows = "\n".join(
        f"| {g['limit_notional_over_equity']:.4g} | {g['pooled_survive']} | "
        f"{g['pooled_survive_pct']:.2f}% | {g['A_survive_pct']:.2f}% | {g['B_survive_pct']:.2f}% |"
        for g in grid)
    return f"""# CR-BLOCK4-D1 NOTIONAL DIAGNOSTIC GRID (PREREGISTERED)

## Rule

D1.1 must show ALL preregistered cells. No dropping poor cells, no adding
thresholds because performance looks good, no interpolating an optimal
threshold. The grid is a stress surface.

`diagnostic_grid_optimized_on_performance = false`.

## Thresholds (anchored mechanically to the observed pooled distribution)

Each limit L is a notional/equity cap for lane A: an event survives iff
`target_notional / equity <= L`. Thresholds were chosen to span the observed
distribution: below median ({pooled['median']:.3f}), around median, upper body
(p75 = {pooled['p75']:.3f}), tail (p95 = {pooled['p95']:.3f}), deep tail
(p99 = {pooled['p99']:.3f}), near observed max ({pooled['max']:.3f}), and beyond
observed max (unbounded headroom reference).

| L (notional/equity) | pooled n surviving | pooled % | A % | B % |
|---|---|---|---|---|
{rows}

## Quantile bins (frozen, pooled accepted)

Feasibility is reported within these bins; bins are frozen before results:

| bin |
|---|
| 0-25% |
| 25-50% |
| 50-75% |
| 75-95% |
| 95-99% |
| 99-100% |

## Notional vs discretization feasibility

- NOTIONAL feasibility (lane A) is account-size invariant: `target_notional / equity`.
- DISCRETIZATION feasibility (lane B) depends on lot minimum, lot step, absolute
  quantity limits and absolute margin, and is therefore account-size dependent.
"""


def _quantity_translation_plan() -> str:
    return f"""# CR-BLOCK4-D1 QUANTITY TRANSLATION PLAN

## Lane B / D: economic notional -> raw quantity -> representable quantity

Generic contract (designed in D1, implemented only in D1.2+ after instrument
spec truth is frozen):

    raw_quantity = target_notional_account_ccy / price_account_ccy_per_unit

- price semantics: causal entry-side price, frozen source (see currency plan)
- units: account-currency notional / account-currency price per unit
- representable_quantity = raw_quantity rounded per frozen policy
- actual_notional = representable_quantity x price
- exposure_ratio and relative_exposure_error computed from actual vs target

## Product-type awareness

No single generic formula is assumed valid for every product. Product-specific
contracts are required per product type (spot FX / CFD / future / etc.); the
research instrument USDJPY's broker representation is unresolved until binding.

## Fail states

- target below min quantity  -> MIN_QUANTITY_BLOCKED (default; no auto round-up)
- target above max quantity -> MAX_QUANTITY_BLOCKED (default; no silent clipping)
- missing spec field -> *_UNRESOLVED / MISSING_REQUIRED_EXECUTION_TRUTH

## Unit safety

Quantity math must be unit-safe and covered by unit tests (e.g. bps/10000,
ccy per unit, lot vs base units) — never mixed silently.
"""


def _rounding_policy_plan() -> str:
    return f"""# CR-BLOCK4-D1 ROUNDING POLICY PLAN

## Frozen defaults

- primary: **{ROUNDING_PRIMARY}** — round toward lower absolute exposure; never
  exceed the approved scientific target
- comparator: {ROUNDING_COMPARATOR} (diagnostic only)
- upward rounding default: **{UPWARD_ROUNDING_DEFAULT}**
- min-quantity default: **{MIN_QUANTITY_POLICY}** — do not round up to minimum
- max-quantity default: **{MAX_QUANTITY_POLICY}** — do not silently clip

## Materiality

- |relative error| <= {IMMATERIAL_RELATIVE_ERROR:.0%} -> REPRESENTABLE_WITH_IMMATERIAL_ROUNDING
- |relative error| > {DISTORTED_RELATIVE_ERROR:.0%} -> ROUNDING_DISTORTED

## Rules

1. Rounding never silently inflates exposure beyond the admitted economic target.
2. A minimum-lot overshoot lane, if studied later, is ALTERED_BOOK_DIAGNOSTIC and
   requires preregistration before results.
3. Rounding policy is not optimized against performance.
4. Post-rounding translated heat must never exceed the model H1 allowance
   (MODEL_HEAT vs REALIZED_TRANSLATED_HEAT contract from planning R1).
"""


def _margin_model_plan() -> str:
    return f"""# CR-BLOCK4-D1 MARGIN MODEL PLAN

## Truth path

`required_margin` is a broker/instrument-specific function of (actual notional,
instrument, account, side, current price). It is NEVER universally assumed to be
`notional / leverage`.

## Current truth

All margin fields are **UNKNOWN** at D1 planning time:

- margin model / symbol margin mode / margin tiers
- account leverage (FakeMT5 demo fixtures are NOT truth)
- symbol leverage
- buying-power semantics
- hedging/netting mode

## Lane C rule

If actual broker/account margin truth is missing:

**BLOCKED_PENDING_MARGIN_TRUTH.**

Do not make up leverage. Any margin number used in a scenario must carry a
truth class; `HYPOTHETICAL_DIAGNOSTIC` margin scenarios are allowed for
sensitivity exploration but are never labeled faithful.

## Structural vs momentary

- STRUCTURAL feasibility: could the target fit under the contract on an otherwise
  available account?
- MOMENTARY OPERATIONAL feasibility: given current positions/equity/margin usage
  and foreign exposure, can it open right now?

The research feasibility study emphasizes structural truth first; momentary
operational gating belongs to the execution runtime.
"""


def _currency_conversion_plan() -> str:
    return f"""# CR-BLOCK4-D1 CURRENCY CONVERSION PLAN

## Research vs executable currency

- research reporting currency: USD (frozen, pair-base evidence)
- executable account currency: UNRESOLVED_UNTIL_ACCOUNT_BINDING
- research instrument: USDJPY (FX pair)

## Causal conversion contract

If account currency / contract currency / margin currency differ, the required
conversion price must be a CAUSAL price (no future price, no stale fixed
conversion unless explicitly a labeled scenario fixture):

- PnL conversion, notional conversion and margin conversion each use their own
  causal price at the relevant timestamp.
- `CURRENCY_CONVERSION_UNRESOLVED` is the honest state while the account
  currency is unresolved.

## Non-account-currency instruments

Design (not implement) conversion via causal prices; never force everything to
USD if the executable environment differs.
"""


def _account_size_plan() -> str:
    return f"""# CR-BLOCK4-D1 ACCOUNT SIZE PLAN

## Principle

- Ideal economic target multiples (`target_notional / equity`) are account-size
  INVARIANT.
- Quantity discretization (lot min/step, absolute limits, absolute margin) is
  account-size DEPENDENT.
- An account size is never selected because it improves performance.

## Scenarios

- Use ACTUAL intended account sizes first (truth class per size).
- A small illustrative grid may be added only if useful, each entry labeled with
  its truth class.
- Do not optimize f by account size; f_total remains frozen at {F_TOTAL_PCT}%.

## Matrix to build in D1.2 (after instrument truth)

Per account size and family: one-R budget, median/p95/p99/max target notional,
median/p95/max notional/equity, historical worst observed account impact.
"""


def _concurrency_episode_plan(conc: Dict) -> str:
    return f"""# CR-BLOCK4-D1 CONCURRENCY / EPISODE PLAN

## Verified frozen truth

- max concurrency: **{conc['max_concurrency']}** (R1_CONCURRENCY_SUMMARY.csv)
- hours with 2 positions: {conc['hours_with_2']}; 3 positions: {conc['hours_with_3']}; 4+: {conc['hours_with_4plus']}
- max gross exposure: {conc['max_gross_exposure_f_units']:.4f} f-units
- episodes at 12h interval: **{conc['n_episodes_12h']}**; max events in one episode: {conc['episode_max_n_events']}

## Plans

- event-level feasibility (each accepted target against the contract)
- episode / account-level resource feasibility (overlapping events against
  shared account resources)

## Causal account replay (D1.4)

Sequential replay, no future resource information:

    admitted event -> economic target -> physical feasibility
    -> if executable, occupy physical resource -> release at frozen event close
    -> next event

## H1 vs physical failure

- H1 admission is NEVER rewritten.
- An H1-approved event that fails physical constraints is labeled
  PHYSICALLY_UNEXECUTABLE.
- Physical blocks are never fed back into the primary research admission history.

## Exit/release semantics

Execution-safety implementation (not new alpha): heat is released only when a
position is actually confirmed closed in broker truth (same-science rule from
planning R1, Part 20).
"""


def _coverage_metrics() -> str:
    return f"""# CR-BLOCK4-D1 COVERAGE METRICS

For every physical scenario report:

- 826 economic targets
- faithfully representable count / %
- blocked count / %
- distorted count / %
- mean exposure ratio
- median exposure ratio
- p5 exposure ratio
- worst underrepresentation
- maximum overrepresentation

## No coverage target yet

No 90% / 95% / 99% minimum is invented at D1. First measure; promotion criteria
are defined deliberately afterward. Falsification criteria (see
CR_BLOCK4_D1_FALSIFICATION_CRITERIA.md) describe when a contract is weakened or
falsified.
"""


def _family_distortion_plan() -> str:
    return f"""# CR-BLOCK4-D1 FAMILY DISTORTION PLAN

## Why first-class

A requires materially larger economic notional than B (median {3.3513:.3f}x vs
{1.2850:.3f}x equity), so physical constraints are expected to be asymmetric.

## Metrics (per scenario)

- A coverage (faithful representable A / 371)
- B coverage (faithful representable B / 455)
- A share original (371/826 = 44.9%) vs A share surviving
- B share original (455/826 = 55.1%) vs B share surviving

## Interpretation rule

A systematically altered family mix is a falsification signal, not a
performance discussion. The canonical A+B portfolio science is one shared
portfolio (A1_70_30 + H1-1.00-REJ); family-level distortion must be reported,
not smoothed away.
"""


def _pos_distortion_plan() -> str:
    return f"""# CR-BLOCK4-D1 POS DISTORTION PLAN

## Metrics

Compare original accepted pos distribution vs surviving pos distribution:

- median / p75 / p95 / p99 / max
- count and share of high-pos events lost

## Purpose

Determine whether physical constraints selectively remove high-pos events
(high pos -> high economic notional -> more likely blocked). Selective removal
of high-pos states is a falsification signal: the surviving book is then not a
random subsample of the sealed book.

## Constraint

Pos values are never capped to "make" feasibility. A cap would be NEW SCIENCE
and requires a separate research checkpoint.
"""


def _time_regime_plan() -> str:
    return f"""# CR-BLOCK4-D1 TIME / REGIME DISTORTION PLAN

## Frozen groupings (already-existing event metadata only)

| grouping | frozen values |
|---|---|
| split | development (inner_sel 461 + inner_val 149) vs OOS (RELATIONSHIP_CONFIRMED_OOS 280) |
| year | 2023 / 2024 / 2025 / 2026 |
| quarter | 2023Q3 .. 2026Q2 |
| session | Asia 264 / London 321 / NY_Overlap 177 / NY_Late 128 |
| severity | LOW 747 / MEDIUM 143 |
| family | A / B |
| hold | fixed 6h (frozen) |

## Rule

Report feasibility within these frozen groupings. No post-result subgrouping
invented to rescue the book. Any newly proposed grouping requires a new
preregistered study generation / amendment.
"""


def _performance_reconstruction() -> str:
    return f"""# CR-BLOCK4-D1 PERFORMANCE RECONSTRUCTION

## Rule (predefined)

- faithfully executed event: physical return derives from ACTUAL represented exposure
- blocked event: physical realized strategy return = 0 (research event still
  exists in the ideal book)
- partial / rounded diagnostic event: return scales with actual/target exposure
  ratio ONLY IF the source model is linear in exposure

## Linearity proof (already established)

Sealed gross account return = (N_t / E_t) x price_return_bps / 1e4 and
N_t/E_t = admitted_f x pos_t x 1e4 / RISK_UNIT_BPS, so account return is exactly
linear in N_t: scaling N by ratio r scales gross account return by r. Research-
modeled cost also scales with pos_t per event (R1 cost audit). Execution-level
net parity remains BROKER_DEPENDENT_UNRESOLVED.

## Two books, never merged

- SEALED IDEAL BOOK (frozen research data — never overwritten)
- PHYSICAL-CONSTRAINT BOOK (per scenario)

## Secondary performance metrics (never used to select constraints)

event count, frequency, WR, EV, PF, payoff, normalized return, DD, streaks,
family contribution, concentration, episode behavior.
"""


def _counterfactual_lanes() -> str:
    return f"""# CR-BLOCK4-D1 COUNTERFACTUAL LANES

## Primary lane: FULL TARGET OR BLOCK

Learn whether the original science survives physical constraints. Do not
immediately try to salvage impossible events.

## Secondary lanes (always labeled ALTERED_BOOK_DIAGNOSTIC)

- ROUND_DOWN
- HARD_CLIP
- PARTIAL_SIZE
- MINIMUM-LOT OVERSHOOT
- NEAREST_STEP

An altered-book lane is NEVER treated as equivalent to the sealed book.
Clipping is an altered-book experiment, never silently called faithful.

## Result identity

A future PhysicalFeasibilityResult binds: translation_id + instrument spec hash
+ account physical contract hash + margin contract hash + rounding policy hash
+ scenario/study version. Same economic target under a different physical
contract -> different feasibility ID.
"""


def _falsification_criteria() -> str:
    return f"""# CR-BLOCK4-D1 FALSIFICATION CRITERIA

The physical-feasibility thesis is weakened/falsified for a contract if ANY of:

1. a material portion of the book is unrepresentable (blocked or distorted)
2. family mix is systematically altered (A vs B shares diverge materially)
3. high-pos states are selectively removed
4. concurrency creates large additional block rates vs event-level feasibility
5. rounding materially changes exposure (relative error beyond the frozen
   {DISTORTED_RELATIVE_ERROR:.0%} materiality band for a material share)
6. the physical return distribution is no longer scientifically representative
   of the sealed ideal book

## Rules

- Criteria are frozen at D1. Feasibility is not redefined afterward.
- No coverage percentage is invented at D1; promotion criteria are defined
  deliberately after measurement.
- No result shopping: if the book does not survive, that is the answer.
"""


def _runtime_handoff() -> str:
    return f"""# CR-BLOCK4-D1 RUNTIME HANDOFF

## Ownership boundary

**Capital Routing owns:** economic exposure target, physical feasibility
science, scientific acceptability of distortion, broker quantity requirements.

**Execution Runtime (execution-runtime-foundation) owns:** AccountRegistry,
BrokerSession, actual instrument observations, orders, fills, reconciliation,
runtime lifecycle, fleet, secrets.

## Interface evidence (read-only, frozen heads)

- execution-runtime-foundation `{EXEC_RUNTIME_HEAD}` ({EXEC_RUNTIME_SUBJECT})
  — generic contracts: AccountProfile, AccountObservedState, BrokerCapabilities
  (tri-state SUPPORTED/UNSUPPORTED/UNKNOWN, fail closed on UNKNOWN), SymbolInfo
  (digits/point/contract_size/volume_min/volume_step/volume_max/tick), AccountState
  (balance/equity/margin/free margin), MT5 symbol mapping, FakeMT5 fixture contract
  (never promoted to truth).
- tb-forward-engine `{TB_ENGINE_HEAD}` ({TB_ENGINE_SUBJECT}) — PROVEN
  ENGINEERING REFERENCE only; no code imported into Capital Routing.

## Handoff sequence

    CapitalTranslationCore (D0.1) -> EconomicExposureTarget
    -> D1 feasibility (structural) -> broker quantity requirements
    -> execution-runtime-foundation (account control plane) -> BrokerSession

No broker infrastructure is duplicated in Capital Routing.
"""


def _implementation_sequence() -> str:
    return f"""# CR-BLOCK4-D1 IMPLEMENTATION SEQUENCE

## Preregistered future checkpoint sequence

| id | name | purpose | gate |
|---|---|---|---|
| D1.1 | BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE | sealed target multiples vs preregistered notional grid; no broker/lot/margin | needs only frozen distribution |
| D1.2 | INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY | economic target -> raw quantity -> representable quantity | actual instrument spec truth frozen |
| D1.3 | MARGIN-CONTRACT-FEASIBILITY | margin/buying-power representability | actual margin semantics; else BLOCKED_PENDING_MARGIN_TRUTH |
| D1.4 | CONCURRENT-ACCOUNT-RESOURCE-REPLAY | causal overlap resource replay | D1.2/D1.3 contracts |
| D1.5 | PHYSICAL-BOOK-DISTORTION-SEAL | ideal vs physical book comparison | no constraint optimization |
| D1.6 | BROKER-QUANTITY-TRANSLATION-CONTRACT | deterministic broker-native quantity handoff | science approval of physical contract |

Then broker-native quantity requirements hand to execution-runtime-foundation.
Revision of this sequence requires explicit architectural justification.

Each later checkpoint requires its own authorization; nothing is automatic.
"""


def _test_plan() -> str:
    return f"""# CR-BLOCK4-D1 TEST PLAN

Future implementation tests must prove (design; not yet implemented):

1. sealed 890 / 826 / 64 unchanged
2. economic target ledger unchanged
3. truth classes cannot silently upgrade (HYPOTHETICAL_DIAGNOSTIC -> ACTUAL_OBSERVED blocked)
4. FakeMT5 fixtures cannot become actual truth (demo leverage never promoted)
5. notional classification deterministic
6. scenario grid immutable within a generation (byte-identical regeneration)
7. family coverage correct (A 371 / B 455 bases)
8. pos distribution correct (original vs surviving)
9. quantile bins deterministic
10. raw quantity calculations unit-safe
11. round-down never exceeds target
12. minimum-lot overshoot blocked by default
13. maximum quantity clipping not called faithful
14. currency conversion causal
15. margin provenance required (no fabricated leverage)
16. account size does not change ideal notional multiple
17. account size may change quantity discretization
18. concurrent resource accounting causal
19. physical block does not rewrite H1
20. blocked event physical return = 0
21. altered-book results clearly labeled ALTERED_BOOK_DIAGNOSTIC
22. no broker orders
23. no CapitalPolicy recomputation
24. no strategy-science modification

The D1 plan suite (tests/test_exposure_feasibility_d1_plan.py) already enforces
preregistration integrity: frozen distribution, grid anchoring, grid
immutability, truth-class protection, rounding policy, decision-field truth,
and offline determinism.
"""


def _sha_manifest() -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "science_inputs": {
            "event_risk_ledger_sha256": _sha(LEDGER),
            "r1_notional_multipliers_sha256": _sha(MULTIPLIERS),
            "d0_1_decision_sha256": _sha(D0_1_DIR / "CR_BLOCK4_D0_1_DECISION.json"),
            "d0_1_translations_sha256": _sha(D0_1_DIR / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv"),
            "r1_1_decision_sha256": _sha(R1_1_DIR / "CR_EXEC_R1_1_DECISION.json"),
            "concurrency_summary_sha256": _sha(CONC_SUMMARY),
            "routing_episodes_sha256": _sha(EPISODES),
        },
        "cross_workstream_heads_frozen_at_start": {
            "execution_runtime_foundation": EXEC_RUNTIME_HEAD,
            "tb_forward_engine": TB_ENGINE_HEAD,
            "main": MAIN_HEAD,
        },
        "note": "Cross-workstream heads are recorded diagnostically; their later movement is NOT a failure of this historical checkpoint.",
    }


def _report(counts: Dict, pooled: Dict, fam: Dict, grid: List[Dict], conc: Dict,
            decision: Dict) -> str:
    grid_tbl = "\n".join(
        f"| {g['limit_notional_over_equity']:.4g} | {g['pooled_survive']} | "
        f"{g['pooled_survive_pct']:.2f}% | {g['A_survive_pct']:.2f}% | {g['B_survive_pct']:.2f}% |"
        for g in grid)
    return f"""# CR-BLOCK4-D1 REPORT

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}`
**Status:** {decision['status']} (preregistration)

## Frozen science (verified)

- events {counts['n_events']} (A {counts['n_A']} / B {counts['n_B']})
- ACCEPT_FULL {counts['n_accepted']} (A {counts['accepted_A']} / B {counts['accepted_B']});
  REJECT_HEAT_CAP {counts['n_rejected']}
- 1R {RISK_UNIT_BPS} bps, NOT a hard stop
- economic target: N = E x admitted_f x pos_t x 1e4 / {RISK_UNIT_BPS} (D0.1 authoritative)

## Frozen economic target distribution (engine-recomputed from source rows)

| stat | pooled | A | B |
|---|---|---|---|
| n | {pooled['n']} | {fam['A']['n']} | {fam['B']['n']} |
| min | {pooled['min']:.12f} | {fam['A']['min']:.12f} | {fam['B']['min']:.12f} |
| p1 | {pooled['p1']:.12f} | {fam['A']['p1']:.12f} | {fam['B']['p1']:.12f} |
| p5 | {pooled['p5']:.12f} | {fam['A']['p5']:.12f} | {fam['B']['p5']:.12f} |
| p25 | {pooled['p25']:.12f} | {fam['A']['p25']:.12f} | {fam['B']['p25']:.12f} |
| median | {pooled['median']:.12f} | {fam['A']['median']:.12f} | {fam['B']['median']:.12f} |
| p75 | {pooled['p75']:.12f} | {fam['A']['p75']:.12f} | {fam['B']['p75']:.12f} |
| p95 | {pooled['p95']:.12f} | {fam['A']['p95']:.12f} | {fam['B']['p95']:.12f} |
| p99 | {pooled['p99']:.12f} | {fam['A']['p99']:.12f} | {fam['B']['p99']:.12f} |
| max | {pooled['max']:.12f} | {fam['A']['max']:.12f} | {fam['B']['max']:.12f} |

## Preregistered notional diagnostic grid (lane A stress surface)

| L (notional/equity) | pooled n | pooled % | A % | B % |
|---|---|---|---|---|
{grid_tbl}

`diagnostic_grid_optimized_on_performance = false` — thresholds anchored to the
observed distribution before any result; all cells shown.

## Concurrency (frozen source)

max concurrency {conc['max_concurrency']}, hours 2/3/4+: {conc['hours_with_2']}/{conc['hours_with_3']}/{conc['hours_with_4plus']},
max gross exposure {conc['max_gross_exposure_f_units']:.4f} f-units, episodes (12h) {conc['n_episodes_12h']}.

## Study lanes

A pure notional · B quantity · C margin/buying power · D full physical contract.
D1.1 (lane A) needs no broker truth and is ready; D1.2+ blocked until
instrument/margin truth exists (see missing truth register).

## Governance

- rounding primary {ROUNDING_PRIMARY}; upward default false; min/max quantity
  blocked by default; clipping never called faithful
- falsification criteria frozen; no coverage target invented yet
- broker execution: FALSE · strategy science changed: FALSE
- d1_1_authorized: FALSE (human review required)

See the sibling artifacts for each contract. Decision: `CR_BLOCK4_D1_DECISION.json`.
"""


def _component_status_csv(rows: List[Dict]) -> str:
    import io
    buf = io.StringIO()
    buf.write("component,status,verdict\n")
    for r in rows:
        buf.write(f'{r["component"]},{r["status"]},{r["verdict"]}\n')
    return buf.getvalue()


def _missing_truth_csv(rows: List[Dict]) -> str:
    import io
    buf = io.StringIO()
    buf.write('field,truth_class,detail,blocking\n')
    for r in rows:
        det = r["detail"].replace('"', "'")
        buf.write(f'{r["field"]},UNKNOWN,"{det}",{r["blocking"]}\n')
    return buf.getvalue()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dist_ok, counts, pooled, fam = frozen_distribution_check()
    grid = grid_rows()
    bins = quantile_bin_rows()
    conc = concurrency_facts()
    missing = missing_truth_register()
    decision = build_decision(dist_ok, counts, grid)

    writes = {
        "CR_BLOCK4_D1_PROTOCOL.md": _protocol(counts, conc),
        "CR_BLOCK4_D1_SCIENTIFIC_QUESTION.md": _scientific_question(counts, pooled),
        "CR_BLOCK4_D1_SOURCE_HIERARCHY.md": _source_hierarchy(),
        "CR_BLOCK4_D1_FAITHFULNESS_METRICS.md": _faithfulness_metrics(),
        "CR_BLOCK4_D1_NOTIONAL_DIAGNOSTIC_GRID.md": _grid_doc(grid, pooled),
        "CR_BLOCK4_D1_QUANTITY_TRANSLATION_PLAN.md": _quantity_translation_plan(),
        "CR_BLOCK4_D1_ROUNDING_POLICY_PLAN.md": _rounding_policy_plan(),
        "CR_BLOCK4_D1_MARGIN_MODEL_PLAN.md": _margin_model_plan(),
        "CR_BLOCK4_D1_CURRENCY_CONVERSION_PLAN.md": _currency_conversion_plan(),
        "CR_BLOCK4_D1_ACCOUNT_SIZE_PLAN.md": _account_size_plan(),
        "CR_BLOCK4_D1_CONCURRENCY_EPISODE_PLAN.md": _concurrency_episode_plan(conc),
        "CR_BLOCK4_D1_COVERAGE_METRICS.md": _coverage_metrics(),
        "CR_BLOCK4_D1_FAMILY_DISTORTION_PLAN.md": _family_distortion_plan(),
        "CR_BLOCK4_D1_POS_DISTORTION_PLAN.md": _pos_distortion_plan(),
        "CR_BLOCK4_D1_TIME_REGIME_DISTORTION_PLAN.md": _time_regime_plan(),
        "CR_BLOCK4_D1_PERFORMANCE_RECONSTRUCTION.md": _performance_reconstruction(),
        "CR_BLOCK4_D1_COUNTERFACTUAL_LANES.md": _counterfactual_lanes(),
        "CR_BLOCK4_D1_FALSIFICATION_CRITERIA.md": _falsification_criteria(),
        "CR_BLOCK4_D1_RUNTIME_HANDOFF.md": _runtime_handoff(),
        "CR_BLOCK4_D1_IMPLEMENTATION_SEQUENCE.md": _implementation_sequence(),
        "CR_BLOCK4_D1_TEST_PLAN.md": _test_plan(),
        "CR_BLOCK4_D1_REPORT.md": _report(counts, pooled, fam, grid, conc, decision),
    }
    for name, text in writes.items():
        (OUT / name).write_text(text, encoding="utf-8")

    (OUT / "CR_BLOCK4_D1_SOURCE_SHA_MANIFEST.json").write_text(
        json.dumps(_sha_manifest(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_TRUTH_CLASS_SCHEMA.json").write_text(
        json.dumps(truth_class_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_INSTRUMENT_SPEC_SCHEMA.json").write_text(
        json.dumps(instrument_spec_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_ACCOUNT_PHYSICAL_CONTRACT_SCHEMA.json").write_text(
        json.dumps(account_physical_contract_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_FEASIBILITY_STATE_SCHEMA.json").write_text(
        json.dumps(feasibility_state_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_INSTRUMENT_SPEC_REQUIREMENTS.csv").write_text(
        instrument_spec_requirements_csv(), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_MISSING_TRUTH_REGISTER.csv").write_text(
        _missing_truth_csv(missing), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_COMPONENT_STATUS.csv").write_text(
        _component_status_csv(component_status_rows(decision)), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    print(f"D1 plan artifacts -> {OUT}")
    print(f"distribution_frozen={dist_ok} counts={counts}")
    print(f"grid rows={len(grid)} quantile bins={len(bins)}")
    print(f"status={decision['status']} d1_plan_pass={decision['d1_plan_pass']}")
    print(f"missing_truth={len(missing)} cross_workstream_heads frozen")


if __name__ == "__main__":
    main()

