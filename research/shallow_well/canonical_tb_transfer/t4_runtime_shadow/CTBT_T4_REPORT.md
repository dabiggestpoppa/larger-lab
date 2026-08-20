# CTBT T4 — Transfer-Family Runtime Shadow Integration Report

**Checkpoint:** `SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION`
**Base:** `44379e416c1c49dd055f0d818f10bafccefec131` (T3)
**Activation commit:** `cbb916d345bf5f845c4c1cf48212dab9ff3a946b`
**Status:** **PASS_FORWARD_SHADOW_ACTIVE**

---

## 1. What was built

A **read-only forward-shadow runtime** (`ctbt_runtime/`) integrating the two
sealed transfer candidates into the existing provider-neutral execution
environment. It is the official transition out of the historical lab:

```
provider market data → completed M5 bars → FrozenTransferStrategyAdapter →
sealed strategy logic → shadow event ledger → independent replay audit
```

Components (all tested):
- `read_only_proxy.py` — fail-closed MT5 facade: a strict read-only allowlist;
  every order/position/history/deal/write capability is unreachable by
  construction (5/5 order-prevention tests pass, static + dynamic).
- `data_feed.py` — synchronized 3-leg M5 feed (all legs share the exact same
  closed M5 timestamp; forming bars never evaluated), UTC-normalized,
  patterned on the canonical TB feed.
- `sealed_engine.py` — loads each T3 candidate seal, **verifies its sha256
  hash at load**, and runs the exact T1.1 lifecycle primitives
  (405/405 + 194/194 verified). **Parity test:** fed the same 2025 bars as
  T2, the runtime reproduces the T2 event ledger exactly — 146 + 81 events,
  identical entry/exit timestamps, directions, exit reasons, and gross bps.
  The runtime path IS the research engine.
- `shadow_ledger.py` — append-only JSONL per candidate with the full
  T4 shadow-event schema (decision/signal ts, z, basis, leg directions, W2
  weights, quotes, modeled + observed crossing cost, gross/net, MAE/MFE,
  completeness class).
- `replay_auditor.py` — independent signal reconstruction from raw bars
  (never from runtime output); six classifications; 100% recognition target.
- `forward_clock.py` + `activate.py` — activation seal + authoritative clock.
- `run_shadow_loop.py` — PID-locked collection loop (watchdog style) for the
  operator to start after human review.

## 2. Activation (real, read-only)

- **Provider:** Ox Securities MetaTrader 5 — `OxSecurities-Demo`, account
  1114712, **trade_mode 0 (DEMO)**, connected read-only.
- **Symbols:** EURGBP.PRO, EURUSD.PRO, GBPUSD.PRO, GBPNZD.PRO, NZDUSD.PRO —
  explicit mapping, all verified live with M5 rates (6,320 bars/30d per leg)
  and live bid/ask ticks (observed spreads 1–11 points, well under the
  conservative 1.5-pip modeled floor).
- **Activation timestamp (UTC):** `2026-08-20T12:59:33.677636Z`
- **First eligible forward M5 bar:** `2026-08-20T13:05:00Z`
- Warmup depth verified: 261 completed bars per leg (≥200 required).

**From this moment, every eligible event strictly after the activation
timestamp is FORWARD evidence.** No earlier bar may be relabeled. The
pre-activation live smoke (last 5 days) produced 1 EUR_GBP_USD eligible
event, which was **discarded** — it is not forward evidence.

## 3. Engineering verification

- Order prevention: 5/5 (static scan + dynamic proxy block of all write
  capabilities; no broker order API reachable; no account mutation possible).
- Sealed-engine parity: 3/3 (hash drift detected; 146 + 81 events identical
  to the T2 ledger).
- Causality: future-perturbation + tail/head truncation invariance pass
  through the runtime path for both candidates.
- Replay auditor: 2/2 (six classifications; replay never reads runtime
  output).
- Forward clock: 3/3 (deterministic first-eligible bar; seal fields; clock
  authoritative).
- Test audit: **38/38**.

## 4. Forward program state (OUT-OF-LAB)

| State | Value |
|---|---|
| historical_lab_state | CLOSED |
| forward_observation_state | ACTIVE |
| research_mode | PROSPECTIVE_ONLY |
| historical_strategy_optimization | PROHIBITED |
| completed forward events | EUR_GBP_USD 0 / GBP_NZD_USD 0 |

Horizons (unchanged): 15 early diagnostic / 30 minimum useful / 50
preferred. Demo-canary eligibility: 10 clean events + 28 days + gates A–K
(`CTBT_T4_DEMO_CANARY_REVIEW_CONTRACT.json`) — computes eligibility only;
**does not authorize orders**. T5 (demo execution canary) requires explicit
human authorization and is not created until a candidate reaches the
evidence hinge.

## 5. Independence & safety

- Canonical AUD_GBP_NZD: shares provider/infrastructure, keeps separate
  state, ledgers, metrics, and priority.
- No portfolio optimization, no PnL pooling, no capital routing, no sizing.
- Ledgers: `state/ledger_<triangle>.jsonl` (append-only).
- `production_authorized = false`, `demo_execution_authorized = false`,
  `capital_routing_authorized = false`, `human_review_required = true`.

## 6. Next steps

WAITING / FORWARD OBSERVATION. The operator starts the collection loop
(`python ctbt_runtime/run_shadow_loop.py --start`) after human review; the
monthly engineering audit and quarterly scientific review proceed on
schedule; no daily commits are made merely because no signal occurred.
Next checkpoint recommendation: `NONE UNTIL EVIDENCE HINGE` (then
`SW-CTBT-T5-DEMO-EXECUTION-CANARY`).

**NO ORDERS. NO CAPITAL. NO LIVE.**
