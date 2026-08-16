# TB-R2 — Clock Semantics

## 1. Three clocks, explicit roles

| Clock | Source | Role |
|---|---|---|
| Broker bar time | MT5 `copy_rates*` timestamp (server time, bar OPEN time) | Strategy key, verbatim; session math `est_hour=(hour-5)%24` |
| Broker tick time | `symbol_info_tick().time` (server time) | `quote_age_ms` and cross-leg skew |
| Local receipt time | `datetime.now(timezone.utc)` at fetch | recorded alongside broker tick time |

## 2. Quote-age definition (frozen)

```
quote_age_ms = snapshot_reference_time - broker_tick_time
```

- **Prefer broker tick timestamp** when available (always the case via MT5).
- Broker tick time is normalized to UTC-aware (`to_utc_aware`).
- If broker timestamps are unavailable/unreliable the snapshot fails closed
  (`INVALID_QUOTE`) — the layer never silently falls back to receipt-time
  semantics for the age gate.

## 3. Cross-leg skew

```
max_cross_leg_skew_ms = max(tick_times) - min(tick_times)
```

across GBPAUD / GBPNZD / AUDNZD. If skew > `max_cross_leg_skew_ms`
(default 1000ms, provisional), the basket is **not** a coherent simultaneous
market state → no submission. Threshold semantics: strictly-greater fails;
exactly-equal passes (tested).

## 4. Timezone normalization

- All internal transport timestamps are UTC-aware datetimes.
- No naive-datetime subtraction across mixed tz-awareness (every subtraction
  goes through `to_utc_aware`).
- The **canonical session conversion remains fixed UTC−5** on the raw bar
  hour — never `America/New_York`, never broker-local DST. A runtime switch
  to DST-corrected time would silently break session parity; the config field
  `canonical_timezone_semantics = "FIXED_UTC_MINUS_5"` is the single lock.

## 5. Clock regression guard

A tick whose timestamp is older than the previously-seen tick for the same
symbol by more than `clock_regression_tolerance_ms` (default 5000ms,
provisional) is flagged `CLOCK_REGRESSION` and the execution snapshot fails
closed (test `J_clock_regression_flags`).

## 6. Replay semantics

During historical replay the reference time is the **selected bar's close
time** (the moment it just closed) — reproducing causal live behavior. The
live staleness gate uses wall-clock `now`. Both are the same semantic:
"how long ago did this bar close?" (replay: 0s; live: wall-clock age).
