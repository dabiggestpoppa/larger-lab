"""Book 6 validation traceability — every row bound to a real assertion.

A traceability matrix is only worth anything if each row names an assertion that
actually exists. Every row below cites a concrete pytest node id, and
``test_book6_traceability.py`` resolves every one of them against the test files
on disk, so a row cannot outlive the assertion it claims to trace to.

The ratified 6D families are covered mechanically:

- **6D.1** missingness — ten states, ``ZERO_OBSERVED != missing``, no fabricated
  zero, and fail-closed quotients;
- **6D.2** methodology sensitivity — two reasonable methodologies may disagree
  and the disagreement is surfaced, never resolved;
- **6D.3** historical sanity — append-preserving revision, linear supersession,
  window-bounded reorgs, and deterministic replay;
- **6D.4** cross-source parity — source-specific measurements preserved, no
  consensus number, no invented tolerance;
- **6D.5** false-comparison detection — all fifteen ratified corpus rows gated.

plus the two structural firewalls (anti-score, D2-6) and state-rule integrity.

Book 6 Hardening R1 added the ``R1.*`` families, one per reproduced defect:
``R1.COMPARISON_METHODOLOGY``, ``R1.PRICE_PROVENANCE``,
``R1.VALUATION_STALENESS``, ``R1.COVERAGE_SUFFICIENCY``,
``R1.NORMALIZATION_INTEGRITY``, ``R1.RULE_AUTHORITY``,
``R1.METHODOLOGY_REGISTRY``, and ``R1.PRESERVED_SEALS``.

Book 6 Hardening R2 added the ``R2.*`` families for the four defects R1 could
not see: ``R2.METHODOLOGY_CONTENT`` (an identity is not a namespace claim),
``R2.PREDICATE_EXECUTION`` (a ratified rule is replayed, not merely named),
``R2.COVERAGE_CLOSURE`` (per-metric set equality against registry state), and
``R2.HISTORICAL_AUTHORITY`` (a preserved record is not revalidated authority),
plus ``R2.PRESERVED_SEALS`` for the R1 gates that must survive R2.
"""

from __future__ import annotations

from typing import Final

#: The ratified 6D validation families.
VALIDATION_FAMILIES: Final[tuple[str, ...]] = ("6D.1", "6D.2", "6D.3", "6D.4", "6D.5")

#: The structural gates that are not part of the 6D corpus but must be traced.
STRUCTURAL_FAMILIES: Final[tuple[str, ...]] = (
    "FIREWALL.ANTI_SCORE",
    "FIREWALL.D2_6",
    "STATE_RULE_INTEGRITY",
    "MEASUREMENT_KERNEL",
    "NORMALIZATION_LINEAGE",
    "VALUATION_SEAM",
    "METRIC_FAMILIES",
)

#: The Book 6 Hardening R1 families — one per reproduced authority defect, plus
#: the preserved-seal family that proves R1 regressed nothing.
R1_FAMILIES: Final[tuple[str, ...]] = (
    "R1.METHODOLOGY_REGISTRY",
    "R1.COMPARISON_METHODOLOGY",
    "R1.PRICE_PROVENANCE",
    "R1.VALUATION_STALENESS",
    "R1.COVERAGE_SUFFICIENCY",
    "R1.NORMALIZATION_INTEGRITY",
    "R1.RULE_AUTHORITY",
    "R1.PRESERVED_SEALS",
)

#: The Book 6 Hardening R2 families — canonical content, executed predicates,
#: per-metric coverage closure, historical authority honesty, and the R1
#: seals that must survive R2.
R2_FAMILIES: Final[tuple[str, ...]] = (
    "R2.METHODOLOGY_CONTENT",
    "R2.PREDICATE_EXECUTION",
    "R2.COVERAGE_CLOSURE",
    "R2.HISTORICAL_AUTHORITY",
    "R2.PRESERVED_SEALS",
)

#: The Book 6 Hardening R3 families — state derivation authority binding:
#: evaluator/target semantics, predicate content fingerprints,
#: derivation-bound ratification, output provenance, and the R1/R2
#: seals that must survive R3.
R3_FAMILIES: Final[tuple[str, ...]] = (
    "R3.EVALUATOR_SEMANTICS",
    "R3.RATIFICATION_BINDING",
    "R3.OUTPUT_PROVENANCE",
    "R3.PRESERVED_SEALS",
)

#: The Book 6 GAP-7 amendment families -- registered lineage terminality as the
#: supersession source of currentness, and the seals that must survive it.
#: Rung 1 only: these trace the lineage FACTS. The authority verdict arrives at
#: rung 2 and is traced there.
R4_FAMILIES: Final[tuple[str, ...]] = (
    "R4.LINEAGE_TERMINALITY",
    "R4.RESOLVER_ORDER",
    "R4.PRESERVED_SEALS",
)

#: The ratified GAP-7 contract, one family per case family. Rung 3 discharges
#: all forty ratified rows, TERM-6 included.
GAP7_FAMILIES: Final[tuple[str, ...]] = (
    "GAP7.CARRIED",
    "GAP7.STATUS",
    "GAP7.TERMINALITY",
    "GAP7.NV_B",
    "GAP7.STRUCTURAL",
    "GAP7.ACCOUNTING",
)

#: The Book 6 comparison / change amendment families, added at Rung 4 for the
#: two new authority-bearing contract classes. One family per ratified clause so
#: that a defect in the contract shape cannot hide behind a broader row.
CMP_FAMILIES: Final[tuple[str, ...]] = (
    "CMP.CONTRACT_SCOPE",
    "CMP.BASELINE_SELECTOR",
    "CMP.NUMERIC_DOMAIN",
    "CMP.SINGLE_MEANING",
    "CMP.SUPERSESSION",
    "CMP.COVERAGE",
    "CMP.TEMPORAL_COMPARABILITY",
    "CMP.POLICY_FIREWALL",
    "CMP.DISPLAY_SEPARATION",
    "CMP.FINGERPRINT",
    "CMP.RULE_AUTHORITY",
    "CMP.BASELINE_ORDERING",
    "CMP.BASELINE_ELIGIBILITY",
    "CMP.COVERAGE_APPLICABILITY",
    "CMP.COVERAGE_AUTHORITY",
    "CMP.TEMPORAL_COMPARABILITY",
    "CMP.CHANGE_ARITHMETIC",
)

#: Every family the matrix must cover.
ALL_FAMILIES: Final[tuple[str, ...]] = (
    VALIDATION_FAMILIES + STRUCTURAL_FAMILIES + R1_FAMILIES + R2_FAMILIES
    + R3_FAMILIES + R4_FAMILIES + GAP7_FAMILIES + CMP_FAMILIES
)

