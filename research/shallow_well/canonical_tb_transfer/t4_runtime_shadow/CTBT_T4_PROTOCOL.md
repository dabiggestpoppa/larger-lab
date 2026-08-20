# CTBT T4 — Transfer-Family Runtime Shadow Integration Protocol

**Checkpoint:** `SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION`
**Authoritative base:** `44379e416c1c49dd055f0d818f10bafccefec131` (T3)
**Parent status:** `PASS_TRANSFER_FAMILY_SEALED_FORWARD_PREREGISTERED`

---

## 1. Mission

Integrate the two sealed CTBT transfer candidates into the existing
provider-neutral Execution Runtime in **READ-ONLY SHADOW MODE** — the
transition from historical research to prospective forward evidence.

**Once T4 is activated successfully, every eligible event strictly after the
activation seal is FORWARD evidence.**

This checkpoint performs **no** historical optimization, **no** demo orders,
**no** live orders, **no** capital routing.

## 2. Sealed strategies

| Version | Strategy hash |
|---|---|
| `CTBT-EUR-GBP-USD-v1` | `aad0a8e64c6964952eb9129ac2cdebd34d308e6df87ebf45e4584c351044b1a7` |
| `CTBT-GBP-NZD-USD-v1` | `5538d63a8acb29883b117fc23c76b1fe389db47ed89009ab3cd258b864f62485` |

Neither spec is modified. The runtime verifies both hashes at load and
refuses to run on drift.

## 3. Activation

`CTBT_T4_ACTIVATION_SEAL.json` is stamped by `ctbt_runtime/activate.py`
after the T4 commit exists, containing: T4 commit SHA, UTC activation
timestamp, provider, account environment, runtime version, strategy hashes,
symbol mappings, and the first causally complete M5 bar eligible for forward
evidence. FORWARD EVIDENCE STARTS ONLY AFTER THIS SEAL. No earlier bar may
be relabeled as forward evidence.

## 4. Provider

Primary: **Ox Securities MetaTrader 5 — `OxSecurities-Demo`** (account
1114712, trade_mode 0 = DEMO), the same demo market-data connection used by
canonical TB, connected **read-only**. T4 sends NO orders and creates NO
broker positions. Canonical and transfer strategies keep separate runtime
slots, strategy IDs, event ledgers, completeness ledgers, and metrics.

## 5. Symbol mapping (explicit, no silent inference)

`EURGBP → EURGBP.PRO`, `EURUSD → EURUSD.PRO`, `GBPUSD → GBPUSD.PRO`,
`GBPNZD → GBPNZD.PRO`, `NZDUSD → NZDUSD.PRO` — recorded in
`CTBT_T4_SYMBOL_MAPPING.json`.

## 6. Runtime contract

`provider market data → completed M5 bars → FrozenTransferStrategyAdapter →
sealed strategy logic → shadow signal/event ledger → independent
replay/completeness audit`.

The adapter (`ctbt_runtime/`) reuses the sealed T1.1 lifecycle primitives
(verified 405/405 + 194/194). The runtime parity test reproduces the T2
2025 event ledger exactly (146 + 81 events, identical entry/exit/direction/
gross) — the runtime path IS the research engine.

## 7. Fail-closed order prevention

All broker write capabilities are **unreachable by construction**: the
runtime touches MetaTrader5 only through `ReadOnlyMT5Proxy`, which exposes a
strict read-only allowlist and raises on every write/order/position/
history/deal capability. Automated tests statically scan the runtime package
for write-capable tokens and dynamically verify the proxy blocks them
(`tests/test_order_prevention.py`, 5 checks).

## 8. Bar causality

Evaluation occurs only on causally completed M5 bars — never a forming bar.
Exact sealed contract: 200-bar causal z, ddof=0, current bar excluded,
strict |z| > 3, W2, E1 ±0.25, z6, fixed London 03:00–12:00 EST, 120-minute
runway, hard noon exit, concurrency 1, canonical re-entry.

## 9. Forward shadow ledger

