"""SENSOR-B5-I09P2A - trusted provider-semantic authority loader (fail-closed).

The I09P2A implementation of the boundary designed in
``BLOC_05_I09P1_REGISTRY_TRUST_BOUNDARY.md``: registry BYTES are untrusted until
a separately controlled approval manifest names their digest, and consumers stop
treating a registry object as authority merely because it is registry-shaped.

Two actors, kept apart on purpose:

* **untrusted author** -- supplies registry bytes, and may put any digest it likes
  *inside* those bytes;
* **trusted approver** -- owns the manifest: the expected digest, the approval
  identity, the validity window, the revocation list, the permitted
  methodologies, the evidence bound to ``(provider, field)``, the declared native
  fields, the approved transformations and the resolved blocking assumptions.

The loader holds no authority of its own: it compares bytes to the MANIFEST's
digest, so a digest travelling beside the artifact it hashes is structurally
irrelevant.  That is the whole point of the design, and
``test_authority_rejects_self_declared_digest`` measures it.

Trust-domain statement (deliberately narrow, and not a security claim):

    This module defends against UNTRUSTED DATA -- registries parsed from
    configuration text, plugin payloads, imported files or any bytes a caller
    did not control.  It does NOT defend against arbitrary Python executing in
    the same interpreter with the loader's privileges: such code can import
    ``_LOADER_SEAL``, call private helpers or patch this module.  Record-level
    provenance is likewise *evidence data*, not an authenticated signature.
    The enforcement point for a fully compromised host is the process boundary,
    which this checkpoint does not and cannot build.

Purity: no network, no wall clock (validity is judged against a caller-supplied
``evaluation_at`` and refused when absent), no filesystem.  Bytes in, authority
out.  Hashing lives here because digest verification IS this module's job; the
pure registry models still mint no digest.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from ..models import NormalizationModelBase, OpaqueIdentifier, RegistryVersion
from ..common.methodologies import (
    NormalizationMethodologyRegistry,
    UnknownNormalizationMethodology,
)
from ..common.semantic_registry import (
    PENDING_EVIDENCE_REFERENCE,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    admits_critical_t1_use,
    parse_provider_semantic_registry_yaml,
)

__all__ = [
    "ApprovalManifest",
    "ApprovedArtifact",
    "AuthorityRefusal",
    "SemanticAuthority",
    "SemanticAuthorityRefusal",
    "parse_approval_manifest",
    "resolve_authority_inputs",
    "load_semantic_authority",
]

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: Module-private issuance seal.  ``SemanticAuthority`` cannot be constructed
#: without it, so a caller holding registry bytes has no path to an authority
#: object: the only path is :func:`load_semantic_authority` over approved bytes.
_LOADER_SEAL = object()


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class AuthorityRefusal(_StrEnum):
    """Why an authority was not issued, or why a row is not attested.

    Each member names the FIRST failed link in the chain, so an operator reading
    a refusal knows which artifact to fix rather than that "something" failed.
    """

    #: The manifest names no approval for this artifact at all.
    NO_APPROVAL = "NO_APPROVAL"
    #: The manifest exists and is well formed but approves no artifact with this id.
    ARTIFACT_NOT_APPROVED = "ARTIFACT_NOT_APPROVED"
    #: The bytes presented are not the bytes that were approved.
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    #: The approval was withdrawn after the fact.
    APPROVAL_REVOKED = "APPROVAL_REVOKED"
    #: The approval's validity window has closed.
    AUTHORITY_EXPIRED = "AUTHORITY_EXPIRED"
    #: A validity window exists and no evaluation instant was supplied.
    EVALUATION_TIME_REQUIRED = "EVALUATION_TIME_REQUIRED"
    #: The artifact's declared registry generation is not the approved one.
    VERSION_MISMATCH = "VERSION_MISMATCH"
    #: A cited methodology is not registered (or is registered at another version).
    UNREGISTERED_METHODOLOGY = "UNREGISTERED_METHODOLOGY"
    #: The cited evidence is not bound to this provider and field by the approval.
    EVIDENCE_NOT_BOUND_TO_PROVIDER = "EVIDENCE_NOT_BOUND_TO_PROVIDER"
    #: The native field is not declared for this provider by the approval.
    NATIVE_FIELD_NOT_DECLARED = "NATIVE_FIELD_NOT_DECLARED"
    #: The transformation is not the one the approval names for this field.
    TRANSFORMATION_NOT_APPROVED = "TRANSFORMATION_NOT_APPROVED"
    #: A blocking assumption has no documented resolution in the approval.
    BLOCKING_ASSUMPTION_UNRESOLVED = "BLOCKING_ASSUMPTION_UNRESOLVED"
    #: The manifest itself is unreadable, duplicated-keyed or ill-typed.
    MALFORMED_MANIFEST = "MALFORMED_MANIFEST"
    #: The artifact bytes are not a parseable provider-semantic registry.
    MALFORMED_ARTIFACT = "MALFORMED_ARTIFACT"
    #: No authority context was supplied where one is required.
    UNTRUSTED_AUTHORITY = "UNTRUSTED_AUTHORITY"
    #: Rows carry no confidence that may back a critical T1 field.
    AMBIGUOUS_MAPPING = "AMBIGUOUS_MAPPING"


class SemanticAuthorityRefusal(ValueError):
    """Typed refusal: ``refusal`` says which link failed, ``detail`` why."""

    def __init__(self, refusal: AuthorityRefusal, detail: str) -> None:
        self.refusal = refusal
        self.detail = detail
        super().__init__(f"{refusal.value}: {detail}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """A manifest with a repeated key has two readings; it has no authority."""
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.MALFORMED_MANIFEST,
                f"duplicate key {key!r} in the approval manifest: a manifest that "
                "can be read two ways cannot approve bytes",
            )
        seen[key] = value
    return seen


class ApprovedArtifact(NormalizationModelBase):
    """One approved artifact and everything the approval asserts about it.

    ``evidence`` is nested ``provider -> native field -> evidence refs`` on
    purpose: the P1 design binds evidence to the provider AND the field, so a
    row cannot borrow a sibling field's citation or another venue's document.

    ``approved_transformations`` is keyed by ``provider_field`` and is enforced
    only where it names a field: for a single approved artifact the digest
    already covers every transformation string, so the map exists for manifests
    that approve several artifacts and need to pin one field explicitly.
    """

    model_config = {"extra": "forbid", "frozen": True}

    sha256: str
    approval_id: OpaqueIdentifier
    artifact_kind: OpaqueIdentifier = "PROVIDER_SEMANTIC_REGISTRY"
    registry_schema_version: RegistryVersion
    approved_at: str
    valid_until: str | None = None
    allowed_methodologies: tuple[OpaqueIdentifier, ...] = Field(min_length=1)
    evidence: dict[str, dict[str, tuple[OpaqueIdentifier, ...]]]
    declared_native_fields: dict[str, tuple[OpaqueIdentifier, ...]]
    approved_transformations: dict[str, OpaqueIdentifier] = {}
    resolved_blocking_assumptions: tuple[OpaqueIdentifier, ...] = ()

    @model_validator(mode="after")
    def _approval_laws(self) -> ApprovedArtifact:
        if not _SHA256_HEX_RE.match(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hex characters")
        if not _ISO_DATE_RE.match(self.approved_at):
            raise ValueError("approved_at must be an ISO date (YYYY-MM-DD)")
        if self.valid_until is not None and not _ISO_DATE_RE.match(self.valid_until):
            raise ValueError("valid_until must be an ISO date (YYYY-MM-DD) or null")
        if self.valid_until is not None and self.valid_until < self.approved_at:
            raise ValueError("valid_until must not precede approved_at")
        for provider, fields in self.evidence.items():
            if not provider.strip() or not fields:
                raise ValueError(
                    "evidence must name a provider and at least one field; an "
                    "empty binding authorizes nothing and is a typo, not an approval"
                )
            for field_name, refs in fields.items():
                if not field_name.strip() or not refs:
                    raise ValueError(
                        f"evidence for {provider}/{field_name} must name at least "
                        "one reference"
                    )
                for ref in refs:
                    if ref == PENDING_EVIDENCE_REFERENCE:
                        raise ValueError(
                            "the pending probe token is not evidence: an approval "
                            "may not cite BLOC2_PROBE_PENDING"
                        )
        for provider, declared in self.declared_native_fields.items():
            if not declared:
                raise ValueError(f"declared_native_fields for {provider} is empty")
        return self


class ApprovalManifest(NormalizationModelBase):
    """The trust root: a reviewed, committed statement of what is approved.

    Ships EMPTY (``artifacts == {}``) so the default posture admits nothing.  It
    is deliberately *not* self-authenticating: its integrity is a review and
    commit fact, and any digest it might carry about itself would be exactly the
    self-approval this design refuses.
    """

    model_config = {"extra": "forbid", "frozen": True}

    schema_version: OpaqueIdentifier
    authority_id: OpaqueIdentifier
    artifacts: dict[str, ApprovedArtifact] = {}
    revoked_approval_ids: tuple[OpaqueIdentifier, ...] = ()

    @model_validator(mode="after")
    def _manifest_laws(self) -> ApprovalManifest:
        artifact_ids = set(self.artifacts)
        approval_ids: list[str] = []
        for artifact_id, entry in self.artifacts.items():
            if not artifact_id.strip():
                raise ValueError("artifact ids must be non-blank")
            approval_ids.append(entry.approval_id)
        duplicates = {value for value in approval_ids if approval_ids.count(value) > 1}
        if duplicates:
            raise ValueError(
                "two artifacts share one approval_id; an approval identifies "
                f"exactly one artifact (duplicates: {sorted(duplicates)})"
            )
        for revoked in self.revoked_approval_ids:
            if revoked in approval_ids and revoked not in {
                entry.approval_id for entry in self.artifacts.values()
            }:  # pragma: no cover - defensive
                raise ValueError("revoked id is not an approval in this manifest")
        if not artifact_ids and self.revoked_approval_ids:
            raise ValueError(
                "a manifest approving no artifact cannot revoke one; the empty "
                "shipping manifest carries no revocation list"
            )
        return self


class SemanticAuthority(NormalizationModelBase):
    """Loader-issued proof that specific registry bytes were approved.

    Constructible only through :func:`load_semantic_authority` (the ``before``
    validator requires the module's private seal).  Downstream consumers accept
    this type, never a bare ``ProviderSemanticRegistry``.
    """

    model_config = {"extra": "forbid", "frozen": True}

    artifact_id: OpaqueIdentifier
    approval_id: OpaqueIdentifier
    registry_digest: str
    manifest_authority_id: OpaqueIdentifier
    registry: ProviderSemanticRegistry
    allowed_methodologies: tuple[OpaqueIdentifier, ...]
    evidence: dict[str, dict[str, tuple[OpaqueIdentifier, ...]]]
    declared_native_fields: dict[str, tuple[OpaqueIdentifier, ...]]
    approved_transformations: dict[str, OpaqueIdentifier] = {}
    resolved_blocking_assumptions: tuple[OpaqueIdentifier, ...] = ()
    approved_at: str = ""
    valid_until: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _require_loader_seal(cls, payload: Any) -> Any:
        if not isinstance(payload, dict) or payload.get("_loader_seal") is not _LOADER_SEAL:
            raise ValueError(
                "SemanticAuthority is issued only by load_semantic_authority over "
                "approved bytes; a caller cannot mint authority from a registry it "
                "built itself (direct record/authority construction carries no "
                "approval)"
            )
        return {key: value for key, value in payload.items() if key != "_loader_seal"}

    def attests(self, row: ProviderSemanticMapping) -> AuthorityRefusal | None:
        """Does this approval cover THIS row?  ``None`` means yes.

        Cheap re-check of the binding that matters at admission time; the loader
        already proved the whole artifact, so this exists to stop a row from
        another registry (or another field) riding on an unrelated approval.
        """
        if self.registry.resolve(row.provider, row.provider_field, row.canonical_sensor) is None:
            return AuthorityRefusal.UNTRUSTED_AUTHORITY
        if row.methodology_id is None:
            return AuthorityRefusal.UNREGISTERED_METHODOLOGY
        if row.methodology_id not in self.allowed_methodologies:
            return AuthorityRefusal.UNREGISTERED_METHODOLOGY
        bound = self.evidence.get(row.provider, {}).get(row.provider_field, ())
        if row.evidence_reference is None or row.evidence_reference not in bound:
            return AuthorityRefusal.EVIDENCE_NOT_BOUND_TO_PROVIDER
        if row.provider_field not in self.declared_native_fields.get(row.provider, ()):
            return AuthorityRefusal.NATIVE_FIELD_NOT_DECLARED
        approved = self.approved_transformations.get(row.provider_field)
        if approved is not None and approved != row.transformation:
            return AuthorityRefusal.TRANSFORMATION_NOT_APPROVED
        for assumption in row.blocking_assumptions:
            if assumption not in self.resolved_blocking_assumptions:
                return AuthorityRefusal.BLOCKING_ASSUMPTION_UNRESOLVED
        if not admits_critical_t1_use(row.semantic_confidence):
            return AuthorityRefusal.AMBIGUOUS_MAPPING
        return None


def parse_approval_manifest(manifest_bytes: bytes) -> ApprovalManifest:
    """Parse manifest BYTES.  Duplicate keys and non-JSON are refused."""
    try:
        text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.MALFORMED_MANIFEST, f"manifest is not UTF-8: {exc}"
        ) from exc
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.MALFORMED_MANIFEST, f"manifest is not JSON: {exc}"
        ) from exc
    try:
        return ApprovalManifest.model_validate(payload)
    except ValueError as exc:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.MALFORMED_MANIFEST, str(exc).splitlines()[0]
        ) from exc


def _row_refusal(
    row: ProviderSemanticMapping,
    entry: ApprovedArtifact,
    methodology_registry: NormalizationMethodologyRegistry,
) -> AuthorityRefusal | None:
    """Validate one row against the approval, in evidence-chain order."""
    if row.methodology_id is None:
        return AuthorityRefusal.UNREGISTERED_METHODOLOGY
    try:
        methodology_registry.require(row.methodology_id, row.version)
    except UnknownNormalizationMethodology:
        return AuthorityRefusal.UNREGISTERED_METHODOLOGY
    if row.methodology_id not in entry.allowed_methodologies:
        return AuthorityRefusal.UNREGISTERED_METHODOLOGY
    if (
        row.evidence_reference is None
        or row.evidence_reference == PENDING_EVIDENCE_REFERENCE
        or row.evidence_reference
        not in entry.evidence.get(row.provider, {}).get(row.provider_field, ())
    ):
        return AuthorityRefusal.EVIDENCE_NOT_BOUND_TO_PROVIDER
    if row.provider_field not in entry.declared_native_fields.get(row.provider, ()):
        return AuthorityRefusal.NATIVE_FIELD_NOT_DECLARED
    approved = entry.approved_transformations.get(row.provider_field)
    if approved is not None and approved != row.transformation:
        return AuthorityRefusal.TRANSFORMATION_NOT_APPROVED
    for assumption in row.blocking_assumptions:
        if assumption not in entry.resolved_blocking_assumptions:
            return AuthorityRefusal.BLOCKING_ASSUMPTION_UNRESOLVED
    return None


def load_semantic_authority(
    *,
    manifest_bytes: bytes,
    artifact_id: str,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    evaluation_at: datetime | date | None = None,
) -> SemanticAuthority:
    """Issue an authority for ``artifact_bytes`` iff the manifest approves them.

    The order is the evidence chain so the refusal names the first broken link:
    manifest -> entry -> revocation -> validity -> digest -> parse -> version ->
    per-row methodology, evidence binding, declared field, transformation,
    assumption resolution.  Every step refuses; nothing is defaulted.
    """
    manifest = parse_approval_manifest(manifest_bytes)
    if not manifest.artifacts:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.NO_APPROVAL,
            f"manifest {manifest.authority_id!r} approves no artifact; the empty "
            "shipping manifest is the honest state of provider evidence and it "
            "admits nothing",
        )
    entry = manifest.artifacts.get(artifact_id)
    if entry is None:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.ARTIFACT_NOT_APPROVED,
            f"artifact {artifact_id!r} is not approved by manifest "
            f"{manifest.authority_id!r}",
        )
    if entry.approval_id in manifest.revoked_approval_ids:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.APPROVAL_REVOKED,
            f"approval {entry.approval_id!r} was revoked; a previously valid "
            "registry does not regain authority by being replayed",
        )
    if entry.valid_until is not None:
        if evaluation_at is None:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.EVALUATION_TIME_REQUIRED,
                "this approval carries a validity window, so the caller must state "
                "the instant it is being applied at; the loader never reads a clock",
            )
        as_of = evaluation_at.date() if isinstance(evaluation_at, datetime) else evaluation_at
        if as_of > date.fromisoformat(entry.valid_until):
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.AUTHORITY_EXPIRED,
                f"approval {entry.approval_id!r} expired on {entry.valid_until}; "
                "staleness is a refusal, never an automatic re-admission",
            )
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    if digest != entry.sha256:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.DIGEST_MISMATCH,
            f"artifact bytes hash to {digest}, the approval names {entry.sha256}; "
            "a digest inside the artifact is not evidence about the artifact",
        )
    try:
        text = artifact_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.MALFORMED_ARTIFACT, f"artifact is not UTF-8: {exc}"
        ) from exc
    try:
        registry = parse_provider_semantic_registry_yaml(text)
    except ValueError as exc:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.MALFORMED_ARTIFACT, str(exc).splitlines()[0]
        ) from exc
    if registry.schema_version != entry.registry_schema_version:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.VERSION_MISMATCH,
            f"artifact declares registry schema {registry.schema_version!r}, the "
            f"approval names {entry.registry_schema_version!r}",
        )
    for row in registry.mappings:
        refusal = _row_refusal(row, entry, methodology_registry)
        if refusal is not None:
            raise SemanticAuthorityRefusal(
                refusal,
                f"row ({row.provider}, {row.provider_field}, "
                f"{row.canonical_sensor.value}) is not covered by approval "
                f"{entry.approval_id!r}",
            )
    return SemanticAuthority.model_validate(
        {
            "_loader_seal": _LOADER_SEAL,
            "artifact_id": artifact_id,
            "approval_id": entry.approval_id,
            "registry_digest": digest,
            "manifest_authority_id": manifest.authority_id,
            "registry": registry,
            "allowed_methodologies": entry.allowed_methodologies,
            "evidence": entry.evidence,
            "declared_native_fields": entry.declared_native_fields,
            "approved_transformations": entry.approved_transformations,
            "resolved_blocking_assumptions": entry.resolved_blocking_assumptions,
            "approved_at": entry.approved_at,
            "valid_until": entry.valid_until,
        }
    )


def resolve_authority_inputs(
    registry: object | None, authority: object | None
) -> tuple[SemanticAuthority | None, ProviderSemanticRegistry | None]:
    """Split the two consumer inputs into (authority, registry-for-resolution).

    A ``SemanticAuthority`` passed in either slot becomes the authority and its
    own registry is used for resolution.  A bare ``ProviderSemanticRegistry``
    stays a DIAGNOSTIC value: rows may be read from it, but it confers no
    admission (the consumer refuses at the ladder with ``UNTRUSTED_AUTHORITY``).
    """
    resolved_authority = authority if isinstance(authority, SemanticAuthority) else None
    if isinstance(registry, SemanticAuthority):
        resolved_authority = resolved_authority or registry
        return resolved_authority, registry.registry
    resolved_registry = registry if isinstance(registry, ProviderSemanticRegistry) else None
    if resolved_authority is not None:
        return resolved_authority, resolved_authority.registry
    return None, resolved_registry
