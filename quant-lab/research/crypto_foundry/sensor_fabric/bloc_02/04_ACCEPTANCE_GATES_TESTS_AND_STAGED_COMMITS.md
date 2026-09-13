# BLOC 2 — ACCEPTANCE GATES, TESTS & STAGED COMMITS

**Status:** PLANNING COMPLETE CANDIDATE  
**Purpose:** define exactly what the eventual build agent must implement, test, commit and prove before Bloc 2 capability probing is considered complete.

---

## 1. Implementation objective

Build a small, deterministic capability-probe subsystem that can answer:

```text
Can provider X deliver sensor Y
for instrument Z
at date D
at granularity G
under the free-only rules,
with enough timestamp/unit/semantic clarity
for later canonical ingestion?
```

The subsystem must create evidence even when the answer is no.

---

## 2. Planned implementation tree

```text
quant-lab/
  src/
    crypto_sensor_fabric/
      probes/
        __init__.py
        models.py
        enums.py
        runner.py
        planner.py
        evidence.py
        coverage.py
        scoring.py
        failures.py
        redaction.py
        reports.py

      providers/
        kraken/probe.py
        gate/probe.py
        binance/probe.py
        bybit/probe.py
        okx/probe.py
        deribit/probe.py
        coinalyze/probe.py
        bitfinex_archive/probe.py

  config/
    crypto_sensor_fabric/
      probe_targets.yaml
      historical_checkpoints.yaml
      provider_probe_endpoints.yaml

  tests/
    crypto_sensor_fabric/
      probes/
      fixtures/
        probe_payloads/

  research/
    crypto_foundry/
      sensor_validation/
        bloc_02/
```

Exact package naming can conform to repository conventions, but architectural separation must survive.

---

## 3. Required data models

At minimum:

```text
CapabilityProbeRequest
CapabilityProbeAttempt
CapabilityProbeEvidence
CapabilityClaim
ProviderSensorCoverage
ProviderProbeSummary
SensorRedundancySummary
DocumentationRuntimeContradiction
```

Models must be typed and serializable.

---

## 4. Required enums / controlled vocabularies

Implement enums for:

```text
CapabilityStatus
ProbeRunStatus
ProbeFailureClass
EvidenceLevel
PITReadiness
ProviderRole
RedundancyClass
AccessMode
QueryMode
HistoricalBoundaryConfidence
```

Reuse Bloc 1 enums where already defined; do not duplicate semantics under new names.

---

## 5. Probe-provider interface

Each provider probe module should satisfy a small interface similar to:

```python
class ProviderCapabilityProbe(Protocol):
    provider_id: ProviderId

    def list_probe_instruments(...) -> ...: ...
    def build_probe_request(...) -> ...: ...
    def execute_probe(...) -> CapabilityProbeEvidence: ...
    def classify_failure(...) -> ProbeFailureClass: ...
    def summarize_native_schema(...) -> ...: ...
```

Provider-specific query construction stays below this boundary.

---

## 6. No production-adapter overbuild

Bloc 2 provider modules may contain:

- endpoint/file URLs,
- request parameter construction,
- minimal pagination sufficient to characterize behavior,
- payload summarization,
- schema fingerprinting,
- timestamp/unit field extraction.

They must NOT yet contain:

- full historical backfill engine,
- raw lake partitioning,
- canonical T1 conversion,
- derived mechanical features,
- live stream recorder,
- cross-venue synthesis.

Those are later blocs.

---

## 7. Network isolation in tests

Unit tests must not depend on live provider availability.

Use frozen fixtures for:

```text
successful payload
empty historical payload
404/unsupported
401/auth
429/rate limit
schema change
pagination cursor
archive index
corrupt file metadata
```

Live probes belong to an explicit integration command, not default unit test execution.

---

## 8. Core model tests

Required tests:

### T2-MODEL-01
`CapabilityProbeRequest` validates canonical dimensions.

