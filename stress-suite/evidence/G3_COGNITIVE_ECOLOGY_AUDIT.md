# G3 Cognitive Ecology Audit

Scope: does the institution distinguish *many voices* from *many independent reasons*, and does it do so without minting a scalar?

## 1. Consensus is observation, not evidence

`ConsensusRecord` preserves, per scenario:

- `raw_reviewer_count` and `raw_vote_distribution`;
- `conclusion_set` and `supporting_evidence_refs`;
- full `reviewer_profiles` (per-reviewer axes, exposure modes);
- `pairwise_dependency_refs` (the DependencyGraph fingerprint);
- source/model/retrieval concentrations and prior-conclusion exposure counts;
- `unknown_independence_dimensions` and retained `disagreement`.

S06 and S09 both produce 100% majority consensuses (10/10 and 8/8). The policy treats them differently **only** through the pairwise dependency topology and lineage counts: S06 has `distinct_source_lineages=1` with exposure 1.0 → `SUPPORTED_BUT_CORRELATED`; S09 has 3 distinct lineages with zero exposure and replication → `INDEPENDENTLY_SUPPORTED`. No scenario-id, no reviewer-name, no expected-conclusion predicate participates (static guard enforced).

## 2. No effective sample size

- `independent_confirmation_satisfied()` applies **test-contract sufficiency predicates** (≥2 source lineages, ≥2 model/runtime lineages, exposure above floor, independent design presence) and returns a boolean + reason — not a scalar score.
- The full pairwise overlap matrix lives in `DependencyGraph` (per-axis overlap edges). Any derived concentration summary is labeled `EXPERIMENTAL_NON_AUTHORITATIVE`.
- AMB-03 (authoritative independence aggregation) remains OPEN by design.

## 3. Dimension swaps (provisional, not universalized)

`test_g3_cross_scenario.py::test_independence_dimension_swaps` mutates ONE axis at a time (same model/different sources; different model/same source; everything different/same allocator; same everything/blind context; same sources/independent design; …) and records which axes change the disposition under the provisional contract. Weights are NOT universalized: the audit reports the sensitivity table as evidence for later G4/G8 ratification, not as constitutional doctrine.

## 4. Reviewer-quality vs institutional-reliability separation (S07)

- Constraint router: `route_review_topology()` selects the **cheapest admissible topology** satisfying capability floors + required independence dimensions, never "most agents" and never a single `quality*independence` scalar.
- High consequence → `TOPO_B_DIFFERENTIATED` (2 weaker-but-differentiated reviewers, cost 24). Low consequence → the cheap highest-capability path is admissible (tested).
- Diverse-but-insufficient-capability reviewers fail the capability constraint; monoculture high-capability fails the independence constraint. Both axes must hold.

## 5. Correlated failure as first-class evidence

`CorrelatedFailureRecord` can attribute many failures to one shared upstream dependency (synthetic fixture truth as observable provenance). Correlation is never inferred merely from matching outputs — it requires known dependency lineage. This is an observational surface for later institutional self-observation; it holds no authority.

## 6. Ecology health is a vector

`CognitiveEcologyHealthRecord` keeps raw consensus concentration, source/model/retrieval concentration, exposure, independent reconstruction count, disagreement preservation, fresh-context count, counter-attractor frequency, review cost, information gain, correlated-failure warnings — **no `HEALTH_SCORE`**. The vector is observational, not authority.

## 7. Sealing

Wrong expected verdict and hidden-ground-truth flips leave actions unchanged (metamorphic tests). Scenario renames and reviewer renames preserve `behavior_fingerprint` (relations-only normalization). Expected/hidden fields are never decision-grade inputs.
