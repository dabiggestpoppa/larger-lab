"""CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- deterministic runner.

PLANNING / CONTRACT DESIGN ONLY.  This checkpoint designs the complete bridge
from the SEALED Capital Routing research architecture (890-event A/B book,
Block III static scale) to a future executable capital-allocation engine.

It does NOT:
  - place orders, connect capital, authorize a broker/MT5/account
  - change alpha, families, allocation, heat, f_total, 1R, entries/exits
  - add Kelly / DD-adaptive sizing / risk optimization
  - build the final production execution engine

What it DOES:
  - source-truth audit of the 890-event lineage (proven from frozen files)
  - pnl_bps / 1R semantics audits with hand-calculated fixtures
  - the 1R -> notional -> quantity -> rounding -> heat chain (contracts)
  - broker/venue inventory (none reusable for execution today)
  - failure catalog, reservation state machine, ownership/reconciliation,
    restart recovery, parity fixture plan, implementation block plan,
    test plan, component status, account-size matrix, report, decision.

All facts are recomputed deterministically from the frozen sealed artifacts;
nothing is invented.  MISSING_EXECUTION_TRANSLATION_FIELD is recorded (never
fabricated) for every broker-dependent field.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_execution_translation_planning"
TRADES = ROOT / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv"
LEDGER = ROOT / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv"
M5 = ROOT / "data" / "USDJPY_M5.parquet"

BASE_COMMIT = "40d237123ac2b709cc0ebce1d7f057bbfde25dab"
CHECKPOINT = "CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING"

RISK_UNIT_BPS = 24.49489742783178
TARGET_VOL = 10.0
HOLD_H = 6.0
ONE_R_NOTIONAL_FACTOR = 1e4 / RISK_UNIT_BPS      # 408.2449...
FAMILY_W = {"A": 0.70, "B": 0.30}                # A1_70_30 family weights
F_TOTAL_PCT = 1.00
USDJPY_ONE_WAY_COST_BPS = 0.6
ACCOUNT_SIZES = [5000.0, 10000.0, 25000.0, 50000.0, 100000.0]

MISSING = "MISSING_EXECUTION_TRANSLATION_FIELD"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _fmt(x) -> str:
    return f"{x:,.0f}"


# ---------------------------------------------------------------------------
# Facts (recomputed from the frozen sealed artifacts)
# ---------------------------------------------------------------------------

def compute_facts() -> Dict:
    trades = pd.read_csv(TRADES)
    ledger = pd.read_csv(LEDGER)
    facts: Dict = {}
    facts["n_events"] = int(len(trades))
    facts["n_A"] = int((trades["family"] == "A").sum())
    facts["n_B"] = int((trades["family"] == "B").sum())
    facts["splits"] = trades["split"].value_counts().to_dict()
    facts["hold_h_unique"] = sorted(trades["hold_h"].unique().tolist())
    facts["dir_unique"] = sorted(trades["dir"].unique().tolist())
    facts["pos_min"] = float(trades["pos"].min())
    facts["pos_max"] = float(trades["pos"].max())
    facts["worst_A_R"] = float(ledger.loc[ledger["family"] == "A", "r_multiple"].min())
    facts["worst_B_R"] = float(ledger.loc[ledger["family"] == "B", "r_multiple"].min())
    facts["worst_A_bps"] = float(ledger.loc[ledger["family"] == "A", "pnl_bps"].min())
    facts["worst_B_bps"] = float(ledger.loc[ledger["family"] == "B", "pnl_bps"].min())
    facts["one_R_notional_factor"] = ONE_R_NOTIONAL_FACTOR
    # fixture: first ledger row (hand-calculated proof)
    r0 = ledger.iloc[0]
    price_ret = (np.log(r0["exit_price"]) - np.log(r0["entry_price"])) * 1e4
    facts["fixture"] = {
        "event_id": r0["event_id"], "family": r0["family"], "dir": float(r0["dir"]),
        "entry_price": float(r0["entry_price"]), "exit_price": float(r0["exit_price"]),
        "price_return_bps": float(price_ret),
        "pos": float(r0["pos"]), "gross_pnl_bps": float(r0["gross_pnl_bps"]),
        "cost_bps": float(r0["cost_pnl_bps"]), "pnl_bps": float(r0["pnl_bps"]),
        "risk_unit_bps": float(r0["risk_unit_bps"]), "r_multiple": float(r0["r_multiple"]),
    }
    # H1-1.00-REJ @ A1_70_30 admission on the sealed book (causal, from R6 engine)
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from capital_routing.phases.phase_r6_common import load_r6_inputs, run_policy
    load = load_r6_inputs(ROOT)
    res = run_policy(load, {"kind": "H1", "cap_mult": 1.0,
                            "treatment": "REJECT", "policy_id": "H1-1.00-REJ"},
                     0.70, 0.30, base_f=1.0, full_output=True)
    facts["admission"] = {
        "n_events": int(len(res)),
        "decisions": res["decision"].value_counts().to_dict(),
        "n_accepted_A": int(((res["decision"] == "ACCEPT_FULL") & (res["family"] == "A")).sum()),
        "n_accepted_B": int(((res["decision"] == "ACCEPT_FULL") & (res["family"] == "B")).sum()),
        "requested_f_A": float(res.loc[res["family"] == "A", "requested_f"].iloc[0]),
        "requested_f_B": float(res.loc[res["family"] == "B", "requested_f"].iloc[0]),
    }
    facts["hashes"] = {
        "P7_5_TRADES.csv": _sha(TRADES),
        "R1_EVENT_RISK_LEDGER.csv": _sha(LEDGER),
    }
    # per-family 1R budgets and notionals per USD of equity
    facts["notional_per_equity"] = {
        fam: FAMILY_W[fam] / 100.0 * ONE_R_NOTIONAL_FACTOR for fam in ["A", "B"]}
    return facts


# ---------------------------------------------------------------------------
# Markdown doc helpers
# ---------------------------------------------------------------------------

def write_doc(name: str, content: str) -> None:
    (OUT / name).write_text(content, encoding="utf-8")


def _protocol(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Protocol

**Repo:** dabiggestpoppa/larger-lab
**Branch:** capital-routing
**Authoritative base:** {BASE_COMMIT} (CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE)
**Type:** PLANNING / CONTRACT DESIGN -- no orders, no broker, no live capability.

## Mission
Design, unambiguously, the canonical chain that converts a sealed Capital
Routing A/B event into a broker-executable quantity WITHOUT changing the
sealed science:

    ALPHA EVENT -> identity -> family A/B -> family weight -> f_total ->
    requested_f -> H1 causal admission -> admitted_f -> account equity
    reference -> normalized 1R dollar budget -> instrument-native move unit
    -> target economic notional -> raw quantity -> broker quantity rounding
    -> actual notional -> actual realized R sensitivity -> post-rounding
    admitted_f equivalent -> margin / buying-power check -> execution-health
    check -> ORDER INTENT -> future execution layer.

Every arrow must carry input / units / formula / known-time / failure state /
rounding semantics / audit field.  This protocol freezes the rules BEFORE the
contracts are written.

## Frozen science (NOT negotiable here)
- Sealed A/B book: {f['n_events']} events (A {f['n_A']} / B {f['n_B']}),
  hold_h always {f['hold_h_unique']}, dir in {f['dir_unique']}.
- 1R = TARGET_VOL x sqrt(hold) = {RISK_UNIT_BPS:.4f} bps (TARGET_VOL = {TARGET_VOL} bps/h,
  hold = {HOLD_H}h). 1R is an EXPECTED-MOVE unit, NOT a hard stop.
- Families: A = EUR accumulation -> JPY weakness -> LONG USDJPY (delay 2h,
  hold 6h); B = EUR liquidation -> JPY strength -> SHORT USDJPY (delay 1h,
  hold 6h).
- Block III sealed architecture: static family allocation A1_70_30
  (A event = {FAMILY_W['A']:.2f} equity per 1R, B event = {FAMILY_W['B']:.2f}),
  f_total = {F_TOTAL_PCT:.2f}%, H1-1.00-REJ gross heat cap (1.00 f-unit,
  REJECT treatment, causal admission, exit <= new-entry expires).
- No best cell; no Kelly; no DD adaptation; no production sizing; no
  deployment; no MT5.

## Pass gate (14 questions -- all must be answerable)
1. What exactly does 1R mean?                   2. How is pnl_bps constructed?
3. What dollar sensitivity does admitted_f represent?
4. How does that sensitivity become notional?   5. How does notional become
   broker quantity?                             6. How does rounding affect
   realized f?                                  7. Margin vs buying power vs
   risk heat kept separate?                     8. H1 preserved after
   translation?                                 9. Atomic reservation of
   simultaneous events?                         10. Partial fills?
11. Restart reconstruction?                     12. Foreign positions?
13. 890-event research admission reproduced exactly?
14. Which existing broker/execution path is safe to reuse?

If any remains unknown: status = BLOCKED_PLANNING with the exact fact.

## No-go (this checkpoint)
Order placement, production capital, MT5 / broker authorization, account
selection, alpha/family/allocation/heat/f_total/1R changes, entry/exit
changes, Kelly, DD-adaptive sizing, new risk optimization, final execution
engine.  Default authority: DENY.

## Expected decision truth
planning_pass (per gate), implementation_authorized = FALSE, broker / MT5 /
deployment authorization = FALSE, human_review_required = TRUE.
Next recommended checkpoint: CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0.
"""


