# BLOC 11 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

## 1. Objective

Provide an implementation-grade execution sequence and hard gates for Historical Replay + Market OS Bridge.

The future implementation agent must build in the exact staged order below and must not squash commits during operator review.

---

## 2. Planned implementation tree

```text
quant-lab/src/crypto_sensor_fabric/
  replay/
    models.py
    clock.py
    plan.py
    generations.py
    universe.py
    compiler.py
    checkpoints.py
    event_context.py
    comparison.py
    parity.py
    exports.py
    receipts.py

  market_os_bridge/
    schemas.py
    field.py
    patch.py
    lifecycle.py
    constraint.py
    shock.py
    evidence.py
    null_boundary.py
    compiler.py

  research_bridge/
    mech21.py
    lower_field14.py
    packet.py
    eligibility.py

quant-lab/tests/crypto_sensor_fabric/replay/
quant-lab/tests/crypto_sensor_fabric/market_os_bridge/
quant-lab/tests/crypto_sensor_fabric/research_bridge/
```

No provider adapters are imported into these packages.

---

## 3. Staged implementation commits

### `SENSOR-B11-I01` — replay models / enums

Implement:
- `ReplayPlan`
- `ReplayFrame`
- `ReplayRunManifest`
- replay/status enums
- deterministic serialization.

Gate: schema tests pass.

### `SENSOR-B11-I02` — generation lock set

Implement full version/generation pinning and hash.

Gate: run cannot start with unresolved generation.

### `SENSOR-B11-I03` — replay clock

Implement fixed, event-driven, hybrid and single-snapshot clocks.

Gate: UTC/boundary tests.

### `SENSOR-B11-I04` — AS_KNOWN_THEN resolver

Implement historical knowledge cutoff semantics using Bloc 5/10 contracts.

Gate: later revision leakage test must fail closed.

### `SENSOR-B11-I05` — latest/exact revision modes

Implement `LATEST_RECONSTRUCTED` and `EXACT_GENERATION` separately.

Gate: no implicit mode switching.

### `SENSOR-B11-I06` — PIT universe resolver

Implement lifecycle-aware universe snapshots.

Gate: listing/delisting golden tests.

### `SENSOR-B11-I07` — baseline eligibility

Audit fixed/expanding/rolling/post-hoc baseline validity under PIT modes.

Gate: future-informed baseline blocked.

### `SENSOR-B11-I08` — canonical sensor service client boundary

Implement local read-only client wrapper against Bloc 10.

Gate: dependency test proves no provider/network imports.

### `SENSOR-B11-I09` — frame compiler

Compile venue-local and cross-venue T2 states into `MechanicalSnapshot`.

Gate: null/missing coordinates preserved.

### `SENSOR-B11-I10` — static temporal views

Implement 1D/3D/7D/14D/30D/60D static retrieval/packaging.

### `SENSOR-B11-I11` — rolling temporal views

Implement 3D/7D/14D/30D and support-gated 60D rolling views.

Gate: static/rolling disagreement remains visible.

### `SENSOR-B11-I12` — transition packaging

Package Bloc 9 state transitions, age, persistence and velocity.

Gate: replay does not infer causal labels.

### `SENSOR-B11-I13` — event anchor registry interface

Read approved research event anchors.

Gate: stage/event labels require source artifact/version.

### `SENSOR-B11-I14` — event context compiler

Build `MechanicalEventContext` with pre/post windows.

### `SENSOR-B11-I15` — distribution summaries

Expose p25/p50/p75/p90/n/coverage where supported.

Gate: median-only collapse test.

### `SENSOR-B11-I16` — neutral event comparison helper

Implement prespecified-coordinate comparisons without feature selection/target optimization.

Gate: API has no target/predictive optimization interface.

### `SENSOR-B11-I17` — replay checkpoint/resume

Implement durable frame-level checkpoints and run manifests.

Gate: mixed-generation resume blocked.

### `SENSOR-B11-I18` — deterministic export/checksum

Implement canonical export ordering and checksums.

Gate: repeated run byte-stable except declared metadata.

### `SENSOR-B11-I19` — Market OS common schemas

Implement runtime object envelope and schema versions.

### `SENSOR-B11-I20` — Field/Patch bridge

Compile mechanical global/local states into `FieldSnapshot` / `PatchSnapshot`.

Gate: global/local distinction preserved.

### `SENSOR-B11-I21` — Lifecycle/Constraint bridge

Compile transition/constraint state without directional prediction.

### `SENSOR-B11-I22` — Shock bridge

Compile shock-aligned mechanical context into `ShockSnapshot`.

Gate: shock timing is sourced, not invented.

### `SENSOR-B11-I23` — Evidence/NullBoundary bridge

Implement `ResearchEvidence` and `NullBoundary` with full reasons/lineage.

### `SENSOR-B11-I24` — scientific status preservation

Enforce no automatic DESCRIPTIVE/LOCAL/PROMOTED/PARKED/NULL upgrades.

Gate: attempted upgrade fails.

### `SENSOR-B11-I25` — shadow-live compiler

