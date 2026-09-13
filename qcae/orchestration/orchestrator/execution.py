"""Durable idempotency / execution semantics (P2-C07R2; repair directive §2.2).

Execution records close the crash window the completion-marker design left
open (effect committed, marker not written ⇒ silent re-execution on retry):

    RESERVED   — key durably reserved BEFORE any effect is attempted
    EXECUTING  — worker began; outcome unknown after a crash
    COMMITTED  — effect + result durably recorded; retries reconstruct
    FAILED     — worker reported failure before any side effect
    ABANDONED  — superseded key; explicit operator/repair action

Laws (directive §2.2):

- the reservation is the idempotency boundary: it happens before execution;
- duplicate reservations are deterministic (same key → same decision);
- COMMITTED returns/reconstructs the prior result without re-executing;
- unresolved EXECUTING after a crash is NEVER silently treated as safe —
  recovery reports it and classifies the step per replay safety;
- workers performing external side effects must be IDEMPOTENCY_AWARE
  (accept and honor the key) or NON_REPLAY_SAFE (ambiguous crash → explicit
  recovery escalation, never a blind rerun).

Truthful claim: the orchestrator provides at-least-once execution with
durable dedup for IDEMPOTENCY_AWARE workers. It does NOT claim exactly-once
for NON_REPLAY_SAFE external effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.errors import QcaeStateTransitionError, QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = [
    "ExecutionState",
    "ReplaySafety",
    "ExecutionRecord",
    "EXECUTION_TRANSITIONS",
    "assert_execution_transition",
]


class ExecutionState(StrEnum):
    """Durable execution-record states (repair directive §2.2)."""

    RESERVED = "RESERVED"
    EXECUTING = "EXECUTING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class ReplaySafety(StrEnum):
    """Worker classification governing ambiguous-crash behavior (§2.2)."""

    #: in-memory/deterministic work; re-execution is harmless
    REPLAY_SAFE = "REPLAY_SAFE"
    #: accepts an idempotency key and deduplicates the external effect
    IDEMPOTENCY_AWARE = "IDEMPOTENCY_AWARE"
    #: external side effect without worker-side dedup: ambiguous crash is
    #: escalated to explicit recovery, never blindly rerun
    NON_REPLAY_SAFE = "NON_REPLAY_SAFE"


#: Explicit, closed-world execution-record transitions. ABANDONED and
#: COMMITTED are terminal for the record; FAILED may be re-reserved as a new
#: attempt (same key, deterministic same-key semantics per store contract).
EXECUTION_TRANSITIONS = {
    (ExecutionState.RESERVED, ExecutionState.EXECUTING),
    (ExecutionState.RESERVED, ExecutionState.FAILED),
    (ExecutionState.RESERVED, ExecutionState.ABANDONED),
    (ExecutionState.EXECUTING, ExecutionState.COMMITTED),
    (ExecutionState.EXECUTING, ExecutionState.FAILED),
    (ExecutionState.EXECUTING, ExecutionState.EXECUTING),
    (ExecutionState.FAILED, ExecutionState.RESERVED),
    # Retry of a previously failed record re-enters execution (same key,
    # deterministic same-key semantics; the reservation boundary still holds).
    (ExecutionState.FAILED, ExecutionState.EXECUTING),
}


def assert_execution_transition(current: ExecutionState, target: ExecutionState) -> None:
    if not isinstance(current, ExecutionState) or not isinstance(target, ExecutionState):
        raise QcaeStateTransitionError(
            f"unknown execution state(s): {current!r} -> {target!r}"
        )
    if (current, target) not in EXECUTION_TRANSITIONS:
        raise QcaeStateTransitionError(
            f"illegal execution transition {current.value} -> {target.value}"
        )


@dataclass(frozen=True)
class ExecutionRecord(SerializableRecord):
    """Durable per-key execution record (idempotency boundary)."""

    SCHEMA_VERSION = 1

    idempotency_key: str
    job_id: str
    step_id: str
    state: ExecutionState
    replay_safety: ReplaySafety

    reserved_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    result_digest: str = ""
    #: canonical JSON of the committed WorkerResult so retries/recovery can
    #: reconstruct the prior outcome without re-executing the effect.
    result_json: str = ""

    _COERCIONS = {
        "state": lambda v: coerce_enum(v, ExecutionState),
        "replay_safety": lambda v: coerce_enum(v, ReplaySafety),
    }

    def validate(self) -> None:
        require_non_empty_str(self.idempotency_key, "idempotency_key")
        require_identifier(self.job_id, "job_id")
        require_identifier(self.step_id, "step_id")
        if not isinstance(self.state, ExecutionState):
            raise QcaeValidationError(
                f"state must be an ExecutionState member, got {self.state!r}"
            )
        if not isinstance(self.replay_safety, ReplaySafety):
            raise QcaeValidationError(
                f"replay_safety must be a ReplaySafety member, got {self.replay_safety!r}"
            )
        require_non_empty_str(self.reserved_at, "reserved_at")
        if self.state is ExecutionState.COMMITTED and not self.completed_at:
            raise QcaeValidationError("COMMITTED records must carry completed_at")
        if self.state is not ExecutionState.COMMITTED and self.completed_at:
            raise QcaeValidationError(
                "completed_at may only be set on COMMITTED records"
            )
        if self.state is ExecutionState.COMMITTED and not self.result_json:
            raise QcaeValidationError(
                "COMMITTED records must carry the committed result payload"
            )

    def reconstruct_result(self):
        """Rebuild the committed WorkerResult (no re-execution of effects)."""
        import json

        from qcae.orchestration.workers.contracts import WorkerResult

        if self.state is not ExecutionState.COMMITTED or not self.result_json:
            raise QcaeValidationError(
                f"execution {self.idempotency_key!r} has no committed result"
            )
        result = WorkerResult.from_dict(json.loads(self.result_json))
        result.validate()
        return result
