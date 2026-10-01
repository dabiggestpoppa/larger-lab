"""Book 6 ratification ledger — registry-controlled authority for rule objects.

Book 6 Hardening R1 (R1-D7): an input object's own ``status`` field is not
authority. Before R1, ``StateRuleRegistry.authorize`` read ``rule.is_ratified()``
straight off the stored object, so a caller could take an UNRATIFIED rule, run

    rule.model_copy(update={"status": "RATIFIED", "ratified_by": "operator"})

register the forgery, and authorize a Class B state. ``CoverageSufficiencyRule``
was worse: its ``status`` was a bare ``str`` that any caller could set to
``"RATIFIED"`` at construction.

The repair is structural. Ratified D6M-3 = A
(``CENTRALIZED_OPERATOR_RATIFICATION``) is realized here as a single ledger that
BOTH rule registries embed:

- a rule object may only ever be REGISTERED as ``UNRATIFIED``;
- ratification is a **registry decision record**, owned by the ledger, not a
  property of untrusted input;
- authority is read from the ledger, re-checked at decision time, and is bound
  to one specific ``(rule_id, version)`` pair, so it decays on a revision
  instead of riding along with it;
- there is no delegation register, no bulk path and no automatic ratification.

Scope note, stated honestly: this is deterministic and offline. It closes every
*reachable* forgery path through the public API — a forged status field, a
``model_copy`` forgery, a directly constructed ``RATIFIED`` object, and a
supersession that inherits a prior ratification. It does not attempt to defend
against a caller who reaches into registry privates or patches the interpreter;
that is out of scope and would not be an epistemic control anyway.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final

from pydantic import ConfigDict, Field, model_validator

from .book6_frozen import Book6FrozenModel


class RatificationError(ValueError):
    """A ratification decision is missing, malformed, or not current."""


@dataclass(frozen=True)
class RatificationRecord:
    """One individual operator ratification decision, owned by a registry.

    Bound to a specific ``(rule_id, version)``: ratifying version 1 says nothing
    about version 2. This is what makes authority decay on supersession rather
    than inherit.
    """

    rule_id: str
    version: str
    operator: str
    ratified_at: datetime
    registry_identity: str


class RatificationLedger:
    """The single place where Book 6 rule authority is granted and revoked.

    Deterministic, offline, in-memory. No external auth infrastructure is
    implied or implemented: ``operator`` is an audit label recorded in the
    decision, not a credential, and the ledger grants nothing on its own — the
    owning registry decides whether a record may exist.
    """

    def __init__(self, registry_identity: str) -> None:
        if not registry_identity:
            raise RatificationError(
                "a ratification ledger requires an explicit registry identity"
            )
        self.registry_identity = registry_identity
        self._records: dict[str, RatificationRecord] = {}

    def record(
        self, rule_id: str, *, version: str, operator: str, at: datetime
    ) -> RatificationRecord:
        """Record an individual ratification decision for one rule version."""

        if not rule_id or not version:
            raise RatificationError(
                "a ratification decision must name both a rule id and a version"
            )
        if not operator:
            raise RatificationError(
                "a ratification decision must record its deciding operator; "
                "ratification is an individual act and is never anonymous"
            )
        existing = self._records.get(rule_id)
        if existing is not None and existing.version == version:
            raise RatificationError(
                f"rule {rule_id} is already ratified at version {version}; a "
                f"rule is ratified by an individual decision, not re-ratified "
                f"implicitly"
            )
        decision = RatificationRecord(
            rule_id=rule_id,
            version=version,
            operator=operator,
            ratified_at=at,
            registry_identity=self.registry_identity,
        )
        self._records[rule_id] = decision
        return decision

    def decision(self, rule_id: str, *, version: str) -> RatificationRecord:
        """Return the live decision for a rule version, or refuse.

        This is the authority chokepoint: nothing else may grant it.
        """

        decision = self._records.get(rule_id)
        if decision is None:
            raise RatificationError(
                f"rule {rule_id} carries no registry ratification decision; "
                f"ratification is an individual operator act and may never be "
                f"inferred from a rule object's own status field"
            )
        if decision.version != version:
            raise RatificationError(
                f"rule {rule_id} is ratified at version {decision.version}, not "
                f"{version}; a new version is a new decision and does not "
                f"inherit the prior ratification"
            )
        return decision

    def has(self, rule_id: str, *, version: str) -> bool:
        """Live ratification check that never raises (structural query)."""

        try:
            self.decision(rule_id, version=version)
        except RatificationError:
            return False
        return True

    def revoke(self, rule_id: str) -> None:
        """Drop authority for a rule id, retaining no implicit carry-forward."""

        self._records.pop(rule_id, None)

    def ratified_count(self) -> int:
        return len(self._records)

    def records(self) -> tuple[RatificationRecord, ...]:
        """Deterministic audit view of every decision held, id-ordered."""

        return tuple(sorted(self._records.values(), key=lambda r: r.rule_id))


class RatificationSeal(Book6FrozenModel):
    """Evidence that a specific rule version was ratified at a specific time.

    Produced only by a registry from its own ledger, and used for reporting and
    tests. Like every Book 6 record it is frozen and rejects unknown fields, so
    a forged ``status`` cannot be appended to it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    ratified_at: datetime
    registry_identity: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_identity_is_recorded(self) -> "RatificationSeal":
        if not self.registry_identity:
            raise RatificationError("a seal must record the registry that granted it")
        return self

    @classmethod
    def from_record(cls, record: RatificationRecord) -> "RatificationSeal":
        return cls(
            rule_id=record.rule_id,
            version=record.version,
            operator=record.operator,
            ratified_at=record.ratified_at,
            registry_identity=record.registry_identity,
        )


#: Canonical bootstrap: the ratified governance model ratified NO individual
#: rule, in any Book 6 rule registry (state rules or coverage-sufficiency rules).
INDIVIDUAL_RULES_RATIFIED_AT_BOOTSTRAP: Final[int] = 0

#: No delegated authority path exists (D6M-3 = A).
NO_DELEGATED_RATIFICATION_AUTHORITY: Final[bool] = True

#: A rule object's self-declared status is never authority.
OBJECT_STATUS_IS_NOT_AUTHORITY: Final[bool] = True


__all__ = [
    "INDIVIDUAL_RULES_RATIFIED_AT_BOOTSTRAP",
    "NO_DELEGATED_RATIFICATION_AUTHORITY",
    "OBJECT_STATUS_IS_NOT_AUTHORITY",
    "RatificationError",
    "RatificationLedger",
    "RatificationRecord",
    "RatificationSeal",
]
