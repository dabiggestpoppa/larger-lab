# BLOC 6 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

**Planning status:** COMPLETE FOR THIS SUB-BLOC  
**Implementation status:** NOT STARTED

---

## 1. Objective

Freeze the implementation order, repository structure, evidence outputs and blocking acceptance gates for the quality/redundancy/failover control plane.

The execution agent must build Bloc 6 in small commits. No squash during review.

---

## 2. Planned implementation tree

```text
quant-lab/src/crypto_sensor_fabric/quality/
  __init__.py
  enums.py
  models.py
  expectations.py
  freshness.py
  gap_detection.py
  provider_health.py
  feed_health.py
  observation_health.py
  dependencies.py
  comparability.py
  quorum.py
  disagreement.py
  reconciliation.py
  quarantine.py
  scoring.py
  operating_mode.py
  routing.py
  failover.py
  recovery.py
  policy.py
  evidence.py

quant-lab/config/crypto_sensor_fabric/
  quality_policy.yaml
  redundancy_policy.yaml
  source_dependencies.yaml
  comparability_policy.yaml
  quorum_policy.yaml
  failover_routes.yaml
  recovery_policy.yaml

quant-lab/tests/crypto_sensor_fabric/quality/
  test_provider_health.py
  test_feed_health.py
  test_observation_health.py
  test_freshness.py
  test_gap_detection.py
  test_dependencies.py
  test_comparability.py
  test_quorum.py
  test_disagreement.py
  test_reconciliation.py
  test_quarantine.py
  test_scoring.py
  test_operating_modes.py
  test_routing.py
  test_failover.py
  test_recovery.py
  test_quality_lineage.py
  test_end_to_end_quality.py

quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_06/
  provider_health_summary.csv
  sensor_health_summary.csv
  dependency_graph_summary.csv
  quorum_matrix.csv
  disagreement_summary.csv
  failover_scenarios.csv
  blocked_windows.csv
  degraded_windows.csv
  T2_eligibility_summary.csv
  BLOC_06_VALIDATION.md
```

---

## 3. Fixture doctrine

Normal CI tests are offline.

Use deterministic fixtures derived from provider payload shapes already frozen in Blocs 2–5.

Fixtures must cover at minimum:

- BTC + ETH + one alt;
- U0 + U1/U2 scopes;
- liquidations;
- OI;
- funding;
- trades/order flow;
- book/depth;
- two first-party independent sources;
- one aggregator dependent on direct venues;
- one community archive;
- one provider outage;
- one stale feed;
- one semantic mismatch;
- one schema drift;
- one revision conflict;
- one valid-zero interval;
- one unknown-dependency case;
- one high-but-legitimate economic disagreement case.

---

## 4. Blocking acceptance gates

### G1 — Provider/sensor separation

Provider can be DOWN while unrelated provider sensors remain healthy.

One failed sensor/feed cannot automatically quarantine the whole provider.

### G2 — Explicit missingness

No zero-fill or generic missing boolean.

Valid zero, empty confirmed, gap, unsupported, not expected and blocked states remain distinct.

### G3 — Independence-aware redundancy

Aggregator/mirror sources cannot inflate independent quorum.

### G4 — Semantic comparability

Incompatible data cannot enter quorum/agreement/T2 eligibility.

### G5 — PIT preservation

Strict historical mode may use only observations and quality metadata valid under the configured as-known/as-observed replay policy.

### G6 — Failover provenance

Fallback coverage cannot erase provider or venue identity.

### G7 — No blind majority vote

Peer disagreement alone cannot auto-delete the outlier source.

### G8 — Degraded modes explicit

FULL / DEGRADED_REDUNDANT / DEGRADED_PARTIAL / RESEARCH_ONLY / DATA_BLOCKED are deterministic and auditable.

### G9 — Quality hard gates

A failed PIT/integrity/semantic gate cannot be averaged into a passing quality score.

### G10 — Scope awareness

Health and quorum are scoped by sensor, instrument/universe, time/granularity and use case.

### G11 — T2 boundary

Bloc 6 outputs eligibility and quality metadata only; no cross-venue economic feature formulas appear here.

### G12 — Versioned decisions

Quality policy, dependency graph, comparability registry and routing policy versions are stored with decisions.

Any failure G1–G12 blocks `PASS_BLOC_06_IMPLEMENTED`.

---

## 5. End-to-end adversarial scenarios

### Scenario A — Kraken down, sensor survives

Input:

- Kraken liquidation feed unavailable;
- Gate liquidation healthy;
- Deribit specialist liquidation evidence healthy;
- required policy allows Gate + second independent first-party source if present.

Expected:

- Kraken provider/feed marked down;
- no relabeling;
- canonical sensor mode reflects actual independent quorum;
- if only one independent broad source remains, do not fabricate R2.

### Scenario B — Fake redundancy through aggregator

Input:

- Binance OI;
- Bybit OI;
- Coinalyze aggregate containing Binance/Bybit.

Expected:

```text
raw_count = 3
independent_count = 2
```

Coinalyze may corroborate but does not create R3.

### Scenario C — High funding disagreement

Input:

- valid first-party funding observations with divergent rates.

Expected:

- high disagreement recorded;
- integrity/semantic checks pass;
- classify `HIGH_ECONOMIC_HETEROGENEITY`, not corrupt automatically.

### Scenario D — Unit bug

Input:

- one OI source accidentally interpreted contracts as BTC.

Expected:

