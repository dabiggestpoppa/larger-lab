# BLOC 10 — AS-OF, GENERATION & REVISION SEMANTICS

## 1. Purpose

Freeze exact temporal/version behavior for every canonical service query.

A query must answer not only **what value**, but:

> what was valid, available, accepted and reproducible under the requested time/version boundary?

## 2. Time coordinates

The service inherits Bloc 5 distinctions:

```text
source_event_at
interval_start_at
interval_end_at
effective_at
published_at
market_available_at
observed_at
ingested_at
normalized_at
```

Research `as_of` semantics are based on market/public availability policy, never ingestion time alone.

## 3. As-of policies

### `AS_KNOWN_THEN`

Only observations/revisions with `market_available_at <= as_of` are eligible.

### `LATEST_ACCEPTED`

Use latest accepted local generation/revision, while still reporting its availability and revision history. Not valid for strict historical reconstruction unless explicitly requested.

### `EXACT_GENERATION`

Caller provides T1/T2 generation IDs and required registry/policy versions.

### `FIRST_KNOWN`

Use earliest accepted representation available for the economic event. Research-only/debug use.

### `ALL_REVISIONS`

Return revision history rather than selecting one canonical value.

## 4. Generation resolution

Generation references may include:

```text
T1_generation_id
T2_generation_id
identity_registry_version
normalization_registry_version
quality_policy_version
dependency_graph_version
observable_registry_version
baseline_registry_version
code_revision
```

Strict mode fails if required versions cannot be uniquely resolved.

No silent fallback from missing exact generation to latest.

## 5. Revision conflicts

Possible service states:

```text
REVISION_UNAMBIGUOUS
REVISION_SELECTED_AS_KNOWN_THEN
REVISION_SELECTED_EXACT
REVISION_MULTIPLE_RETURNED
REVISION_CONFLICT
REVISION_UNRESOLVED
```

Default research-safe behavior on unresolved ambiguity is fail closed.

## 6. Window boundary semantics

Every temporal query must declare:

```text
left_boundary
right_boundary
boundary_inclusion
horizon
window_mode
minimum_coverage
```

Default interval convention should be explicit and uniform, e.g. `[start, end)` where compatible.

No query may mix interval-close data into an `as_of` before the close/publication boundary.

## 7. Static and rolling windows

Canonical research protocol:

```text
STATIC: 1D / 3D / 7D / 14D / 30D / 60D
ROLLING: 3D / 7D / 14D / 30D
ROLLING 60D: only where support is adequate
```

Responses preserve:

```text
window_mode
window_start
window_end
sample_count
coverage_fraction
source_count
independent_source_count
quality_mode
```

## 8. Historical/live convergence

The same closed interval queried from a frozen historical generation and from an equivalent finalized live generation must agree within declared methodology tolerance.

If not:

```text
HISTORICAL_LIVE_PARITY_FAILURE
```

is blocking for promotion.

## 9. Future knowledge defense

The service must prevent:

- current symbol lifecycle knowledge from creating pre-listing observations;
- later provider corrections entering earlier `AS_KNOWN_THEN` views;
- future stablecoin conversion values being used historically;
- later universe membership changing prior PIT membership;
- later quality policy silently rewriting a pinned historical response.

## 10. Reproducibility receipt

Every strict response includes a receipt containing at least:

```text
request_fingerprint
resolved_as_of_policy
resolved_generations
registry_versions
revision_policy
quality_policy_version
query_engine_version
source_manifest_refs
response_hash
```

The receipt is sufficient to prove exactly which canonical truth surface produced the answer.