### T2-MODEL-02
Invalid provider/sensor/granularity enum fails closed.

### T2-MODEL-03
Evidence serialization is deterministic for identical normalized content.

### T2-MODEL-04
Secret-bearing headers/params are redacted from evidence.

### T2-MODEL-05
Failed probes still emit an evidence object.

### T2-MODEL-06
Unattempted is not serialized as unsupported.

---

## 9. Historical checkpoint tests

### T2-HIST-01
Default checkpoint config contains 2021/2022/2024/2026 + recent control.

### T2-HIST-02
A pre-listing instrument emits `PRE_LISTING`, not provider failure.

### T2-HIST-03
A current-only success plus old-history failure resolves to `VERIFIED_CURRENT_ONLY` or `HISTORY_BLOCKED`, not `UNSUPPORTED`.

### T2-HIST-04
Earliest verified history is never earlier than successful evidence supports.

### T2-HIST-05
Claimed history and verified history remain separate fields.

---

## 10. Pagination/archive tests

### T2-PAGE-01
Cursor pagination terminates deterministically.

### T2-PAGE-02
Repeated cursor is classified `F_PAGINATION_LOOP`.

### T2-PAGE-03
Truncated page history is detected when target window cannot be reached.

### T2-PAGE-04
Archive file listing can be summarized without downloading complete history.

### T2-PAGE-05
Checksum mismatch emits `F_CHECKSUM_FAILURE`.

---

## 11. Timestamp/unit semantic tests

### T2-SEM-01
Known event-time payload maps timestamp metadata correctly.

### T2-SEM-02
Ambiguous timestamp fixture cannot become `PIT_READY`.

### T2-SEM-03
Unknown OI native unit cannot become normalization-ready.

### T2-SEM-04
Predicted funding and realized funding are distinguished.

### T2-SEM-05
Orderbook snapshot and orderbook event-stream semantics remain distinct.

### T2-SEM-06
Trade liquidation flag does not automatically map as exact-equivalent interval liquidation volume.

---

## 12. Free-only gate tests

### T2-FREE-01
Paid subscription required -> `PAYMENT_BLOCKED`.

### T2-FREE-02
Payment method required -> hard fail for required-runtime eligibility.

### T2-FREE-03
Staking required -> hard fail.

### T2-FREE-04
Transaction required -> hard fail for data ingestion.

### T2-FREE-05
Free API key with no payment may remain eligible.

### T2-FREE-06
Unknown pricing/access cannot be promoted from `UNVERIFIED`.

---

## 13. Failure-class tests

Fixture-driven classification for:

```text
geo block
auth failure
payment block
429
500
404 endpoint removed
symbol missing
history truncation
schema change
timeout
checksum failure
corrupt payload
```

Every failure must map to one controlled class and retain redacted provider-native detail.

---

## 14. Coverage/scoring tests

### T2-COV-01
Coverage vector calculated per provider/sensor scope.

### T2-COV-02
Hard blocker overrides high composite score.

### T2-COV-03
R2 requires two independent verified sources, not two aliases of same feed.

### T2-COV-04
Unverified source does not increment redundancy.

### T2-COV-05
Community archive increments corroboration diversity but is not silently counted as first-party venue truth.

### T2-COV-06
Provider role is sensor-specific.

---

## 15. Documentation/runtime contradiction tests

### T2-CONTRA-01
Docs claim + runtime mismatch emits contradiction record.

### T2-CONTRA-02
Blocking contradiction prevents production-adapter promotion.

### T2-CONTRA-03
Later evidence may supersede claim but cannot erase prior contradiction/evidence.

---

## 16. Probe planner tests

### T2-PLAN-01
Planner creates recent control before deep-history requests.

### T2-PLAN-02
Hard recent-control failure suppresses wasteful deep-history spam where appropriate.

### T2-PLAN-03
Historical boundary search stops at configured month/quarter precision.

