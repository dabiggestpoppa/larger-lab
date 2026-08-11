# TB-LIVE-EXEC-SEAL-03B — REAL-BROKER EXECUTION SEAL REPORT

- **Timestamp (UTC):** 2026-08-10T04:15:07.740827
- **Account:** 1114712 OxSecurities-Demo (balance $281.28, leverage 500)
- **Conversion rates (live):** GBPUSD=1.34852 AUDUSD=0.70583 NZDUSD=0.58844

**All results computed against the ACTUAL MT5 demo broker — no FakeBroker, no mock data, no hardcoded contract/conversion values.**

Pipeline: model_weight -> weight_share -> USD notional -> raw lots -> rounded lots -> real base/quote units -> actual currency exposure -> residual hedge error (GATE K). Canonical inverse-ATR weights preserved.

## Key Finding: Canonical Weights Are Not FX-Neutral

The seal reveals a **material, structural property** of the canonical Triangular Basis strategy: the inverse-ATR normalized weights (from the 405-trade backtest) produce a **real currency residual** when sized to real broker contracts. This is not a bug in the execution layer — it is an intrinsic property of the weight vector itself. At the minimum-viable notional ($25,000) the median basket shows 34.9% max currency residual, meaning the strategy as sized leaves a significant net exposure to GBP, AUD, or NZD. This residual must be managed via the configured threshold (GATE K) or addressed via position-level hedging.

## Final Execution Gates

| Gate | Requirement | Pass |
|------|-------------|------|
| D | foreign strategy untouched | PASS |
| E | partial basket recovers flat/halt | PASS |
| F | restart cannot duplicate | PASS |
| I | PLACED-only cannot OPEN | PASS |
| J | weights translate deterministically | PASS |
| K | TRUE currency residual inside threshold | FAIL |
| L | CLOSED only after broker confirms flat | PASS |
| M | all 3 order_check before first send | PASS |

## Minimum Viable Demo Notional

**demo_basket_notional_usd = $25,000**

Margin accessibility: {"balance": 281.28, "leverage": 500, "est_basket_margin_usd": null, "affordable": false}

## Notes

- M gate: REAL mt5.order_check() preflight on all 3 legs; no order_send.
- D/F gates: REAL mt5.positions_get()/orders_get() broker truth on a live (closed-state) account; restart recovery results in restart_execution_tests.json and foreign_restart_isolation.json.
- I and L are retained from the EXEC-03 execution layer (PLACED != FILLED; CLOSED only after flat verification).
- This run placed NO demo orders (shadow-safe).
