# BLOC 10 — QUERY SURFACES, LINEAGE & AGENT INTERFACE

## 1. Purpose

Define the actual read-only surfaces used by research agents and operator tooling.

## 2. Core service calls

Planned local API/CLI methods:

```text
get_observations()
get_mechanical_state()
get_cross_venue_state()
get_window_series()
get_event_context()
get_coverage()
get_readiness()
get_generation_info()
get_schema()
get_lineage()
explain_response()
```

All methods are provider-independent by default.

## 3. Mechanical-state query examples

```text
BTC LiquidationState at 2022-05-12T14:00Z
BTC FlowConsensus rolling 7D as of t
SOL LiquidityWithdrawalBreadth static 30D
ETH VenueDispersion across liquidation mechanics
BTC LeverageState venue=BYBIT
```

The service returns canonical state objects, quality, coverage, generations and lineage rather than provider-native schema fragments.

## 4. Event-context query

`get_event_context()` supports research episode alignment:

```text
asset
anchor_time
phase_boundaries or window recipe
requested_states
static_horizons
rolling_horizons
quality requirements
redundancy requirements
```

Response is phase-indexed and suitable for MECH/LF matching without future leakage.

## 5. Batch research interface

Must support deterministic batch requests for event sets without one request per row.

```text
EventBatchQuery
  event_ids
  assets
  anchor_times
  state_names
  window_recipe
  generation_policy
```

Output preserves `event_id` and exact scope.

## 6. Lineage levels

### L0 — summary

```text
T2 generation
T1 generation
source count
independent count
quality mode
```

### L1 — canonical inputs

T1 observation IDs and normalization methods.

### L2 — evidence lineage

T0B projection refs, acquisition refs and T0A SHA-256 evidence blobs.

### L3 — operator debug

Provider-native source boundaries, parser versions, revision tickets and integrity records.

Research defaults to L0; deeper levels are opt-in.

## 7. Explainability

`explain_response()` must answer:

- why this generation was selected;
- why sources were included/excluded;
- whether source groups are independent;
- what coverage exists;
- why the quality mode is what it is;
- whether any disagreement is present;
- whether the response is strict PIT-safe;
- which transformations produced the state.

It must not fabricate causal interpretation.

## 8. Schema introspection

Agents can query the local schema registry instead of assuming field names.

Schema response includes:

```text
object name
version
field definitions
units
nullable fields
quality fields
allowed horizons
allowed operations
lineage availability
```

## 9. Pagination and result bounds

Large observation queries require deterministic cursor pagination.

Cursor binds:

```text
request fingerprint
generation IDs
sort order
last key
schema version
```

Changing generations invalidates old cursor use.

## 10. Read-only CLI

Planned examples:

```text
sensorctl state BTC liquidation --as-of ...
sensorctl state BTC flow_consensus --rolling 7d
sensorctl coverage BTC open_interest --from ... --to ...
sensorctl lineage <state-id> --level 2
sensorctl readiness lower-field-14 --manifest ...
```

CLI is a client of the same service contracts; it must not contain separate business logic.

## 11. Agent firewall

Research agents are prohibited from:

- importing provider adapters directly;
- querying provider endpoints as part of canonical research runs;
- opening raw lake filesystem paths as a substitute for service output;
- bypassing quality/revision policy;
- upgrading blocked data through ad hoc proxies without explicit new research authorization.

This makes the service the canonical consumer boundary for the sensor fabric.