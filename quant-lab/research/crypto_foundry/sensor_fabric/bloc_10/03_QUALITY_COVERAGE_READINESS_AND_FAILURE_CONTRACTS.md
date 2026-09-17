# BLOC 10 — QUALITY, COVERAGE, READINESS & FAILURE CONTRACTS

## 1. Purpose

Make quality and missingness part of every answer instead of optional side metadata.

## 2. Quality propagation

The service consumes Bloc 6 quality objects and may only preserve or downgrade them.

It may never upgrade:

```text
FULL
DEGRADED_REDUNDANT
DEGRADED_PARTIAL
RESEARCH_ONLY
DATA_BLOCKED
```

If a query combines multiple windows/sensors, resulting quality is bounded by the weakest required component under the requested operation.

## 3. Coverage object

Every temporal/mechanical response returns:

```text
CoverageSummary
  expected_intervals
  available_intervals
  valid_intervals
  missing_intervals
  coverage_fraction
  expected_sources
  available_sources
  independent_sources
  venue_count
  not_expected_intervals
  known_gaps
  blocked_intervals
```

Coverage denominator excludes `NOT_EXPECTED` where PIT lifecycle proves the observation could not exist.

## 4. Missingness contract

Typed reasons include at minimum:

```text
VALID_ZERO
PROVIDER_EMPTY_CONFIRMED
NOT_EXPECTED
UNSUPPORTED
HISTORY_UNAVAILABLE
ACCESS_BLOCKED
KNOWN_GAP
NORMALIZATION_BLOCKED
QUALITY_BLOCKED
REVISION_CONFLICT
GENERATION_MISSING
NOT_COMPARABLE
NO_QUORUM
STALE
UNKNOWN
```

Empty result sets must carry one or more explicit reasons.

## 5. Readiness contract

The service exposes scope-aware readiness rather than global readiness.

Request dimensions:

```text
sensor/state
asset/universe
date range
granularity
minimum quality
minimum independent sources
required operations
```

Possible states inherit Bloc 7:

```text
NOT_STARTED
ACQUIRING
RAW_READY
T1_PARTIAL
QUALITY_PARTIAL
RESEARCH_LOCAL_ONLY
RESEARCH_REDUNDANT
RESEARCH_CROSS_VENUE
RESEARCH_MULTI_ERA
DATA_BLOCKED
VALIDATION_FAILED
```

## 6. Operation eligibility

The service must expose which cross-venue operations are allowed:

```text
VENUE_LOCAL_FEATURES
CROSS_VENUE_BREADTH
CROSS_VENUE_CONSENSUS
CROSS_VENUE_DISPERSION
NOTIONAL_SUM
WEIGHTED_AGGREGATION
CORROBORATION_ONLY
```

A query requesting a forbidden operation fails explicitly rather than performing a weaker substitute.

## 7. Failure hierarchy

Canonical service errors:

```text
InvalidQuery
UnknownSensor
UnknownAsset
UnknownContract
UnknownGeneration
GenerationConflict
RevisionConflict
AsOfViolation
QualityRequirementNotMet
CoverageRequirementNotMet
RedundancyRequirementNotMet
OperationNotEligible
LineageUnavailable
SchemaVersionMismatch
BackendUnavailable
LocalCatalogInconsistent
DataBlocked
```

Provider/network failures do not originate here; if upstream history contains them they are represented as data quality/missingness evidence.

## 8. Partial results

Partial results are allowed only when caller policy permits them.

Request policy:

```text
FAIL_ON_PARTIAL
RETURN_PARTIAL_WITH_FLAGS
RETURN_AVAILABLE_ONLY
```

Default research-critical mode should be `FAIL_ON_PARTIAL` where required mechanics are part of a causal/mechanism test.

## 9. Quality-aware event windows

For LF14-style event context the service must return coverage by phase/window:

```text
PRE_SHOCK
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
```

Each sub-window carries independent quality/coverage so a good annual coverage percentage cannot hide a missing propagation window.

## 10. Acceptance principle

No consumer should need to guess whether a returned number is trustworthy, partial, one-source, revised, stale or blocked. The response contract must state it directly.