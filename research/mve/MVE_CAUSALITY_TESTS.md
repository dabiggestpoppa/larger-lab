# MVE CAUSALITY TESTS — R0.6

## Status: BLOCKED (no harness exists; code does not compile)

There is no causality test harness in the repo, and the tests cannot be written
to run against `src/mve` until the two broken modules are repaired. Below is
the source-review result plus the required test spec.

## Source review (static, performed on the committed source)

Backward-looking (causal) patterns present — good:

- `volatility.py`: `prices.shift(1)` log-returns, `.rolling(window=...)` for
  std / EWMA / Parkinson / Garman-Klass / ATR / MAD / GARCH-style estimators.
- `anchors.py`: `rolling(window).min()/.max()` for swing anchors,
  `rolling` volatility for anchor ranking.
- `backtest.py:55` and `:462`: `strategy_returns = returns * signals.shift(1)`
  — correctly shifts signals to avoid lookahead.

Forward-looking patterns present — MUST be restricted to outcome labeling only:

- `morphic_coordinates.py:334`: `forward_returns = np.log(prices.shift(-1)/prices)`
- `sigma_states.py:317`: `forward_returns = np.log(prices.shift(-1)/prices)`

Per the program rules, `shift(-1)` may only be used for event-study OUTCOME
classification, never as a feature available to a live signal. After repair,
verify these forward returns are never fed back into state classification,
acceptance, or rekey inputs.

## Required test harness (to be added once the code compiles)

1. **Sigma causality** — a volatility/sigma value at bar t must be identical
   when the series is truncated at t (no dependence on bars > t).
2. **Anchor causality** — an anchor detected at t must not move when later bars
   are appended (no repainting).
3. **Acceptance causality** — acceptance at t uses only bars ≤ t; appending
   bars must not change historical acceptance labels.
4. **Rekey causality** — rekey boundaries must not repaint; rekey state at t is
   a function of bars ≤ t.
5. **State-label uniqueness** — each bar classified exactly once per state
   ladder; no duplicate events.
6. **Event deduplication** — repeated touches/breaches deduplicated per event
   definition.
7. **Current-bar vs next-bar** — no next-bar information leaks into entry
   features; signals must be applied with `shift(1)` in backtests.
8. **Resampling consistency** — H1 open=first, close=last within each hour;
   independent reproduction matches.

Each test should use a synthetic deterministic OHLC series with planted
regimes so causality violations surface as mismatched values after truncation.