#: ``(row_id, family, claim, test_file, test_name)``. Every row must resolve.
TRACEABILITY_ROWS: Final[tuple[tuple[str, str, str, str, str], ...]] = (
    # -- 6D.1 missingness ---------------------------------------------------
    (
        "6D.1.01",
        "6D.1",
        "ten distinct missingness states exist and none collapses into another",
        "test_book6_missingness.py",
        "test_ten_distinct_missingness_states",
    ),
    (
        "6D.1.02",
        "6D.1",
        "ZERO_OBSERVED is a measured zero and is not any form of absence",
        "test_book6_missingness.py",
        "test_zero_observed_is_distinct_from_every_absence",
    ),
    (
        "6D.1.03",
        "6D.1",
        "a missingness state that forbids a value may never carry a fabricated zero",
        "test_book6_missingness.py",
        "test_absence_may_never_carry_a_fabricated_zero",
    ),
    (
        "6D.1.04",
        "6D.1",
        "an absent observation carries no value at all",
        "test_book6_missingness.py",
        "test_absence_carries_no_value_at_all",
    ),
    (
        "6D.1.05",
        "6D.1",
        "the engine refuses to read a value out of an absence",
        "test_book6_missingness.py",
        "test_engine_refuses_to_read_a_value_out_of_an_absence",
    ),
    (
        "6D.1.06",
        "6D.1",
        "six distinct denominator states exist",
        "test_book6_missingness.py",
        "test_denominator_states_are_distinct",
    ),
    (
        "6D.1.07",
        "6D.1",
        "an observed-zero denominator yields an undefined ratio, never infinity",
        "test_book6_missingness.py",
        "test_observed_zero_denominator_yields_undefined_not_infinity",
    ),
    (
        "6D.1.08",
        "6D.1",
        "a missing denominator never produces a ratio",
        "test_book6_missingness.py",
        "test_missing_denominator_never_produces_a_ratio",
    ),
    (
        "6D.1.09",
        "6D.1",
        "a coverage observation can never assert sufficiency on its own",
        "test_book6_missingness.py",
        "test_coverage_percentage_asserts_no_sufficiency",
    ),
    # -- 6D.2 methodology sensitivity ---------------------------------------
    (
        "6D.2.01",
        "6D.2",
        "disagreeing methodologies are surfaced as METHODOLOGY_SENSITIVE",
        "test_book6_sensitivity.py",
        "test_disagreeing_methodologies_are_reported_sensitive",
    ),
    (
        "6D.2.02",
        "6D.2",
        "a sensitivity finding names no preferred, best or canonical methodology",
        "test_book6_sensitivity.py",
        "test_a_sensitive_finding_names_no_winner",
    ),
    (
        "6D.2.03",
        "6D.2",
        "each variant retains its own methodology identity",
        "test_book6_sensitivity.py",
        "test_each_variant_keeps_its_own_methodology_identity",
    ),
    (
        "6D.2.04",
        "6D.2",
        "an unobserved variant makes the comparison UNDETERMINED, not zero",
        "test_book6_sensitivity.py",
        "test_an_unobserved_variant_makes_the_comparison_undetermined_not_zero",
    ),
    (
        "6D.2.05",
        "6D.2",
        "a finding carries no numeric severity",
        "test_book6_sensitivity.py",
        "test_sensitivity_finding_carries_no_numeric_severity",
    ),
    (
        "6D.2.06",
        "6D.2",
        "all five ratified methodology divergences are surfaced (accounts, volume, fees, developers, capital)",
        "test_book6_sensitivity.py",
        "test_each_ratified_methodology_divergence_is_surfaced",
    ),
    # -- 6D.3 historical sanity --------------------------------------------
    (
        "6D.3.01",
        "6D.3",
        "a restatement creates a new observation rather than overwriting the prior one",
        "test_book6_temporal.py",
        "test_a_restatement_creates_a_new_observation_rather_than_overwriting",
    ),
    (
        "6D.3.02",
        "6D.3",
        "supersession is linear and ordered",
        "test_book6_temporal.py",
        "test_the_supersession_chain_is_linear_and_ordered",
    ),
    (
        "6D.3.03",
        "6D.3",
        "a forked supersession chain is refused",
        "test_book6_temporal.py",
        "test_a_forked_supersession_chain_is_refused",
    ),
    (
        "6D.3.04",
        "6D.3",
        "history is retained across many revisions",
        "test_book6_temporal.py",
        "test_history_is_retained_across_many_revisions",
    ),
    (
        "6D.3.05",
        "6D.3",
        "a chain reorg is window-bounded and does not rewrite the whole history",
        "test_book6_temporal.py",
        "test_a_reorg_is_window_bounded",
    ),
    (
        "6D.3.06",
        "6D.3",
        "a methodology change creates a new version, never an in-place edit",
        "test_book6_temporal.py",
        "test_a_methodology_change_creates_a_new_version_not_an_edit",
    ),
    (
        "6D.3.07",
        "6D.3",
        "the same sequence replays to the same history",
        "test_book6_temporal.py",
        "test_the_same_sequence_replays_to_the_same_history",
    ),
    (
        "6D.3.08",
        "6D.3",
        "replay does not depend on wall-clock time",
        "test_book6_temporal.py",
        "test_replay_does_not_depend_on_wall_clock_time",
    ),
    (
        "6D.3.09",
        "6D.3",
        "valid time and observed time are independent axes",
        "test_book6_temporal.py",
        "test_observed_at_and_valid_time_are_independent_axes",
    ),
    (
        "6D.3.10",
        "6D.3",
        "a stale Book 2 claim decays the citing measurement's authority",
        "test_book6_temporal.py",
        "test_a_stale_claim_decays_the_measurement_authority",
    ),
    (
        "6D.3.11",
        "6D.3",
        "where Book 2 legally restores authority, Book 6 restores too",
        "test_book6_temporal.py",
        "test_where_book_2_restores_authority_book_6_restores_too",
    ),
    (
        "6D.3.12",
        "6D.3",
        "a decayed measurement survives as queryable history",
        "test_book6_temporal.py",
        "test_the_record_survives_the_decay_as_queryable_history",
    ),
    (
        "6D.3.13",
        "6D.3",
        "partial Book 2 authority grants nothing",
        "test_book6_temporal.py",
        "test_a_partial_authority_grants_nothing",
    ),
    (
        "6D.3.14",
        "6D.3",
        "a stale current price makes a current valuation unavailable",
        "test_book6_temporal.py",
        "test_a_stale_price_makes_the_current_valuation_unavailable",
    ),
    (
        "6D.3.15",
        "6D.3",
        "current unavailability is not historical invalidity (bitemporal)",
        "test_book6_temporal.py",
        "test_currently_unavailable_is_not_historically_invalid",
    ),
    (
        "6D.3.16",
        "6D.3",
        "a source-unavailable price is absent, not zero",
        "test_book6_temporal.py",
        "test_a_source_unavailable_price_is_absent_not_zero",
    ),
    (
        "6D.3.17",
        "6D.3",
        "a market-closed price is stale, not invalid",
        "test_book6_temporal.py",
        "test_a_market_closed_price_is_stale_not_invalid",
    ),
    # -- 6D.4 cross-source parity -------------------------------------------
    (
        "6D.4.01",
        "6D.4",
        "agreeing sources are reported as agreeing",
        "test_book6_sensitivity.py",
        "test_sources_that_agree_are_reported_agreeing",
    ),
    (
        "6D.4.02",
        "6D.4",
        "divergent sources are reported as diverging and both values are preserved",
        "test_book6_sensitivity.py",
        "test_divergent_sources_are_reported_diverging_and_preserved",
    ),
    (
        "6D.4.03",
        "6D.4",
        "no consensus value is computed from divergent sources",
        "test_book6_sensitivity.py",
        "test_no_consensus_value_is_computed_from_divergent_sources",
    ),
    (
        "6D.4.04",
        "6D.4",
        "the module offers no averaging, median or blending helper",
        "test_book6_sensitivity.py",
        "test_the_module_offers_no_averaging_helper",
    ),
    (
        "6D.4.05",
        "6D.4",
        "an absent source is not a source that agrees",
        "test_book6_sensitivity.py",
        "test_an_absent_source_is_not_a_source_that_agrees",
    ),
    (
        "6D.4.06",
        "6D.4",
        "no tolerance is invented; near-equal floats are reported as divergence",
        "test_book6_sensitivity.py",
        "test_no_tolerance_is_invented_for_float_agreement",
    ),
    # -- 6D.5 false-comparison detection -------------------------------------
    (
        "6D.5.01",
        "6D.5",
        "the corpus carries the fifteen ratified rows",
        "test_book6_comparability.py",
        "test_corpus_has_the_fifteen_ratified_rows",
    ),
    (
        "6D.5.02",
        "6D.5",
        "every operator-required comparison has a mechanized row",
        "test_book6_comparability.py",
        "test_every_required_operator_comparison_has_a_row",
    ),
    (
        "6D.5.03",
        "6D.5",
        "no corpus row is a bare comparable verdict",
        "test_book6_comparability.py",
        "test_no_row_is_a_bare_comparable_verdict",
    ),
    (
        "6D.5.04",
        "6D.5",
        "every ratified pair is refused without its named methodology",
        "test_book6_comparability.py",
        "test_every_ratified_pair_is_refused_without_its_methodology",
    ),
    (
        "6D.5.05",
        "6D.5",
        "a NOT_COMPARABLE pair stays refused even with a methodology",
        "test_book6_comparability.py",
        "test_not_comparable_pairs_stay_refused_even_with_a_methodology",
    ),
    (
        "6D.5.06",
        "6D.5",
        "an AS_DISTINCT pair is licensed only as separate metrics",
        "test_book6_comparability.py",
        "test_as_distinct_pairs_are_never_a_comparison",
    ),
    (
        "6D.5.07",
        "6D.5",
        "the gate is symmetric",
        "test_book6_comparability.py",
        "test_the_gate_is_symmetric",
    ),
    (
        "6D.5.08",
        "6D.5",
        "an ungoverned pair is refused rather than defaulted",
        "test_book6_comparability.py",
        "test_an_ungoverned_pair_is_refused_not_defaulted",
    ),
    (
        "6D.5.09",
        "6D.5",
        "a wildcard comparison is refused",
        "test_book6_comparability.py",
        "test_a_wildcard_comparison_is_refused",
    ),
    (
        "6D.5.10",
        "6D.5",
        "mismatched comparability classes are refused even under a named methodology",
        "test_book6_comparability.py",
        "test_comparability_classes_must_match_even_under_a_named_methodology",
    ),
    (
        "6D.5.11",
        "6D.5",
        "the engine routes every comparison through the same gate",
        "test_book6_comparability.py",
        "test_engine_comparison_goes_through_the_same_gate",
    ),
    # -- structural firewall: anti-score ------------------------------------
    (
        "FW.AS.01",
        "FIREWALL.ANTI_SCORE",
        "the vector declares no score, total, rating, grade or rank field",
        "test_book6_state_vector.py",
        "test_the_vector_has_no_score_fields",
    ),
    (
        "FW.AS.02",
        "FIREWALL.ANTI_SCORE",
        "constructor injection of a score field is refused",
        "test_book6_state_vector.py",
        "test_constructor_injection_of_an_anti_score_field_fails",
    ),
    (
        "FW.AS.03",
        "FIREWALL.ANTI_SCORE",
        "model_copy injection of a score field is refused, not smuggled",
        "test_book6_state_vector.py",
        "test_model_copy_injection_of_an_anti_score_field_is_refused",
    ),
    (
        "FW.AS.04",
        "FIREWALL.ANTI_SCORE",
        "raw dict deserialization of a score field is refused",
        "test_book6_state_vector.py",
        "test_raw_dict_deserialization_of_an_anti_score_field_fails",
    ),
    (
        "FW.AS.05",
        "FIREWALL.ANTI_SCORE",
        "a serialization round-trip injects nothing",
        "test_book6_state_vector.py",
        "test_a_serialization_round_trip_injects_nothing",
    ),
    (
        "FW.AS.06",
        "FIREWALL.ANTI_SCORE",
        "nested payload injection into a dimension is refused",
        "test_book6_state_vector.py",
        "test_nested_payload_injection_into_a_dimension_fails",
    ),
    (
        "FW.AS.07",
        "FIREWALL.ANTI_SCORE",
        "a nested dimension may not carry a prescriptive name",
        "test_book6_state_vector.py",
        "test_a_nested_dimension_cannot_carry_a_prescriptive_name",
    ),
    (
        "FW.AS.08",
        "FIREWALL.ANTI_SCORE",
        "no Book 6 record class declares a score field",
        "test_book6_state_vector.py",
        "test_no_book6_record_class_declares_a_score_field",
    ),
    (
        "FW.AS.09",
        "FIREWALL.ANTI_SCORE",
        "there is no numeric completeness score",
        "test_book6_state_vector.py",
        "test_there_is_no_numeric_completeness_score",
    ),
    # -- structural firewall: D2-6 -----------------------------------------
    (
        "FW.D26.01",
        "FIREWALL.D2_6",
        "no usage, health, retention, bot or adoption state exists",
        "test_book6_state_vector.py",
        "test_no_usage_health_state_exists",
    ),
    (
        "FW.D26.02",
        "FIREWALL.D2_6",
        "D6M-5 names are prohibited state names",
        "test_book6_state_vector.py",
        "test_d2_6_names_are_prohibited_state_names",
    ),
    (
        "FW.D26.03",
        "FIREWALL.D2_6",
        "no usage or health threshold appears on the Book 6 surface",
        "test_book6_state_vector.py",
        "test_no_usage_threshold_appears_anywhere_in_the_book6_surface",
    ),
    (
        "FW.D26.04",
        "FIREWALL.D2_6",
        "no D2-6 research executor exists anywhere in Book 6",
        "test_book6_adversarial.py",
        "test_no_d2_6_research_executor_exists_in_book6",
    ),
    # -- state-rule integrity -----------------------------------------------
    (
        "SR.01",
        "STATE_RULE_INTEGRITY",
        "INDIVIDUAL_STATE_RULES_RATIFIED is 0 at bootstrap",
        "test_book6_state_rules.py",
        "test_bootstrap_ratified_count_is_zero",
    ),
    (
        "SR.02",
        "STATE_RULE_INTEGRITY",
        "a fresh registry holds no rules at all",
        "test_book6_state_rules.py",
        "test_a_fresh_registry_holds_no_rules_at_all",
    ),
    (
        "SR.03",
        "STATE_RULE_INTEGRITY",
        "registering a rule does not ratify it",
        "test_book6_state_rules.py",
        "test_registering_a_rule_does_not_ratify_it",
    ),
    (
        "SR.04",
        "STATE_RULE_INTEGRITY",
        "no Class B or C state is emittable at bootstrap",
        "test_book6_state_rules.py",
        "test_no_class_b_or_c_state_is_emittable_at_bootstrap",
    ),
    (
        "SR.05",
        "STATE_RULE_INTEGRITY",
        "the engine refuses to emit any Class B or C state",
        "test_book6_state_rules.py",
        "test_the_engine_refuses_to_emit_any_class_b_or_c_state",
    ),
    (
        "SR.06",
        "STATE_RULE_INTEGRITY",
        "synthetic fixture ratification is local and never becomes canonical",
        "test_book6_state_rules.py",
        "test_synthetic_ratification_is_local_and_not_canonical",
    ),
    (
        "SR.07",
        "STATE_RULE_INTEGRITY",
        "there is no delegated, bulk or automatic ratification path",
        "test_book6_state_rules.py",
        "test_there_is_no_delegated_or_automatic_ratification_path",
    ),
    (
        "SR.08",
        "STATE_RULE_INTEGRITY",
        "Class A states are emittable with no rule and may not carry one",
        "test_book6_state_rules.py",
        "test_a_class_a_state_may_not_carry_a_rule",
    ),
    (
        "SR.09",
        "STATE_RULE_INTEGRITY",
        "generic EXPANDING/CONTRACTING are deferred and unwritable as a rule",
        "test_book6_state_rules.py",
        "test_no_rule_can_be_written_for_a_generic_state",
    ),
    (
        "SR.10",
        "STATE_RULE_INTEGRITY",
        "a new rule version does not inherit the prior ratification",
        "test_book6_state_rules.py",
        "test_a_new_version_does_not_inherit_the_prior_ratification",
    ),
    (
        "SR.11",
        "STATE_RULE_INTEGRITY",
        "a forged RATIFIED flag does not authorize a state",
        "test_book6_adversarial.py",
        "test_a_forged_ratified_flag_does_not_authorize_a_state",
    ),
    (
        "SR.12",
        "STATE_RULE_INTEGRITY",
        "an unregistered state rule is refused",
        "test_book6_state_rules.py",
        "test_an_unregistered_rule_ref_is_refused",
    ),
    (
        "SR.13",
        "STATE_RULE_INTEGRITY",
        "no data reports INSUFFICIENT_DATA rather than zero",
        "test_book6_state_rules.py",
        "test_no_data_reports_insufficient_data_not_zero",
    ),
    (
        "SR.14",
        "STATE_RULE_INTEGRITY",
        "unratified coverage sufficiency is reported, never assumed",
        "test_book6_state_rules.py",
        "test_unratified_coverage_sufficiency_is_reported_not_assumed",
    ),
    # -- measurement-kernel invariants --------------------------------------
    (
        "MK.01",
        "MEASUREMENT_KERNEL",
        "DATA_COMPLETE fails closed without a ratified coverage-sufficiency rule",
        "test_book6_state_vector.py",
        "test_fully_observed_dimensions_still_fail_closed_without_a_sufficiency_rule",
    ),
    (
        "MK.02",
        "MEASUREMENT_KERNEL",
        "no coverage-sufficiency rule exists to name at bootstrap",
        "test_book6_state_vector.py",
        "test_no_coverage_sufficiency_rule_exists_to_name_at_bootstrap",
    ),
    (
        "MK.03",
        "MEASUREMENT_KERNEL",
        "the twenty-one grammar categories remain distinct types and do not collapse",
        "test_book6_core.py",
        "test_grammar_categories_remain_distinct_types",
    ),
    (
        "MK.04",
        "MEASUREMENT_KERNEL",
        "COUNT is not FLOW, FLOW is not STOCK, RATE is not RATIO",
        "test_book6_core.py",
        "test_count_is_not_sum_and_flow_is_not_stock",
    ),
    (
        "MK.05",
        "MEASUREMENT_KERNEL",
        "NORMALIZED is a distinct measurement role, not a flag",
        "test_book6_core.py",
        "test_normalized_is_a_distinct_role",
    ),
    (
        "MK.06",
        "MEASUREMENT_KERNEL",
        "a MeasurementObservation is not a Book 2 claim (D6M-1 = A)",
        "test_book6_core.py",
        "test_measurement_is_not_a_book2_claim",
    ),
    (
        "MK.07",
        "MEASUREMENT_KERNEL",
        "the provenance adapter refuses a defaulted or disabled resolver",
        "test_book6_core.py",
        "test_book6_provenance_requires_explicit_resolver",
    ),
    (
        "MK.08",
        "MEASUREMENT_KERNEL",
        "an unknown Book 2 claim reference fails closed",
        "test_book6_core.py",
        "test_unknown_claim_ref_fails_closed",
    ),
    (
        "MK.09",
        "MEASUREMENT_KERNEL",
        "a value-bearing observation requires live Book 2 authority",
        "test_book6_core.py",
        "test_value_bearing_observation_requires_book2_authority",
    ),
    (
        "MK.10",
        "MEASUREMENT_KERNEL",
        "a metric name alone is not a definition",
        "test_book6_core.py",
        "test_metric_name_alone_is_not_a_definition",
    ),
    (
        "MK.11",
        "MEASUREMENT_KERNEL",
        "a ratio definition must declare its denominator rule",
        "test_book6_core.py",
        "test_ratio_definition_must_declare_denominator_rule",
    ),
    (
        "MK.12",
        "MEASUREMENT_KERNEL",
        "a cross-architecture class may not be scoped to specific families",
        "test_book6_core.py",
        "test_cross_architecture_class_may_not_be_scoped_to_families",
    ),
    (
        "MK.13",
        "MEASUREMENT_KERNEL",
        "architecture applicability is an explicit allow-list",
        "test_book6_core.py",
        "test_architecture_applicability_is_an_allow_list",
    ),
    (
        "MK.14",
        "MEASUREMENT_KERNEL",
        "a windowed metric requires an explicit interval",
        "test_book6_core.py",
        "test_windowed_metric_requires_explicit_interval",
    ),
    (
        "MK.15",
        "MEASUREMENT_KERNEL",
        "an instantaneous metric may not declare an interval",
        "test_book6_core.py",
        "test_instantaneous_metric_may_not_declare_interval",
    ),
    (
        "MK.16",
        "MEASUREMENT_KERNEL",
        "a value-bearing state requires both its value and its unit",
        "test_book6_core.py",
        "test_value_bearing_state_requires_value_and_unit",
    ),
    (
        "MK.17",
        "MEASUREMENT_KERNEL",
        "a measurement requires a registered definition and may not define its own metric",
        "test_book6_core.py",
        "test_measurement_requires_registered_definition",
    ),
    (
        "MK.18",
        "MEASUREMENT_KERNEL",
        "an observation drifting from its definition is refused",
        "test_book6_core.py",
        "test_observation_drifting_from_definition_is_refused",
    ),
    # -- normalization lineage (D6M-2 = B) ---------------------------------
    (
        "NL.01",
        "NORMALIZATION_LINEAGE",
        "the NormalizationRule contract binds every ratified field",
        "test_book6_normalization.py",
        "test_normalization_rule_requires_every_ratified_field",
    ),
    (
        "NL.02",
        "NORMALIZATION_LINEAGE",
        "normalization is not a field on the metric definition",
        "test_book6_normalization.py",
        "test_normalization_is_not_a_field_on_the_metric_definition",
    ),
    (
        "NL.03",
        "NORMALIZATION_LINEAGE",
        "normalization is not a field on the measurement observation",
        "test_book6_normalization.py",
        "test_normalization_is_not_a_field_on_the_measurement_observation",
    ),
    (
        "NL.04",
        "NORMALIZATION_LINEAGE",
        "a normalized product requires native lineage at construction",
        "test_book6_normalization.py",
        "test_normalized_product_requires_native_lineage_at_construction",
    ),
    (
        "NL.05",
        "NORMALIZATION_LINEAGE",
        "lineage pointed at a different native set is refused",
        "test_book6_normalization.py",
        "test_lineage_pointed_at_a_different_native_set_is_refused",
    ),
    (
        "NL.06",
        "NORMALIZATION_LINEAGE",
        "lineage cannot be widened by appending fabricated inputs",
        "test_book6_normalization.py",
        "test_lineage_cannot_be_widened_by_appending_fabricated_inputs",
    ),
    (
        "NL.07",
        "NORMALIZATION_LINEAGE",
        "model_copy cannot strip lineage and still authorize",
        "test_book6_normalization.py",
        "test_model_copy_cannot_strip_lineage_and_still_authorize",
    ),
    (
        "NL.08",
        "NORMALIZATION_LINEAGE",
        "NORMALIZED_WITHOUT_NATIVE_LINEAGE is invalid end to end",
        "test_book6_normalization.py",
        "test_normalized_without_native_lineage_is_invalid_end_to_end",
    ),
    (
        "NL.09",
        "NORMALIZATION_LINEAGE",
        "PERCENTILE is not a normalization type and cannot be built or injected",
        "test_book6_normalization.py",
        "test_percentile_cannot_be_constructed_even_as_a_raw_string",
    ),
    (
        "NL.10",
        "NORMALIZATION_LINEAGE",
        "a cohort-relative normalization must name its cohort",
        "test_book6_normalization.py",
        "test_cohort_relative_normalization_requires_a_cohort",
    ),
    (
        "NL.11",
        "NORMALIZATION_LINEAGE",
        "a dividing normalization must name its denominator",
        "test_book6_normalization.py",
        "test_dividing_normalization_requires_a_denominator",
    ),
    (
        "NL.12",
        "NORMALIZATION_LINEAGE",
        "cohort membership is explicit, never an implicit all-chains",
        "test_book6_normalization.py",
        "test_cohort_membership_is_explicit_not_implicit_all_chains",
    ),
    (
        "NL.13",
        "NORMALIZATION_LINEAGE",
        "normalization admissibility is scoped to the metric category",
        "test_book6_normalization.py",
        "test_per_user_is_invalid_for_a_ratio_metric",
    ),
    (
        "NL.14",
        "NORMALIZATION_LINEAGE",
        "a normalized product is never registered as a native measurement",
        "test_book6_normalization.py",
        "test_normalized_products_are_never_registered_as_native_measurements",
    ),
    # -- valuation seam (D6M-4 = A) -----------------------------------------
    (
        "VS.01",
        "VALUATION_SEAM",
        "a valuation requires an explicit numeraire with no default",
        "test_book6_valuation.py",
        "test_numeraire_is_required",
    ),
    (
        "VS.02",
        "VALUATION_SEAM",
        "USD is not the default numeraire",
        "test_book6_valuation.py",
        "test_usd_is_not_the_default_numeraire",
    ),
    (
        "VS.03",
        "VALUATION_SEAM",
        "no common value exists without an explicit cited price observation",
        "test_book6_valuation.py",
        "test_no_common_value_without_a_price_observation",
    ),
    (
        "VS.04",
        "VALUATION_SEAM",
        "price authority is purpose-specific across every ratified purpose",
        "test_book6_valuation.py",
        "test_price_authority_is_purpose_specific",
    ),
    (
        "VS.05",
        "VALUATION_SEAM",
        "no price class is admissible for every purpose, so no global winner exists",
        "test_book6_valuation.py",
        "test_no_price_class_is_admissible_for_every_purpose",
    ),
    (
        "VS.06",
        "VALUATION_SEAM",
        "divergent price classes are preserved side by side and never merged",
        "test_book6_valuation.py",
        "test_divergent_price_classes_are_preserved_side_by_side",
    ),
    (
        "VS.07",
        "VALUATION_SEAM",
        "there is no consensus price combinator",
        "test_book6_valuation.py",
        "test_there_is_no_consensus_price_combinator",
    ),
    (
        "VS.08",
        "VALUATION_SEAM",
        "the Book 5 write-back refusal is explicit and named",
        "test_book6_valuation.py",
        "test_book_5_write_back_is_explicitly_refused",
    ),
    (
        "VS.09",
        "VALUATION_SEAM",
        "no Book 6 module imports Book 5, so the seam is structurally write-free",
        "test_book6_valuation.py",
        "test_no_book6_api_writes_into_a_book_5_record",
    ),
    (
        "VS.10",
        "VALUATION_SEAM",
        "no Book 6 module imports the Book 4 dependency graph",
        "test_book6_valuation.py",
        "test_no_book6_measurement_api_can_rewrite_a_book_4_edge",
    ),
    (
        "VS.11",
        "VALUATION_SEAM",
        "no Book 6 API can rewrite a dependency edge",
        "test_book6_valuation.py",
        "test_no_book6_module_mutates_a_dependency_edge",
    ),
    (
        "VS.12",
        "VALUATION_SEAM",
        "the engine re-reads the numeraire at use, refusing a stripped copy",
        "test_book6_valuation.py",
        "test_engine_rejects_a_stripped_numeraire_that_reuses_an_admissible_price",
    ),
    (
        "VS.13",
        "VALUATION_SEAM",
        "the engine re-reads the price source at use, refusing a stripped copy",
        "test_book6_valuation.py",
        "test_engine_rejects_a_price_with_a_stripped_source",
    ),
    # -- metric families (Phase 28) -----------------------------------------
    (
        "MF.01",
        "METRIC_FAMILIES",
        "the five ratified 6A families exist as schema",
        "test_book6_families.py",
        "test_the_five_ratified_families_are_present",
    ),
    (
        "MF.02",
        "METRIC_FAMILIES",
        "no default metric is shipped and the registry holds no pre-registered definitions",
        "test_book6_families.py",
        "test_the_registry_ships_no_pre_registered_definitions",
    ),
    (
        "MF.03",
        "METRIC_FAMILIES",
        "a scoped definition is NOT_SUPPORTED outside its architectures",
        "test_book6_families.py",
        "test_a_scoped_definition_is_not_supported_outside_its_architectures",
    ),
    (
        "MF.04",
        "METRIC_FAMILIES",
        "NOT_SUPPORTED is not zero",
        "test_book6_families.py",
        "test_not_supported_is_not_zero",
    ),
    (
        "MF.05",
        "METRIC_FAMILIES",
        "a scoped definition requires a declared architecture family",
        "test_book6_families.py",
        "test_a_scoped_definition_requires_a_declared_architecture_family",
    ),
    (
        "MF.06",
        "METRIC_FAMILIES",
        "measurement roles remain distinct across families",
        "test_book6_families.py",
        "test_measurement_roles_remain_distinct_across_families",
    ),
    # -- R1.D5 methodology registry ----------------------------------------
    (
        "R1.MR.01",
        "R1.METHODOLOGY_REGISTRY",
        "the methodology registry required by the authorized design exists",
        "test_book6_hardening_r1.py",
        "test_r1_d5_the_five_separated_stores_all_exist",
    ),
    (
        "R1.MR.02",
        "R1.METHODOLOGY_REGISTRY",
        "methodology identity is a versioned ref@version string, parsed exactly",
        "test_book6_hardening_r1.py",
        "test_r1_d5_methodology_identity_is_versioned_and_exact",
    ),
    (
        "R1.MR.03",
        "R1.METHODOLOGY_REGISTRY",
        "an empty methodology reference resolves to nothing",
        "test_book6_hardening_r1.py",
        "test_r1_d5_an_empty_methodology_ref_resolves_to_nothing",
    ),
    (
        "R1.MR.04",
        "R1.METHODOLOGY_REGISTRY",
        "a metric definition may not name an unregistered methodology",
        "test_book6_hardening_r1.py",
        "test_r1_d5_a_metric_definition_may_not_name_an_unregistered_methodology",
    ),
    (
        "R1.MR.05",
        "R1.METHODOLOGY_REGISTRY",
        "a measurement may not name an unregistered methodology",
        "test_book6_hardening_r1.py",
        "test_r1_d5_a_measurement_may_not_name_an_unregistered_methodology",
    ),
    (
        "R1.MR.06",
        "R1.METHODOLOGY_REGISTRY",
        "a measurement loses authority when its methodology is invalidated",
        "test_book6_hardening_r1.py",
        "test_r1_d5_a_measurement_loses_authority_when_its_methodology_is_invalidated",
    ),
    (
        "R1.MR.07",
        "R1.METHODOLOGY_REGISTRY",
        "the no-free-string-methodology-authority invariant is asserted",
        "test_book6_hardening_r1.py",
        "test_r1_d5_no_free_string_methodology_authority_constant",
    ),
    # -- R1.D1 comparison methodology --------------------------------------
    (
        "R1.CM.01",
        "R1.COMPARISON_METHODOLOGY",
        "FC-05 with a fabricated methodology ref is refused (R1-D1 A1)",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a1_fake_methodology_ref_is_refused_for_fc05",
    ),
    (
        "R1.CM.02",
        "R1.COMPARISON_METHODOLOGY",
        "FC-07 with another row's methodology is refused (R1-D1 A2)",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a2_the_wrong_named_methodology_is_refused_for_fc07",
    ),
    (
        "R1.CM.03",
        "R1.COMPARISON_METHODOLOGY",
        "the correct name but unregistered is refused (R1-D1 A3)",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a3_the_correct_name_but_unregistered_is_refused",
    ),
    (
        "R1.CM.04",
        "R1.COMPARISON_METHODOLOGY",
        "a registered but unrelated methodology is refused (R1-D1 A4)",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a4_a_registered_unrelated_methodology_is_refused",
    ),
    (
        "R1.CM.05",
        "R1.COMPARISON_METHODOLOGY",
        "the exact required, registered, row-authorized methodology authorizes",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a5_the_exact_required_methodology_authorizes",
    ),
    (
        "R1.CM.06",
        "R1.COMPARISON_METHODOLOGY",
        "identity alone is insufficient without row authorization",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a5b_identity_alone_is_not_enough_without_row_authority",
    ),
    (
        "R1.CM.07",
        "R1.COMPARISON_METHODOLOGY",
        "a superseded methodology stops authorizing the comparison (A6)",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a6_a_superseded_methodology_stops_authorizing",
    ),
    (
        "R1.CM.08",
        "R1.COMPARISON_METHODOLOGY",
        "a locally invalidated methodology stops authorizing (A6)",
        "test_book6_hardening_r1.py",
        "test_r1_d1_a6b_a_locally_invalidated_methodology_stops_authorizing",
    ),
    (
        "R1.CM.09",
        "R1.COMPARISON_METHODOLOGY",
        "no substring, alias or near-miss name resolves to the required methodology",
        "test_book6_hardening_r1.py",
        "test_r1_d1_no_substring_or_alias_matching",
    ),
    (
        "R1.CM.10",
        "R1.COMPARISON_METHODOLOGY",
        "every CONDITIONAL corpus row requires a versioned methodology identity",
        "test_book6_hardening_r1.py",
        "test_r1_d1_every_conditional_row_requires_a_versioned_identity",
    ),
    # -- R1.D2 price provenance ---------------------------------------------
    (
        "R1.PP.01",
        "R1.PRICE_PROVENANCE",
        "a price observation must cite Book 2 claims",
        "test_book6_hardening_r1.py",
        "test_r1_d2_a_price_observation_must_cite_book_2_claims",
    ),
    (
        "R1.PP.02",
        "R1.PRICE_PROVENANCE",
        "an empty price claim-ref tuple is refused",
        "test_book6_hardening_r1.py",
        "test_r1_d2_an_empty_claim_ref_tuple_is_refused",
    ),
    (
        "R1.PP.03",
        "R1.PRICE_PROVENANCE",
        "the fabricated price-source reproducer is refused (R1-D2)",
        "test_book6_hardening_r1.py",
        "test_r1_d2_the_fake_price_source_reproducer_is_now_refused",
    ),
    (
        "R1.PP.04",
        "R1.PRICE_PROVENANCE",
        "a source_ref string alone is never epistemic evidence",
        "test_book6_hardening_r1.py",
        "test_r1_d2_a_source_ref_string_alone_is_never_epistemic_evidence",
    ),
    (
        "R1.PP.05",
        "R1.PRICE_PROVENANCE",
        "Book 2 decay propagates to price and valuation authority",
        "test_book6_hardening_r1.py",
        "test_r1_d2_and_d4_price_book2_decay_propagates",
    ),
    (
        "R1.PP.06",
        "R1.PRICE_PROVENANCE",
        "a detached evidence ref on the price claim is caught",
        "test_book6_hardening_r1.py",
        "test_r1_d2_evidence_cited_by_a_price_claim_must_not_be_detached",
    ),
    (
        "R1.PP.07",
        "R1.PRICE_PROVENANCE",
        "valid Book 2 claim with the wrong price class is refused",
        "test_book6_hardening_r1.py",
        "test_r1_d4_valid_book2_claim_with_the_wrong_price_class_is_refused",
    ),
    (
        "R1.PP.08",
        "R1.PRICE_PROVENANCE",
        "correct price class with a fabricated Book 2 claim is refused",
        "test_book6_hardening_r1.py",
        "test_r1_d4_correct_price_class_with_a_fake_book2_claim_is_refused",
    ),
    (
        "R1.PP.09",
        "R1.PRICE_PROVENANCE",
        "both requirements satisfied authorizes the valuation",
        "test_book6_hardening_r1.py",
        "test_r1_d4_both_requirements_met_authorizes",
    ),
    (
        "R1.PP.10",
        "R1.PRICE_PROVENANCE",
        "price evidence existing is not admissibility for purpose",
        "test_book6_hardening_r1.py",
        "test_r1_d4_evidence_exists_is_not_admissible_for_purpose",
    ),
    (
        "R1.PP.11",
        "R1.PRICE_PROVENANCE",
        "price authority restores when Book 2 legally restores it",
        "test_book6_hardening_r1.py",
        "test_r1_d4_price_authority_restores_when_book_2_restores",
    ),
    (
        "R1.PP.12",
        "R1.PRICE_PROVENANCE",
        "a valuation may not name an unregistered conversion methodology",
        "test_book6_hardening_r1.py",
        "test_r1_d4_a_valuation_may_not_name_an_unregistered_conversion_methodology",
    ),
    # -- R1.D3 bitemporal valuation authority --------------------------------
    (
        "R1.VS.01",
        "R1.VALUATION_STALENESS",
        "the stale-current-valuation reproducer is refused (R1-D3)",
        "test_book6_hardening_r1.py",
        "test_r1_d3_the_stale_current_valuation_reproducer_is_now_refused",
    ),
    (
        "R1.VS.02",
        "R1.VALUATION_STALENESS",
        "a fresh price at the same instant authorizes a current valuation",
        "test_book6_hardening_r1.py",
        "test_r1_d3_a_fresh_price_at_the_same_instant_authorizes",
    ),
    (
        "R1.VS.03",
        "R1.VALUATION_STALENESS",
        "staleness is evaluated at the explicit as_of, never a hidden wall clock",
        "test_book6_hardening_r1.py",
        "test_r1_d3_staleness_is_evaluated_at_the_explicit_as_of_not_wall_clock",
    ),
    (
        "R1.VS.04",
        "R1.VALUATION_STALENESS",
        "current unavailable is not historically invalid",
        "test_book6_hardening_r1.py",
        "test_r1_d3_current_unavailable_is_not_historically_invalid",
    ),
    (
        "R1.VS.05",
        "R1.VALUATION_STALENESS",
        "a valuation already stale when observed is not historically valid",
        "test_book6_hardening_r1.py",
        "test_r1_d3_a_valuation_already_stale_when_observed_is_not_historically_valid",
    ),
    (
        "R1.VS.06",
        "R1.VALUATION_STALENESS",
        "historical validation still requires Book 2 authority",
        "test_book6_hardening_r1.py",
        "test_r1_d3_historical_validation_still_requires_book_2_authority",
    ),
    (
        "R1.VS.07",
        "R1.VALUATION_STALENESS",
        "the ambiguous single authorization API is gone",
        "test_book6_hardening_r1.py",
        "test_r1_d3_the_ambiguous_single_api_is_gone",
    ),
    # -- R1.D4 coverage sufficiency and DATA_COMPLETE -----------------------
    (
        "R1.CS.01",
        "R1.COVERAGE_SUFFICIENCY",
        "the fake coverage-rule reproducer is refused (R1-D4)",
        "test_book6_hardening_r1.py",
        "test_r1_d4_the_fake_coverage_rule_reproducer_is_now_refused",
    ),
    (
        "R1.CS.02",
        "R1.COVERAGE_SUFFICIENCY",
        "no arbitrary rule ref reaches DATA_COMPLETE",
        "test_book6_hardening_r1.py",
        "test_r1_d4_no_arbitrary_ref_reaches_data_complete",
    ),
    (
        "R1.CS.03",
        "R1.COVERAGE_SUFFICIENCY",
        "an attestation alone, without matching refs, is refused",
        "test_book6_hardening_r1.py",
        "test_r1_d4_an_attestation_alone_is_not_enough",
    ),
    (
        "R1.CS.04",
        "R1.COVERAGE_SUFFICIENCY",
        "an attestation whose scope misses a dimension fails closed",
        "test_book6_hardening_r1.py",
        "test_r1_d4_a_scope_that_misses_a_dimension_fails_closed",
    ),
    (
        "R1.CS.05",
        "R1.COVERAGE_SUFFICIENCY",
        "the coverage-rule bootstrap ratification count is zero",
        "test_book6_hardening_r1.py",
        "test_r1_d4_coverage_rule_bootstrap_count_is_zero",
    ),
    (
        "R1.CS.06",
        "R1.COVERAGE_SUFFICIENCY",
        "registering a coverage rule is not ratifying it",
        "test_book6_hardening_r1.py",
        "test_r1_d4_registration_is_not_ratification",
    ),
    (
        "R1.CS.07",
        "R1.COVERAGE_SUFFICIENCY",
        "an unratified coverage rule authorizes no sufficiency",
        "test_book6_hardening_r1.py",
        "test_r1_d4_an_unratified_rule_cannot_authorize_sufficiency",
    ),
    (
        "R1.CS.08",
        "R1.COVERAGE_SUFFICIENCY",
        "an unknown coverage rule ref authorizes no sufficiency",
        "test_book6_hardening_r1.py",
        "test_r1_d4_an_unknown_rule_ref_cannot_authorize_sufficiency",
    ),
    (
        "R1.CS.09",
        "R1.COVERAGE_SUFFICIENCY",
        "a coverage rule scoped to another metric authorizes nothing",
        "test_book6_hardening_r1.py",
        "test_r1_d4_a_wrong_metric_scope_cannot_authorize_sufficiency",
    ),
    (
        "R1.CS.10",
        "R1.COVERAGE_SUFFICIENCY",
        "superseding a coverage rule drops its ratification",
        "test_book6_hardening_r1.py",
        "test_r1_d4_a_superseded_rule_loses_its_ratification",
    ),
    (
        "R1.CS.11",
        "R1.COVERAGE_SUFFICIENCY",
        "a valid locally ratified synthetic rule reaches DATA_COMPLETE",
        "test_book6_hardening_r1.py",
        "test_r1_d4_a_valid_synthetic_ratified_rule_reaches_data_complete",
    ),
    (
        "R1.CS.12",
        "R1.COVERAGE_SUFFICIENCY",
        "at bootstrap DATA_COMPLETE is unreachable",
        "test_book6_hardening_r1.py",
        "test_r1_d4_bootstrap_data_status_fails_closed",
    ),
    (
        "R1.CS.13",
        "R1.COVERAGE_SUFFICIENCY",
        "a full numeric coverage fraction never reaches DATA_COMPLETE",
        "test_book6_hardening_r1.py",
        "test_r1_d4_a_full_coverage_fraction_alone_never_reaches_data_complete",
    ),
    # -- R1.D6 normalized value integrity ------------------------------------
    (
        "R1.NI.01",
        "R1.NORMALIZATION_INTEGRITY",
        "the forged normalized-value reproducer is refused (R1-D6)",
        "test_book6_hardening_r1.py",
        "test_r1_d6_the_forged_normalized_value_reproducer_is_now_refused",
    ),
    (
        "R1.NI.02",
        "R1.NORMALIZATION_INTEGRITY",
        "the correctly derived value authorizes",
        "test_book6_hardening_r1.py",
        "test_r1_d6_the_correctly_derived_value_authorizes",
    ),
    (
        "R1.NI.03",
        "R1.NORMALIZATION_INTEGRITY",
        "a near-miss value is still refused",
        "test_book6_hardening_r1.py",
        "test_r1_d6_a_near_miss_value_is_still_refused",
    ),
    (
        "R1.NI.04",
        "R1.NORMALIZATION_INTEGRITY",
        "normalized computation is deterministic over its declared inputs",
        "test_book6_hardening_r1.py",
        "test_r1_d6_compute_normalized_value_is_deterministic_and_total",
    ),
    (
        "R1.NI.05",
        "R1.NORMALIZATION_INTEGRITY",
        "base-relative normalizations are computed, not asserted",
        "test_book6_hardening_r1.py",
        "test_r1_d6_base_relative_normalizations_are_computed_not_asserted",
    ),
    (
        "R1.NI.06",
        "R1.NORMALIZATION_INTEGRITY",
        "an observed-zero divisor yields UNDEFINED, never zero or infinity",
        "test_book6_hardening_r1.py",
        "test_r1_d6_a_zero_divisor_yields_undefined_not_zero_or_infinity",
    ),
    (
        "R1.NI.07",
        "R1.NORMALIZATION_INTEGRITY",
        "a normalization rule methodology that resolves to nothing is refused",
        "test_book6_hardening_r1.py",
        "test_r1_d9_a_rule_methodology_that_resolves_to_nothing_is_refused",
    ),
    (
        "R1.NI.08",
        "R1.NORMALIZATION_INTEGRITY",
        "a rule methodology that does not declare its inputs is refused",
        "test_book6_hardening_r1.py",
        "test_r1_d9_a_rule_methodology_that_does_not_declare_its_inputs_is_refused",
    ),
    (
        "R1.NI.09",
        "R1.NORMALIZATION_INTEGRITY",
        "a matching rule methodology continues to authorize",
        "test_book6_hardening_r1.py",
        "test_r1_d9_a_matching_rule_methodology_continues",
    ),
    (
        "R1.NI.10",
        "R1.NORMALIZATION_INTEGRITY",
        "a rule for metric A may not consume metric B measurements",
        "test_book6_hardening_r1.py",
        "test_r1_d9_a_rule_for_metric_a_may_not_consume_metric_b",
    ),
    (
        "R1.NI.11",
        "R1.NORMALIZATION_INTEGRITY",
        "a product unit may not diverge from its output metric definition",
        "test_book6_hardening_r1.py",
        "test_r1_d9_a_product_unit_may_not_diverge_from_its_output_metric",
    ),
    (
        "R1.NI.12",
        "R1.NORMALIZATION_INTEGRITY",
        "native-before-normalized lineage is still enforced after R1",
        "test_book6_hardening_r1.py",
        "test_r1_d6_native_before_normalized_is_still_enforced",
    ),
    # -- R1.D7 / Phase 12 rule authority and post-construction attacks --------
    (
        "R1.RA.01",
        "R1.RULE_AUTHORITY",
        "a state rule may not be constructed carrying RATIFIED",
        "test_book6_hardening_r1.py",
        "test_r1_d7_a_state_rule_may_not_be_constructed_ratified",
    ),
    (
        "R1.RA.02",
        "R1.RULE_AUTHORITY",
        "a model_copy-forged RATIFIED rule cannot be registered",
        "test_book6_hardening_r1.py",
        "test_r1_d7_a_forged_ratified_rule_cannot_be_registered",
    ),
    (
        "R1.RA.03",
        "R1.RULE_AUTHORITY",
        "ratification authority lives in the registry ledger, not the object",
        "test_book6_hardening_r1.py",
        "test_r1_d7_ratification_authority_lives_in_the_registry_ledger",
    ),
    (
        "R1.RA.04",
        "R1.RULE_AUTHORITY",
        "the ledger binds authority to one specific rule version",
        "test_book6_hardening_r1.py",
        "test_r1_d7_the_ledger_binds_authority_to_one_version",
    ),
    (
        "R1.RA.05",
        "R1.RULE_AUTHORITY",
        "there is no bulk or delegated ratification path in either registry",
        "test_book6_hardening_r1.py",
        "test_r1_d7_there_is_no_bulk_or_delegated_ratification_path",
    ),
    (
        "R1.RA.06",
        "R1.RULE_AUTHORITY",
        "the object-status-is-not-authority invariants are asserted",
        "test_book6_hardening_r1.py",
        "test_r1_d7_ratification_constants",
    ),
    (
        "R1.RA.07",
        "R1.RULE_AUTHORITY",
        "C1 a comparison methodology replaced by a fake ref is refused",
        "test_book6_hardening_r1.py",
        "test_r1_c1_comparison_methodology_replaced_by_a_fake_ref",
    ),
    (
        "R1.RA.08",
        "R1.RULE_AUTHORITY",
        "C2 a normalization methodology replaced is refused",
        "test_book6_hardening_r1.py",
        "test_r1_c2_normalization_methodology_replaced",
    ),
    (
        "R1.RA.09",
        "R1.RULE_AUTHORITY",
        "C2b a rule copy cannot change which registered rule is evaluated",
        "test_book6_hardening_r1.py",
        "test_r1_c2b_a_normalization_rule_copy_cannot_change_the_registered_rule",
    ),
    (
        "R1.RA.10",
        "R1.RULE_AUTHORITY",
        "C3 a valuation conversion methodology replaced is refused",
        "test_book6_hardening_r1.py",
        "test_r1_c3_valuation_conversion_methodology_replaced",
    ),
    (
        "R1.RA.11",
        "R1.RULE_AUTHORITY",
        "C4 stripped price claim refs are refused",
        "test_book6_hardening_r1.py",
        "test_r1_c4_price_claim_refs_stripped",
    ),
    (
        "R1.RA.12",
        "R1.RULE_AUTHORITY",
        "C5 a swapped price source changes no authority on its own",
        "test_book6_hardening_r1.py",
        "test_r1_c5_price_source_swapped",
    ),
    (
        "R1.RA.13",
        "R1.RULE_AUTHORITY",
        "C6 a swapped price class is refused at the decision boundary",
        "test_book6_hardening_r1.py",
        "test_r1_c6_price_class_swapped",
    ),
    (
        "R1.RA.14",
        "R1.RULE_AUTHORITY",
        "C7 a forged staleness bound is re-read at use",
        "test_book6_hardening_r1.py",
        "test_r1_c7_staleness_bound_forged_downward_is_caught_at_the_boundary",
    ),
    (
        "R1.RA.15",
        "R1.RULE_AUTHORITY",
        "C8 forged vector coverage rule refs lose DATA_COMPLETE",
        "test_book6_hardening_r1.py",
        "test_r1_c8_vector_coverage_rule_refs_replaced_by_fake_refs",
    ),
    (
        "R1.RA.16",
        "R1.RULE_AUTHORITY",
        "C9 a coverage rule status forged to RATIFIED grants nothing",
        "test_book6_hardening_r1.py",
        "test_r1_c9_coverage_rule_status_forged_to_ratified",
    ),
    (
        "R1.RA.17",
        "R1.RULE_AUTHORITY",
        "C10 a swapped coverage rule scope is refused",
        "test_book6_hardening_r1.py",
        "test_r1_c10_coverage_rule_scope_swapped",
    ),
    # -- R1 preserved seals -------------------------------------------------
    (
        "R1.PS.01",
        "R1.PRESERVED_SEALS",
        "missing is still not zero across every value-forbidden state",
        "test_book6_hardening_r1.py",
        "test_r1_missing_is_still_not_zero",
    ),
    (
        "R1.PS.02",
        "R1.PRESERVED_SEALS",
        "an observed-zero denominator still yields an undefined quotient",
        "test_book6_hardening_r1.py",
        "test_r1_denominator_still_fails_closed_to_undefined",
    ),
    (
        "R1.PS.03",
        "R1.PRESERVED_SEALS",
        "percentile is still not a normalization type",
        "test_book6_hardening_r1.py",
        "test_r1_percentile_is_still_not_a_normalization_type",
    ),
    (
        "R1.PS.04",
        "R1.PRESERVED_SEALS",
        "the fifteen-row false-comparison corpus is intact",
        "test_book6_hardening_r1.py",
        "test_r1_fifteen_row_corpus_is_intact",
    ),
    (
        "R1.PS.05",
        "R1.PRESERVED_SEALS",
        "there is still no global authoritative price source class",
        "test_book6_hardening_r1.py",
        "test_r1_no_global_price_source_constant",
    ),
    (
        "R1.PS.06",
        "R1.PRESERVED_SEALS",
        "a methodology is still a complete typed object with row authority",
        "test_book6_hardening_r1.py",
        "test_r1_methodology_is_a_complete_typed_object",
    ),
    (
        "R1.PS.07",
        "R1.PRESERVED_SEALS",
        "the corpus row lookup is symmetric",
        "test_book6_hardening_r1.py",
        "test_r1_d1_corpus_row_lookup_is_symmetric",
    ),
    (
        "R1.PS.08",
        "R1.PRESERVED_SEALS",
        "the coverage-rule invariants are asserted after the repair",
        "test_book6_hardening_r1.py",
        "test_r1_d6_coverage_rule_constants",
    ),
    # -- R2 methodology identity binds content -------------------------------
    (
        "R2.MC.01",
        "R2.METHODOLOGY_CONTENT",
        "D1 reproducer: a caller-built methodology with the right name and garbage content is refused the FC-05 comparison",
        "test_book6_hardening_r2.py",
        "test_r2_d1_the_self_authorization_reproducer_is_now_refused",
    ),
    (
        "R2.MC.02",
        "R2.METHODOLOGY_CONTENT",
        "A5 preserved: the canonical specification itself authorizes the comparison",
        "test_book6_hardening_r2.py",
        "test_r2_d1_canonical_exact_methodology_authorizes",
    ),
    (
        "R2.MC.03",
        "R2.METHODOLOGY_CONTENT",
        "the identity-binds-content and self-authorization-rejected invariants are asserted",
        "test_book6_hardening_r2.py",
        "test_r2_d1_identity_binds_content_constants",
    ),
    (
        "R2.MC.04",
        "R2.METHODOLOGY_CONTENT",
        "the content fingerprint is deterministic and covers every semantic field",
        "test_book6_hardening_r2.py",
        "test_r2_d1_fingerprint_is_deterministic_and_content_complete",
    ),
    (
        "R2.MC.05",
        "R2.METHODOLOGY_CONTENT",
        "M1/M2/M3: formula, row-set and input-ref mutations are refused at registration boundaries",
        "test_book6_hardening_r2.py",
        "test_r2_d1_content_mutations_are_refused_at_registration_boundaries",
    ),
    (
        "R2.MC.06",
        "R2.METHODOLOGY_CONTENT",
        "require_canonical_methodology refuses an object whose content differs from the bound digest",
        "test_book6_hardening_r2.py",
        "test_r2_d1_require_canonical_methodology_refuses_a_mutated_object",
    ),
    (
        "R2.MC.07",
        "R2.METHODOLOGY_CONTENT",
        "the corpus row-authority condition is checked against the ratified spec, not the registered object",
        "test_book6_hardening_r2.py",
        "test_r2_d1_comparison_authority_row_condition_is_live",
    ),
    (
        "R2.MC.08",
        "R2.METHODOLOGY_CONTENT",
        "A6 preserved: a superseded methodology stops authorizing until the corpus licenses a new version",
        "test_book6_hardening_r2.py",
        "test_r2_d1_a_superseded_methodology_stops_authorizing",
    ),
    (
        "R2.MC.09",
        "R2.METHODOLOGY_CONTENT",
        "the measurement-definition surface refuses a mutated methodology",
        "test_book6_hardening_r2.py",
        "test_r2_phase16_measurement_surface_refuses_mutated_formula",
    ),
    (
        "R2.MC.10",
        "R2.METHODOLOGY_CONTENT",
        "the normalization surface refuses a mutated methodology and still validates a matching one",
        "test_book6_hardening_r2.py",
        "test_r2_phase16_normalization_surface_refuses_mutated_methodology",
    ),
    # -- R2 predicate execution ----------------------------------------------
    (
        "R2.PE.01",
        "R2.PREDICATE_EXECUTION",
        "D2 reproducer: a ratified rule whose predicate evaluates FALSE (current 50 over prior 100) no longer emits INCREASING",
        "test_book6_hardening_r2.py",
        "test_r2_d2_the_false_predicate_reproducer_is_now_refused",
    ),
    (
        "R2.PE.02",
        "R2.PREDICATE_EXECUTION",
        "a true predicate emits only after full live replay of inputs, rule and predicate",
        "test_book6_hardening_r2.py",
        "test_r2_d2_a_true_predicate_emits_after_full_replay",
    ),
    (
        "R2.PE.03",
        "R2.PREDICATE_EXECUTION",
        "a false predicate never inverts into the opposite state",
        "test_book6_hardening_r2.py",
        "test_r2_d2_false_predicate_does_not_invert_to_the_opposite_state",
    ),
    (
        "R2.PE.04",
        "R2.PREDICATE_EXECUTION",
        "canonical predicate and rule ratification counts are zero at bootstrap",
        "test_book6_hardening_r2.py",
        "test_r2_d2_predicates_shut_with_zero_canonical_ratification",
    ),
    (
        "R2.PE.05",
        "R2.PREDICATE_EXECUTION",
        "the evaluator family is a closed three-member enumeration with one explicit operand order",
        "test_book6_hardening_r2.py",
        "test_r2_d2_the_evaluator_family_is_a_closed_enumeration",
    ),
    (
        "R2.PE.06",
        "R2.PREDICATE_EXECUTION",
        "the predicate registry ships empty and resolves nothing by string convention",
        "test_book6_hardening_r2.py",
        "test_r2_d2_the_registry_ships_empty_and_never_executes_strings",
    ),
    (
        "R2.PE.07",
        "R2.PREDICATE_EXECUTION",
        "the evaluator enforces its declared input arity",
        "test_book6_hardening_r2.py",
        "test_r2_d2_arity_is_enforced_by_the_evaluator",
    ),
    (
        "R2.PE.08",
        "R2.PREDICATE_EXECUTION",
        "every evaluator kind computes its own verdict over concrete operands",
        "test_book6_hardening_r2.py",
        "test_r2_d2_each_evaluator_kind_computes_its_own_truth",
    ),
    (
        "R2.PE.09",
        "R2.PREDICATE_EXECUTION",
        "a rule may not bind another state's predicate",
        "test_book6_hardening_r2.py",
        "test_r2_phase6_a_rule_may_not_bind_another_states_predicate",
    ),
    (
        "R2.PE.10",
        "R2.PREDICATE_EXECUTION",
        "a rule whose class or target disagrees with its predicate is refused at emission",
        "test_book6_hardening_r2.py",
        "test_r2_phase6_a_rule_may_not_misstate_its_class",
    ),
    (
        "R2.PE.11",
        "R2.PREDICATE_EXECUTION",
        "S3: swapped measurement ordering is refused because operand order belongs to the rule",
        "test_book6_hardening_r2.py",
        "test_r2_phase6_measurement_order_is_explicit_not_conventional",
    ),
    (
        "R2.PE.12",
        "R2.PREDICATE_EXECUTION",
        "S4: a model_copy target mutation cannot change which rule the registry authorizes",
        "test_book6_hardening_r2.py",
        "test_r2_phase6_predicate_target_mismatch_s4_is_refused",
    ),
    (
        "R2.PE.13",
        "R2.PREDICATE_EXECUTION",
        "an emission whose rule names an unregistered predicate refuses",
        "test_book6_hardening_r2.py",
        "test_r2_phase7_an_unresolvable_predicate_refuses_the_emission",
    ),
    (
        "R2.PE.14",
        "R2.PREDICATE_EXECUTION",
        "S1: a mutated predicate_ref on a rule copy grants nothing; ratification lives in the ledger",
        "test_book6_hardening_r2.py",
        "test_r2_phase7_s1_predicate_ref_mutation_grants_nothing",
    ),
    # -- R2 per-metric coverage closure --------------------------------------
    (
        "R2.CC.01",
        "R2.COVERAGE_CLOSURE",
        "D3 reproducer: a forged attestation claiming metric B cannot make an A-only rule set DATA_COMPLETE",
        "test_book6_hardening_r2.py",
        "test_r2_d3_the_forged_attestation_reproducer_is_now_refused",
    ),
    (
        "R2.CC.02",
        "R2.COVERAGE_CLOSURE",
        "DATA_COMPLETE requires covered == required with every metric backed by a live ratified rule",
        "test_book6_hardening_r2.py",
        "test_r2_d3_every_required_metric_covered_is_data_complete",
    ),
    (
        "R2.CC.03",
        "R2.COVERAGE_CLOSURE",
        "C1: widening the attestation scope grants nothing",
        "test_book6_hardening_r2.py",
        "test_r2_d3_c1_scope_widening_grants_nothing",
    ),
    (
        "R2.CC.04",
        "R2.COVERAGE_CLOSURE",
        "C2: a forged registry identity on an attestation grants nothing",
        "test_book6_hardening_r2.py",
        "test_r2_d3_c2_a_forged_registry_identity_grants_nothing",
    ),
    (
        "R2.CC.05",
        "R2.COVERAGE_CLOSURE",
        "C3: reducing the coverage rule list leaves the metric uncovered and reports it",
        "test_book6_hardening_r2.py",
        "test_r2_d3_c3_reducing_the_rule_list_leaves_a_metric_uncovered",
    ),
    (
        "R2.CC.06",
        "R2.COVERAGE_CLOSURE",
        "C4: an unrelated live rule cannot stand in for an uncovered metric",
        "test_book6_hardening_r2.py",
        "test_r2_d3_c4_an_unrelated_live_rule_cannot_stand_in_for_a_metric",
    ),
    (
        "R2.CC.07",
        "R2.COVERAGE_CLOSURE",
        "the attestation is an audit record: stripping or forging it never flips the authoritative verdict",
        "test_book6_hardening_r2.py",
        "test_r2_phase10_attestation_is_an_audit_record_not_authority",
    ),
    (
        "R2.CC.08",
        "R2.COVERAGE_CLOSURE",
        "the registry issues no partial attestation when one metric lacks a live rule",
        "test_book6_hardening_r2.py",
        "test_r2_phase11_build_availability_vector_never_issues_a_partial_attestation",
    ),
    (
        "R2.CC.09",
        "R2.COVERAGE_CLOSURE",
        "a coverage report may not claim a metric is both covered and uncovered",
        "test_book6_hardening_r2.py",
        "test_r2_phase9_coverage_report_partition_is_enforced",
    ),
    # -- R2 historical authority honesty -------------------------------------
    (
        "R2.HA.01",
        "R2.HISTORICAL_AUTHORITY",
        "the Book 2 authority-replay capability is recorded as NOT_IMPLEMENTED, not faked",
        "test_book6_hardening_r2.py",
        "test_r2_d4_the_capability_constant_is_recorded",
    ),
    (
        "R2.HA.02",
        "R2.HISTORICAL_AUTHORITY",
        "no historical authority report may claim replay availability while the capability is absent",
        "test_book6_hardening_r2.py",
        "test_r2_d4_a_report_may_not_claim_replay_availability",
    ),
    (
        "R2.HA.03",
        "R2.HISTORICAL_AUTHORITY",
        "H1: a current price over a current claim authorizes current valuation",
        "test_book6_hardening_r2.py",
        "test_r2_phase14_h1_current_price_and_current_claim_authorizes",
    ),
    (
        "R2.HA.04",
        "R2.HISTORICAL_AUTHORITY",
        "H2: a stale-now price is refused for CURRENT authority",
        "test_book6_hardening_r2.py",
        "test_r2_phase14_h2_a_stale_now_claim_is_refused_for_current_authority",
    ),
    (
        "R2.HA.05",
        "R2.HISTORICAL_AUTHORITY",
        "H3: a record stale by clock alone keeps its preserved historical shape",
        "test_book6_hardening_r2.py",
        "test_r2_phase14_h3_clock_only_decay_preserves_the_historical_record",
    ),
    (
        "R2.HA.06",
        "R2.HISTORICAL_AUTHORITY",
        "H4/H6: a claim decayed after observation preserves the record and reports current backing honestly",
        "test_book6_hardening_r2.py",
        "test_r2_phase14_h4_h5_h6_later_claim_decay_preserves_the_record_honestly",
    ),
    (
        "R2.HA.07",
        "R2.HISTORICAL_AUTHORITY",
        "no false PASS: a decayed claim grants no current authority through the historical path",
        "test_book6_hardening_r2.py",
        "test_r2_phase14_no_false_pass_on_historical_authority",
    ),
    # -- R2 preserved seals ---------------------------------------------------
    (
        "R2.PS.01",
        "R2.PRESERVED_SEALS",
        "the current path still hard-requires Book 2 authority after the historical split",
        "test_book6_hardening_r2.py",
        "test_r2_phase18_r1_preserved_the_current_path_still_requires_book2",
    ),
    (
        "R2.PS.02",
        "R2.PRESERVED_SEALS",
        "the valuation surface is explicit, separate and honest about its three authorities",
        "test_book6_hardening_r2.py",
        "test_r2_phase18_the_r1_valuation_surface_is_preserved_and_honest",
    ),
    # -- R3 evaluator/target semantics ---------------------------------------
    (
        "R3.ES.01",
        "R3.EVALUATOR_SEMANTICS",
        "D1 reproducer: a predicate declaring INCREASING with LESS_THAN semantics is refused as data",
        "test_book6_hardening_r3.py",
        "test_r3_d1_the_evaluator_target_contradiction_reproducer_is_refused",
    ),
    (
        "R3.ES.02",
        "R3.EVALUATOR_SEMANTICS",
        "INCREASING only binds GREATER_THAN; the three wrong pairings are rejected",
        "test_book6_hardening_r3.py",
        "test_r3_phase1_wrong_pairings_are_rejected",
    ),
    (
        "R3.ES.03",
        "R3.EVALUATOR_SEMANTICS",
        "the three correct evaluator-target pairings pass structurally",
        "test_book6_hardening_r3.py",
        "test_r3_phase1_the_three_correct_pairings_pass_structurally",
    ),
    (
        "R3.ES.04",
        "R3.EVALUATOR_SEMANTICS",
        "the evaluator-target map is closed and asserted constant",
        "test_book6_hardening_r3.py",
        "test_r3_phase1_the_map_is_closed_and_constant_true",
    ),
    (
        "R3.ES.05",
        "R3.EVALUATOR_SEMANTICS",
        "Class C targets remain unimplementable: no STABLE/VOLATILE/OWN-HISTORY semantics",
        "test_book6_hardening_r3.py",
        "test_r3_phase2_class_c_targets_are_unimplementable",
    ),
    (
        "R3.ES.06",
        "R3.EVALUATOR_SEMANTICS",
        "no generic EXPANDING/CONTRACTING predicate or rule can exist",
        "test_book6_hardening_r3.py",
        "test_r3_phase2_no_generic_expanding_contracting_predicate",
    ),
    # -- R3 ratification binding ---------------------------------------------
    (
        "R3.RB.01",
        "R3.RATIFICATION_BINDING",
        "B1: ratification may not precede its predicate; no late binding",
        "test_book6_hardening_r3.py",
        "test_r3_phase3_b1_ratification_may_not_precede_its_predicate",
    ),
    (
        "R3.RB.02",
        "R3.RATIFICATION_BINDING",
        "B2: predicate first, rule second, ratification third produces a full binding",
        "test_book6_hardening_r3.py",
        "test_r3_phase3_b2_predicate_first_then_rule_then_ratify_passes",
    ),
    (
        "R3.RB.03",
        "R3.RATIFICATION_BINDING",
        "B3: authorization never silently follows a later predicate version",
        "test_book6_hardening_r3.py",
        "test_r3_phase3_b3_rule_authorization_does_not_silently_follow_predicate_v2",
    ),
    (
        "R3.RB.04",
        "R3.RATIFICATION_BINDING",
        "B4: an unavailable bound predicate removes the rule's current authority",
        "test_book6_hardening_r3.py",
        "test_r3_phase3_b4_unavailable_predicate_loses_authority",
    ),
    (
        "R3.RB.05",
        "R3.RATIFICATION_BINDING",
        "Phase 4: the predicate fingerprint is deterministic and content-complete",
        "test_book6_hardening_r3.py",
        "test_r3_phase4_the_predicate_fingerprint_is_deterministic_and_content_complete",
    ),
    (
        "R3.RB.06",
        "R3.RATIFICATION_BINDING",
        "Phase 5: the ratification decision records the full derivation binding",
        "test_book6_hardening_r3.py",
        "test_r3_phase5_the_ratification_records_a_derivation_binding",
    ),
    (
        "R3.RB.07",
        "R3.RATIFICATION_BINDING",
        "Phase 7: a low-level ledger decision without a binding is not usable authority",
        "test_book6_hardening_r3.py",
        "test_r3_phase7_a_low_level_ledger_ratification_is_not_usable_authority",
    ),
    (
        "R3.RB.08",
        "R3.RATIFICATION_BINDING",
        "Phase 7: an unwired registry records binding-less decisions, honestly refused when wired",
        "test_book6_hardening_r3.py",
        "test_r3_phase7_bare_ratify_without_wired_registries_records_no_binding",
    ),
    (
        "R3.RB.09",
        "R3.RATIFICATION_BINDING",
        "Phase 8: live predicate content drift from the ratified fingerprint refuses authorization",
        "test_book6_hardening_r3.py",
        "test_r3_phase8_binding_mismatch_is_refused_at_authorization",
    ),
    (
        "R3.RB.10",
        "R3.RATIFICATION_BINDING",
        "Phase 8: methodology content drift refuses authorization; the R2 seal holds",
        "test_book6_hardening_r3.py",
        "test_r3_phase8_methodology_content_drift_refuses_authorization",
    ),
    (
        "R3.RB.11",
        "R3.RATIFICATION_BINDING",
        "Phase 13: predicate supersession is explicit and never auto-followed",
        "test_book6_hardening_r3.py",
        "test_r3_phase13_predicate_supersession_is_explicit_and_not_auto_followed",
    ),
    (
        "R3.RB.12",
        "R3.RATIFICATION_BINDING",
        "Phase 13: supersession requires a prior version",
        "test_book6_hardening_r3.py",
        "test_r3_phase13_predicate_supersession_requires_a_prior_version",
    ),
    (
        "R3.RB.13",
        "R3.RATIFICATION_BINDING",
        "Phase 14: methodology supersession is not auto-followed by a ratified rule",
        "test_book6_hardening_r3.py",
        "test_r3_phase14_methodology_supersession_is_not_auto_followed",
    ),
    # -- R3 output provenance --------------------------------------------------
    (
        "R3.OP.01",
        "R3.OUTPUT_PROVENANCE",
        "D3 reproducer: a caller-supplied output methodology_ref that differs from the rule is refused",
        "test_book6_hardening_r3.py",
        "test_r3_d3_the_output_methodology_forgery_reproducer_is_refused",
    ),
    (
        "R3.OP.02",
        "R3.OUTPUT_PROVENANCE",
        "the emitted dimension derives its methodology from the authorized rule",
        "test_book6_hardening_r3.py",
        "test_r3_phase9_the_emitted_dimension_derives_its_methodology",
    ),
    (
        "R3.OP.03",
        "R3.OUTPUT_PROVENANCE",
        "every provenance field on the emitted dimension matches the actual derivation",
        "test_book6_hardening_r3.py",
        "test_r3_phase10_the_emitted_dimension_provenance_is_coherent",
    ),
    (
        "R3.OP.04",
        "R3.OUTPUT_PROVENANCE",
        "S1-S6: mutated rule objects (predicate_ref, methodology, order, target, class) grant nothing",
        "test_book6_hardening_r3.py",
        "test_r3_s1_rule_predicate_ref_mutated",
    ),
    (
        "R3.OP.05",
        "R3.OUTPUT_PROVENANCE",
        "S6/S9: mutated predicate content (description, permitted methodologies) refuses at authorization",
        "test_book6_hardening_r3.py",
        "test_r3_s6_predicate_evaluator_kind_mutated",
    ),
    (
        "R3.OP.06",
        "R3.OUTPUT_PROVENANCE",
        "S7: a contradictory predicate target is unconstructable",
        "test_book6_hardening_r3.py",
        "test_r3_s7_predicate_target_state_mutated_is_unconstructable",
    ),
    (
        "R3.OP.07",
        "R3.OUTPUT_PROVENANCE",
        "S8: the operand order is a one-member closed enum",
        "test_book6_hardening_r3.py",
        "test_r3_s8_predicate_operand_order_mutated",
    ),
    (
        "R3.OP.08",
        "R3.OUTPUT_PROVENANCE",
        "S10: a forged emitted methodology_ref is refused",
        "test_book6_hardening_r3.py",
        "test_r3_s10_emitted_methodology_ref_forged",
    ),
    (
        "R3.OP.09",
        "R3.OUTPUT_PROVENANCE",
        "Phase 15: a false INCREASING predicate is a non-emission and never inverts",
        "test_book6_hardening_r3.py",
        "test_r3_phase15_negative_increasing_is_not_emitted",
    ),
    (
        "R3.OP.10",
        "R3.OUTPUT_PROVENANCE",
        "Phase 15: UNCHANGED emits only under a properly bound EXACT_EQUALITY rule",
        "test_book6_hardening_r3.py",
        "test_r3_phase15_unchanged_requires_exact_equality_binding",
    ),
    # -- R3 preserved seals -----------------------------------------------------
    (
        "R3.PS.01",
        "R3.PRESERVED_SEALS",
        "canonical ratification counts for rules, predicates and coverage rules remain zero",
        "test_book6_hardening_r3.py",
        "test_r3_phase6_canonical_counts_remain_zero",
    ),
    (
        "R3.PS.02",
        "R3.PRESERVED_SEALS",
        "no delegated, bulk or automatic ratification path exists on the registry surface",
        "test_book6_hardening_r3.py",
        "test_r3_phase6_no_delegated_or_bulk_ratification_path",
    ),
    (
        "R3.PS.03",
        "R3.PRESERVED_SEALS",
        "Phase 16 audit: dimension_id is a documented schema-local label; the derivation stays identified",
        "test_book6_hardening_r3.py",
        "test_r3_phase16_dimension_id_is_a_schema_local_label",
    ),
    (
        "R3.PS.04",
        "R3.PRESERVED_SEALS",
        "the R2 comparison content seal and corpus row authority survive R3",
        "test_book6_hardening_r3.py",
        "test_r3_phase17_r2_seals_survive_at_the_state_boundary",
    ),
    # -- R4 GAP-7 registered lineage terminality -----------------------------
    (
        "R4.LT.01",
        "R4.LINEAGE_TERMINALITY",
        "a lone registered measurement is terminal with an empty successor set",
        "test_book6_hardening_r4_lineage.py",
        "test_lone_measurement_is_terminal",
    ),
    (
        "R4.LT.02",
        "R4.LINEAGE_TERMINALITY",
        "a superseded measurement is non-terminal while its successor is terminal",
        "test_book6_hardening_r4_lineage.py",
        "test_superseded_measurement_is_not_terminal",
    ),
    (
        "R4.LT.03",
        "R4.LINEAGE_TERMINALITY",
        "in A <- B <- C only C is terminal (TERM-3)",
        "test_book6_hardening_r4_lineage.py",
        "test_three_link_chain_terminality",
    ),
    (
        "R4.LT.04",
        "R4.LINEAGE_TERMINALITY",
        "a branched lineage A <- B and A <- C is invalid on A (TERM-4)",
        "test_book6_hardening_r4_lineage.py",
        "test_branched_lineage_is_invalid",
    ),
    (
        "R4.LT.05",
        "R4.LINEAGE_TERMINALITY",
        "fail-closed scope is PER_RECORD: the successors of a branch stay valid and terminal (TERM-6)",
        "test_book6_hardening_r4_lineage.py",
        "test_successors_of_a_branch_are_unaffected",
    ),
    (
        "R4.LT.06",
        "R4.LINEAGE_TERMINALITY",
        "direct successors are deterministic in registration order",
        "test_book6_hardening_r4_lineage.py",
        "test_direct_successors_are_deterministic_in_registration_order",
    ),
    (
        "R4.LT.07",
        "R4.LINEAGE_TERMINALITY",
        "an unknown measurement is refused by every lineage accessor, never reported empty",
        "test_book6_hardening_r4_lineage.py",
        "test_unknown_measurement_is_refused_not_reported_empty",
    ),
    (
        "R4.PS.01",
        "R4.PRESERVED_SEALS",
        "registration still accepts a second successor; no registration policy was invented",
        "test_book6_hardening_r4_lineage.py",
        "test_second_successor_registration_is_still_accepted",
    ),
    (
        "R4.PS.02",
        "R4.PRESERVED_SEALS",
        "measurement_history still refuses a branched chain, unchanged",
        "test_book6_hardening_r4_lineage.py",
        "test_measurement_history_still_refuses_branching",
    ),
    (
        "R4.PS.03",
        "R4.PRESERVED_SEALS",
        "all four status assignments leave the lineage facts identical (B-STRICT)",
        "test_book6_hardening_r4_lineage.py",
        "test_status_permutation_does_not_change_lineage_facts",
    ),
    (
        "R4.PS.04",
        "R4.PRESERVED_SEALS",
        "the deferred status-validator incoherence still refuses SUPERSEDED on a root, recorded not patched",
        "test_book6_hardening_r4_lineage.py",
        "test_superseded_status_on_a_root_is_refused_by_the_record_validator",
    ),
    (
        "R4.RO.01",
        "R4.RESOLVER_ORDER",
        "a terminal, sourced, valid record resolves current",
        "test_book6_hardening_r4_resolver.py",
        "test_terminal_record_resolves",
    ),
    (
        "R4.RO.02",
        "R4.RESOLVER_ORDER",
        "a superseded record is refused at the terminality gate (TERM-2)",
        "test_book6_hardening_r4_resolver.py",
        "test_superseded_record_is_refused_at_terminality",
    ),
    (
        "R4.RO.03",
        "R4.RESOLVER_ORDER",
        "a superseded predecessor never resurrects when its successor decays (TERM-5)",
        "test_book6_hardening_r4_resolver.py",
        "test_superseded_predecessor_never_resurrects",
    ),
    (
        "R4.RO.04",
        "R4.RESOLVER_ORDER",
        "a branched lineage is refused at the lineage gate (TERM-4)",
        "test_book6_hardening_r4_resolver.py",
        "test_branched_record_is_refused_at_lineage",
    ),
    (
        "R4.RO.05",
        "R4.RESOLVER_ORDER",
        "the successors of a branch still resolve current; fail-closed scope is PER_RECORD (TERM-6)",
        "test_book6_hardening_r4_resolver.py",
        "test_branch_successors_still_resolve_current",
    ),
    (
        "R4.RO.06",
        "R4.RESOLVER_ORDER",
        "a refused record stays registered and queryable history",
        "test_book6_hardening_r4_resolver.py",
        "test_refused_record_remains_registered_history",
    ),
    (
        "R4.RO.07",
        "R4.RESOLVER_ORDER",
        "every non-value-bearing state without sources is not current; one rule, no per-state split (NV-8)",
        "test_book6_hardening_r4_resolver.py",
        "test_every_non_value_state_without_sources_is_not_current",
    ),
    (
        "R4.RO.08",
        "R4.RESOLVER_ORDER",
        "a sourced absence clears NV-B and is refused later, at the absence read",
        "test_book6_hardening_r4_resolver.py",
        "test_non_value_state_with_sources_is_not_current_for_a_different_reason",
    ),
    (
        "R4.RO.09",
        "R4.RESOLVER_ORDER",
        "an unknown measurement refuses at resolver step 1",
        "test_book6_hardening_r4_resolver.py",
        "test_unknown_measurement_refuses_at_step_one",
    ),
    (
        "R4.RO.10",
        "R4.RESOLVER_ORDER",
        "the refusal vocabulary is closed, reads no status, and names no registration policy",
        "test_book6_hardening_r4_resolver.py",
        "test_refusal_vocabulary_is_closed_and_status_free",
    ),
    (
        "R4.PS.05",
        "R4.PRESERVED_SEALS",
        "status alone never changes the verdict (CURR-S1)",
        "test_book6_hardening_r4_resolver.py",
        "test_status_alone_does_not_change_the_verdict",
    ),
    (
        "R4.PS.06",
        "R4.PRESERVED_SEALS",
        "a SUPERSEDED-status non-terminal record is refused at terminality, not status (CURR-S2)",
        "test_book6_hardening_r4_resolver.py",
        "test_superseded_status_record_is_refused_at_terminality_not_status",
    ),
    (
        "R4.PS.07",
        "R4.PRESERVED_SEALS",
        "a SUPERSEDED-status record with a decayed claim is refused at revalidation, not status (CURR-S3)",
        "test_book6_hardening_r4_resolver.py",
        "test_stale_claim_refusal_is_not_a_status_refusal",
    ),
    (
        "R4.PS.08",
        "R4.PRESERVED_SEALS",
        "is_authoritative_now inherits the central resolver with no separate edit",
        "test_book6_hardening_r4_resolver.py",
        "test_is_authoritative_now_inherits_the_resolver",
    ),
    # -- R4 GAP-7 ratified contract (rung 3) -----------------------------------
    (
        "GAP7.CARR.01",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_10_normalization_citing_a_superseded_predecessor_is_refused",
    ),
    (
        "GAP7.CARR.02",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_11_predecessor_filtered_before_ordering",
    ),
    (
        "GAP7.CARR.03",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_12_lexical_tie_break_never_sees_a_filtered_candidate",
    ),
    (
        "GAP7.CARR.04",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_13_superseded_record_still_queryable",
    ),
    (
        "GAP7.CARR.05",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_14_predecessor_does_not_resurrect",
    ),
    (
        "GAP7.CARR.06",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_15_history_intact_after_supersession",
    ),
    (
        "GAP7.CARR.07",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_16_resolve_current_mutates_nothing",
    ),
    (
        "GAP7.CARR.08",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_17_non_value_bearing_decayed_claim_refused",
    ),
    (
        "GAP7.CARR.09",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_18_structural_drift_fails_at_structure",
    ),
    (
        "GAP7.CARR.10",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_19_status_flip_changes_nothing",
    ),
    (
        "GAP7.CARR.11",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_1_terminal_live_record_resolves",
    ),
    (
        "GAP7.CARR.12",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_2_superseded_refused_successor_current",
    ),
    (
        "GAP7.CARR.13",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_3_decayed_successor_refuses_both",
    ),
    (
        "GAP7.CARR.14",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_4_successor_methodology_withdrawn_refuses_both",
    ),
    (
        "GAP7.CARR.15",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_5_three_link_chain_only_head_current",
    ),
    (
        "GAP7.CARR.16",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_6_branched_lineage_refused_at_lineage",
    ),
    (
        "GAP7.CARR.17",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_7_observed_status_alone_is_insufficient",
    ),
    (
        "GAP7.CARR.18",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_8_resolve_current_on_predecessor_raises",
    ),
    (
        "GAP7.CARR.19",
        "GAP7.CARRIED",
        "the ratified GAP-7 case CARR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_carr_9_is_authoritative_now_on_predecessor_is_false",
    ),
    (
        "GAP7.STAT.20",
        "GAP7.STATUS",
        "the ratified GAP-7 case CURR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_curr_s1_identical_except_status_gives_identical_verdict",
    ),
    (
        "GAP7.STAT.21",
        "GAP7.STATUS",
        "the ratified GAP-7 case CURR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_curr_s2_superseded_status_refused_at_terminality_not_status",
    ),
    (
        "GAP7.STAT.22",
        "GAP7.STATUS",
        "the ratified GAP-7 case CURR is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_curr_s3_superseded_status_refused_at_revalidation_not_status",
    ),
    (
        "GAP7.NV_B.23",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_10_non_terminal_cited_record_refused_at_terminality_first",
    ),
    (
        "GAP7.NV_B.24",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_1_source_less_non_value_bearing_refused",
    ),
    (
        "GAP7.NV_B.25",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_2_cited_non_value_bearing_is_current",
    ),
    (
        "GAP7.NV_B.26",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_3_cited_non_value_bearing_with_decayed_claim_refused",
    ),
    (
        "GAP7.NV_B.27",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_4_source_less_record_is_constructible_and_registrable",
    ),
    (
        "GAP7.NV_B.28",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_5_source_less_record_remains_queryable",
    ),
    (
        "GAP7.NV_B.29",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_6_current_value_still_refuses_on_non_value_bearing",
    ),
    (
        "GAP7.NV_B.30",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_7_missingness_partition_unchanged",
    ),
    (
        "GAP7.NV_B.31",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_8_uniform_across_all_eight_non_value_states",
    ),
    (
        "GAP7.NV_B.32",
        "GAP7.NV_B",
        "the ratified GAP-7 case NV is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_nv_9_methodology_live_re_resolved_for_non_value_bearing",
    ),
    (
        "GAP7.STRU.33",
        "GAP7.STRUCTURAL",
        "the ratified GAP-7 case STRUCT is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_struct_1_uncited_structural_assertion_is_not_current",
    ),
    (
        "GAP7.STRU.34",
        "GAP7.STRUCTURAL",
        "the ratified GAP-7 case STRUCT is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_struct_2_cited_structural_assertion_may_be_current",
    ),
    (
        "GAP7.TERM.35",
        "GAP7.TERMINALITY",
        "the ratified GAP-7 case TERM is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_term_1_lone_record_may_be_current",
    ),
    (
        "GAP7.TERM.36",
        "GAP7.TERMINALITY",
        "the ratified GAP-7 case TERM is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_term_2_superseded_record_not_current_successor_may_be",
    ),
    (
        "GAP7.TERM.37",
        "GAP7.TERMINALITY",
        "the ratified GAP-7 case TERM is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_term_3_only_chain_head_may_be_current",
    ),
    (
        "GAP7.TERM.38",
        "GAP7.TERMINALITY",
        "the ratified GAP-7 case TERM is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_term_4_branched_lineage_fails_closed",
    ),
    (
        "GAP7.TERM.39",
        "GAP7.TERMINALITY",
        "the ratified GAP-7 case TERM is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_term_5_predecessor_never_resurrects",
    ),
    (
        "GAP7.TERM.40",
        "GAP7.TERMINALITY",
        "the ratified GAP-7 case TERM is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_term_6_branch_successors_are_still_current",
    ),
    (
        "GAP7.ACCO.41",
        "GAP7.ACCOUNTING",
        "the ratified GAP-7 case THE is discharged",
        "test_book6_hardening_r4_gap7_contract.py",
        "test_the_forty_ratified_cases_are_all_named_in_this_file",
    ),
    # -- Rung 4: comparison / change contracts ------------------------------
    (
        "CMP.SCOPE.01",
        "CMP.CONTRACT_SCOPE",
        "G-8: exactly two public authority-bearing contract classes exist and "
        "there is no hidden third contract",
        "test_book6_comparison_contracts.py",
        "test_exactly_two_authority_bearing_classes",
    ),
    (
        "CMP.SCOPE.02",
        "CMP.CONTRACT_SCOPE",
        "GAP-5 5E: BaselineSelectorSpec is nested rule content, with no "
        "registry, ratification ledger, lifecycle, or authority of its own",
        "test_book6_comparison_contracts.py",
        "test_baseline_selector_spec_is_not_authority_bearing",
    ),
    (
        "CMP.GAP5.03",
        "CMP.BASELINE_SELECTOR",
        "grammar v0.6 §2.2.3: reserved selector names are refused at "
        "construction and carry no placeholder behaviour",
        "test_book6_comparison_contracts.py",
        "test_reserved_selector_kinds_are_rejected",
    ),
    (
        "CMP.GAP5.04",
        "CMP.BASELINE_SELECTOR",
        "EXECUTABLE_BASELINE_SELECTOR_COUNT == 1 and the reserved set is "
        "disjoint from it",
        "test_book6_comparison_contracts.py",
        "test_only_one_selector_is_executable",
    ),
    (
        "CMP.GAP5.05",
        "CMP.BASELINE_SELECTOR",
        "grammar v0.6 §2.2.4: the ordering policy is single-valued and admits "
        "no caller, observed_at, ingestion, random, or insertion order",
        "test_book6_comparison_contracts.py",
        "test_ordering_policy_is_single_valued",
    ),
    (
        "CMP.GAP1.06",
        "CMP.NUMERIC_DOMAIN",
        "GAP-1 1A-STRICT: the delta operator set is closed and no free-form "
        "formula or expression language exists",
        "test_book6_comparison_contracts.py",
        "test_delta_formula_basis_is_not_a_free_string",
    ),
    (
        "CMP.GAP1.07",
        "CMP.NUMERIC_DOMAIN",
        "GAP-1: non-finite stored deltas are refused rather than carried as a "
        "sentinel that could read as a result",
        "test_book6_comparison_contracts.py",
        "test_non_finite_deltas_are_refused",
    ),
    (
        "CMP.GAP1.08",
        "CMP.NUMERIC_DOMAIN",
        "plan v0.4 §5: NO_CHANGE means exact canonical equality and there is no "
        "epsilon, tolerance, materiality, or significance field through which a "
        "threshold could be expressed",
        "test_book6_comparison_contracts.py",
        "test_no_change_requires_exact_canonical_equality",
    ),
    (
        "CMP.AC17.09",
        "CMP.SINGLE_MEANING",
        "AC-17: an absent delta is NOT_COMPUTABLE or UNDEFINED and is never "
        "spelled as 0",
        "test_book6_comparison_contracts.py",
        "test_absent_delta_is_never_zero",
    ),
    (
        "CMP.R5.10",
        "CMP.SUPERSESSION",
        "R-5: supersedes_ref absence means first version only, and a later "
        "version may not be silently unlinked",
        "test_book6_comparison_contracts.py",
        "test_later_version_must_declare_supersession",
    ),
    (
        "CMP.R2.11",
        "CMP.COVERAGE",
        "R-2: coverage_applicability_source_ref absence means "
        "NO_UPSTREAM_DETERMINATION_EXISTS only, and is required when a "
        "determination is asserted",
        "test_book6_comparison_contracts.py",
        "test_coverage_source_ref_required_when_a_determination_is_asserted",
    ),
    (
        "CMP.R3.12",
        "CMP.COVERAGE",
        "R-3: the coverage observation state and its ref are one fact; silence "
        "about known coverage is INVALID",
        "test_book6_comparison_contracts.py",
        "test_coverage_observation_ref_iff_present",
    ),
    (
        "CMP.AC17.13",
        "CMP.SINGLE_MEANING",
        "AC-17: NOT_APPLICABLE is a real closed-enum member and is never used "
        "as an absence encoding",
        "test_book6_comparison_contracts.py",
        "test_not_applicable_is_a_real_state_not_an_absence",
    ),
    (
        "CMP.GAP4.14",
        "CMP.TEMPORAL_COMPARABILITY",
        "GAP-4 4D: TemporalComparabilityStatus is a closed three-member "
        "domain, distinct from CorpusVerdict, ComparabilityClass, StateName, "
        "and ClaimState",
        "test_book6_comparison_contracts.py",
        "test_temporal_comparability_status_is_closed_three",
    ),
    (
        "CMP.GAP4.15",
        "CMP.TEMPORAL_COMPARABILITY",
        "grammar v0.5 §3.4: UNRESOLVED is never mapped to NOT_COMPARABLE, "
        "because absence of basis is not a structural failure",
        "test_book6_comparison_contracts.py",
        "test_unresolved_never_maps_to_not_comparable",
    ),
    (
        "CMP.GAP4.16",
        "CMP.TEMPORAL_COMPARABILITY",
        "GAP-4 closes the v0.4 defect: a NOT_COMPARABLE or UNRESOLVED status "
        "must name the gate that produced it",
        "test_book6_comparison_contracts.py",
        "test_a_decision_status_requires_a_producer",
    ),
    (
        "CMP.AC17.17",
        "CMP.SINGLE_MEANING",
        "selected_baseline_measurement_ref is absent exactly when no "
        "comparison reached arithmetic, and present exactly when it did",
        "test_book6_comparison_contracts.py",
        "test_selected_baseline_presence_tracks_resolution",
    ),
    (
        "CMP.POLICY.18",
        "CMP.POLICY_FIREWALL",
        "plan v0.4 §0: the four deleted policy surfaces do not exist and cannot "
        "be re-added as fields",
        "test_book6_comparison_contracts.py",
        "test_removed_policy_fields_do_not_exist",
    ),
    (
        "CMP.PHANTOM.19",
        "CMP.POLICY_FIREWALL",
        "boundary v0.4: the phantom benchmark field is absent from both "
        "authority classes",
        "test_book6_comparison_contracts.py",
        "test_phantom_benchmark_field_does_not_exist",
    ),
    (
        "CMP.DISPLAY.20",
        "CMP.DISPLAY_SEPARATION",
        "plan v0.4 §0 repair 5: display precision is presentation-only, held "
        "in its own field and outside every derivation",
        "test_book6_comparison_contracts.py",
        "test_display_metadata_is_presentation_only",
    ),
    (
        "CMP.FIREWALL.21",
        "FIREWALL.ANTI_SCORE",
        "the anti-score firewall reaches the constructor and model_copy: no "
        "score, rank, grade, or recommendation field can be attached",
        "test_book6_comparison_contracts.py",
        "test_model_copy_cannot_smuggle_a_field",
    ),
    (
        "CMP.FP.22",
        "CMP.FINGERPRINT",
        "equal rule content yields an equal digest, and unordered requirement "
        "tuples are order-insensitive so a cosmetic reordering is not a change",
        "test_book6_comparison_registry.py",
        "test_unordered_fields_are_order_insensitive",
    ),
    (
        "CMP.FP.23",
        "CMP.DISPLAY_SEPARATION",
        "display_metadata is outside the fingerprint: re-rendering a rule does "
        "not invalidate its live authority",
        "test_book6_comparison_registry.py",
        "test_display_metadata_is_outside_the_fingerprint",
    ),
    (
        "CMP.FP.24",
        "CMP.BASELINE_SELECTOR",
        "grammar v0.6 §2.7: the baseline selector's semantic content is folded "
        "into the rule digest, so swapping the selector changes the rule",
        "test_book6_comparison_registry.py",
        "test_selector_content_is_inside_the_rule_fingerprint",
    ),
    (
        "CMP.FP.25",
        "CMP.FINGERPRINT",
        "the canonical field lists match the ratified specification, with the "
        "presentation-only fields excluded by construction",
        "test_book6_comparison_registry.py",
        "test_canonical_field_lists_match_the_specification",
    ),
    (
        "CMP.AUTH.26",
        "CMP.RULE_AUTHORITY",
        "D6M-3 = A: the canonical bootstrap ratified count is zero and there is "
        "no bulk or delegated ratification",
        "test_book6_comparison_registry.py",
        "test_bootstrap_ratified_count_is_zero",
    ),
    (
        "CMP.AUTH.27",
        "CMP.RULE_AUTHORITY",
        "REGISTERED THEN != AUTHORITATIVE NOW: registration alone refuses",
        "test_book6_comparison_registry.py",
        "test_registered_is_not_authoritative",
    ),
    (
        "CMP.AUTH.28",
        "CMP.RULE_AUTHORITY",
        "authority decays on supersession: a new version is a new decision and "
        "never inherits the prior one",
        "test_book6_comparison_registry.py",
        "test_decision_does_not_inherit_across_versions",
    ),
    (
        "CMP.AUTH.29",
        "CMP.RULE_AUTHORITY",
        "the R2-D1 content seal: a tampered in-memory rule stops authorizing "
        "even though it still resolves structurally",
        "test_book6_comparison_registry.py",
        "test_content_drift_invalidates_a_still_registered_rule",
    ),
    (
        "CMP.AUTH.30",
        "CMP.RULE_AUTHORITY",
        "invalidation removes authority immediately while the record stays "
        "queryable as history",
        "test_book6_comparison_registry.py",
        "test_invalidation_removes_authority_but_keeps_history",
    ),
    (
        "CMP.AUTH.31",
        "CMP.RULE_AUTHORITY",
        "an unknown rule identity refuses; there is no fuzzy or aliasing "
        "resolution anywhere in the registry",
        "test_book6_comparison_registry.py",
        "test_unknown_rule_refuses",
    ),
    (
        "CMP.PHANTOM.32",
        "CMP.POLICY_FIREWALL",
        "G-10: the phantom benchmark registry and fingerprint namespace does "
        "not come back under any name",
        "test_book6_comparison_registry.py",
        "test_no_benchmark_registry_was_introduced",
    ),
    (
        "CMP.TIME1.33",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-1 / G-16: an instantaneous candidate carries no interval, stays "
        "eligible, and its record is never mutated by key derivation",
        "test_book6_comparison_selector.py",
        "test_time_1_instantaneous_candidate_carries_no_interval_and_is_eligible",
    ),
    (
        "CMP.TIME9.34",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-9: forging an interval on an instantaneous record is rejected by "
        "the accepted model, so the selector never sees it",
        "test_book6_comparison_selector.py",
        "test_forging_an_interval_on_instantaneous_is_rejected_at_the_record",
    ),
    (
        "CMP.TIME2.35",
        "CMP.BASELINE_ORDERING",
        "TIME-2: with t1 < t2 < t3 < t4 the selector resolves t3",
        "test_book6_comparison_selector.py",
        "test_time_2_latest_prior_instant_is_selected",
    ),
    (
        "CMP.TIME3.36",
        "CMP.BASELINE_ORDERING",
        "TIME-3: caller order never affects the selected baseline",
        "test_book6_comparison_selector.py",
        "test_time_3_caller_order_does_not_affect_the_baseline",
    ),
    (
        "CMP.TIME4.37",
        "CMP.BASELINE_ORDERING",
        "TIME-4: observed_at is never read anywhere in the ordering path, "
        "verified against the executable source with docstrings stripped",
        "test_book6_comparison_selector.py",
        "test_time_4_observed_at_is_never_read",
    ),
    (
        "CMP.TIME5.38",
        "CMP.BASELINE_ORDERING",
        "TIME-5: an exact instant tie resolves to the greater lexical ref, so "
        "the tie-break fires when it should",
        "test_book6_comparison_selector.py",
        "test_time_5_same_instant_tie_resolves_to_the_greater_ref",
    ),
    (
        "CMP.TIME6.39",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-6: strict precedence means the same instant is NOT prior, so one "
        "instant may never serve as both baseline and comparison",
        "test_book6_comparison_selector.py",
        "test_time_6_same_instant_is_not_prior",
    ),
    (
        "CMP.TIME7.40",
        "CMP.BASELINE_ORDERING",
        "TIME-7 / GAP-6 §1.4: for interval windows the projection is the "
        "identity, so interval ordering is unchanged by the effective keys",
        "test_book6_comparison_selector.py",
        "test_time_7_interval_ordering_matches_the_effective_key_rule",
    ),
    (
        "CMP.TIME8.41",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-8: mixed temporal shapes are rejected before any ordering is "
        "computed, and nothing is coerced in either direction",
        "test_book6_comparison_selector.py",
        "test_time_8_mixed_temporal_shapes_are_rejected_without_ordering",
    ),
    (
        "CMP.TIME10.42",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-10: an interval record missing its bounds is rejected at the "
        "record, not defaulted by the selector",
        "test_book6_comparison_selector.py",
        "test_time_10_interval_without_bounds_is_rejected",
    ),
    (
        "CMP.TIME11.43",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-11 / G-19: a non-terminal predecessor that would win the "
        "lexical tie-break is filtered during eligibility, never during ordering",
        "test_book6_comparison_selector.py",
        "test_time_11_non_terminal_predecessor_is_filtered_before_ordering",
    ),
    (
        "CMP.BSTRICT.44",
        "CMP.BASELINE_ELIGIBILITY",
        "B-STRICT: the candidate record-state gate is currentness authority "
        "and never status, in either direction",
        "test_book6_comparison_selector.py",
        "test_time_11_refusal_is_terminality_not_status",
    ),
    (
        "CMP.TIME11.45",
        "CMP.BASELINE_ELIGIBILITY",
        "TIME-11.1: across all four status permutations the selection is "
        "unchanged, so status decides nothing",
        "test_book6_comparison_selector.py",
        "test_time_11_1_status_permutation_gives_one_outcome",
    ),
    (
        "CMP.BIAS.46",
        "CMP.BASELINE_ELIGIBILITY",
        "the selection-bias firewall: coverage is never a selection input, so "
        "the authorization gate cannot choose which observation is the baseline",
        "test_book6_comparison_selector.py",
        "test_coverage_is_not_a_selection_input",
    ),
    (
        "CMP.AGG.47",
        "CMP.BASELINE_ORDERING",
        "§2.6: the selector selects exactly one observation and never "
        "aggregates; aggregation belongs to the metric definition",
        "test_book6_comparison_selector.py",
        "test_selector_selects_exactly_one_and_never_aggregates",
    ),
    (
        "CMP.UNAVAIL.48",
        "CMP.BASELINE_ORDERING",
        "§2.5: no eligible prior baseline is a first-class outcome with no "
        "silent fallback",
        "test_book6_comparison_selector.py",
        "test_no_eligible_baseline_is_a_first_class_outcome",
    ),
    (
        "CMP.NAMED.49",
        "CMP.BASELINE_ELIGIBILITY",
        "AGGREGATE_ONLY is rejected: every exclusion names the requirement "
        "that refused it, so a failing check can be diagnosed",
        "test_book6_comparison_selector.py",
        "test_every_exclusion_is_named_not_aggregated",
    ),
    (
        "CMP.DERIVED.50",
        "CMP.BASELINE_ORDERING",
        "G-17: effective ordering keys are derived and discarded; they never "
        "persist onto a record and no new temporal contract field exists",
        "test_book6_comparison_selector.py",
        "test_no_new_temporal_contract_field_exists",
    ),
    (
        "CMP.COVAPP.51",
        "CMP.COVERAGE_APPLICABILITY",
        "GAP-3 3C: an exact-metric, current, ratified, in-scope rule yields "
        "coverage applicability REQUIRED",
        "test_book6_comparison_coverage.py",
        "test_exact_metric_current_ratified_rule_yields_required",
    ),
    (
        "CMP.COVAPP.52",
        "CMP.COVERAGE_APPLICABILITY",
        "3C: no coverage rule yields UNRESOLVED with "
        "NO_UPSTREAM_DETERMINATION_EXISTS",
        "test_book6_comparison_coverage.py",
        "test_no_coverage_rule_yields_unresolved_not_not_applicable",
    ),
    (
        "CMP.COVSEL.52A",
        "CMP.COVERAGE_APPLICABILITY",
        "CHECK12_SELECTS_COVERAGE_RULE is FALSE: applicability exposes no "
        "authoritative rule ref, so registry order cannot become authority",
        "test_book6_comparison_coverage.py",
        "test_applicability_selects_no_rule",
    ),
    (
        "CMP.COVSEL.52B",
        "CMP.COVERAGE_AUTHORITY",
        "LEXICAL_COVERAGE_RULE_SELECTION is corrected: two current exact-metric "
        "rules invoke no lexical winner and both are reported as candidates",
        "test_book6_comparison_coverage.py",
        "test_two_current_rules_do_not_invoke_a_lexical_winner",
    ),
    (
        "CMP.COVSEL.52C",
        "CMP.COVERAGE_AUTHORITY",
        "NAMED_RULE_BINDING_CONTROLS: the same observation replayed under each "
        "of two ratified rules follows the bound rule, not the identifier",
        "test_book6_comparison_coverage.py",
        "test_comparison_rule_may_name_either_currently_authorized_rule",
    ),
    (
        "CMP.COVSEL.52D",
        "CMP.COVERAGE_AUTHORITY",
        "no rule substitution: the named rule is replayed and the other is "
        "never silently consulted",
        "test_book6_comparison_coverage.py",
        "test_named_rule_is_never_silently_replaced",
    ),
    (
        "CMP.COVAPP.53",
        "CMP.COVERAGE_APPLICABILITY",
        "ABSENCE_OF_COVERAGE_RULE != NOT_APPLICABLE: a rule nobody wrote is a "
        "gap in the basis, never a negative determination",
        "test_book6_comparison_coverage.py",
        "test_absence_never_implies_not_applicable",
    ),
    (
        "CMP.COVAUTH.54",
        "CMP.COVERAGE_AUTHORITY",
        "a stale or superseded coverage rule does not authorize a comparison; "
        "authority decays on revision",
        "test_book6_comparison_coverage.py",
        "test_check_14_fails_for_a_stale_named_rule",
    ),
    (
        "CMP.COVAUTH.55",
        "CMP.COVERAGE_AUTHORITY",
        "a wrong-metric coverage rule cannot authorize, and check 15 reports "
        "the scope fault independently of ratification",
        "test_book6_comparison_coverage.py",
        "test_check_15_fails_for_a_wrong_metric_named_rule",
    ),
    (
        "CMP.COVAUTH.56",
        "CMP.COVERAGE_AUTHORITY",
        "check 16 is deterministic across runs and refuses to claim a verdict "
        "it cannot establish",
        "test_book6_comparison_coverage.py",
        "test_check_16_is_deterministic",
    ),
    (
        "CMP.COVCB.56A",
        "CMP.COVERAGE_AUTHORITY",
        "CALLER_SUPPLIED_COVERAGE_CALLBACK is prohibited: the replay signature "
        "carries no callable and no verdict parameter at all",
        "test_book6_comparison_coverage.py",
        "test_no_callable_or_verdict_parameter_exists_on_the_replay_path",
    ),
    (
        "CMP.COVCB.56B",
        "CMP.COVERAGE_AUTHORITY",
        "CALLER_SUPPLIED_COVERAGE_VERDICT is prohibited: the defect A "
        "reproducer is now a permanent regression test and cannot be re-entered",
        "test_book6_comparison_coverage.py",
        "test_caller_cannot_inject_a_sufficient_verdict",
    ),
    (
        "CMP.COV16.56C",
        "CMP.COVERAGE_AUTHORITY",
        "check 16 replays an ACTUAL CoverageObservation: observed_fraction "
        "above required_fraction derives SUFFICIENT deterministically",
        "test_book6_comparison_coverage.py",
        "test_actual_fraction_above_required_is_sufficient",
    ),
    (
        "CMP.COV16.56D",
        "CMP.COVERAGE_AUTHORITY",
        "check 16 replays an ACTUAL CoverageObservation: observed_fraction "
        "below required_fraction derives INSUFFICIENT deterministically",
        "test_book6_comparison_coverage.py",
        "test_actual_fraction_below_required_is_insufficient",
    ),
    (
        "CMP.COV16.56E",
        "CMP.COVERAGE_AUTHORITY",
        "a missing required CoverageObservation fails check 16 and reports no "
        "verdict rather than inferring one",
        "test_book6_comparison_coverage.py",
        "test_missing_required_observation_fails_check_16",
    ),
    (
        "CMP.COV16.56F",
        "CMP.COVERAGE_AUTHORITY",
        "an observation naming a different sufficiency rule fails check 16; "
        "no rule substitution is permitted",
        "test_book6_comparison_coverage.py",
        "test_observation_naming_the_wrong_rule_fails_check_16",
    ),
    (
        "CMP.COVSEP.57",
        "CMP.COVERAGE_AUTHORITY",
        "checks 12 through 16 are each independently falsifiable; one may fail "
        "while its neighbours hold",
        "test_book6_comparison_coverage.py",
        "test_each_coverage_check_is_individually_falsifiable",
    ),
    (
        "CMP.BIAS.58",
        "CMP.COVERAGE_APPLICABILITY",
        "COVERAGE_SELECTS_BASELINE is FALSE, enforced structurally: the "
        "coverage module never imports or calls the selector",
        "test_book6_comparison_coverage.py",
        "test_coverage_module_does_not_import_the_selector",
    ),
    (
        "CMP.BIAS.59",
        "CMP.COVERAGE_APPLICABILITY",
        "the selected baseline is byte-identical before and after coverage "
        "evaluation, across every coverage verdict",
        "test_book6_comparison_coverage.py",
        "test_baseline_selection_is_unchanged_by_coverage",
    ),
    (
        "CMP.TCMP.60",
        "CMP.TEMPORAL_COMPARABILITY",
        "GAP-4 4D: every applicable structural and coverage gate passing "
        "derives COMPARABLE",
        "test_book6_comparison_coverage.py",
        "test_comparable_path",
    ),
    (
        "CMP.TCMP.61",
        "CMP.TEMPORAL_COMPARABILITY",
        "an explicit ratified determination that coverage is INSUFFICIENT is a "
        "DECISION and derives NOT_COMPARABLE, not UNRESOLVED",
        "test_book6_comparison_coverage.py",
        "test_recomputed_insufficient_is_check_success_then_not_comparable",
    ),
    (
        "CMP.TCMP.61A",
        "CMP.TEMPORAL_COMPARABILITY",
        "CHECK16_SUCCEEDED_WITH_INSUFFICIENT and CHECK16_FAILED are different "
        "outcomes, NOT_COMPARABLE and UNRESOLVED respectively",
        "test_book6_comparison_coverage.py",
        "test_the_two_are_not_the_same_outcome",
    ),
    (
        "CMP.TCMP.61B",
        "CMP.TEMPORAL_COMPARABILITY",
        "a check 16 that could not run is an absence of basis and derives "
        "UNRESOLVED, never NOT_COMPARABLE",
        "test_book6_comparison_coverage.py",
        "test_failed_check_16_is_unresolved_not_not_comparable",
    ),
    (
        "CMP.TCMP.62",
        "CMP.TEMPORAL_COMPARABILITY",
        "no upstream determination derives UNRESOLVED",
        "test_book6_comparison_coverage.py",
        "test_unresolved_path_when_no_upstream_determination_exists",
    ),
    (
        "CMP.TCMP.63",
        "CMP.TEMPORAL_COMPARABILITY",
        "UNRESOLVED is never collapsed into NOT_COMPARABLE: absence of basis is "
        "not a structural failure",
        "test_book6_comparison_coverage.py",
        "test_missing_required_observation_fails_check_16",
    ),
    (
        "CMP.TCMP.64",
        "CMP.TEMPORAL_COMPARABILITY",
        "an explicit structural failure outranks an unresolved basis, and both "
        "are reported rather than merged",
        "test_book6_comparison_coverage.py",
        "test_an_explicit_structural_failure_outranks_an_unresolved_basis",
    ),
    (
        "CMP.CHECK19.65",
        "CMP.TEMPORAL_COMPARABILITY",
        "check 19 is separate from the coverage block and can fail while every "
        "coverage check passes",
        "test_book6_comparison_coverage.py",
        "test_check_19_can_fail_while_every_coverage_check_passes",
    ),
    (
        "CMP.AUTHORITY.66",
        "CMP.COVERAGE_AUTHORITY",
        "no second coverage registry, no comparison-local coverage authority, "
        "and no benchmark authority is introduced",
        "test_book6_comparison_coverage.py",
        "test_no_second_coverage_registry_or_benchmark_is_introduced",
    ),
    (
        "CMP.AUTHORITY.67",
        "CMP.CONTRACT_SCOPE",
        "G-8 still holds: Rung 7 declares no new authority-bearing contract "
        "class and re-declares no accepted type",
        "test_book6_comparison_coverage.py",
        "test_no_new_authority_bearing_class_is_introduced",
    ),
    (
        "CMP.THRESH.68",
        "CMP.COVERAGE_AUTHORITY",
        "NO NUMERIC COVERAGE THRESHOLD ON THIS OBJECT is preserved: the "
        "threshold lives on the ratified coverage rule, never on ComparisonRule",
        "test_book6_comparison_coverage.py",
        "test_no_threshold_was_added_to_the_comparison_rule",
    ),
    (
        "CMP.NOAGG.69",
        "CMP.COVERAGE_AUTHORITY",
        "check 16 introduces no aggregation, tolerance, epsilon or rounding; "
        "it compares one stored scalar against one ratified threshold",
        "test_book6_comparison_coverage.py",
        "test_rung_7_adds_no_aggregation_or_tolerance_field",
    ),
    (
        "CMP.BINDING.70",
        "CMP.COVERAGE_AUTHORITY",
        "COVERAGE_OBSERVATION_MEASUREMENT_BINDING: an observation attached to "
        "another measurement cannot authorize this comparison, whatever its "
        "rule, scope or fraction",
        "test_book6_comparison_coverage.py",
        "test_no_coverage_substitution_from_another_measurement",
    ),
    (
        "CMP.BINDING.71",
        "CMP.COVERAGE_AUTHORITY",
        "RULE_MATCH_ALONE_IS_NOT_ENOUGH: same rule, same metric and a passing "
        "fraction still fail when only the measurement_id differs",
        "test_book6_comparison_coverage.py",
        "test_same_rule_same_metric_wrong_measurement_fails",
    ),
    (
        "CMP.BINDING.72",
        "CMP.COVERAGE_AUTHORITY",
        "a wrong-measurement observation yields no verdict at all: check 16 "
        "fails, the verdict is UNKNOWN and it is never INSUFFICIENT",
        "test_book6_comparison_coverage.py",
        "test_wrong_measurement_cannot_produce_insufficient",
    ),
    (
        "CMP.BINDING.73",
        "CMP.COVERAGE_AUTHORITY",
        "a wrong-measurement observation is an evidence-binding failure, so "
        "temporal comparability is UNRESOLVED and never NOT_COMPARABLE",
        "test_book6_comparison_coverage.py",
        "test_wrong_measurement_yields_temporal_comparability_unresolved",
    ),
    (
        "CMP.BINDING.74",
        "CMP.COVERAGE_AUTHORITY",
        "the measurement binding is independently falsifiable from checks 14 "
        "and 15, and correcting one fault never cures another",
        "test_book6_comparison_coverage.py",
        "test_measurement_binding_is_independently_falsifiable_from_14_and_15",
    ),
    (
        "CMP.BINDING.75",
        "CMP.COVERAGE_AUTHORITY",
        "no caller may omit or null the replayed measurement identity: the "
        "parameter carries no default and a deliberate None fails closed",
        "test_book6_comparison_coverage.py",
        "test_no_caller_may_omit_or_null_the_replayed_measurement_identity",
    ),
    (
        "CMP.BINDING.76",
        "CMP.COVERAGE_AUTHORITY",
        "metric identity and measurement identity are distinct questions: a "
        "rule scoped to the metric says nothing about which observation it covers",
        "test_book6_comparison_coverage.py",
        "test_metric_identity_and_measurement_identity_are_distinct",
    ),
    (
        "CMP.BINDING.77",
        "CMP.COVERAGE_AUTHORITY",
        "the identity is fetched by the comparison ref and re-verified on the "
        "fetched evidence; the seal travels on the structured authorization",
        "test_book6_comparison_coverage.py",
        "test_the_binding_is_fetched_and_verified_never_inferred",
    ),    (
        "CMP.BINDING.78",
        "CMP.COVERAGE_AUTHORITY",
        "the operator's named rule still decides among several current rules; "
        "the measurement binding neither selects nor overrides it",
        "test_book6_comparison_coverage.py",
        "test_multiple_rule_named_binding_is_unchanged_by_the_measurement_binding",
    ),
    # -- Rung 8: deterministic change arithmetic -----------------------------
    (
        "CMP.CHANGE.01",
        "CMP.CHANGE_ARITHMETIC",
        "one authoritative ChangeObservation carries exactly one comparison "
        "measurement ref, stamped by the engine from the one operand it "
        "received",
        "test_book6_comparison_change_derivation.py",
        "test_exactly_one_comparison_ref_is_accepted",
    ),
    (
        "CMP.CHANGE.02",
        "CMP.CHANGE_ARITHMETIC",
        "a comparison set of any size other than one is refused as a set with "
        "MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED; no first, last, "
        "sort, average, sum, time, coverage or caller-order selection exists",
        "test_book6_comparison_change_derivation.py",
        "test_no_aggregation_path_exists",
    ),
    (
        "CMP.CHANGE.03",
        "CMP.CHANGE_ARITHMETIC",
        "no parameter of the derivation engine could carry a caller-authored "
        "comparison set, delta, or change kind; caller order cannot select an "
        "operand",
        "test_book6_comparison_change_derivation.py",
        "test_caller_order_cannot_select_a_comparison_operand",
    ),
    (
        "CMP.CHANGE.04",
        "CMP.CHANGE_ARITHMETIC",
        "absolute_delta is the stored binary64 subtraction, with no epsilon "
        "and no tolerance: 0.1+0.2 vs 0.3 keeps binary64 semantics and is "
        "INCREASE, not NO_CHANGE",
        "test_book6_comparison_change_derivation.py",
        "test_stored_binary64_semantics_0_1_plus_0_2_vs_0_3",
    ),
    (
        "CMP.CHANGE.05",
        "CMP.CHANGE_ARITHMETIC",
        "direction derives from the sign of the canonical UNROUNDED delta; "
        "+0.0 and -0.0 both compare equal under IEEE-754 and are NO_CHANGE",
        "test_book6_comparison_change_derivation.py",
        "test_signed_zero_in_both_directions_is_no_change",
    ),
    (
        "CMP.CHANGE.06",
        "CMP.CHANGE_ARITHMETIC",
        "exact stored-value equality is NO_CHANGE, and nothing below a "
        "materiality threshold exists to soften it",
        "test_book6_comparison_change_derivation.py",
        "test_exact_equality_is_no_change",
    ),
    (
        "CMP.CHANGE.07",
        "CMP.CHANGE_ARITHMETIC",
        "at baseline 0.0 the relative delta is UNDEFINED (None) and the kind "
        "is CHANGE_UNDEFINED; never 0, inf, NaN, capped or a percentage",
        "test_book6_comparison_change_derivation.py",
        "test_zero_baseline_relative_is_change_undefined",
    ),
    (
        "CMP.CHANGE.08",
        "CMP.CHANGE_ARITHMETIC",
        "the zero-baseline law does not suppress the absolute delta: it still "
        "computes and stays finite",
        "test_book6_comparison_change_derivation.py",
        "test_zero_baseline_absolute_still_computes",
    ),
    (
        "CMP.CHANGE.09",
        "CMP.CHANGE_ARITHMETIC",
        "NaN, +Inf and -Inf in the comparison operand fail closed before any "
        "arithmetic; no non-finite delta can be derived or persisted",
        "test_book6_comparison_change_derivation.py",
        "test_non_finite_comparison_is_refused",
    ),
    (
        "CMP.CHANGE.10",
        "CMP.CHANGE_ARITHMETIC",
        "a non-finite baseline operand fails closed the same way, before the "
        "subtraction",
        "test_book6_comparison_change_derivation.py",
        "test_non_finite_baseline_is_refused",
    ),
    (
        "CMP.CHANGE.11",
        "CMP.CHANGE_ARITHMETIC",
        "cross-metric operands never reach arithmetic: same-metric identity "
        "is re-checked at derivation and no conversion exists",
        "test_book6_comparison_change_derivation.py",
        "test_metric_mismatch_never_reaches_arithmetic",
    ),
    (
        "CMP.CHANGE.12",
        "CMP.CHANGE_ARITHMETIC",
        "exact-unit identity is enforced from the record model up; a unit "
        "mismatch cannot register, so it can never be an operand",
        "test_book6_comparison_change_derivation.py",
        "test_unit_mismatch_never_reaches_arithmetic",
    ),
    (
        "CMP.CHANGE.13",
        "CMP.CHANGE_ARITHMETIC",
        "a sealed UNRESOLVED verdict produces an INSUFFICIENT_DATA record with "
        "producing gates recorded, no deltas and no baseline resolution",
        "test_book6_comparison_change_derivation.py",
        "test_unresolved_comparability_never_reaches_arithmetic",
    ),
    (
        "CMP.CHANGE.14",
        "CMP.CHANGE_ARITHMETIC",
        "a sealed NOT_COMPARABLE verdict produces a NOT_COMPARABLE record; "
        "arithmetic never runs on a refused comparison",
        "test_book6_comparison_change_derivation.py",
        "test_not_comparable_never_reaches_arithmetic",
    ),
    (
        "CMP.CHANGE.15",
        "CMP.CHANGE_ARITHMETIC",
        "the engine consumes the sealed Rung 7 coverage result and never "
        "recomputes it: the same sealed verdict yields the same recorded "
        "verdict from engines in different live coverage states",
        "test_book6_comparison_change_derivation.py",
        "test_coverage_result_is_consumed_not_recomputed",
    ),
    (
        "CMP.CHANGE.16",
        "CMP.CHANGE_ARITHMETIC",
        "the selected baseline becomes an operand only through the engine's "
        "live resolution; a superseded selection is refused at derivation time",
        "test_book6_comparison_change_derivation.py",
        "test_selected_baseline_is_engine_derived",
    ),
    (
        "CMP.CHANGE.17",
        "CMP.CHANGE_ARITHMETIC",
        "deltas and change kind are engine-derived; test helpers may cross-check "
        "only and a mismatch raises rather than overrides",
        "test_book6_comparison_change_derivation.py",
        "test_caller_cannot_author_deltas",
    ),
    (
        "CMP.CHANGE.18",
        "CMP.CHANGE_ARITHMETIC",
        "change_kind has no caller-authorable parameter; direction is derived, "
        "never asserted",
        "test_book6_comparison_change_derivation.py",
        "test_caller_cannot_author_change_kind",
    ),
    (
        "CMP.CHANGE.19",
        "CMP.CHANGE_ARITHMETIC",
        "display_metadata cannot alter arithmetic and is fingerprint-invisible: "
        "no rounding, epsilon or label reaches the stored delta",
        "test_book6_comparison_change_derivation.py",
        "test_display_metadata_cannot_alter_arithmetic",
    ),
    (
        "CMP.CHANGE.20",
        "CMP.CHANGE_ARITHMETIC",
        "the governing rule's authority is re-checked live at derivation time; "
        "registration is not authority",
        "test_book6_comparison_change_derivation.py",
        "test_rule_without_live_authority_is_refused",
    ),
    # -- Rung 8 authority sealing erratum v0.1: baseline authority ------------
    (
        "CMP.CHANGE.21",
        "CMP.CHANGE_ARITHMETIC",
        "the derivation API has no selected_baseline_ref, "
        "baseline_selector_result or baseline_is_valid parameter; the caller "
        "may not author the selected baseline (grammar v0.6 §3.2)",
        "test_book6_comparison_change_derivation.py",
        "test_caller_cannot_provide_selected_baseline_ref",
    ),
    (
        "CMP.CHANGE.22",
        "CMP.CHANGE_ARITHMETIC",
        "an observation outside the supplied candidate set can never become "
        "the selected baseline; the outsider appears nowhere on the record",
        "test_book6_comparison_change_derivation.py",
        "test_outsider_cannot_become_the_selected_baseline",
    ),
    (
        "CMP.CHANGE.23",
        "CMP.CHANGE_ARITHMETIC",
        "the candidate set is the caller's only influence on selection; the "
        "selector's deterministic answer cannot be forced to another member",
        "test_book6_comparison_change_derivation.py",
        "test_caller_cannot_force_b_when_the_selector_selects_a",
    ),
    (
        "CMP.CHANGE.24",
        "CMP.CHANGE_ARITHMETIC",
        "the derivation is independent of caller candidate ordering: every "
        "derived field and the selected ref are identical either way",
        "test_book6_comparison_change_derivation.py",
        "test_candidate_ordering_does_not_change_the_result",
    ),
    (
        "CMP.CHANGE.25",
        "CMP.CHANGE_ARITHMETIC",
        "the engine-derived selected baseline is always a member of the "
        "supplied candidate set",
        "test_book6_comparison_change_derivation.py",
        "test_selected_baseline_is_always_in_the_candidate_set",
    ),
    (
        "CMP.CHANGE.26",
        "CMP.CHANGE_ARITHMETIC",
        "an unknown or dangling candidate ref fails the whole set closed: "
        "no silent pruning, no substitution",
        "test_book6_comparison_change_derivation.py",
        "test_unknown_candidate_fails_closed",
    ),
    (
        "CMP.CHANGE.27",
        "CMP.CHANGE_ARITHMETIC",
        "a dangling candidate is refused even alongside a viable one, and an "
        "unregistered ref fails the same way",
        "test_book6_comparison_change_derivation.py",
        "test_unknown_candidate_is_refused_even_alongside_a_viable_one",
    ),
    (
        "CMP.CHANGE.28",
        "CMP.CHANGE_ARITHMETIC",
        "SELECTOR_IMPLEMENTATIONS = 1: the Rung 8 selection equals a direct "
        "Rung 6 select_baseline call over the same ratified inputs",
        "test_book6_comparison_change_derivation.py",
        "test_rung8_selector_result_equals_direct_rung6_selector_result",
    ),
    (
        "CMP.CHANGE.29",
        "CMP.CHANGE_ARITHMETIC",
        "coverage never influences baseline selection: the selector reads no "
        "coverage state and a differing live coverage state under one sealed "
        "verdict does not move the selection",
        "test_book6_comparison_change_derivation.py",
        "test_coverage_never_influences_baseline_selection",
    ),
    # -- Rung 8 authority sealing erratum v0.1: structured coverage -----------
    (
        "CMP.CHANGE.30",
        "CMP.CHANGE_ARITHMETIC",
        "reason-wording-only mutation of a sealed verdict changes nothing in "
        "the derived record; DIAGNOSTIC_TEXT_IS_AUTHORITY = FALSE",
        "test_book6_comparison_change_derivation.py",
        "test_reason_wording_cannot_change_the_coverage_verdict",
    ),
    (
        "CMP.CHANGE.31",
        "CMP.CHANGE_ARITHMETIC",
        "the coverage requirement status is a structured field; check 12's "
        "prose cannot move it",
        "test_book6_comparison_change_derivation.py",
        "test_reason_wording_cannot_change_the_requirement_status",
    ),
    (
        "CMP.CHANGE.32",
        "CMP.CHANGE_ARITHMETIC",
        "the derivation module carries no reason-fragment authority and no "
        "prose parser; the structured-coverage refusal is named in source",
        "test_book6_comparison_change_derivation.py",
        "test_rung8_reads_no_reason_string_for_semantic_decisions",
    ),
    (
        "CMP.CHANGE.33",
        "CMP.CHANGE_ARITHMETIC",
        "a sealed verdict without its structured CoverageAuthorization cannot "
        "drive arithmetic on either the positive or the refusal path; prose is "
        "never a fallback",
        "test_book6_comparison_change_derivation.py",
        "test_sealed_verdict_without_structured_coverage_cannot_drive_arithmetic",
    ),
    (
        "CMP.CHANGE.34",
        "CMP.CHANGE_ARITHMETIC",
        "a SUFFICIENT structured verdict persists its state, ref and "
        "requirement status onto the record",
        "test_book6_comparison_change_derivation.py",
        "test_sufficient_structured_verdict_persists",
    ),
    (
        "CMP.CHANGE.35",
        "CMP.CHANGE_ARITHMETIC",
        "an INSUFFICIENT structured verdict persists and maps to the sealed "
        "NOT_COMPARABLE decision",
        "test_book6_comparison_change_derivation.py",
        "test_insufficient_structured_verdict_persists",
    ),
    (
        "CMP.CHANGE.36",
        "CMP.CHANGE_ARITHMETIC",
        "an UNKNOWN structured verdict persists as UNAVAILABLE / "
        "INSUFFICIENT_DATA — an absence encoding, never NOT_APPLICABLE",
        "test_book6_comparison_change_derivation.py",
        "test_unknown_structured_verdict_persists",
    ),
    (
        "CMP.CHANGE.37",
        "CMP.CHANGE_ARITHMETIC",
        "ReplayCheck reasons remain present for check-by-check falsifiability "
        "alongside structured consumption; they are never canonical",
        "test_book6_comparison_change_derivation.py",
        "test_replaycheck_reasons_remain_present_for_diagnostics",
    ),
    # -- erratum: metric binding / canonical object ----------------------------
    (
        "CMP.CHANGE.38",
        "CMP.CHANGE_ARITHMETIC",
        "exact rule metric binding: a rule bound to metric B is refused for "
        "metric A operands before selection and arithmetic",
        "test_book6_comparison_change_derivation.py",
        "test_rule_metric_b_with_metric_a_operands_is_refused",
    ),
    (
        "CMP.CHANGE.39",
        "CMP.CHANGE_ARITHMETIC",
        "the three-way binding refuses a baseline whose metric differs from "
        "the rule's metric",
        "test_book6_comparison_change_derivation.py",
        "test_baseline_metric_differs_from_rule_metric_is_refused",
    ),
    (
        "CMP.CHANGE.40",
        "CMP.CHANGE_ARITHMETIC",
        "the positive path requires comparison == baseline == rule metric "
        "definition ref, exactly",
        "test_book6_comparison_change_derivation.py",
        "test_all_three_metric_refs_equal_is_the_positive_path",
    ),
    (
        "CMP.CHANGE.41",
        "CMP.CHANGE_ARITHMETIC",
        "the derivation API accepts a ref, not an object: a mutated caller "
        "comparison copy has no authority channel over subject, metric or "
        "coverage ref",
        "test_book6_comparison_change_derivation.py",
        "test_mutated_caller_comparison_object_has_no_authority_channel",
    ),
    (
        "CMP.CHANGE.42",
        "CMP.CHANGE_ARITHMETIC",
        "an UNRESOLVED refusal record is built from the canonical "
        "registry-resolved comparison, never a caller copy",
        "test_book6_comparison_change_derivation.py",
        "test_refusal_record_uses_canonical_registered_comparison",
    ),
    (
        "CMP.CHANGE.43",
        "CMP.CHANGE_ARITHMETIC",
        "a NOT_COMPARABLE refusal record is built from the canonical "
        "registry-resolved comparison, never a caller copy",
        "test_book6_comparison_change_derivation.py",
        "test_not_comparable_refusal_record_uses_canonical_registered_comparison",
    ),
    (
        "CMP.CHANGE.44",
        "CMP.CHANGE_ARITHMETIC",
        "methodology identity on the record derives from the canonical "
        "resolved operands",
        "test_book6_comparison_change_derivation.py",
        "test_methodology_identity_derives_from_the_canonical_record",
    ),
    # -- erratum: fail-closed selection and state mapping ----------------------
    (
        "CMP.CHANGE.45",
        "CMP.CHANGE_ARITHMETIC",
        "BASELINE_UNAVAILABLE on a COMPARABLE verdict is a derivation fault, "
        "not a record; no placeholder baseline ref is invented",
        "test_book6_comparison_change_derivation.py",
        "test_comparable_with_no_eligible_baseline_fails_closed",
    ),
    (
        "CMP.CHANGE.46",
        "CMP.CHANGE_ARITHMETIC",
        "a superseded candidate is excluded by the selector's live currentness "
        "gate (NOT_CURRENT) and can never be selected",
        "test_book6_comparison_change_derivation.py",
        "test_superseded_candidate_is_excluded_by_the_selector_gate",
    ),
    (
        "CMP.CHANGE.47",
        "CMP.COVERAGE_AUTHORITY",
        "R-3 / AC-17: applicability UNRESOLVED is an absence encoding and "
        "resolves the observation state to UNAVAILABLE, never NOT_APPLICABLE",
        "test_book6_comparison_coverage.py",
        "test_unresolved_applicability_is_unavailable_never_not_applicable",
    ),
    # -- coverage authorization identity sealing erratum v0.1 -----------------
    (
        "CMP.CHANGE.48",
        "CMP.COVERAGE_AUTHORITY",
        "the authority replay takes no metric and no coverage-observation "
        "parameter: metric and evidence are registry-derived (A1/A2 sealed)",
        "test_book6_comparison_coverage.py",
        "test_no_metric_or_observation_parameter_exists_on_the_replay_path",
    ),
    (
        "CMP.CHANGE.49",
        "CMP.COVERAGE_AUTHORITY",
        "check 12 resolves applicability for the canonical comparison "
        "measurement's own metric_definition_ref, never a caller string",
        "test_book6_comparison_coverage.py",
        "test_canonical_measurement_metric_drives_check_12",
    ),
    (
        "CMP.CHANGE.50",
        "CMP.COVERAGE_AUTHORITY",
        "a rule scoped to another metric than the comparison's canonical "
        "metric fails check 15; the caller cannot redefine the scope",
        "test_book6_comparison_coverage.py",
        "test_metric_a_comparison_with_metric_b_scoped_rule_fails_check_15",
    ),
    (
        "CMP.CHANGE.51",
        "CMP.COVERAGE_AUTHORITY",
        "check 16 recomputes from the registered canonical evidence's "
        "observed_fraction against the named rule's required_fraction",
        "test_book6_comparison_coverage.py",
        "test_registered_canonical_coverage_fraction_is_used",
    ),
    (
        "CMP.CHANGE.52",
        "CMP.COVERAGE_AUTHORITY",
        "an unregistered forged CoverageObservation has no API path into the "
        "replay: evidence substitution is structurally impossible",
        "test_book6_comparison_coverage.py",
        "test_unregistered_forged_coverage_object_has_no_api_path",
    ),
    (
        "CMP.CHANGE.53",
        "CMP.COVERAGE_AUTHORITY",
        "the replay tracks the registry's canonical evidence, and only it: "
        "changing registered coverage changes the recomputed verdict",
        "test_book6_comparison_coverage.py",
        "test_changing_canonical_registry_coverage_changes_replay",
    ),
    (
        "CMP.CHANGE.54",
        "CMP.COVERAGE_AUTHORITY",
        "the coverage store is keyed by measurement id, so another "
        "measurement's evidence is unfetchable for this comparison",
        "test_book6_comparison_coverage.py",
        "test_registry_can_never_return_another_measurements_evidence",
    ),
    (
        "CMP.CHANGE.55",
        "CMP.COVERAGE_AUTHORITY",
        "the replay resolves the comparison through the live GAP-7 resolver: "
        "a superseded comparison measurement cannot be replayed at all",
        "test_book6_comparison_coverage.py",
        "test_a_non_current_comparison_measurement_cannot_be_replayed",
    ),
    (
        "CMP.CHANGE.56",
        "CMP.COVERAGE_AUTHORITY",
        "the structured CoverageAuthorization seals the identity of its "
        "authority bundle: comparison measurement, canonical metric and named "
        "rule (or the honest absence)",
        "test_book6_comparison_coverage.py",
        "test_coverage_authorization_records_named_rule_identity",
    ),
    (
        "CMP.CHANGE.57",
        "CMP.COVERAGE_AUTHORITY",
        "the identity seal travels intact through the sealed ComparabilityVerdict "
        "Rung 8 consumes",
        "test_book6_comparison_coverage.py",
        "test_sealed_identity_travels_through_the_comparability_verdict",
    ),
    (
        "CMP.CHANGE.58",
        "CMP.CHANGE_ARITHMETIC",
        "Rung 8 refuses a sealed bundle derived for another measurement: same "
        "status from a foreign authority bundle is a substitution",
        "test_book6_comparison_change_derivation.py",
        "test_rung8_refuses_sealed_result_from_another_measurement",
    ),
    (
        "CMP.CHANGE.59",
        "CMP.CHANGE_ARITHMETIC",
        "Rung 8 refuses a sealed bundle whose metric identity is not the "
        "comparison's canonical metric and the rule's metric",
        "test_book6_comparison_change_derivation.py",
        "test_rung8_refuses_sealed_result_from_another_metric",
    ),
    (
        "CMP.CHANGE.60",
        "CMP.CHANGE_ARITHMETIC",
        "Rung 8 refuses a sealed bundle derived under a coverage rule other "
        "than the governing rule's bound citation",
        "test_book6_comparison_change_derivation.py",
        "test_rung8_refuses_sealed_result_from_another_coverage_rule",
    ),
    (
        "CMP.CHANGE.61",
        "CMP.CHANGE_ARITHMETIC",
        "Rung 8 refuses a sealed bundle whose applicability source is not the "
        "upstream determination the operator recorded on the rule",
        "test_book6_comparison_change_derivation.py",
        "test_rung8_refuses_a_different_applicability_source_ref",
    ),
    (
        "CMP.CHANGE.62",
        "CMP.CHANGE_ARITHMETIC",
        "equal REQUIRED status alone cannot satisfy bundle agreement: every "
        "identity field is verified against the rule and the canonical operand",
        "test_book6_comparison_change_derivation.py",
        "test_same_required_status_alone_cannot_satisfy_bundle_agreement",
    ),)


def rows_for_family(family: str) -> tuple[tuple[str, str, str, str, str], ...]:
    """Every traced row in one family, in declaration order."""

    return tuple(row for row in TRACEABILITY_ROWS if row[1] == family)


#: Canonical invariant: no traceability row may exist without a real assertion.
EVERY_ROW_IS_BOUND_TO_A_REAL_ASSERTION: bool = True


__all__ = [
    "ALL_FAMILIES",
    "EVERY_ROW_IS_BOUND_TO_A_REAL_ASSERTION",
    "R1_FAMILIES",
    "R2_FAMILIES",
    "R3_FAMILIES",
    "STRUCTURAL_FAMILIES",
    "TRACEABILITY_ROWS",
    "VALIDATION_FAMILIES",
    "rows_for_family",
]
