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

from ...contracts.enums import SensorFamily
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
    "MappingProvenance",
    "TRUSTED_MANIFEST_RELPATH",
    "TRUSTED_MANIFEST_SCHEMA_VERSION",
    "TRUSTED_MANIFEST_SHA256",
    "load_trusted_authority",
    "verify_evidence_custody",
    "verify_liquidation_admission_provenance",
    "verify_mapping_provenance",
    "ApprovedArtifact",
    "AuthorityRefusal",
    "SemanticAuthority",
    "SemanticAuthorityRefusal",
    "parse_approval_manifest",
    "pit_availability_refusal",
    "resolve_authority_inputs",
    "load_semantic_authority",
    "manifest_digest",
    "evidence_digest",
]

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: SENSOR-B5-I09P2c: an offset-aware ISO-8601 instant.  The date-only
#: ``available_at`` cannot say when during the day an approval became operative,
#: so an intraday cutoff needs this finer statement (P2bR1 F4).
_ISO_INSTANT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _parse_offset_instant(value: str) -> datetime:
    """Parse an offset-aware instant, or refuse -- a naive value orders nothing.

    A bare timestamp has no position on a timeline, so it is refused rather than
    assumed to be UTC midnight; that assumption is exactly what made same-day
    availability look admissible in the previous checkpoint.
    """
    if not _ISO_INSTANT_RE.match(value):
        raise ValueError(
            "available_at_instant must be an offset-aware ISO-8601 instant "
            "(e.g. 2026-03-01T15:00:00+00:00); a naive or date-only value cannot "
            "be ordered against a knowledge cutoff"
        )
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:  # pragma: no cover
        raise ValueError("available_at_instant must state its UTC offset")
    return parsed

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
    #: The manifest bytes are not the reviewed production manifest.
    TRUSTED_ROOT_MISMATCH = "TRUSTED_ROOT_MISMATCH"
    #: The approval did not exist yet at the instant being evaluated.
    APPROVAL_NOT_YET_AVAILABLE = "APPROVAL_NOT_YET_AVAILABLE"
    #: An evidence reference has no verifiable blob under custody.
    EVIDENCE_BLOB_UNVERIFIED = "EVIDENCE_BLOB_UNVERIFIED"
    #: A record claims an admission without any provenance to check.
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    #: A record's declared provenance contradicts the trusted authority.
    PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"
    #: SENSOR-B5-I09P2e: the approval states neither availability field, so no
    #: cutoff can be shown to postdate it; it is admissible at no instant.
    PIT_AVAILABILITY_MISSING = "PIT_AVAILABILITY_MISSING"
    #: SENSOR-B5-I09P2e: a date-only availability certifies a calendar day, not
    #: an instant inside it, so a same-day intraday cutoff is ambiguous.
    INTRADAY_PIT_AMBIGUOUS = "INTRADAY_PIT_AMBIGUOUS"


class SemanticAuthorityRefusal(ValueError):
    """Typed refusal: ``refusal`` says which link failed, ``detail`` why."""

    def __init__(self, refusal: AuthorityRefusal, detail: str) -> None:
        self.refusal = refusal
        self.detail = detail
        super().__init__(f"{refusal.value}: {detail}")


