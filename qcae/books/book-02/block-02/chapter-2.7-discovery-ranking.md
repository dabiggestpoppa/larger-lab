# Chapter 2.7 — Discovery Ranking

## Mission

Discovery Ranking decides which candidates deserve the next unit of investigation budget. It is a triage system, not a final acquisition score and not a substitute for Book III proof.

## 2.7.1 Ranking Objective

Optimize:

> expected information/capability value of the next investigation step per unit of cost.

This differs from simply ranking "best repositories."

## 2.7.2 Inputs

Preliminary ranking may use:

- contract/atom semantic match;
- required-atom coverage claims;
- obvious hard-constraint conflicts;
- focused-component likelihood;
- source availability;
- test/docs/benchmark presence;
- dependency burden signals;
- maintenance signals;
- license claim;
- implementation diversity;
- novelty relative to current candidate set;
- internal baseline;
- prior evaluation state;
- expected cost of deeper investigation.

## 2.7.3 Hard Prefilters

Candidates with obvious hard failures can be rejected/deferred before expensive intelligence, provided the evidence is strong enough.

Examples:

- explicit incompatible license;
- wrong platform under non-negotiable constraint;
- no relevant capability;
- forbidden SaaS/data-egress requirement.

Weak metadata cannot justify hard rejection.

## 2.7.4 Ranking Is Not Proof

A top-ranked candidate means:

> inspect this first.

It does not mean:

> acquire this.

The state transition is from `DISCOVERED` toward `UNDER_REPOSITORY_INTELLIGENCE`, not toward `ACCEPTED`.

## 2.7.5 Diversity-Aware Ranking

If the top ten candidates are near-identical wrappers around one dependency, investigating all ten has low information value.

Ranking should preserve representative diversity across:

- implementation family;
- language/runtime;
- algorithm;
- acquisition form;
- source ecosystem;
- architectural approach.

## 2.7.6 Family Clustering

Candidates should be grouped when they share substantial lineage or implementation core:

```text
original project
forks
thin wrappers
bindings
ports
reimplementations
```

QCAE can inspect a representative candidate first and branch deeper only when differences matter.

## 2.7.7 Novelty Bonus

A candidate that introduces a genuinely different implementation/specification family may deserve investigation even with weaker popularity/activity signals because it increases knowledge diversity.

Novelty is valuable only if contract relevance remains plausible.

## 2.7.8 Information-Gain Ranking

A candidate can be valuable because evaluating it resolves uncertainty.

Example:

A highly focused implementation with unclear license may be worth a cheap license check before spending hours understanding a complex but clearly permissive framework.

Ranking therefore operates on **next action**, not only candidate identity.

## 2.7.9 Escalation Queue

Output should resemble:

```text
Candidate A → next: source-tree map → priority high
Candidate B → next: license verify → priority high, cheap uncertainty
Candidate C → next: defer pending A because same family
Candidate D → reject: hard platform mismatch
Candidate E → next: specification lookup
```

## 2.7.10 Preliminary Dimensions

Possible normalized dimensions:

```text
semantic_fit
coverage_potential
constraint_fit
focus/extractability_prior
evidence_availability
maintenance_prior
dependency_prior
license_prior
novelty
expected_investigation_cost
expected_information_gain
```

These are discovery priors, not final Capability Value dimensions.

## 2.7.11 Popularity Cap

Popularity/community metrics may influence only a bounded portion of preliminary ranking. They must not overwhelm semantic fit, constraints, or evidence availability.

The exact weighting is implementation policy and must be versioned/tested.

## 2.7.12 LLM Ranking Boundary

An LLM may synthesize candidate metadata and explain ranking rationale. It may not fabricate missing facts or convert a weak metadata prior into verified evidence.

## 2.7.13 Dominance Triage

If one candidate is clearly worse on all observed relevant dimensions than another candidate in the same family, it can be deprioritized without deep inspection unless novelty/uncertainty justifies otherwise.

## 2.7.14 Budget Allocation

Ranking should produce waves:

```text
Wave 1 — cheap/high-information candidates
Wave 2 — promising alternatives/diverse families
Wave 3 — expensive/uncertain candidates only if needed
```

After each wave, the Discovery Planner reevaluates saturation and stop rules.

## 2.7.15 Discovery Report

Block 2's terminal artifact should include:

```text
contract + atom scope
internal baseline
sources searched
query families executed
coverage/partial-search notes
canonical candidate set
candidate families
prefilter decisions
ranked escalation queue
negative findings
saturation metrics
remaining uncertainties
contract amendment proposals
stop/continue recommendation
```

## 2.7.16 Invariants

1. Ranking allocates investigation budget; it does not approve acquisition.
2. Semantic/constraint fit outranks social popularity.
3. Candidate diversity matters.
4. Fork/wrapper families are not treated as fully independent evidence.
5. Expected information gain influences next-action priority.
6. Hard rejection requires sufficiently strong evidence.
7. Ranking policy is versioned and auditable.
8. Search saturation is reevaluated after each investigation wave.

## Exit Criteria

Block 3 can receive a bounded, diverse, provenance-rich candidate queue with explicit next actions and know why those candidates—not merely the most popular search results—were selected for repository intelligence.
