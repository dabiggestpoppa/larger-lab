# BLOC 12 — FULL VALIDATION + RESEARCH RESTART ARCHITECTURE

**Planning status:** FINAL SYSTEM VALIDATION BOOK  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Upstream:** Blocs 1–11 frozen  
**Purpose:** certify the Crypto Mechanical Sensor Fabric as a coherent research substrate before MECH-21 / LOWER-FIELD-14 resume.

---

## 1. Mission

Bloc 12 is not another feature layer. It is the system-wide proving ground.

The final build must demonstrate that the chain:

```text
PROVIDER CLAIM
→ VERIFIED CAPABILITY
→ ADAPTER ACQUISITION
→ T0 EXACT EVIDENCE
→ T1 PIT NORMALIZATION
→ QUALITY / REDUNDANCY
→ HISTORICAL BACKFILL
→ LIVE RECORDER
→ T2 MECHANICAL STATE
→ READ-ONLY SENSOR SERVICE
→ HISTORICAL REPLAY
→ MARKET OS BRIDGE
→ RESEARCH PACKET
```

is internally consistent, reproducible, fail-closed and scientifically honest.

No research restart is allowed merely because individual modules pass unit tests.

---

## 2. Global validation doctrine

### 2.1 Hard invariants

The final stack MUST preserve:

1. **$0 required data subscription cost.**
2. **No payment-method, staking, transaction or premium-feed requirement.**
3. **No provider is canonical truth.**
4. **Provider identity is never erased.**
5. **No silent semantic equivalence.**
6. **No silent zero fill.**
7. **No future leakage in `AS_KNOWN_THEN`.**
8. **No silent latest-revision substitution in historical replay.**
9. **No synthetic provider failover impersonation.**
10. **No destructive rewrite of T0 evidence.**
11. **No cross-venue aggregation without Bloc 6 eligibility.**
12. **No live/historical semantic divergence.**
13. **No strategy, PnL, sizing, leverage, order placement or deployment logic.**
14. **No research promotion by infrastructure code.**
15. **NULL / DATA_BLOCKED remain first-class outputs.**

### 2.2 Final validation outputs

Implementation must produce:

```text
SystemValidationRun
ValidationGateResult
ValidationEvidenceRef
FailureInjectionResult
CostAudit
ProviderCapabilityAudit
T0IntegrityAudit
T1PITAudit
QualityRedundancyAudit
HistoricalCoverageAudit
LiveRecorderAudit
T2ObservableAudit
SensorServiceAudit
ReplayDeterminismAudit
MarketOSBridgeAudit
ResearchReadinessAudit
ResearchRestartPacket
FinalSystemManifest
```

Every verdict must be machine-readable and human-readable.

---

## 3. Final system verdicts

Only the following system-wide states are legal:

```text
PASS_FULL
PASS_DEGRADED_DECLARED
RESEARCH_LOCAL_ONLY
DATA_BLOCKED
VALIDATION_FAILED
```

### PASS_FULL
All blocking gates pass and required research scopes satisfy declared redundancy/coverage requirements.

### PASS_DEGRADED_DECLARED
Core stack is valid but one or more provider/sensor regions operate under explicit degraded quality. Research packets must carry those limitations.

### RESEARCH_LOCAL_ONLY
Infrastructure is valid but cross-venue or multi-era support is insufficient for global claims. Local/venue-specific research may proceed.

### DATA_BLOCKED
Required mechanical families cannot support the requested research scope.

### VALIDATION_FAILED
A system invariant is broken: PIT leak, lineage break, evidence mutation, semantic drift, replay nondeterminism, free-only violation, etc.

`VALIDATION_FAILED` blocks research restart.

---

## 4. Validation layers

### V0 — GOVERNANCE / COST / ACCESS

Validate:
- free-only policy;
- no trading credentials;
- no execution path;
- no hidden paid dependency;
- provider access classifications;
- provenance of all external dependencies.

### V1 — CAPABILITY TRUTH

Validate Bloc 2 claims against actual executed probes and evidence:
- 2021 / 2022 / 2024 / 2026 checkpoints;
- recent control;
- historical depth;
- granularity;
- units;
- pagination;
- rate limits;
- auth requirements;
- geo/access failures.

