"""SENSOR-B5-I03 - registered instrument aliases (bloc_05/01 section 8).

:class:`InstrumentAlias` is one frozen evidence row binding an exact provider +
venue + alias_text (all verbatim, no normalization) to the contract instance it
denotes, over a dual-clock window:

* valid time  = when the alias text denoted that instance on that venue;
* known time  = when the registration could be justified.

The object name, the eleven fields and the six alias types are frozen by the
plan (section 8 lists exactly: alias_id, provider, venue, alias_text,
alias_type, contract_instance_id, valid_from, valid_to, known_from,
source_evidence_refs, confidence).  NOT present: ``known_to`` - the frozen
list has no such field and the I03 directive 7 expressly forbids inventing it.

``confidence`` is an opaque validated token (vocabulary matrix: no frozen
confidence vocabulary exists, directive 8 forbids inventing HIGH/MEDIUM/LOW or
any scale).  It is carried verbatim as evidence context; the resolver's
matching order must never depend on it or on any threshold.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, ConfigDict, Field, model_validator

from ..models import NormalizationModelBase, OpaqueIdentifier
from .models import (
    _EvidenceRef,
    _require_unique,
    UtcDatetime,
)
from .enums import AliasType

__all__ = ["InstrumentAlias"]


class InstrumentAlias(NormalizationModelBase):
    """One registered alias denotation (bloc_05/01 section 8, exact fields).

    Laws enforced here (fail closed):

    * non-blank, unpadded identifiers and alias text; text preserved verbatim
      (no case folding, no separator normalization - section 10);
    * timezone-aware UTC datetimes; naive input refused outright;
    * finite alias intervals order forward: ``valid_to > valid_from``;
    * source evidence non-empty, duplicate-free, never path-shaped;
    * ``confidence`` arrives as an opaque validated token, never as a number
      and never as one of the invented scale words.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    alias_id: OpaqueIdentifier
    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    alias_text: str
    alias_type: AliasType
    contract_instance_id: OpaqueIdentifier
    valid_from: UtcDatetime
    valid_to: UtcDatetime | None = None
    known_from: UtcDatetime
    source_evidence_refs: Annotated[
        tuple[_EvidenceRef, ...],
        Field(min_length=1),
        AfterValidator(_require_unique),
    ]
    confidence: str

    @model_validator(mode="after")
    def _validate_interval(self) -> InstrumentAlias:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("finite alias valid_to must be strictly after valid_from")
        return self