def pit_availability_refusal(
    *,
    available_at: str | None,
    available_at_instant: str | None,
    evaluation_at: datetime | date | None,
) -> AuthorityRefusal | None:
    """The ONE point-in-time availability rule for approval admissibility.

    SENSOR-B5-I09P2e: the record-level verifiers refused an approval that states
    no availability at all, and refused a date-only approval on its own day,
    while :func:`verify_mapping_provenance` admitted both (P2dR1 F02).  Every PIT
    verification entry point now calls this function, so a caller cannot obtain
    the weaker answer by choosing a different public verifier.

    The rule, in order:

    * no cutoff -> ``None``: approval authentication alone is not a point-in-time
      claim, and the loader already refuses to project an approval that HAS
      availability without a cutoff;
    * an instant-precise basis is ordered against an offset-aware cutoff, and
      equality is admissible because the approval is operative at that instant;
    * a date-only basis certifies a calendar day, not an instant inside it, so a
      same-day intraday cutoff is ambiguous and refuses while a later day passes;
    * a bare-date cutoff keeps the frozen date-granular contract;
    * neither field -> the approval is admissible at no instant.
    """
    if evaluation_at is None:
        return None
    if available_at_instant is not None:
        if (
            not isinstance(evaluation_at, datetime)
            or evaluation_at.tzinfo is None
            or evaluation_at.utcoffset() is None
        ):
            return AuthorityRefusal.EVALUATION_TIME_REQUIRED
        if evaluation_at < _parse_offset_instant(available_at_instant):
            return AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE
        return None
    if available_at is not None:
        day = date.fromisoformat(available_at)
        if isinstance(evaluation_at, datetime):
            if evaluation_at.tzinfo is None or evaluation_at.utcoffset() is None:
                return AuthorityRefusal.EVALUATION_TIME_REQUIRED
            if evaluation_at.date() < day:
                return AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE
            if evaluation_at.date() == day:
                return AuthorityRefusal.INTRADAY_PIT_AMBIGUOUS
            return None
        if evaluation_at < day:
            return AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE
        return None
    return AuthorityRefusal.PIT_AVAILABILITY_MISSING


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
    #: When this approval first became operative.  A revision approved after a
    #: knowledge cutoff must not be applied before it existed (PIT law).
    available_at: str | None = None
    #: SENSOR-B5-I09P2c: when present this instant is authoritative over the
    #: date-only ``available_at``.  The date stays for history; the instant is the
    #: only statement precise enough to order against an intraday cutoff.
    available_at_instant: str | None = None
    #: evidence reference -> SHA-256 of the source blob held under custody.  A
    #: reference is only evidence when the bytes behind it can be checked.
    evidence_blobs: dict[str, str] = {}
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
        if self.available_at is not None:
            if not _ISO_DATE_RE.match(self.available_at):
                raise ValueError("available_at must be an ISO date (YYYY-MM-DD)")
            if self.available_at < self.approved_at:
                raise ValueError(
                    "available_at must not precede approved_at: an approval cannot "
                    "be operative before it was granted"
                )
        if self.available_at_instant is not None:
            instant = _parse_offset_instant(self.available_at_instant)
            if instant.date() < date.fromisoformat(self.approved_at):
                raise ValueError(
                    "available_at_instant must not precede approved_at: an "
                    "approval cannot be operative before it was granted"
                )
        bound_refs = {
            ref
            for fields in self.evidence.values()
            for refs in fields.values()
            for ref in refs
        }
        for ref, blob in self.evidence_blobs.items():
            if not _SHA256_HEX_RE.match(blob):
                raise ValueError(
                    f"evidence blob digest for {ref!r} must be 64 lowercase hex characters"
                )
            if ref not in bound_refs:
                raise ValueError(
                    f"evidence blob {ref!r} is not bound to any provider field by this "
                    "approval; an unbound blob certifies nothing"
                )
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
    available_at: str | None = None
    #: SENSOR-B5-I09P2c: when present this instant is authoritative over the
    #: date-only ``available_at``.  The date stays for history; the instant is the
    #: only statement precise enough to order against an intraday cutoff.
    available_at_instant: str | None = None
    evidence_blobs: dict[str, str] = {}

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


def manifest_digest(manifest_bytes: bytes) -> str:
    """SHA-256 of manifest BYTES -- the only digest the trust boundary needs.

    Exposed so the record-verification layer never imports a hashing library
    itself: digest verification IS this module's job (P2a), and the pure sensor
    layer is audited to stay hash-free (I10/I11 scope audits).
    """
    return hashlib.sha256(manifest_bytes).hexdigest()


