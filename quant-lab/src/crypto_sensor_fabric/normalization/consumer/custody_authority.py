"""SENSOR-B5-P3 - custody-source authority as a DERIVATION (Rung 3).

The harness defended authorization with a capability object: ``_issue()`` plus
a module-private ``_ISSUANCE_MARKER``.  It said so itself -- CAP01 (direct
minting) and CAP02 (marker copying) both work, and no in-process sentinel can
be made uncopyable.  Production therefore ships **no capability at all**: the
consumer never reads an authorization object, so a perfect forgery of one
authorizes nothing (design spec section 5).

Authorization is this function instead::

    (pinned manifest bytes, manifest sha256, artifact id, approval id,
     registry digest, record kind, provider, knowledge cutoff)
        -> AUTHORIZED | INTEGRATION_REQUIRED | UNAUTHORIZED

evaluated afresh at every consumption from bytes the policy loaded itself.  A
caller can compute the same function and gets the same answer, because there is
no value to steal.

**The honest limit of this rung.**  ``ApprovalManifest`` can approve a
``PROVIDER_SEMANTIC_REGISTRY`` artifact and its evidence blobs.  It carries no
record type that names a custody *source* as operator-authorized.  Design spec E
forbids reinterpreting ordinary artifact approval as custody-source
authorization, and this checkpoint is not authorized to invent the missing
record type.  So :func:`derive_custody_authority` checks every binding it can
check and then returns ``INTEGRATION_REQUIRED`` naming
:data:`UNRESOLVED_AUTHORITY_CONTRACT`.

Consequence, stated plainly: **no input can produce ``AUTHORIZED`` from the
shipped code.**  That is not a placeholder and not a permissive path -- it is
the bounded, fail-closed result the directive requires, and it is why the
approval manifest stays byte-identical and ``INTEGRATION_STATE`` stays
``INTEGRATION_REQUIRED``.  The positive ``AUTHORIZED`` branch is exercised only
by a wiring double in ``tests/`` (design spec E sanctions exactly that seam),
and ``tests/`` asserts that the production source never returns it.

No network, no filesystem, no wall clock, no id generation.  Manifest bytes
arrive as DATA.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable

import crypto_sensor_fabric.normalization.authority as _authority_pkg
from pydantic import ConfigDict, Field, model_validator

from ..authority import (
    ApprovalManifest,
    SemanticAuthorityRefusal,
    manifest_digest,
    parse_approval_manifest,
)
from ..models import NormalizationModelBase, OpaqueIdentifier
from .models import CustodyAuthorityBasis, KnowledgeCutoffInstant

__all__ = [
    "CustodyAuthorityDerivation",
    "CustodyAuthorityIdentity",
    "CustodySourceAuthoritySource",
    "ManifestCustodyAuthority",
    "SUPPORTED_RECORD_KINDS",
    "UNRESOLVED_AUTHORITY_CONTRACT",
    "derive_custody_authority",
]

#: The exact missing contract.  Named, not invented: no token in this module can
#: be written into a manifest to obtain authority, because :func:`derive` does
#: not look for one.
#: Kept short enough to survive the verdict's bounded diagnostic field intact:
#: a contract name truncated in the middle is not an actionable requirement.
UNRESOLVED_AUTHORITY_CONTRACT = (
    "OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1 is unresolved: the reviewed "
    "ApprovalManifest can approve a registry artifact and its evidence, but it "
    "has no record type naming a custody SOURCE (store, operator, record kinds, "
    "providers) as operator-authorized. Artifact approval is not source "
    "authorization, and inventing the record is outside this grant."
)

#: Record kinds the derivation can bind.  A wildcard kind does not exist: an
#: authorization for "any record" is the cross-record reuse CAP12 refuses.
SUPPORTED_RECORD_KINDS = ("TRADE", "LIQUIDATION")

_DETAIL_MAX = 400


class CustodyAuthorityIdentity(NormalizationModelBase):
    """The complete identity an authorization is valid for.  Nothing optional.

    Every element is bound because every element was a demonstrated reuse axis:
    CAP08b (provider), CAP12 (record kind), A07 (artifact/approval/registry),
    A08 (cutoff).  ``manifest_sha256`` binds the root the other elements were
    read under, so an identity derived under one root cannot be spent under
    another.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_sha256: OpaqueIdentifier
    artifact_id: OpaqueIdentifier
    approval_id: OpaqueIdentifier
    registry_digest: OpaqueIdentifier
    record_kind: OpaqueIdentifier
    provider: OpaqueIdentifier
    knowledge_cutoff: KnowledgeCutoffInstant

    @model_validator(mode="after")
    def _kind_law(self) -> CustodyAuthorityIdentity:
        if self.record_kind not in SUPPORTED_RECORD_KINDS:
            raise ValueError(
                f"record_kind must be one of {SUPPORTED_RECORD_KINDS}; an "
                "authorization that does not name its record kind is a wildcard"
            )
        return self