### T2-PLAN-04
Provider-specific unsupported granularity does not generate invalid requests.

### T2-PLAN-05
Probe plan is deterministic from config + provider capability hints.

---

## 17. Report tests

Generate fixtures for:

```text
provider_coverage_matrix.csv
provider_capability_claims.jsonl
probe_evidence.jsonl
probe_failures.jsonl
provider_coverage_report.md
sensor_gap_matrix.csv
source_promotion_candidates.yaml
```

### T2-REPORT-01
CSV contains no secrets.

### T2-REPORT-02
JSONL is parseable and one-record-per-line.

### T2-REPORT-03
Markdown report derives claims from evidence IDs.

### T2-REPORT-04
Coverage report never labels unattempted cells unsupported.

---

## 18. Provider fixture minimums

Before live probing, every provider probe module needs at least:

```text
1 success fixture
1 failure/empty fixture
1 pagination/archive fixture where relevant
```

Providers with materially different sensor payloads should have sensor-specific fixtures.

---

## 19. Live smoke command

Implementation should expose a safe explicit command, e.g. conceptually:

```text
sensor-probe run --provider kraken --sensor open_interest --instrument BTC --checkpoint recent
```

and matrix mode:

```text
sensor-probe run-plan --config config/.../probe_targets.yaml
```

No exact CLI syntax is frozen, only the operational behavior.

---

## 20. Live-probe safety

Default live settings:

```text
concurrency = low
retry_count = conservative
respect Retry-After
request timeout bounded
no credential logging
no geo bypass
no paid endpoint fallback
```

Never automatically retry a payment/geo/auth block as if it were transient.

---

## 21. Staged implementation commits

The eventual build agent must use granular commits.

### `SENSOR-B2-I01 probe-core-models`

Implement:
- request/evidence/claim models,
- enums,
- failure classes,
- deterministic serialization,
- redaction.

Tests:
- model + free-only + failure basics.

### `SENSOR-B2-I02 probe-planner-and-runner`

Implement:
- historical checkpoint planner,
- recent-control-first logic,
- bounded history search,
- probe runner lifecycle.

Tests:
- planner/pagination lifecycle.

### `SENSOR-B2-I03 probe-evidence-and-coverage`

Implement:
- immutable evidence writer,
- coverage vector,
- evidence levels,
- redundancy classes,
- capability scoring,
- contradiction records.

### `SENSOR-B2-I04 kraken-capability-probe`

Implement minimal Kraken probe module + fixtures + provider report support.

### `SENSOR-B2-I05 gate-capability-probe`

Gate module + fixtures.

### `SENSOR-B2-I06 binance-capability-probe`

REST/archive probe module + fixtures.

### `SENSOR-B2-I07 bybit-capability-probe`

Bybit module + fixtures.

### `SENSOR-B2-I08 okx-capability-probe`

OKX historical query/archive module + fixtures.

### `SENSOR-B2-I09 deribit-capability-probe`

Deribit timestamp/sequence module + liquidation semantic fixtures.

### `SENSOR-B2-I10 coinalyze-capability-probe`

Free-key/retention module + fixtures.

### `SENSOR-B2-I11 bitfinex-archive-capability-probe`

Community archive/license/schema/hash probe + fixtures.

### `SENSOR-B2-I12 report-and-gap-matrix`

Implement all human/machine report outputs.

### `SENSOR-B2-I13 live-capability-evidence-run`

Run approved low-rate live matrix.
Commit **evidence summaries/manifests only**, not raw bulk market data or secrets.

### `SENSOR-B2-I14 provider-role-decision-packet`

Freeze:
- provider/sensor capability claims,
- source roles,
- excluded/limited sources,
- sensor redundancy classes,
- adapter promotion candidates.

No Bloc 3 code yet.

---

## 22. Commit discipline

Every provider commit must include:

```text
provider probe code
fixtures
tests
docstring/source references
expected capability report fields
```

Do not implement all providers in one commit.

