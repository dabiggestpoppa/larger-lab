"""CSIA Book 2 — Bloc 2I: constrained research-system interface."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .acquisition import AcquisitionContract, AcquisitionType
from .claims import Claim, ClaimService, ClaimState
from .evidence import EvidenceStore, EvidenceTier, RawEvidence
from .sources import Source, SourceRegistry
from .temporal import normalize_utc


class ResearchOperation(str, Enum):
    DISCOVER = "DISCOVER"
    RETRIEVE = "RETRIEVE"
    PARSE = "PARSE"
    PROPOSE = "PROPOSE"
    CORROBORATE = "CORROBORATE"


class CorroborationMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    material_id: str = Field(min_length=1)
    target_claim_id: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    actor: str = Field(min_length=1)
    observed_at: datetime

    def model_post_init(self, __context: object) -> None:
        normalize_utc(self.observed_at)


class ResearchInterface:
    """API-surface firewall: proposal is not promotion.

    The class intentionally has no ``promote``, ``set_state``,
    ``set_authority``, ``mutate_graph``, ``mutate_time``, or
    ``bypass_provenance`` method. Research actors can only append to the
    registered source/evidence/claim ingress or record corroboration material.
    """

    def __init__(
        self,
        *,
        source_registry: SourceRegistry,
        evidence_store: EvidenceStore,
        claim_service: ClaimService,
    ) -> None:
        self.source_registry = source_registry
        self.evidence_store = evidence_store
        self.claim_service = claim_service
        self._corroborations: list[CorroborationMaterial] = []

    def discover(self, source: Source) -> Source:
        if source.source_id in self.source_registry:
            raise ValueError("source candidate must not overwrite a registered source")
        return self.source_registry.register(source)

    def retrieve(
        self,
        contract: AcquisitionContract,
        evidence: RawEvidence,
    ) -> RawEvidence:
        if evidence.source_id != contract.source_id:
            raise ValueError("retrieved evidence source does not match contract source")
        if contract.acquisition_type not in set(AcquisitionType):
            raise ValueError("unsupported acquisition type")
        return self.evidence_store.add(evidence)

    def parse(
        self,
        parent: RawEvidence,
        *,
        evidence_id: str,
        retrieved_at: datetime,
        content: bytes | str,
        content_locator: str,
        raw_snapshot_ref: str,
        extractor_version: str,
        parser_version: str,
        evidence_tier: EvidenceTier,
        claim_refs: tuple[str, ...] = (),
    ) -> RawEvidence:
        return self.evidence_store.derive(
            parent,
            evidence_id=evidence_id,
            retrieved_at=retrieved_at,
            content=content,
            content_locator=content_locator,
            raw_snapshot_ref=raw_snapshot_ref,
            extractor_version=extractor_version,
            parser_version=parser_version,
            evidence_tier=evidence_tier,
            claim_refs=claim_refs,
        )

    def propose(self, claim: Claim) -> Claim:
        if claim.claim_state is not ClaimState.DECLARED:
            raise ValueError("research systems may propose only DECLARED claims")
        return self.claim_service.add(claim)

    def corroborate(
        self,
        *,
        target_claim_id: str,
        evidence_refs: tuple[str, ...],
        actor: str,
        observed_at: datetime,
    ) -> CorroborationMaterial:
        self.claim_service.require(target_claim_id)
        if not evidence_refs:
            raise ValueError("corroboration requires evidence")
        for evidence_ref in evidence_refs:
            self.evidence_store.require(evidence_ref)
        payload = f"{target_claim_id}|{actor}|{normalize_utc(observed_at).isoformat()}"
        material = CorroborationMaterial(
            material_id="csia:corroboration:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24],
            target_claim_id=target_claim_id,
            evidence_refs=evidence_refs,
            actor=actor,
            observed_at=observed_at,
        )
        self._corroborations.append(material)
        return material

    @property
    def corroborations(self) -> tuple[CorroborationMaterial, ...]:
        return tuple(self._corroborations)


__all__ = [
    "CorroborationMaterial",
    "ResearchInterface",
    "ResearchOperation",
]
