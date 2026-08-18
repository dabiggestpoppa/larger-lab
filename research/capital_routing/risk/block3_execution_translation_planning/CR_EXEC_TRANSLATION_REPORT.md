# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Report

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING
**Status:** PASS
**Base:** 40d237123ac2b709cc0ebce1d7f057bbfde25dab (sealed Block III, fail-closed gate PASS)

## 1. What is 1R?
1R = 24.4949 bps = TARGET_VOL x sqrt(6h) with TARGET_VOL = 10.0 bps/h.
A normalized expected-move unit -- NOT a stop (worst A -3.66R, worst B -3.31R).

## 2. How is pnl_bps constructed?
pnl_bps = dir x pos x ln(P_exit/P_entry) x 1e4 - cost, pos = TARGET_VOL/rv,
cost = 1.2 bps round-trip spread+commission + signed swap.  Fixture-verified
on the first sealed ledger event (r = -0.8568 reproduces exactly).

## 3. Dollar sensitivity of admitted_f
one_R_budget_usd = equity_at_admission x admitted_f_pct/100.  A 0.70 -> $70 per 1R at $10k;
B 0.30 -> $30.

## 4. Sensitivity -> notional
target_notional_usd = one_R_budget / (1R_bps/1e4) = E x f x 408.25.
Proven from the sealed account contract (account% = r x f); the research pos
is the R-normalization device, not the executed notional.

## 5. Notional -> broker quantity
Raw quantity = notional / contract units per lot; rounded toward LOWER
absolute exposure; broker symbol/spec are MISSING_EXECUTION_TRANSLATION_FIELD until a broker is chosen.

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
Golden admission fixture: 890 events, A 432 / B 458,
826 accepted (A 371 + B 455),
64 H1-rejected -- frozen as a regression fixture.

## 14. Reusable broker/execution path
NONE today: MT5 adapter is historical-data export only; OCE is a planning
shell; core/execution/journal.py is an agent journal (pattern reference);
no Alpaca/Nautilus/Robinhood/TB-forward engine exists in this checkout.  All
execution capability = new implementation (E0..E9 block plan).

## Leverage audit (descriptive, preferred research default, notional/equity)
A alone 2.86x; B alone 1.22x; A+B 4.08x;
B+B 2.45x; B+B+B 3.67x.  Descriptive only -- no
leverage cap imposed; broker/legal limits that contradict the translation are
recorded, never silently fixed by changing f_total.

## Historical loss translation (scenario, NOT maximum possible loss)
A worst -3.66R at 0.70 -> 2.56% of equity;
B worst -3.31R at 0.30 -> 0.99%;
-2R at A -> -1.40%; -2R at B -> -0.60%; -1R -> -0.70% (A) / -0.30% (B).

## Decision
planning_pass = true; implementation_ready = true; implementation_authorized
= FALSE; broker_selected / broker_execution_authorized / deployment_authorized
/ mt5_authorized = FALSE.  Next recommended checkpoint:
CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0 (NOT started).

**STOP for human review.**
