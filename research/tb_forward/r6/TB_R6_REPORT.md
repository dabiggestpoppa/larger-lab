# TB-R6-DEMO-EXECUTION-CANARY — Report

**Status: PARTIAL_PASS_WAITING_NATURAL_CANARY**
**Base: `9d0a3951413d153d494b8b1e81afcde5894cd40b` (R5.1)**

## Summary

R6 is the first order-submitting checkpoint. It ran against the real **Ox Securities MetaTrader 5 / OxSecurities-Demo** account (login `11***12`, USD) during an active FX session (Monday Asia, ~04:00 UTC). All **controlled broker-execution mechanics passed**: 5 complete three-leg demo baskets opened, verified, and atomically closed via real `order_send`, with broker truth (orders/deals/positions) recorded. No natural z2.5 canary signal occurred in the short observation window, so per the R6 status logic the checkpoint is **PARTIAL_PASS_WAITING_NATURAL_CANARY** — the execution infrastructure is proven; the natural-strategy lifecycle evidence remains pending.

## Environment

- Terminal: Ox Securities MetaTrader 5 — `OxSecurities-Demo` — DEMO (trade_mode 0) — USD
- Symbols: `GBPAUD.PRO` / `GBPNZD.PRO` / `AUDNZD.PRO`
- Identity gate: PASS (company/server/login/trade-mode/currency all verified before any send)
- Fixed basket notional: **$5,000 USD** (frozen; `BROKER_MINIMUM_EXECUTION_TEST` — smallest notional clearing all three volume minimums at 0.01/0.01/0.02 lots while keeping Gate K ≤ 10%)

## Phase A — Controlled demo execution harness (TB-DEMO-EXEC-TEST)

- **5/5 complete baskets** (`R6T010200`…`R6T050202`), each: 3 opens → OPEN verified → 3 closes → flat verified
- **36 real `order_send` calls** (30 in the 5-basket run + 6 in the restart-with-open-basket test), **all retcode 10009** (DONE), **0 rejected**
- 15 deal tickets + 15 position tickets captured per open side; 18 deals verified in final audit (`TB_R6_DEAL_LEDGER.csv`)
- Ownership: magic `31082027` + comment-tag `TB|<basket>|<symbol>|L<n>` linkage; `_verify_fills` polls until the basket's own tagged positions appear (fixed the stale-snapshot defect that could close the wrong basket under rapid succession)
- **Fill mode: PASS** — `order_check` probe resolved **FOK** as the working mode on all three symbols (declared bits 2/IOC, but IOC/RETURN probes → retcode 10030, FOK → 0); actual fills used FOK
- **Slippage: PASS** — per-leg −6.0 to +5.5 points (≤ 0.6 pips) vs signal reference
- **Three-leg latency: PASS** — leg1→leg3 total 71–85 ms across 5 baskets (mean ~75.6 ms)
- **Preflight gates: PASS** on all 5 baskets — quote age ≤ 1 s, cross-leg skew ≤ 1 s, max spread 12 pts, Gate K residual ≤ 10%

## Partial-fill / rollback

- Actual broker partial fill: **not observed** (broker filled 3/3 every time) — honestly classified `false`
- Recovery path: **validated** via deterministic broker-response injection against the real state machine: 2/3 → flatten → flat, 1/3 → flatten → flat, 0/3 → abort → flat; all safe, `aborted_flat`
- Rollback policy (BROKEN_HEDGE → flatten owned legs → verify flat): validated

## Restart / crash

- **Restart with open basket: PASS** — basket `R6R40529` opened in one process; a separate process reconstructed from ledger + broker truth (comment-tag linkage via `reconcile_open_baskets`), classified OPEN_VERIFIED, closed all 3 legs, verified flat
- Crash windows: covered by sealed R3/R4 deterministic suites (after intent / after leg1 / after leg2 / after leg3 before open claim / during close) + the real restart-with-open-basket test

## Safety

- Foreign positions modified: **0**
- Duplicate orders: **0**
- Primary (TB-FWD-V1) execution calls: **0** (shadow only)
- Control (TB-FROZEN-CONTROL) execution calls: **0** in R6 (natural canary observed; none fired)
- Order-send guard: all sends attributed to TB-DEMO-EXEC-TEST only

## Nonregression

- Historical parity: PRIMARY **194/194**, CONTROL **405/405**, lifecycle mismatches **0**, max z diff 1e-12 (265,809 bars)
- Failure injection: 8/8 safe classification
- Long-run: clean (50k bars, 451 events, 1 DB handle)
- Suites: R1.1 36/36 · R2 26/26 · R3 40/40 · P6 411/411 · P7 160/160
- Strategy science: **unchanged** (only mechanical execution-layer repairs: retcode-0 acceptance for real-broker `order_check`/`order_send`, 29-char comment bound, bounded basket tag, poll-for-own-positions fill verification)

## R6 mechanical defects found & repaired (adopted layer)

1. **Retcode mismatch** — the adopted layer only accepted `TRADE_RETCODE_DONE=10009`, but this broker returns `0` from `order_check` (and `10009` from `order_send`); accepted both.
2. **Comment-length limit** — this MT5 build returns `None` from `order_check` for comments > 29 chars; added a bounded basket tag (`TB|NNNNNNNNN|SYM|L#`) + fail-closed length check.
3. **Empty-varargs C-extension quirk** — calling the captured `order_send(req, *(), **{})` returns `None`; the guard wrapper now passes positionally only.
4. **Stale position snapshot under rapid baskets** — `_verify_fills` now polls until the basket's own comment-tagged positions appear, preventing wrong-basket closes.

## Caveats

- Natural canary window was short (~40 cycles, 2 healthy bars); 0 signals is expected at ~0.4 signals/day and does not fail R6 mechanics.
- Phase A ran in Asia-session liquidity (spreads 8–12 pts) — healthy, not the wide Sunday-rollover regime.
- PnL not evaluated (execution checkpoint; descriptive only).

## Next

**TB-R7-CANARY-DEMO-OPERATIONS-SEAL** — continue natural TB-FROZEN-CONTROL demo observation until ≥1 (target 10–20) natural baskets complete. R7 not auto-started; awaits human approval.
