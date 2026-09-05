# BLOC 10 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

## 1. Objective

Give the implementation agent a reviewable build sequence and hard acceptance gates for the read-only canonical sensor service.

No squashing during staged review.

## 2. Test layers

```text
S0 CONTRACT
S1 TEMPORAL / AS-OF
S2 GENERATION / REVISION
S3 QUALITY / COVERAGE
S4 LINEAGE
S5 BACKEND / OFFLINE
S6 HISTORICAL-LIVE PARITY
S7 PERFORMANCE / RESOURCE
S8 AGENT FIREWALL / SECURITY
```

## 3. Mandatory contract tests

- every response has request fingerprint;
- every response has response schema version;
- `as_of` always explicit or deterministically defaulted by named mode;
- empty responses have typed missingness;
- quality metadata cannot be omitted from canonical state responses;
- provider-native fields do not leak through default research contracts;
- unsupported operations fail explicitly;
- deterministic ordering is enforced.

## 4. Temporal/adversarial tests

Must test:

- event exactly on interval boundary;
- pre-publication query;
- post-publication query;
- later historical revision queried with earlier `AS_KNOWN_THEN`;
- current symbol mapping against pre-listing date;
- stablecoin conversion knowledge from future date;
- incomplete rolling window;
- static/rolling disagreement preserved;
- query crossing listing/delisting lifecycle;
- query while newer generation publishes.

## 5. Generation/revision tests

- exact generation succeeds;
- missing generation fails closed;
- ambiguous latest under strict mode fails;
- revision conflict does not silently pick latest;
- pinned old generation remains queryable after new generation publication;
- cache key changes with generation/policy revisions;
- response receipt reproduces exact response hash.

## 6. Quality/coverage tests

- valid zero vs gap;
- not-expected excluded from denominator;
- one source cannot satisfy two-source quorum;
- aggregator dependency does not fake independent redundancy;
- degraded upstream remains degraded downstream;
- `FAIL_ON_PARTIAL` blocks incomplete event phase;
- event-window quality reported by phase;
- operation eligibility enforced.

## 7. Lineage tests

At least one golden state per major family must traverse:

```text
T2 state
→ T1 observations
→ T0B projections
→ acquisition records
→ T0A SHA256 evidence
```

Broken lineage is blocking.

## 8. Offline/network tests

Run service with outbound network disabled.

Pass conditions:

- startup succeeds;
- state queries work against local fixtures;
- no provider adapter invoked;
- no DNS/HTTP attempt occurs;
- no trading credentials required.

## 9. Historical/live parity tests

For finalized intervals under identical methodology:

```text
historical batch output == finalized live output
```

within declared numeric tolerance and identical semantic fields.

Parity failures block promotion.

## 10. Failure-injection tests

Inject:

- corrupt manifest;
- missing Parquet partition;
- stale Postgres metadata pointer;
- unavailable DuckDB backend;
- generation published mid-query;
- oversized query;
- memory limit breach;
- cursor used after generation change;
- lineage pointer missing;
- schema version mismatch.

Service must fail typed and bounded.

## 11. Research-agent integration tests

A fixture research script must obtain:

```text
BTC LiquidationState at t
BTC FlowConsensus rolling 7D
ETH LiquidityWithdrawalBreadth static 30D
event-context packet with pre/absorb/reorganize/propagate/contain windows
quality + coverage + lineage summary
```

without importing provider adapters or reading raw filesystem paths directly.

## 12. Planned staged implementation commits

```text
SENSOR-B10-I01  service enums/models/errors
SENSOR-B10-I02  request fingerprint + response envelope
SENSOR-B10-I03  generation catalog
SENSOR-B10-I04  revision/as-of resolver
SENSOR-B10-I05  Parquet read backend
SENSOR-B10-I06  DuckDB read backend
SENSOR-B10-I07  Postgres metadata backend
SENSOR-B10-I08  canonical observation queries
SENSOR-B10-I09  venue-local T2 state queries
SENSOR-B10-I10  cross-venue T2 state queries
SENSOR-B10-I11  static/rolling window queries
SENSOR-B10-I12  quality/coverage propagation
SENSOR-B10-I13  readiness/eligibility queries
SENSOR-B10-I14  lineage resolver L0-L3
SENSOR-B10-I15  event-context query
SENSOR-B10-I16  deterministic batch/event query
SENSOR-B10-I17  schema/generation introspection
SENSOR-B10-I18  explain-response + receipts
SENSOR-B10-I19  deterministic pagination/cursors
SENSOR-B10-I20  local cache layer
SENSOR-B10-I21  atomic generation publication/read pinning
SENSOR-B10-I22  CLI/local API surface
SENSOR-B10-I23  offline/network firewall tests
SENSOR-B10-I24  historical-live parity suite
SENSOR-B10-I25  quality/revision adversarial suite
SENSOR-B10-I26  performance/resource limits
SENSOR-B10-I27  research-agent fixture integration
SENSOR-B10-I28  golden reproducibility packet
SENSOR-B10-I29  final acceptance evidence
SENSOR-B10-I30  Bloc 11 handoff
```

## 13. Required evidence outputs

Implementation must eventually produce:

```text
service_contract_report.md
as_of_revision_test_report.md
generation_resolution_matrix.csv
quality_coverage_test_report.md
lineage_integrity_report.md
offline_network_firewall_report.md
historical_live_parity_report.md
performance_benchmark_report.md
resource_limit_report.md
research_agent_integration_report.md
golden_reproducibility_receipts/
bloc_10_acceptance_summary.md
```

## 14. Promotion gate

Bloc 10 implementation may pass only if:

1. service works fully offline;
2. strict as-of queries resist future leakage;
3. pinned generations/revisions are deterministic;
4. quality/missingness remain explicit;
5. lineage reaches T0 evidence;
6. historical/live finalized intervals converge;
7. research agents need no provider-specific code;
8. read-only boundary is enforced;
9. resource limits fail safely;
10. golden response receipts reproduce exact results.

Any failure in PIT truth, lineage, read-only authority, offline operation or generation determinism is blocking.