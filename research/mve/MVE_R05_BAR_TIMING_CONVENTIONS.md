# MVE R0.5 — BAR TIMING CONVENTIONS (FROZEN)

> Checkpoint: MVE-R0.5-CAUSALITY-GATE · 2026-08-15

These conventions bind all future P4-P7 implementations. They prevent the
feature-timestamp / execution-timestamp confusion that produces off-by-one
leakage.

## H1 resampling (frozen in `data_loader.py`)

| Convention | Value |
|---|---|
| Source | canonical EURUSD M5 (`quant-lab/data/EURUSDPRO_M5_2023_2026.csv`) |
| Aggregation | open=first, high=max, low=min, close=last, volume=sum (`tick_volume`) |
| H1 label | left edge (`label='left'`) |
| H1 closed | left (`closed='left'`) — an H1 bar spans [t, t+1h) |
| Timezone | UTC |
| `h1_interval_time` | the bar's left-edge label t |
| `h1_knowledge_time` | the end of the hour (t + 1h) — H1 OHLC is NOT knowable before the hour completes |
| Empty hours | dropped (weekend gaps); never forward-filled |
| Partial hours | retained with `source_bar_count < 12` recorded; research filters may exclude them; the bar is not knowable until the hour completes |

**Tested:** `test_h1_knowledge_timing_hour_boundary` (identical H1 through a
completed hour when truncated at the hour boundary) and
`test_h1_partial_hour_not_knowable` (a mid-hour cut never yields the complete
hour's OHLC as knowable).

## Bar-level timing (frozen)

| Quantity | Timing |
|---|---|
| `close_t` | only knowable after bar t closes |
| `high_t` / `low_t` | only knowable after bar t closes |
| `open_t` | knowable at bar t open |
| Signal timestamp | the bar at which the signal is FIRST knowable |
| Execution timestamp | always >= signal timestamp + 1 bar (next-bar open or breakout close) |

## Off-by-one rule

- A signal computed from `close_t` must not be timestamped earlier than bar t.
- A signal that needs bar t+1 for confirmation must be timestamped at bar t+1
  (delayed confirmation), never backdated to t.
- No component may mix its feature timestamp with a hypothetical execution
  timestamp.

## Execution contract (frozen, R0.5.1-J)

Every scientific signal declares exactly one of:

| Convention | Meaning | Used by |
|---|---|---|
| `CLOSE_KNOWN` | signal becomes known after the current bar closes | Models B, C (exit), RKEY-A/C |
| `NEXT_OPEN_EXECUTABLE` | signal known after bar close; hypothetical execution only on the next bar open | Models A, C (entry), B — the frozen execution convention for all repaired signals |
| `INTRABAR_CAUSAL` | allowed only when the input itself is genuinely observable intrabar | none currently |

Event timestamps and executable timestamps are NEVER mixed: a signal's
`known_time` is where it appears in the series; execution is always >= the
next bar open after `known_time`.

## Repaired timings (R0.5.1)

| Component | event_time | evidence_complete_time | known_time | action_time |
|---|---|---|---|---|
| Model A (escape) | crossing bar i | bar i+1 close | i+1 | >= i+1 close / next open |
| Model B (breakout) | accepted-state bar i | bar i | i | >= i close / next open |
| Model C (entry) | crossing bar i-1 | +2-sigma bar i | i | >= i close / next open |
| Model C (exit) | trailing-window bar i | bar i | i | >= i close / next open |
| RKEY-B | scan-origin bar i | retest bar j | j | j (anchor active) |

All repaired timestamps are enforced by `MVE_SCIENTIFIC_EVENT_TIME_SCHEMA.json`
and validated by `src/mve/causality.validate_scientific_event_times()` +
`validate_rekey_events()`.
