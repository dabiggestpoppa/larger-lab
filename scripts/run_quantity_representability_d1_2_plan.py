"""
CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN —
Lane B (quantity representability) preregistration.

PLAN ONLY.  This checkpoint designs and preregisters:

  - the scientific question: given a frozen account/product contract, can each
    sealed EconomicTarget be represented by broker-native quantity without
    materially altering exposure?
  - truth hierarchy (incl. USER_SPECIFIED_SCENARIO), physical / instrument /
    account profile schemas, the Execution-Runtime handoff contract
  - the quantity pipeline EconomicTarget -> notional -> native exposure ->
    raw quantity -> feasibility gate -> faithful rounded quantity ->
    represented notional -> exposure error
  - rounding policy (primary ROUND_DOWN_TOWARD_ZERO; min/max BLOCK; no clip;
    no upward default; nearest comparator only)
  - fidelity metrics + frozen materiality tolerance
  - account-size scenarios, currency-conversion semantics, long/short
    symmetry check, family / pos / quantile / subperiod distortion plans
  - counterfactual lanes (always ALTERED_BOOK_DIAGNOSTIC)
  - missing-truth register (empirical D1.2 BLOCKED until quantity fields are
    frozen), implementation sequence (D1.2A ingest+seal, D1.2B surface)

Do NOT: implement broker quantity execution, connect MT5, query live broker,
send orders, round production lots, clip events, change H1 / pos / f / family
weights / strategy science, select broker/account by performance, or build a
margin engine (Lane C -> D1.3).

Base: 73f760ce09e7109b23732fb7ff2ec8ad455a563e (D1.1A).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_quantity_representability_d1_2_plan"
D1_1A_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1a"
D1_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1"
D1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_plan"
TRANSLATIONS = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0_1" / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv"
MULTIPLIERS = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning_r1" / "CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv"

BASE_COMMIT = "73f760ce09e7109b23732fb7ff2ec8ad455a563e"
CHECKPOINT = "CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN"
NEXT_CHECKPOINT = "CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL"
NEXT_AFTER_INGEST = "CR-RISK-BLOCK-IV-D1.2B-QUANTITY-REPRESENTABILITY-SURFACE"

# Frozen science (Block III + R1/R1.1/D0/D0.1/D1/D1.1/D1.1A).
RISK_UNIT_BPS = 24.49489742783178
CANONICAL_BOOK_HASH = "b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a"
GRID = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
GRID_COUNTS = [39, 178, 417, 655, 786, 817, 825, 826]

# Truth classes (D1.2 adds USER_SPECIFIED_SCENARIO between PROFILE_FROZEN and
# HYPOTHETICAL_DIAGNOSTIC per the source-precedence ladder).
TRUTH_CLASSES = [
    "ACTUAL_OBSERVED",
    "BROKER_DOCUMENTED",
    "PROFILE_FROZEN",
    "USER_SPECIFIED_SCENARIO",
    "HYPOTHETICAL_DIAGNOSTIC",
    "UNKNOWN",
]
TRUTH_CLASS_RANK = {c: i for i, c in enumerate(TRUTH_CLASSES)}

# Preregistered rounding / materiality (consistent with D1 frozen bands).
ROUNDING_PRIMARY = "ROUND_DOWN_TOWARD_ZERO"
ROUNDING_COMPARATOR = "NEAREST_STEP"
UPWARD_ROUNDING_DEFAULT = False
MIN_QUANTITY_DEFAULT = "MIN_QUANTITY_BLOCKED"
MAX_QUANTITY_DEFAULT = "MAX_QUANTITY_BLOCKED"
CLIPPING_DEFAULT = False
MULTI_TICKET_SPLIT_DEFAULT = False
IMMATERIAL_RELATIVE_ERROR = 0.01      # |rel err| <= 1% -> immaterial rounding
DISTORTED_RELATIVE_ERROR = 0.05       # |rel err| >  5% -> rounding distorted

# User-specified scenario profiles (research labels; NO broker truth implied).
PROFILE_25K_L50 = "PROP_25K_L50_SCENARIO"
PROFILE_25K_L100 = "PROP_25K_L100_SCENARIO"
PROFILE_25K_L500 = "PROP_25K_L500_SCENARIO"
PROFILE_OX_L1000 = "OX_SMALL_L1000_SCENARIO"
SCENARIO_PROFILES = [
    {"profile_id": PROFILE_25K_L50, "equity": 25000.0, "leverage": "1:50",
     "account_size_note": "frozen user scenario", "truth_class": "USER_SPECIFIED_SCENARIO"},
    {"profile_id": PROFILE_25K_L100, "equity": 25000.0, "leverage": "1:100",
     "account_size_note": "frozen user scenario", "truth_class": "USER_SPECIFIED_SCENARIO"},
    {"profile_id": PROFILE_25K_L500, "equity": 25000.0, "leverage": "1:500",
     "account_size_note": "frozen user scenario", "truth_class": "USER_SPECIFIED_SCENARIO"},
    {"profile_id": PROFILE_OX_L1000, "equity": None, "leverage": "up to 1:1000",
     "account_size_note": "UNRESOLVED / user to freeze later",
     "truth_class": "USER_SPECIFIED_SCENARIO"},
]

# Diagnostic account sizes (NOT actual intended sizes unless later frozen).
DIAGNOSTIC_ACCOUNT_SIZES = [5000.0, 10000.0, 25000.0, 50000.0, 100000.0]

# Feasibility states for Lane B (margin states deferred to D1.3).
FEASIBILITY_STATES = [
    "EXACTLY_REPRESENTABLE",
    "REPRESENTABLE_WITH_IMMATERIAL_ROUNDING",
    "ROUNDING_DISTORTED",
    "MIN_QUANTITY_BLOCKED",
    "MAX_QUANTITY_BLOCKED",
    "BROKER_SYMBOL_UNRESOLVED",
    "CONTRACT_SIZE_UNRESOLVED",
    "VOLUME_RULE_UNRESOLVED",
    "ACCOUNT_CURRENCY_UNRESOLVED",
    "CURRENCY_CONVERSION_UNRESOLVED",
    "PRODUCT_TYPE_UNRESOLVED",
    "ACCOUNT_PROFILE_UNRESOLVED",
]
FAIL_CLOSED_DEFAULT = "OTHER_FAIL_CLOSED"

# Cross-workstream heads recorded at checkpoint start (git fetch, read-only).
EXEC_RUNTIME_HEAD = "62e6d0402a780d171a8b81c2070567045e341be7"
EXEC_RUNTIME_SUBJECT = "QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN"
TB_ENGINE_HEAD = "b48fd35255b41865026a3cba333ae2a2a0d6a004"
TB_ENGINE_SUBJECT = "TB-R6.1D-BOOT-FLOW-STACK: supervisor owns watcher + dashboard, full stack auto-starts at logon"
MAIN_HEAD = "9f61288679eea56a298e08f718c314f2ca509bc5"
MAIN_SUBJECT = "OCE Block 0: ratify constitutional control checkpoint"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_frozen_facts() -> Dict:
    """Verify D1.1A PASS, canonical book hash, D1.1 grid — from sealed files."""
    d11a = json.loads((D1_1A_DIR / "CR_BLOCK4_D1_1A_DECISION.json").read_text(encoding="utf-8"))
    qr = json.loads((D1_1A_DIR / "CR_BLOCK4_D1_1A_QUANTILE_RECONCILIATION.json").read_text(encoding="utf-8"))
    grid = json.loads((D1_1_DIR / "CR_BLOCK4_D1_1_GRID_REPLICATION.json").read_text(encoding="utf-8"))
    tr = pd.read_csv(TRANSLATIONS)
    counts = {"n_events": int(len(tr)),
              "n_accepted": int((tr["decision"] == "ACCEPT_FULL").sum()),
              "n_rejected": int((tr["decision"] == "REJECT_HEAT_CAP").sum()),
              "accepted_A": int(((tr["decision"] == "ACCEPT_FULL") & (tr["family"] == "A")).sum()),
              "accepted_B": int(((tr["decision"] == "ACCEPT_FULL") & (tr["family"] == "B")).sum())}
    ok = (d11a["status"] == "PASS" and d11a["d1_1a_pass"] is True
          and qr["d1_distribution_source_hash"] == CANONICAL_BOOK_HASH
          and qr["same_source_book"] is True
          and grid["replication_pass"] is True
          and [r["n_surviving"] for r in grid["rows"]] == GRID_COUNTS
          and counts == {"n_events": 890, "n_accepted": 826, "n_rejected": 64,
                         "accepted_A": 371, "accepted_B": 455})
    return {"verified": ok, "d1_1a_status": d11a["status"],
            "canonical_book_hash": qr["d1_distribution_source_hash"],
            "grid_replication_pass": grid["replication_pass"],
            "counts": counts}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
def physical_profile_schema() -> Dict:
    return {
        "$id": "cr-block4.d1.2.physical-profile",
        "title": "PhysicalProfile",
        "description": ("A frozen or scenario account/product pairing for Lane B. "
                        "Research scenario labels (PROP_*/OX_*) imply NO broker "
                        "truth; every profile carries exactly one truth class."),
        "fields": [
            {"name": "profile_id", "type": "string", "semantics": "immutable profile identity"},
            {"name": "equity", "type": "number|null", "semantics": "account equity; None = UNRESOLVED"},
            {"name": "account_currency", "type": "string|null", "semantics": "executable currency"},
            {"name": "leverage", "type": "string|null", "semantics": "recorded metadata; belongs to D1.3 margin, not Lane B"},
            {"name": "account_size", "type": "number|null", "semantics": "distinct from leverage"},
            {"name": "instrument_spec_hash", "type": "string|null", "semantics": "immutable spec hash; None until sealed"},
            {"name": "account_profile_hash", "type": "string|null", "semantics": "immutable account profile hash"},
            {"name": "truth_class", "type": "enum", "semantics": TRUTH_CLASSES},
            {"name": "source", "type": "string", "semantics": "evidence location / scenario provenance"},
            {"name": "freeze_timestamp", "type": "string|null", "semantics": "when frozen/observed"},
        ],
        "rule": ("Changing contract size / volume step / volume max / account "
                 "currency / broker symbol requires a NEW profile generation. "
                 "No silent mutable profile."),
        "missing_critical_field": "MISSING_REQUIRED_EXECUTION_TRUTH",
    }


def instrument_spec_schema() -> Dict:
    fields = [
        ("source_id", "string|null", "observation/spec source id"),
        ("observed_at", "string|null", "causal observation timestamp"),
        ("broker_company", "string|null", "unresolved"),
        ("environment", "DEMO|CONTEST|REAL|SIM|REPLAY|UNKNOWN|null", "unresolved"),
        ("transport", "string|null", "MT5 / other transport unresolved"),
        ("research_symbol", "string", "USDJPY (frozen research identity)"),
        ("broker_symbol", "string|null", "MISSING_EXECUTION_TRANSLATION_FIELD until binding"),
        ("product_type", "string|null", "spot FX vs CFD representation unresolved"),
        ("contract_size", "number|null", "trade_contract_size"),
        ("point", "number|null", "point size"),
        ("digits", "integer|null", "digits"),
        ("tick_size", "number|null", "trade_tick_size"),
        ("tick_value", "number|null", "trade_tick_value"),
        ("volume_min", "number|null", "minimum volume"),
        ("volume_step", "number|null", "volume step"),
        ("volume_max", "number|null", "maximum volume"),
        ("volume_limit", "number|null", "separate volume limit if any"),
        ("volume_semantics", "string|null", "lot / units / base-currency semantics"),
        ("base_currency", "string|null", "unresolved"),
        ("quote_currency", "string|null", "unresolved"),
        ("margin_currency", "string|null", "unresolved"),
        ("hedging_or_netting", "HEDGING|NETTING|UNKNOWN|null", "position mode"),
        ("truth_class", "enum", TRUTH_CLASSES),
        ("source", "string", "evidence location"),
    ]
    return {
        "$id": "cr-block4.d1.2.instrument-spec",
        "title": "InstrumentPhysicalSpec",
        "description": ("Field inventory for USDJPY physical instrument truth. "
                        "NO generic FX defaults (100000 / 0.01 / 0.01 / 100) are "
                        "assumed unless inside a labeled "
                        "HYPOTHETICAL_DIAGNOSTIC_PROFILE."),
        "required": ["research_symbol", "broker_symbol", "product_type",
                     "contract_size", "volume_min", "volume_step", "volume_max",
                     "base_currency", "quote_currency", "truth_class", "source"],
        "fields": [{"name": n, "type": t, "semantics": s} for n, t, s in fields],
        "missing_critical_field": "MISSING_REQUIRED_EXECUTION_TRUTH",
    }


def account_profile_schema() -> Dict:
    return {
        "$id": "cr-block4.d1.2.account-profile",
        "title": "AccountPhysicalProfile",
        "description": "Frozen or observed account-level physical truth (Lane B fields).",
        "fields": [
            {"name": "account_id", "type": "string", "semantics": "account identity"},
            {"name": "observed_at", "type": "string|null", "semantics": "causal observation timestamp"},
            {"name": "balance", "type": "number|null", "semantics": "account balance"},
            {"name": "equity", "type": "number|null", "semantics": "causal equity snapshot"},
            {"name": "account_currency", "type": "string|null", "semantics": "executable currency"},
            {"name": "leverage", "type": "string|null", "semantics": "recorded; margin semantics deferred to D1.3"},
            {"name": "margin_mode", "type": "string|null", "semantics": "recorded; deferred to D1.3"},
            {"name": "hedging_netting", "type": "HEDGING|NETTING|UNKNOWN|null", "semantics": "position mode"},
            {"name": "broker_company", "type": "string|null", "semantics": "unresolved"},
            {"name": "environment", "type": "string|null", "semantics": "unresolved"},
            {"name": "truth_class", "type": "enum", "semantics": TRUTH_CLASSES},
            {"name": "source", "type": "string", "semantics": "evidence location"},
        ],
        "missing_critical_field": "MISSING_REQUIRED_EXECUTION_TRUTH",
    }


def feasibility_state_schema() -> Dict:
    return {
        "$id": "cr-block4.d1.2.feasibility-state",
        "title": "QuantityFeasibilityState",
        "description": ("Lane B primary-state taxonomy. One primary state per "
                        "result plus optional secondary flags. Margin / buying "
                        "power / leverage states belong to Lane C (D1.3), NOT "
                        "Lane B."),
        "primary_states": FEASIBILITY_STATES,
        "secondary_flags": ["ROUNDING_ACTIVE", "MIN_QUANTITY_OVERSHOOT_PROHIBITED",
                            "MAX_QUANTITY_OVERSHOOT_PROHIBITED",
                            "MULTI_TICKET_SPLIT_PROHIBITED"],
        "fail_closed_default": FAIL_CLOSED_DEFAULT,
        "rule": ("A result with any unresolved required truth takes the "
                 "corresponding *_UNRESOLVED or fail-closed state, never a "
                 "representable state. An event can be QUANTITY_REPRESENTABLE "
                 "and later MARGIN_BLOCKED (D1.3) — lanes are never combined."),
    }


def profile_registry() -> List[Dict]:
    rows = []
    for p in SCENARIO_PROFILES:
        rows.append({
            "profile_id": p["profile_id"],
            "equity": p["equity"] if p["equity"] is not None else "UNRESOLVED",
            "leverage": p["leverage"],
            "account_size_note": p["account_size_note"],
            "truth_class": p["truth_class"],
            "instrument_spec": "UNKNOWN_UNTIL_FROZEN",
            "account_currency": "UNKNOWN_UNTIL_FROZEN",
            "quantity_feasibility_runnable": "no",
        })
    return rows


def missing_truth_register() -> List[Dict]:
    rows = [
        ("actual_intended_broker", "actual broker identity unresolved"),
        ("actual_account", "actual account / account id unresolved"),
        ("actual_broker_symbol", "USDJPY broker representation (USDJPY / USDJPY.PRO / CFD / spot) unresolved"),
        ("product_type", "spot FX vs CFD representation unresolved"),
        ("contract_size", "trade_contract_size unknown"),
        ("volume_min", "minimum volume unknown"),
        ("volume_step", "volume step unknown"),
        ("volume_max", "maximum volume unknown"),
        ("volume_limit", "separate volume limit unknown"),
        ("account_currency", "executable account currency unresolved until account binding"),
        ("margin_currency", "margin currency unresolved"),
        ("tick_size", "trade_tick_size unknown"),
        ("tick_value", "trade_tick_value unknown"),
        ("point", "point size unknown"),
        ("digits", "digits unknown"),
        ("hedging_netting", "HEDGING vs NETTING mode unknown"),
        ("causal_conversion_source", "causal FX conversion price source unresolved"),
        ("actual_account_size", "intended account size unresolved"),
    ]
    return [{"field": f, "truth_class": "UNKNOWN", "detail": d,
             "blocking_for_d1_2_empirical": "yes"} for f, d in rows]


def component_status_rows(status: str) -> List[Dict]:
    comps = [
        ("D1.1 notional feasibility surface (Lane A)", "SEALED", "PASS"),
        ("D1.1A artifact truth / quantile reconciliation", "SEALED", "PASS"),
        ("D1.2 quantity representability plan (Lane B)", "PREREGISTERED", status),
        ("D1.2A physical-profile truth ingest + seal", "PLANNED", "NOT_STARTED"),
        ("D1.2B quantity-representability surface", "PLANNED", "NOT_STARTED"),
        ("D1.3 margin-contract feasibility (Lane C)", "PLANNED", "NOT_STARTED"),
        ("D1.4 concurrent account-resource replay", "PLANNED", "NOT_STARTED"),
        ("D1.5 physical-book distortion seal", "PLANNED", "NOT_STARTED"),
        ("D1.6 broker quantity translation contract", "PLANNED", "NOT_STARTED"),
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
            "r1_notional_multipliers_sha256": _sha(MULTIPLIERS),
            "d1_1a_decision_sha256": _sha(D1_1A_DIR / "CR_BLOCK4_D1_1A_DECISION.json"),
            "d1_1a_quantile_reconciliation_sha256": _sha(D1_1A_DIR / "CR_BLOCK4_D1_1A_QUANTILE_RECONCILIATION.json"),
            "d1_1_grid_replication_sha256": _sha(D1_1_DIR / "CR_BLOCK4_D1_1_GRID_REPLICATION.json"),
            "d1_plan_decision_sha256": _sha(D1_DIR / "CR_BLOCK4_D1_DECISION.json"),
        },
        "canonical_book_hash": CANONICAL_BOOK_HASH,
        "cross_workstream_heads_frozen_at_start": {
            "execution_runtime_foundation": EXEC_RUNTIME_HEAD,
            "tb_forward_engine": TB_ENGINE_HEAD,
            "main": MAIN_HEAD,
        },
        "note": ("Cross-workstream heads recorded diagnostically; their later "
                 "movement is NOT a failure of this historical checkpoint."),
    }


# ---------------------------------------------------------------------------
# Markdown document builders
# ---------------------------------------------------------------------------
def _protocol(facts: Dict) -> str:
    return f"""# CR-BLOCK4-D1.2 PROTOCOL — Instrument Spec + Quantity Representability Plan

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` (D1.1A)
**Status:** PLAN + PREREGISTRATION (no empirical quantity study, no broker, no orders)

## 1. Question (Lane B)

> Given a frozen account/product contract, can each sealed EconomicTarget be
> represented by broker-native quantity WITHOUT materially altering exposure?

The question is NOT "can we make some order fit" — it is "can the INTENDED
EXPOSURE be represented faithfully?".  EconomicTarget != broker quantity.

## 2. Frozen science (verified)

| fact | value |
|---|---|
| events | {facts['counts']['n_events']} |
| ACCEPT_FULL | {facts['counts']['n_accepted']} (A {facts['counts']['accepted_A']} / B {facts['counts']['accepted_B']}) |
| REJECT_HEAT_CAP | {facts['counts']['n_rejected']} |
| canonical book hash | `{CANONICAL_BOOK_HASH}` |
| D1.1 grid | {GRID_COUNTS} (PASS) |
| 1R | {RISK_UNIT_BPS} bps — NOT a hard stop |

## 3. Non-goals

- no broker quantity execution, no MT5 connection, no live broker queries, no orders
- no production-lot rounding, no clipping, no multi-ticket evasion
- no H1 / pos / f_total / family-weight / strategy-science change
- no margin / buying-power / leverage feasibility (Lane C -> D1.3)
- no performance-based broker/profile selection

## 4. Truth hierarchy

1. ACTUAL_OBSERVED 2. BROKER_DOCUMENTED 3. PROFILE_FROZEN
4. USER_SPECIFIED_SCENARIO 5. HYPOTHETICAL_DIAGNOSTIC 6. UNKNOWN

Lower truth classes never silently upgrade.

## 5. Empirical execution gate

D1.2 empirical quantity study is **BLOCKED** until minimum required quantity
fields are frozen (contract size, volume min/step/max, broker symbol, product
type, account currency, causal conversion source).

## 6. Artifacts

26 preregistration files in this directory; `CR_BLOCK4_D1_2_DECISION.json` is
the checkpoint decision. Nothing here is an empirical feasibility result.
"""


def _scientific_question(facts: Dict) -> str:
    return f"""# CR-BLOCK4-D1.2 SCIENTIFIC QUESTION

## Primary question

Given a frozen account/product contract — account, broker symbol, product
type, contract size, volume min/step/max, account currency, conversion
semantics — can each of the {facts['counts']['n_accepted']} sealed
EconomicTargets be represented by broker-native quantity without materially
altering exposure?

## Core principle

- EconomicTarget is a scientific exposure.
- Broker quantity is a physical representation.
- Lane B measures **target exposure vs actually representable quantity** and
  reports fidelity (exposure ratio / relative error), never silently treating
  an altered quantity as equivalent.

## Distinction from Lane C

Lane B (quantity representability) is DISTINCT from Lane C (margin / buying
power / leverage, D1.3).  An event can be QUANTITY_REPRESENTABLE and later
MARGIN_BLOCKED.  Lanes are never combined in one state machine.

## Primary faithful policy

FULL TARGET OR BLOCK:

- raw quantity below volume_min -> MIN_QUANTITY_BLOCKED (no auto round-up)
- raw quantity above volume_max -> MAX_QUANTITY_BLOCKED (no clip, no split)
- within range -> floor toward zero to volume_step, then measure exposure error

Counterfactual lanes (round-up / nearest / clipped) are
ALTERED_BOOK_DIAGNOSTIC only.
"""


def _truth_hierarchy() -> str:
    rank = "\n".join(f"| {i+1} | {c} |" for i, c in enumerate(TRUTH_CLASSES))
    return f"""# CR-BLOCK4-D1.2 TRUTH HIERARCHY

## Source precedence

{rank}

## Rules

- Every physical field carries exactly one truth class.
- Classes never silently upgrade: USER_SPECIFIED_SCENARIO never becomes
  ACTUAL_OBSERVED without a real observation; FakeMT5 / TB demo specs never
  become actual broker truth.
- The user-supplied operating assumptions (prop ~25k USD, leverage floors
  1:50 / 1:100 / 1:500, OX up to 1:1000, smaller live balance with high
  leverage) are **USER_SPECIFIED_SCENARIO**, NOT ACTUAL_OBSERVED and NOT
  BROKER_DOCUMENTED.
- UNKNOWN is a first-class answer; missing critical quantity truth blocks the
  empirical lane.

## Cross-workstream heads (recorded read-only at checkpoint start)

| workstream | head | checkpoint |
|---|---|---|
| execution-runtime-foundation | `{EXEC_RUNTIME_HEAD}` | {EXEC_RUNTIME_SUBJECT} |
| tb-forward-engine | `{TB_ENGINE_HEAD}` | {TB_ENGINE_SUBJECT} |
| main | `{MAIN_HEAD}` | {MAIN_SUBJECT} |
"""


def _runtime_handoff() -> str:
    return f"""# CR-BLOCK4-D1.2 RUNTIME HANDOFF CONTRACT

Capital Routing must NOT build a broker client.  Execution Runtime owns
BrokerSession, account/symbol observations, transport, credentials.  Capital
Routing consumes normalized physical-truth artifacts.

## InstrumentPhysicalSpec (required from Execution Runtime)

| field | semantics |
|---|---|
| source_id | observation/spec source id |
| observed_at | causal observation timestamp |
| broker_company | broker identity |
| environment | DEMO / CONTEST / REAL / SIM / REPLAY |
| transport | MT5 / other |
| research_symbol | USDJPY (frozen research identity) |
| broker_symbol | actual broker symbol |
| product_type | spot FX / CFD / ... |
| contract_size | trade_contract_size |
| point | point size |
| digits | digits |
| tick_size | trade_tick_size |
| tick_value | trade_tick_value |
| volume_min / volume_step / volume_max | volume rules |
| base_currency / quote_currency / margin_currency | currency legs |
| truth_class | ACTUAL_OBSERVED / BROKER_DOCUMENTED / ... |

## AccountPhysicalProfile (required from Execution Runtime)

| field | semantics |
|---|---|
| account_id | account identity |
| observed_at | causal observation timestamp |
| balance / equity | account state |
| account_currency | executable currency |
| leverage | recorded metadata (margin semantics -> D1.3) |
| margin_mode | recorded (-> D1.3) |
| hedging_netting | position mode |
| broker_company / environment | venue identity |
| truth_class | source authority |

## Boundary

- Execution Runtime `{EXEC_RUNTIME_HEAD}` ({EXEC_RUNTIME_SUBJECT}) is the
  authoritative future source of these normalized artifacts.
- tb-forward-engine `{TB_ENGINE_HEAD}` is PROVEN_ENGINEERING_REFERENCE; its
  demo specs are never borrowed automatically.
- No code from either branch is imported into Capital Routing.
"""


def _quantity_pipeline() -> str:
    return f"""# CR-BLOCK4-D1.2 QUANTITY PIPELINE (PLAN)

    EconomicTarget
      -> account-currency notional (D0.1 target, equity-normalized x equity)
      -> instrument/native exposure (contract semantics)
      -> raw broker quantity
      -> quantity feasibility gate (min / max / step)
      -> faithful rounded quantity (ROUND_DOWN_TOWARD_ZERO)
      -> represented notional
      -> exposure error (exposure ratio, relative / signed error)

## Rules

1. The pipeline is implemented ONLY in D1.2B after physical truth is sealed.
2. No generic FX contract is assumed: contract_size = 100000, volume_min =
   0.01, volume_step = 0.01, volume_max = 100 may appear only inside a labeled
   HYPOTHETICAL_DIAGNOSTIC_PROFILE.
3. Long/short symmetry is CHECKED against the instrument contract, never
   assumed; if asymmetric, side-specific conversion is preserved.
4. Causality: instrument spec known at/before event simulation, account equity
   snapshot known at decision time, causal FX conversion at translation time.
   No end-of-period price conversion.

## Currency conversion (USDJPY / USD account)

Research EconomicTarget notional (account currency) must map to native
instrument quantity using broker contract semantics.  The plan specifies the
required causal conversion price(s): entry-side price for notional->units, and
contract-side semantics for USDJPY (base USD / quote JPY) with a USD account —
conversion is NOT assumed trivial.  CURRENCY_CONVERSION_UNRESOLVED while the
causal conversion source is unknown.
"""


def _rounding_policy() -> str:
    return f"""# CR-BLOCK4-D1.2 ROUNDING POLICY

## Frozen defaults

| item | value |
|---|---|
| primary | **{ROUNDING_PRIMARY}** — never exceeds the approved target |
| comparator | {ROUNDING_COMPARATOR} (diagnostic only) |
| upward rounding default | **{UPWARD_ROUNDING_DEFAULT}** |
| below volume_min | **{MIN_QUANTITY_DEFAULT}** (no auto round-up) |
| above volume_max | **{MAX_QUANTITY_DEFAULT}** (no clip) |
| multi-ticket split | **{MULTI_TICKET_SPLIT_DEFAULT}** unless broker truth says the max is per ticket AND a later execution contract explicitly authorizes it |
| clipping | **{CLIPPING_DEFAULT}** |

## Volume-step rule (within min/max)

    faithful_quantity = floor_toward_zero(raw_quantity / volume_step) * volume_step

Then recompute represented_notional, exposure_ratio, relative_exposure_error.

## Rationale

- Rounding DOWN can only under-represent, never over-represent, the approved
  scientific target.
- Rounding UP creates MORE exposure than science requested — prohibited as a
  default; studied only in ALTERED_BOOK_ROUND_UP diagnostics.
"""


def _fidelity_metrics() -> str:
    return f"""# CR-BLOCK4-D1.2 FIDELITY METRICS

Frozen BEFORE any empirical outcome.

## Definitions

- `raw_quantity` — unrounded broker quantity from the pipeline
- `rounded_quantity` — faithful (floor-to-step) quantity
- `quantity_delta = rounded_quantity - raw_quantity`
- `target_notional` — sealed EconomicTarget notional (account currency)
- `represented_notional = rounded_quantity x price_semantics`
- `exposure_ratio = represented_notional / target_notional`
- `relative_exposure_error = |represented_notional - target_notional| / target_notional`
- `signed_exposure_error = (represented_notional - target_notional) / target_notional`

## Materiality tolerance (preregistered)

| band | condition | primary state |
|---|---|---|
| exact | exposure_ratio == 1 (float tolerance) | EXACTLY_REPRESENTABLE |
| immaterial | relative_exposure_error <= {IMMATERIAL_RELATIVE_ERROR:.0%} | REPRESENTABLE_WITH_IMMATERIAL_ROUNDING |
| distorted | relative_exposure_error > {DISTORTED_RELATIVE_ERROR:.0%} | ROUNDING_DISTORTED |

Rationale for the {IMMATERIAL_RELATIVE_ERROR:.0%} candidate: it matches the D1
frozen immaterial band (IMMATERIAL_RELATIVE_ERROR = {IMMATERIAL_RELATIVE_ERROR:.0%}
preregistered in D1), keeping one consistent materiality language across
lanes.  Expressed in risk-unit terms, 1% of target notional corresponds to 1%
of that event's one-R exposure — economically interpretable and independent
of PF/EV.  The tolerance is re-confirmed at D1.2A when the physical profile is
sealed; it is never chosen from performance.

## Result surfaces (future D1.2B)

Per profile / account size: n accepted targets, exactly representable,
immaterial rounding, rounding distorted, min blocked, max blocked, unresolved,
coverage %, mean / median / p95 / max relative error.
"""


def _account_size_plan() -> str:
    return f"""# CR-BLOCK4-D1.2 ACCOUNT SIZE PLAN

## Lane-B dependence

Unlike Lane A, Lane B is ACCOUNT-SIZE DEPENDENT: absolute quantity and
volume min/step/max matter.  `target_notional / equity` stays invariant, but
raw quantity and step rounding depend on equity.

## Diagnostic sizes (frozen)

{', '.join(f'{int(s):,} USD' for s in DIAGNOSTIC_ACCOUNT_SIZES)}

These are DIAGNOSTIC sizes only unless tied to real profiles.

## Actual intended size

Included when frozen (D1.2A).  Scenario profiles: {PROFILE_25K_L50} /
{PROFILE_25K_L100} / {PROFILE_25K_L500} at 25,000 USD equity;
{PROFILE_OX_L1000} account size UNRESOLVED (user to freeze later).

## Leverage note

Leverage does NOT affect pure quantity rounding unless broker volume rules
depend on account tier.  Leverage is recorded in profile metadata but belongs
primarily to D1.3 margin feasibility.
"""


def _currency_conversion_plan() -> str:
    return f"""# CR-BLOCK4-D1.2 CURRENCY CONVERSION PLAN

## Research vs executable

- research reporting currency: USD
- executable account currency: UNRESOLVED_UNTIL_ACCOUNT_BINDING
- research instrument: USDJPY (FX pair, base USD / quote JPY)

## Quantity semantics (USDJPY, USD account)

- The EconomicTarget account-currency notional must be mapped to native
  instrument quantity using broker contract semantics — conversion is NOT
  assumed trivial even for USD accounts.
- Required causal conversion price(s): entry-side price at translation time
  for notional -> units; margin-currency conversion deferred to D1.3.
- No future price, no stale fixed conversion unless explicitly a labeled
  scenario fixture.

## Long / short

Symmetry is CHECKED against the instrument contract, not assumed.  If
asymmetric, side-specific conversion is preserved.

## States

CURRENCY_CONVERSION_UNRESOLVED while the causal conversion source is unknown;
ACCOUNT_CURRENCY_UNRESOLVED until account binding.
"""


def _family_pos_quantile_plans() -> List[str]:
    fam = f"""# CR-BLOCK4-D1.2 FAMILY DISTORTION PLAN

Because D1.1 proved physical filters can materially change family mix (A share
shift -0.398 at L=0.5), every physical profile must report feasibility by A / B:

- A coverage (representable A / 371)
- B coverage (representable B / 455)
- A / B share of the surviving (representable) book
- share shift vs original (371/826, 455/826)

No optimization.  A systematically altered family mix is a falsification
signal, not a discussion.
"""
    pos = f"""# CR-BLOCK4-D1.2 POS DISTORTION PLAN

Report representability by frozen pos_t bins / distribution (median, p75, p95,
p99, max of original vs representable vs blocked).  High pos -> higher notional
-> mechanically more exposed to quantity filters.  Never cap pos to make
feasibility; pos_t is sealed.
"""
    quant = f"""# CR-BLOCK4-D1.2 QUANTILE DISTORTION PLAN

Reuse the D1.1 frozen RANK_BIN_EDGE boundaries (0-25 / 25-50 / 50-75 / 75-95 /
95-99 / 99-100) from CR_BLOCK4_D1_1_GRID_REPLICATION.json.  Boundaries are
NOT recomputed.  Report original / representable / blocked n and coverage %
per bin for every profile.  Do NOT conflate RANK_BIN_EDGE with the D1
DESCRIPTIVE_DISTRIBUTION_QUANTILE values.
"""
    sub = f"""# CR-BLOCK4-D1.2 SUBPERIOD / REGIME DISTORTION PLAN

Use only sealed fields: split (development = inner_sel + inner_val vs OOS),
year, quarter, session, severity.  No post-hoc category invention.  Regime
fields without sealed labels (volatility bucket, signal subtype) remain
NOT_AVAILABLE_IN_SEALED_LEDGER.
"""
    return [fam, pos, quant, sub]


def _counterfactual_plan() -> str:
    return f"""# CR-BLOCK4-D1.2 COUNTERFACTUAL PLAN

## Primary book (faithful)

FULL TARGET OR BLOCK — the only lane that may be called faithful.

## Altered-book diagnostics (NEVER faithful)

| lane | label |
|---|---|
| round up to step | ALTERED_BOOK_ROUND_UP |
| nearest step | ALTERED_BOOK_NEAREST |
| clipped at volume_max | ALTERED_BOOK_CLIPPED |
| multi-ticket split | ALTERED_BOOK_SPLIT (only if broker truth authorizes later) |

Every altered-book result is labeled ALTERED_BOOK_DIAGNOSTIC and is never
treated as equivalent to the sealed book.  These lanes are studied only if
scientifically useful later, and only after preregistration.
"""


def _implementation_sequence() -> str:
    return f"""# CR-BLOCK4-D1.2 IMPLEMENTATION SEQUENCE

| id | name | gate |
|---|---|---|
| D1.2A | PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL | ingest actual observed / documented USDJPY account + instrument specs from the intended venue(s); freeze profiles |
| D1.2B | QUANTITY-REPRESENTABILITY-SURFACE | execute the sealed Lane-B study on frozen profiles |
| D1.3 | MARGIN-CONTRACT-FEASIBILITY | Lane C; actual margin semantics else BLOCKED_PENDING_MARGIN_TRUTH |
| D1.4 | CONCURRENT-ACCOUNT-RESOURCE-REPLAY | causal overlap replay |
| D1.5 | PHYSICAL-BOOK-DISTORTION-SEAL | ideal vs physical book |
| D1.6 | BROKER-QUANTITY-TRANSLATION-CONTRACT | broker-native quantity handoff |

D1.2A must precede D1.2B so physical assumptions cannot silently enter the
empirical engine.  Each later checkpoint requires its own authorization.
"""


def _test_plan() -> str:
    return f"""# CR-BLOCK4-D1.2 TEST PLAN

Plan-artifact / schema tests (see tests/test_quantity_representability_d1_2_plan.py):

1. D1.1A PASS verified 2. 890/826/371/455/64 frozen 3. D1.1 grid unchanged
4. same canonical book hash 5. physical profiles carry truth_class
6. no profile silently marked ACTUAL_OBSERVED 7. user-supplied leverage
labeled USER_SPECIFIED_SCENARIO 8. account size distinct from leverage
9. Lane B distinct from margin Lane C 10. EconomicTarget distinct from broker
quantity 11. min quantity default BLOCK 12. max quantity default BLOCK
13. clipping default false 14. upward rounding default false
15. primary rounding candidate toward zero 16. nearest comparator only
17. relative exposure error defined 18. tolerance preregistration required
19. account size scenarios frozen 20. instrument spec immutable/hashable
21. account profile immutable/hashable 22. runtime handoff schema defined
23. no broker client in CR 24. no execution API 25. no MT5 import
26. no order logic 27. no performance-based profile selection
28. D1.3 margin deferred 29. missing truth blocks empirical D1.2
30. production authorization false.

All tests offline and deterministic; no network, no git, no broker.
"""


def build_decision(facts: Dict) -> Dict:
    ok = (facts["verified"]
          and facts["d1_1a_status"] == "PASS"
          and facts["canonical_book_hash"] == CANONICAL_BOOK_HASH)
    return {
        "checkpoint": CHECKPOINT,
        "status": "PASS" if ok else "FAIL",
        "base_commit": BASE_COMMIT,
        "d1_1a_pass_verified": facts["d1_1a_status"] == "PASS",
        "science_unchanged": facts["verified"],
        "n_events": facts["counts"]["n_events"],
        "n_accepted": facts["counts"]["n_accepted"],
        "accepted_A": facts["counts"]["accepted_A"],
        "accepted_B": facts["counts"]["accepted_B"],
        "canonical_book_hash": CANONICAL_BOOK_HASH,
        "lane_b_defined": True,
        "lane_c_excluded": True,
        "truth_hierarchy_defined": True,
        "user_scenario_truth_class_defined": True,
        "instrument_spec_schema_defined": True,
        "account_profile_schema_defined": True,
        "runtime_handoff_defined": True,
        "quantity_pipeline_defined": True,
        "rounding_policy_defined": True,
        "min_quantity_default_block": True,
        "max_quantity_default_block": True,
        "clipping_default": False,
        "upward_rounding_default": False,
        "fidelity_metric_defined": True,
        "rounding_tolerance_preregistered": True,
        "account_size_plan_defined": True,
        "currency_conversion_plan_defined": True,
        "family_distortion_plan_defined": True,
        "pos_distortion_plan_defined": True,
        "quantile_distortion_plan_defined": True,
        "physical_profiles_defined": True,
        "actual_profile_complete": False,
        "missing_truth_register_complete": True,
        "broker_client_added": False,
        "mt5_import_added": False,
        "execution_logic_added": False,
        "margin_engine_added": False,
        "strategy_science_changed": False,
        "d1_2_plan_pass": ok,
        "d1_2_empirical_ready": False,
        "d1_2_empirical_authorized": False,
        "d1_3_ready": False,
        "d1_3_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "next_checkpoint_recommended": NEXT_CHECKPOINT,
    }


def _report(facts: Dict, decision: Dict) -> str:
    reg = "\n".join(
        f"| {r['profile_id']} | {r['equity']} | {r['leverage']} | "
        f"{r['truth_class']} | {r['instrument_spec']} |" for r in profile_registry())
    return f"""# CR-BLOCK4-D1.2 REPORT

**Checkpoint:** {CHECKPOINT}
**Base:** `{BASE_COMMIT}` · **Status:** {decision['status']} (preregistration)

## Frozen science (verified)

- events {facts['counts']['n_events']} · ACCEPT_FULL {facts['counts']['n_accepted']}
  (A {facts['counts']['accepted_A']} / B {facts['counts']['accepted_B']}) ·
  REJECT_HEAT_CAP {facts['counts']['n_rejected']}
- canonical book hash `{CANONICAL_BOOK_HASH}` · D1.1 grid {GRID_COUNTS} (PASS)
- D1.1A PASS verified: {facts['d1_1a_status']}

## Scenario profile registry (USER_SPECIFIED_SCENARIO — no broker truth)

| profile | equity | leverage | truth class | instrument spec |
|---|---|---|---|---|
{reg}

## Lane B vs Lane C

Lane B quantity representability is planned; Lane C margin/buying-power is
EXCLUDED (deferred to D1.3).  An event can be QUANTITY_REPRESENTABLE and
later MARGIN_BLOCKED.

## Rounding / fidelity (frozen defaults)

Primary {ROUNDING_PRIMARY} · upward default {UPWARD_ROUNDING_DEFAULT} ·
min {MIN_QUANTITY_DEFAULT} · max {MAX_QUANTITY_DEFAULT} · clipping
{CLIPPING_DEFAULT} · comparator {ROUNDING_COMPARATOR} · immaterial tolerance
{IMMATERIAL_RELATIVE_ERROR:.0%} / distorted {DISTORTED_RELATIVE_ERROR:.0%}
(preregistered; never chosen from performance).

## Missing truth

{len(missing_truth_register())} unresolved fields, all UNKNOWN, all blocking
for empirical D1.2.  Empirical quantity study is BLOCKED until quantity
fields are frozen (D1.2A).

## Decision

`d1_2_plan_pass = {decision['d1_2_plan_pass']}` ·
`d1_2_empirical_authorized = false` · `d1_3_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: {NEXT_CHECKPOINT} (then {NEXT_AFTER_INGEST}).
"""


def main() -> Dict:
    OUT.mkdir(parents=True, exist_ok=True)
    facts = verify_frozen_facts()
    decision = build_decision(facts)
    status = decision["status"]

    (OUT / "CR_BLOCK4_D1_2_SOURCE_SHA_MANIFEST.json").write_text(
        json.dumps(sha_manifest(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2_PHYSICAL_PROFILE_SCHEMA.json").write_text(
        json.dumps(physical_profile_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2_INSTRUMENT_SPEC_SCHEMA.json").write_text(
        json.dumps(instrument_spec_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2_ACCOUNT_PROFILE_SCHEMA.json").write_text(
        json.dumps(account_profile_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2_FEASIBILITY_STATE_SCHEMA.json").write_text(
        json.dumps(feasibility_state_schema(), indent=2), encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    pd.DataFrame(profile_registry()).to_csv(
        OUT / "CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv", index=False)
    pd.DataFrame(missing_truth_register()).to_csv(
        OUT / "CR_BLOCK4_D1_2_MISSING_TRUTH_REGISTER.csv", index=False)
    pd.DataFrame(component_status_rows(status)).to_csv(
        OUT / "CR_BLOCK4_D1_2_COMPONENT_STATUS.csv", index=False)

    docs = {
        "CR_BLOCK4_D1_2_PROTOCOL.md": _protocol(facts),
        "CR_BLOCK4_D1_2_SCIENTIFIC_QUESTION.md": _scientific_question(facts),
        "CR_BLOCK4_D1_2_TRUTH_HIERARCHY.md": _truth_hierarchy(),
        "CR_BLOCK4_D1_2_RUNTIME_HANDOFF_CONTRACT.md": _runtime_handoff(),
        "CR_BLOCK4_D1_2_QUANTITY_PIPELINE.md": _quantity_pipeline(),
        "CR_BLOCK4_D1_2_ROUNDING_POLICY.md": _rounding_policy(),
        "CR_BLOCK4_D1_2_FIDELITY_METRICS.md": _fidelity_metrics(),
        "CR_BLOCK4_D1_2_ACCOUNT_SIZE_PLAN.md": _account_size_plan(),
        "CR_BLOCK4_D1_2_CURRENCY_CONVERSION_PLAN.md": _currency_conversion_plan(),
        "CR_BLOCK4_D1_2_COUNTERFACTUAL_PLAN.md": _counterfactual_plan(),
        "CR_BLOCK4_D1_2_IMPLEMENTATION_SEQUENCE.md": _implementation_sequence(),
        "CR_BLOCK4_D1_2_TEST_PLAN.md": _test_plan(),
    }
    fam, pos, quant, sub = _family_pos_quantile_plans()
    docs["CR_BLOCK4_D1_2_FAMILY_DISTORTION_PLAN.md"] = fam
    docs["CR_BLOCK4_D1_2_POS_DISTORTION_PLAN.md"] = pos
    docs["CR_BLOCK4_D1_2_QUANTILE_DISTORTION_PLAN.md"] = quant
    docs["CR_BLOCK4_D1_2_SUBPERIOD_DISTORTION_PLAN.md"] = sub
    for name, content in docs.items():
        (OUT / name).write_text(content, encoding="utf-8")
    (OUT / "CR_BLOCK4_D1_2_REPORT.md").write_text(_report(facts, decision), encoding="utf-8")
    return decision


if __name__ == "__main__":
    d = main()
    print(json.dumps({
        "checkpoint": CHECKPOINT,
        "status": d["status"],
        "d1_2_plan_pass": d["d1_2_plan_pass"],
        "n_accepted": d["n_accepted"],
    }, indent=2))