class CustodyAuthorityDerivation(NormalizationModelBase):
    """The derived basis, the bounded reason, and the contract still missing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    basis: CustodyAuthorityBasis
    detail: str = Field(max_length=_DETAIL_MAX)
    unresolved_contract: str | None = Field(default=None, max_length=_DETAIL_MAX)

    @model_validator(mode="after")
    def _basis_laws(self) -> CustodyAuthorityDerivation:
        if self.basis is CustodyAuthorityBasis.AUTHORIZED and self.unresolved_contract:
            raise ValueError(
                "an AUTHORIZED derivation that names a missing contract is "
                "contradictory: authorization cannot be granted while its "
                "authority record is unresolved"
            )
        if self.basis is CustodyAuthorityBasis.INTEGRATION_REQUIRED and not (
            self.unresolved_contract or self.detail
        ):
            raise ValueError(
                "INTEGRATION_REQUIRED must say which requirement is unmet; a bare "
                "deferral is indistinguishable from a default"
            )
        return self


@runtime_checkable
class CustodySourceAuthoritySource(Protocol):
    """The policy seam: something that can state a basis for one identity.

    Production's only constructed implementation is
    :class:`ManifestCustodyAuthority`.  A test passes a wiring double here --
    the seam design spec E sanctions -- precisely so the accepting branch can be
    exercised without shipping a synthetic basis in ``src/``.  A hostile wiring
    is a compromised process (threat-model X03), not a data attack, and the
    policy still requires ``custody_verified`` before it will read any
    ``AUTHORIZED`` basis.
    """

    def authorize(self, identity: CustodyAuthorityIdentity) -> CustodyAuthorityDerivation:
        ...


def _result(
    basis: CustodyAuthorityBasis,
    detail: str,
    *,
    unresolved: str | None = None,
) -> CustodyAuthorityDerivation:
    return CustodyAuthorityDerivation(
        basis=basis,
        detail=detail[:_DETAIL_MAX],
        unresolved_contract=unresolved[:_DETAIL_MAX] if unresolved else None,
    )


def derive_custody_authority(
    *, manifest_bytes: bytes, identity: CustodyAuthorityIdentity
) -> CustodyAuthorityDerivation:
    """Derive the basis from pinned bytes and one complete identity.

    Order matters and is the design's: root, schema, empty-manifest, artifact,
    approval, registry, revocation, validity at the cutoff, provider binding --
    and only then the authority requirement that does not exist yet.
    """
    if not isinstance(manifest_bytes, bytes):
        raise TypeError(
            "manifest_bytes must be bytes; a manifest object handed in by the "
            "actor that also supplies the record is not a reviewed root"
        )
    if not isinstance(identity, CustodyAuthorityIdentity):
        raise TypeError(
            "identity must be a CustodyAuthorityIdentity; raw kwargs are not a "
            "bound identity and cannot be authorized"
        )

    digest = manifest_digest(manifest_bytes)
    pin = _authority_pkg.TRUSTED_MANIFEST_SHA256
    if digest != pin:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            "the manifest bytes are not the reviewed production root; a manifest "
            "supplied beside the record is not an approval",
        )
    if identity.manifest_sha256 != digest:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            "the identity was derived under a different manifest root; authority "
            "does not travel between roots",
        )

    try:
        manifest: ApprovalManifest = parse_approval_manifest(manifest_bytes)
    except SemanticAuthorityRefusal as exc:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            f"the reviewed manifest does not parse: {getattr(exc, 'refusal', exc)}",
        )

    if not manifest.artifacts:
        return _result(
            CustodyAuthorityBasis.INTEGRATION_REQUIRED,
            "the reviewed manifest approves no artifact, so no custody source can "
            "be authorized under it",
            unresolved=UNRESOLVED_AUTHORITY_CONTRACT,
        )

    artifact = manifest.artifacts.get(identity.artifact_id)
    if artifact is None:
        return _result(
            CustodyAuthorityBasis.INTEGRATION_REQUIRED,
            "the reviewed manifest approves no artifact with this id, so there is "
            "no integration to authorize",
            unresolved=UNRESOLVED_AUTHORITY_CONTRACT,
        )

    if artifact.approval_id != identity.approval_id:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            "the approval id this record was derived under is not the approval the "
            "reviewed manifest names for this artifact",
        )
    if artifact.sha256 != identity.registry_digest:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            "the registry digest this record was derived under is not the digest "
            "the approval names; the record was verified against other bytes",
        )
    if identity.approval_id in manifest.revoked_approval_ids:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            "the approval covering this record has been revoked",
        )
    if identity.provider not in artifact.evidence:
        return _result(
            CustodyAuthorityBasis.UNAUTHORIZED,
            "the approval names no evidence for this provider; a venue's approval "
            "never transfers to another venue",
        )

    cutoff: datetime = identity.knowledge_cutoff
    if artifact.valid_until is not None:
        if cutoff.date() > date.fromisoformat(artifact.valid_until):
            return _result(
                CustodyAuthorityBasis.UNAUTHORIZED,
                "the approval had expired at the knowledge cutoff",
            )
    if artifact.available_at_instant is not None:
        operative = _parse_instant(artifact.available_at_instant)
        if cutoff < operative:
            return _result(
                CustodyAuthorityBasis.UNAUTHORIZED,
                "the approval was not yet operative at the knowledge cutoff",
            )

    # Every binding this schema can check has been checked.  The one it cannot
    # check is the authority requirement itself, and it is reported, not assumed.
    return _result(
        CustodyAuthorityBasis.INTEGRATION_REQUIRED,
        "artifact, approval, registry, provider and cutoff all bind, but the "
        "reviewed manifest carries no operator custody-source authority record; "
        "ordinary artifact approval is not source authorization",
        unresolved=UNRESOLVED_AUTHORITY_CONTRACT,
    )


def _parse_instant(value: str) -> datetime:
    """Parse an offset-aware manifest instant; the model law already proved it."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ManifestCustodyAuthority:
    """Production's only authority source: pinned manifest bytes it holds.

    It refuses foreign bytes at construction, so a caller cannot build one over
    a manifest of its own choosing.  It cannot return ``AUTHORIZED`` -- not
    because the branch is stubbed, but because no manifest this schema can
    express carries the authority record
    :data:`UNRESOLVED_AUTHORITY_CONTRACT` names.
    """

    def __init__(self, *, manifest_bytes: bytes) -> None:
        if not isinstance(manifest_bytes, bytes):
            raise TypeError("manifest_bytes must be bytes")
        digest = manifest_digest(manifest_bytes)
        pin = _authority_pkg.TRUSTED_MANIFEST_SHA256
        if digest != pin:
            raise ValueError(
                "ManifestCustodyAuthority refuses manifest bytes that are not the "
                "reviewed production root; a source built over the caller's own "
                "manifest would approve the caller"
            )
        self._manifest_bytes = manifest_bytes

    def authorize(self, identity: CustodyAuthorityIdentity) -> CustodyAuthorityDerivation:
        return derive_custody_authority(
            manifest_bytes=self._manifest_bytes, identity=identity
        )

    @property
    def manifest_sha256(self) -> str:
        return manifest_digest(self._manifest_bytes)
