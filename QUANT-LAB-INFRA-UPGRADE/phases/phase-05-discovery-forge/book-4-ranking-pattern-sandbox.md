# Phase 5, Book 4 — Ranking and Pattern Sandbox

> **Purpose:** Rank qualified matches reproducibly and convert bounded observations into testable pattern hypotheses  
> **Input:** Scanner matches, feature evidence, request/thesis lineage, and quality state  
> **Output:** Explainable `CandidateSet` and optional `PatternHypothesis` objects  
> **Previous:** [Book 3 — Scanner Fabric](book-3-scanner-fabric.md)  
> **Next:** [Book 5 — Discovery Operations and Lock](book-5-discovery-operations-lock.md)

---

## 1. Success Statement

Fixed inputs and policies produce the same ordered candidate set, every score reconciles from stored components, optional missing features cannot destabilize ranking silently, and pattern mining produces hypotheses rather than overfit trading rules.

---

## 2. Applicable Anchors

- **A0:** Human Strategic Authority
- **A2:** Evidence Before Narrative
- **A3:** Point-in-Time Data
- **A5:** Research Is Not Execution
- **A9:** Separate Research From Approval
- **A10:** Observable and Reconstructable
- **F4:** Testable research only
- **F5:** Code scans broad markets

---

## 3. Ranking Topology

```mermaid
flowchart LR
    M["ScannerMatch"] --> E["Eligibility gate"]
    E --> N["Component normalization"]
    N --> S["Score composition"]
    S --> T["Stable tie-break"]
    T --> C["CandidateSet"]
    C --> A["Bounded agent analysis"]
    A --> H["PatternHypothesis"]
```

---

## 4. Work Packages

### 4.1 Ranking policy

```yaml
ranking_policy_id: registry-id
version: semver
eligibility_predicates: []
components:
  - feature_ref: registry-ref
    direction: higher|lower|target_range|two_sided
    transform: registry-ref
    normalization: registry-ref
    weight: decimal
    cap: optional-decimal
    missing_policy: exclude|renormalize|penalty|neutral
score_range: {}
tie_breakers: [stable_instrument_id]
maximum_candidates: integer
```

Weights and transforms are frozen before the run. Agents cannot reorder the full candidate field by subjective preference.

### 4.2 Candidate record

The record contains rank, score, component contributions, match explanations, feature refs, missingness, thesis/event trace, universe/tradability status, quality flags, and counterevidence or limitations.

### 4.3 Missing optional features

Policies are explicit:

- exclude candidate;
- renormalize across available components;
- apply fixed penalty;
- use neutral contribution.

The method and effective denominator appear in the explanation.

### 4.4 Ranking stability

Tests cover deterministic ties, floating-point tolerance, partition order, optional-feature loss, benign input perturbations, and changes around eligibility thresholds.

Stability does not mean hiding real signal changes. The report distinguishes expected sensitivity from implementation instability.

### 4.5 Explanation

For every candidate:

```text
why included
why ranked here
which evidence and features contributed
which features were absent
which constraints or penalties applied
what would remove the candidate
which thesis/request produced the search
```

Component contributions must sum to the stored score within declared tolerance.

### 4.6 Bounded agent review

Agents may investigate only the returned candidate set and cited evidence, annotate contradictions or data gaps, and propose follow-up research. They cannot add unscanned symbols or silently rerank candidates.

### 4.7 Pattern-discovery sandbox

The sandbox explores feature/event/forward-observable relationships under a declared research protocol:

- hypothesis before final evaluation;
- discovery, validation, and holdout periods;
- walk-forward or nested evaluation;
- multiple-testing correction;
- minimum sample and coverage;
- stable identity and point-in-time inputs;
- economic and statistical effect reporting;
- false-discovery and regime sensitivity;
- complete experiment registry.

### 4.8 Pattern hypothesis

```yaml
pattern_hypothesis_id: typed-id
candidate_or_group_refs: []
source_feature_refs: []
conditioning_event_refs: []
claim: testable-string
expected_observable: {}
horizon: duration
falsification: {}
discovery_sample: {}
reserved_evaluation_sample: {}
multiple_testing_family_ref: typed-id
known_limitations: []
strategy_forge_request: bounded-object
```

It cannot contain an executable entry, exit, target, size, order, or claimed live edge.

### 4.9 Candidate set