### V2 — ACQUISITION / T0

Validate:
- exact bytes;
- SHA-256 identity;
- source mutation preservation;
- atomic writes;
- resume-after-durability;
- manifest integrity;
- quarantine behavior.

### V3 — PIT IDENTITY / T1

Validate:
- contract lifecycle;
- symbol history;
- linear/inverse contracts;
- base/quote/settlement;
- multipliers;
- OI/funding/liquidation/flow/book semantics;
- stablecoin conversion PIT rules;
- T1→T0 lineage;
- duplicate handling;
- generation immutability.

### V4 — QUALITY / REDUNDANCY

Validate:
- provider health vs sensor health;
- source dependency graph;
- aggregator double-count protection;
- semantic comparability;
- quorum;
- disagreement handling;
- degraded modes;
- failover routing;
- recovery hysteresis.

### V5 — HISTORICAL PROGRAM

Validate:
- deterministic shard graph;
- bounded pilot;
- restart/resume;
- typed ragged coverage;
- event-window coverage;
- source revisions;
- storage forecasts;
- deep-book controls;
- actual redundancy by era.

### V6 — LIVE RECORDER

Validate:
- WebSocket capture;
- REST polling;
- event/arrival times;
- heartbeat layers;
- sequence-gap detection;
- reconnect/resubscribe;
- machine reboot recovery;
- disk pressure;
- forward-gap registry;
- historical repair handoff.

### V7 — T2 OBSERVABLE FABRIC

Validate:
- venue-local states;
- cross-venue eligibility;
- physical + standardized magnitude;
- static and rolling windows;
- breadth / consensus / dispersion;
- versioned baseline registry;
- no universal stress-score leakage;
- historical/live compiler parity.

### V8 — SENSOR SERVICE

Validate:
- read-only behavior;
- local/offline operation;
- deterministic queries;
- generation pinning;
- `AS_KNOWN_THEN` correctness;
- quality/coverage/lineage response envelopes;
- no provider/network calls.

### V9 — REPLAY / MARKET OS

Validate:
- deterministic `mechanical_replay(t)`;
- PIT universe;
- generation locks;
- event-stage context;
- NullBoundary propagation;
- shadow-live equivalence;
- runtime object schema compatibility.

### V10 — RESEARCH RESTART

Validate that MECH-21 and LF14 can consume canonical mechanical packets without provider-specific code, future leakage or unsupported inference.

---

## 5. Evidence-first validation

Every passing gate must point to evidence.

A valid gate record includes:

```text
gate_id
system_run_id
bloc
component
scope
status
blocking
started_at
finished_at
input_versions
commands
fixture_refs
artifact_refs
metrics
warnings
failure_refs
review_notes
```

A green checkbox without a reproducibility receipt is invalid.

---

## 6. Final certification sequence

```text
FREE-ONLY AUDIT
        ↓
CAPABILITY RE-PROBE
        ↓
T0/T1 GOLDEN FIXTURE
        ↓
HISTORICAL PILOT
        ↓
LIVE 24H/72H PILOT + FAILURES
        ↓
T2 HISTORICAL/LIVE PARITY
        ↓
SENSOR SERVICE OFFLINE TEST
        ↓
REPLAY DETERMINISM / PIT LEAK TEST
        ↓
MARKET OS OBJECT BRIDGE
        ↓
MECH-21 / LF14 DRY-RUN PACKETS
        ↓
FINAL HUMAN REVIEW
```

No later stage can waive a failed earlier blocking gate.

---

## 7. Human authority

Final infrastructure state remains:

```text
human_review_required = TRUE
next_checkpoint_authorized = FALSE
```

The implementation agent may recommend a restart verdict, but only the operator authorizes MECH-21 / LF14 execution.

---

## 8. Out of scope

Bloc 12 does NOT authorize:
- strategy research;
- PnL optimization;
- signal generation;
- execution;
- portfolio construction;
- leverage;
- live order routing;
- alpha promotion;
- causal claims from mechanical data alone.

It certifies the measurement and replay substrate only.
