# TB-R5.1 — Active-Market Shadow Completion Protocol

Checkpoint: `TB-R5.1-ACTIVE-MARKET-SHADOW-COMPLETION`
Base: `59a42cd64bb9e658b01b2313559609226f72485a` (R5)
Status: **PASS** (active-market evidence collected)

## Purpose

Complete the R5 shadow-forward seal with **active-market** evidence, which R5
could not provide (R5 ran on a closed-market Sunday and correctly fail-closed
on every cycle). R5.1 re-runs the identical R5 runtime during live FX hours and
requires:

- >= 20 unique advancing synchronized closed M5 bars
- live real ticks with updating spreads
- quote-age / cross-leg-skew measurement during active market
- broker metadata stability under live conditions
- restart / read-only reconciliation
- historical parity nonregression (265,809 bars; PRIMARY 194; CONTROL 405; 0 mismatches)
- `order_send` call count = 0

No strategy change. No order submission. Execution remains `NOT_AUTHORIZED`.

## FROZEN SCIENTIFIC CONTRACT (unchanged, re-affirmed)

| Item | Value |
|------|-------|
| Universe | GBPAUD, GBPNZD, AUDNZD |
| Broker symbols | GBPAUD.PRO, GBPNZD.PRO, AUDNZD.PRO |
| Basis | ln(GBPAUD) − ln(GBPNZD) + ln(AUDNZD) |
| Rolling z | previous 200 M5 bars, current excluded, population std (ddof=0) |
| PRIMARY entry | strict \|z\| > 3.0 (SHORT z>+3, LONG z<−3) |
| PRIMARY exit | SHORT z ≤ −0.25; LONG z ≥ +0.25 |
| STOP | canonical ±6 semantics (research parity) |
| CONTROL entry | strict \|z\| > 2.5, exit z=0 canonical (SHADOW ONLY) |
| Session | 03:00–12:00 fixed UTC−5, no DST |
| MIN exit age | 120 minutes |
| Max concurrent baskets | 1 |

## Method

1. Connect to the real MT5 terminal (Ox Securities MetaTrader 5, OxSecurities-Demo, USD, DEMO trade mode).
2. **Server-clock calibration** (new in R5.1): MT5 bar/tick epochs here are
   **server time = UTC+3**. The feed's closure/age math now calibrates its
   reference clock from live `symbol_info_tick().time` deltas instead of
   assuming the epochs are real UTC. The **strategy bar key remains the raw
   server-time M5 open time, verbatim** (R2 parity contract — never shifted).
   Without this, fresh bars would be rejected (or 3h-old bars accepted) during
   live operation.
3. Per-cycle: synchronized closed M5 snapshot → PRIMARY decision → CONTROL
   decision (independent) → real ticks with spread/age/skew → metadata
   stability hash → hypothetical lot translation with real broker specs (when a
   signal occurs) → write-ahead durable ledger → append cycle row to CSV →
   `order_send` guard armed.
4. `--restart-test`: fresh ledger on the same DB → integrity → reconstruct →
   real broker read → ownership classification → reconcile → resume gate.
5. Nonregression: R4 integrated replay (PRIMARY/CONTROL/failure-injection/
   long-run) + full suite battery (R1.1, R2, R3, P6, P7).

## Evidence standard

- **ACTIVE_MARKET_VERIFIED**: fresh M5 bar advancement + updating real ticks +
  non-static spread sample during market hours.
- Weekend/static data is never presented as active-market proof.
- Broker-execution classes (partial fill, fill mode, slippage, atomic close)
  remain `PENDING_DEMO_EXECUTION_VALIDATION` — not claimed in R5.1.

## Pass gate (all required)

1. real MT5 connected during active market — **PASS**
2. real symbols remain resolved — **PASS**
3. >= 20 unique advancing synchronized M5 bars — **PASS (21)**
4. closed-bar synchronization works — **PASS (all signal bars age 300–576 s, ≤ 1 M5 cycle)**
5. real ticks update — **PASS**
6. quote quality measured during active market — **PASS**
7. spread distribution measured during active market — **PASS**
8. cross-leg skew measured during active market — **PASS**
9. broker metadata stable — **PASS (static fields 0 variants / 40 re-reads)**
10. real lot translation valid — **PASS (194/194 GATE K, median residual 6.62%)**
11. durable ledger healthy — **PASS**
12. restart/reconcile works — **PASS (FLAT_MATCH)**
13. CONTROL isolated — **PASS (405 events, zero broker interaction)**
14. `order_send` calls = 0 — **PASS (0)**
15. historical parity 194/405 exact, 0 mismatches — **PASS**
16. strategy science unchanged — **PASS (UNCHANGED)**
17. active-market shadow runtime stable — **PASS (506 cycles, 0 health failures)**
18. broker-execution tests remain pending — **PASS (PENDING_DEMO_EXECUTION_VALIDATION)**
19. test suites pass — **PASS (see TB_R5_1_REPORT.md / TB_R5_1_COMPONENT_STATUS.json)**

## Result

`demo_execution_gate_ready = true` per the R5.1 definition (active-market
shadow seal complete). `demo_authorized` and `live_authorized` remain
**FALSE** — R6 requires separate human approval and would be the first
checkpoint allowed to submit orders (TB-FROZEN-CONTROL only, OxSecurities-Demo
only, TB-FWD-V1 shadow).
