# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING — Progress

**Repo:** dabiggestpoppa/larger-lab · **Branch:** capital-routing
**Base:** `40d23712` (CR-RISK-BLOCK-III-SCALE-SEAL-R1-FAIL-CLOSED-GATE — fully sealed)
**Checkpoint:** `CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING`

## Status: COMPLETE ✅ (planning PASS, implementation NOT authorized)

## The 14 planning-gate questions — all answered with proof

1. **1R** = TARGET_VOL × √(6h) = 10 × √6 = **24.49489742783178 bps** — normalized
   expected-move unit, NOT a hard stop (worst A −3.66R, worst B −3.31R).
2. **pnl_bps** = dir × pos × ln(P_exit/P_entry)×1e4 − cost, pos = TARGET_VOL/rv,
   cost = 1.2 bps round-trip spread+commission + signed swap. Fixture-verified
   on every one of the 890 ledger rows (reconstruction test).
3. **admitted_f $ sensitivity** = one_R_budget_usd = equity_at_admission ×
   admitted_f_pct/100 (A 0.70% → $70/1R at $10k; B 0.30% → $30).
4. **1R → notional**: N = E × f / (1R_bps/1e4) = E × f × 408.248. Proven from the
   sealed account contract (account% = r × f); the research pos = 10/rv is the
   R-normalization device, NOT the executed notional.
5. **Notional → quantity**: raw quantity = notional ÷ contract units per lot;
   broker spec is MISSING_EXECUTION_TRANSLATION_FIELD (recorded, not fabricated).
6. **Rounding**: round toward LOWER absolute exposure; realized_f_pct recorded;
   overshoot → MIN_QUANTITY_RISK_OVERSHOOT.
7. **Margin vs buying power vs heat**: four separate gates; margin failure is a
   translation block, not strategy failure.
8. **H1 preserved**: MODEL_HEAT and REALIZED_TRANSLATED_HEAT both ≤ 1.00 f-unit;
   admission snapshots never revalued.
9. **Atomic reservation**: PROPOSED → ADMITTED_RESERVED → ORDER_SUBMITTED →
   FILLED_ACTIVE → EXIT_PENDING → CLOSED_RELEASED (+ explicit failure variants).
10. **Partial fills**: realized heat tracks actual filled quantity; no compensating
    quantity that would breach admission.
11. **Restart**: durable-ledger cold start with integrity verify, broker
    reconciliation, heat reconstruction, reservation restore; ambiguity → block.
12. **Foreign positions**: ownership_tag separates; never touched; consume
    margin/buying power.
13. **890-event parity**: golden admission fixture frozen (826 accepted: A 371 +
    B 455; 64 H1-rejected; requested_f A 0.70 / B 0.30).
14. **Reusable execution path**: NONE — MT5 adapter is data-export only, OCE is a
    planning shell, core/execution/journal.py is an agent journal, no
    Alpaca/Nautilus/Robinhood/TB-forward engine. All execution = new build (E0–E9).

## Key decisions
- equity_basis = CURRENT_ACCOUNT_EQUITY_AT_CAUSAL_ADMISSION (matches the
  multiplicative research model).
- account currency: USD proposed (pair base), frozen at the executable-
  environment checkpoint, not here.
- All broker-dependent fields recorded as MISSING_EXECUTION_TRANSLATION_FIELD.
- planning_pass=true, implementation_ready=true, **implementation_authorized=
  false**, broker/MT5/deployment authorization = false.
- Next recommended: CR-RISK-BLOCK-IV-EXECUTION-TRANSLATION-ENGINE-D0 (NOT started).

## Artifacts (research/capital_routing/risk/block3_execution_translation_planning/)
26 files: protocol, source-truth audit, event lineage + schema JSON, risk-unit +
pnl_bps audits, equity-basis / quantity-formula / rounding / margin / cost-parity /
model-vs-actual-heat / reservation / ownership / restart / parity / implementation-
block / test-plan docs, instrument + broker-path + product-type + account-size +
component-status CSVs, failure catalog JSON, report, decision JSON.

## Tests
16 new (`tests/test_exec_translation_planning.py`) — pnl_bps reconstruction over
ALL 890 rows, 1R definition, H1 admission reproduction (826/64), notional formula
fixtures, decision fields, no-fabrication checks · planning+seal suites 67/67 ·
determinism verified (byte-identical re-run).

## Scope honored
No orders, no broker, no live capability, no alpha/family/allocation/heat/f_total/
1R changes, no Kelly, no DD adaptation, no risk optimization, no production engine.
Stopped for human review.
