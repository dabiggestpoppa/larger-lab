# BLOC 12 — FINAL ACCEPTANCE SUITE + STAGED IMPLEMENTATION COMMITS

## 1. Purpose

Define the execution history for the final certification layer.

Bloc 12 implementation must remain auditable. Do not collapse full-stack validation into one commit.

---

## 2. Planned implementation tree

```text
quant-lab/src/crypto_sensor_fabric/validation/
  __init__.py
  models.py
  gates.py
  registry.py
  runner.py
  evidence.py
  cost_audit.py
  capability_audit.py
  lineage_audit.py
  pit_audit.py
  quality_audit.py
  coverage_audit.py
  live_audit.py
  observable_audit.py
  service_audit.py
  replay_audit.py
  market_os_audit.py
  adversarial/
    transport.py
    storage.py
    identity.py
    semantics.py
    redundancy.py
    backfill.py
    live.py
    replay.py
  readiness/
    scoring.py
    event_overlap.py
    null_burden.py
    research_policy.py
  packets/
    common.py
    mech21.py
    lf14.py
    receipts.py
  reports/
    markdown.py
    json_report.py
    matrices.py

quant-lab/tests/crypto_sensor_fabric/validation/
  test_gate_registry.py
  test_cost_audit.py
  test_capability_reprobe.py
  test_end_to_end_lineage.py
  test_as_known_then.py
  test_revision_isolation.py
  test_free_only.py
  test_quality_monotonicity.py
  test_source_independence.py
  test_historical_resume.py
  test_live_failures.py
  test_observable_parity.py
  test_sensor_service_offline.py
  test_replay_determinism.py
  test_market_os_bridge.py
  test_null_boundaries.py
  test_mech21_packet.py
  test_lf14_packet.py
```

Evidence outputs:

```text
quant-lab/research/crypto_foundry/sensor_validation/final/
```

Actual large data/evidence blobs remain outside Git.

---

## 3. Required test classes

### A. CONTRACT TESTS

- gate IDs unique;
- all frozen blocs represented;
- schemas validate;
- verdict enums closed;
- no implicit defaults that upgrade quality/readiness.

### B. FREE-ONLY TESTS

- paid classifications rejected;
- requester-pays rejected;
- trading key requirements rejected;
- payment/staking/transaction requirements rejected;
- access-policy drift triggers review.

### C. PROVENANCE TESTS

Randomly sample T2 values and traverse:

```text
T2 → T1 → T0B → acquisition → T0A hash
```

Require closure.

### D. PIT / LEAKAGE TESTS

Construct fixtures where future knowledge exists and verify it does not enter `AS_KNOWN_THEN`.

Attack:
- future revisions;
- future identity aliases;
- future delisting knowledge;
- future stablecoin prices;
- future provider-quality state;
- future baseline samples.

### E. SEMANTIC TESTS

Golden fixtures for:
- liquidation side;
- OI units;
- funding intervals;
- aggressor side;
- book sequence;
- linear/inverse contract math.

### F. REDUNDANCY TESTS

- independence graph;
- aggregators;
- unknown dependencies;
- quorum downgrade;
- disagreement preservation;
- source loss.

### G. STORAGE / RESUME TESTS

- crash matrix;
- atomicity;
- manifest integrity;
- revision append;
- restore hash verification;
- cursor advancement ordering.

### H. BACKFILL TESTS

- deterministic shard IDs;
- PIT universe clipping;
- partial history;
- gap repair;
- source mutation;
- rate deferral;
- disk deferral;
- event-window coverage.

### I. LIVE TESTS

- disconnect;
- silent stall;
- heartbeat distinction;
- sequence gap;
- checksum failure;
- restart;
- machine downtime;
- disk pressure;
- gap repair request.

### J. T2 TESTS

- venue-local first;
- cross-venue eligibility;
- coverage denominator;
- physical + standardized amplitude;
- static + rolling windows;
- insufficient baseline support;
- immutable generation.

### K. SERVICE TESTS

- offline mode;
- network monkeypatch hard-fail;
- read-only filesystem/db permission test;
- generation pin;
- typed missingness;
- lineage receipt;
- deterministic response hash.

### L. REPLAY TESTS

- repeated replay same hash;
- generation-lock test;
- later revision isolation;
- NullBoundary;
- PIT universe;
- shadow-live equivalence.

### M. MARKET OS TESTS

Validate runtime objects:

```text
FieldSnapshot
PatchSnapshot
RelationalSnapshot
LifecycleSnapshot
ConstraintSnapshot
ShockSnapshot
ResearchEvidence
NullBoundary
```

No forbidden strategy/execution fields.

### N. RESEARCH PACKET TESTS

MECH-21 and LF14 dry runs using only canonical sensor service/replay interfaces.

