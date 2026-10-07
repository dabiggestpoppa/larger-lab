"""SENSOR-B5-I03 - minimal lifecycle-event evidence record (bloc_05/01 section 6).

The frozen plan names the seven lifecycle states (section 6) but defines NO
LifecycleRecord object and no broad lifecycle-registry architecture.  The
vocabulary authority matrix records the smallest faithful representation the
directive authorizes (I03 directive 9: "the smallest explicit record needed to
bind ... ONLY if necessary"): one immutable event per state transition, tied to
the exact ContractInstance it speaks about, over a dual-clock window (valid
time = when the state was economically true; known time = when it could be
justified), with the same evidence discipline as every other I03 record.

Design laws:

* NATIVE_SYMBOL is deliberately NOT a field.  bloc_05/01 section 7 demoted the
  native symbol from durable contract identity in I02; a lifecycle event is
  spoken about the *instance*, and instance identity is the registry's job.
* DUAL-CLOCK gate: ``valid_from <= event_time < valid_to`` AND
  ``known_from <= knowledge_cutoff`` is enforced by the resolver, not by this
  record; the record only requires finite intervals to order forward.
* Frozen-immutable like every registry record: laundering a lifecycle event
  means publishing a new registry version, never editing history.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, ConfigDict, Field, model_validator

from ..models import NormalizationModelBase, OpaqueIdentifier
from .models import _EvidenceRef, _require_unique, UtcDatetime

__all__ = ["InstrumentLifecycle"]

from .enums import LifecycleState


class InstrumentLifecycle(NormalizationModelBase):
    """One lifecycle-state evidence record for one contract instance.

    State windows may abut (a DELISTING_ANNOUNCED window ending exactly when
    DELISTED begins) but must not overlap for the same instance+state; the
    registry-level validation refuses contradictory evidence at snapshot
    boundaries.  ``valid_to``/``known_to`` are ``None`` when open-ended.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    contract_instance_id: OpaqueIdentifier
    lifecycle_state: LifecycleState
    valid_from: UtcDatetime
    valid_to: UtcDatetime | None = None
    known_from: UtcDatetime
    known_to: UtcDatetime | None = None
    source_evidence_refs: Annotated[
        tuple[_EvidenceRef, ...],
        Field(min_length=1),
        AfterValidator(_require_unique),
    ]

    @model_validator(mode="after")
    def _validate_intervals(self) -> InstrumentLifecycle:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("finite valid_to must be strictly after valid_from")
        if self.known_to is not None and self.known_to <= self.known_from:
            raise ValueError("finite known_to must be strictly after known_from")
        return self
