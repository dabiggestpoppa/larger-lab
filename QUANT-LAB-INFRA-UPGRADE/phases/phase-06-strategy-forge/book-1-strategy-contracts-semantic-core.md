# Phase 6, Book 1 — Strategy Contracts and Semantic Core

> **Purpose:** Define the canonical strategy contract, family registry, expression language, and normalized semantic representation  
> **Input:** Approved Phase 5 candidate or pattern-hypothesis handoff  
> **Output:** Validated `StrategySpec`, `ParameterSpace`, and `StrategyIR`  
> **Previous:** Phase 5 — Discovery Forge  
> **Next:** [Book 2 — CEREBUS Building Blocks and Rule Semantics](book-2-cerebus-building-blocks.md)

---

## 1. Success Statement

One complete, typed, versioned specification expresses every material strategy decision without depending on an agent’s memory, a prose manual, or target-specific code. Ambiguous or contradictory rules fail before generation.

---

## 2. Applicable Anchors

- **A0:** Human Strategic Authority
- **A1:** One Orchestration Spine
- **A2:** Evidence Before Narrative
- **A3:** Point-in-Time Data
- **A4:** Stable Identity Everywhere
- **A5:** Research Is Not Execution
- **A6:** Explicit Authority and Capability
- **A9:** Separate Research From Approval
- **A10:** Observable and Reconstructable
- **F5:** Code scans broad markets
- **F6:** One spec, no silent divergence

---

## 3. Contract Topology

```mermaid
flowchart LR
    H["Phase 5 handoff"] --> R["StrategyBuildRequest"]
    R --> F["Family registry"]
    F --> S["StrategySpec"]
    S --> V["Schema validator"]
    V --> M["Semantic validator"]
    M --> I["Normalized StrategyIR"]
```

---

## 4. Work Packages

### 4.1 Build request

```yaml
strategy_build_request_id: typed-id
candidate_set_refs: []
pattern_hypothesis_ref: optional-artifact-ref
research_thesis_ref: artifact-ref
discovery_request_ref: artifact-ref
discovery_lock_ref: artifact-ref
proposed_family: registry-ref
supported_asset_classes: []
observables: []
falsification_ref: artifact-ref
requested_targets: [signal_scanner, fast_evaluator, nautilus]
expires_at: timestamp
```

The request cannot contain executable code presented as authoritative or preapprove a result.

### 4.2 Strategy identity and lineage

`strategy_id` identifies the conceptual strategy. `strategy_spec_id` identifies an immutable spec version. Variants receive explicit parentage and semantic diffs; they do not overwrite the parent.

### 4.3 StrategySpec schema

```yaml
strategy_spec_id: content-id
strategy_id: stable-id
version: semver
name: string
family_ref: registry-ref
purpose: string
lineage: {}
supported_scope: {}
data_contract: {}
clock_and_session_contract: {}
features: []
parameters: {}
state_machine: {}
eligibility: {}
setup_rules: []
entry_rules: []
invalidation_rules: []
target_and_exit_rules: []
scaling_and_concurrency: {}
event_precedence: []
missing_and_stale_policy: {}
shutdown_and_reset: {}
expected_semantic_events: []
required_fixture_refs: []
validation_hypotheses: []
prohibited_capabilities: []
```

### 4.4 Family registry

A family definition states required sections, allowed primitives, supported market/event types, state template, parameter invariants, compatible targets, and forbidden constructs.

Initial families may include:

```text
session_range
breakout
pullback_retracement
mean_reversion
momentum_continuation
structural_rekey
relative_strength
event_conditioned
multi_leg_or_scaled
```

CEREBUS variants use registered primitives and may compose families; “CEREBUS” is not permission for undefined behavior.

### 4.5 Parameter contract

Every parameter declares:

```yaml
parameter_id: stable-id
type: integer|decimal|duration|timestamp|enum|boolean|ratio|price_distance
unit: pips|points|ticks|percent|R|bars|minutes|none
domain: {}
baseline_value: typed-value
optimization_permission: frozen|bounded|categorical|derived
dependency_rules: []
source: evidence-ref|operator-decision
sensitivity_expectation: monotonic|non_monotonic|unknown
```

No parameter may default differently across targets.

### 4.6 Expression language

The constrained DSL supports:

- typed arithmetic and comparisons;
- boolean composition;
- causal lag and completed-bar references;
- registered feature/state references;
- session/window predicates;
- cross/touch/close/hold/count operators;
- named level construction;
- deterministic state transitions;
- bounded list/set operations.

It forbids arbitrary Python, dynamic imports, file/network access, reflection, `eval`, and wall-clock reads.

### 4.7 Temporal references

Examples:

```text
bar.close at current completed bar
feature.value lag 1
session.high accumulated through timestamp
state entered_at plus duration
event available_at <= evaluation_time
```

The validator rejects future offsets, centered windows, or unspecified finality.

### 4.8 State machine

Each state variable has type, initial value, transition guards, actions, reset scope, persistence, and invariants. Transitions are ordered through the event-precedence policy.

### 4.9 TradeIntent boundary

Phase 6 may represent a test-only desired strategy action:

```yaml
trade_intent:
  semantic_event_ref: typed-id
  side: long|short|flat|reduce
  activation: market_on_event|limit_at_level|stop_at_level
  level_ref: optional-expression
  quantity_model: test_unit|fraction_of_strategy_unit
  time_in_force_semantics: abstract-policy-ref
  invalidation_ref: rule-ref
  target_refs: []
```

