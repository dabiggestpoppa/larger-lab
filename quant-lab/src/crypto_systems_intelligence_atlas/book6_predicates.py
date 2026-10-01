"""Book 6 state predicates — a ratified rule must be REPLAYED, not merely named.

Book 6 Hardening R2 (R2-D2) closes the most serious gap found so far. The
accepted engine, on the path that exists to emit a Class B or Class C state,
checked that a rule was registered, ratified, and had a resolvable methodology —
and then emitted the rule's ``target_state`` **without ever evaluating the rule's
predicate**. The reproducer was blunt:

    prior = 100, current = 50, predicate_ref = "predicate:current_gt_prior"
    -> emits INCREASING

Ratification licenses a derivation *method*. It does not assert the method's
*outcome*. The governing invariant is therefore:

    RATIFIED RULE  !=  TRUE PREDICATE

and every emitted Class B/C state must satisfy four conditions together:

    RULE RATIFIED
      AND INPUTS CURRENT
      AND METHODOLOGY CURRENT
      AND PREDICATE EVALUATES TRUE

This module provides the fourth. Three design constraints are load-bearing:

- **No ``eval``, no ``exec``, no code execution from strings.** The evaluator is
  a closed ``match`` over :class:`EvaluatorKind` and nothing else.
- **No caller-supplied callback at authority time.** A caller cannot pass a
  function that returns ``True``; the only evaluators that exist are the ones
  enumerated here.
- **No predicate is canonically ratified.** ``PREDICATES_CANONICALLY_RATIFIED``
  is 0, exactly as ``INDIVIDUAL_STATE_RULES_RATIFIED`` is 0. This module ships
  the architecture and the fixtures; it grants no authority.

A false predicate yields an explicit **non-emission**, never the opposite
state. ``FALSE INCREASING != DECREASING``: inverting a verdict is itself a
directional claim, and requires its own separately ratified rule.

Book 6 Hardening R3 closes the next layer of the same defect class: a predicate
declaration is DATA, and data can lie. R3-D1 saw a predicate declare
``target_state = INCREASING`` while its evaluator computed
``CURRENT_LESS_THAN_PRIOR`` — a falling series then emitted INCREASING through a
perfectly replayed pipeline. The closed semantic map :data:`EVALUATOR_TARGET_STATE`
now binds each evaluator kind to exactly one target state, mechanically. R3-D2
extends the R2 methodology doctrine to predicates themselves:
``PREDICATE_IDENTITY_BINDS_CONTENT`` — a predicate's identity carries a
content fingerprint, and a rule RATIFICATION records the exact fingerprint it
was shown, so the operator's decision names the executable derivation and not
merely a name that may later mean something else.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Final

from pydantic import ConfigDict, Field, model_validator

from .book6_frozen import Book6FrozenModel
from .book6_grammar import WindowClass
from .book6_states import StateClass, StateName


class PredicateRegistryError(ValueError):
    """A predicate reference is unknown, mismatched, or cannot be evaluated."""


class PredicateNotSatisfied(PredicateRegistryError):
    """A ratified rule was replayed and its predicate evaluated FALSE.

    An explicit non-emission carrying the operands and the outcome, so the
    refusal is inspectable rather than a bare failure. The opposite state is
    NOT inferred: that would be a second directional claim with no rule of its
    own.
    """

    def __init__(self, message: str, *, predicate_id: str, operands: tuple[float, ...]) -> None:
        super().__init__(message)
        self.predicate_id = predicate_id
        self.operands = operands


class EvaluatorKind(str, Enum):
    """The closed set of canonical evaluators.

    Closed on purpose: adding a kind is an explicit code change to this module,
    which is the point. A caller cannot introduce an evaluator by supplying a
    string.
    """

    CURRENT_GREATER_THAN_PRIOR = "CURRENT_GREATER_THAN_PRIOR"
    CURRENT_LESS_THAN_PRIOR = "CURRENT_LESS_THAN_PRIOR"
    EXACT_EQUALITY = "EXACT_EQUALITY"


#: R3-D1 (Phase 1): the closed semantic map binding each Class B evaluator to
#: EXACTLY ONE target state. A predicate's declared target is data, and data can
#: lie: before R3 a predicate could declare INCREASING while its evaluator
#: computed CURRENT_LESS_THAN_PRIOR, and a falling series emitted INCREASING
#: through a perfectly replayed pipeline. No other pairing is legal, and a
#: Class C evaluator family does not exist yet (Phase 2 — Class C remains
#: unimplemented until a later individually ratified methodology defines its
#: benchmark/threshold machinery).
EVALUATOR_TARGET_STATE: Final[dict[EvaluatorKind, StateName]] = {
    EvaluatorKind.CURRENT_GREATER_THAN_PRIOR: StateName.INCREASING,
    EvaluatorKind.CURRENT_LESS_THAN_PRIOR: StateName.DECREASING,
    EvaluatorKind.EXACT_EQUALITY: StateName.UNCHANGED,
}


def predicate_fingerprint(definition: StatePredicateDefinition) -> str:
    """A stable content digest for a predicate specification (R3-D2, Phase 4).

    The R2 methodology doctrine applied to predicates:
    ``PREDICATE_IDENTITY_BINDS_CONTENT``. Deliberately NOT Python object
    identity and deliberately NOT a hidden global singleton — the digest is a
    pure function of the definition's semantic content. Unordered collections
    are sorted, so a cosmetic reordering is not a different predicate.
    """

    payload = [
        definition.predicate_id,
        definition.version,
        definition.state_class.value,
        definition.target_state.value,
        definition.description,
        definition.required_input_arity,
        definition.evaluator_kind.value,
        definition.operand_order.value,
        sorted(w.value for w in definition.permitted_window_classes),
        sorted(definition.permitted_methodology_refs),
    ]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


class OperandOrder(str, Enum):
    """How a rule's declared measurement refs map onto evaluator operands.

    Explicit rather than positional-by-convention, because ``CURRENT > PRIOR``
    and ``PRIOR < CURRENT`` are the same statement while ``CURRENT > CURRENT``
    is not. A rule states its order; the engine does not guess it.
    """

    CURRENT_THEN_PRIOR = "CURRENT_THEN_PRIOR"


class StatePredicateDefinition(Book6FrozenModel):
    """A canonical, replayable derivation predicate for one target state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    state_class: StateClass
    target_state: StateName
    description: str = Field(min_length=8)
    required_input_arity: int = Field(ge=2)
    evaluator_kind: EvaluatorKind
    operand_order: OperandOrder = OperandOrder.CURRENT_THEN_PRIOR
    #: Window classes this predicate may compare across. Empty means the
    #: predicate imposes no additional window constraint beyond the rule's own.
    permitted_window_classes: tuple[WindowClass, ...] = ()
    #: Methodology identities this predicate may be evaluated under. Empty means
    #: no additional methodology constraint beyond the rule's own.
    permitted_methodology_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _check_shape(self) -> "StatePredicateDefinition":
        if self.state_class in (StateClass.A_AVAILABILITY, StateClass.DEFERRED_GENERIC):
            raise PredicateRegistryError(
                f"predicate {self.predicate_id} targets {self.state_class.value}; "
                f"only Class B and Class C states are rule-gated and replayable"
            )
        if self.evaluator_kind is EvaluatorKind.EXACT_EQUALITY and (
            self.required_input_arity != 2
        ):
            raise PredicateRegistryError(
                "EXACT_EQUALITY compares exactly two operands"
            )
        # R3-D1: the declared target may not contradict the executable
        # evaluator. This is registration-time refusal — a lying predicate is
        # rejected as DATA before any rule can bind it, not merely refused at
        # some later emission.
        expected_target = EVALUATOR_TARGET_STATE.get(self.evaluator_kind)
        if expected_target is not None and self.target_state is not expected_target:
            raise PredicateRegistryError(
                f"predicate {self.predicate_id} declares target "
                f"{self.target_state.value} but its evaluator "
                f"{self.evaluator_kind.value} computes "
                f"{expected_target.value}; an evaluator may not contradict the "
                f"state it claims to derive"
            )
        if self.target_state not in tuple(EVALUATOR_TARGET_STATE.values()):
            raise PredicateRegistryError(
                f"predicate {self.predicate_id} targets {self.target_state.value}, "
                f"for which no canonical Class B evaluator family exists; Class C "
                f"semantics remain unimplemented"
            )
        return self

    @property
    def identity(self) -> str:
        """Fully-qualified predicate identity (``predicate_id@version``)."""

        return f"{self.predicate_id}@{self.version}"


