"""Rung 5 — comparison-rule governance: fingerprint and ratification.

The properties that matter here are all negative. A fingerprint is only worth
having if it is *sensitive* to the things that change meaning and *insensitive*
to the things that do not, and authority is only worth having if it refuses.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
    BaselineSelectorKind,
    BaselineSelectorSpec,
    ComparisonRule,
    CoverageRequirementStatus,
    DeltaOperator,
)
from crypto_systems_intelligence_atlas.book6_comparison_registry import (
    BASELINE_SELECTOR_CANONICAL_FIELDS,
    COMPARISON_RULE_CANONICAL_FIELDS,
    NON_AUTHORITATIVE_RULE_FIELDS,
    ComparisonRuleAuthorityError,
    ComparisonRuleRegistry,
    baseline_selector_fingerprint,
    canonical_comparison_rule_spec,
    comparison_rule_fingerprint,
)
from crypto_systems_intelligence_atlas.book6_grammar import WindowClass

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)
METRIC = "metric.tx"
R = "book6-methodology@1"


def _selector(**kw):
    base = dict(
        selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        methodology_compatibility=(R,),
    )
    base.update(kw)
    return BaselineSelectorSpec(**base)


def _rule(**kw):
    base = dict(
        comparison_rule_id="cmp:1",
        version=1,
        metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint="fp:metric",
        baseline_selector=_selector(),
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        compatible_methodology_refs=(R,),
        unit_requirements="count",
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        missingness_requirements=("OBSERVED",),
        output_semantics="ABSOLUTE_DELTA",
        coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
    )
    base.update(kw)
    return ComparisonRule(**base)


def _ratified_registry(rule=None, **kw):
    reg = ComparisonRuleRegistry()
    rule = rule or _rule(**kw)
    reg.register_rule(rule)
    reg.ratify_rule(
        rule.comparison_rule_id, version=rule.version, operator="operator:1", at=NOW
    )
    return reg, rule


# -- fingerprint sensitivity and insensitivity -----------------------------


def test_equal_content_gives_equal_digest() -> None:
    assert comparison_rule_fingerprint(_rule()) == comparison_rule_fingerprint(_rule())


def test_unordered_fields_are_order_insensitive() -> None:
    """A cosmetic reordering must not masquerade as a different rule."""

    a = _rule(compatible_methodology_refs=("m@1", "m@2"),
              denominator_requirements=("d1", "d2"))
    b = _rule(compatible_methodology_refs=("m@2", "m@1"),
              denominator_requirements=("d2", "d1"))
    assert comparison_rule_fingerprint(a) == comparison_rule_fingerprint(b)


def test_display_metadata_is_outside_the_fingerprint() -> None:
    """plan v0.4 §0 repair 5: re-rendering must not invalidate live authority."""

    plain = _rule()
    decorated = _rule(display_metadata={"decimals": 2, "format": "0.00"})
    assert comparison_rule_fingerprint(plain) == comparison_rule_fingerprint(decorated)
    assert "display_metadata" in NON_AUTHORITATIVE_RULE_FIELDS
    for excluded in NON_AUTHORITATIVE_RULE_FIELDS:
        assert excluded not in COMPARISON_RULE_CANONICAL_FIELDS


@pytest.mark.parametrize(
    "field,value",
    [
        ("delta_operator", DeltaOperator.RELATIVE_DELTA),
        ("unit_requirements", "count-per-user"),
        ("output_semantics", "RELATIVE_DELTA"),
        ("missingness_requirements", ("OBSERVED", "NOT_COLLECTED")),
        ("metric_definition_semantic_fingerprint", "fp:other"),
        ("window_compatibility", (WindowClass.DAILY,)),
    ],
)
def test_semantic_change_changes_the_digest(field, value) -> None:
    assert comparison_rule_fingerprint(_rule()) != comparison_rule_fingerprint(
        _rule(**{field: value})
    )


def test_selector_content_is_inside_the_rule_fingerprint() -> None:
    """grammar v0.6 §2.7: swapping the selector must change the rule digest."""

    plain = _rule()
    with_denominator = _rule(
        baseline_selector=_selector(denominator_requirements=("distinct_users",))
    )
    with_wider_windows = _rule(
        baseline_selector=_selector(window_compatibility=(WindowClass.DAILY,))
    )
    digests = {
        comparison_rule_fingerprint(plain),
        comparison_rule_fingerprint(with_denominator),
        comparison_rule_fingerprint(with_wider_windows),
    }
    assert len(digests) == 3


def test_selector_fingerprint_is_stable_and_selector_sensitive() -> None:
    assert baseline_selector_fingerprint(_selector()) == baseline_selector_fingerprint(
        _selector()
    )
    assert baseline_selector_fingerprint(_selector()) != baseline_selector_fingerprint(
        _selector(cohort_requirements=("cohort:1",))
    )


def test_canonical_field_lists_match_the_specification() -> None:
    assert set(BASELINE_SELECTOR_CANONICAL_FIELDS) == set(
        BaselineSelectorSpec.model_fields
    )
    assert set(COMPARISON_RULE_CANONICAL_FIELDS) == set(ComparisonRule.model_fields) - set(
        NON_AUTHORITATIVE_RULE_FIELDS
    )
    assert "baseline_selector" in COMPARISON_RULE_CANONICAL_FIELDS


def test_canonical_spec_is_deterministic_json() -> None:
    spec = canonical_comparison_rule_spec(_rule())
    assert spec == canonical_comparison_rule_spec(_rule())
    assert spec.startswith("[") and spec.endswith("]")


# -- registration is not authority -----------------------------------------


def test_bootstrap_ratified_count_is_zero() -> None:
    """D6M-3 = A: no bootstrap seeding, no delegated or bulk ratification."""

    reg = ComparisonRuleRegistry()
    assert reg.ratified_count() == 0
    reg.register_rule(_rule())
    assert reg.ratified_count() == 0
    assert reg.is_authoritative_now("cmp:1") is False
    assert not hasattr(reg, "ratify_all")


def test_registered_is_not_authoritative() -> None:
    reg = ComparisonRuleRegistry()
    reg.register_rule(_rule())
    with pytest.raises(ComparisonRuleAuthorityError, match="registration is not authority"):
        reg.resolve_current("cmp:1")


def test_ratification_grants_authority() -> None:
    reg, rule = _ratified_registry()
    assert reg.is_authoritative_now("cmp:1") is True
    assert reg.resolve_current("cmp:1") == rule
    assert reg.ratified_count() == 1


def test_anonymous_ratification_is_refused() -> None:
    reg = ComparisonRuleRegistry()
    reg.register_rule(_rule())
    with pytest.raises(ComparisonRuleAuthorityError, match="never anonymous"):
        reg.ratify_rule("cmp:1", version=1, operator="", at=NOW)


# -- authority decays on supersession --------------------------------------


def test_supersession_retires_the_prior_version() -> None:
    reg, _v1 = _ratified_registry()
    v2 = _rule(version=2, supersedes_ref="cmp:1@1")
    reg.supersede_rule(v2)
    # v2 is registered but NOT ratified: a new version is a new decision.
    assert reg.is_authoritative_now("cmp:1") is False
    # Keyed by the SUPERSEDED identity, exactly as Book6MethodologyRegistry
    # keys superseded methodologies, so the two registries answer alike.
    assert reg.superseded_versions("cmp:1@1") == (_v1,)
    assert reg.registered_rule("cmp:1@1") == _v1  # history stays queryable


def test_ratifying_the_new_version_restores_authority() -> None:
    reg, _ = _ratified_registry()
    reg.supersede_rule(_rule(version=2, supersedes_ref="cmp:1@1"))
    reg.ratify_rule("cmp:1", version=2, operator="operator:2", at=NOW)
    assert reg.resolve_current("cmp:1").version == 2


def test_decision_does_not_inherit_across_versions() -> None:
    reg, _ = _ratified_registry()
    reg.supersede_rule(_rule(version=2, supersedes_ref="cmp:1@1"))
    assert reg.decision_for("cmp:1", version=1) is not None
    assert reg.decision_for("cmp:1", version=2) is None


# -- content may not drift under a fixed identity (the R2-D1 seal) --------


def test_content_drift_under_one_identity_is_refused_at_registration() -> None:
    reg, _ = _ratified_registry()
    with pytest.raises(ComparisonRuleAuthorityError, match="already registered"):
        reg.register_rule(_rule(unit_requirements="count-per-user"))


def test_content_drift_invalidates_a_still_registered_rule() -> None:
    """A tampered in-memory record stops authorizing even though it resolves."""

    reg, rule = _ratified_registry()
    assert reg.is_authoritative_now("cmp:1") is True
    object.__setattr__(rule, "unit_requirements", "count-per-user")
    assert reg.is_authoritative_now("cmp:1") is False
    with pytest.raises(ComparisonRuleAuthorityError, match="drifted"):
        reg.resolve_current("cmp:1")


def test_fingerprint_is_bound_at_registration() -> None:
    reg, rule = _ratified_registry()
    identity = ComparisonRuleRegistry.identity_of(rule)
    assert reg.fingerprint_of(identity) == comparison_rule_fingerprint(rule)
    with pytest.raises(ComparisonRuleAuthorityError, match="not registered"):
        reg.fingerprint_of("cmp:missing@1")


# -- invalidation ----------------------------------------------------------


def test_invalidation_removes_authority_but_keeps_history() -> None:
    reg, rule = _ratified_registry()
    reg.invalidate_rule("cmp:1@1", reason="metric redefined")
    assert reg.is_authoritative_now("cmp:1") is False
    assert reg.invalidation_reason("cmp:1@1") == "metric redefined"
    assert reg.registered_rule("cmp:1@1") == rule
    reg.clear_invalidation("cmp:1@1")
    assert reg.is_authoritative_now("cmp:1") is True


def test_invalidation_requires_a_reason_and_a_registration() -> None:
    reg = ComparisonRuleRegistry()
    with pytest.raises(ComparisonRuleAuthorityError, match="not registered"):
        reg.invalidate_rule("cmp:missing@1", reason="x")
    reg.register_rule(_rule())
    with pytest.raises(ComparisonRuleAuthorityError, match="must record a reason"):
        reg.invalidate_rule("cmp:1@1", reason="")


# -- unknown identities refuse; there is no fuzzy resolution ---------------


def test_unknown_rule_refuses() -> None:
    reg = ComparisonRuleRegistry()
    with pytest.raises(ComparisonRuleAuthorityError, match="no registered version"):
        reg.resolve_current("cmp:nope")
    with pytest.raises(ComparisonRuleAuthorityError, match="not registered"):
        reg.registered_rule("cmp:nope@1")
    assert reg.is_authoritative_now("cmp:nope") is False


def test_supersede_requires_a_prior_registration() -> None:
    reg = ComparisonRuleRegistry()
    with pytest.raises(ComparisonRuleAuthorityError, match="not registered"):
        reg.supersede_rule(_rule())


def test_snapshot_is_registration_ordered() -> None:
    reg = ComparisonRuleRegistry()
    reg.register_rule(_rule())
    reg.supersede_rule(_rule(version=2, supersedes_ref="cmp:1@1"))
    assert reg.registered_identities() == ("cmp:1@1", "cmp:1@2")
    assert reg.current_identity("cmp:1") == "cmp:1@2"


def test_no_benchmark_registry_was_introduced() -> None:
    """G-10: the phantom benchmark namespace does not come back."""

    from crypto_systems_intelligence_atlas import book6_comparison_registry as m

    for banned in ("BenchmarkRule", "BenchmarkRuleRegistry",
                   "benchmark_fingerprint", "benchmark_registry"):
        assert not hasattr(m, banned), banned
    assert m.ComparisonRuleRegistry.identity_of(_rule()) == "cmp:1@1"
