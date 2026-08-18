# QL-EXEC-R1.1 BROKER CLOCK CONTRACT

## Contract
`BrokerSession.clock_state() -> BrokerClockState`

## BrokerClockState fields
| Field | Meaning |
|---|---|
| `source_clock_name` | identifies the source clock (e.g. `MT5_SERVER`) |
| `source_offset_seconds` | calibrated source-clock minus UTC; always observed/calibrated |
| `calibrated` | whether offset is currently calibrated |
| `calibration_age_seconds` | age of calibration where meaningful |
| `status` | `ClockStatus`: CALIBRATED / UNCALIBRATED / STALE / FAILED / UNKNOWN |
| `observed_at_utc` | local observation time |
| `failure_reason` | why calibration failed, if any |

## Hard rule
The offset is observed/calibrated data. No hardcoded `UTC+3` (or any other
fixed offset) belongs in the generic runtime. Positive and negative offsets
must both be representable. `UNKNOWN` / `UNCALIBRATED` must be representable.

## Why
TB engineering proves MT5 source timestamps and local UTC cannot be casually
mixed. TB calibrates broker/server epoch offset for bar closure, quote age,
and freshness — while the raw MT5 M5 bar-open key remains canonical strategy
parity.

## R2 note
R2 `MT5BrokerSession.clock_state()` must populate this from the validated TB
calibration mechanics. SIM/REPLAY may provide deterministic clock state.
