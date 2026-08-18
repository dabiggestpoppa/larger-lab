# QL_EXEC_R4_TB_MARKET_DATA_CONTRACT

## Raw timestamp truth

- MT5 `copy_rates*` bar timestamp is the **BAR OPEN time** (server time).
- The strategy key uses that raw open time **verbatim**; it is never
  normalized to UTC and never `+5min`.
- `bar_close_time = bar_open_time + bar_seconds` exists only for freshness math.

## Common-bar synchronization

- A valid `TriangleSignalSnapshot` requires all three legs (GBPAUD, GBPNZD,
  AUDNZD) to share the SAME closed-bar open time.
- `SynchronizedTriangleFeed` selects the latest common closed timestamp; a
  lagging/forming/missing/stale leg fails closed (never mixed timestamps).

## Failure codes (frozen)

`MISSING_LEG`, `NO_COMMON_CLOSED_BAR`, `FORMING_BAR`, `STALE_SIGNAL_BAR`,
`INVALID_OHLC`, `TIMESTAMP_MISMATCH`, `DUPLICATE_BAR`, `NO_NEW_SIGNAL_BAR`,
quote/clock failures, `OK`.

## Market-closed / recovery

- `NO_COMMON_CLOSED_BAR` / `STALE_SIGNAL_BAR` / `MISSING_LEG` => transient
  `ONLINE_MARKET_CLOSED`; the status is recomputed on the next fresh healthy
  observation (non-latching — the R6.1B lesson).

## Parity result

EXACT. Tests cover raw open-time key, derived close-time, common-bar validity,
lagging-symbol fail-closed, forming-bar fail-closed, and recovery non-latching
(`test_execution_runtime_r4_market_data.py`).
