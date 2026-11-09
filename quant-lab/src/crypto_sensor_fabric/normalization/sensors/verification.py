"""SENSOR-B5-I09P2c - full-record trusted verification, custody and intraday PIT.

The R1 audit measured that ``verify_mapping_provenance`` re-derived the APPROVAL
but never looked at the record, so a trade record whose canonical side had been
replaced verified clean against an unchanged mapping (P2B-18/P2B-19 FAIL).  This
module closes that hole and only that hole:

* :func:`verify_trade_record` takes the COMPLETE ``T1TradeRecord``, re-derives the
  approved row under the reviewed root, and re-executes the declared
  native->canonical transformation on the record's own preserved native value;
* :func:`verify_liquidation_record` takes the COMPLETE ``T1LiquidationRecord``,
  binds every admission to the RECORD's provider and to the exact canonical
  field it authorizes, and refuses a claim whose canonical value is not the
  admitted reading;
* :class:`TrustedAuthorityContext` is the only entry: it refuses to exist unless
  its manifest bytes are the reviewed production root, so the actor supplying
  observation data cannot supply its own approval;
* :class:`TrustedCustodyProvider` replaces the caller-authored custody dict with a
  protocol whose implementation must read bytes from a store the observation
  actor does not control;
* PIT admission here is instant-based and fail-closed: a date-only approval
  cannot certify ANY instant on its own day (R1 F4).

What this module deliberately does NOT claim, and says so in its result:

* ``source_lineage_verified`` is never ``True``.  A byte-identical forged record
  is indistinguishable from a legitimate one by serialization alone, so no
  evaluator here can attest that the provider payload was authentic.  Custody
  proves the approved evidence blob is held and unchanged; it does not prove
  authorship.
* ``instrument_authenticated`` / ``source_revision_authenticated`` stay ``False``
  unless the approval actually names them; the mapping binds provider, native
  field, canonical field, methodology and evidence -- nothing else.
* ``record_transformation_verified`` stays ``False`` for liquidation rows: the
  repository declares no EXECUTABLE liquidation transformation, and a prose
  ``transformation`` string is not proof.  Guessing one would invent provider
  semantics (bloc_05/04 section 3, bloc_05/07 F17).

Custody is verified by BYTES, never by a provider's report about itself: the
protocol hands over bytes and this module hashes them through the authority
module, so an object that echoes the approved digest without holding the bytes
fails (P2cR1 F-R1-01).  ``downstream_trusted`` is scoped to
``ECONOMIC_FIELD_BINDING`` and every dimension outside that scope is enumerated
in ``unverified_dimensions`` (F-R1-02); the result model refuses contradictory
combinations (F-R1-03); and an approval carrying no availability information is
admissible at no instant (F-R1-04).

Deployment state: ``INTEGRATION_STATE`` is ``INTEGRATION_REQUIRED``.  There is no
production ingestion application in this repository, so the initializer that
would read the reviewed manifest at startup does not exist; the boundary is
specified and tested, not deployed.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import Field, model_validator

from ...contracts.enums import AggressorSide, SensorFamily
from ...storage import IntegrityState, StorageEncoding
from .. import authority as _authority_pkg
from ..authority import (
    SemanticAuthority,
    evidence_digest,
    manifest_digest,
    SemanticAuthorityRefusal,
    load_trusted_authority,
    pit_availability_refusal,
)
from ..common.methodologies import NormalizationMethodologyRegistry
from ..common.semantic_registry import ProviderSemanticMapping
from ..models import NormalizationModelBase, OpaqueIdentifier
from .liquidation import (
    ContradictoryLiquidationSideError,
    LiquidationCanonicalField,
    LiquidationPositionSide,
    LiquidationRole,
    T1LiquidationRecord,
    require_consistent_liquidation_sides,
)
from .side_maps import apply_declared_side_transformation
from .trade import T1TradeRecord

__all__ = [
    "INTEGRATION_STATE",
    "BlobStoreCustody",
    "RecordVerification",
    "RecordVerificationError",
    "TRUST_SCOPE_ECONOMIC_FIELD_BINDING",
    "RecordVerificationRefusal",
    "TrustedAuthorityContext",
    "TrustedCustodyProvider",
    "verify_liquidation_record",
    "verify_trade_record",
]

#: The trusted-initialization boundary is specified and tested, NOT deployed:
#: this repository has no application startup path that would own the manifest.
INTEGRATION_STATE = "INTEGRATION_REQUIRED"

#: Topics the trusted verification layer refuses to certify from a mapping row.
_LINEAGE_NOTE = (
    "raw observation bytes are not reconstructible from a normalized record, so "
    "source lineage is not verified here; custody proves the approved evidence "
    "blob is held unchanged, not that the provider authored it"
)

#: SENSOR-B5-I09P2d: the ONE thing ``downstream_trusted`` is allowed to mean.
#: The P2cR1 audit measured that the flag read like a full authenticity badge
#: while venue, instrument, revision and acquisition stayed unauthenticated
#: (F-R1-02).  The scope is now named, and every dimension outside it is
#: enumerated in :attr:`RecordVerification.unverified_dimensions`.
TRUST_SCOPE_ECONOMIC_FIELD_BINDING = "ECONOMIC_FIELD_BINDING"

_SCOPE_NOTE = (
    "downstream_trusted is scoped to ECONOMIC_FIELD_BINDING only: the declared "
    "canonical field was re-derived from the approved mapping and the approved "
    "evidence bytes hash to the digest the approval names. Venue, instrument, "
    "source revision, acquisition lineage and custody-source authority are NOT "
    "authenticated and are enumerated in unverified_dimensions"
)

#: The dimensions this evaluator never establishes, in result order.  A trust
#: verdict that omitted them would read as an authentication claim it cannot
#: support (P2cR1 F-R1-02), so they are emitted on every verification.
_UNVERIFIED_DIMENSIONS: tuple[str, ...] = (
    "SOURCE_LINEAGE",
    "VENUE_IDENTITY",
    "INSTRUMENT_IDENTITY",
    "SOURCE_REVISION",
    "ACQUISITION_LINEAGE",
    "CUSTODY_SOURCE_AUTHORITY",
)


class RecordVerificationRefusal(str, Enum):
    """One closed vocabulary for the whole chain, so a consumer reads one name.

    The first block repeats the authority loader's own refusals verbatim (a
    record verification that fails inside the loader must not hide which link
    broke); the second block is new in P2c and names the record-level mismatch.
    """

    # -- authority chain (surfaced unchanged) ------------------------------
    NO_APPROVAL = "NO_APPROVAL"
    ARTIFACT_NOT_APPROVED = "ARTIFACT_NOT_APPROVED"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    APPROVAL_REVOKED = "APPROVAL_REVOKED"
    AUTHORITY_EXPIRED = "AUTHORITY_EXPIRED"
    EVALUATION_TIME_REQUIRED = "EVALUATION_TIME_REQUIRED"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    UNREGISTERED_METHODOLOGY = "UNREGISTERED_METHODOLOGY"
    EVIDENCE_NOT_BOUND_TO_PROVIDER = "EVIDENCE_NOT_BOUND_TO_PROVIDER"
    NATIVE_FIELD_NOT_DECLARED = "NATIVE_FIELD_NOT_DECLARED"
    TRANSFORMATION_NOT_APPROVED = "TRANSFORMATION_NOT_APPROVED"
    BLOCKING_ASSUMPTION_UNRESOLVED = "BLOCKING_ASSUMPTION_UNRESOLVED"
    MALFORMED_MANIFEST = "MALFORMED_MANIFEST"
    MALFORMED_ARTIFACT = "MALFORMED_ARTIFACT"
    UNTRUSTED_AUTHORITY = "UNTRUSTED_AUTHORITY"
    AMBIGUOUS_MAPPING = "AMBIGUOUS_MAPPING"
    TRUSTED_ROOT_MISMATCH = "TRUSTED_ROOT_MISMATCH"
    APPROVAL_NOT_YET_AVAILABLE = "APPROVAL_NOT_YET_AVAILABLE"
    EVIDENCE_BLOB_UNVERIFIED = "EVIDENCE_BLOB_UNVERIFIED"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"

    # -- record-level (P2c) ------------------------------------------------
    TRUSTED_CONTEXT_MISMATCH = "TRUSTED_CONTEXT_MISMATCH"
    RECORD_KIND_MISMATCH = "RECORD_KIND_MISMATCH"
    PROVIDER_MISMATCH = "PROVIDER_MISMATCH"
    NATIVE_FIELD_MISMATCH = "NATIVE_FIELD_MISMATCH"
    NATIVE_VALUE_MISSING = "NATIVE_VALUE_MISSING"
    CANONICAL_VALUE_MISSING = "CANONICAL_VALUE_MISSING"
    CANONICAL_VALUE_MISMATCH = "CANONICAL_VALUE_MISMATCH"
    TRANSFORMATION_UNVERIFIABLE = "TRANSFORMATION_UNVERIFIABLE"
    ADMISSION_MISSING = "ADMISSION_MISSING"
    ADMISSION_REFUSED = "ADMISSION_REFUSED"
    ADMISSION_MISMATCH = "ADMISSION_MISMATCH"
    INTRADAY_PIT_AMBIGUOUS = "INTRADAY_PIT_AMBIGUOUS"
    PIT_CUTOFF_REQUIRED = "PIT_CUTOFF_REQUIRED"
    CUSTODY_REQUIRED = "CUSTODY_REQUIRED"
    CUSTODY_UNVERIFIED = "CUSTODY_UNVERIFIED"

    # -- result-level (P2d) ------------------------------------------------
    PIT_AVAILABILITY_MISSING = "PIT_AVAILABILITY_MISSING"
    CONTRADICTORY_VERIFICATION = "CONTRADICTORY_VERIFICATION"


class RecordVerificationError(ValueError):
    """Typed refusal: ``refusal`` names the link, ``detail`` says why."""

    def __init__(self, refusal: RecordVerificationRefusal, detail: str) -> None:
        self.refusal = refusal
        self.detail = detail
        super().__init__(f"{refusal.value}: {detail}")


@runtime_checkable
class TrustedCustodyProvider(Protocol):
    """Custody as BYTES, not as a report about itself.

    SENSOR-B5-I09P2d: P2c asked for ``held_digest()`` and believed the answer,
    so an object that held no bytes but returned the approval's own public
    digest earned ``custody_verified=True`` and full downstream trust (P2cR1
    F-R1-01).  The boundary now hands over BYTES and the verifier hashes them
    itself, so the only way to satisfy ``read_evidence`` is to hold the
    approved bytes: producing that digest from other bytes is a preimage search.

    Returning ``None`` means "not held / not intact" and is never softened into
    a default.  Returning bytes proves they are PRESENT and UNCHANGED; it still
    does not prove who wrote them, which ``source_lineage_verified`` refuses to
    claim and ``custody_source_authorized`` reports separately.
    """

    def read_evidence(self, reference: str) -> bytes | None: ...


class BlobStoreCustody:
    """Bounded adapter over the accepted immutable blob store (test/composition).

    ``index`` maps an approved evidence reference to the content address the
    operator's catalog records.  The adapter then re-reads the stored object and
    re-hashes it, so a mutated object is refused even when the index still names
    the original digest.  The INDEX itself must be operator-controlled; wiring a
    caller-supplied index here reproduces the defect this checkpoint repairs, so
    production use is ``INTEGRATION_REQUIRED`` and the operational custody gate
    stays PARTIAL.
    """

    def __init__(self, store: Any, index: dict[str, str]) -> None:
        self._store = store
        self._index = dict(index)

    def read_evidence(self, reference: str) -> bytes | None:
        """Return the STORED BYTES, or ``None`` when nothing intact is held.

        The object is re-read and re-verified first, so a mutated object is
        refused even while the operator index still names the original digest.
        The verifier hashes what comes back; this adapter never speaks for the
        bytes it returns.
        """
        digest = self._index.get(reference)
        if digest is None:
            return None
        try:
            check = self._store.verify_blob(digest, StorageEncoding.NONE)
            if check.integrity_state is not IntegrityState.LOCAL_HASH_VERIFIED:
                return None
            with self._store.open_blob(digest, StorageEncoding.NONE) as handle:
                return handle.read()
        except Exception:  # a missing or unreadable object is not custody
            return None

    def held_digest(self, reference: str) -> str | None:
        """Digest of the bytes ACTUALLY READ, or ``None`` -- inspection only.

        Kept so operators (and the P2c tamper tests) can see what the adapter
        found; the verifier never calls this, because a digest that travels
        alone is the exact claim P2d stopped accepting.
        """
        blob = self.read_evidence(reference)
        if blob is None:
            return None
        return evidence_digest(blob)


class TrustedAuthorityContext(NormalizationModelBase):
    """The reviewed root, as the trusted initializer would hold it.

    Constructible only through :meth:`from_reviewed_root`, which refuses any
    manifest bytes that are not the pinned, reviewed production root.  That is
    what stops the actor supplying observation data from supplying its own
    approval: a forged manifest cannot produce a context at all.
    """

    model_config = {"extra": "forbid", "frozen": True}

    manifest_sha256: str
    artifact_id: OpaqueIdentifier
    manifest_bytes: bytes = Field(repr=False)

    @classmethod
    def from_reviewed_root(
        cls, *, manifest_bytes: bytes, artifact_id: str
    ) -> TrustedAuthorityContext:
        if not isinstance(manifest_bytes, bytes):
            raise TypeError(
                f"manifest_bytes must be bytes, got {type(manifest_bytes).__name__}"
            )
        digest = manifest_digest(manifest_bytes)
        pin = _authority_pkg.TRUSTED_MANIFEST_SHA256
        if digest != pin:
            raise RecordVerificationError(
                RecordVerificationRefusal.TRUSTED_CONTEXT_MISMATCH,
                f"manifest bytes hash to {digest}; the reviewed root is {pin}. A "
                "manifest supplied by the actor that also supplies the records is "
                "not an approval (SENSOR-B5-I09P2bR1 F5)",
            )
        return cls(
            manifest_sha256=digest, artifact_id=artifact_id, manifest_bytes=manifest_bytes
        )

    @model_validator(mode="after")
    def _pin_law(self) -> TrustedAuthorityContext:
        digest = manifest_digest(self.manifest_bytes)
        if digest != self.manifest_sha256:
            raise RecordVerificationError(
                RecordVerificationRefusal.TRUSTED_CONTEXT_MISMATCH,
                "the context's stored manifest bytes no longer hash to the digest "
                "it declares; a mutated context verifies nothing",
            )
        if digest != _authority_pkg.TRUSTED_MANIFEST_SHA256:
            raise RecordVerificationError(
                RecordVerificationRefusal.TRUSTED_CONTEXT_MISMATCH,
                "the context's manifest is not the reviewed production root",
            )
        return self


class RecordVerification(NormalizationModelBase):
    """What was actually established -- distinct claims, never one badge.

    P2d adds three things the P2cR1 audit found missing:

    * ``trust_scope`` names what ``downstream_trusted`` means (one scope only:
      ``ECONOMIC_FIELD_BINDING``), so the flag can no longer be read as an
      authenticity badge for the whole record;
    * ``unverified_dimensions`` enumerates what the verdict does NOT cover, and
      the laws refuse a downstream verdict that leaves it empty;
    * ``custody_source_authorized`` stays separate from ``custody_verified``:
      the second says the approved bytes were handed over and hashed here; the
      first says an independently controlled application owns that store, and
      this repository has no such initializer, so it is always ``False``.

    The positive claims are gated on proof references, so a result cannot
    assert lineage, instrument or revision authenticity it never established.
    """

    model_config = {"extra": "forbid", "frozen": True}

    record_kind: OpaqueIdentifier
    artifact_id: OpaqueIdentifier
    approval_id: OpaqueIdentifier
    registry_digest: OpaqueIdentifier
    provider: OpaqueIdentifier
    semantic_mapping_approved: bool
    record_transformation_verified: bool
    custody_verified: bool
    source_lineage_verified: bool = False
    pit_admissible: bool
    instrument_authenticated: bool = False
    source_revision_authenticated: bool = False
    downstream_trusted: bool
    trust_scope: OpaqueIdentifier = TRUST_SCOPE_ECONOMIC_FIELD_BINDING
    unverified_dimensions: tuple[OpaqueIdentifier, ...] = ()
    custody_source_authorized: bool = False
    lineage_proof: OpaqueIdentifier | None = None
    instrument_authentication_ref: OpaqueIdentifier | None = None
    revision_authentication_ref: OpaqueIdentifier | None = None
    fields_verified: tuple[OpaqueIdentifier, ...] = ()
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _trust_laws(self) -> RecordVerification:
        """A verdict may not claim more than its evidence established."""
        if self.trust_scope != TRUST_SCOPE_ECONOMIC_FIELD_BINDING:
            raise ValueError(
                f"trust_scope must be {TRUST_SCOPE_ECONOMIC_FIELD_BINDING!r}; a "
                "verdict that cannot name its scope cannot be consumed safely"
            )
        if self.downstream_trusted:
            prerequisites = {
                "semantic_mapping_approved": self.semantic_mapping_approved,
                "record_transformation_verified": self.record_transformation_verified,
                "custody_verified": self.custody_verified,
                "pit_admissible": self.pit_admissible,
            }
            absent = sorted(name for name, held in prerequisites.items() if not held)
            if absent:
                raise ValueError(
                    "downstream_trusted requires every in-scope prerequisite; "
                    f"absent: {absent} (P2cR1 F-R1-03)"
                )
            if not self.fields_verified:
                raise ValueError(
                    "downstream_trusted requires at least one verified canonical field"
                )
            if not self.unverified_dimensions:
                raise ValueError(
                    "a downstream verdict must enumerate the dimensions it does NOT "
                    "cover; an empty list reads as a whole-record authentication "
                    "claim no evaluator here can support (P2cR1 F-R1-02)"
                )
        claimed = {
            "SOURCE_LINEAGE": self.source_lineage_verified,
            "INSTRUMENT_IDENTITY": self.instrument_authenticated,
            "SOURCE_REVISION": self.source_revision_authenticated,
        }
        for dimension, held in claimed.items():
            if held and dimension in self.unverified_dimensions:
                raise ValueError(
                    f"{dimension} is claimed authentic and listed as unverified"
                )
        if self.source_lineage_verified and self.lineage_proof is None:
            raise ValueError(
                "source_lineage_verified requires a lineage proof reference; no "
                "evaluator in this repository can attest provider authorship"
            )
        if self.instrument_authenticated and self.instrument_authentication_ref is None:
            raise ValueError(
                "instrument_authenticated requires an approval that actually names "
                "the instrument; semantic mapping approval is not instrument identity"
            )
        if self.source_revision_authenticated and self.revision_authentication_ref is None:
            raise ValueError(
                "source_revision_authenticated requires a revision proof reference; "
                "a preserved revision string is data, not authentication"
            )
        return self

    def assert_trustworthy(self) -> None:
        """Re-run the laws over this object's own payload.

        ``model_copy(update=...)`` is a documented Pydantic bypass: it stamps a
        new field set without validating.  A consumer that accepts a copied
        result as final trusted evidence must call this first; the verifier's
        own results are validated at construction and pass unchanged.
        """
        try:
            RecordVerification.model_validate(self.model_dump())
        except ValueError as exc:
            raise RecordVerificationError(
                RecordVerificationRefusal.CONTRADICTORY_VERIFICATION,
                "this verification object does not satisfy its own laws; a "
                "model_copy(update=...) bypass can construct exactly this state, "
                f"so it must not be consumed as final evidence ({exc})",
            ) from exc


def _map_refusal(refusal: Any) -> RecordVerificationRefusal:
    return RecordVerificationRefusal(str(getattr(refusal, "value", refusal)))


def _derive_authority(
    context: TrustedAuthorityContext,
    *,
    artifact_id: str,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    knowledge_cutoff: datetime | None,
) -> SemanticAuthority:
    try:
        return load_trusted_authority(
            manifest_bytes=context.manifest_bytes,
            artifact_id=artifact_id,
            artifact_bytes=artifact_bytes,
            methodology_registry=methodology_registry,
            evaluation_at=knowledge_cutoff,
        )
    except SemanticAuthorityRefusal as exc:
        raise RecordVerificationError(_map_refusal(exc.refusal), exc.detail) from exc


def _row_for_provenance(
    authority: SemanticAuthority, provenance: Any
) -> ProviderSemanticMapping:
    """Re-derive the approved row the record claims, refusing every divergence."""
    if authority.approval_id != provenance.approval_id:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            f"record claims approval {provenance.approval_id!r}, the trusted root "
            f"issues {authority.approval_id!r}",
        )
    if authority.registry_digest != provenance.registry_digest:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            "record claims registry digest "
            f"{provenance.registry_digest}, the approved bytes hash to "
            f"{authority.registry_digest}",
        )
    try:
        family = SensorFamily(provenance.canonical_sensor)
    except ValueError as exc:  # pragma: no cover - model vocabulary is closed
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH, str(exc)
        ) from exc
    row = authority.registry.resolve(
        provenance.provider, provenance.provider_field, family
    )
    if row is None:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            "the approved registry declares no row for "
            f"({provenance.provider}, {provenance.provider_field}, "
            f"{provenance.canonical_sensor})",
        )
    if row.canonical_field != provenance.canonical_field:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            f"row maps to {row.canonical_field!r}, the record claims "
            f"{provenance.canonical_field!r}",
        )
    if (
        row.methodology_id != provenance.methodology_id
        or row.version != provenance.methodology_version
    ):
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            "the record's methodology identity is not the approved row's",
        )
    if row.evidence_reference != provenance.evidence_reference:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            "the record's evidence reference is not the approved row's reference",
        )
    if row.semantic_confidence.value != provenance.semantic_confidence:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISMATCH,
            f"row confidence is {row.semantic_confidence.value}, the record "
            f"claims {provenance.semantic_confidence}",
        )
    refusal = authority.attests(row)
    if refusal is not None:
        raise RecordVerificationError(
            _map_refusal(refusal),
            "the approved row is not attested by the trusted root",
        )
    return row


def _require_cutoff(knowledge_cutoff: datetime | None) -> None:
    """Reject an unusable cutoff BEFORE any authority is derived.

    Shape first: record verification is a point-in-time claim, so a bare date or
    a naive datetime cannot be ordered against availability and is refused with
    the cutoff's own name rather than surfacing a loader refusal that describes a
    different link.
    """
    if (
        knowledge_cutoff is None
        or not isinstance(knowledge_cutoff, datetime)
        or knowledge_cutoff.tzinfo is None
        or knowledge_cutoff.utcoffset() is None
    ):
        raise RecordVerificationError(
            RecordVerificationRefusal.PIT_CUTOFF_REQUIRED,
            "record verification is a point-in-time claim, so an offset-aware "
            "instant is required; a bare date or a naive datetime cannot be "
            "ordered against an approval's availability",
        )


def _assert_intraday_pit(
    authority: SemanticAuthority, knowledge_cutoff: datetime | None
) -> None:
    """Apply the ONE shared PIT availability rule (SENSOR-B5-I09P2e).

    P2d implemented this rule here, at the record layer, while
    ``verify_mapping_provenance`` had no equivalent, so an approval carrying no
    availability stayed admissible through the mapping entry point (P2dR1 F02).
    The rule now lives in the authority module and every PIT verification entry
    point calls it; this function only translates the refusal into the record
    vocabulary, so the two layers cannot drift apart again.
    """
    refusal = pit_availability_refusal(
        available_at=getattr(authority, "available_at", None),
        available_at_instant=getattr(authority, "available_at_instant", None),
        evaluation_at=knowledge_cutoff,
    )
    if refusal is None:
        return
    mapped = _map_refusal(refusal)
    if mapped is RecordVerificationRefusal.APPROVAL_NOT_YET_AVAILABLE:
        detail = (
            "the approval became operative at "
            f"{getattr(authority, 'available_at_instant', None) or getattr(authority, 'available_at', None)}"
            f", after the evaluated instant {knowledge_cutoff.isoformat()}"
        )
    elif mapped is RecordVerificationRefusal.INTRADAY_PIT_AMBIGUOUS:
        detail = (
            "the approval states only the date "
            f"{getattr(authority, 'available_at', None)}; it cannot certify an "
            "instant on that same day (SENSOR-B5-I09P2bR1 F4). Verification "
            "requires a later day or an instant-precise availability"
        )
    elif mapped is RecordVerificationRefusal.PIT_AVAILABILITY_MISSING:
        detail = (
            "the approval states neither available_at nor available_at_instant, so "
            "no cutoff can be shown to postdate it; an approval with no "
            "availability is admissible at no instant (P2cR1 F-R1-04)"
        )
    else:
        detail = (
            "an instant-precise availability requires an offset-aware evaluation "
            "instant; a bare date or a naive datetime is refused rather than "
            "assumed to be UTC midnight"
        )
    raise RecordVerificationError(mapped, detail)


def _custody_verified(
    authority: SemanticAuthority, custody: TrustedCustodyProvider | None
) -> bool:
    if custody is None:
        return False
    if not isinstance(custody, TrustedCustodyProvider):
        raise TypeError(
            "custody must implement TrustedCustodyProvider.held_digest(); a "
            "caller-authored {reference: digest} dictionary is the claim, not the "
            "custody, and accepting it was P2B-11's defect"
        )
    if not authority.evidence_blobs:
        return False
    for reference, expected in authority.evidence_blobs.items():
        blob = custody.read_evidence(reference)
        if blob is None:
            raise RecordVerificationError(
                RecordVerificationRefusal.CUSTODY_UNVERIFIED,
                f"evidence reference {reference!r} is approved but the trusted "
                "custody provider handed over no intact bytes for it",
            )
        observed = evidence_digest(blob)
        if observed != expected:
            raise RecordVerificationError(
                RecordVerificationRefusal.CUSTODY_UNVERIFIED,
                f"the bytes held for {reference!r} hash to {observed}, the "
                f"approval names {expected}; a custody object's own report is "
                "not evidence (P2cR1 F-R1-01)",
            )
    return True


def verify_trade_record(
    record: T1TradeRecord,
    *,
    trusted_context: TrustedAuthorityContext,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    knowledge_cutoff: datetime | None,
    custody: TrustedCustodyProvider | None = None,
) -> RecordVerification:
    """Verify a COMPLETE trade record against the reviewed root.

    The checks, in evidence-chain order: the record carries provenance; the
    approval the record names is re-derived from the pinned root; the approved
    row covers exactly the claimed canonical field, methodology and evidence; the
    record's provider and preserved native field are the row's; the preserved
    native value re-executes the DECLARED transformation to exactly the record's
    canonical side; the provisional mapping agrees; the cutoff is admissible; and
    (when supplied) the trusted custody provider holds the approved blob.

    ``custody=None`` is not a shortcut: the result then reports
    ``custody_verified=False`` and ``downstream_trusted=False``.
    """
    if not isinstance(record, T1TradeRecord):
        raise RecordVerificationError(
            RecordVerificationRefusal.RECORD_KIND_MISMATCH,
            f"verify_trade_record requires a T1TradeRecord, got "
            f"{type(record).__name__}",
        )
    if not isinstance(trusted_context, TrustedAuthorityContext):
        raise TypeError(
            "trusted_context must be a TrustedAuthorityContext built by the trusted "
            "initializer; raw manifest bytes are not a context"
        )
    provenance = record.authority_provenance
    if provenance is None:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVENANCE_MISSING,
            "the record carries no authority provenance, so its canonical side "
            "cannot be re-derived; a hand-written admission is indistinguishable "
            "from a normalized one",
        )
    _require_cutoff(knowledge_cutoff)
    authority = _derive_authority(
        trusted_context,
        artifact_id=provenance.artifact_id,
        artifact_bytes=artifact_bytes,
        methodology_registry=methodology_registry,
        knowledge_cutoff=knowledge_cutoff,
    )
    row = _row_for_provenance(authority, provenance)

    if record.provider != row.provider:
        raise RecordVerificationError(
            RecordVerificationRefusal.PROVIDER_MISMATCH,
            f"record provider is {record.provider!r}, the approved row belongs to "
            f"{row.provider!r}; a venue's polarity never transfers",
        )
    if record.native_side_field != row.provider_field:
        raise RecordVerificationError(
            RecordVerificationRefusal.NATIVE_FIELD_MISMATCH,
            f"record preserves native field {record.native_side_field!r}, the "
            f"approved row names {row.provider_field!r}",
        )
    if record.native_side_boolean is None:
        raise RecordVerificationError(
            RecordVerificationRefusal.NATIVE_VALUE_MISSING,
            "the record preserves no native boolean, so no transformation can be "
            "re-executed; an absent native value is evidence, not a default",
        )
    if record.aggressor_side is AggressorSide.UNKNOWN:
        raise RecordVerificationError(
            RecordVerificationRefusal.CANONICAL_VALUE_MISSING,
            "the record claims an approval but carries no canonical side",
        )
    expected = apply_declared_side_transformation(row, record.native_side_boolean)
    if expected is None:
        raise RecordVerificationError(
            RecordVerificationRefusal.TRANSFORMATION_UNVERIFIABLE,
            "no executable transformation is declared for "
            f"({row.provider}, {row.provider_field}, {row.methodology_id}); the "
            "row's prose transformation is not proof, and guessing a polarity is "
            "forbidden (bloc_05/07 F17)",
        )
    if record.aggressor_side is not expected:
        raise RecordVerificationError(
            RecordVerificationRefusal.CANONICAL_VALUE_MISMATCH,
            f"record claims aggressor_side={record.aggressor_side.value}, the "
            f"approved transformation of native isBuyerMaker="
            f"{record.native_side_boolean} yields {expected.value}",
        )
    provisional = record.provisional_side
    if provisional is not None:
        if (
            provisional.provider != row.provider
            or provisional.provider_field != row.provider_field
        ):
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                "the provisional reading names a different (provider, field) than "
                "the approved row",
            )
        if provisional.methodology_ref.methodology_id != row.methodology_id or (
            provisional.methodology_ref.version != row.version
        ):
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                "the provisional reading cites a different methodology identity "
                "than the approved row",
            )
        if provisional.mapped_side is not expected:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                f"the provisional reading is {provisional.mapped_side.value}, the "
                f"re-executed transformation yields {expected.value}",
            )
    _assert_intraday_pit(authority, knowledge_cutoff)
    custody_ok = _custody_verified(authority, custody)

    notes = [
        _LINEAGE_NOTE,
        _SCOPE_NOTE,
        "instrument identity is not part of the approved mapping, so it is "
        "preserved but not authenticated",
        "source revision identity is preserved but not authenticated by a "
        "semantic mapping",
    ]
    if not custody_ok:
        notes.append(
            "no trusted custody provider was supplied: evidence blobs are "
            "unverified and the record is not downstream-trusted"
        )
    return RecordVerification(
        record_kind="TRADE",
        artifact_id=authority.artifact_id,
        approval_id=authority.approval_id,
        registry_digest=authority.registry_digest,
        provider=record.provider,
        semantic_mapping_approved=True,
        record_transformation_verified=True,
        custody_verified=custody_ok,
        source_lineage_verified=False,
        pit_admissible=True,
        instrument_authenticated=False,
        source_revision_authenticated=False,
        downstream_trusted=custody_ok,
        trust_scope=TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
        unverified_dimensions=_UNVERIFIED_DIMENSIONS,
        custody_source_authorized=False,
        fields_verified=(row.canonical_field,),
        notes=tuple(notes),
    )


_LIQUIDATION_NATIVE_SLOTS: dict[LiquidationCanonicalField, tuple[str, str]] = {
    LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED: (
        "native_position_side_field",
        "native_position_side_value",
    ),
    LiquidationCanonicalField.EXECUTION_SIDE: (
        "native_execution_side_field",
        "native_execution_side_value",
    ),
    LiquidationCanonicalField.AGGRESSOR_SIDE: (
        "native_aggressor_side_field",
        "native_aggressor_side_value",
    ),
    LiquidationCanonicalField.MAKER_TAKER_ROLE: (
        "native_maker_taker_role_field",
        "native_maker_taker_role_value",
    ),
}


def verify_liquidation_record(
    record: T1LiquidationRecord,
    *,
    trusted_context: TrustedAuthorityContext,
    artifact_bytes: bytes,
    methodology_registry: NormalizationMethodologyRegistry,
    knowledge_cutoff: datetime | None,
    custody: TrustedCustodyProvider | None = None,
) -> RecordVerification:
    """Verify a COMPLETE liquidation record against the reviewed root.

    Every canonical side claim must have its OWN admitted ``side_admissions``
    decision, and that admission must resolve -- under the RECORD's provider, not
    by row uniqueness across unrelated venues -- to exactly the canonical field it
    claims, with the same methodology, version, evidence reference, confidence and
    approving identity.  The canonical value must be the admitted reading, and the
    provider's own preserved native field must be the admitted native field.

    ``record_transformation_verified`` stays ``False``: no executable liquidation
    transformation is declared in this repository, so the canonical value is
    verified against its admission, never against a re-executed provider
    transform.  That is the honest state and it is why the liquidation gate
    remains PARTIAL.
    """
    if not isinstance(record, T1LiquidationRecord):
        raise RecordVerificationError(
            RecordVerificationRefusal.RECORD_KIND_MISMATCH,
            "verify_liquidation_record requires a T1LiquidationRecord, got "
            f"{type(record).__name__}",
        )
    if not isinstance(trusted_context, TrustedAuthorityContext):
        raise TypeError(
            "trusted_context must be a TrustedAuthorityContext built by the trusted "
            "initializer; raw manifest bytes are not a context"
        )
    _require_cutoff(knowledge_cutoff)
    authority = _derive_authority(
        trusted_context,
        artifact_id=trusted_context.artifact_id,
        artifact_bytes=artifact_bytes,
        methodology_registry=methodology_registry,
        knowledge_cutoff=knowledge_cutoff,
    )

    claims: list[tuple[LiquidationCanonicalField, str]] = []
    if record.position_side_liquidated is not LiquidationPositionSide.UNKNOWN:
        claims.append(
            (
                LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED,
                record.position_side_liquidated.value,
            )
        )
    if record.execution_side is not AggressorSide.UNKNOWN:
        claims.append(
            (LiquidationCanonicalField.EXECUTION_SIDE, record.execution_side.value)
        )
    if record.aggressor_side is not AggressorSide.UNKNOWN:
        claims.append(
            (LiquidationCanonicalField.AGGRESSOR_SIDE, record.aggressor_side.value)
        )
    role = record.maker_taker_role
    if role is not None and role is not LiquidationRole.UNKNOWN:
        claims.append((LiquidationCanonicalField.MAKER_TAKER_ROLE, role.value))

    if not claims:
        return RecordVerification(
            record_kind="LIQUIDATION",
            artifact_id=authority.artifact_id,
            approval_id=authority.approval_id,
            registry_digest=authority.registry_digest,
            provider=record.provider,
            semantic_mapping_approved=False,
            record_transformation_verified=False,
            custody_verified=False,
            pit_admissible=False,
            downstream_trusted=False,
            trust_scope=TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
            unverified_dimensions=_UNVERIFIED_DIMENSIONS,
            custody_source_authorized=False,
            fields_verified=(),
            notes=(
                "the record claims no canonical side, so there is nothing to "
                "authorize; this is not a trusted record",
                _LINEAGE_NOTE,
            ),
        )

    by_field = {admission.canonical_field: admission for admission in record.side_admissions}
    verified_fields: list[str] = []
    for field, value in claims:
        admission = by_field.get(field)
        if admission is None:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISSING,
                f"canonical {field.value}={value} has no side admission; a "
                "canonical field is the admitted reading, never a new claim",
            )
        if not admission.admitted:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_REFUSED,
                f"canonical {field.value} is present while its admission was "
                f"refused ({admission.refusal.value if admission.refusal else 'unknown'})",
            )
        if admission.provider_field is None:  # pragma: no cover - model law
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                "an admitted field names no native provider field",
            )
        field_attr, value_attr = _LIQUIDATION_NATIVE_SLOTS[field]
        if getattr(record, field_attr) != admission.provider_field:
            raise RecordVerificationError(
                RecordVerificationRefusal.NATIVE_FIELD_MISMATCH,
                f"record preserves native field "
                f"{getattr(record, field_attr)!r} for {field.value}, the admission "
                f"names {admission.provider_field!r}",
            )
        if getattr(record, value_attr) is None:
            raise RecordVerificationError(
                RecordVerificationRefusal.NATIVE_VALUE_MISSING,
                f"record preserves no native value for {field.value}; an "
                "unattributed canonical claim is unverifiable",
            )
        row = authority.registry.resolve(
            record.provider,
            admission.provider_field,
            SensorFamily.MECHANICAL_LIQUIDATION,
        )
        if row is None:
            raise RecordVerificationError(
                RecordVerificationRefusal.PROVIDER_MISMATCH,
                f"the approved registry declares no liquidation row for the "
                f"record's provider {record.provider!r} and native field "
                f"{admission.provider_field!r}; uniqueness across venues is not "
                "identity",
            )
        if row.canonical_field != field.value:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                f"the approved row authorizes {row.canonical_field!r}, the record "
                f"claims {field.value}; one admission never authorizes a sibling "
                "field",
            )
        if (
            row.methodology_id != admission.methodology_id
            or row.version != admission.mapping_version
        ):
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                f"admission cites {admission.methodology_id}@"
                f"{admission.mapping_version}, the approved row is "
                f"{row.methodology_id}@{row.version}",
            )
        if row.evidence_reference != admission.evidence_reference:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                "the admission's evidence reference is not the approved row's",
            )
        if row.semantic_confidence is not admission.semantic_confidence:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                "the admission's confidence is not the approved row's",
            )
        if admission.admission_approval_id != authority.approval_id:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                f"admission claims approval {admission.admission_approval_id!r}, "
                f"the trusted root issues {authority.approval_id!r}",
            )
        if admission.admission_registry_digest != authority.registry_digest:
            raise RecordVerificationError(
                RecordVerificationRefusal.ADMISSION_MISMATCH,
                "the admission's registry digest is not the approved bytes' digest",
            )
        refusal = authority.attests(row)
        if refusal is not None:
            raise RecordVerificationError(
                _map_refusal(refusal),
                f"the approved row is not attested for {field.value}",
            )
        if admission.provisional_value != value:
            raise RecordVerificationError(
                RecordVerificationRefusal.CANONICAL_VALUE_MISMATCH,
                f"canonical {field.value}={value} disagrees with the admitted "
                f"reading {admission.provisional_value!r}",
            )
        verified_fields.append(field.value)

    try:
        require_consistent_liquidation_sides(
            record.position_side_liquidated, record.execution_side
        )
    except ContradictoryLiquidationSideError as exc:
        raise RecordVerificationError(
            RecordVerificationRefusal.CANONICAL_VALUE_MISMATCH,
            str(exc),
        ) from exc

    _assert_intraday_pit(authority, knowledge_cutoff)
    custody_ok = _custody_verified(authority, custody)

    notes = [
        _SCOPE_NOTE,
        "no executable liquidation transformation is declared in this repository, "
        "so each canonical value is verified against its admission rather than a "
        "re-executed provider transform; a posteriori mutation of BOTH the record "
        "and its admission is therefore outside this boundary",
        _LINEAGE_NOTE,
    ]
    if not custody_ok:
        notes.append(
            "no trusted custody provider was supplied: evidence blobs are "
            "unverified and the record is not downstream-trusted"
        )
    return RecordVerification(
        record_kind="LIQUIDATION",
        artifact_id=authority.artifact_id,
        approval_id=authority.approval_id,
        registry_digest=authority.registry_digest,
        provider=record.provider,
        semantic_mapping_approved=True,
        record_transformation_verified=False,
        custody_verified=custody_ok,
        source_lineage_verified=False,
        pit_admissible=True,
        instrument_authenticated=False,
        source_revision_authenticated=False,
        downstream_trusted=False,
        trust_scope=TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
        unverified_dimensions=_UNVERIFIED_DIMENSIONS,
        custody_source_authorized=False,
        fields_verified=tuple(verified_fields),
        notes=tuple(notes),
    )