The content-addressed result records every eligible candidate and final rank, plus excluded-after-match records, ranking policy, manifests, code versions, coverage, cutoff, and expiration.

---

## 5. Target Layout

```text
discovery/
  ranking/
    policy.py
    eligibility.py
    normalization.py
    score.py
    stability.py
    explain.py
    candidate_set.py
  patterns/
    protocol.py
    experiment_registry.py
    multiple_testing.py
    hypothesis.py
    handoff.py
```

---

## 6. Deliverables

- Ranking-policy schema and registry.
- Eligibility, transform, normalization, score, and tie-break engine.
- Candidate explanation and reconciliation.
- Missing-feature policies.
- Ranking stability/sensitivity report.
- Bounded candidate-review workflow.
- Point-in-time pattern sandbox.
- Experiment and multiple-testing registry.
- `PatternHypothesis` and Phase 6 request contracts.
- Immutable `CandidateSet`.

---

## 7. Required Tests

### P5-RNK-001 — Deterministic Ranking

Fixed inputs produce identical scores, ordering, and candidate-set hash.

### P5-RNK-002 — Score Reconciliation

Stored component contributions reconcile to the final score.

### P5-RNK-003 — Stable Tie Break

Exact score ties resolve by the declared deterministic fields.

### P5-RNK-004 — Weight Freeze

Weights cannot change during or after a run without a new policy version.

### P5-RNK-005 — Result Bound

The output respects the request maximum while preserving all cutoff/exclusion evidence.

### P5-MIS-001 — Optional Missing Stability

Removing one optional feature follows policy and does not produce unexplained rank changes.

### P5-MIS-002 — Effective Weight Disclosure

Renormalized or penalized scores expose the effective component denominator.

### P5-MIS-003 — Required Missing Exclusion

Missing required ranking data excludes with an explicit reason.

### P5-STB-001 — Partition-Order Stability

Input/worker order does not change scores or ranking.

### P5-STB-002 — Floating-Point Stability

Supported runtimes agree within the declared tolerance and stable ordering rule.

### P5-STB-003 — Perturbation Report

Small input changes produce measured sensitivity rather than unexplained discontinuity.

### P5-TRC-001 — Event-to-Candidate Traceability

Every candidate traces to request, thesis, event, universe, scanner, and feature artifacts.

### P5-EXP-001 — Inclusion Explanation

Each candidate exposes all passed gates, matches, and score contributions.

### P5-EXP-002 — Removal Explanation

Each matched but unranked instrument exposes the eliminating gate.

### P5-EXP-003 — Explanation Fidelity

Displayed explanations match stored machine-readable values.

### P5-AGT-001 — Bounded Review

An agent cannot add an instrument outside the immutable candidate set.

### P5-AGT-002 — No Subjective Rerank

Agent annotations cannot mutate canonical scores or ranks.

### P5-PAT-001 — Sample Separation

Discovery and reserved evaluation observations do not overlap.

### P5-PAT-002 — Multiple-Testing Registry

Every explored hypothesis belongs to a declared test family.

### P5-PAT-003 — Holdout Integrity

Holdout outcomes remain inaccessible until the hypothesis is frozen.

### P5-PAT-004 — Minimum Evidence

Patterns below sample, coverage, or effect thresholds cannot advance.

### P5-PAT-005 — Regime Sensitivity

The report discloses material dependence on period, asset group, or volatility regime.

### P5-PAT-006 — Hypothesis-Only Output

Pattern output rejects executable strategy and trading fields.

### P5-PAT-007 — Negative Result Preservation

Failed and null experiments remain in the registry.

---

## 8. Failure Modes

- Agent intuition reranks the universe.
- Missing features change denominator invisibly.
- Tie order depends on worker arrival.
- Explanation text does not reconcile to the score.
- Candidate set omits near misses and exclusions.
- Pattern mining leaks the holdout.
- Hundreds of trials reported as one successful discovery.
- A correlation is emitted as a deployable strategy.

---

## 9. Exit Gate

Book 4 is complete only when candidate ranking reproduces, explanations reconcile, missingness is stable, agents are bounded to the narrowed field, and any discovered pattern remains a registered falsifiable hypothesis for Phase 6.

---

## 10. Handoff

Book 5 receives the immutable candidate set, ranking evidence, review annotations, pattern experiment registry, optional hypotheses, and all manifests needed for operational validation.
