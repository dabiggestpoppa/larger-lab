# QL-EXEC-R1.1 TIMESTAMP TRUTH CONTRACT

## Rule
The generic runtime must never silently convert every bar/tick timestamp into
UTC. Provider/source timestamps needed for strategy parity are preserved.

## Three distinct time concepts
| Concept | Field | Meaning |
|---|---|---|
| Source timestamp | `Tick.time` / `Bar.time` | raw provider timestamp; MT5 bar time == BAR OPEN time |
| Observation time | `Tick.observed_at_utc` / `Bar.observed_at_utc` | local received/observed time |
| Calibration context | `source_clock_name` + `offset_seconds` | which source clock, calibrated offset |

## Critical TB rule
For TB, MT5 bar timestamp == BAR OPEN TIME and the strategy uses that raw
source key. Closure/freshness uses a calibrated server-time reference. R2
must reproduce this exactly; R1.1 only creates enough generic contract space
to represent it.

## No strategy clock policy
London session, EST fixed offset, M5 TB closure rules — none of these belong
in the generic `execution_runtime`. The generic runtime carries timing truth;
`StrategyAdapter` decides strategy-time semantics.

## Non-normalization guarantee
There is no generic normalization function that rewrites `Tick.time` or
`Bar.time`. A market-data record distinguishes raw source, observation, and
calibration context.