Compile finalized live intervals through the same state/bridge semantics.

### `SENSOR-B11-I26` — historical vs shadow parity harness

Build parity packets and field-level diffs.

Gate: semantic or quality mismatch blocks.

### `SENSOR-B11-I27` — MECH-21 research packet

Implement global-response-law mechanical context export.

### `SENSOR-B11-I28` — LF14 research packet

Implement matched-event mechanical context, missingness and exclusion-accounting export.

### `SENSOR-B11-I29` — adversarial scientific-integrity suite

Test future leakage, current-universe leakage, revision ambiguity, blocked data, asymmetric missingness, generation drift and null coercion.

### `SENSOR-B11-I30` — performance / bounded-memory replay

Validate partition pruning, streaming and resumability on multi-era sample.

Performance changes cannot alter result checksums.

### `SENSOR-B11-I31` — full acceptance evidence packet

Generate all required reports and golden outputs.

### `SENSOR-B11-I32` — Bloc 12 handoff

Freeze implementation evidence and expose validation interfaces needed by final system-wide audit.

---

## 4. Core acceptance gates

### G1 — PIT / no-future gate

Must prove:
- later revisions excluded in `AS_KNOWN_THEN`;
- future listings absent;
- future baselines absent;
- future conversion observations absent.

**Blocking.**

### G2 — generation determinism

Exact generation set + plan produces reproducible results.

**Blocking.**

### G3 — T2 lineage

Every populated state resolves to Bloc 10/T2 → T1 → T0 evidence.

**Blocking.**

### G4 — null fidelity

Missing/blocked observations remain null/blocked.

No zero-fill or stale carry-forward.

**Blocking.**

### G5 — static + rolling

Research packet contains both required temporal perspectives wherever supported.

### G6 — cross-venue quality

Breadth/consensus/dispersion preserve coverage, independence and source eligibility.

### G7 — Market OS status fidelity

Bridge cannot change scientific status.

**Blocking.**

### G8 — historical/live parity

Finalized shadow-live and historical replay converge under same generations/interval.

Semantic or quality mismatch is **blocking**.

### G9 — read-only boundary

No provider/network/order/execution dependencies.

**Blocking.**

### G10 — research packet integrity

MECH/LF packet exposes exclusions, missingness and quality rather than silently filtering.

---

## 5. Golden replay scenarios

At minimum:

### Scenario A — 2022 stress

BTC + ETH + one supported alt.

Must include available:
- liquidation;
- OI;
- funding;
- flow;
- liquidity;
- cross-venue states.

### Scenario B — 2024 ordinary period

Tests non-stress mechanics and no false extreme compression.

### Scenario C — 2026 recent period

Tests newest provider/schema paths and historical/live parity.

### Scenario D — listing boundary

Asset/contract launches inside replay range.

### Scenario E — source revision

Same historical boundary has two source revisions.

### Scenario F — ragged coverage

One venue missing while other independent venues remain usable.

### Scenario G — blocked sensor

Depth or liquidation unavailable and `NullBoundary` emitted.

---

## 6. Event-context validation

For LF14-style events, validate:

```text
PRE-SHOCK
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
```

against externally supplied stage labels.

Required evidence:
- no invented stage;
- exact event-anchor lineage;
- mechanical state matrix;
- rate/reach distribution summaries where provided;
- static/rolling views;
- inclusion/exclusion counts;
- sign-group missingness comparison.

---

## 7. Parity tolerance registry

Numerical tolerances must be versioned by field/method.

Examples:
- exact integer/count fields: exact match;
- decimal conversion fields: fixed epsilon;
- quantiles: deterministic algorithm/version;
- floating rolling statistics: declared absolute/relative tolerance.

No blanket `allclose` tolerance across the system.

---

## 8. Evidence outputs

Bloc 11 implementation must produce:

```text
REPLAY_ACCEPTANCE_REPORT.md
PIT_LEAKAGE_TEST_REPORT.md
GENERATION_DETERMINISM_REPORT.md
LINEAGE_CLOSURE_REPORT.md
NULL_BOUNDARY_REPORT.md
STATIC_ROLLING_COMPLETENESS.csv
MARKET_OS_SCHEMA_VALIDATION.json
SHADOW_LIVE_PARITY_REPORT.md
MECH21_PACKET_FIXTURE/
LF14_PACKET_FIXTURE/
REPLAY_GOLDEN_CHECKSUMS.json
BLOC_11_IMPLEMENTATION_MANIFEST.json
```

---

## 9. Stop gate

Bloc 11 implementation must stop with failure if any of these remain unresolved:

```text
future leakage
mixed generations
lineage break
silent null coercion
status promotion by bridge
historical/live semantic mismatch
provider/network dependency in replay service
research packet silent sample filtering
```

Partial provider coverage is not itself a failure when represented honestly.

---

## 10. Handoff rule

Passing Bloc 11 means:

```text
historical replay / Market OS bridge = implementation-ready or implemented and validated
```

It does **not** mean:

```text
MECH-21 / LF14 restart authorized
```

Only Bloc 12 can issue the final research-restart authorization.