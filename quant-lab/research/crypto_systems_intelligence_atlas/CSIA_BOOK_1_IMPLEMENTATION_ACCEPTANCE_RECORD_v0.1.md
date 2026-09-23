# CSIA Book 1 Implementation Acceptance Record — v0.1

Date: 2026-09-23
Branch: `agent/crypto-systems-intelligence-atlas-build`
Accepted build commit: `c0f19fe03aae03707801d083c269b919e38ed868`

```text
BOOK = 1

PLAN_VERSION = v0.3
PLANNING_STATUS = RATIFIED

IMPLEMENTATION_STATUS = ACCEPTED

EXIT_GATE =
PASS_CSIA_BOOK1_IDENTITY_ONTOLOGY_TEMPORAL_KERNEL

HARDENING_R1 = PASS
HARDENING_R2 = PASS

CSIA_TESTS = 107 PASS
SENSOR_REGRESSION = 2339 PASS / 4 SKIPPED
RUFF = PASS
MYPY = PASS

BLOCKING_CORRECTNESS_ISSUES = 0
```

The operator explicitly ACCEPTS
`PASS_CSIA_BOOK1_IDENTITY_ONTOLOGY_TEMPORAL_KERNEL`.

## Accepted implementation scope

### Bloc 1A — canonical identity
- canonical identity (mint-once `csia:<type>:<slug>`, identity permanence)
- deployment identity (typed markers, N deployments per canonical object)
- REALIZATION (Option C travel-form identity, chain-local manifestations)
- ticker collision discipline (contextual attribute, never an identity key)
- rebrand/history (Constitution §8.3: old name → aliases, object_id stable)
- migration lineage (acyclic, coherent, fail-closed at insertion)
- lifecycle transitions (never deletions; chronology fail-closed)

### Bloc 1B — node ontology
- node ontology (ratified 42-class registry incl. REALIZATION as 42nd class)
- role tags (registry with collision/validation discipline)
- architecture extension slots (FamilySlotRegistry / FinalityDevice reservation)

### Bloc 1C — relationship ontology
- typed relationships (EdgeType dictionary + EdgeSpecs)
- domain/range validation
- fail-closed acyclic insertion (cycle-forming edges rejected atomically)
- hyperedges (roles, route_attributes, IR-9 projection)
- route attributes (record-level multi-hop route identity)

### Bloc 1D — temporal semantics
- valid time / transaction time (bitemporal six-field records)
- UnknownBound (validated bounds; UNKNOWN never converted to OPEN — R9)
- historical replay semantics (as-of queries over valid time)
- strict TemporalRecord supersession semantics (store-level metadata,
  committed records never mutated in place — INV-1D-1)
- lifecycle temporal rules (closure as world-change; liveness is
  valid-time-driven, never status-driven)

## Known non-blocking limitations (explicitly deferred)

- registry is mutable current-state + additive history windows,
  not event sourcing
- no persistence implementation yet (later authorized scope)
- same-instant rebrand guard is registry-level metadata
- stale-window values deferred to Book 2 (Bloc 2G)
- replay machinery deferred to Book 7D
- source/evidence acquisition deferred to Book 2
- family-native value registries deferred to Book 3B
- capital plumbing deferred to Book 5
- Sensor bridge deferred to Book 8

## Governance flags

```text
BOOK_1_IMPLEMENTATION_AUTHORITY_USED = COMPLETE
BOOK_1_IMPLEMENTATION_ACCEPTED = TRUE
PRODUCTION_DEPLOYMENT_AUTHORITY = FALSE
```

Book 1 is closed for implementation. It is NOT reopened unless future work
exposes an actual contract or correctness defect. Acceptance does not grant
production deployment authority.
