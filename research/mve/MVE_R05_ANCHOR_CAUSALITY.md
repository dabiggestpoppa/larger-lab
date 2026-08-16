# MVE R0.5 — ANCHOR CAUSALITY AUDIT

> Checkpoint: MVE-R0.5-CAUSALITY-GATE · 2026-08-15

## Pivot known-time semantics (the one delayed component)

`_calculate_pivot_high` / `_calculate_pivot_low` confirm a pivot at bar i by
comparing against **both** the `window` bars before and the `window` bars after i:

```python
if ((prices.iloc[i] > prices.iloc[i-window:i]).all() and
    (prices.iloc[i] > prices.iloc[i+1:i+window+1]).all()):
```

Consequence — two distinct timestamps must be separated:

| Timestamp | Definition |
|---|---|
| `pivot_event_time` | bar i (where the local extremum actually is) |
| `pivot_known_time` | bar i + window (when the right-side confirmation is complete) |

**Rule:** no downstream MVE process may consume the pivot value before
`pivot_known_time`. The usable series is
`apply_anchor_delay(pivots, window)` = `pivots.shift(window).ffill()`
(first `window` rows are NaN by construction).

## Verified properties (real data, bounded dev slice 2023-07-03..2024-03-31)

| Probe | Result |
|---|---|
| Confirmed pivots (knowledge time <= t) under future mutation | invariant — max diff 0.0 |
| Raw (undelayed) pivots under future mutation | repaint — diff > 0 near t (expected; this is the delayed-confirmation behavior) |
| Morphic coordinates from **delayed** pivots | invariant through confirmation window — max diff 0.0 |
| Morphic coordinates from **raw** pivots | repaint — diff > 0 (demonstrates exactly what the contract prohibits) |
| Pivot truncation invariance (knowledge-filtered) | invariant — 0.0 at all cutoffs |

## Non-pivot anchors — all causal

Support/resistance levels, trend line, volume profile, time-based, and
volatility-based anchors use trailing windows ending at bar i (incl. current).
They are `CAUSAL_REALTIME`. The trend-line fit uses `recent_indices[-1]` on a
window ending at i — the fitted value at i uses no future bars.

## Consumption rule for future phases

Any phase that uses pivot anchors MUST apply `apply_anchor_delay(pivots, window)`
before feeding them into coordinates. `tests/mve/test_causality.py` enforces
this with `test_pivot_event_time_vs_known_time`, `test_pivot_future_perturbation_with_delay_semantics`,
and `test_anchors_consumed_only_after_confirmation`.