No provider-native imports allowed.

---

## 4. Mandatory sentinel periods

Final validation must include, subject to real coverage:

```text
2021 high-activity sample
2022 stress sample
2024 ordinary/regime sample
2026 recent sample
quiet-period control
```

Each major available mechanical family should be checked across multiple eras rather than only current data.

---

## 5. Live certification duration

Minimum functional pilot:

```text
24 continuous hours
```

Preferred resilience certification:

```text
72 hours
```

Must include forced failures during the pilot.

A clean 72h run without failure injection does not satisfy the adversarial requirement.

---

## 6. Performance / scale checks

This is not an HFT latency target.

Validate instead:
- bounded memory under historical replay;
- bounded live queues;
- deterministic streaming compilation;
- DuckDB scan practicality;
- service query latency by scope;
- disk growth vs forecast;
- restart time;
- backfill throughput under rate budgets.

Performance optimization cannot weaken evidence semantics.

---

## 7. Staged implementation commits

The execution agent must use the following granular sequence unless a dependency forces an even smaller split.

```text
SENSOR-B12-I01  validation models / enums / gate classes
SENSOR-B12-I02  gate registry covering Blocs 1–11
SENSOR-B12-I03  validation evidence / receipt model
SENSOR-B12-I04  final validation runner / run manifest
SENSOR-B12-I05  free-only / access / governance audit
SENSOR-B12-I06  capability re-probe audit integration
SENSOR-B12-I07  provider adapter certification checks
SENSOR-B12-I08  T0 provenance / hash / manifest audit
SENSOR-B12-I09  T0 crash / atomicity certification
SENSOR-B12-I10  T1 PIT identity audit
SENSOR-B12-I11  T1 semantic golden-fixture audit
SENSOR-B12-I12  historical revision / AS_KNOWN_THEN leakage audit
SENSOR-B12-I13  source independence / dependency audit
SENSOR-B12-I14  quality / degraded-mode / failover audit
SENSOR-B12-I15  historical shard / resume certification
SENSOR-B12-I16  historical ragged coverage / event-overlap audit
SENSOR-B12-I17  live transport / heartbeat failure drills
SENSOR-B12-I18  live sequence / reconnect / gap certification
SENSOR-B12-I19  disk-pressure / machine-restart live drills
SENSOR-B12-I20  T2 venue-local observable certification
SENSOR-B12-I21  T2 cross-venue eligibility / breadth / consensus certification
SENSOR-B12-I22  static / rolling baseline certification
SENSOR-B12-I23  historical-live T2 compiler parity
SENSOR-B12-I24  read-only sensor-service offline certification
SENSOR-B12-I25  sensor-service generation / lineage / failure contracts
SENSOR-B12-I26  deterministic replay certification
SENSOR-B12-I27  shadow-live replay equivalence certification
SENSOR-B12-I28  Market OS runtime-object bridge certification
SENSOR-B12-I29  NullBoundary / DATA_BLOCKED propagation certification
SENSOR-B12-I30  scope-aware research readiness engine
SENSOR-B12-I31  sign-conditional / event-stage null-burden reporting
SENSOR-B12-I32  MECH-21 restart packet generator
SENSOR-B12-I33  LF14 restart packet generator
SENSOR-B12-I34  MECH-21 / LF14 no-provider-code dry runs
SENSOR-B12-I35  whole-stack adversarial regression suite
SENSOR-B12-I36  final human-readable + machine-readable certification report
SENSOR-B12-I37  final system manifest / research restart recommendation
SENSOR-B12-I38  master implementation handoff evidence packet
```

No squashing during review.

---

## 8. Commit checkpoint requirements

Every staged commit should record:
- tests added;
- tests passed/failed;
- evidence artifacts generated;
- blocking issues;
- cost state;
- data mutations;
- network interactions if any;
- next authorized implementation checkpoint.

The implementation agent must stop on any G0 failure.

---

## 9. Final acceptance evidence

Required summary artifact:

```text
FINAL_SENSOR_FABRIC_CERTIFICATION.md
FINAL_SENSOR_FABRIC_CERTIFICATION.json
```

Required sections:
1. branch / commit / versions;
2. cost audit;
3. provider matrix;
4. sensor coverage;
5. independent redundancy;
6. PIT certification;
7. lineage certification;
8. live certification;
9. replay certification;
10. Market OS compatibility;
11. research readiness;
12. unresolved DATA_BLOCKED regions;
13. restart recommendation;
14. human approval field.

---

## 10. Stop gate

Bloc 12 implementation ends after certification + restart recommendation.

It must NOT automatically launch MECH-21 or LF14.

Final state remains:

```text
human_review_required = TRUE
next_checkpoint_authorized = FALSE
```
