"""Book 6 coverage-sufficiency rule registry — closing the ``DATA_COMPLETE`` gap.

Book 6 Hardening R1 (R1-D4): ``FundamentalStateVector`` derived ``DATA_COMPLETE``
from

    sufficiency_backed = bool(coverage_sufficiency_rule_refs) and all(...)

It never checked that those refs named anything. The reproducer was one line::

    coverage_sufficiency_rule_refs=("fake:rule",)

on a vector whose dimensions were all observed and all carried coverage ids —
which produced ``DATA_COMPLETE`` with **zero** ratified coverage-sufficiency
rules in existence. The ratified doctrine is the opposite (plan v0.2 §11,
state-vector v0.2 §5):

    COVERAGE_OBSERVATION != COVERAGE_SUFFICIENCY_RULE

so no numeric coverage value and no free string may assert SUFFICIENT,
INSUFFICIENT or DATA_COMPLETE.

The repair has two layers, deliberately:

1. **Conservative local status** — ``FundamentalStateVector.data_status`` now
   requires a registry-issued ``CoverageSufficiencyAttestation`` whose scope
   provably covers every dimension. A hand-written ref tuple can no longer
   produce ``DATA_COMPLETE``.

2. **Authoritative engine status** — ``Book6MeasurementEngine.data_status``
   re-resolves every named rule through this registry at decision time:
   exists, carries a live ratification decision for its current version, and
   scopes to the relevant metric. ``DATA_COMPLETE`` is granted only there.

Layer 1 is what makes the defect mechanically gone from a bare string; layer 2
is the actual authority. That split is stated plainly rather than hidden: an
in-process Python object cannot be made unforgeable against a caller with code
execution, so the seal is always "re-resolve through the registry at decision
time", exactly as Book 2 already seals claims and Books 4/5 seal graph and
capital authority.

Ratified D6M-3 = A applies: registration is not ratification, there is no
delegated or bulk ratification, and the canonical bootstrap count is zero.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

from pydantic import ConfigDict, Field, model_validator

from .book6_definitions import CoverageRuleRatificationStatus, CoverageSufficiencyRule
from .book6_frozen import Book6FrozenModel
from .book6_ratification import RatificationError, RatificationLedger, RatificationRecord


class CoverageRuleError(ValueError):
    """A coverage-sufficiency rule reference is unknown, unratified, or out of scope."""


class CoverageSufficiencyAttestation(Book6FrozenModel):
    """Registry-issued evidence that named sufficiency rules were applied.

    Produced only by ``CoverageRuleRegistry.attest``. It names the rules that
    were resolved and the metric scope they were applied to, so a vector can
    check that its own dimensions fall inside the attested scope. It carries no
    verdict of its own and no numeric threshold: sufficiency was decided by the
    ratified rules, not by this object.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_ids: tuple[str, ...] = Field(min_length=1)
    scope_metric_ids: tuple[str, ...] = Field(min_length=1)
    attested_at: datetime
    registry_identity: str = Field(min_length=1)

    def covers(self, metric_ids: tuple[str, ...]) -> bool:
        """Whether this attestation's scope covers every named metric."""

        return set(metric_ids) <= set(self.scope_metric_ids)


