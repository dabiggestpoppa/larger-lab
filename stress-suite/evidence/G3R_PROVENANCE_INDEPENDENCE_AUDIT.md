# G3R Provenance & Independence Audit

Scope: reviewer provenance is governed (claims cannot self-ratify independence), unknown metadata never mints favorable independence, and fresh-context is distinct from independent design.

## 1. Reviewer provenance is registry-bound (G3R-07)

`ReviewerProvenanceRegistry` holds VERIFIED/REGISTERED provenance per reviewer (model family, provider, runtime lineage, source lineage, retrieval bundle, prompt/context, experiment-design origin, allocator, prior-conclusion exposure, fresh context, exposure mode, independent-design flag). `bind()` separates CLAIMED from VERIFIED:

- **Registered wins:** `worker_claims_fake_model_lineage`, `..._fake_source_lineage`, `..._fake_retrieval_bundle` all resolve to the registered value with a `REGISTERED_WINS` conflict recorded.
- **System-observable exposure:** a worker claiming BLIND while the registry records `prior_conclusion_exposure=TRUE` and `FULL_SHARED_CONTEXT` is corrected; exposure_mode is provenance.
- **UNKNOWN never promotes a claim:** `unknown_registry_provenance_remains_unknown` keeps the axis UNKNOWN with an `UNVERIFIED_CLAIM` conflict; `missing_registry_entry_does_not_promote_claims` marks every claimed axis unverified.
- **CASE E:** three reviewers claiming three model lineages bind to the ONE registered lineage; `distinct_model_family_count == 1`; all three conflicts preserved.

The runner binds every scenario profile through the registry (fixture identity ⇒ no conflicts for the primary packs); `provenance_conflicts` is a first-class artifact and receipt field.

## 2. Tri-state dependency semantics (G3R-08)

Pairwise overlap is now `SAME` / `DIFFERENT` / `UNKNOWN` on every axis:

- UNKNOWN-vs-UNKNOWN is **UNKNOWN** — neither independent nor shared; `fully_correlated_pairs` requires every axis SAME.
- Known-same ⇒ `SAME`; known-different ⇒ `DIFFERENT`.
- `pair_overlap_counts` counts only SAME (unknowns contribute to neither side).
- `unknown_axis_cannot_satisfy_independence_requirement`: two reviewers with distinct sources but UNKNOWN model/runtime fail the sufficiency guard — source diversity never substitutes for unknown model axes.

## 3. Fresh context vs independent design (G3R-06)

- `ReviewerIndependenceProfile.independently_originated_design` is provenance-flagged (fixture/registry), NEVER inferred from design-name differences.
- The topology contract's `min_fresh_or_independent_design` accepts `fresh_context_count + independently_originated_design_count`; `min_fresh_context` and `min_independent_design` are supported separately.
- `fresh_context_satisfies_fresh_or_design_requirement` (fresh only), `independent_design_satisfies_requirement_without_fresh_context` (design only, CASE D), `duplicated_design_does_not_satisfy` (one shared design origin, no fresh), `unknown_design_does_not_count_favorably` — all PASS.
- `independent_confirmation_satisfied` also counts provenance-verified independent designs toward its fresh-or-design requirement.

## 4. No scalar minted

All independence reasoning remains vector/graph-based. `dominant_vote_ratio` and concentrations describe vote/lineage topology only. AMB-03 (authoritative aggregation) remains OPEN.
