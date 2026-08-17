# TB-R5.1 — Active-Market Shadow Completion — REPORT

Checkpoint: `TB-R5.1-ACTIVE-MARKET-SHADOW-COMPLETION`
Base: `59a42cd64bb9e658b01b2313559609226f72485a` (R5)
Status: **PASS** — active-market evidence complete

## Headline

The R5 shadow runtime was run during **live FX market hours** (Sunday rollover
into the new week, 21:41–23:20 UTC). The market was genuinely active: 21 unique
**advancing** synchronized closed M5 bars, real ticks updating continuously
(quote age p50 **0 ms**, p99 **19 s**), live spreads, cross-leg skew p50 **2 ms**
(p99 14 ms). Every gate in the R5 pass list now has active-market evidence.
`order_send` calls: **0**. Historical parity remains exact: **194/194 primary,
405/405 control, 0 lifecycle mismatches**.

## Why R5 was BLOCKED and R5.1 lifts it

R5 ran on a closed-market Sunday: all 16 cycles fail-closed with
`STALE_SIGNAL_BAR` — correct but not active-market proof. R5.1 waited for the
market to open and re-ran the identical runtime. The R5 evidence standard is
satisfied: fresh bar advancement, updating ticks, non-static spreads, live
cross-leg sync.

## Mechanical change introduced in R5.1 (the one real find)

**Server-clock calibration.** This broker's MT5 epochs are **server time =
UTC+3**, while the R2 adapter assumed epochs were real UTC. Without
calibration, a live engine would reject fresh bars (or accept 3-hour-old bars
as fresh) — exactly the class of defect this deployment phase exists to catch.
The fix:

- The feed's **closure/age math** now calibrates its reference clock from live
  `symbol_info_tick().time` deltas (tick-clock delta measured each cycle;
  observed server offset ~10,770 s ≈ 3 h, drifting +28 s over 99 min).
- The **strategy bar key remains the raw server-time M5 open time, verbatim**
  (R2 parity contract — never shifted).
- `snapshot.py` also now accepts numpy structured arrays (real MT5 output) in
  addition to dict-shaped mocks.

Both changes are **MECHANICAL**: R2 suite 26/26 and the full 265,809-bar
replay (194/194 + 405/405, max z diff 1e-12) are unchanged.

## Active-market evidence

| Metric | Value |
|--------|-------|
| Window (UTC) | 2026-08-16 21:41 → 23:20 (~99 min) |
| Cycles | 506 |
| Unique advancing synchronized M5 bars | **21** (≥ 20 required) |
| Signal-bar age | 300–576 s (all ≤ 1 M5 cycle after close) |
| Quote age | p50 0 ms · p90 5 s · p95 9 s · p99 19 s · max 39 s |
| Spread (points) | GA p50 12 / p99 287 · GN p50 16 / p99 521 · AN p50 10 / p99 309 (Sunday rollover liquidity — wide tails expected) |
| Cross-leg skew | p50 2 ms · p95 13 ms · p99 14 ms |
| Bar sync rate | 35/506 healthy (6.9%), remainder dedup no-ops — correct |
| Metadata | static fields 0 variants over 40 re-reads / 234 s |
| Reconciliation | FLAT_MATCH across all 506 cycles |
| order_send | **0 calls** |

No z-threshold breach occurred during the window (primary and control signals
observed: 0). That is expected and acceptable — R5.1 proves continuous
plumbing, and signal lifecycle is covered by the 194/405 historical replay.

## Nonregression

- Integrated replay: **265,809 bars** · PRIMARY **194/194** · CONTROL **405/405**
  · all five mismatch classes (entry/direction/exit/reason/weight) **0**
  · max z diff **1e-12**
- Failure injection: **8/8** signals safe under deterministic leg1-reject
  (2/3 partial → BROKEN_HEDGE → mock flatten; 0 unsafe states)
- Long-run: 50k bars, 451 ledger events, 1 DB handle, integrity clean
- Suite battery: R1.1 **36/36** · R2 **26/26** · R3 **40/40** · P6 **411/411**
  · P7 **160/160**

## Honest disclosures

1. The observation window was Sunday rollover — spreads show wide tails
   (p99 287–521 points vs p50 10–16). That is real active-market data, but a
   weekday London-session sample would tighten the distributions. Not a
   blocker: the requirement was active-market measurement, which is satisfied.
2. No live signal occurred, so no live shadow order intent was exercised
   end-to-end in the active window. The intent path is proven by the
   194/194 historical replay through the full engine + real lot translation
   (194/194 GATE K, median residual 6.62%).
3. Broker-execution classes (partial fill, fill mode, slippage, atomic close)
   remain `PENDING_DEMO_EXECUTION_VALIDATION` — not claimed here.

## Decision

`demo_execution_gate_ready = true`. `demo_authorized` and `live_authorized`
remain **FALSE**.

**Next recommended checkpoint:** `TB-R6-DEMO-EXECUTION-CANARY` — the first
order-submitting checkpoint. It must NOT auto-start; it requires separate
human authorization, runs on the OxSecurities-Demo environment only, executes
**TB-FROZEN-CONTROL** (z2.5/z0 canary) with **TB-FWD-V1 shadow-only**, and
uses a conservative fixed basket notional.
