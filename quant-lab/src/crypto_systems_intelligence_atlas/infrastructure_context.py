"""Scoped Book 4 infrastructure context; explicitly excludes Book 5 capital fields."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dependency_provenance import Book4Provenance
from .temporal import Timestamp, UnknownBound


class InfrastructureContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    context_id: str = Field(min_length=1)
    system_ref: str = Field(min_length=1)
    function: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    role_assignment_ids: tuple[str, ...] = ()
    dependency_ids: tuple[str, ...] = ()
    path_ids: tuple[str, ...] = ()
    failure_domain_ids: tuple[str, ...] = ()
    redundancy_ids: tuple[str, ...] = ()
    valid_time: Timestamp | UnknownBound
    book2_claim_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _technical_scope(self) -> "InfrastructureContext":
        forbidden = (
            "total value locked",
            "staking economics",
            "capital concentration",
            "credit risk",
            "derivative position",
            "yield farming",
            "collateral value",
        )
        text = f"{self.function} {self.scope}".lower()
        if any(term in text for term in forbidden):
            raise ValueError("Book 5 capital fields cannot enter Book 4 infrastructure context")
        return self


class InfrastructureContextBook:
    def __init__(self, provenance: Book4Provenance) -> None:
        self.provenance = provenance
        self._contexts: dict[str, InfrastructureContext] = {}

    def add(self, context: InfrastructureContext) -> InfrastructureContext:
        if context.context_id in self._contexts:
            raise ValueError("infrastructure context IDs are immutable and unique")
        self.provenance.validate_refs(context.book2_claim_refs)
        self._contexts[context.context_id] = context
        return context

    def require(self, context_id: str) -> InfrastructureContext:
        return self._contexts[context_id]


__all__ = ["InfrastructureContext", "InfrastructureContextBook"]
