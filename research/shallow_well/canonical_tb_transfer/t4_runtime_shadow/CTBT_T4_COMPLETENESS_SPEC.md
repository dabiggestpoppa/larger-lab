# CTBT T4 — Forward Signal-Completeness Specification (Runtime)

**Part of:** `SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION`

## 1. Purpose

Verify that the forward-shadow runtime captures **every** theoretically
eligible signal for `CTBT-EUR-GBP-USD-v1` and `CTBT-GBP-NZD-USD-v1`, and
that any gap is an individual, auditable failure.

## 2. Independent replay (mandatory)

`ctbt_runtime/replay_auditor.py` reconstructs eligible signals
**independently** from raw completed M5 broker bars using the sealed engine.
It never derives expected signals from runtime output: replay is a separate
code path over raw bar data (provider fetch or stored fixture), while the
runtime ledger is the observation layer. The auditor compares the two
truth layers.

## 3. Classification

| Class | Meaning |
|---|---|
| `MATCHED_SHADOW` | runtime captured the event identically (entry/exit ts, direction, exit reason within tolerance) |
| `VALID_RUNTIME_BLOCK` | runtime correctly declined (concurrency/session block) — matches replay logic |
| `MISSED_SIGNAL` | replay says an eligible event occurred; runtime did not record it (and no valid block) |
| `RUNTIME_ONLY_SIGNAL` | runtime recorded an event replay cannot reproduce from raw bars |
| `DATA_DIVERGENCE` | replay/runtime differ due to bar/data/provider divergence (not strategy) |
| `NO_SIGNAL` | no eligible event |

**Target: 100% legitimate signal recognition.** Every MISSED_SIGNAL and
RUNTIME_ONLY_SIGNAL is reported with bar timestamp, legs, z, and root cause;
each requires investigation; none is averaged away.

## 4. Data-parity separation

Before any `FORWARD_MECHANISM_FAILED` classification, distinguish strategy
failure from data/provider divergence. Persisted per divergence: bar
timestamps, OHLC, spread, provider provenance, symbol mapping, missing bars.

## 5. Quote quality at signal time

Record per leg: quote freshness, cross-leg timestamp skew (where
observable), missing leg, stale quote status, spread anomaly, data validity.
Where true tick age/skew cannot be measured → `NOT_AVAILABLE`. Never invent
precision.

## 6. Boundaries

Observation and auditing only. No orders, no account mutation, no capital
routing, no parameter changes.
