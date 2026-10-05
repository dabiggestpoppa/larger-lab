"""SENSOR-B5-I01 — frozen Bloc 5 base normalization models and T1 envelope.

This module is the *container* layer of Bloc 5.  It defines the shape in which
a canonical observation may eventually be expressed and the vocabulary with
which it must report that it could not be expressed.  It resolves nothing:

* no registry, resolver or alias matching;
* no unit, notional or stablecoin conversion;
* no timestamp derivation, interval reconstruction or availability inference;
* no T1 writer, generation manifest, checksum or canonical query;
* no provider adapter, network call, DuckDB, catalog, path or blob access.

What it does instead is refuse.  The base layer is where the honest answers
have to be *representable*, so the validation laws below encode the frozen
fail-closed rules that would otherwise be discovered late:

* native evidence survives, and no canonical field exists to overwrite it
  (bloc_05/03 §1/§5, bloc_05/07 F12);
* ``0`` and absent are different answers, and absence is always typed
  (bloc_05/03 §14, bloc_05/07 F13);
* provider and venue stay separate fields (bloc_05/01 §13, F1);
* a blocked or quarantined row must say WHY, and a verified row must name the
  registry and methodology versions it was produced under
  (bloc_05/01 §15, bloc_05/05 §12/§20, bloc_05/06 §3);
* lineage is a required chain, and a broken chain blocks
  (bloc_05/05 §3/§11, bloc_05/07 F25);
* nothing may claim verified status next to a flag a frozen gate treats as
  failed.

Model convention follows the accepted storage layer (``extra="forbid"``, plain
pydantic ``BaseModel``): the repository's models are validated mutable objects
with UTC-normalizing validators, so the base layer matches them rather than
introducing a second convention.  Determinism is delivered by canonical
serialization (:func:`canonical_json_bytes`) plus the canonical flag ordering
the envelope enforces, not by a new base class.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from ..contracts.base import normalize_utc_datetimes
from ..contracts.enums import SensorFamily
from ..probes.enums import Granularity
from ..storage import (
    CoverageState,
    RevisionState,
    SourceUnitContract,
    SourceUnitEvidence,
)
from .enums import (
    _FLAG_ORDER,
    BLOCKED_STATUS_MISSINGNESS_REASON,
    BLOCKING_QUALITY_FLAGS,
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    MissingnessReason,
    NormalizationQualityFlag,
    NormalizationStatus,
    QuarantineReason,
    QualityDimensionState,
    TimestampPrecision,
)

#: SHA-256 hexadecimal syntax.  Format-only; hashing lives in Bloc 4
#: (`storage.checksums`) and is never performed here.  The rule is duplicated
#: rather than imported because ``storage.checksums`` is deliberately outside
#: the accepted public handoff surface, and the dependency firewall
#: (``BLOC_04_I17_BLOC5_HANDOFF_CONTRACT`` §12/§13) forbids reaching past it.
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_unpadded(value: str) -> str:
    """Reject leading/trailing whitespace on an opaque identifier.

    Padded identifiers are a silent identity hazard: ``"BINANCE_USDM "`` and
    ``"BINANCE_USDM"`` are different keys that render identically.
    """
    if value != value.strip():
        raise ValueError(f"must not carry leading/trailing whitespace: {value!r}")
    return value


def _reject_blank(value: str) -> str:
    """Reject whitespace-only identifiers, which are not identifiers."""
    if not value.strip():
        raise ValueError("must not be blank")
    return value


_OpaqueString = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
]

#: Validated opaque identifier: non-blank, unpadded, otherwise uninterpreted.
#:
#: Deliberately *not* a registry lookup and deliberately *not* a foreign key: at
#: B5-I01 no registry exists to resolve any of these, so the base layer can only
#: guarantee they are well-formed strings.
OpaqueIdentifier = _OpaqueString

#: T1 record identity.  TYPE ONLY -- see the class docstring of
#: :class:`T1BaseEnvelope` and ``BLOC_05_I01_TYPE_SCOPE_MATRIX.json``.
T1RecordId = _OpaqueString

#: PIT contract-instance identity.  TYPE ONLY; the registry is B5-I02.
#:
#: There is no ``UNKNOWN_CONTRACT`` or other placeholder member: bloc_05/01 §2.5
#: requires every economically normalized row to resolve to a real
#: ``contract_instance_id`` or fail closed, so a synthetic "unknown contract"
#: value would be a lie with a field name on it.  An unresolved row carries no
#: value here plus a blocked status instead.
ContractInstanceId = _OpaqueString

#: T1 generation identity.  TYPE ONLY; generation, manifest and atomic
#: publication are B5-I18.
T1GenerationId = _OpaqueString

#: A registry or methodology version reference.  TYPE ONLY; the identity,
#: contract-terms, semantic, methodology and time-semantics registries are
#: B5-I02/I04/I05/I09.  The base layer can name a version; it can never resolve
#: or mint one.
RegistryVersion = _OpaqueString


class NormalizationModelBase(BaseModel):
    """Common fail-closed configuration for every Bloc 5 base model.

    ``extra="forbid"`` matches the accepted storage convention: an unknown
    field is a schema contradiction, never a silently accepted extra.
    """

    model_config = ConfigDict(extra="forbid")


def canonical_json_bytes(model: BaseModel) -> bytes:
    """Deterministic canonical serialization for the base layer.

    Mirrors the accepted storage rule (``storage/models.py``, SENSOR-B4-I01
    §37): UTF-8, sorted keys, enums serialized as their string values, UTC
    ISO-8601 timestamps, no ``repr`` and no wall-clock auto-population.  Two
    structurally equal envelopes therefore produce byte-identical output, which
    is what makes an eventual B5-I18 checksum reproducible.

    This is a serialization helper, not content hashing.  Hashing belongs to
    Bloc 4 and to B5-I16/I18; nothing here computes a T1 identity.
    """
    payload = json.loads(model.model_dump_json())
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


class ObservationTimeEnvelope(NormalizationModelBase):
    """PIT time coordinates, preserved and never derived (bloc_05/02 §2/§3).

    All nine canonical clocks stay distinct (bloc_05/07 F8):
    ``source_event_at``, ``interval_start_at``, ``interval_end_at``,
    ``effective_at``, ``published_at``, ``market_available_at``, ``observed_at``,
    ``ingested_at``, ``normalized_at``.  ``None`` means "not applicable or not
    verified" and never "same as another timestamp" (bloc_05/02 §2), so every
    field is Optional: at B5-I01 nothing derives any of them, and forcing a
    value here would be fabrication.

    Enforced laws:

    * timezone-aware, UTC-normalized, naive datetimes refused
      (bloc_05/02 §18 invariant 1, matching ``coerce_utc``);
    * ``interval_end_at >= interval_start_at`` -- the one ordering that is
      universally valid.  No ordering is assumed between the other clocks,
      because bloc_05/02 §6 explicitly requires a future-effective published
      value (``published_at < effective_at``) to stay representable;
    * interval bounds require an explicit ``interval_closed`` and
      ``interval_time_convention`` (bloc_05/02 §7): an interval whose boundary
      semantics are undeclared is the exact ambiguity the plan forbids;
    * ``market_available_at`` requires an ``availability_basis`` that is not
      ``UNKNOWN`` (bloc_05/02 §5: an unplaceable availability time must not be
      presented as a market-availability time).
    """

    source_event_at: datetime | None = None
    interval_start_at: datetime | None = None
    interval_end_at: datetime | None = None
    effective_at: datetime | None = None
    published_at: datetime | None = None
    market_available_at: datetime | None = None
    observed_at: datetime | None = None
    ingested_at: datetime | None = None
    normalized_at: datetime | None = None
    interval_closed: bool | None = None
    interval_time_convention: IntervalTimeConvention | None = None
    availability_basis: AvailabilityBasis | None = None
    source_precision: TimestampPrecision | None = None
    clock_skew_ms: Decimal | None = None
    clock_skew_methodology_id: OpaqueIdentifier | None = None

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> ObservationTimeEnvelope:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_interval_order(self) -> ObservationTimeEnvelope:
        start, end = self.interval_start_at, self.interval_end_at
        if start is not None and end is not None and end < start:
            raise ValueError(
                "interval_end_at must be >= interval_start_at "
                f"({end.isoformat()} < {start.isoformat()})"
            )
        return self

    @model_validator(mode="after")
    def _validate_interval_declaration(self) -> ObservationTimeEnvelope:
        has_bounds = (
            self.interval_start_at is not None or self.interval_end_at is not None
        )
        if has_bounds and self.interval_time_convention is None:
            raise ValueError(
                "interval bounds require interval_time_convention (bloc_05/02 §7): "
                "an undeclared boundary convention is a guess"
            )
        if has_bounds and self.interval_closed is None:
            raise ValueError(
                "interval bounds require an explicit interval_closed "
                "(bloc_05/02 §7); None is not a substitute for declaring it"
            )
        return self

    @model_validator(mode="after")
    def _validate_availability_basis(self) -> ObservationTimeEnvelope:
        if self.market_available_at is None:
            return self
        if self.availability_basis is None:
            raise ValueError(
                "market_available_at requires availability_basis "
                "(bloc_05/02 §5)"
            )
        if self.availability_basis is AvailabilityBasis.UNKNOWN:
            raise ValueError(
                "market_available_at must not be presented with an UNKNOWN "
                "availability_basis (bloc_05/02 §5)"
            )
        return self


class NativeQuantity(NormalizationModelBase):
    """One provider-native quantity, preserved verbatim (bloc_05/03 §1/§5).

    This model exists so that native truth has a place that canonical values
    cannot occupy.  It has a ``native_value`` and NO ``normalized_value``,
    ``canonical_value``, notional, base or USD field at all: the separation is
    structural rather than a convention that could be broken later, because at
    B5-I01 no conversion exists to store one (bloc_05/07 F12).

    * ``native_value`` is a ``Decimal`` so provider precision is neither
      rounded away nor widened into false precision (bloc_05/03 §3.1/§3.3).
    * ``native_unit_evidence`` is the accepted Bloc 4 public
      :class:`~crypto_sensor_fabric.storage.SourceUnitEvidence` object itself,
      not a re-implementation.  That keeps the truth-bound ``VERIFIED_NATIVE``
      proof law (BLOC_04_I17 §4.4) and the ``ROW_NATIVE`` location law
      (§4.5) exactly as Bloc 4 established them, and keeps ``UNIT_UNVERIFIED``
      meaning "no verified native-unit evidence", which never licenses guessing.
    * ``source_unit_contract`` carries the three-state unit contract verbatim:
      ``NO_UNIT_FIELDS`` is a positive declaration, ``UNIT_EVIDENCE_DECLARED``
      requires evidence, and both absent stays
      ``HISTORICAL_UNIT_CONTRACT_ABSENT`` -- a third, distinct state that must
      never be merged into either (BLOC_04_I17 §4.7).

    Dimensionless families (funding, basis, positioning -- BLOC_04_I17 §5) carry
    a value with no unit evidence and an explicit ``NO_UNIT_FIELDS`` marker;
    that is a declaration, not an omission.
    """

    native_field_name: str = Field(min_length=1)
    native_value: Decimal
    native_unit_evidence: SourceUnitEvidence | None = None
    source_unit_contract: SourceUnitContract | None = None

    @model_validator(mode="after")
    def _validate_field_name(self) -> NativeQuantity:
        if not self.native_field_name.strip():
            raise ValueError("native_field_name must not be blank")
        return self

    @model_validator(mode="after")
    def _validate_unit_contract(self) -> NativeQuantity:
        marker = self.source_unit_contract
        if marker is SourceUnitContract.UNIT_EVIDENCE_DECLARED:
            if self.native_unit_evidence is None:
                raise ValueError(
                    "source_unit_contract=UNIT_EVIDENCE_DECLARED requires "
                    "native_unit_evidence"
                )
        elif marker is SourceUnitContract.NO_UNIT_FIELDS:
            if self.native_unit_evidence is not None:
                raise ValueError(
                    "source_unit_contract=NO_UNIT_FIELDS contradicts "
                    "native_unit_evidence being present"
                )
        return self


class T1Quality(NormalizationModelBase):
    """The eight frozen T1 quality dimensions (bloc_05/05 §10; bloc_05/07 §6).

    ``identity_quality``, ``time_quality``, ``semantic_quality``,
    ``unit_quality``, ``lineage_quality``, ``source_integrity_quality``,
    ``coverage_quality``, ``replay_quality``.

    Every dimension is REQUIRED and has no default, because a defaulted quality
    dimension is a claim.  A dimension nobody has determined must be declared
    ``UNKNOWN`` -- the frozen state for "not determined" -- rather than
    silently defaulting to something healthy.

    No aggregate, score or health number is computed here.  Bloc 6 may derive
    operational sensor health from these components later, and bloc_05/07 §6
    forbids it from overwriting them.
    """

    identity_quality: QualityDimensionState
    time_quality: QualityDimensionState
    semantic_quality: QualityDimensionState
    unit_quality: QualityDimensionState
    lineage_quality: QualityDimensionState
    source_integrity_quality: QualityDimensionState
    coverage_quality: QualityDimensionState
    replay_quality: QualityDimensionState


class T1LineageRef(NormalizationModelBase):
    """Base-envelope slice of the T1 lineage chain (bloc_05/05 §2/§3, F25).

    The frozen chain is

        T1 -> T0B raw normalization batch -> AcquisitionRecord -> T0A blob SHA256

    and all three links are REQUIRED and non-empty here, so a canonical row that
    cannot name its projection, its acquisition and its blob cannot be
    constructed at all.  ``identity_evidence_refs``, ``semantic_evidence_refs``
    and ``conversion_lineage_refs`` are empty-by-default slots for evidence that
    does not exist yet (identity B5-I02/I03, semantics B5-I09, conversion
    lineage B5-I16).

    ``code_version`` and ``config_version`` are required (bloc_05/05 §3) so a
    normalized value is never unattributable to the code that produced it.

    Only durable identifiers and digests appear here.  No filesystem path, no
    catalog layout, no DuckDB location, no absolute root (BLOC_04_I17 §12/§13),
    and the reference lists must be duplicate-free so a ref count means
    something.
    """

    raw_projection_refs: tuple[OpaqueIdentifier, ...]
    acquisition_refs: tuple[OpaqueIdentifier, ...]
    evidence_blob_hashes: tuple[str, ...]
    identity_evidence_refs: tuple[OpaqueIdentifier, ...] = ()
    semantic_evidence_refs: tuple[OpaqueIdentifier, ...] = ()
    conversion_lineage_refs: tuple[OpaqueIdentifier, ...] = ()
    code_version: OpaqueIdentifier
    config_version: OpaqueIdentifier

    @model_validator(mode="after")
    def _validate_required_chain(self) -> T1LineageRef:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            if not getattr(self, name):
                raise ValueError(
                    f"{name} must be non-empty (bloc_05/05 §2/F25: every T1 row has "
                    "a complete T0 lineage chain)"
                )
        return self

    @model_validator(mode="after")
    def _validate_unique_refs(self) -> T1LineageRef:
        for name in (
            "raw_projection_refs",
            "acquisition_refs",
            "identity_evidence_refs",
            "semantic_evidence_refs",
            "conversion_lineage_refs",
        ):
            refs = getattr(self, name)
            if len(set(refs)) != len(refs):
                raise ValueError(f"{name} contains duplicate references")
        return self

    @model_validator(mode="after")
    def _validate_blob_hashes(self) -> T1LineageRef:
        for digest in self.evidence_blob_hashes:
            if not _SHA256_HEX_RE.match(digest):
                raise ValueError(
                    f"evidence_blob_hashes member is not a SHA-256 hex digest: {digest!r}"
                )
        if len(set(self.evidence_blob_hashes)) != len(self.evidence_blob_hashes):
            raise ValueError("evidence_blob_hashes contains duplicate digests")
        return self


class T1VersionContext(NormalizationModelBase):
    """Registry and methodology version references (bloc_05/01 §15; 03 §2; 05 §13).

    ``identity_registry_version``, ``contract_terms_version``,
    ``semantic_registry_version``, ``methodology_registry_version``,
    ``time_semantics_version``.

    Every one is Optional, and ``T1BaseEnvelope`` requires the first four on a
    row that claims a canonical status: bloc_05/06 §3 makes
    "methodology/registry versions required where derived fields exist" an N0
    law, and bloc_05/01 §15 requires every T1 row to record the identity
    registry and contract-terms versions.  A row with no canonical claim carries
    none, because there is nothing to attribute.

    Naming a version is not resolving it.  None of these registries exists at
    B5-I01.
    """

    identity_registry_version: RegistryVersion | None = None
    contract_terms_version: RegistryVersion | None = None
    semantic_registry_version: RegistryVersion | None = None
    methodology_registry_version: RegistryVersion | None = None
    time_semantics_version: RegistryVersion | None = None


class T1BaseEnvelope(NormalizationModelBase):
    """Minimum generic T1 observation envelope (bloc_05/03 §2; bloc_5/07 F1-F13).

    This is the base layer only.  It is deliberately named ``T1BaseEnvelope`` and
    NOT the frozen ``T1ObservationEnvelope``: the frozen envelope also carries
    ``economic_contract_id``, ``canonical_asset_id``,
    ``normalization_methodology_id`` / ``_version`` and ``replay_eligibility``,
    which belong to B5-I02, B5-I09 and B5-I06.  Exporting the frozen full name
    now would let a consumer mistake this base layer for the finished contract,
    so the full name stays unexported until the composite is complete.  The
    split is recorded in ``BLOC_05_I01_TYPE_SCOPE_MATRIX.json``.

    What the envelope carries, and why each is unavoidable at this layer:

    * **identity placeholders** -- ``provider``, ``venue`` and
      ``native_instrument`` are separate required fields (bloc_05/01 §13, F1);
      ``provider`` is who supplied the payload and ``venue`` is where the market
      event occurred, so an aggregator reporting Binance venue data stays
      representable and a multi-venue aggregate cannot be assigned a fabricated
      single venue.  ``contract_instance_id`` is an opaque Optional id with NO
      placeholder value: it may be absent only while identity is unresolved,
      blocked or native-only (bloc_05/01 §2.5).
    * **upstream evidence** -- ``source_revision_id`` plus the reused Bloc 4
      ``source_revision_state`` and ``source_coverage_state``; the accepted
      upstream vocabularies are consumed, never re-declared.  A dedicated
      ``provider``/``venue`` split is not duplicated into a single ``source``
      field.
    * **time coordinates** -- ``time`` preserves all nine frozen clocks without
      deriving any of them.
    * **native values** -- ``native_values`` holds :class:`NativeQuantity`
      objects.  No canonical numeric field exists on this model at all, so
      "native was overwritten by normalized" is not a bug to catch later -- it
      is unrepresentable.
    * **failure vocabulary** -- ``normalization_status``, ``missingness_reason``,
      ``quarantine_reason`` / ``quarantine_evidence_refs`` /
      ``quarantine_remediation`` (bloc_05/05 §20).
    * **quality** -- ``quality`` (eight frozen dimensions) and
      ``quality_flags`` in canonical order.
    * **lineage and versions** -- ``lineage_state``, ``lineage``,
      ``versions``, ``normalization_generation``, ``code``/``config`` versions.

    What is intentionally absent: no normalized value, canonical unit, canonical
    asset, notional, USD equivalent, aggregation, dedupe result or replay
    verdict.  Every one of those would require semantics that B5-I02..I19 own.

    Determinism: construction performs no wall-clock read, no hashing and no ID
    generation, and :func:`canonical_json_bytes` serializes two equal envelopes
    to identical bytes.

    Immutability is contractual, not enforced by a second model base: the
    repository's models are validated mutable pydantic objects, and a T1 envelope
    is an evidence record, so it is treated as a value (never edited after
    construction; a change means a new row).
    """

    t1_record_id: T1RecordId | None = None
    sensor_family: SensorFamily
    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    source_granularity: Granularity | None = None
    native_event_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None
    contract_instance_id: ContractInstanceId | None = None
    normalization_generation: T1GenerationId
    source_revision_id: OpaqueIdentifier
    supersedes_t1_record_id: T1RecordId | None = None
    source_revision_state: RevisionState
    source_coverage_state: CoverageState
    time: ObservationTimeEnvelope
    native_values: tuple[NativeQuantity, ...]
    normalization_status: NormalizationStatus
    missingness_reason: MissingnessReason | None = None
    lineage_state: LineageState
    lineage: T1LineageRef
    quality: T1Quality
    quality_flags: tuple[NormalizationQualityFlag, ...] = ()
    versions: T1VersionContext
    quarantine_reason: QuarantineReason | None = None
    quarantine_evidence_refs: tuple[OpaqueIdentifier, ...] = ()
    quarantine_remediation: str | None = Field(default=None, min_length=1)

    # -- helpers ----------------------------------------------------------

    @property
    def _claims_canonical_status(self) -> bool:
        return self.normalization_status in (
            NormalizationStatus.NORMALIZED,
            NormalizationStatus.PARTIALLY_NORMALIZED,
        )

    # -- validation -------------------------------------------------------

    @model_validator(mode="after")
    def _validate_quality_flag_order(self) -> T1BaseEnvelope:
        """Require canonical, duplicate-free flag ordering.

        Canonical serialization can only be deterministic if the flag sequence is
        itself canonical.  Silently sorting would mutate caller data, so a
        non-canonical order is refused and the caller is told the exact order.
        """
        expected = tuple(sorted(self.quality_flags, key=_FLAG_ORDER.__getitem__))
        if len(set(self.quality_flags)) != len(self.quality_flags):
            raise ValueError("quality_flags contains duplicate flags")
        if self.quality_flags != expected:
            raise ValueError(
                "quality_flags must be in canonical NormalizationQualityFlag "
                f"declaration order; expected {tuple(f.value for f in expected)}, "
                f"got {tuple(f.value for f in self.quality_flags)}"
            )
        return self

    @model_validator(mode="after")
    def _validate_lineage_state_and_flag_agree(self) -> T1BaseEnvelope:
        """The lineage state and the matching lineage flag must agree.

        bloc_05/05 §11 carries the lineage completeness as a flag; the base layer
        also needs it as a state.  Two spellings of one fact drift, so exactly
        the matching flag must be present and no other lineage flag may be.
        """
        state_flag = NormalizationQualityFlag(self.lineage_state.value)
        lineage_flags = {
            NormalizationQualityFlag.LINEAGE_COMPLETE,
            NormalizationQualityFlag.LINEAGE_PARTIAL,
            NormalizationQualityFlag.LINEAGE_BROKEN,
        }
        present = lineage_flags & set(self.quality_flags)
        if present != {state_flag}:
            raise ValueError(
                f"lineage_state={self.lineage_state.value} requires exactly the "
                f"{state_flag.value} quality flag; got "
                f"{sorted(f.value for f in present)}"
            )
        return self

    @model_validator(mode="after")
    def _validate_identity_law(self) -> T1BaseEnvelope:
        """F3: every economically normalized row resolves to a contract instance.

        One-way, so it cannot over-validate resolver behavior: a canonical claim
        REQUIRES ``contract_instance_id``.  Absence is legal while the status is
        native-only, blocked or quarantined -- and there is no placeholder value
        standing in for the absent one.
        """
        if self._claims_canonical_status and self.contract_instance_id is None:
            raise ValueError(
                f"normalization_status={self.normalization_status.value} requires "
                "contract_instance_id (bloc_05/01 §2.5, bloc_05/07 F3)"
            )
        return self

    @model_validator(mode="after")
    def _validate_typed_missingness(self) -> T1BaseEnvelope:
        """Absence is typed, never a bool and never a zero (bloc_05/05 §12).

        * a blocked status must carry its own blocked cause, so
          ``BLOCKED_IDENTITY`` cannot be filed under a generic gap;
        * a quarantined row's cause is quarantine;
        * a ``NORMALIZED`` row is not missing anything at the row level.
        """
        status = self.normalization_status
        if status in BLOCKED_STATUS_MISSINGNESS_REASON:
            required = BLOCKED_STATUS_MISSINGNESS_REASON[status]
            if self.missingness_reason is None:
                raise ValueError(
                    f"normalization_status={status.value} requires "
                    f"missingness_reason={required.value} (bloc_05/05 §12)"
                )
            if self.missingness_reason is not required:
                raise ValueError(
                    f"normalization_status={status.value} requires "
                    f"missingness_reason={required.value}, got "
                    f"{self.missingness_reason.value}"
                )
        elif status is NormalizationStatus.QUARANTINED:
            if self.missingness_reason is not MissingnessReason.QUARANTINED:
                raise ValueError(
                    "normalization_status=QUARANTINED requires "
                    "missingness_reason=QUARANTINED"
                )
        elif status is NormalizationStatus.NORMALIZED:
            if self.missingness_reason is not None:
                raise ValueError(
                    "normalization_status=NORMALIZED must not carry "
                    f"missingness_reason={self.missingness_reason.value}"
                )
        return self

    @model_validator(mode="after")
    def _validate_quarantine_law(self) -> T1BaseEnvelope:
        """Reasoned quarantine, both directions (bloc_05/05 §20).

        ``QUARANTINED`` requires a typed cause, at least one evidence ref and a
        non-blank remediation note, and conversely a quarantined-looking reason
        is refused on a row that is not quarantined -- otherwise quarantine
        metadata could ride along unapplied on a row that entered canonical
        queries.
        """
        if self.normalization_status is NormalizationStatus.QUARANTINED:
            if self.quarantine_reason is None:
                raise ValueError(
                    "normalization_status=QUARANTINED requires a typed "
                    "quarantine_reason (bloc_05/05 §20)"
                )
            if not self.quarantine_evidence_refs:
                raise ValueError(
                    "a quarantined row requires quarantine_evidence_refs "
                    "(bloc_05/05 §20)"
                )
            if self.quarantine_remediation is None or not self.quarantine_remediation.strip():
                raise ValueError(
                    "a quarantined row requires a non-blank "
                    "quarantine_remediation (bloc_05/05 §20)"
                )
        elif (
            self.quarantine_reason is not None
            or self.quarantine_evidence_refs
            or self.quarantine_remediation is not None
        ):
            raise ValueError(
                "quarantine metadata requires normalization_status=QUARANTINED"
            )
        return self

    @model_validator(mode="after")
    def _validate_native_evidence_law(self) -> T1BaseEnvelope:
        """A canonical claim must rest on native evidence (bloc_05/07 F12).

        Blocked and native-only rows may legitimately carry no numeric quantity
        -- funding, basis and positioning families have no unit-bearing field at
        all (BLOC_04_I17 §5) -- so emptiness is only refused for a canonical
        claim.  What is never allowed is a canonical claim with nothing behind
        it.
        """
        if self._claims_canonical_status and not self.native_values:
            raise ValueError(
                f"normalization_status={self.normalization_status.value} requires "
                "at least one native value (bloc_05/07 F12)"
            )
        return self

    @model_validator(mode="after")
    def _validate_version_law(self) -> T1BaseEnvelope:
        """Registry/methodology versions are required where derivation exists.

        bloc_05/06 §3: "methodology/registry versions required where derived
        fields exist"; bloc_05/01 §15: every T1 row records the identity
        registry and contract-terms versions.  At B5-I01 "derived fields" means
        exactly the rows that claim a canonical status.
        """
        if not self._claims_canonical_status:
            return self
        required = (
            "identity_registry_version",
            "contract_terms_version",
            "semantic_registry_version",
            "methodology_registry_version",
        )
        missing = [
            name for name in required if getattr(self.versions, name) is None
        ]
        if missing:
            raise ValueError(
                f"normalization_status={self.normalization_status.value} requires "
                f"{', '.join(missing)} (bloc_05/01 §15, bloc_05/06 §3)"
            )
        return self

    @model_validator(mode="after")
    def _validate_blocking_flags(self) -> T1BaseEnvelope:
        """No canonical claim next to a flag a frozen gate treats as failed.

        ``LINEAGE_BROKEN`` is called out separately because bloc_05/05 §11 states
        it is blocking in its own right, independent of the status the row claims.
        """
        blocking = sorted(
            flag.value for flag in set(self.quality_flags) & BLOCKING_QUALITY_FLAGS
        )
        if blocking and self._claims_canonical_status:
            raise ValueError(
                f"normalization_status={self.normalization_status.value} conflicts "
                f"with blocking quality flags {blocking}"
            )
        if (
            NormalizationQualityFlag.LINEAGE_BROKEN in self.quality_flags
            and self._claims_canonical_status
        ):
            raise ValueError(
                "LINEAGE_BROKEN is blocking (bloc_05/05 §11) and cannot coexist "
                f"with normalization_status={self.normalization_status.value}"
            )
        return self

    @model_validator(mode="after")
    def _validate_quality_dimensions(self) -> T1BaseEnvelope:
        """A VERIFIED dimension must not contradict the envelope around it.

        Each clause is a contradiction the model can prove on its own evidence,
        never a judgement about resolver behavior:

        * ``identity_quality=VERIFIED`` with no contract instance;
        * ``lineage_quality`` acceptable while the lineage chain is broken;
        * ``unit_quality=VERIFIED`` while a conversion-blocking flag is set;
        * ``time_quality=VERIFIED`` with unverified or unknown availability.
        """
        quality = self.quality
        flags = set(self.quality_flags)

        if (
            quality.identity_quality is QualityDimensionState.VERIFIED
            and self.contract_instance_id is None
        ):
            raise ValueError(
                "identity_quality=VERIFIED requires contract_instance_id"
            )

        if (
            self.lineage_state is LineageState.LINEAGE_BROKEN
            and quality.lineage_quality
            in (
                QualityDimensionState.VERIFIED,
                QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
            )
        ):
            raise ValueError(
                f"lineage_state={self.lineage_state.value} contradicts "
                f"lineage_quality={quality.lineage_quality.value}"
            )

        if quality.unit_quality is QualityDimensionState.VERIFIED:
            unit_blockers = sorted(
                flag.value
                for flag in (
                    NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,
                    NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE,
                )
                if flag in flags
            )
            if unit_blockers:
                raise ValueError(
                    "unit_quality=VERIFIED contradicts blocking unit flags "
                    f"{unit_blockers}"
                )

        if quality.time_quality is QualityDimensionState.VERIFIED:
            if (
                NormalizationQualityFlag.TIME_SEMANTICS_UNVERIFIED in flags
                or NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN in flags
            ):
                raise ValueError(
                    "time_quality=VERIFIED contradicts an unverified/unknown "
                    "time flag"
                )
            if self.time.availability_basis in (None, AvailabilityBasis.UNKNOWN):
                raise ValueError(
                    "time_quality=VERIFIED requires a usable availability_basis"
                )

        if (
            quality.semantic_quality is QualityDimensionState.VERIFIED
            and NormalizationQualityFlag.SEMANTICS_UNVERIFIED in flags
        ):
            raise ValueError("semantic_quality=VERIFIED contradicts SEMANTICS_UNVERIFIED")

        return self

    @model_validator(mode="after")
    def _validate_quarantine_refs_unique(self) -> T1BaseEnvelope:
        if len(set(self.quarantine_evidence_refs)) != len(self.quarantine_evidence_refs):
            raise ValueError("quarantine_evidence_refs contains duplicate references")
        return self

    # -- serialization ----------------------------------------------------

    def canonical_json(self) -> bytes:
        """Deterministic canonical bytes for this envelope (see helper)."""
        return canonical_json_bytes(self)

    def as_canonical_dict(self) -> dict[str, Any]:
        """Canonical plain-data view, for evidence records and comparisons."""
        return json.loads(canonical_json_bytes(self))


__all__ = [
    "ContractInstanceId",
    "NativeQuantity",
    "NormalizationModelBase",
    "ObservationTimeEnvelope",
    "OpaqueIdentifier",
    "RegistryVersion",
    "T1BaseEnvelope",
    "T1GenerationId",
    "T1LineageRef",
    "T1Quality",
    "T1RecordId",
    "T1VersionContext",
    "canonical_json_bytes",
]