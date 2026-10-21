# Chapter 3.1 — Repository Comprehension Mission

## Mission

Repository Intelligence converts a candidate source container into a structured, revision-scoped model of its architecture and relevant capability locations.

The governing question is not:

> What does this repository say it does?

It is:

> What capability-relevant structure can we locate in source, and what remains only claimed or inferred?

## 3.1.1 Inputs

- candidate identity;
- immutable source revision;
- target contract/atoms;
- discovery claims;
- ranked unresolved questions;
- source access policy.

## 3.1.2 Outputs

```text
repository structural map
capability localization map
dependency graph
interface/state map
test/docs/benchmark map
claim verification ledger
architecture summary
archaeology findings
uncertainty ledger
Block 4 forensic targets
```

## 3.1.3 Source Hierarchy

For repository facts, prefer direct source artifacts:

```text
code/config/manifests/tests
> generated/static structural analysis
> official documentation
> DeepWiki/LLM explanation
> README/marketing claims
```

The exact strength depends on the question. Tests can reveal intended semantics without proving runtime correctness.

## 3.1.4 Comprehension vs Proof

Repository Intelligence may establish:

- symbol exists;
- module imports dependency;
- test claims behavior;
- interface has method X;
- code path appears to implement algorithm Y.

It does not by inspection alone establish:

- build succeeds;
- runtime behavior is correct;
- performance claims hold;
- strategy alpha exists;
- sandbox/security behavior is safe.

Those belong to later proof stages.

## 3.1.5 Targeted Comprehension

QCAE should not summarize every file equally. Investigation is guided by target atoms and unresolved discovery questions.

This minimizes context and cost while preserving enough whole-repository structure to detect hidden coupling.

## 3.1.6 Whole-Repo Context Requirement

Targeting must not become tunnel vision. Before extracting a component, QCAE needs enough structural context to understand:

- initialization;
- shared state;
- global registries;
- code generation;
- side effects;
- configuration;
- lifecycle hooks;
- hidden services.

## 3.1.7 Evidence Anchoring

Every substantive structural assertion should be anchorable to one or more of:

```text
commit SHA
file path
symbol/line region
manifest entry
test path
config path
document revision
```

LLM-generated prose without anchors is analysis only.

## 3.1.8 Uncertainty Ledger

Unknowns must be explicit:

```text
UNKNOWN_RUNTIME_BEHAVIOR
UNKNOWN_DYNAMIC_IMPORT
UNKNOWN_GENERATED_CODE
UNKNOWN_EXTERNAL_SERVICE_SEMANTICS
UNKNOWN_BUILD_STEP
UNKNOWN_PLATFORM_ASSUMPTION
```

Uncertainty becomes a Block 4/Book III work item rather than being silently resolved by inference.

## 3.1.9 Context Budget

Large repositories require progressive comprehension:

```text
repo metadata
→ tree/manifests
→ likely modules
→ symbol neighborhood
→ cross-reference/dependency expansion
→ targeted history
```

Do not dump an entire repository into one model context and call the result understanding.

## 3.1.10 Repository Intelligence Record

Future schema should include:

```text
candidate_id
source_revision
analysis_revision
structural_map_ref
capability_locations
dependency_map_ref
claim_ledger_ref
history_findings
uncertainties
evidence_anchors
recommended_forensic_targets
```

## 3.1.11 Invariants

1. Repository comprehension is revision-scoped.
2. Source is authoritative over model explanation.
3. Comprehension and runtime proof are distinct.
4. Investigation is capability-targeted but preserves enough global context to detect coupling.
5. Assertions are evidence-anchorable.
6. Unknowns remain explicit.
7. Large repositories are understood progressively.

## Exit Criteria

The repository intelligence subsystem has a clear mission/boundary and can hand Block 4 a structural evidence package rather than an ungrounded prose summary.
