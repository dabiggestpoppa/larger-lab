# TB-R4 — REAL MT5 FULL-ENGINE SHADOW & FAILURE SEAL (PROTOCOL)

**Checkpoint:** `TB-R4-REAL-MT5-FULL-ENGINE-SHADOW-SEAL`
**Base:** `4685d7f0ec66d64d3e44739b5aee650b2e803604` (R3)
**Status:** PASS

## 1. Purpose

Prove the COMPLETE TB forward engine against the ACTUAL connected
MT5/OxSecurities environment in SHADOW mode. The science is not under study.
This checkpoint is system reliability: real broker truth for data/metadata/
state, with order submission permanently unreachable.

## 2. Real-MT5 principle

The real terminal is the authoritative broker/data interface:

- terminal connectivity, account identity, server/broker name
- symbol existence, suffix resolution, `symbol_select`, contract metadata
- M5 bars, bar timestamps, bid/ask ticks, tick timestamps
- current positions, pending orders, historical orders/deals, magic visibility

Nothing is fabricated. If MT5 is unavailable the broker-specific sections are
recorded `PENDING_TERMINAL_VALIDATION` and are never declared PASS from mocks.

## 3. Authorization split (frozen for this checkpoint)

| Capability | Authorization |
|---|---|
| MT5 connectivity / market data / metadata | **AUTHORIZED (read)** |
| Positions / orders / deals reconciliation | **AUTHORIZED (read-only)** |
| Shadow loop (intents persisted, no execution) | **AUTHORIZED** |
| `mt5.order_send` | **NOT AUTHORIZED** |
| Demo order submission | **NOT AUTHORIZED** |
| Live order submission | **NOT AUTHORIZED** |

`order_send` is wrapped by a guard that FAILS the run if ever invoked.

## 4. Shadow loop sequence

```
CONNECT
 -> resolve real broker symbols (explicit, locked)
 -> audit environment / symbol specs / account state (read-only)
 -> fetch synchronized closed M5 bars (R2 feed; forming bar excluded)
 -> validate signal snapshot (fail closed)
 -> PRIMARY TB-FWD-V1 process_snapshot
 -> CONTROL TB-FROZEN-CONTROL process_snapshot (isolated shadow)
 -> if PRIMARY intent:
      fetch fresh real ticks -> age/skew/spread gates
      translate TB-B weights with REAL contract specs -> hypothetical lots
      neutrality re-check (frozen GATE K)
      persist intent to R3 ledger (write-ahead)
      record SHADOW_ORDER_WOULD_SEND
      DO NOT CALL order_send
 -> log health state -> sleep -> next cycle
```

Signal generation remains closed-M5-bar based. Ticks are execution pricing/
freshness only — never alpha.

## 5. Failure classes

- **CLASS A (tested against the real terminal, safely):** disconnect handling,
  missing/stale data, no tick, market closed, foreign position, wrong local
  state, ledger corruption, restart, duplicate signal/event, clock issues,
  symbol metadata. These are exercised with real terminal truth plus the
  deterministic replay/injection suites.
- **CLASS B (requires actual order execution):** leg1-rejects-but-leg2-fills,
  partial broker fills, slippage after `order_send`, fill-mode broker
  rejection, crash after a real accepted order, partial real close.
  These are **NOT** claimed as broker-validated in R4. They are marked
  `PENDING_DEMO_EXECUTION_VALIDATION` and will be validated only when DEMO
  execution is separately authorized. The deterministic code paths are
  verified in simulation (0/3, 1/3, 2/3, 3/3) and the report distinguishes
  CODE-PATH VERIFIED from BROKER-VERIFIED.

## 6. Historical replay (scientific parity — kept)

The canonical 265,809-bar M5 dataset is replayed through the COMPLETE
integrated path (R2 feed -> wrapper -> TB-B translation -> atomic layer in
simulation -> R3 ledger -> reconciliation) and must stay at

- PRIMARY 194 events, CONTROL 405 events, 0 lifecycle mismatches
  (entry / direction / exit / exit reason / weights measured individually)
- max |z| difference ~1e-12

Replay is the canonical strategy regression test, not a mock broker.

## 7. Component truth chain

```
TB-B model weight
 -> scientific relative notional
 -> currency-neutral execution contract (frozen conversion rates)
 -> REAL broker notional (contract size, quote-ccy conversion)
 -> MT5 lots (volume_min/step rounding)
 -> post-rounding neutrality re-check (GATE K)
```

MODEL WEIGHT != LOT SIZE.

## 8. Pass gate (summary)

1-13: real terminal connected, OxSecurities environment identified, symbols
resolved, specs captured, real M5 consumed, forming bar excluded, 3-leg sync
works, real ticks captured, spread/age/skew measured, real-spec lot
translation passes GATE K, R3 ledger works against real terminal state,
read-only reconciliation, foreign/manual positions protected.
14-20: historical parity exact (194/405), CONTROL isolated, restart works,
`order_send` call count = 0, strategy science unchanged, destructive
broker-execution tests deferred to DEMO, all suites pass.

## 9. Artifacts

See `TB_R4_REAL_MT5_ENVIRONMENT_AUDIT.json`, `TB_R4_REAL_SYMBOL_SPEC_AUDIT.json`,
`TB_R4_REAL_MARKET_DATA_AUDIT.json`, `TB_R4_REAL_TICK_QUALITY.csv`,
`TB_R4_REAL_SPREAD_DISTRIBUTION.csv`, `TB_R4_REAL_CROSS_LEG_SKEW.csv`,
`TB_R4_REAL_LOT_TRANSLATION.csv`, `TB_R4_REAL_ACCOUNT_RECONCILIATION.json`,
`TB_R4_SHADOW_LOOP_AUDIT.json`, `TB_R4_HISTORICAL_PARITY.json`,
`TB_R4_FAILURE_INJECTION_AUDIT.json`, `TB_R4_FULL_LIFECYCLE_AUDIT.json`,
`TB_R4_LONG_RUN_AUDIT.json`, `TB_R4_RESTART_STATE_MATRIX.csv`,
`TB_R4_LEDGER_RECONSTRUCTION_AUDIT.json`, `TB_R4_CONTROL_ISOLATION_AUDIT.json`,
`TB_R4_ORDER_SEND_GUARD.json`, `TB_R4_PENDING_DEMO_EXECUTION_TESTS.json`,
`TB_R4_INPUT_HASH_MANIFEST.json`, `TB_R4_COMPONENT_STATUS.json`,
`TB_R4_REPORT.md`, `TB_R4_DECISION.json`.
