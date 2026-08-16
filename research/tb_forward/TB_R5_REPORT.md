# TB-R5 — SHADOW FORWARD SEAL — REPORT

**Status: BLOCKED (active-market evidence pending).** All non-active-market
gates pass; the seal cannot be declared PASS on weekend data.

## Why BLOCKED, honestly

The checkpoint ran at **Sunday ~16:5x UTC** — FX market closed. The R5 pass
gate requires, at minimum, fresh M5 bar advancement and updating real ticks
during market hours. The runtime behaved exactly as designed (every cycle
fail-closed `STALE_SIGNAL_BAR`), which proves fail-closed handling but not
continuous active-market operation. Per the evidence standard, weekend data is
not presented as active-market behavior.

## What was built

`quant-lab/engines/tb_r5_shadow.py` — the continuous SHADOW forward runtime:

- real MT5 connect + symbol resolution (GBPAUD.PRO / GBPNZD.PRO / AUDNZD.PRO)
- per-cycle synchronized closed-M5 snapshot via the R2 feed
- PRIMARY TB-FWD-V1 + CONTROL TB-FROZEN-CONTROL evaluation (sealed engines)
- real bid/ask ticks: spread, quote age, cross-leg skew per cycle
- **broker metadata stability**: per-cycle hash of digits/point/tick size/
  tick value/contract size/volume min-max-step/trade mode/filling mode;
  drift → `METADATA_DRIFT_BLOCKED`
- shadow order intent: TB-B weights → real specs → hypothetical lots →
  GATE K neutrality → durable write-ahead intent → `SHADOW_ORDER_WOULD_SEND`
- append-only cycle log (TB_R5_ACTIVE_MARKET_RUNTIME.csv, restart-safe)
- `order_send` hard guard (any call fails the run)
- `--restart-test`: integrity → reconstruct → real broker read → reconcile
- `--offline`: honest PENDING shell, never PASS

## Real-terminal evidence (weekend, read-only)

- Terminal: Ox Securities MT5 / OxSecurities-Demo / DEMO / USD
- Symbols resolved and metadata hash-stable across all 12 cycles
  (baseline `8c82667a5c71b167`, no drift)
- Account: 0 positions, 0 pending orders, 0 TB-magic history in last 7d;
  foreign history (2 orders / 3 deals) protected
- Runtime: 12 cycles, 0 valid snapshots (market closed), 0 order_send
  attempts, ledger clean
- Restart test: PASS — fresh ledger object, integrity clean, FLAT_MATCH,
  resume allowed

## Historical nonregression (PASS)

| Gate | Result |
|---|---|
| Integrated replay bars | 265,809 |
| PRIMARY | 194/194, 0 mismatches (all 5 classes measured), max z 1e-12 |
| CONTROL | 405/405, 0 mismatches, max z 1e-12 |
| Failure injection | 8/8 safe |
| Long-run | 50k bars, integrity clean, 1 DB handle |
| TB-R1.1 | 36/36 |
| TB-R2 | 26/26 |
| TB-R3 | 40/40 |
| TB-P6 | 411/411 |
| TB-P7 | 160/160 |

## Authorization state

- EXECUTION AUTHORIZATION: **NOT_AUTHORIZED** · DEMO: **FALSE** · LIVE: **FALSE**
- ORDER_SEND CALLS: **0** · STRATEGY SCIENCE: **UNCHANGED**
- Broker-execution validations: all four **PENDING_DEMO_EXECUTION_VALIDATION**

## To lift BLOCKED (active-market seal)

Run during market hours (London session recommended):

```bash
python quant-lab/engines/tb_r5_shadow.py --cycles 480 --cycle-sleep 15
python quant-lab/engines/tb_r5_shadow.py --restart-test
```

Confirm CSV rows with `three_leg_sync=True`, advancing bar keys, non-static
tick times, then regenerate the distribution CSVs and flip
`active_market_verified=true` in TB_R5_DECISION.json. Human review → R6 (demo
execution validation) requires a separate explicit authorization.