Append-only JSONL per candidate (`state/ledger_<triangle>.jsonl`) with the
full schema in `CTBT_T4_SHADOW_EVENT_SCHEMA.json`: strategy identity, event
id, decision/signal timestamps, direction, entry/exit z, exit reason, leg
symbols/directions, W2 model weights, per-leg bid/ask/mid/spread, modeled
historical cost, observed quote-crossing cost, observed/model multiple,
gross/net bps, MAE/MFE, hold, completeness classification.

## 10. Observed cost reality

At signal time the runtime captures actual provider quotes (bid/ask/mid/
spread, quote timestamp) for all required legs. Slippage stays
`NOT_OBSERVED` until actual demo fills exist. Historical modeled cost
remains separate from observed quote-crossing cost. Quote quality fields
(freshness, cross-leg skew, missing/stale legs, spread anomaly, validity)
are recorded; where not measurable → `NOT_AVAILABLE`.

## 11. Independent completeness auditor

`ctbt_runtime/replay_auditor.py` reconstructs eligible signals
independently from raw completed M5 bars (never from runtime output) and
classifies: MATCHED_SHADOW / VALID_RUNTIME_BLOCK / MISSED_SIGNAL /
RUNTIME_ONLY_SIGNAL / DATA_DIVERGENCE / NO_SIGNAL. Target: 100% legitimate
signal recognition; every MISSED_SIGNAL or RUNTIME_ONLY_SIGNAL requires
investigation. See `CTBT_T4_COMPLETENESS_SPEC.md`.

## 12. Forward clock

`CTBT_T4_FORWARD_CLOCK.json` is the authoritative forward clock:
activation timestamp/commit, first eligible M5 bar, elapsed days, and
per-candidate completed-event counts.

## 13. Horizons (unchanged from T3)

15 = early scientific diagnostic only · 30 = minimum useful forward
evidence · 50 = preferred. No forcing of event frequency.

## 14. Demo-canary review eligibility (new engineering bridge)

A candidate becomes eligible for a **human review** for tiny demo execution
only after BOTH: (1) ≥10 clean natural forward shadow events AND (2) ≥28
elapsed calendar days since T4 activation — plus the 11 engineering gates
(A–K) in `CTBT_T4_DEMO_CANARY_REVIEW_CONTRACT.json`. It is NOT
FORWARD_VALIDATED / PRODUCTION_READY / CAPITAL_READY. Candidates promote
independently. Eligibility computes nothing else: **it does not authorize
orders**. Actual demo execution requires the explicit
`SW-CTBT-T5-DEMO-EXECUTION-CANARY` checkpoint with human authorization.

## 15. Expectancy & early stop

Expectancy states (INSUFFICIENT_EVENTS … COST_MARGIN_BROKEN) are labels
only. Before 30 events, stop only for catastrophic evidence (causality
failure, runtime mismatch, mechanism inversion, cost impossibility, invalid
data) — never an ordinary losing streak.

## 16. Monthly engineering audit

Deterministic monthly audit: runtime uptime, missing bars, data
divergences, signal classifications, provider costs, event count, hash
integrity. No strategy changes.

## 17. Canonical TB

May share provider / market-data process / infrastructure. Must NOT share
strategy state, event ledger, completeness ledger, evidence count, or
metrics. Canonical TB continues independently and takes priority.

## 18. Out-of-lab state

On successful activation: `historical_lab_state = CLOSED`,
`forward_observation_state = ACTIVE`, `research_mode = PROSPECTIVE_ONLY`,
`historical_strategy_optimization = PROHIBITED`.

## 19. T4 success criteria

Engineering PASS requires: provider connected, symbols mapped, causal M5
feed functioning, both strategies loaded by exact hash, forward ledgers
functioning, independent replay functioning, cost capture functioning,
write/order barriers proven, activation seal written. **No minimum strategy
event count is required** — T4 can pass on day 1 with zero events if the
engineering is correct. After T4 PASS the project enters WAITING / FORWARD
OBSERVATION mode.

## 20. Status

Expected: `PASS_FORWARD_SHADOW_ACTIVE`. Next checkpoint normally `NONE
UNTIL EVIDENCE HINGE`; recommend `SW-CTBT-T5-DEMO-EXECUTION-CANARY` only
when a candidate meets 10 events + 28 days + all demo-canary gates.

**NO ORDERS. NO CAPITAL. NO LIVE.**