This is not Phase 9 `OrderIntent`: it has no account, venue route, broker, credential, or live capital authority.

### 4.10 Normalized IR

The compiler:

1. resolves references and defaults;
2. type-checks expressions;
3. converts units to canonical forms;
4. expands family templates;
5. orders state transitions and events;
6. assigns stable node IDs;
7. emits a canonical serialized IR and content hash.

Equivalent specs normalize identically only when their material semantics are identical.

### 4.11 Versioning

- patch: documentation or nonsemantic metadata;
- minor: backward-compatible optional capability;
- major: changed events, parameters, state, timing, entries, exits, or target meaning.

Any semantic change invalidates generated artifacts and downstream validation.

---

## 5. Target Layout

```text
strategy_forge/
  contracts/
    build_request.py
    strategy_spec.py
    trade_intent.py
  registry/
    families.py
    primitives.py
  spec/
    schema/
    validator.py
    semantic_diff.py
  ir/
    nodes.py
    normalize.py
    serialize.py
  dsl/
    grammar.py
    types.py
    parser.py
    static_checks.py
```

---

## 6. Deliverables

- `StrategyBuildRequest`, `StrategySpec`, and `TradeIntent` schemas.
- Stable strategy identity/version model.
- Strategy-family and primitive registries.
- Typed parameter-space contract.
- Constrained expression/state DSL.
- Schema, type, temporal, authority, and completeness validators.
- Canonical `StrategyIR` normalizer and serializer.
- Semantic diff and migration rules.
- Positive and invalid spec corpus.

---

## 7. Required Tests

### P6-REQ-001 — Valid Handoff Admission

A complete, locked, unexpired Phase 5 handoff produces one idempotent build request.

### P6-REQ-002 — Expired Handoff Rejection

Expired or invalidated candidate/hypothesis artifacts cannot build.

### P6-REQ-003 — Lineage Completeness

Missing candidate, hypothesis, thesis, discovery, or lock lineage fails admission.

### P6-SPC-001 — Canonical Spec Valid

A complete golden `StrategySpec` passes schema and semantic validation.

### P6-SPC-002 — Stable Spec Identity

Canonical serialization produces the same content ID independent of map ordering.

### P6-SPC-003 — Unknown Field Rejection

Unknown material fields fail closed rather than being ignored.

### P6-SPC-004 — Omitted Behavior Rejection

Missing reset, missing-data, precedence, entry, invalidation, or exit behavior fails when required.

### P6-INV-001 — Contradictory Rule Rejection

Mutually impossible or conflicting material rules cannot normalize.

### P6-INV-002 — Unsupported Family Primitive

A family cannot use an unregistered or unsupported primitive.

### P6-INV-003 — Long/Short Ambiguity

An undeclared asymmetric or mirrored rule fails validation.

### P6-FAM-001 — Family Requirements

Every registered family enforces its required sections and invariants.

### P6-FAM-002 — Family Version Isolation

A changed family template cannot alter an existing locked spec.

### P6-PRM-001 — Typed Parameter Domain

Every parameter value satisfies type, unit, bounds, and dependency rules.

### P6-PRM-002 — No Hidden Default

Removing a material baseline value fails rather than selecting a target default.

### P6-PRM-003 — Parameter Dependency

Conditional parameter requirements resolve exactly for all branches.

### P6-PRM-004 — Frozen Parameter

A frozen parameter cannot enter a Phase 7 search request.

### P6-DSL-001 — Expression Type Safety

Invalid unit arithmetic and incompatible comparisons fail compilation.

### P6-DSL-002 — Future Reference Rejection

Positive offsets, centered windows, and unavailable-event reads fail.

### P6-DSL-003 — Arbitrary Code Rejection

Imports, I/O, reflection, dynamic execution, and wall-clock calls are impossible in the DSL.

### P6-STM-001 — State Initialization

All state is initialized deterministically before the first event.

### P6-STM-002 — Transition Determinism

One event and state produce one ordered transition result.

### P6-STM-003 — Reset Completeness

Session/day/strategy resets cover all declared state without leaking prior state.

### P6-TRI-001 — Test-Only Intent

A valid strategy event produces a schema-valid test-only `TradeIntent`.

### P6-TRI-002 — Execution Field Rejection

Account, venue routing, broker, credential, and live-capital fields fail.

### P6-IR-001 — Canonical Normalization

Semantically identical source formatting produces the same IR and hash.

### P6-IR-002 — Semantic Difference

A material rule change produces a different IR hash and semantic diff.

### P6-VER-001 — Version Enforcement

Material semantic changes require a major version and invalidate prior target artifacts.

---

## 8. Failure Modes

- Strategy truth split across prose and code.
- Target adapter chooses missing defaults.
- Fixed parameters accidentally enter optimization.
- Future values enter via DSL offsets.
- State resets differ by runtime.
- “Mirror short” hides asymmetric price math.
- An abstract intent contains broker/account fields.
- Semantically changed spec retains the same version.

---

## 9. Exit Gate

Book 1 is complete only when one complete spec passes all contract and semantic gates, invalid/ambiguous specs fail closed, parameter and clock ownership is explicit, and a canonical IR is ready for registered building blocks.

---

## 10. Handoff

Book 2 receives the validated spec/IR, family and primitive versions, parameter space, Phase 5 feature references, and unresolved domain rules that must be converted into approved CEREBUS semantics or rejected.