- comparison/invariant checks detect impossible divergence;
- source sensor quarantined;
- other provider sensors unaffected;
- strict quorum recalculated.

### Scenario E — Unknown aggregator lineage

Input:

- third-party source with unknown upstream composition.

Expected:

- `RX_DEPENDENCY_AMBIGUOUS`;
- no strict independent quorum increment;
- source remains visible for corroboration.

### Scenario F — Strict 5m query with only daily fallback

Expected:

- no silent downgrade;
- strict query DATA_BLOCKED unless caller explicitly permits daily degraded mode.

### Scenario G — Valid zero

Provider explicitly reports zero liquidations for interval.

Expected:

```text
VALID_ZERO
```

not gap/missing.

### Scenario H — Pre-listing interval

Expected:

```text
NOT_EXPECTED
```

not historical gap.

### Scenario I — Recovery flapping

Provider alternates success/failure.

Expected:

- recovery hysteresis prevents constant primary/fallback switching;
- route and health transitions auditable.

### Scenario J — T1 revision ambiguity

Expected:

- strict replay blocked under `ERROR_ON_AMBIGUITY`;
- exploratory research may explicitly request all revisions/research-only path.

---

## 6. Property/invariant tests

Implementation should include property tests for:

```text
independent_count <= eligible_source_count <= raw_source_count

FULL implies all hard gates pass

DATA_BLOCKED cannot be upgraded downstream without new evidence

provider failover never changes venue_id of observation

NOT_COMPARABLE never appears in numeric comparison set

same upstream group cannot count twice for strict independence

quarantined observation cannot enter strict quorum

valid zero remains an observation

NOT_EXPECTED is excluded from denominator where policy says observation was not expected
```

---

## 7. Determinism gate

Given identical:

- T1 generation;
- provider health evidence;
- dependency graph version;
- quality policy;
- comparability registry;
- requested scope/use case;

Bloc 6 must produce identical:

- health states;
- source exclusions;
- quorum result;
- operating mode;
- failover route;
- quality flags.

---

## 8. Performance expectations

Quality evaluation must be cheap enough to run over large historical panels.

Design targets:

- vectorized/batch evaluation for historical coverage;
- incremental update for live health;
- no network access in quality calculations;
- no repeated raw-payload parsing once T1/health inputs exist;
- policy/config cache allowed but version-safe.

No premature microservice split.

---

## 9. Staged implementation commits

The future build agent should use this exact checkpoint sequence unless a genuine blocking contradiction is documented.

```text
SENSOR-B6-I01
  quality enums / core health models / operating modes

SENSOR-B6-I02
  observation expectation + freshness engine

SENSOR-B6-I03
  layered gap detection + missingness mapping

SENSOR-B6-I04
  provider/feed/observation health evaluators

SENSOR-B6-I05
  source dependency graph + independence collapse

SENSOR-B6-I06
  semantic comparability eligibility engine

SENSOR-B6-I07
  quorum policies + redundancy classes

SENSOR-B6-I08
  disagreement diagnostics + economic/data conflict classification

SENSOR-B6-I09
  cross-provider reconciliation + T2 eligibility

SENSOR-B6-I10
  quarantine / impossible-value controls

SENSOR-B6-I11
  quality vector + hard-gate engine

SENSOR-B6-I12
  operating-mode policy

SENSOR-B6-I13
  routing + failover decision engine

SENSOR-B6-I14
  provider recovery / anti-flap state machine

SENSOR-B6-I15
  config loaders + policy/version lineage

SENSOR-B6-I16
  Bloc 5 T1 integration + historical batch quality pass

SENSOR-B6-I17
  Bloc 3 live provider-health integration boundary

SENSOR-B6-I18
  evidence/report generation

SENSOR-B6-I19
  adversarial / property / determinism suite

SENSOR-B6-I20
  full Bloc 6 acceptance run

SENSOR-B6-I21
  Bloc 7 historical-backfill handoff packet
```

Every commit should remain individually reviewable.

---

## 10. Commit evidence requirements

Each implementation commit must update at least one of:

- tests;
- fixtures;
- evidence report;
- architecture/status manifest.

No giant code-only commit.

Provider-specific assumptions discovered during implementation must be documented in provider evidence, not hidden in code comments only.

---

## 11. Validation report

Final implementation report must answer:

1. Can one provider fail without taking down unrelated sensor families?
2. Can the system distinguish provider health from sensor health?
3. Does fake aggregator redundancy collapse correctly?
4. Does semantic incompatibility fail closed?
5. Are valid zeros preserved?
6. Are lifecycle-related non-expectations excluded correctly?
7. Are quality hard gates non-compensatory?
8. Are degraded operating modes deterministic?
9. Does failover preserve provider/venue identity?
10. Is disagreement preserved without forced consensus?
11. Can specialist/corroboration sources remain useful without inflating quorum?
12. Is T2 eligibility emitted without T2 economic aggregation?
13. Can all quality decisions be replayed from versioned inputs?
14. Are historical/live policies separate?
15. Is Bloc 7 ready to backfill against this quality plane?

---

## 12. Stop gate

Do not proceed into production historical backfill until Bloc 6 implementation later proves:

```text
PASS_QUALITY_GATES
PASS_INDEPENDENCE_GATES
PASS_FAILOVER_GATES
PASS_DEGRADED_MODE_GATES
PASS_T2_ELIGIBILITY_BOUNDARY
```

Planning verdict for this document:

`PASS_BLOC_06_TEST_PLAN_DEFINED`

`human_review_required = TRUE`
