"""Book 6 comparison-rule governance — RUNG 5 (fingerprint and ratification).

Rung 4 declared the two contract classes. This rung gives ``ComparisonRule``
the two things it needs to actually bear authority:

1. a **deterministic content fingerprint**, so "same identity, same content"
   is a checkable property rather than an assertion; and
2. a **registry whose authority is an operator ratification decision**, so a
   rule that merely exists authorizes nothing.

The accepted precedent is deliberately reused rather than reinvented.
``METHODOLOGY_CANONICAL_FIELDS`` -> ``canonical_methodology_spec()`` ->
``methodology_fingerprint()`` is the shape, and ``RatificationLedger`` is the
authority. Grammar v0.6 §2.7 names that precedent explicitly.

Two rules carry the weight.

**The selector's content lives inside the rule's fingerprint.** A baseline
selector that could be swapped without changing the rule digest would mean the
operator ratified one comparison and a different one executes. So
``baseline_selector`` is fingerprinted as rule content, not as a reference.

**Presentation is outside the fingerprint.** ``display_metadata`` is carried but
never hashed. If display precision were inside the digest, re-rendering the
same rule at two decimal places would invalidate live authority, which is the
v0.3 defect this amendment was written to remove.

Authority decays on supersession, exactly as it does for methodologies:
ratifying version 1 says nothing about version 2. A later version is a new
decision, not an inherited one.

D6M-3 = A is unchanged by this rung. Registration is not ratification, there is
no delegated or bulk ratification, and the canonical bootstrap count is zero.
There is deliberately no ``ratify_all``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Final

from .book6_comparison_contracts import (
    BaselineSelectorSpec,
    ComparisonContractError,
    ComparisonRule,
)
from .book6_ratification import RatificationError, RatificationLedger, RatificationRecord


class ComparisonRuleAuthorityError(ValueError):
    """A comparison rule is unknown, unratified, superseded, or altered."""


#: Every semantic field of a baseline selector, in canonical order. Grammar
#: v0.6 §2.7 names this as the minimum fingerprinted content.
BASELINE_SELECTOR_CANONICAL_FIELDS: Final[tuple[str, ...]] = (
    "selector_kind",
    "window_compatibility",
    "methodology_compatibility",
    "denominator_requirements",
    "cohort_requirements",
    "ordering_policy",
)

#: Every semantic field of a comparison rule, in canonical order. The nested
#: selector's content is included as ONE entry rather than by reference, which
#: is what makes swapping the selector change the rule's digest.
COMPARISON_RULE_CANONICAL_FIELDS: Final[tuple[str, ...]] = (
    "comparison_rule_id",
    "version",
    "supersedes_ref",
    "metric_definition_ref",
    "metric_definition_semantic_fingerprint",
    "baseline_selector",
    "delta_operator",
    "compatible_methodology_refs",
    "unit_requirements",
    "denominator_requirements",
    "cohort_requirements",
    "window_compatibility",
    "missingness_requirements",
    "output_semantics",
    "coverage_requirement_status",
    "coverage_applicability_source_ref",
    "coverage_sufficiency_rule_ref",
)

#: Fields deliberately absent from the fingerprint. Presentation never enters
#: authority, and the identity of the record is not its content.
NON_AUTHORITATIVE_RULE_FIELDS: Final[tuple[str, ...]] = (
    "display_metadata",
)


def canonical_baseline_selector_spec(selector: BaselineSelectorSpec) -> str:
    """Serialize a selector's full semantic content deterministically.

    Unordered requirement tuples are SORTED: their order carries no meaning,
    and an order-sensitive digest would let a cosmetic reordering look like a
    different selector.
    """

    values: dict[str, object] = {
        "selector_kind": selector.selector_kind.value,
        "window_compatibility": sorted(c.value for c in selector.window_compatibility),
        "methodology_compatibility": sorted(selector.methodology_compatibility),
        "denominator_requirements": sorted(selector.denominator_requirements),
        "cohort_requirements": sorted(selector.cohort_requirements),
        "ordering_policy": selector.ordering_policy.value,
    }
    if set(values) != set(BASELINE_SELECTOR_CANONICAL_FIELDS):  # pragma: no cover
        raise ComparisonContractError(
            "canonical baseline selector fields drifted from the specification"
        )
    return json.dumps(
        [values[field] for field in BASELINE_SELECTOR_CANONICAL_FIELDS],
        separators=(",", ":"),
        ensure_ascii=True,
    )


def baseline_selector_fingerprint(selector: BaselineSelectorSpec) -> str:
    """A stable content digest for a baseline selector specification.

    This is the value ``ChangeObservation.baseline_selector_spec_fingerprint``
    carries. It is also folded into the owning rule's fingerprint, so it is
    derived rather than trusted.
    """

    return hashlib.sha256(
        canonical_baseline_selector_spec(selector).encode("utf-8")
    ).hexdigest()


def canonical_comparison_rule_spec(rule: ComparisonRule) -> str:
    """Serialize a comparison rule's full semantic content deterministically.

    ``display_metadata`` is absent by construction: it is not a canonical field,
    so presentation cannot reach authority even if a caller populates it.
    """

    values: dict[str, object] = {
        "comparison_rule_id": rule.comparison_rule_id,
        "version": rule.version,
        "supersedes_ref": rule.supersedes_ref,
        "metric_definition_ref": rule.metric_definition_ref,
        "metric_definition_semantic_fingerprint": (
            rule.metric_definition_semantic_fingerprint
        ),
        "baseline_selector": canonical_baseline_selector_spec(rule.baseline_selector),
        "delta_operator": rule.delta_operator.value,
        "compatible_methodology_refs": sorted(rule.compatible_methodology_refs),
        "unit_requirements": rule.unit_requirements,
        "denominator_requirements": sorted(rule.denominator_requirements),
        "cohort_requirements": sorted(rule.cohort_requirements),
        "window_compatibility": sorted(c.value for c in rule.window_compatibility),
        "missingness_requirements": sorted(rule.missingness_requirements),
        "output_semantics": rule.output_semantics,
        "coverage_requirement_status": rule.coverage_requirement_status.value,
        "coverage_applicability_source_ref": rule.coverage_applicability_source_ref,
        "coverage_sufficiency_rule_ref": rule.coverage_sufficiency_rule_ref,
    }
    if set(values) != set(COMPARISON_RULE_CANONICAL_FIELDS):  # pragma: no cover
        raise ComparisonContractError(
            "canonical comparison rule fields drifted from the specification"
        )
    for excluded in NON_AUTHORITATIVE_RULE_FIELDS:
        if excluded in values:  # pragma: no cover
            raise ComparisonContractError(
                f"{excluded} is presentation-only and must never be fingerprinted"
            )
    return json.dumps(
        [values[field] for field in COMPARISON_RULE_CANONICAL_FIELDS],
        separators=(",", ":"),
        ensure_ascii=True,
    )


def comparison_rule_fingerprint(rule: ComparisonRule) -> str:
    """A stable content digest for a comparison rule.

    Deliberately NOT object identity and deliberately NOT a hidden global: a
    seal that depended on process state would be a different defect from the
    one this closes. Content may not drift under a fixed identity — the
    registry refuses a re-registration whose digest differs.
    """

    return hashlib.sha256(
        canonical_comparison_rule_spec(rule).encode("utf-8")
    ).hexdigest()


class ComparisonRuleRegistry:
    """Deterministic, offline, in-memory store of comparison rules.

    Inherits the Book 4 / Book 5 lesson literally:

        REGISTERED THEN != AUTHORITATIVE NOW != RATIFIED AT ALL

    ``register_rule`` accepts a rule without judging it and grants nothing.
    ``ratify_rule`` is the only thing that grants authority, it is an
    individual decision, and it is bound to one version. ``resolve_current``
    re-checks everything at the moment of use.

    There is no ``ratify_all``, no bulk or delegated ratification, and no
    bootstrap seeding, so the canonical ratified count starts at zero.
    """

    def __init__(self, *, registry_identity: str = "book6-comparison-rules") -> None:
        self._ledger = RatificationLedger(registry_identity)
        self._by_identity: dict[str, ComparisonRule] = {}
        self._order: list[str] = []
        self._current_by_id: dict[str, str] = {}
        self._superseded: dict[str, tuple[ComparisonRule, ...]] = {}
        self._invalidated: dict[str, str] = {}
        self._fingerprints: dict[str, str] = {}

    # -- registration (proves nothing about authority) -----------------------

    def register_rule(self, rule: ComparisonRule) -> ComparisonRule:
        """Register a rule version. Registration is not ratification."""

        identity = self.identity_of(rule)
        if identity in self._by_identity:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} is already registered; a new version "
                f"is a new identity and is installed with supersede_rule()"
            )
        fingerprint = comparison_rule_fingerprint(rule)
        current = self._current_by_id.get(rule.comparison_rule_id)
        if current is not None:
            self._superseded[current] = self._superseded.get(current, ()) + (
                self._by_identity[current],
            )
        self._by_identity[identity] = rule
        self._order.append(identity)
        self._fingerprints[identity] = fingerprint
        self._current_by_id[rule.comparison_rule_id] = identity
        return rule

    def supersede_rule(self, rule: ComparisonRule) -> ComparisonRule:
        """Install a NEW VERSION of a rule, retaining the prior one as history."""

        if rule.comparison_rule_id not in self._current_by_id:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {rule.comparison_rule_id} is not registered; "
                f"supersession requires a prior version of the same rule id"
            )
        return self.register_rule(rule)

    # -- ratification (the only grant of authority) -------------------------

    def ratify_rule(
        self,
        rule_id: str,
        *,
        version: int,
        operator: str,
        at: datetime,
    ) -> RatificationRecord:
        """Record ONE individual operator decision for one rule version.

        Ratifying version 1 says nothing about version 2; that is what makes
        authority decay on supersession rather than inherit.
        """

        if not operator:
            raise ComparisonRuleAuthorityError(
                "a ratification decision must record its deciding operator; "
                "ratification is an individual act and is never anonymous"
            )
        try:
            return self._ledger.record(
                rule_id, version=str(version), operator=operator, at=at
            )
        except RatificationError as exc:
            raise ComparisonRuleAuthorityError(str(exc)) from exc

    def ratified_count(self) -> int:
        """How many rules currently carry a live decision. Zero at bootstrap."""

        return self._ledger.ratified_count()

    def decision_for(
        self, rule_id: str, *, version: int
    ) -> RatificationRecord | None:
        """The live decision for a version, or ``None``. Never raises."""

        try:
            return self._ledger.decision(rule_id, version=str(version))
        except RatificationError:
            return None

    # -- structural accessors (never authority) -----------------------------

    @staticmethod
    def identity_of(rule: ComparisonRule) -> str:
        """``<rule_id>@<version>`` — the identity a decision is bound to."""

        return f"{rule.comparison_rule_id}@{rule.version}"

    def registered_rule(self, identity: str) -> ComparisonRule:
        """Return a registered rule by identity, or refuse. History, not authority."""

        try:
            return self._by_identity[identity]
        except KeyError as exc:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} is not registered"
            ) from exc

    def registered_identities(self) -> tuple[str, ...]:
        """Deterministic structural snapshot, registration-ordered."""

        return tuple(self._order)

    def superseded_versions(self, identity: str) -> tuple[ComparisonRule, ...]:
        """Prior versions of a rule identity, retained as history."""

        return self._superseded.get(identity, ())

    def invalidation_reason(self, identity: str) -> str | None:
        return self._invalidated.get(identity)

    def invalidate_rule(self, identity: str, *, reason: str) -> str:
        """Locally invalidate a registered rule, with a recorded reason."""

        if identity not in self._by_identity:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} is not registered and cannot be invalidated"
            )
        if not reason:
            raise ComparisonRuleAuthorityError("an invalidation must record a reason")
        self._invalidated[identity] = reason
        return identity

    def clear_invalidation(self, identity: str) -> None:
        """Reverse a local invalidation. Explicit, and a no-op if absent."""

        self._invalidated.pop(identity, None)

    # -- authority ----------------------------------------------------------

    def current_identity(self, rule_id: str) -> str:
        """The current version identity for a bare rule id."""

        try:
            return self._current_by_id[rule_id]
        except KeyError as exc:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {rule_id} has no registered version"
            ) from exc

    def resolve_current(self, rule_id: str) -> ComparisonRule:
        """Return the rule that currently holds authority, or refuse.

        Authority requires ALL of, re-checked here at the moment of use rather
        than trusted from registration:

            the rule id resolves to a registered version
            that version is the current one (supersession retires the rest)
            it is not locally invalidated
            it carries a live operator ratification decision
            its content still hashes to the digest fixed at registration

        The last check is the R2-D1 seal: content may not drift under a fixed
        identity. A caller who edits a rule in place and re-registers it under
        the same version is refused.
        """

        identity = self.current_identity(rule_id)
        rule = self.registered_rule(identity)
        if identity in self._invalidated:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} is locally invalidated "
                f"({self._invalidated[identity]})"
            )
        if self.decision_for(rule_id, version=rule.version) is None:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} is registered but carries no current "
                f"operator ratification decision; registration is not authority"
            )
        expected = self._fingerprints[identity]
        if comparison_rule_fingerprint(rule) != expected:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} content drifted from the digest fixed "
                f"at registration"
            )
        return rule

    def is_authoritative_now(self, rule_id: str) -> bool:
        """Whether a rule currently holds authority, without raising."""

        try:
            self.resolve_current(rule_id)
        except ComparisonRuleAuthorityError:
            return False
        return True

    def fingerprint_of(self, identity: str) -> str:
        """The content digest bound to a registered identity at registration."""

        try:
            return self._fingerprints[identity]
        except KeyError as exc:
            raise ComparisonRuleAuthorityError(
                f"comparison rule {identity} is not registered"
            ) from exc


__all__ = [
    "BASELINE_SELECTOR_CANONICAL_FIELDS",
    "COMPARISON_RULE_CANONICAL_FIELDS",
    "NON_AUTHORITATIVE_RULE_FIELDS",
    "ComparisonRuleAuthorityError",
    "ComparisonRuleRegistry",
    "baseline_selector_fingerprint",
    "canonical_baseline_selector_spec",
    "canonical_comparison_rule_spec",
    "comparison_rule_fingerprint",
]
