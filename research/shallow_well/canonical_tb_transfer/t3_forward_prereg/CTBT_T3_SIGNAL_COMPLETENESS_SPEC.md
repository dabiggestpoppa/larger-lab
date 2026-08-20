# CTBT T3 — Forward Signal-Completeness Specification

**Part of:** `SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION`

## 1. Purpose

Verify that the forward-shadow runtime captures **every** theoretically
eligible signal for each sealed candidate, and that any gap is an
individual, auditable failure — never averaged away.

Patterned after the canonical TB weekly completeness audit, applied
independently to:

- `CTBT-EUR-GBP-USD-v1`
- `CTBT-GBP-NZD-USD-v1`

## 2. Independent replay (mandatory)

The completeness auditor must **reconstruct eligible signals independently**
from raw completed M5 data using the frozen candidate engine (the sealed T1.1
lifecycle implementation: 200-bar ddof=0 causal z, strict |z|>3, E1 ±0.25
exit, z6 stop, London 03:00–12:00 EST, 120-min runway, noon hard exit,
concurrency 1, deterministic re-entry).

It must **not** merely reread runtime signal logs. The runtime ledger and the
independent replay are two separate truth layers; the auditor compares them.

## 3. Inputs required for replay

For each candidate, per bar:

- timestamp (M5)
- open / high / low / close for all three legs
- spread if provider bar carries it (separate diagnostic layer)
- provider provenance + symbol mapping
- missing-bar flags (gaps, holidays, feed interruptions)

## 4. Event classifications

For every theoretically eligible event (independent replay), classify against
the runtime shadow ledger:

| Class | Meaning |
|---|---|
| `MATCHED_SHADOW` | runtime captured the event identically (entry/exit ts, direction, exit reason within tolerance) |
| `VALID_RUNTIME_BLOCK` | runtime correctly declined to trade (e.g., concurrency already in a basket, session block) — matches replay logic |
| `MISSED_SIGNAL` | replay says an eligible event occurred; runtime did not record it (and no valid block) |
| `RUNTIME_ONLY_SIGNAL` | runtime recorded an event that replay cannot reproduce from raw data (possible data/runtime divergence) |
| `DATA_DIVERGENCE` | replay and runtime differ due to data/provider divergence (bar timestamp/OHLC mismatch, missing bars, mapping error) — strategy not implicated |
| `NO_SIGNAL` | no eligible event on this bar in either layer |

## 5. Recognition target

**100%** of replay-eligible events must map to MATCHED_SHADOW or
VALID_RUNTIME_BLOCK (or DATA_DIVERGENCE with a documented data cause).
MISSED_SIGNAL and RUNTIME_ONLY_SIGNAL are individual failures: each is
reported with its bar timestamp, legs, z, and root cause; none may be folded
into an average.

## 6. Data-parity separation

Before classifying a candidate as `FORWARD_MECHANISM_FAILED`, the auditor
must distinguish:

- **strategy failure** (frozen engine on clean data is negative / sign
  reversed / cost-dominated), from
- **data/provider divergence** (bars missing, OHLC mismatched, spread
  distortion, symbol mapping error, unsynchronized legs).

Persisted per divergence: bar timestamps, OHLC, spread, provider provenance,
symbol mapping, missing bars.

## 7. Reporting cadence

- Completeness report accompanies every forward evidence review (monthly
  engineering audit / quarterly scientific review).
- Fields per candidate: total eligible, MATCHED_SHADOW, VALID_RUNTIME_BLOCK,
  MISSED_SIGNAL, RUNTIME_ONLY_SIGNAL, DATA_DIVERGENCE, NO_SIGNAL, and the
  per-failure detail list.
- A completeness shortfall does not, by itself, stop the candidate; it
  invalidates the evidence window in which it occurred until reconciled.

## 8. Boundaries

This spec describes observation and auditing only. It authorizes **no**
orders, no account mutation, no capital routing, and no parameter changes.