def evidence_digest(blob: bytes) -> str:
    """SHA-256 of evidence BYTES -- computed here, never asserted by custody.

    SENSOR-B5-I09P2d: the P2c custody boundary asked a provider object for the
    digest it "held" and believed the answer, so an object holding no bytes
    could echo the approval's own public digest (P2cR1 F-R1-01).  Verification
    now hands the bytes over and hashes them HERE -- the module that owns
    digest verification -- so satisfying custody requires the approved bytes,
    not a string that repeats the expected value.  Hashing still never
    happens in the pure sensor layer (I10/I11 scope audits).
    """
    if not isinstance(blob, (bytes, bytearray)):
        raise TypeError(
            f"evidence_digest hashes bytes, got {type(blob).__name__}; a "
            "digest string is exactly the claim custody must stop accepting"
        )
    return hashlib.sha256(bytes(blob)).hexdigest()


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
    as_of_instant = None
    if evaluation_at is not None:
        as_of_instant = (
            evaluation_at.date()
            if isinstance(evaluation_at, datetime)
            else evaluation_at
        )
    if entry.available_at is not None:
        if as_of_instant is None:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.EVALUATION_TIME_REQUIRED,
                "this approval records when it became operative, so the caller must "
                "state the instant it is being applied at; a revision is not "
                "retroactively authoritative",
            )
        if as_of_instant < date.fromisoformat(entry.available_at):
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE,
                f"approval {entry.approval_id!r} became operative on "
                f"{entry.available_at}, after the evaluated instant "
                f"{as_of_instant.isoformat()}; a later approval cannot be projected "
                "backwards over an earlier knowledge cutoff",
            )
    if entry.available_at_instant is not None:
        if evaluation_at is None:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.EVALUATION_TIME_REQUIRED,
                "this approval states an instant-precise availability, so the "
                "caller must state an offset-aware instant; a calendar day "
                "cannot be ordered against an instant",
            )
        if (
            not isinstance(evaluation_at, datetime)
            or evaluation_at.tzinfo is None
            or evaluation_at.utcoffset() is None
        ):
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.EVALUATION_TIME_REQUIRED,
                "an instant-precise availability requires an offset-aware "
                "evaluation instant; a bare date or a naive datetime is refused "
                "rather than assumed to be UTC midnight",
            )
        if evaluation_at < _parse_offset_instant(entry.available_at_instant):
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.APPROVAL_NOT_YET_AVAILABLE,
                f"approval {entry.approval_id!r} became operative at "
                f"{entry.available_at_instant}, after the evaluated instant "
                f"{evaluation_at.isoformat()}; an intraday approval cannot be "
                "projected backwards over an earlier knowledge cutoff",
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
            "available_at": entry.available_at,
            "available_at_instant": entry.available_at_instant,
            "evidence_blobs": entry.evidence_blobs,
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

# ---------------------------------------------------------------------------
# SENSOR-B5-I09P2b - trusted initialization, custody and record verification
# ---------------------------------------------------------------------------

#: The reviewed production approval root, relative to the ``quant-lab`` tree.
TRUSTED_MANIFEST_RELPATH = (
    "config/crypto_sensor_fabric/provider_semantics/approval_manifest.json"
)

#: SHA-256 of the reviewed production manifest.  This constant IS the bootstrap
#: pin: it lives in reviewed source and in a governance ledger line, never
#: inside the manifest it describes, so the manifest cannot authenticate itself.
#: Changing the shipped manifest therefore requires a reviewed change here.
TRUSTED_MANIFEST_SHA256 = (
    "3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654"
)

#: The exact generation the reviewed root may declare.
TRUSTED_MANIFEST_SCHEMA_VERSION = "b5-i09p2a-1"


class MappingProvenance(NormalizationModelBase):
    """What one admitted canonical field claims about its authorization.

    An AUDIT TRAIL, not authentication: every field here is data a caller can
    type.  It becomes meaningful only when a consumer re-derives it with
    :func:`verify_mapping_provenance` against the trusted root.
    """

    model_config = {"extra": "forbid", "frozen": True}

    artifact_id: OpaqueIdentifier
    approval_id: OpaqueIdentifier
    registry_digest: str
    provider: OpaqueIdentifier
    provider_field: OpaqueIdentifier
    canonical_field: OpaqueIdentifier
    canonical_sensor: OpaqueIdentifier
    methodology_id: OpaqueIdentifier
    methodology_version: OpaqueIdentifier
    evidence_reference: OpaqueIdentifier | None = None
    semantic_confidence: str
    approved_at: str = ""
    available_at: str | None = None
    #: SENSOR-B5-I09P2c: when present this instant is authoritative over the
    #: date-only ``available_at``.  The date stays for history; the instant is the
    #: only statement precise enough to order against an intraday cutoff.
    available_at_instant: str | None = None

    @model_validator(mode="after")
    def _digest_law(self) -> MappingProvenance:
        if not _SHA256_HEX_RE.match(self.registry_digest):
            raise ValueError("registry_digest must be 64 lowercase hex characters")
        return self


