# BLOC 10 — READ-ONLY CANONICAL SENSOR SERVICE ARCHITECTURE

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`

## 1. Mission

Expose T1 canonical observations and T2 mechanical observable states through one provider-independent, local-first, read-only query boundary for research agents, replay systems and future Market OS consumers.

The service is a **truth-serving layer**, not an acquisition layer and not an analytics engine.

```text
T0 evidence
  ↓
T1 canonical observations
  ↓
T2 mechanical observables
  ↓
BLOC 10 READ-ONLY CANONICAL SENSOR SERVICE
  ↓
research agents / replay / Market OS bridge
```

Hard rules:

1. no provider API/network calls from service code;
2. no writes to T0/T1/T2 from query paths;
3. no hidden recomputation with unversioned logic;
4. no quality upgrading;
5. no provider-specific fields in research-facing responses unless explicitly requesting lineage/debug context;
6. every response is `as_of` aware and generation/version aware;
7. missing, stale, degraded and blocked states are explicit;
8. historical and live consumers use the same contracts.

## 2. Responsibilities

The service MUST provide:

- canonical observation retrieval;
- venue-local T2 state retrieval;
- cross-venue T2 state retrieval;
- static and rolling horizon retrieval;
- exact `as_of` queries;
- explicit quality/coverage/degraded-mode metadata;
- source independence/redundancy metadata;
- generation/version pinning;
- lineage lookup from T2→T1→T0;
- availability/readiness lookup;
- deterministic pagination/streaming of local results;
- bounded batch/event-window queries;
- schema introspection for agents;
- reproducibility receipts.

The service MUST NOT:

- call Kraken/Gate/Binance/etc.;
- perform historical backfills;
- run live collectors;
- mutate canonical datasets;
- invent fallback values;
- zero-fill missing data;
- create strategy/trade signals;
- hide disagreement;
- silently select newest generations in strict reproducibility mode.

## 3. Service planes

### 3.1 Query plane

Read-only local access to canonical T1/T2.

### 3.2 Metadata plane

Schemas, generations, quality policies, coverage, readiness and lineage.

### 3.3 Reproducibility plane

Returns exact query specification, generation IDs, registry/policy versions and source lineage sufficient to replay the answer later.

### 3.4 Debug plane

Operator-only detailed provider/source lineage. Research-facing default remains provider-independent.

## 4. Canonical query objects

```text
SensorQuery
ObservationQuery
MechanicalStateQuery
WindowQuery
EventContextQuery
LineageQuery
CoverageQuery
ReadinessQuery
SchemaQuery
GenerationQuery
```

Common request fields:

```text
asset_or_contract
sensor_family
state_name
venue_scope
as_of
start
end
granularity
horizon
window_mode
quality_requirement
redundancy_requirement
generation_policy
revision_policy
include_lineage
include_quality
limit
cursor
```

## 5. Canonical response envelope

Every service response MUST return a versioned envelope:

```text
CanonicalSensorResponse
  request_fingerprint
  response_schema_version
  generated_at
  as_of
  query_scope
  generation_refs
  quality_mode
  coverage
  redundancy
  independence
  data
  missingness
  disagreement
  lineage_summary
  warnings
  reproducibility_receipt
```

`data` may be empty only with typed reason.

## 6. Local-first backends

The service may use:

- Parquet T1/T2 datasets;
- DuckDB as read-only analytical/query engine;
- PostgreSQL operational metadata/catalog;
- versioned manifests/catalogs.

DuckDB remains rebuildable and is never authoritative truth.

The service MUST be capable of starting with network disabled.

## 7. Modes

```text
STRICT_REPRODUCIBLE
LATEST_ACCEPTED
AS_KNOWN_THEN
LIVE_CURRENT
DEBUG_LINEAGE
```

`STRICT_REPRODUCIBLE` requires explicit/pinned generations or deterministic resolution under a frozen manifest.

`AS_KNOWN_THEN` obeys historical availability truth and cannot use later revisions that were not knowable by the requested `as_of`.

`LIVE_CURRENT` may expose latest locally committed data only; it cannot trigger provider requests.

## 8. Security / authority

This service is permanently read-only with respect to market data.

No endpoint/method may:

- place orders;
- use trading credentials;
- mutate exchange state;
- write provider API keys into outputs;
- call paid endpoints;
- bypass free-only policy;
- modify research doctrine.

## 9. Primary implementation modules

```text
quant-lab/src/crypto_sensor_fabric/service/
  models.py
  enums.py
  query.py
  response.py
  catalog.py
  generations.py
  quality.py
  coverage.py
  lineage.py
  readiness.py
  backends/
    parquet.py
    duckdb.py
    postgres_metadata.py
  api/
    local.py
    cli.py
  receipts.py
  errors.py
```

No network provider clients belong under this tree.

## 10. Architectural verdict

Bloc 10 creates the stable consumer boundary required before historical replay and Market OS integration. Research code should no longer need filesystem paths, provider APIs, exchange schemas, or hand-written DuckDB SQL to access canonical mechanics.