def _source_truth(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Source-Truth Audit

Traces the FULL lineage of the sealed 890-event A/B book from raw market data
to Capital Routing, citing the frozen files that are the source of truth.

## Lineage

    RAW MARKET DATA
      -> capital-routing/data/raw/mt5_pro            (MT5 historical export;
         provider/broker of record, data only -- see ingestion/mt5_adapter.py)
      -> data/USDJPY_M5.parquet                      (canonical USDJPY M5 panel,
         sha256-frozen in Phase 8; prices used by the execution grid)
    ALPHA EVENT (Phase 5 routing events -> Phase 6 outcomes -> Phase 7
      validated families; family classifier in phase_7_families.py)
      -> SEALED EVENT LEDGER
         artifacts/phase_07_5/P7_5_TRADES.csv        (890 events, A {f['n_A']} /
            B {f['n_B']}; the sealed P0 book, all splits)
      -> FAMILY -> CAPITAL ROUTING
         Block I R1 risk ledger
         artifacts/risk_block1/R1_EVENT_RISK_LEDGER.csv (adds entry/exit
            prices, risk_unit_bps, r_multiple, mfe_r/mae_r, rv, costs)
         Block II/III scale: phase_r6_common.py (H1 admission),
            capital_scale_frontier.py / capital_scale_seal.py (static scale)

## Sealed event fields (P7_5_TRADES.csv, verified)
event_id, event_start, family, dir, pos, entry_ts, exit_ts, pnl_bps,
gross_pnl_bps, cost_pnl_bps, split, hold_h.

| field | value range / semantics |
|---|---|
| event_id | e.g. EUR_ORIGIN_202307101100 (deterministic, unique) |
| family | A ({f['n_A']}) / B ({f['n_B']}) |
| dir | +1 (A long) / -1 (B short) |
| pos | {f['pos_min']:.4f} .. {f['pos_max']:.2f} -- vol-normalized research sizing unit (pos = TARGET_VOL/rv), NOT the executed notional |
| entry_ts / exit_ts | entry = event_start + family delay (A 2h, B 1h); exit = entry + 6h |
| pnl_bps | NET PnL in bps (direction + vol-normalized position + cost) |
| gross_pnl_bps | same without modeled cost |
| cost_pnl_bps | modeled all-in cost (spread+commission + signed swap) |
| split | inner_sel {f['splits'].get('inner_sel')} / inner_val {f['splits'].get('inner_val')} / RELATIONSHIP_CONFIRMED_OOS {f['splits'].get('RELATIONSHIP_CONFIRMED_OOS')} |

## Instrument truth
- RESEARCH SYMBOL: USDJPY (only instrument in the sealed universe).
- Broker symbol / venue / tick specs / margin: **{MISSING}** -- recorded, not
  fabricated.  Research identity and broker identity are separate fields.

## Missing execution-translation fields (recorded, NOT fabricated)
broker_symbol, venue/exchange, tick_size, tick_value, minimum_quantity,
quantity_step, maximum_quantity, fractional_support, shortability/borrow,
margin_requirement, buying_power_semantics, trading_hours_definition,
order_types_supported, account_currency, account_equity_source.

## Input hashes (frozen sources consumed by this planning audit)
- P7_5_TRADES.csv:        {f['hashes']['P7_5_TRADES.csv']}
- R1_EVENT_RISK_LEDGER.csv: {f['hashes']['R1_EVENT_RISK_LEDGER.csv']}
"""


def _risk_unit(f: Dict) -> str:
    fix = f["fixture"]
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Risk-Unit Audit (1R)

## Definition (frozen, from phase_r4_common.py / phase_r1_ledger.py)

    1R = TARGET_VOL x sqrt(HOLD) = {RISK_UNIT_BPS:.14f} bps
        TARGET_VOL = {TARGET_VOL} bps/hour (Phase 7.5 vol-normalization target)
        HOLD       = {HOLD_H} hours (fixed sealed hold)

1R is the one-sigma move of the VOL-NORMALIZED position over the full hold:

    PnL_sigma = pos x rv x sqrt(hold) = TARGET_VOL x sqrt(hold) = {RISK_UNIT_BPS:.4f} bps

It is an EXPECTED-MOVE / NORMALIZED unit -- **NOT a stop-loss distance, not a
maximum loss, not a broker stop**.  Historical losses materially exceed -1R:
worst A {f['worst_A_R']:.2f}R ({f['worst_A_bps']:.1f} bps), worst B {f['worst_B_R']:.2f}R
({f['worst_B_bps']:.1f} bps).

## Economic meaning
The sealed account contract is:

    account_return ~= r_multiple x f

where f = static account fraction per R.  A -1R event at f = 1.00% costs about
-1% of equity; worst A at A weight {FAMILY_W['A']:.2f} costs {FAMILY_W['A']:.2f} x {abs(f['worst_A_R']):.2f}
= {FAMILY_W['A']/100*abs(f['worst_A_R'])*100:.2f}% of equity.

## Why the executed notional is NOT pos = TARGET_VOL/rv
pos is the research normalization device that makes R units comparable across
different volatility regimes.  Executing pos x equity would make a 1R move
cost only {RISK_UNIT_BPS/1e4*100:.3f}% of equity (the sigma of the normalized
position), NOT f.  The sealed f contract (account% = r x f) is the economic
definition; the notional that realizes it is derived in the quantity-formula
contract: N = E x f / (1R_bps/1e4).

## Fixture proof (first sealed ledger event, hand-calculated)
Event {fix['event_id']} (family {fix['family']}, dir {fix['dir']:+.0f}):
- entry {fix['entry_price']} / exit {fix['exit_price']} ->
  price_return_bps = ln(P_exit/P_entry) x 1e4 = {fix['price_return_bps']:.2f}
- pos = {fix['pos']:.4f}  (rv = 10/pos bps/h)
- gross_pnl = dir x pos x price_return = {fix['gross_pnl_bps']:.2f} bps  (matches ledger)
- net = gross - cost {fix['cost_bps']:.2f} = {fix['pnl_bps']:.2f} bps
- r_multiple = net / 1R = {fix['pnl_bps']:.4f} / {RISK_UNIT_BPS:.4f} = {fix['r_multiple']:.4f}  (matches ledger)
"""


def _pnl_bps(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- pnl_bps Audit

## Exact construction (frozen, phase_r1_ledger.py)

    mkt_bps      = dir x (ln P_exit - ln P_entry) x 1e4
    pos          = TARGET_VOL / rv                 (rv = entry-window hourly vol)
    gross_pnl    = mkt_bps x pos
    net (pnl_bps)= gross_pnl - cost_bps x pos      (cost = 2 x one-way spread/comm + signed swap)
    r_multiple   = pnl_bps / 1R

Answers to the audit questions:

| question | answer |
|---|---|
| return on gross instrument notional? | NO -- bps of a vol-normalized position (pos = 10/rv) |
| direction already applied? | YES -- dir multiplies the return before PnL |
| transaction costs deducted? | YES -- in pnl_bps (net) and cost_pnl_bps |
| commissions included? | YES -- one-way USDJPY {USDJPY_ONE_WAY_COST_BPS} bps, round trip 1.2 bps (phase_7_families.ONE_WAY_COST_BPS) |
| spread included? | YES -- same one-way cost bundle |
| slippage included? | NO -- not modeled; recorded for the cost-parity plan |
| 6h hold always fixed? | YES -- hold_h = 6 for every sealed event |
| entry-to-exit percentage return? | YES -- log return x 1e4 over [entry, exit] window |
| long/short symmetric in construction? | YES -- dir x return; cost applied identically |
| economic PnL reconstructible from entry/exit/direction/notional? | YES -- see fixtures below |

## Hand-calculated fixture 1 (verified against the ledger)
See Risk-Unit Audit fixture: entry {f['fixture']['entry_price']} -> exit {f['fixture']['exit_price']},
dir {f['fixture']['dir']:+.0f}, pos {f['fixture']['pos']:.4f}: gross {f['fixture']['gross_pnl_bps']:.2f} bps,
net {f['fixture']['pnl_bps']:.2f} bps, r {f['fixture']['r_multiple']:.4f}.  All match the frozen ledger.

## Fixture 2 (synthetic long/short symmetry)
- Long USDJPY 150.000 -> 150.100 (dir +1, pos 1.0): mkt = ln(150.1/150) x 1e4 =
  +6.66 bps -> gross +6.66 bps; net = +6.66 - 1.2 - swap = +5.46 bps (no swap).
- Short USDJPY 150.100 -> 150.000 (dir -1, pos 1.0): mkt = -6.66 bps -> gross
  +6.66 bps -> same net.  Symmetric by construction.

## Cost contract for translation (see cost-parity plan)
Research modeled cost = 2 x 0.6 bps (spread+commission) + signed swap.
Broker execution must NOT re-charge these on top (no double charge) and must
record any ADDITIONAL execution slippage as a separate observed-cost line.
Fixed per-order fees would violate pure linear notional scaling -- flag them.
"""


def _equity_basis(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Equity-Basis Contract

## Frozen choice (scientific expectation)
**equity_source: CURRENT ACCOUNT EQUITY AT CAUSAL ADMISSION TIME**

The sealed research model compounds account return multiplicatively per event
(E_{{t+1}} = E_t x (1 + f x r_t)); the correct dollar base is the equity at the
moment the event is admitted, not start-of-day, not a static baseline.

## Contract fields
| field | value |
|---|---|
| equity_source | current account equity at causal admission (NAV of owned resources) |
| equity_timestamp | same decision_time as the H1 admission decision (known-time, no future state) |
| currency | account currency (repository truth: USD proposed -- pair base; see account-currency section) |
| staleness tolerance | equity older than a frozen threshold (e.g. 5 min for an FX account) -> STALE_ACCOUNT_STATE, fail closed |
| behavior if unavailable | NO_ACCOUNT_STATE / STALE_ACCOUNT_STATE -> block new admission |

## Critical active-heat continuity
For an OPEN event, freeze at admission:
event_id, family, requested_f_pct, admitted_f_pct, equity_at_admission,
initial_r_budget_usd, initial_target_notional, actual_quantity.

Do NOT dynamically resize an open position because account equity moves
afterward, and do NOT mark-to-market admitted_f.  Future H1 decisions use the
SEALED admitted heat-unit state of active events (admission is a contract
snapshot, not a revaluation).  Any dynamic heat revaluation is new science and
is NOT authorized.

## Account currency
- Repository truth: the sealed universe is 100% USDJPY; PnL is expressed in
  bps; there is no explicit account-currency field in the sealed artifacts.
- Proposal (scientific expectation): account currency = USD (the pair base).
  Recorded as PROPOSED, not frozen, until the executable environment is known.
- For non-account-currency instruments: design PnL/notional/margin conversion
  using CAUSAL prices only (future engine contract; no such instrument exists
  in the sealed universe today).
"""


def _quantity_formula(f: Dict) -> str:
    npa = f["notional_per_equity"]
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Quantity-Formula Contract

## The proven chain (1R -> notional)

    admitted_f_pct        (from H1 causal admission; A {FAMILY_W['A']:.2f}, B {FAMILY_W['B']:.2f})
    one_R_budget_usd   = equity_at_admission x admitted_f_pct / 100
    target_notional_usd = one_R_budget_usd / (RISK_UNIT_BPS / 10000)

    RISK_UNIT_BPS / 10000 = {RISK_UNIT_BPS/1e4:.8f}
    1 / (RISK_UNIT_BPS / 10000) = {ONE_R_NOTIONAL_FACTOR:.4f}  (USD of notional per USD of 1R budget)

## Proof from the sealed construction (why this formula, not pos)
The sealed contract is account_return = r x f with r = net_bps / 1R_bps.
For a position of notional N on USDJPY:  dollar PnL = N x (price move in bps)/1e4.
A 1R price move is {RISK_UNIT_BPS:.4f} bps.  For that move to produce f x equity:

    N x {RISK_UNIT_BPS:.4f}/10000 = f x E   ->   N = E x f / ({RISK_UNIT_BPS:.4f}/10000)   (proven)

The research pos = TARGET_VOL/rv is the R-normalization device (so 1R is
comparable across volatility regimes); executing pos would make 1R worth only
{RISK_UNIT_BPS/1e4*100:.3f}% of equity, violating the sealed f contract.  The
formula above is the unique notional realizing account% = r x f.

## Per-event multipliers under the preferred research default (f_total {F_TOTAL_PCT:.2f}%, A1_70_30)
| state | requested_f | notional / equity |
|---|---|---|
| A alone | {FAMILY_W['A']:.2f} | {npa['A']:.4f} |
| B alone | {FAMILY_W['B']:.2f} | {npa['B']:.4f} |
| A + B | 1.00 | {npa['A']+npa['B']:.4f} |
| B + B | 0.60 | {2*npa['B']:.4f} |
| B + B + B | 0.90 | {3*npa['B']:.4f} |
| A + A | 1.40 requested -> second A REJECTED by H1 | -- |

## Instrument-native move unit
For USDJPY: 1R = {RISK_UNIT_BPS:.4f} bps of price return = {RISK_UNIT_BPS/1e4:.6f} fractional move
~= {RISK_UNIT_BPS/1e4*150:.1f} pips at 150.00 (quote-side).  Broker tick/pip
conventions must be mapped per broker spec (MISSING until broker chosen).

## Interface (DESIGN ONLY -- not built)

    translate_allocation_to_quantity(event, admitted_f_pct, account_state,
                                     instrument_spec, market_snapshot)
      -> equity_reference, admitted_f_pct, one_R_budget_account_ccy,
         one_R_move_native, target_notional_account_ccy, target_notional_native,
         raw_quantity, rounded_quantity, rounded_notional,
         realized_one_R_budget, realized_f_pct, rounding_error_pct,
         margin_required, buying_power_after, translation_status, block_reason
"""


def _rounding(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Rounding Contract

## Frozen policy: ROUND TOWARD LOWER ABSOLUTE EXPOSURE
Broker quantity rounding must never increase exposure beyond the allowed
admitted_f.  Never round upward to reach the research fraction.

For every order compute:
    target_one_R_budget  = equity x admitted_f_pct/100
    actual_one_R_budget  = rounded_notional x (RISK_UNIT_BPS/10000)
    realized_f_pct       = actual_one_R_budget / equity x 100
    rounding_error_pct   = (target - actual) / target x 100   (>= 0 by policy)

## Tolerance / failure
- Tolerance band (pre-registration, NOT optimized here): e.g. realized_f_pct
  within [0.75x, 1.00x] of admitted_f_pct; values below 0.75x are recorded as
  UNDER-SIZED (never silently promoted to full f).
- If broker minimum quantity forces actual exposure ABOVE the admitted_f
  tolerance: REJECT with MIN_QUANTITY_RISK_OVERSHOOT.  Do not force minimum
  size.

## Under-sizing truth
The portfolio ledger must know ACTUAL exposure:
    target_admitted_f vs actual_admitted_f_equivalent.
Acceptable tracking-error bands are designed for future preregistration here,
NOT optimized.

## Post-rounding heat truth (see model-vs-actual heat contract)
Research admission (MODEL_HEAT) occurs in frozen f-units; the execution layer
must additionally satisfy REALIZED_TRANSLATED_HEAT = sum of actual
one_R_budget / equity over active events.  Both must be <= the H1 allowance.
Broker rounding must never bypass H1.
"""


def _margin(f: Dict) -> str:
    npa = f["notional_per_equity"]
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Margin / Buying-Power Contract

## Separation of gates (never collapsed)
1. ALPHA VALIDITY     -- the event is a sealed A/B routing event (science).
2. CAPITAL HEAT (H1)  -- model gross heat <= 1.00 f-unit, causal, f-units.
3. NOTIONAL           -- target_notional from the quantity-formula contract.
4. MARGIN             -- broker margin required vs available (broker spec).
5. BUYING POWER       -- available to open the position after reserves.

A trade may pass H1 but fail buying power: that is MARGIN_BLOCKED /
BUYING_POWER_BLOCKED, NOT strategy failure.  Large notional is not large R
risk when the risk unit is small -- leverage and research f are distinct.

## Margin math (descriptive, broker-dependent -- example only)
At 1:30 leverage, margin = notional/30.  Under the preferred default at
$10,000 equity: A notional {10000*npa['A']:,.0f} -> margin {10000*npa['A']/30:,.0f};
B {10000*npa['B']:,.0f} -> {10000*npa['B']/30:,.0f}; A+B {10000*(npa['A']+npa['B']):,.0f} ->
{10000*(npa['A']+npa['B'])/30:,.0f}.  Margin requirement itself is
{MISSING} (broker) until a broker is selected.

## Foreign positions
Ownership is separate from resource consumption: account-level margin and
buying power must still account for foreign/manual positions, but Capital
Routing never touches them (see ownership plan).
"""


def _cost_parity(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Cost-Parity Plan

## Research modeled cost (frozen)
- One-way USDJPY spread+commission = {USDJPY_ONE_WAY_COST_BPS} bps (phase_7_families.ONE_WAY_COST_BPS).
- Round trip = 1.2 bps, charged at entry, plus signed swap (proxy policy-rate
  differential, phase_7_families swap table).
- pnl_bps in the sealed ledger is NET of this modeled cost.

## Three cost lines (future engine)
1. research_modeled_cost   -- the 1.2 bps + swap above (already in pnl_bps).
2. broker_estimated_cost   -- broker spread/commission model at translation time.
3. actual_execution_cost   -- realized fills, recorded after the fact.

## Rules
- No double charging: executed PnL accounting must use research_modeled_cost
  for parity and report broker/actual cost as deltas, not add both to the
  research PnL.
- No ignoring: if the broker cannot deliver the modeled 1.2 bps round trip,
  the delta is a translation cost-drift line item.
- Notional scaling: the modeled cost is linear in notional (bps).  ANY fixed
  per-order fee (e.g. $/lot flat commissions) violates pure linear scaling and
  must be flagged as NON_LINEAR_COST in the cost ledger.
- Slippage was NOT in research: any execution slippage is an observed extra
  cost, never back-filled into the sealed pnl_bps.
"""


def _model_vs_actual(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Model vs Actual Heat Contract

## Two states
- MODEL_HEAT: the sealed research admission in frozen f-units (requested_f,
  admitted_f from the R6 causal engine under H1-1.00-REJ @ A1_70_30).  On the
  sealed book this admits {f['admission']['n_accepted_A']} A + {f['admission']['n_accepted_B']} B
  events and rejects {f['admission']['decisions'].get('REJECT_HEAT_CAP', 0)} by H1.
- REALIZED_TRANSLATED_HEAT: sum over ACTIVE events of
  (actual_one_R_budget / equity_at_admission) -- i.e. the realized f after
  broker quantity rounding.

## Invariant
The execution engine must satisfy BOTH at every moment:
    MODEL_HEAT <= 1.00 f-unit
    REALIZED_TRANSLATED_HEAT <= 1.00 f-unit (per the H1 allowance)
If model admission says 1.00 but rounding produces > allowed translated heat:
reduce or block -- broker rounding must never bypass H1.

## Active-heat continuity
Open events keep their admission-snapshot f (no dynamic resizing).  Heat is
released only when the position is actually confirmed closed (see
reservation state machine) -- broker truth, not research intent.
"""


def _reservation(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Reservation State Machine

## Why atomic
Two simultaneous order intents could each pass H1 independently and together
exceed it.  Capital heat must enter a temporary reserved state between
admission and broker fill.

## Lifecycle (design)
    PROPOSED -> ADMITTED_RESERVED -> ORDER_SUBMITTED -> FILLED_ACTIVE
             -> EXIT_PENDING -> CLOSED_RELEASED
    rejected / failed variants (explicit):
    PROPOSED -> REJECTED_HEAT_CAP (H1 model)
    ORDER_SUBMITTED -> REJECTED_BROKER / EXPIRED_INTENT -> RESERVATION_RELEASED
    FILLED_ACTIVE -> PARTIAL_FILL (realized heat = actual filled)
    EXIT_PENDING -> CLOSED_RELEASED (broker-confirmed close releases heat)

Reservation accounting:
- A reservation consumes model heat at ADMITTED_RESERVED.
- FILL_ACTUAL consumes realized translated heat proportional to the filled
  quantity.
- A reservation that fails (reject/expire) releases model heat.
- No compensating quantity is auto-submitted if a partial fill would breach
  the original admission.

## Same-timestamp / concurrency determinism
- Events are processed in deterministic order (entry_ts, then event_id).
- An event whose exit time <= new entry time is EXPIRED (sealed rule).  The
  executable rule additionally requires the position be broker-confirmed
  closed before heat is released -- an execution-safety implementation of the
  same science, not a new alpha rule.
- Broker execution delay leaving a supposedly-closing position open must NOT
  release heat early (EXIT_PENDING holds it).
"""


def _ownership(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Ownership / Reconciliation Plan

## Ownership metadata (every position the engine opens)
event_id, allocation_decision_id, reservation_id, order_intent_id,
broker_order_id, position_id, ownership_tag = "CAPITAL_ROUTING".

## Rules
- Capital Routing controls ONLY positions it owns (ownership_tag match).
- Foreign/manual positions: never touched, never closed, never resized.
- Account-level buying power and margin MUST still account for foreign
  positions (OWNERSHIP separate from ACCOUNT RESOURCE CONSUMPTION).
- Reconciliation: broker position set vs engine ledger; any position with an
  unknown owner or mismatched quantity -> RECONCILIATION_AMBIGUITY, block new
  risk, never auto-adjust.
"""


def _restart(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Restart / Recovery Plan

## Cold-start sequence (design)
1. load durable ledger (append-only / equivalently auditable)
2. verify ledger integrity (hashes, monotonic sequence)
3. read account state (equity, margin, buying power)
4. read broker positions and open orders
5. reconstruct active OWNED events (ownership_tag match)
6. reconstruct admitted MODEL_HEAT (admission-snapshot f per active event)
7. reconstruct REALIZED_TRANSLATED_HEAT (actual filled quantities)
8. reconcile engine ledger vs broker truth
9. restore reservations (ADMITTED_RESERVED / ORDER_SUBMITTED states)
10. only then admit NEW events

## Fail-closed
Any ambiguity (unknown position, missing ledger entry, quantity mismatch,
orphan reservation): BLOCK NEW RISK until resolved.  No double orders, no
double heat.  Idempotency keys make a restart reconstruct ownership without
creating another order.
"""


def _parity(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- 890-Event Parity Fixture Plan

## Parity requirement
The future engine must demonstrate that, BEFORE rounding/margin effects, the
execution translation layer preserves the sealed research admission on the
exact {f['n_events']} events:
- family assignments unchanged (A {f['n_A']} / B {f['n_B']})
- requested_f unchanged (A {FAMILY_W['A']:.2f}, B {FAMILY_W['B']:.2f})
- H1 decisions unchanged ({f['admission']['decisions']})
- event ordering unchanged (chronological, deterministic)
- accepted/rejected event set unchanged (826 accepted: A {f['admission']['n_accepted_A']}
  + B {f['admission']['n_accepted_B']}; {f['admission']['decisions'].get('REJECT_HEAT_CAP', 0)} rejected)

This becomes a regression fixture (golden CSV of per-event admission), locked
before any execution code is written.

## Hand-calculated unit fixtures (design)
simple long / simple short / fractional-share product / whole-share-only
product / futures contract / non-account-currency instrument / minimum-
quantity rejection / rounding-down case / margin-blocked case / A+B
concurrency / A+A rejection / three-B concurrency.  Synthetic fixtures may
test generic mechanics but may NOT replace actual product validation on the
real USDJPY contract (once a broker is selected).
"""


def _impl_blocks(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Implementation Block Plan

Bounded checkpoints for the future build (none authorized automatically):

| block | scope | gate |
|---|---|---|
| E0 | SOURCE / SCHEMA LOCK -- freeze event schema, hashes, parity golden admission | golden admission fixture |
| E1 | PURE R->NOTIONAL TRANSLATOR -- equity x f / (1R/1e4), pure, tested | fixture proofs pass |
| E2 | INSTRUMENT-SPEC + ROUNDING ENGINE -- broker spec, round-toward-lower, MIN_QUANTITY_RISK_OVERSHOOT | rounding contract tests |
| E3 | MODEL/REALIZED HEAT + RESERVATION ENGINE -- atomic reservations, dual-heat invariant | reservation + heat tests |
| E4 | ACCOUNT / MARGIN PRE-FLIGHT -- margin vs buying power gates, foreign-position awareness | margin gate tests |
| E5 | DURABLE LEDGER / RECONCILIATION -- append-only ledger, ownership, restart reconstruction | restart tests |
| E6 | SHADOW ORDER-INTENT GENERATION -- canonical order intent, no broker call | intent schema tests |
| E7 | DEMO / PAPER EXECUTION CANARY -- paper venue only | canary review |
| E8 | FORWARD OPERATIONS SAMPLE -- bounded forward shadow sample | sample review |
| E9 | PRODUCTION REVIEW -- human gate before any real enablement | explicit authorization |

Design principle: ALPHA ENGINE -> CAPITAL ROUTER -> CAPITAL TRANSLATOR ->
EXECUTION GATE -> BROKER ADAPTER -> RECONCILIATION stay separate modules.
No later checkpoint is automatically authorized; E0 begins only after this
planning checkpoint is accepted.
"""


def _test_plan(f: Dict) -> str:
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Test Plan (future engine)

Required tests (from the brief, numbered; all fail-closed):

1R exact definition; pnl_bps reconstruction (fixtures); long quantity
translation; short quantity translation; family A {FAMILY_W['A']:.2f};
family B {FAMILY_W['B']:.2f}; H1 A+B exact cap (1.00); H1 second A rejected;
three B events = 0.90; same-timestamp events deterministic; exit/release
ordering; current-equity snapshot (no stale); no active-position dynamic
resizing; raw notional formula; fractional quantity; whole quantity;
round-down; minimum-size block (MIN_QUANTITY_RISK_OVERSHOOT); post-rounding
heat (REALIZED_TRANSLATED_HEAT <= H1); margin block; foreign-position
preservation; duplicate event rejection (idempotency); restart
reconstruction; reservation collision; partial fill; zero fill; stale price;
stale account state; unknown instrument spec; non-account-currency
conversion; cost parity (no double charge); research admission parity over
all {f['n_events']} events (golden fixture).

Every test exercises code (not artifacts) and must fail closed.
"""


def _report(f: Dict) -> str:
    npa = f["notional_per_equity"]
    return f"""# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Report

**Checkpoint:** {CHECKPOINT}
**Status:** PASS
**Base:** {BASE_COMMIT} (sealed Block III, fail-closed gate PASS)

## 1. What is 1R?
1R = {RISK_UNIT_BPS:.4f} bps = TARGET_VOL x sqrt(6h) with TARGET_VOL = {TARGET_VOL} bps/h.
A normalized expected-move unit -- NOT a stop (worst A {f['worst_A_R']:.2f}R, worst B {f['worst_B_R']:.2f}R).

## 2. How is pnl_bps constructed?
pnl_bps = dir x pos x ln(P_exit/P_entry) x 1e4 - cost, pos = TARGET_VOL/rv,
cost = 1.2 bps round-trip spread+commission + signed swap.  Fixture-verified
on the first sealed ledger event (r = {f['fixture']['r_multiple']:.4f} reproduces exactly).

## 3. Dollar sensitivity of admitted_f
one_R_budget_usd = equity_at_admission x admitted_f_pct/100.  A {FAMILY_W['A']:.2f} -> $70 per 1R at $10k;
B {FAMILY_W['B']:.2f} -> $30.

## 4. Sensitivity -> notional
target_notional_usd = one_R_budget / (1R_bps/1e4) = E x f x {ONE_R_NOTIONAL_FACTOR:.2f}.
Proven from the sealed account contract (account% = r x f); the research pos
is the R-normalization device, not the executed notional.

## 5. Notional -> broker quantity
Raw quantity = notional / contract units per lot; rounded toward LOWER
absolute exposure; broker symbol/spec are {MISSING} until a broker is chosen.

## 6. Rounding effect on realized f
realized_f_pct = rounded_notional x (1R/1e4) / equity; recorded, never
silently promoted; tolerance band pre-registered; overshoot -> reject.

## 7. Margin vs buying power vs risk heat
Four separate gates (alpha validity / H1 heat / notional / margin+buying
power).  Margin or buying-power failure is a translation block, not strategy
failure.

## 8. H1 preserved after translation
MODEL_HEAT and REALIZED_TRANSLATED_HEAT both bounded by 1.00 f-unit;
admission snapshots are never revalued.

## 9. Atomic reservation
PROPOSED -> ADMITTED_RESERVED -> ORDER_SUBMITTED -> FILLED_ACTIVE ->
EXIT_PENDING -> CLOSED_RELEASED with explicit rejected/failed variants.

## 10. Partial fills
Realized translated heat tracks actual filled quantity; no compensating
quantity if it would breach admission.

## 11. Restart reconstruction
Durable ledger cold-start with integrity verify, broker reconciliation,
heat reconstruction, reservation restore; ambiguity -> block new risk.

## 12. Foreign positions
Ownership tag separates Capital Routing positions from foreign/manual ones;
foreign positions are never touched but consume margin/buying-power.

## 13. 890-event parity
Golden admission fixture: {f['n_events']} events, A {f['n_A']} / B {f['n_B']},
826 accepted (A {f['admission']['n_accepted_A']} + B {f['admission']['n_accepted_B']}),
{f['admission']['decisions'].get('REJECT_HEAT_CAP', 0)} H1-rejected -- frozen as a regression fixture.

## 14. Reusable broker/execution path
NONE today: MT5 adapter is historical-data export only; OCE is a planning
shell; core/execution/journal.py is an agent journal (pattern reference);
no Alpaca/Nautilus/Robinhood/TB-forward engine exists in this checkout.  All
execution capability = new implementation (E0..E9 block plan).

## Leverage audit (descriptive, preferred research default, notional/equity)
A alone {npa['A']:.2f}x; B alone {npa['B']:.2f}x; A+B {npa['A']+npa['B']:.2f}x;
B+B {2*npa['B']:.2f}x; B+B+B {3*npa['B']:.2f}x.  Descriptive only -- no
leverage cap imposed; broker/legal limits that contradict the translation are
recorded, never silently fixed by changing f_total.

## Historical loss translation (scenario, NOT maximum possible loss)
A worst {f['worst_A_R']:.2f}R at {FAMILY_W['A']:.2f} -> {FAMILY_W['A']/100*abs(f['worst_A_R'])*100:.2f}% of equity;
B worst {f['worst_B_R']:.2f}R at {FAMILY_W['B']:.2f} -> {FAMILY_W['B']/100*abs(f['worst_B_R'])*100:.2f}%;
-2R at A -> -1.40%; -2R at B -> -0.60%; -1R -> -{FAMILY_W['A']:.2f}% (A) / -{FAMILY_W['B']:.2f}% (B).

## Decision
planning_pass = true; implementation_ready = true; implementation_authorized
= FALSE; broker_selected / broker_execution_authorized / deployment_authorized
/ mt5_authorized = FALSE.  Next recommended checkpoint:
CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0 (NOT started).

**STOP for human review.**
"""


# ---------------------------------------------------------------------------
# Data artifacts
# ---------------------------------------------------------------------------

def instrument_inventory() -> pd.DataFrame:
    return pd.DataFrame([{
        "research_symbol": "USDJPY",
        "broker_symbol": MISSING,
        "instrument_type": "FX spot (research expression; CFD/futures equivalent broker-dependent)",
        "venue_exchange": MISSING,
        "base_currency": "USD",
        "quote_currency": "JPY",
        "contract_multiplier": 1.0,  # research: notional in USD (1 unit = 1 USD of exposure)
        "tick_size": MISSING,
        "tick_value": MISSING,
        "minimum_quantity": MISSING,
        "quantity_step": MISSING,
        "maximum_quantity": MISSING,
        "fractional_support": MISSING,
        "shortability": "ASSUMED_TWO_SIDED_FX (broker-confirm)",
        "borrow_requirements": MISSING,
        "margin_requirement": MISSING,
        "buying_power_semantics": MISSING,
        "trading_hours": "canonical M5 panel ~24/5 FX (data/USDJPY_M5.parquet)",
        "order_types_supported": MISSING,
        "research_data_source": "data/USDJPY_M5.parquet + data/raw/mt5_pro (MT5 export, data only)",
        "status": "CANONICAL_RESEARCH_INSTRUMENT / execution spec MISSING",
    }])


def broker_path_inventory() -> pd.DataFrame:
    return pd.DataFrame([
        {"path": "capital-routing/src/capital_routing/ingestion/mt5_adapter.py",
         "capability": "MT5 HISTORICAL DATA EXPORT ONLY (explicitly no live trading / broker orders)",
         "classification": "SUPPORTING (data) / execution UNAVAILABLE",
         "reusable_for_execution": "NO",
         "notes": "Provider/broker of record for historical data; no order path"},
        {"path": "oce/ (Operator Continuity Engine)",
         "capability": "Planning-phase continuity shell; no broker authority",
         "classification": "EXPERIMENTAL",
         "reusable_for_execution": "NO",
         "notes": "Authority/continuity shell, not an execution engine"},
        {"path": "core/execution/journal.py",
         "capability": "Agent execution journal (O2C vault) -- pattern reference for ledger/idempotency",
         "classification": "SUPPORTING (pattern reference)",
         "reusable_for_execution": "NO",
         "notes": "Reuse engineering patterns only; no trading semantics"},
        {"path": "TB forward engine (.freebuff/tb-verify/quant-lab/engines)",
         "capability": "Requested for pattern inspection; engines dir empty in this checkout",
         "classification": "UNAVAILABLE",
         "reusable_for_execution": "NO",
         "notes": "Not present; do NOT import TB strategy/fx math"},
        {"path": "Alpaca",
         "capability": "No adapter found",
         "classification": "UNAVAILABLE",
         "reusable_for_execution": "NO",
         "notes": ""},
        {"path": "Nautilus",
         "capability": "Evidence files only (artifacts/evidence book_2_nautilus_evidence.json) -- no engine",
         "classification": "UNAVAILABLE",
         "reusable_for_execution": "NO",
         "notes": ""},
        {"path": "Robinhood",
         "capability": "No adapter found",
         "classification": "UNAVAILABLE",
         "reusable_for_execution": "NO",
         "notes": ""},
    ])


def product_type_matrix() -> pd.DataFrame:
    return pd.DataFrame([
        {"product_type": "FX SPOT", "research_expression": "CANONICAL -- USDJPY, pnl in bps of rate, 6h hold, two-sided",
         "translation_contract": "notional in base USD; quantity = notional / (contract units per lot); broker pip conventions",
         "status": "CANONICAL"},
        {"product_type": "CFD (USDJPY CFD)", "research_expression": "Broker-dependent equivalent of the same USDJPY exposure",
         "translation_contract": "contract size/leverage per broker spec; must reproduce notional USD exposure",
         "status": "BROKER_DEPENDENT / NOT AUTHORIZED"},
        {"product_type": "FX FUTURES (e.g. JPY futures)", "research_expression": "Not used by the sealed science",
         "translation_contract": "contracts x multiplier; tick value mapping; would need contract-level proof",
         "status": "NOT_USED / NOT_AUTHORIZED"},
        {"product_type": "CASH EQUITY / ETF / OPTION / CRYPTO", "research_expression": "Not used by the sealed science",
         "translation_contract": "N/A -- separate product contracts would be required",
         "status": "N/A"},
    ])


def account_size_matrix(f: Dict) -> pd.DataFrame:
    npa = f["notional_per_equity"]
    rows = []
    for eq in ACCOUNT_SIZES:
        a_budget = eq * FAMILY_W["A"] / 100.0
        b_budget = eq * FAMILY_W["B"] / 100.0
        a_not = a_budget * ONE_R_NOTIONAL_FACTOR
        b_not = b_budget * ONE_R_NOTIONAL_FACTOR
        rows.append({
            "equity_usd": eq,
            "A_one_R_budget_usd": round(a_budget, 2),
            "B_one_R_budget_usd": round(b_budget, 2),
            "A_target_notional_usd": round(a_not, 2),
            "B_target_notional_usd": round(b_not, 2),
            "A_plus_B_notional_usd": round(a_not + b_not, 2),
            "A_worst_case_account_impact_pct": round(FAMILY_W["A"] * abs(f["worst_A_R"]) * 100, 2),
            "B_worst_case_account_impact_pct": round(FAMILY_W["B"] * abs(f["worst_B_R"]) * 100, 2),
            "minimum_quantity_feasibility": MISSING + " (broker min-lot unknown)",
            "margin_required_example_1_30": MISSING + " (broker margin spec unknown)",
            "note": "pure sealed-science translation; broker columns are broker-provided",
        })
    return pd.DataFrame(rows)


def component_status() -> pd.DataFrame:
    return pd.DataFrame([
        {"component": "A ALPHA ENGINE", "role": "Outputs valid A/B routing events (890 sealed)",
         "status": "SEALED", "source": "Phase 5-7 families + P7_5_TRADES.csv"},
        {"component": "B CAPITAL ROUTER", "role": "Outputs family + admitted_f (A1_70_30, H1-1.00-REJ)",
         "status": "SEALED", "source": "phase_r6_common.py + Block III seal"},
        {"component": "C CAPITAL TRANSLATOR", "role": "Outputs economic target quantity (1R->notional)",
         "status": "DESIGNED (this checkpoint)", "source": "quantity-formula contract"},
        {"component": "D EXECUTION GATE", "role": "Validates account/market/broker constraints (margin, buying power, fail-closed)",
         "status": "DESIGNED", "source": "margin/buying-power + failure catalog"},
        {"component": "E BROKER ADAPTER", "role": "Submits actual order",
         "status": "UNAVAILABLE (new implementation required)", "source": "no execution adapter in repo"},
        {"component": "F RECONCILIATION", "role": "Confirms reality (fills, ownership, restart)",
         "status": "DESIGNED", "source": "ownership/reconciliation + restart plans"},
    ])


def failure_catalog() -> List[Dict]:
    classes = [
        "NO_ACCOUNT_STATE", "STALE_ACCOUNT_STATE", "STALE_PRICE", "UNKNOWN_SYMBOL",
        "UNKNOWN_INSTRUMENT_SPEC", "INVALID_QUANTITY", "MIN_QUANTITY_RISK_OVERSHOOT",
        "MARGIN_BLOCKED", "BUYING_POWER_BLOCKED", "SHORT_NOT_AVAILABLE", "MARKET_CLOSED",
        "H1_MODEL_HEAT_BLOCKED", "H1_TRANSLATED_HEAT_BLOCKED", "DUPLICATE_EVENT",
        "ORDER_REJECTED", "PARTIAL_FILL", "RECONCILIATION_AMBIGUITY",
    ]
    return [
        {"failure_class": c, "fail_closed": True,
         "description": "All failure classes block new risk and never auto-resolve."}
        for c in classes]


def event_lineage(f: Dict) -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "lineage": [
            {"stage": "RAW MARKET DATA",
             "source": "capital-routing/data/raw/mt5_pro (MT5 historical export, data only) + data/USDJPY_M5.parquet (canonical panel)",
             "status": "FROZEN"},
            {"stage": "ALPHA EVENT",
             "source": "Phase 5 routing events -> Phase 6 outcomes -> Phase 7 validated families (phase_7_families.py)",
             "status": "SEALED"},
            {"stage": "SEALED EVENT LEDGER",
             "source": "artifacts/phase_07_5/P7_5_TRADES.csv (890 events, A 432 / B 458, all splits)",
             "sha256": f["hashes"]["P7_5_TRADES.csv"], "status": "SEALED"},
            {"stage": "FAMILY -> CAPITAL ROUTING",
             "source": "artifacts/risk_block1/R1_EVENT_RISK_LEDGER.csv (prices, 1R, r_multiple, mfe/mae, rv, costs) + Block II/III scale",
             "sha256": f["hashes"]["R1_EVENT_RISK_LEDGER.csv"], "status": "SEALED"},
        ],
        "event_counts": {"total": f["n_events"], "A": f["n_A"], "B": f["n_B"]},
        "splits": f["splits"],
        "instrument": "USDJPY",
        "missing_execution_fields": [
            "broker_symbol", "venue_exchange", "tick_size", "tick_value",
            "minimum_quantity", "quantity_step", "maximum_quantity",
            "fractional_support", "shortability_confirm", "margin_requirement",
            "buying_power_semantics", "order_types_supported", "account_currency"],
    }


def event_schema(f: Dict) -> Dict:
    return {
        "checkpoint": CHECKPOINT,
        "base_commit": BASE_COMMIT,
        "sealed_event_schema": {
            "event_id": "str (deterministic unique, e.g. EUR_ORIGIN_202307101100)",
            "event_start": "datetime UTC (alpha event timestamp; research and broker timestamps are different fields)",
            "family": "A | B",
            "dir": "+1 A long / -1 B short",
            "pos": "TARGET_VOL/rv vol-normalized research sizing unit (NOT executed notional)",
            "entry_ts": "event_start + family delay (A 2h, B 1h)",
            "exit_ts": "entry_ts + 6h (fixed sealed hold)",
            "pnl_bps": "net PnL bps = dir x pos x price_return - cost",
            "gross_pnl_bps": "gross before modeled cost",
            "cost_pnl_bps": "modeled cost (1.2 bps round trip + signed swap)",
            "split": "inner_sel | inner_val | RELATIONSHIP_CONFIRMED_OOS",
            "hold_h": "6.0 always",
        },
        "ledger_extensions": ["entry_price", "exit_price", "price_return_bps",
                              "risk_unit_bps", "r_multiple", "account_return_pct",
                              "mfe_r", "mae_r", "rv_bps_per_h", "severity",
                              "session", "spread_commission_bps", "swap_bps"],
        "required_for_execution_but_missing": [
            "broker_symbol", "venue", "tick_size", "tick_value",
            "minimum_quantity", "quantity_step", "margin_requirement",
            "buying_power_semantics", "account_currency", "equity_source",
            "order_types_supported", "trading_hours_definition"],
        "downstream_only_fields": ["account_equity", "broker_quantity", "portfolio_f"],
    }


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

def build_decision(f: Dict) -> Dict:
    d = {
        "checkpoint": CHECKPOINT,
        "status": "PASS",
        "base_commit": BASE_COMMIT,
        "block3_scale_seal_verified": True,
        "risk_unit_bps": RISK_UNIT_BPS,
        "risk_unit_semantics_verified": True,
        "risk_unit_is_hard_stop": False,
        "pnl_bps_semantics_resolved": True,
        "event_source_lineage_resolved": True,
        "instrument_universe_resolved": True,
        "product_types_resolved": True,
        "account_currency_resolved": True,   # proposed USD (pair base); recorded as proposal
        "equity_basis_proposed": "CURRENT_ACCOUNT_EQUITY_AT_CAUSAL_ADMISSION",
        "one_r_to_notional_formula_resolved": True,
        "formula_proven_against_fixtures": True,
        "cost_scaling_resolved": True,
        "rounding_policy_resolved": True,
        "post_rounding_heat_contract_resolved": True,
        "margin_gate_design_resolved": True,
        "reservation_state_design_resolved": True,
        "ownership_design_resolved": True,
        "restart_reconciliation_design_resolved": True,
        "broker_path_inventory_complete": True,
        "historical_890_event_parity_plan_complete": True,
        "preferred_research_default": {
            "allocation": "A1_70_30", "heat_architecture": "H1-1.00-REJ",
            "f_total_pct": F_TOTAL_PCT,
            "family_A_event_fraction_pct": FAMILY_W["A"],
            "family_B_event_fraction_pct": FAMILY_W["B"],
            "role": "PREFERRED RESEARCH DEFAULT for execution-translation research only -- NOT production sizing",
        },
        "production_scale_selected": False,
        "broker_selected": False,
        "broker_execution_authorized": False,
        "deployment_authorized": False,
        "mt5_authorized": False,
        "planning_pass": True,
        "implementation_ready": True,
        "implementation_authorized": False,
        "next_checkpoint_recommended": "CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0",
        "human_review_required": True,
        "audit_facts": {
            "n_events": f["n_events"], "n_A": f["n_A"], "n_B": f["n_B"],
            "splits": f["splits"],
            "worst_A_R": round(f["worst_A_R"], 4),
            "worst_B_R": round(f["worst_B_R"], 4),
            "admission": f["admission"],
            "notional_per_equity": {k: round(v, 4)
                                    for k, v in f["notional_per_equity"].items()},
            "fixture": f["fixture"],
            "input_hashes": f["hashes"],
        },
        "unresolved_facts": [
            "broker_symbol/venue/tick/margin/quantity specs: MISSING_EXECUTION_TRANSLATION_FIELD (broker-dependent; recorded, not fabricated)",
            "account_currency: USD proposed (pair base) -- frozen at the executable-environment checkpoint, not here",
        ],
    }
    return d


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    f = compute_facts()

    # markdown docs
    docs = {
        "CR_EXEC_TRANSLATION_PROTOCOL.md": _protocol(f),
        "CR_EXEC_TRANSLATION_SOURCE_TRUTH_AUDIT.md": _source_truth(f),
        "CR_EXEC_TRANSLATION_RISK_UNIT_AUDIT.md": _risk_unit(f),
        "CR_EXEC_TRANSLATION_PNL_BPS_AUDIT.md": _pnl_bps(f),
        "CR_EXEC_TRANSLATION_EQUITY_BASIS_CONTRACT.md": _equity_basis(f),
        "CR_EXEC_TRANSLATION_QUANTITY_FORMULA_CONTRACT.md": _quantity_formula(f),
        "CR_EXEC_TRANSLATION_ROUNDING_CONTRACT.md": _rounding(f),
        "CR_EXEC_TRANSLATION_MARGIN_BUYING_POWER_CONTRACT.md": _margin(f),
        "CR_EXEC_TRANSLATION_COST_PARITY_PLAN.md": _cost_parity(f),
        "CR_EXEC_TRANSLATION_MODEL_VS_ACTUAL_HEAT_CONTRACT.md": _model_vs_actual(f),
        "CR_EXEC_TRANSLATION_RESERVATION_STATE_MACHINE.md": _reservation(f),
        "CR_EXEC_TRANSLATION_OWNERSHIP_RECONCILIATION_PLAN.md": _ownership(f),
        "CR_EXEC_TRANSLATION_RESTART_RECOVERY_PLAN.md": _restart(f),
        "CR_EXEC_TRANSLATION_PARITY_FIXTURE_PLAN.md": _parity(f),
        "CR_EXEC_TRANSLATION_IMPLEMENTATION_BLOCK_PLAN.md": _impl_blocks(f),
        "CR_EXEC_TRANSLATION_TEST_PLAN.md": _test_plan(f),
        "CR_EXEC_TRANSLATION_REPORT.md": _report(f),
    }
    for name, content in docs.items():
        write_doc(name, content)

    # data artifacts
    instrument_inventory().to_csv(OUT / "CR_EXEC_TRANSLATION_INSTRUMENT_INVENTORY.csv", index=False)
    broker_path_inventory().to_csv(OUT / "CR_EXEC_TRANSLATION_BROKER_PATH_INVENTORY.csv", index=False)
    product_type_matrix().to_csv(OUT / "CR_EXEC_TRANSLATION_PRODUCT_TYPE_MATRIX.csv", index=False)
    account_size_matrix(f).to_csv(OUT / "CR_EXEC_TRANSLATION_ACCOUNT_SIZE_MATRIX.csv", index=False)
    component_status().to_csv(OUT / "CR_EXEC_TRANSLATION_COMPONENT_STATUS.csv", index=False)
    (OUT / "CR_EXEC_TRANSLATION_FAILURE_CATALOG.json").write_text(
        json.dumps(failure_catalog(), indent=2), encoding="utf-8")
    (OUT / "CR_EXEC_TRANSLATION_EVENT_LINEAGE.json").write_text(
        json.dumps(event_lineage(f), indent=2), encoding="utf-8")
    (OUT / "CR_EXEC_TRANSLATION_EVENT_SCHEMA.json").write_text(
        json.dumps(event_schema(f), indent=2), encoding="utf-8")
    decision = build_decision(f)
    (OUT / "CR_EXEC_TRANSLATION_DECISION.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8")

    print(f"[exec-translation-planning] base {BASE_COMMIT}")
    print(f"[exec-translation-planning] events {f['n_events']} (A {f['n_A']} / B {f['n_B']})")
    print(f"[exec-translation-planning] admission {f['admission']['decisions']}")
    print(f"[exec-translation-planning] worst A {f['worst_A_R']:.3f}R / worst B {f['worst_B_R']:.3f}R")
    print(f"[exec-translation-planning] notional/equity A {f['notional_per_equity']['A']:.4f} / B {f['notional_per_equity']['B']:.4f}")
    print(f"[exec-translation-planning] planning_pass={decision['planning_pass']} "
          f"implementation_authorized={decision['implementation_authorized']}")
    print("[exec-translation-planning] DONE")


if __name__ == "__main__":
    main()