def load_trusted_authority(
    *,
    manifest_bytes: bytes,
    artifact_id: str,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    evaluation_at: datetime | date | None = None,
) -> SemanticAuthority:
    """The production entry point: authority under the REVIEWED root.

    The distinction from :func:`load_semantic_authority` is the repair: that
    function trusts whichever manifest it is handed, which is a caller approving
    itself.  This one refuses any manifest whose bytes are not the pinned,
    reviewed production manifest, so an untrusted actor controlling both the
    artifact and the manifest gets ``TRUSTED_ROOT_MISMATCH``.

    Deployment assumption, stated plainly: the constant above is the anchor and
    it is only as strong as review of the commit that changes it.  This is a
    data boundary inside one process; it is not a signature scheme and does not
    resist code running with the application's privileges.
    """
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if digest != TRUSTED_MANIFEST_SHA256:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.TRUSTED_ROOT_MISMATCH,
            f"manifest bytes hash to {digest}; the reviewed production root is "
            f"{TRUSTED_MANIFEST_SHA256}. A manifest supplied by the actor that "
            "also supplies the artifact is not an approval (SENSOR-B5-I09P2b)",
        )
    manifest = parse_approval_manifest(manifest_bytes)
    if manifest.schema_version != TRUSTED_MANIFEST_SCHEMA_VERSION:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.TRUSTED_ROOT_MISMATCH,
            f"reviewed root declares schema {manifest.schema_version!r}, the pin "
            f"names {TRUSTED_MANIFEST_SCHEMA_VERSION!r}",
        )
    return load_semantic_authority(
        manifest_bytes=manifest_bytes,
        artifact_id=artifact_id,
        artifact_bytes=artifact_bytes,
        methodology_registry=methodology_registry,
        evaluation_at=evaluation_at,
    )


def verify_evidence_custody(
    authority: SemanticAuthority, custody: dict[str, str]
) -> None:
    """Every approved evidence reference must resolve to the bytes it names.

    ``custody`` maps an evidence reference to the SHA-256 the storage layer
    holds.  Custody proves the bytes exist and are unchanged; it does NOT prove
    the provider authored them, which stays an operator review obligation.
    """
    for reference, expected in authority.evidence_blobs.items():
        observed = custody.get(reference)
        if observed is None:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.EVIDENCE_BLOB_UNVERIFIED,
                f"evidence reference {reference!r} is approved but no blob is "
                "held under custody; a citation without bytes is a claim",
            )
        if observed != expected:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.EVIDENCE_BLOB_UNVERIFIED,
                f"evidence reference {reference!r} resolves to blob {observed}, "
                f"the approval names {expected}",
            )


def verify_mapping_provenance(
    provenance: MappingProvenance | None,
    *,
    manifest_bytes: bytes,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    evaluation_at: datetime | date | None = None,
) -> None:
    """Re-derive one record's admission against the trusted root.

    A consumer passes the record's declared provenance plus the independently
    held root, artifact bytes and evaluation instant.  It does not believe the
    record: it rebuilds the authority and checks that the row the record names
    is the row the approval actually covers.
    """
    if provenance is None:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISSING,
            "the record carries no authority provenance, so nothing can be "
            "verified; an unprovenanced admission is indistinguishable from a "
            "hand-written one",
        )
    authority = load_trusted_authority(
        manifest_bytes=manifest_bytes,
        artifact_id=provenance.artifact_id,
        artifact_bytes=artifact_bytes,
        methodology_registry=methodology_registry,
        evaluation_at=evaluation_at,
    )
    if authority.approval_id != provenance.approval_id:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"record claims approval {provenance.approval_id!r}, the trusted root "
            f"issues {authority.approval_id!r}",
        )
    if authority.registry_digest != provenance.registry_digest:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"record claims registry digest {provenance.registry_digest}, the "
            f"approved bytes hash to {authority.registry_digest}",
        )
    row = authority.registry.resolve(
        provenance.provider,
        provenance.provider_field,
        SensorFamily(provenance.canonical_sensor),
    )
    if row is None:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            "the approved registry declares no row for "
            f"({provenance.provider}, {provenance.provider_field}, "
            f"{provenance.canonical_sensor})",
        )
    if row.canonical_field != provenance.canonical_field:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"row maps to canonical field {row.canonical_field!r}, the record "
            f"claims {provenance.canonical_field!r}",
        )
    if (
        row.methodology_id != provenance.methodology_id
        or row.version != provenance.methodology_version
    ):
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"row cites methodology {row.methodology_id!r}@{row.version!r}, the "
            f"record claims {provenance.methodology_id!r}"
            f"@{provenance.methodology_version!r}",
        )
    if row.evidence_reference != provenance.evidence_reference:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            "the record's evidence reference is not the approved row's reference",
        )
    if row.semantic_confidence.value != provenance.semantic_confidence:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"row confidence is {row.semantic_confidence.value}, the record "
            f"claims {provenance.semantic_confidence}",
        )
    refusal = authority.attests(row)
    if refusal is not None:
        raise SemanticAuthorityRefusal(
            refusal,
            "the approved row is not attested by the trusted root; the record "
            "claims an admission the approval does not cover",
        )
    availability = pit_availability_refusal(
        available_at=authority.available_at,
        available_at_instant=authority.available_at_instant,
        evaluation_at=evaluation_at,
    )
    if availability is not None:
        raise SemanticAuthorityRefusal(
            availability,
            "the approval does not support a point-in-time admission at the "
            "evaluated instant; the record-level verifiers apply this same rule, "
            "so no public verifier answers differently (SENSOR-B5-I09P2e)",
        )



