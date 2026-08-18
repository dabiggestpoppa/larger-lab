# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1 — Progress
# POSITION-SCALING + ACCOUNT-BOUNDARY TRUTH REPAIR

**Repo:** dabiggestpoppa/larger-lab · **Branch:** capital-routing
**Base:** `5a79bf23` (planning — MOSTLY COMPLETE, NOT implementation-safe)
**Parent seal:** `40d23712` (Block III scale science — UNCHANGED)

## Status: COMPLETE ✅ (PASS — blocking error repaired, no broker execution)

## The blocking defect, confirmed independently
The prior planning formula `N = E × f × 1e4/RISK` omitted the event position
term `pos_t`. The sealed construction (phase_r1_ledger.py) is
`gross_pnl_bps = dir × pos_t × price_return_bps` with `pos_t = TARGET_VOL/rv_t`.
**Corrected formula (proven at machine precision over all 890 events):**
`N_t = Equity_t × admitted_f_decimal × pos_t × 10,000 / RISK_UNIT_BPS`.
Gross parity max error = **6.9e-18**; old formula max error = **0.0449** (rejected).
One-R underlying price move is **event-specific**: `RISK/pos` — median 22.1 bps,
range 1.35–221.9 bps (the old "always 24.4949 bps" statement is removed).

## Other repairs
- **Account-impact units**: % = r × admitted_f_pct (signed). A worst
  **−2.5588%**, B worst **−0.9939%** (old matrix reported 255.88/99.39 — 100× off).
- **Pip semantics**: one-R pip move event-specific; `raw_quote_move = P×bps/1e4`,
  `pip_move = raw_quote_move/0.01` (fixtures across pos).
- **Account currency**: research_reporting_currency = USD (RESOLVED) vs
  executable_account_currency = UNRESOLVED_UNTIL_ACCOUNT_BINDING.
- **Product identity**: research_instrument USDJPY/FX_PAIR vs broker
  product/symbol/margin UNRESOLVED.
- **Cost scaling**: cost_pnl_bps = cost_bps × pos_t (per-position-unit), NOT a
  flat 1.2 bps on raw notional; research-modeled net parity proven (6.9e-18);
  execution-level net parity BROKER_DEPENDENT_UNRESOLVED.

## Parity (all 890 events)
- GROSS: PASS (826 accepted at machine precision) · NET (research cost): PASS ·
  H1: 826 ACCEPT_FULL (A 371 / B 455), 64 REJECT → **zero exposure** (verified).
- Corrected notional/equity (accepted): median 2.29×, p95 8.77×, p99 12.9×,
  max 32.77× (A) / 22.28× (B). **NO clipping** (new science); extreme states
  flagged for a future feasibility study.

## Account Control Plane boundary (frozen)
Capital Routing owns ONLY: A/B allocation, H1, f semantics, event pos/1R truth,
target exposure, translation request schema, model heat, parity fixtures.
Generic execution (AccountRegistry, BrokerSession, orders/fills, reconciliation,
supervisor, secrets, MT5/TradeLocker) belongs to **execution-runtime-foundation**
(branch audited read-only, HEAD df5f349e). **Portfolio Master requirement**:
A+B bound to ONE shared H1 ledger (splitting across independent accounts would
change portfolio science). TB Forward = **PROVEN ENGINEERING REFERENCE** (read-only,
HEAD d1200598, authority df5f349e ancestor); no TB code imported.

## Artifacts (research/capital_routing/risk/block3_execution_translation_planning_r1/)
23 files: protocol, defect audit, position-scaling derivation, position
distribution + one-R price-move fixtures + event notional multipliers + account
size matrix + account impact repair CSVs, account currency + product identity +
cost scaling + account control plane docs, gross/net/H1 parity JSONs (per-event),
cross-branch inventory, handoff + translation request schemas, component status,
test audit, report, decision.

## Tests
31 new (`tests/test_exec_translation_planning_r1.py`) covering the 28 required
checks (1R unchanged, pos/gross reconstruction all 890, corrected notional
includes pos, removing pos breaks parity, event-specific one-R moves, pip
fixtures, impact units, 826/64 + zero exposure, gross parity every accepted
event, long/short parity, low/high-pos fixtures, currency/product truth, no
broker calls, no TB import, schemas) · 47/47 planning+R1 · determinism verified.

## Scope honored
No alpha/allocation/H1/f_total/1R/cost/entry-exit change, no clipping, no Kelly,
no DD adaptation, no broker execution, no cross-branch writes.
**STOP for human review.** Next (NOT started):
CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.
