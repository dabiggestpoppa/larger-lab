# G3R2 — Unknown-Semantics Audit

**Scope:** G3R2-04 (source-overlap prevalence), G3R2-05 (UNKNOWN prior
exposure), G3R2-06 (tri-state coverage into facts), G3R2-09 (unique epistemic
paths).

## 1. Source-overlap prevalence (G3R2-04)

Whole-bundle modal concentration misses the case where every reviewer depends on
one common source while their bundles otherwise differ:

```
R1 = [SOURCE_A, SOURCE_B]   R2 = [SOURCE_A, SOURCE_C]   R3 = [SOURCE_A, SOURCE_D]
bundle concentration = 1/3   but   SOURCE_A prevalence = 1.0
```

`EcologyFacts` now carries BOTH:

- `source_concentration` — modal whole-bundle concentration (preserved),
- `max_single_source_lineage_prevalence` — max over sources of
  (reviewers containing the source) / (reviewers with known source provenance).

Friction correlation logic and the shared policy gate on the common-source
measure; the correlated-failure health warning uses it too. Reviewers with NO
source metadata report `None` — never a benign low number that could be
mistaken for diversity.

**Proven by:** `partial_bundle_overlap_detects_shared_source`,
`all_reviewers_share_one_source_prevalence_is_one`,
`disjoint_source_bundles_remain_low_overlap`,
`unknown_source_metadata_not_treated_as_diverse`,
`common_source_plus_unique_sources_keeps_correlation_visible` (CASE G).

## 2. UNKNOWN prior exposure is not FALSE (G3R2-05)

The old `prior_conclusion_exposure_ratio = true / all` silently lowered the
exposure ratio for UNKNOWN reviewers — treating missing exposure as if it were
known-unexposed.

`EcologyFacts` now separates:

- `prior_exposure_true_count`, `prior_exposure_false_count`,
  `prior_exposure_unknown_count`
- `prior_exposure_known_ratio` (known / all)
- `prior_exposure_true_ratio_among_known` (true / (true+false))

For HIGH/MEDIUM consequence the independent-confirmation contract requires known
exposure coverage (`require_known_exposure_coverage`): UNKNOWN reviewers can
never satisfy an "unexposed" requirement. UNKNOWN is also not treated as
exposed — uncertainty is preserved, not resolved in either direction.

**Proven by:** `all_unknown_exposure_does_not_count_as_zero_exposure`,
`unknown_exposure_cannot_satisfy_strict_independence_contract`,
`known_false_exposure_can_satisfy`,
`mixed_known_unknown_preserves_coverage_uncertainty`,
`case_h_unknown_exposure_blocks_strict_independence`.

## 3. Tri-state UNKNOWN survives into decision-grade facts (G3R2-06)

Pairwise overlaps were already tri-state (SAME / DIFFERENT / UNKNOWN). The
downstream facts now preserve that uncertainty explicitly:

- `known_coverage_by_axis` — fraction of reviewers with a known value per axis,
- `unknown_count_by_axis` — unknown reviewers per axis.

A policy may use known diversity only when coverage is sufficient under its
PROVISIONAL test contract (e.g. `min_source_known_coverage`). No independence
score is minted: `2 known different + 8 unknown` remains visibly different from
`10 known diversified reviewers`.

**Proven by:** `unknown_heavy_set_is_not_equivalent_to_known_diversity`,
`unknown_axis_coverage_survives_into_facts_dict`.

## 4. Unique epistemic paths (G3R2-09)

The fresh/design/replication gate previously SUMMED labels
(`fresh_context_count + independently_originated_design_count +
independent_replication_count`) — a single path with several properties counted
multiple times.

`collect_epistemic_paths()` now builds `EpistemicPathRecord` identities:

- one reviewer that is fresh AND independently-designed is ONE path,
- duplicated path ids count once,
- a path whose provenance is entirely UNKNOWN does not qualify,
- replication paths are distinct fixture identities.

`EcologyFacts.unique_epistemic_path_count` and
`ReviewTopology.unique_epistemic_path_count()` consume the unique count, so
future thresholds (≥2, ≥3) are safe.

**Proven by:** `one_path_fresh_plus_design_counts_as_one`,
`two_distinct_qualifying_paths_count_as_two`,
`duplicated_path_id_counts_once`, `unknown_path_provenance_does_not_qualify`,
`case_j_one_path_two_labels_is_one`,
`replication_paths_are_distinct_identities`.

## 5. No effective-sample-size scalar

AMB-03 remains OPEN. The pair-wise dependency matrix, the per-axis coverage
facts, and the unique-path vector are preserved as observations; no
`effective_independent_agents` / `independence_score` / `HEALTH_SCORE` scalar
exists anywhere in the decision-grade facts (`no_effective_independence_scalar_minted`).