def verify_liquidation_admission_provenance(
    admission: object,
    *,
    artifact_id: str,
    manifest_bytes: bytes,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    evaluation_at: datetime | date | None = None,
) -> MappingProvenance:
    """Re-derive one liquidation side admission against the trusted root.

    ``LiquidationSideAdmission`` carries the approving identity rather than a
    full provenance object, so this reconstructs the provenance from the approved
    row and then applies the same re-derivation trade records get.  The admission
    does not serialize its provider, so the row is resolved by its exact
    (canonical field, provider field, methodology, version) identity and an
    ambiguous match refuses rather than guessing.
    """

    def _text(value: object) -> str:
        return str(getattr(value, "value", value))

    def _required(name: str) -> object:
        value = getattr(admission, name, None)
        if value is None:
            raise SemanticAuthorityRefusal(
                AuthorityRefusal.PROVENANCE_MISSING,
                f"liquidation admission states no {name!r}; a decision without an "
                "approving identity cannot be re-derived",
            )
        return value

    if not getattr(admission, "admitted", False):
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISSING,
            "a refused liquidation field is not an admission; nothing to verify",
        )
    approval_id = _text(_required("admission_approval_id"))
    registry_digest = _text(_required("admission_registry_digest"))
    canonical_field = _text(_required("canonical_field"))
    provider_field = _text(_required("provider_field"))
    methodology_id = _text(_required("methodology_id"))
    mapping_version = _text(_required("mapping_version"))
    _required("evidence_reference")

    authority = load_trusted_authority(
        manifest_bytes=manifest_bytes,
        artifact_id=artifact_id,
        artifact_bytes=artifact_bytes,
        methodology_registry=methodology_registry,
        evaluation_at=evaluation_at,
    )
    if authority.approval_id != approval_id:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"admission claims approval {approval_id!r}, the trusted root issues "
            f"{authority.approval_id!r}",
        )
    if authority.registry_digest != registry_digest:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"admission claims registry digest {registry_digest}, the approved "
            f"bytes hash to {authority.registry_digest}",
        )
    candidates = [
        row
        for row in authority.registry.mappings
        if row.canonical_sensor is SensorFamily.MECHANICAL_LIQUIDATION
        and row.provider_field == provider_field
        and row.canonical_field == canonical_field
        and row.methodology_id == methodology_id
        and row.version == mapping_version
    ]
    if len(candidates) != 1:
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            f"the admission names {len(candidates)} approved rows; exactly one is "
            "required, so an ambiguous or absent mapping cannot be verified",
        )
    row = candidates[0]
    if row.methodology_id is None:  # pragma: no cover - filtered above
        raise SemanticAuthorityRefusal(
            AuthorityRefusal.PROVENANCE_MISMATCH,
            "the approved row cites no methodology, so its admission cannot be "
            "re-derived",
        )
    provenance = MappingProvenance(
        artifact_id=artifact_id,
        approval_id=authority.approval_id,
        registry_digest=authority.registry_digest,
        provider=row.provider,
        provider_field=row.provider_field,
        canonical_field=row.canonical_field,
        canonical_sensor=row.canonical_sensor.value,
        methodology_id=row.methodology_id,
        methodology_version=row.version,
        evidence_reference=row.evidence_reference,
        semantic_confidence=row.semantic_confidence.value,
        approved_at=str(getattr(authority, "approved_at", "")),
        available_at=authority.available_at,
    )
    verify_mapping_provenance(
        provenance,
        manifest_bytes=manifest_bytes,
        artifact_bytes=artifact_bytes,
        methodology_registry=methodology_registry,
        evaluation_at=evaluation_at,
    )
    return provenance