class PredicateEvaluation(Book6FrozenModel):
    """The recorded outcome of replaying one predicate over concrete operands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate_identity: str = Field(min_length=1)
    evaluator_kind: EvaluatorKind
    operand_order: OperandOrder
    operands: tuple[float, ...] = Field(min_length=2)
    result: bool


def evaluate_predicate(
    definition: StatePredicateDefinition, operands: tuple[float, ...]
) -> PredicateEvaluation:
    """Replay a canonical predicate over concrete operands.

    The ONLY place a predicate's truth value is produced. A closed ``match`` over
    a three-member enum: no ``eval``, no dynamic attribute lookup, no
    caller-supplied callable.
    """

    if len(operands) != definition.required_input_arity:
        raise PredicateRegistryError(
            f"predicate {definition.identity} requires exactly "
            f"{definition.required_input_arity} operands, got {len(operands)}; "
            f"operand order is {definition.operand_order.value} over the rule's "
            f"declared measurement refs"
        )
    current, prior = operands[0], operands[1]
    match definition.evaluator_kind:
        case EvaluatorKind.CURRENT_GREATER_THAN_PRIOR:
            result = current > prior
        case EvaluatorKind.CURRENT_LESS_THAN_PRIOR:
            result = current < prior
        case EvaluatorKind.EXACT_EQUALITY:
            result = current == prior
        case _:  # pragma: no cover - the enum is closed
            raise PredicateRegistryError(
                f"no canonical evaluator for {definition.evaluator_kind}"
            )
    return PredicateEvaluation(
        predicate_identity=definition.identity,
        evaluator_kind=definition.evaluator_kind,
        operand_order=definition.operand_order,
        operands=operands,
        result=result,
    )


class PredicateRegistry:
    """Deterministic, offline, in-memory store of canonical predicates.

    Ships empty of authority: registration proves nothing, and no predicate in
    this registry is canonically ratified. Its purpose is to make a rule's
    ``predicate_ref`` resolve to executable canonical code instead of prose.
    """

    def __init__(self) -> None:
        self._by_identity: dict[str, StatePredicateDefinition] = {}
        self._order: list[str] = []

    def register(self, definition: StatePredicateDefinition) -> StatePredicateDefinition:
        if definition.identity in self._by_identity:
            raise PredicateRegistryError(
                f"predicate {definition.identity} is already registered"
            )
        self._by_identity[definition.identity] = definition
        self._order.append(definition.identity)
        return definition

    def registered_predicate(self, identity: str) -> StatePredicateDefinition:
        try:
            return self._by_identity[identity]
        except KeyError as exc:
            raise PredicateRegistryError(
                f"predicate {identity} is not registered; a ratified rule must "
                f"name a canonical predicate, not prose"
            ) from exc

    def supersede(self, definition: StatePredicateDefinition) -> StatePredicateDefinition:
        """Install a NEW VERSION of a predicate id, retaining the prior one.

        R3 Phase 13: supersession is explicit and version-pinned. A rule
        ratified against ``x@1`` NEVER follows ``x@2`` — the rule's binding
        names one exact identity, and the registry resolves exactly that. This
        method exists so a version bump is an act with a name, and so the prior
        version stays queryable as history.
        """

        prior = self._by_identity.get(definition.identity)
        if prior is not None:
            raise PredicateRegistryError(
                f"predicate {definition.identity} is already registered; "
                f"supersession requires a new version"
            )
        if not any(k.startswith(f"{definition.predicate_id}@") for k in self._by_identity):
            raise PredicateRegistryError(
                f"predicate {definition.predicate_id} has no prior registered "
                f"version; supersession requires a prior version of the same id"
            )
        return self.register(definition)

    def resolve(self, identity: str) -> StatePredicateDefinition:
        """Authority-bearing resolution: a registered canonical predicate."""

        return self.registered_predicate(identity)

    def registered_identities(self) -> tuple[str, ...]:
        return tuple(self._order)

    def evaluate(
        self, identity: str, operands: tuple[float, ...]
    ) -> PredicateEvaluation:
        """Resolve and replay a predicate. The authority-bearing path."""

        return evaluate_predicate(self.resolve(identity), operands)


#: Canonical bootstrap: no predicate is canonically ratified. Ratifying one is an
#: individual operator act recorded by a state-rule registry, never inferred.
PREDICATES_CANONICALLY_RATIFIED: Final[int] = 0

#: A ratified rule is replayed before it may emit; ratification is not a verdict.
PREDICATES_ARE_EXECUTED_NOT_NAMED: Final[bool] = True

#: A false predicate never inverts into the opposite state.
FALSE_PREDICATE_IS_NOT_THE_OPPOSITE_STATE: Final[bool] = True

#: R3-D1: an evaluator may not contradict the state it claims to derive; the map
#: above is closed and mechanical.
EVALUATOR_TARGET_SEMANTIC_BINDING: Final[bool] = True

#: R3-D2 (Phase 4): a predicate identity means one exact specification.
PREDICATE_IDENTITY_BINDS_CONTENT: Final[bool] = True


__all__ = [
    "EVALUATOR_TARGET_STATE",
    "EVALUATOR_TARGET_SEMANTIC_BINDING",
    "PREDICATE_IDENTITY_BINDS_CONTENT",
    "evaluate_predicate",
    "EvaluatorKind",
    "FALSE_PREDICATE_IS_NOT_THE_OPPOSITE_STATE",
    "OperandOrder",
    "PREDICATES_ARE_EXECUTED_NOT_NAMED",
    "PREDICATES_CANONICALLY_RATIFIED",
    "PredicateEvaluation",
    "PredicateNotSatisfied",
    "PredicateRegistry",
    "PredicateRegistryError",
    "predicate_fingerprint",
    "StatePredicateDefinition",
]
