# TB-R4 — REAL MT5 FULL-ENGINE SHADOW & FAILURE SEAL — REPORT

**Status: PASS** — base `4685d7f0` (R3) → this checkpoint.

## Headline

The complete TB forward engine was driven against the ACTUAL connected
MT5/OxSecurities terminal in SHADOW mode, and the full canonical history was
replayed through the integrated path (feed → wrapper → TB-B translation →
real atomic layer in simulation → R3 durable ledger → reconciliation).
Order submission stayed unreachable; historical parity stayed exact.

## Real-terminal evidence (read-only, nothing fabricated)

| Area | Measured |
|---|---|
| Terminal | Ox Securities MetaTrader 5, server `OxSecurities-Demo`, account DEMO, USD, leverage 500 |
| Symbols | `GBPAUD.PRO` / `GBPNZD.PRO` / `AUDNZD.PRO` — visible, FULL trade mode, 5 digits, point 1e-5, contract 100,000, vol 0.01/0.01/200, filling_mode 2 (IOC\|RETURN) |
| M5 bars | 200 bars per leg; **OPEN_TIME** timestamp semantics (R2 confirmed); latest three-leg common bar `2026-08-14 23:50` synchronized |
| Ticks | weekend closed-market sample captured (honest descriptive data; live-hours distribution pending) |
| Account state | 0 positions, 0 TB-magic positions, 0 pending orders; foreign (non-TB) history present and protected |
| Lot translation | 194/194 canonical shadow baskets pass GATE K with real specs/prices — median currency residual **6.61%** (frozen 10% gate) |
| Shadow loop | 10 cycles, all fail-closed `STALE_SIGNAL_BAR` (market closed); `order_send` attempts **0**; ledger clean |

## Integrated historical replay (scientific parity — exact)

- 265,809 bars emitted through the full integrated path
- **PRIMARY 194/194** — entry 0, direction 0, exit 0, exit-reason 0, weight 0 mismatches; max |z| diff 1e-12
- **CONTROL 405/405** — same, all 0
- Ledger: 194 baskets reconstructed from durable records alone, all terminal `CLOSED_VERIFIED`, integrity problems 0
- Full lifecycle: 194 opens + 194 closes, 388 executed results, 194 closed-verified
- Failure injection (leg1-reject → 2/3 partial): **8/8 signals classified safe** (BROKEN_HEDGE → mock flatten → flat), 0 unsafe states, 0 surviving OPEN_VERIFIED
- Long-run (50k bars): 451 ledger events, 50 opens, 1 DB handle, integrity clean, buffers bounded at 400

## Tests

| Suite | Result |
|---|---|
| TB-R1.1 | 36 collected / 36 passed / 0 failed / 0 skipped |
| TB-R2 | 26 / 26 / 0 / 0 |
| TB-R3 | 40 / 40 / 0 / 0 |
| TB-P6 | 411 / 411 / 0 / 0 |
| TB-P7 | 160 / 160 / 0 / 0 |
| TB-R4 integrated replay | primary + control + failure + long-run stages all PASS |
| TB-R4 real-MT5 audit | CONNECTED, 0 order_send, ledger clean |

## What was built

- `quant-lab/tb_live/full_engine.py` — `TBFullEngineHarness`: the complete
  integrated path (feed → engines → TB-B translation → real atomic layer in
  simulation → R3 ledger → reconciliation), deterministic, no MetaTrader5.
- `quant-lab/engines/tb_r4_replay.py` — 265,809-bar integrated replay with
  full-lifecycle comparison (entry/direction/exit/reason/weights all measured),
  ledger reconstruction, deterministic failure injection, long-run audit.
- `quant-lab/engines/tb_r4_real_mt5.py` — real-terminal audit + shadow loop
  with an `order_send` guard that fails the run on any attempt.
- `quant-lab/tb_live/snapshot.py` — numpy structured-array support for real
  MT5 `copy_rates` (dict-shaped mocks still supported).
- 21 artifacts under `research/tb_forward/`.

## Honest disclosures

1. **Weekend evidence.** All real-terminal shadow cycles failed closed
   (`STALE_SIGNAL_BAR`) because the market was closed — the correct safe
   behavior. No real trading signal occurred during the sample; R4 proves
   plumbing, not signal frequency.
2. **Tick/spread/skew distributions** are a static closed-market sample.
   Live-market distributions are `PENDING_TERMINAL_VALIDATION` during active
   hours.
3. **CLASS-B broker execution behavior** (partial fills, fill modes, slippage,
   atomic close) is **CODE-PATH VERIFIED** in simulation only and marked
   `PENDING_DEMO_EXECUTION_VALIDATION`. Not claimed broker-proven.
4. **exec-sim prior art.** `tb_live_exec_sim.py` fails at the R3 base
   (`ExposureSummary` attribute rename from an older refactor) — pre-existing,
   untouched, not part of the R4 seal; the R4 harness supersedes it.
5. **Snapshot adapter change** is mechanical (numpy records); R2 26/26 and the
   exact 194/405 integrated parity prove zero strategy drift.

## Authorization state

- EXECUTION AUTHORIZATION: **NOT_AUTHORIZED** · DEMO: **FALSE** · LIVE: **FALSE**
- REAL ORDER_SEND CALLS: **0** · SHADOW FORWARD SEAL READY: **TRUE**
- SCIENTIFIC CHANGES: **NONE**

## Next recommended checkpoint

**TB-R5-SHADOW-FORWARD-SEAL** — freeze engine/config/logging/IDs, verify
continuous SHADOW run, define the forward review protocol (10/25/50/100
signals), prepare the demo gate. Do not authorize demo/live.
