# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 -- Report

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1-POSITION-SCALING-ACCOUNT-BOUNDARY-TRUTH-REPAIR
**Status:** PASS
**Base:** 5a79bf2323ac2657de74e3efa7c4a29d8715db33 · **Parent seal:** 40d237123ac2b709cc0ebce1d7f057bbfde25dab (science UNCHANGED)

## The blocking error is repaired
Old formula (no pos) max gross error 0.044900 ->
REJECTED. Corrected formula N = E x f x pos x 1e4/RISK: gross parity max error
6.94e-18 over all 826 accepted events
(machine precision). One-R price move is event-specific: RISK/pos, median
22.11 bps, range
1.35-221.91 bps.

## Units repaired
Account impact % = r x admitted_f_pct (signed): A worst -2.5588%,
B worst -0.9939% (renamed
historical_worst_observed_account_impact_pct; never maximum possible loss).
Pip semantics: one-R pip move is event-specific (raw_quote_move = P x bps/1e4;
pip_move = raw_quote_move/0.01).

## Parity
- Gross: PASS (all accepted events, machine precision).
- Net (research-modeled cost): PASS (max err 6.94e-18).
- Net (execution): BROKER_DEPENDENT_UNRESOLVED (broker cost not frozen).
- H1: 826 ACCEPT_FULL (A 371 / B 455),
  64 REJECT_HEAT_CAP -> ZERO target exposure (verified).
- requested_f A 0.70 / B 0.30; model heat stays in f-space.

## Corrected notional multipliers (equity-normalized, accepted)
Pooled median 1.984x, p95
7.61x, max
32.77x. No clipping (new
science); extreme states flagged for feasibility study.

## Account/product truth
research_reporting_currency USD (RESOLVED) vs executable_account_currency
UNRESOLVED_UNTIL_ACCOUNT_BINDING. research_instrument USDJPY/FX_PAIR vs broker
product/symbol/margin UNRESOLVED until account binding.

## Boundaries
Account Control Plane boundary explicit; Capital Routing owns only capital
translation (A/B, H1, f, pos, target exposure, request schema, parity);
generic execution (registry, sessions, orders, reconciliation, supervisor,
secrets, MT5/TradeLocker) belongs to execution-runtime-foundation. TB Forward =
PROVEN ENGINEERING REFERENCE (read-only, HEAD d1200598, authority
df5f349e ancestor). No cross-branch writes. No broker calls.

## Decision
gross_890_translation_parity_pass = true; h1_parity_pass = true;
implementation_ready = true (repair proven); implementation_authorized = false;
production_authorized = false; broker_execution_performed = false.
Next (NOT started): CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.
