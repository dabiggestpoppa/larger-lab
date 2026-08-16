# TB-R2 — Signal Bar Contract

## 1. Closed-M5-only rule

Primary and control strategy logic receive **ONLY the latest fully closed M5
bar** for each leg. Forbidden:

- the current forming M5 candle;
- partial bars;
- quote-built provisional OHLC;
- bars with a future close time;
- a mixed closed/forming leg set.

All three legs must share the **identical canonical signal timestamp**.

Example (FAIL CLOSED — no strategy evaluation):

```
GBPAUD closed bar = 10:35
GBPNZD closed bar = 10:35
AUDNZD closed bar = 10:30   <- mismatch
```

The system waits for all three legs to catch up.

## 2. Bar structure

```python
@dataclass(frozen=True)
class ClosedBar:
    symbol: str
    bar_open_time: datetime     # raw MT5 bar OPEN time (server time) = strategy key
    bar_close_time: datetime    # open + 300s; freshness math only
    open / high / low / close: float
    volume: float
    source_timestamp: datetime
    is_closed: bool             # True (never the forming bar)
    bar_id: str                 # "{symbol}:{unix_time}" source identifier
```

## 3. Enforced invariants (validation)

`validate_closed_bar` fails closed on:

- NaN / inf in OHLC;
- nonpositive FX price;
- `high < low`;
- open or close outside `[low, high]` (float tolerance 1e-12).

`validate_signal_snapshot` additionally requires:

- all three legs at the **same** `bar_open_time`;
- all bars closed;
- no per-leg duplicate timestamps (detected in the feed);
- the common bar not stale beyond `max_signal_bar_age_s`
  (`bar_close_time` vs reference time).

## 4. Forming-bar exclusion (time-based, not position-based)

A bar is treated as closed only when `bar_close_time <= reference_time`.
The forming bar (close time in the future) can never enter a snapshot even if
it sits at the end of the fetched list. Proven by the adversarial forming-bar
leakage audit: extreme forming prices produce **zero** snapshot/strategy
changes (`TB_R2_FORMING_BAR_LEAKAGE_AUDIT.json`, `leak_detected = false`).

## 5. Dedup

`last_processed_signal_ts` guarantees **one strategy evaluation per new
synchronized closed bar**. Feeding the same bar 10 times yields exactly one
evaluation (`NO_NEW_SIGNAL_BAR` after the first). A new M5 bar yields exactly
one new evaluation (tests `M_same_signal_bar_looped_10_times_single_evaluation`
and `N_next_m5_bar_one_new_evaluation`).

## 6. Causality

No future bar access, no centered windows, no backfilled rolling values, no
full-sample normalization. The feed reveals bars monotonically; the strategy
computes basis/z only from bars already seen (the sealed previous-200-bars
window, current bar excluded).
