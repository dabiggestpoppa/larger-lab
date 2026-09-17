# G5 — SENSOR RESOLUTION AUDIT (S18)

## SensorRequirement
claim/mechanism ref · required observable (aggressor flow / historical liquidation detail) · resolution · history depth · instrument coverage · time semantics · quality minimum · why required · which alternative evidence is insufficient.

## DataAvailabilityRecord (from Sensor Fabric capability contract, not invention)
Status set: `AVAILABLE`, `PARTIAL`, `CURRENT_ONLY`, `HISTORICAL_LIMITED`, `UNAVAILABLE`, `UNKNOWN`. `UNKNOWN` is not `AVAILABLE`; `PARTIAL`/`CURRENT_ONLY` are not adequate historical coverage (tested).

## Behavior
- Required observable `UNAVAILABLE` → **DATA_BLOCKED**. `DATA_BLOCKED` is a valid terminal: the claim is not demoted as false; no mechanism promotion; no synthetic backfill (`synthetic_backfill_used=false`); no assertion that missing historical data existed.
- `SearchDemand` emitted (demand_id, blocked claim, required sensor, reason, value-of-information class, acceptable providers, history/quality requirement, status, **reopen condition**). Endogenous search demand — no internet crawl.
- Later sensor availability → blocked claim becomes `REOPEN_CANDIDATE` / eligible for frozen experiment — NOT retroactively validated. The institution may now test; it cannot claim historical results that predate measurement.

## Research priority vs promotion
High value-of-information raises priority while the claim remains DATA_BLOCKED — priority and promotion are separate records.

## Status
**PASS** — DATA_BLOCKED + SearchDemand discipline, no fabrication, reactivation-not-validation on sensor arrival.