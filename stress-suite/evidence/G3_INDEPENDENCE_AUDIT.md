# G3 Independence Audit

Scope: independence semantics are precise enough for cognitive ecology, and provenance cannot be gamed.

## 1. Axes are independent — no inference between them (G3-P0-A)

`ReviewerIndependenceProfile` V1 carries, per reviewer: `reviewer_id`, `runtime_id`, `model_family`, `provider`, `runtime_lineage`, `source_lineages`, `retrieval_bundle_id`, `prompt_context_id`, `prior_conclusion_exposure`, `implementation_path`, `experiment_design_origin`, `allocator`, `role`, `claim_id`, `conclusion`, optional `confidence`.

Regression proof that the harness never infers one axis from another:

- `test_source_lineage_not_model_lineage` — distinct sources with one model family do NOT yield model-family diversity.
- `test_source_diversity_does_not_imply_runtime_diversity` / `test_runtime_diversity_does_not_imply_source_diversity` — the two directions fail closed.
- Unknown values are `UNKNOWN` and are counted as unknowns, never treated as independence.

## 2. Unambiguous shared-state semantics (G3-P0-B)

The old ambiguous `shared_allocator` / `shared_retrieval` booleans are replaced by explicit quantities: `distinct_allocator_count`, `distinct_retrieval_lineage_count`, `allocator_concentration`, `retrieval_bundle_concentration`, plus pairwise per-axis overlap in `DependencyGraph`. "More than one distinct value" is now expressed as a count/concentration, not a boolean. The profile is versioned V1; historical G2R receipts are untouched.

## 3. Pairwise dependency representation (§3)

`DependencyGraph` preserves per-reviewer-pair overlap on all ten axes (model family, provider, runtime lineage, source lineage, retrieval bundle, prompt/context, prior-conclusion exposure, implementation path, experiment design, allocator). It is a matrix of relations, not a scalar. Consumers may query per-axis concentration; no axis is collapsed into an authoritative score.

## 4. Metamorphics that matter

- Collapse S06's ten reviewers' lineage to one shared lineage → profile shows concentration 1.0 → independent confirmation fails.
- Same votes, diversified paths (distinct sources/models/retrievals) → disposition changes (tested in the S06 family).
- Model-name swap while sharing runtime lineage → no false independence (`test_model_name_swap_does_not_fake_independence`).
- Reviewer renaming preserves the topology decision where relations are unchanged (cross-scenario family).

## 5. CON-02 observation — allocation provenance is visible but not evidence

`AllocationProvenance` records who selected reviewers, who selected source bundles, who decided fresh-context status, who selected experiment design. The policy consumes the resulting topology as evidence context; the allocator's identity has no evidentiary weight by declaration. G3 therefore observes PO-style allocation influence without giving it authority — CON-02 remains constitutionally OPEN.

## 6. CON-03 observation — provenance is sealed (no Goodhart via self-report)

Fixture provenance is loaded from `reviewers.json` into sealed `ReviewerIndependenceProfile` objects before routing/adjudication. A reviewer cannot change its reported lineage fields during the run to satisfy constraints: registry/fixture truth wins. If provenance is `UNKNOWN`, `UNKNOWN` wins — favorable independence is never inferred. Threshold visibility policy remains as carried (PUBLIC / ROLE_RESTRICTED / SEALED_TEST_PARAMETER); CON-03 stays OPEN.

## 7. Receipt SHA semantics (G3-P0-C)

`G3_EVIDENCE_RECEIPT.json` uses `artifacts_head_sha` / `receipt_content_parent_sha` / `externally_verified_branch_head` and explicitly sets `self_pin_attempted: false`. No receipt claims to contain the SHA of the commit that contains it. The final human report (G3_RESULT.md) states the externally verified head only after an external push/verify step.
