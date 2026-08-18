# QL-EXEC-R2 MT5 CLOCK MAPPING

`clock_state(symbol=None)` -> `BrokerClockState`.

## Calibration
`offset = tick.time - time.time()` (source minus UTC). Adopted only when
`abs(offset) < 12h` (TB plausibility gate). A stale/missing tick retains the
previous valid calibration; no silent clock mixing.

## BrokerClockState
| Field | Value |
|---|---|
| `source_clock_name` | "MT5_SERVER" |
| `source_offset_seconds` | observed/calibrated offset |
| `calibrated` | True when a valid offset exists |
| `status` | CALIBRATED / UNCALIBRATED |
| `observed_at_utc` | local observation time |
| `failure_reason` | "no fresh tick available" when uncalibrated |

## No hardcoded timezone
No UTC+3 (or any fixed offset) is baked in. Positive, negative, and zero
offsets are all representable and tested.

## Probe symbol
`clock_probe_symbol` is injectable. The adapter never hardcodes a TB strategy
symbol for calibration.
