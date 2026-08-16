# TB-R5 — SHADOW FORWARD SEAL (PROTOCOL)

**Checkpoint:** `TB-R5-SHADOW-FORWARD-SEAL`
**Base:** `fb8d25e4f61dc6e863ddbe04e3b9ba5ddaeb610a` (R4)
**Status:** BLOCKED — active-market evidence pending (all other gates pass)

## 1. Purpose

Freeze and observe the COMPLETE forward engine during ACTIVE-MARKET
conditions in SHADOW mode. R5 is infrastructure observation — not strategy
research, not a backtest, not a demo-execution gate.

## 2. Hard requirement: active market

R5 must be run while the FX market is OPEN. A weekend-only or stale-bar-only
run is NOT complete R5 evidence (it only proves fail-closed handling).

Required live observations during market hours:

- fresh closed M5 bars advance over time
- fresh real ticks update (non-static tick times)
- cross-leg timestamp synchronization holds
- spread / quote-age / cross-leg-skew distributions are measured
- shadow loop cycles run with valid synchronized snapshots

## 3. Runtime

`quant-lab/engines/tb_r5_shadow.py` — continuous SHADOW runtime:

```
CONNECT -> resolve/lock real symbols -> metadata baseline hash
loop (each cycle):
  ref = now
  synchronized closed M5 snapshot (R2 feed; forming bar excluded)
  PRIMARY TB-FWD-V1 + CONTROL TB-FROZEN-CONTROL process_snapshot
  real ticks: bid/ask, spread, quote age, cross-leg skew
  metadata hash re-check (drift -> METADATA_DRIFT_BLOCKED)
  if PRIMARY intent: TB-B weights -> real specs -> hypothetical lots
                     -> GATE K neutrality -> durable intent (write-ahead)
                     -> SHADOW_ORDER_WOULD_SEND  (no order_send)
  append cycle row to TB_R5_ACTIVE_MARKET_RUNTIME.csv (append-only)
  ledger event + health state
  sleep
```

Run command (active market, e.g. ~2h London session):

```bash
python quant-lab/engines/tb_r5_shadow.py --cycles 480 --cycle-sleep 15
```

The CSV appends across restarts, so observation can be resumed safely.

## 4. Authorization

| Capability | Status |
|---|---|
| MT5 read / market data / metadata | AUTHORIZED |
| Positions / orders / deals read | AUTHORIZED (read-only) |
| Shadow loop | AUTHORIZED |
| `mt5.order_send` | NOT AUTHORIZED (hard guard; any call fails R5) |
| Demo / live execution | NOT AUTHORIZED |

## 5. Evidence standard

- `ACTIVE_MARKET_VERIFIED`: fresh bars advanced, ticks updated, sync held,
  distributions measured during market hours.
- `PENDING`: weekend/closed-market sample only (current state).
- `FAIL`: something broke.

Weekend data must never be presented as active-market behavior.

## 6. Restart / reconciliation

Controlled restarts during the run: integrity → reconstruct → real broker
read → ownership classification → reconcile → resume only if safe. Deeper
lifecycle states use deterministic R3/R4 replay (never fabricated live state).

## 7. Demo readiness

R5 does NOT test broker execution. The four broker-execution validations
(partial fill, fill mode, slippage, atomic close) remain
`PENDING_DEMO_EXECUTION_VALIDATION` — acceptable for R5. Demo execution is a
separate, human-authorized checkpoint (R6).

## 8. Completion procedure (to lift BLOCKED)

1. Run the runtime during market hours (London session recommended):
   ```bash
   python quant-lab/engines/tb_r5_shadow.py --cycles 480 --cycle-sleep 15
   ```
2. Confirm CSV rows show `three_leg_sync=True`, fresh bar keys advancing,
   non-static tick times, healthy cycles.
3. Regenerate the distribution CSVs from the CSV rows.
4. Re-run `--restart-test`.
5. Update the decision artifact: `active_market_verified=true`, status PASS.
6. Human review → R6 (demo execution validation) requires separate approval.
