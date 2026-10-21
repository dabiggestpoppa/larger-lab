"""Step authority gate (P2-R2-C01; Book V 12.1, 13.2; ADR-0009).

Every step execution passes through a typed authority evaluation BEFORE any
worker runs. The gate binds the five directive-required elements:

    principal  -> the worker identity claiming the lease
    action     -> the step's declared ``authority_requirement`` or, when the
                  step declares none, the baseline ``execute.<step_type>``
                  action derived from its worker contract
    resource   -> the job's ``subject_ref`` (the capability/candidate the job
                  operates on)
    scope      -> the job's ``authority_context_ref`` or the deterministic
                  default ``job:<job_id>``
    requirement-> the declared requirement, carried verbatim for audit

The decision vocabulary is the Book V 13.2 set verbatim: ALLOW, DENY,
REQUIRE_APPROVAL, ALLOW_WITH_CONSTRAINTS. Anything else fails closed.

Fail-closed law: an engine constructed without a gate executes NOTHING
(``FailClosedStepAuthorityGate``). Governance is wired explicitly at the
composition root (``build_local_runtime`` -> ``PolicyStepAuthorityGate``),
never implicitly. A verdict whose decision is unknown, or whose binding does
not match the step/principal being executed, is refused — a verdict can never
be replayed for a different step or principal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, Tuple, runtime_checkable

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = [
    "StepAuthorityDecision",
    "StepAuthorityVerdict",
    "StepAuthorityGate",
    "AuthorityRequestSink",
    "FailClosedStepAuthorityGate",
    "StaticStepAuthorityGate",
    "baseline_action_for_step",
]


class StepAuthorityDecision(StrEnum):
    """Book V 13.2 decision vocabulary, verbatim (operational layer)."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    ALLOW_WITH_CONSTRAINTS = "ALLOW_WITH_CONSTRAINTS"


_DECISIONS = frozenset(StepAuthorityDecision)


def baseline_action_for_step(step) -> str:
    """The evaluated action for a step: declared requirement or the
    worker-contract baseline ``execute.<step_type>`` (both are policy-level
    open-string actions; the policy engine fails closed on unknown ones)."""
    declared = (step.authority_requirement or "").strip()
    return declared or f"execute.{step.step_type}"


@dataclass(frozen=True)
class StepAuthorityVerdict(SerializableRecord):
    """Typed result of one step-authority evaluation (13.2 decision record)."""

    SCHEMA_VERSION = 1

    step_id: str
    job_id: str
    principal: str
    action: str
    resource: str
    scope: str
    decision: StepAuthorityDecision

    #: Audit reference to the durable basis of this verdict (policy decision
    #: id, static-rule identity, ...). Non-empty always.
    decision_ref: str
    policy_version: str
    evaluated_at: str
    reason: str = ""
    constraints: Tuple[str, ...] = ()

    #: The step's declared requirement, verbatim ("" when undeclared).
    requirement: str = ""

    _COERCIONS = {
        "decision": lambda v: coerce_enum(v, StepAuthorityDecision),
    }

    def validate(self) -> None:
        require_identifier(self.step_id, "step_id")
        require_identifier(self.job_id, "job_id")
        require_non_empty_str(self.principal, "principal")
        require_non_empty_str(self.action, "action")
        require_non_empty_str(self.decision_ref, "decision_ref")
        require_non_empty_str(self.policy_version, "policy_version")
        require_non_empty_str(self.evaluated_at, "evaluated_at")
        if self.decision not in _DECISIONS:
            raise QcaeValidationError(
                f"decision must be a StepAuthorityDecision member, got {self.decision!r}"
            )
        if self.decision is StepAuthorityDecision.ALLOW_WITH_CONSTRAINTS and not self.constraints:
            raise QcaeValidationError(
                "ALLOW_WITH_CONSTRAINTS verdicts must carry constraints"
            )
        if self.decision is StepAuthorityDecision.DENY and self.constraints:
            raise QcaeValidationError("DENY verdicts cannot carry constraints")


@runtime_checkable
class StepAuthorityGate(Protocol):
    """Port the orchestrator consults before every step execution."""

    def evaluate_step_authority(self, step, job, *, worker_id: str) -> StepAuthorityVerdict:
        """Evaluate authority for executing ``step`` of ``job`` as ``worker_id``."""
        ...


@runtime_checkable
class AuthorityRequestSink(Protocol):
    """Port for persisting a durable authority request on REQUIRE_APPROVAL."""

    def record_authority_request(self, verdict: StepAuthorityVerdict) -> str:
        """Persist the request; return its durable request_id."""
        ...


