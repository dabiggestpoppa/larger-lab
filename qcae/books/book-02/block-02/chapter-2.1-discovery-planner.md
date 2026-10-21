# Chapter 2.1 — Discovery Planner

## Mission

The Discovery Planner translates a frozen Capability Contract and its atom decomposition into an explicit search program. It prevents ad-hoc browsing, first-result capture, vocabulary lock-in, and uncontrolled search cost.

Its output is not a repository. Its output is a **Discovery Plan**.

## 2.1.1 Inputs

Required inputs:

```text
contract_id + version
required atoms
optional atoms
required/preferred/forbidden conditions
operating context
security/data constraints
accepted acquisition forms
required evidence class
known internal implementations
known prior evaluations
budget envelope
```

The planner must query durable memory for existing capability/rejection knowledge before external search.

## 2.1.2 Search Hypotheses

For each atom, create multiple hypotheses about where the capability may exist:

- focused library/package;
- component inside larger framework;
- protocol/specification;
- academic paper/reference implementation;
- mature application with extractable subsystem;
- service/API;
- internal Quant Lab implementation;
- adjacent-domain implementation using different vocabulary.

A hypothesis is a search route, not a belief that the candidate works.

## 2.1.3 Query Families

The planner generates families rather than one prompt/query:

### Behavioral queries
Describe what the capability does.

### Domain-term queries
Use accepted technical names.

### Synonym queries
Search alternate terminology.

### Interface queries
Search likely protocols, classes, APIs, symbols, schemas, file formats, or standards.

### Implementation-pattern queries
Search known algorithm/design names without requiring a particular repository.

### Failure/edge-case queries
Search terms associated with the hard part of the capability; these often surface serious implementations.

### Specification/paper queries
Search standards and literature separately from code.

### Negative-space queries
Intentionally omit dominant framework/product names to discover alternatives.

## 2.1.4 Query Expansion

Expansion may use an LLM to propose vocabulary, but generated terms are hypotheses only. Expansion should be anchored to contract semantics and later evaluated by retrieval quality.

The planner should preserve the lineage:

```text
contract atom
→ semantic concept
→ query family
→ concrete query
→ source adapter
→ returned candidate
```

## 2.1.5 Source Portfolio

A Discovery Plan allocates work across source classes rather than relying on one index:

```text
internal registry/code
GitHub repository/code search
curated sensors
package/ecosystem registries
research literature
standards/specifications
known project documentation
web discovery where useful
```

Source choice depends on capability type.

A protocol parser should overweight standards/code search. A statistical estimator may overweight papers/packages. A developer tool may overweight GitHub/package ecosystems.

## 2.1.6 Internal-First Rule

Before external acquisition search, determine whether Quant Lab already possesses:

- the full capability;
- a partial atom;
- a better primitive;
- an abandoned implementation worth reviving;
- prior evidence that the proposed route failed.

Internal-first does not mean internal-only. It establishes the baseline against which external value is measured.

## 2.1.7 Diversity Budget

The planner should reserve budget for candidates outside the dominant vocabulary/ecosystem.

Example allocation concept:

```text
50% high-likelihood mainstream search
20% alternate terminology
10% adjacent-domain transfer
10% research/specification
10% exploratory/novel sources
```

Percentages are policy examples, not frozen universal constants. The invariant is that the top-ranked ecosystem must not consume the entire discovery budget by default.

## 2.1.8 Cost Tiers

Discovery work should escalate progressively:

```text
Tier 0 — memory lookup / prior evaluations
Tier 1 — metadata and search snippets
Tier 2 — README/docs/package metadata
Tier 3 — source-tree inspection / code search
Tier 4 — repository intelligence / DeepWiki-assisted comprehension
Tier 5 — capability forensics
Tier 6 — proving lab
```

Block 2 controls Tiers 0–3 and decides what merits Block 3/4 escalation.

## 2.1.9 Stop Rules

Discovery must terminate rationally.

Possible stop conditions:

- enough non-dominated candidates exist for deeper comparison;
- new searches produce negligible novel capability coverage;
- remaining sources are lower expected value than deeper investigation of current candidates;
- hard constraints eliminate the candidate class;
- internal capability already dominates plausible external routes;
- budget ceiling reached;
- contract ambiguity discovered that requires amendment before further search.

"Search the whole internet" is not an operational objective.

## 2.1.10 Saturation

The planner should track marginal novelty:

```text
new candidates
new implementation families
new specifications
new atoms covered
new acquisition forms
new failure information
```

If successive query families return duplicates or dominated variants, the search is approaching saturation.

## 2.1.11 Candidate Intake Record

Every discovered candidate should initially capture:

```text
candidate_id
source_type
source_locator
immutable/retrieved revision when available
discovered_by_query
discovery_timestamp
candidate_kind
claimed_capabilities
possible_atom_matches
language/runtime
license_claim
activity signals
popularity signals
initial constraints conflicts
novelty family
prior-evaluation linkage
```

These are discovery observations, not verified facts unless the evidence warrants that state.

## 2.1.12 Deduplication

The same project may appear through GitHub, GitHubDaily, package registries, papers, and web search. QCAE should merge discovery paths into one canonical candidate while preserving all source paths.

Do not count repeated discovery as independent evidence of capability quality.

## 2.1.13 Search Failure as Information

If multiple diversified searches fail to find a focused implementation, that is evidence relevant to build/borrow economics.

It may imply:

- capability is unusually novel;
- terminology is wrong;
- capability exists only embedded in larger systems;
- a standard/spec is a better acquisition source;
- internal construction may be rational.

Absence is not proof of nonexistence, but systematic failed search is durable negative knowledge.

## 2.1.14 Contract Amendment Boundary

Discovery may uncover that the contract is malformed.

Example: every serious implementation requires an input the contract omitted.

The planner may emit:

```text
CONTRACT_AMENDMENT_PROPOSAL
```

with evidence. It may not silently add the requirement and continue as if the original contract said it.

## 2.1.15 DiscoveryPlan Object

Future schema should contain at minimum:

```text
discovery_plan_id
contract_id
contract_version
atom_ids
internal_baseline_queries
search_hypotheses
query_families
source_allocations
budget
cost_tier_ceiling
diversity_requirements
hard_prefilters
stop_rules
saturation_metrics
created_by
policy_version
```

## 2.1.16 Planner Failure Modes

Prevent:

- one-query discovery;
- product-name capture;
- dominant-vocabulary capture;
- star-count selection;
- searching externally before checking internal capability;
- spending forensic budget on dozens of weak candidates;
- repeated rediscovery of known rejected candidates;
- treating duplicate search hits as corroboration;
- silently changing the capability contract.

## 2.1.17 Invariants

1. Discovery begins from frozen capability semantics.
2. Multiple search hypotheses are mandatory for nontrivial capabilities.
3. Internal capability is part of the search universe.
4. Search provenance is retained.
5. Diversity is deliberate.
6. Discovery cost escalates progressively.
7. Stop rules exist before expensive investigation.
8. Discovery can propose, never silently enact, contract changes.
9. Discovery produces candidates, not proof.

## Exit Criteria

The chapter is complete when an implementation agent can construct a reproducible Discovery Plan from a Capability Contract and explain why each source/query family is being searched, what budget it receives, and when the search should stop.