class CoverageReport(Book6FrozenModel):
    """The explicit set equality a data-complete vector must satisfy.

    R2-D3: sufficiency is reconstructed per metric rather than inferred from an
    attestation's claimed scope. This report is that reconstruction made
    inspectable, so a ``DATA_INCOMPLETE`` verdict says WHICH metric is uncovered
    and why, instead of only that something is.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    required_metric_ids: tuple[str, ...] = Field(min_length=1)
    covered_metric_ids: tuple[str, ...]
    uncovered_metric_ids: tuple[str, ...]
    status: str = "DATA_INCOMPLETE"
    reasons: tuple[tuple[str, str], ...] = ()

    @model_validator(mode="after")
    def _check_partition(self) -> "CoverageReport":
        covered = set(self.covered_metric_ids)
        uncovered = set(self.uncovered_metric_ids)
        if covered & uncovered:
            raise CoverageRuleError(
                "a metric may not be both covered and uncovered in a report"
            )
        return self


class CoverageRuleRegistry:
    """Deterministic, offline, in-memory registry of coverage-sufficiency rules.

    Authority lives in the embedded :class:`RatificationLedger`, never in a
    rule object's own ``status`` field. Registration is not ratification; there
    is no delegation register, no bulk path, and no automatic ratification.
    """

    def __init__(self, *, registry_identity: str = "csia:book6:coverage-rule-registry") -> None:
        self._rules: dict[str, CoverageSufficiencyRule] = {}
        self._order: list[str] = []
        self._ledger = RatificationLedger(registry_identity)
        self._superseded: dict[str, tuple[CoverageSufficiencyRule, ...]] = {}

    @property
    def registry_identity(self) -> str:
        return self._ledger.registry_identity

    # -- registration --------------------------------------------------------

    def register(self, rule: CoverageSufficiencyRule) -> CoverageSufficiencyRule:
        """Register a rule. Only ``UNRATIFIED`` rules may be registered.

        Refusing a rule that already claims to be ``RATIFIED`` closes the
        R1-D7 forgery at the door: a caller cannot smuggle authority in through
        an input object.
        """

        if rule.rule_id in self._rules:
            raise CoverageRuleError(f"coverage rule {rule.rule_id} already registered")
        if rule.status is not CoverageRuleRatificationStatus.UNRATIFIED:
            raise CoverageRuleError(
                f"coverage rule {rule.rule_id} may only be registered UNRATIFIED; "
                f"ratification is an individual operator decision recorded by "
                f"this registry, never a property of an input object"
            )
        self._rules[rule.rule_id] = rule
        self._order.append(rule.rule_id)
        return rule

    def supersede(self, rule: CoverageSufficiencyRule) -> CoverageSufficiencyRule:
        """Install a new version of a rule id; the prior one is retained.

        The superseded version's ratification does NOT carry forward — authority
        decays on a revision, exactly as it does for state rules.
        """

        current = self._rules.get(rule.rule_id)
        if current is None:
            raise CoverageRuleError(
                f"coverage rule {rule.rule_id} is not registered; supersession "
                f"requires a prior version of the same rule id"
            )
        if current.version == rule.version:
            raise CoverageRuleError(
                f"coverage rule {rule.rule_id} is already at version "
                f"{rule.version}; supersession requires a new version"
            )
        self._superseded[rule.rule_id] = self._superseded.get(rule.rule_id, ()) + (current,)
        self._rules[rule.rule_id] = rule
        self._ledger.revoke(rule.rule_id)
        return rule

    # -- ratification (the only path to authority) ---------------------------

    def ratify(self, rule_ref: str, *, operator: str, at: datetime) -> CoverageSufficiencyRule:
        """Record an individual operator ratification of one rule version."""

        rule = self._rules.get(rule_ref)
        if rule is None:
            raise CoverageRuleError(f"coverage rule {rule_ref} is not registered")
        try:
            self._ledger.record(rule_ref, version=rule.version, operator=operator, at=at)
        except RatificationError as exc:
            raise CoverageRuleError(str(exc)) from exc
        return rule

    def ratified_count(self) -> int:
        """Number of rules carrying a live ratification decision."""

        return self._ledger.ratified_count()

    def ratification_of(self, rule_ref: str) -> RatificationRecord | None:
        """The live decision record for a rule, or ``None``. Never raises."""

        return next((r for r in self._ledger.records() if r.rule_id == rule_ref), None)

    # -- structural accessors (never authority) ------------------------------

    def registered_rule(self, rule_ref: str) -> CoverageSufficiencyRule:
        try:
            return self._rules[rule_ref]
        except KeyError as exc:
            raise CoverageRuleError(
                f"coverage rule {rule_ref} is not registered"
            ) from exc

    def registered_rule_refs(self) -> tuple[str, ...]:
        return tuple(self._order)

    def superseded_versions(self, rule_ref: str) -> tuple[CoverageSufficiencyRule, ...]:
        return self._superseded.get(rule_ref, ())

    def rules_for_metric(self, metric_id: str) -> tuple[CoverageSufficiencyRule, ...]:
        """All registered rules scoped to a metric, id-ordered."""

        return tuple(
            sorted(
                (r for r in self._rules.values() if r.scope_metric_id == metric_id),
                key=lambda r: r.rule_id,
            )
        )

    # -- authority-bearing resolution ---------------------------------------

    def authorize(self, *, metric_id: str, rule_ref: str) -> CoverageSufficiencyRule:
        """Return a currently-ratified, in-scope rule, or refuse.

        Every check is live at decision time: the rule must exist, must carry a
        registry ratification decision for its CURRENT version, and must scope
        to the metric being judged. A scope mismatch is a refusal, not a
        silent pass.
        """

        rule = self._rules.get(rule_ref)
        if rule is None:
            raise CoverageRuleError(
                f"coverage sufficiency rule {rule_ref} is not registered; a "
                f"coverage rule ref alone grants no sufficiency"
            )
        try:
            self._ledger.decision(rule_ref, version=rule.version)
        except RatificationError as exc:
            raise CoverageRuleError(
                f"coverage sufficiency rule {rule_ref} is not ratified: {exc}"
            ) from exc
        if rule.scope_metric_id != metric_id:
            raise CoverageRuleError(
                f"coverage sufficiency rule {rule_ref} is scoped to "
                f"{rule.scope_metric_id}, not {metric_id}"
            )
        return rule

    def is_sufficient(self, *, metric_id: str, rule_ref: str) -> bool:
        """Live sufficiency check that never raises (structural query)."""

        try:
            self.authorize(metric_id=metric_id, rule_ref=rule_ref)
        except CoverageRuleError:
            return False
        return True

    def attest(
        self, metric_ids: tuple[str, ...], *, at: datetime
    ) -> CoverageSufficiencyAttestation | None:
        """Issue an attestation for a metric scope, or return ``None``.

        ``None`` is the honest answer whenever sufficiency cannot be fully
        established — no rule registered, no ratification, a scope mismatch, or
        an empty scope. Returning ``None`` rather than a partial attestation is
        what makes the caller fail closed.
        """

        if not metric_ids:
            return None
        resolved: list[str] = []
        for metric_id in metric_ids:
            candidates = self.rules_for_metric(metric_id)
            current = [
                rule.rule_id
                for rule in candidates
                if self.is_sufficient(metric_id=metric_id, rule_ref=rule.rule_id)
            ]
            if not current:
                return None
            resolved.extend(current)
        return CoverageSufficiencyAttestation(
            rule_ids=tuple(sorted(set(resolved))),
            scope_metric_ids=tuple(sorted(set(metric_ids))),
            attested_at=at,
            registry_identity=self.registry_identity,
        )


#: Canonical bootstrap invariant: the ratified governance model ratified NO
#: individual coverage-sufficiency rule, so ``DATA_COMPLETE`` is unreachable
#: without a synthetic local fixture.
COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP: Final[int] = 0

#: A coverage rule ref alone grants nothing.
COVERAGE_RULE_REF_IS_NOT_AUTHORITY: Final[bool] = True

#: A numeric coverage fraction can never assert sufficiency.
NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY: Final[bool] = True


__all__ = [
    "COVERAGE_RULE_REF_IS_NOT_AUTHORITY",
    "CoverageReport",
    "COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP",
    "CoverageRuleError",
    "CoverageRuleRegistry",
    "CoverageSufficiencyAttestation",
    "NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY",
]
