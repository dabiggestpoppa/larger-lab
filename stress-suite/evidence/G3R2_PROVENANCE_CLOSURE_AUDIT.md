# G3R2 — Provenance Closure Audit

**Scope:** G3R2-01 (missing registry fails closed), G3R2-02 (no silent
self-registration), G3R2-03 (secondary surfaces bound), G3R2-10 (capability
provenance).

## 1. Missing registry entry fails closed (G3R2-01)

`ReviewerProvenanceRegistry.bind()` previously returned the CLAIMED profile
unchanged when no registry record existed, emitting only conflict markers. A
self-claim could therefore retain VERIFIED independence semantics.

**Fix:** with no registry record, the bound profile is rebuilt with every
decision-grade independence axis forced to non-qualifying:

- `model_family`, `provider`, `runtime_lineage`, `retrieval_bundle`,
  `prompt_context`, `experiment_design_origin`, `allocator` → `UNKNOWN`
- `source_lineages` → `()`
- `prior_conclusion_exposure` → `None` (UNKNOWN)
- `fresh_context` → `False`, `exposure_mode` → `UNKNOWN`,
  `independently_originated_design` → `False`

Identity, conclusion and evidence refs survive as claims but carry no
independence weight. Every claimed axis is recorded as an `UNVERIFIED_CLAIM`
conflict.

**Proven by:** `missing_registry_model_claim_becomes_unknown`,
`missing_registry_source_claim_becomes_unknown`,
`missing_registry_runtime_claim_becomes_unknown`,
`missing_registry_retrieval_claim_becomes_unknown`,
`missing_registry_blind_claim_not_verified`,
`missing_registry_independent_design_not_verified`,
`unverified_claims_cannot_satisfy_independence`.

## 2. No silent self-registration (G3R2-02)

The runner previously fell back to `registry = reviewers` when no
`registered_provenance` was supplied — implicitly upgrading fixture claims into
verified truth.

**Fix:** `G3ScenarioPack.provenance_mode` is explicit:

- `GOVERNED_REGISTRY` (default) — decision-grade axes come ONLY from
  `registered_provenance`; a missing registry file means NO verified provenance
  and every claim fails closed.
- `AUTHORITATIVE_SYNTHETIC_FIXTURE` — declared in each primary scenario
  contract; the harness owns the deterministic synthetic ground truth. This is
  an explicit authority grant to the harness, never an inference from a missing
  registry file, and never a trust grant for agent self-claims
  (`agent_claims_trusted=false`).
- Unknown mode → `ValueError` (fail closed).

Receipts record `provenance_mode`, `synthetic_fixture_authority_used` and the
`SyntheticFixtureAuthority` block.

**Proven by:** `default_missing_registry_fails_closed`,
`explicit_synthetic_fixture_mode_allows_fixture_truth`,
`synthetic_fixture_mode_recorded_in_receipt`,
`governed_registry_mode_never_self_registers_claims`,
`unknown_provenance_mode_rejected`.

## 3. Secondary cognitive surfaces bound (G3R2-03)

All surfaces now flow through the same provenance authority via a single
`_bind()` path in the runner:

- primary reviewer profiles
- topology-option candidate reviewers
- friction / fresh-context reviewers
- independent experiment-design flags (carried on the bound profiles)

In governed mode an unregistered candidate cannot self-declare different model
families, different sources, fresh context, BLIND status or independent design —
binding collapses those claims to UNKNOWN/non-qualifying, so a proposed
topology cannot become admissible on self-declared diversity. In synthetic mode
the same surfaces are harness-authoritative (identity binding).

**Proven by:** `topology_candidate_fake_model_diversity_fails`,
`topology_candidate_fake_source_diversity_fails`,
`topology_candidate_fake_independent_design_fails`,
`friction_reviewer_fake_blind_status_fails`,
`friction_reviewer_registry_blind_status_succeeds`,
`secondary_surfaces_share_same_provenance_semantics`.

## 4. Capability provenance (G3R2-10)

`ReviewTopology.capability_source` is explicit:

- `AUTHORITATIVE_SYNTHETIC_CAPABILITY` — harness-owned fixture tiers (S07).
- `REGISTERED_CAPABILITY` — every candidate has a registered capability fact.
- `UNVERIFIED_CAPABILITY` — otherwise; never satisfies a positive
  minimum-capability requirement.

Capability is a routing fact, not an authority fact: routing with different
capability sources leaves `authority_before`/`authority_after` at NONE.

**Proven by:** `unverified_high_capability_does_not_pass`,
`registered_adequate_capability_passes`,
`synthetic_authoritative_capability_mode_explicit`,
`case_k_fake_topology_cannot_satisfy_verified_routing`,
`capability_change_does_not_change_authority`.

## 5. Cross-case matrix (F–K)

| case | threat | outcome |
|---|---|---|
| F | self-registered swarm (10 claimed lineages, no registry) | independence NOT established |
| G | partial source monoculture (common + unique per reviewer) | prevalence 1.0; correlation visible |
| H | UNKNOWN exposure, diverse sources/models | strict unexposed requirement NOT satisfied |
| I | early challenge (budget 5, contradiction at 2) | stops at 2 |
| J | one path, two labels (fresh AND design) | one unique epistemic path |
| K | fake topology (self-claimed HIGH capability, registry UNKNOWN) | verified HIGH routing unsatisfied |