class FailClosedStepAuthorityGate:
    """Default gate: no authority provider configured -> nothing executes."""

    policy_version = "fail-closed"

    def evaluate_step_authority(self, step, job, *, worker_id: str) -> StepAuthorityVerdict:
        return StepAuthorityVerdict(
            step_id=step.step_id,
            job_id=job.job_id,
            principal=worker_id,
            action=baseline_action_for_step(step),
            resource=job.subject_ref,
            scope=job.authority_context_ref or f"job:{job.job_id}",
            decision=StepAuthorityDecision.DENY,
            decision_ref="fail-closed:no-gate-configured",
            policy_version=self.policy_version,
            evaluated_at=step.created_at or "1970-01-01T00:00:00Z",
            reason="no authority provider configured; failing closed",
            requirement=step.authority_requirement,
        )


def _matches(pattern: str, value: str) -> bool:
    """Same matching discipline as the policy engine: exact or prefix-star."""
    if pattern == "*":
        return True
    if pattern.endswith("*") and value.startswith(pattern[:-1]):
        return True
    return pattern == value


class PermissiveStepAuthorityGate:
    """Explicit test/composition gate: baseline worker actions permitted.

    ONLY for deterministic test fixtures that exercise non-governance
    semantics (retries, idempotency, leases, recovery). Permits exactly the
    derived baseline action of each step (``execute.<step_type>``) and still
    fails closed for any declared ``authority_requirement`` — a declared
    requirement always needs a real provider verdict.
    """

    policy_version = "permissive-test-1"

    def evaluate_step_authority(self, step, job, *, worker_id: str) -> StepAuthorityVerdict:
        declared = (step.authority_requirement or "").strip()
        if declared:
            decision = StepAuthorityDecision.REQUIRE_APPROVAL
            ref = f"{self.policy_version}:declared-requirement"
            reason = "declared authority requirement needs a real provider"
        else:
            decision = StepAuthorityDecision.ALLOW
            ref = f"{self.policy_version}:baseline"
            reason = "test gate: baseline worker action permitted"
        return StepAuthorityVerdict(
            step_id=step.step_id,
            job_id=job.job_id,
            principal=worker_id,
            action=declared or f"execute.{step.step_type}",
            resource=job.subject_ref,
            scope=job.authority_context_ref or f"job:{job.job_id}",
            decision=decision,
            decision_ref=ref,
            policy_version=self.policy_version,
            evaluated_at=step.created_at or "1970-01-01T00:00:00Z",
            reason=reason,
            requirement=declared,
        )


class StaticStepAuthorityGate:
    """Policy-as-data gate: a fixed, versioned action declaration.

    Declared actions either ALLOW or REQUIRE_APPROVAL; everything else DENIES
    (fail closed). Useful for composition roots and deterministic test
    fixtures; not a substitute for the policy engine, which it mirrors
    structurally (first declared match wins, unknown actions deny).
    """

    def __init__(
        self,
        allowed: Tuple[str, ...] = (),
        *,
        require_approval: Tuple[str, ...] = (),
        policy_version: str = "static-1",
        constraints: Tuple[str, ...] = (),
        clock=None,
    ) -> None:
        self._allowed = tuple(allowed)
        self._require_approval = tuple(require_approval)
        self._constraints = tuple(constraints)
        self._version = policy_version
        self._clock = clock or (lambda: "1970-01-01T00:00:00Z")

    def evaluate_step_authority(self, step, job, *, worker_id: str) -> StepAuthorityVerdict:
        action = baseline_action_for_step(step)
        scope = job.authority_context_ref or f"job:{job.job_id}"

        def _verdict(decision: StepAuthorityDecision, ref: str, reason: str,
                     constraints: tuple = ()) -> StepAuthorityVerdict:
            return StepAuthorityVerdict(
                step_id=step.step_id,
                job_id=job.job_id,
                principal=worker_id,
                action=action,
                resource=job.subject_ref,
                scope=scope,
                decision=decision,
                decision_ref=ref,
                policy_version=self._version,
                evaluated_at=self._clock(),
                reason=reason,
                constraints=constraints,
                requirement=step.authority_requirement,
            )

        for pattern in self._require_approval:
            if _matches(pattern, action):
                return _verdict(
                    StepAuthorityDecision.REQUIRE_APPROVAL,
                    f"{self._version}:require_approval:{pattern}",
                    f"action {action!r} requires operator approval (declared {pattern!r})",
                )
        for pattern in self._allowed:
            if _matches(pattern, action):
                return _verdict(
                    StepAuthorityDecision.ALLOW_WITH_CONSTRAINTS if self._constraints
                    else StepAuthorityDecision.ALLOW,
                    f"{self._version}:allow:{pattern}",
                    f"action {action!r} declared permitted (declared {pattern!r})",
                    self._constraints,
                )
        return _verdict(
            StepAuthorityDecision.DENY,
            f"{self._version}:fail_closed",
            f"action {action!r} is not declared to this gate; failing closed",
        )