If a provider fails, commit the failure-supporting probe and evidence handling anyway.

Failure is an architectural result.

---

## 23. Required implementation evidence packet

Before human review, generate:

```text
01_PROBE_RUN_MANIFEST.md
02_PROVIDER_COVERAGE_MATRIX.csv
03_SENSOR_GAP_MATRIX.csv
04_PROVIDER_ROLE_RECOMMENDATIONS.md
05_BLOCKING_CONTRADICTIONS.csv
06_FREE_ONLY_AUDIT.csv
07_PIT_READINESS_MATRIX.csv
08_HISTORY_BOUNDARIES.csv
09_SCHEMA_FINGERPRINTS.jsonl
10_CAPABILITY_CLAIMS.jsonl
11_FAILURES.jsonl
12_BLOC_02_IMPLEMENTATION_DECISION.md
```

Exact numbering may vary if repository conventions require, but content is mandatory.

---

## 24. Acceptance gates

### GATE B2-A — Contract gate

PASS only if all probe evidence maps to Bloc 1 contracts without bypassing provider identity or missingness semantics.

### GATE B2-B — Test gate

PASS only if unit/fixture suite passes with no live network dependency.

### GATE B2-C — Free-only gate

PASS only if no production-adapter candidate requires paid subscription/payment/staking/transaction.

### GATE B2-D — Recent-control gate

Every promoted provider/sensor pair has at least one successful recent runtime/archive verification.

### GATE B2-E — Historical-characterization gate

Every historical-adapter candidate has characterized earliest history and target-era behavior.

### GATE B2-F — PIT gate

Every PIT-ready candidate has timestamp semantics explicit enough for replay.

### GATE B2-G — Unit gate

Native quantity/rate units are known or candidate is demoted.

### GATE B2-H — Reproducibility gate

Capability claim references immutable evidence and rerunnable normalized request specification.

### GATE B2-I — Redundancy report gate

Critical sensors receive R0/R1/R2/R3 classification based on independent verified evidence.

### GATE B2-J — Human review gate

No provider is automatically authorized for production adapter build.

---

## 25. Fail-closed conditions

Bloc 2 cannot claim COMPLETE if:

- provider history was inferred from docs only,
- timestamps remain ambiguous for promoted PIT source,
- native units remain unknown,
- secrets appear in evidence,
- unattempted cells are marked unsupported,
- community source is mislabeled first-party,
- paid source is silently accepted,
- evidence cannot reproduce the claim,
- provider identities are merged.

---

## 26. Bloc 2 implementation verdicts

Possible final verdicts:

```text
PASS_BLOC_02_CAPABILITY_MAP
PASS_BLOC_02_WITH_SENSOR_GAPS
PASS_BLOC_02_FREE_ONLY_REDUNDANCY
PARTIAL_BLOC_02_TRANSIENT_BLOCKERS
FAIL_BLOC_02_EVIDENCE_NOT_REPRODUCIBLE
FAIL_BLOC_02_FREE_ONLY_VIOLATION
```

A `PASS_BLOC_02_WITH_SENSOR_GAPS` is acceptable.

The fabric is designed to survive missing providers.

---

## 27. Handoff to Bloc 3

Bloc 3 may only plan/build production adapters for provider/sensor pairs listed in the final `source_promotion_candidates` packet.

Bloc 3 must inherit:

```text
capability status
earliest verified history
sensor role
access mode
PIT readiness
semantic equivalence class
known gaps
rate-limit behavior
provider-specific hazards
```

No Bloc 3 developer may re-assume capabilities from documentation.

---

## 28. Final planning decision

`BLOC_02_TESTS_COMMITS_AND_GATES_READY`

The build path is now decomposed into independently reviewable commits with unit/integration boundaries, fail-closed acceptance gates, provider-by-provider evidence and a strict handoff contract into production adapter work.

`human_review_required = TRUE`
`implementation_authorized = FALSE`
