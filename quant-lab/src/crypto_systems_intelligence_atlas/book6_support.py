"""Shared deterministic fixtures for Book 6 offline tests.

Mirrors the accepted Book 5 fixture pattern: a registered offline source,
captured evidence, and OBSERVED Book 2 claims, so every canonical Book 6 record
resolves through the real Book 2 engines rather than a stub. Everything is
synthetic and in-memory — no network, no RPC, no database.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from crypto_systems_intelligence_atlas.book6_core import Book6MeasurementEngine
from crypto_systems_intelligence_atlas.book6_definitions import (
    AggregationSemantics,
    ComparabilityClass,
    CoverageObservation,
    DenominatorRule,
    MeasurementMethodology,
    MetricDefinition,
    SourceFamily,
)
from crypto_systems_intelligence_atlas.book6_grammar import (
    ArchitectureFamily,
    MeasurementCategory,
    MeasurementRole,
    MissingnessState,
    ObservationStatus,
    QualityFlag,
    RestatementReason,
    SubjectDomain,
    WindowClass,
)
from crypto_systems_intelligence_atlas.book6_provenance import Book6Provenance
from crypto_systems_intelligence_atlas.book6_records import (
    DenominatorRef,
    MeasurementObservation,
)
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    ClaimStore,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.types import (
    AuthoritySeed,
    AuthorityTier,
    ClaimFamily,
    SourceClass,
)

NOW = datetime(2026, 9, 30, 12, tzinfo=UTC)
T1 = NOW
T2 = NOW + timedelta(days=1)
SOURCE_ID = "csia:source:book6-offline"
MEASUREMENT_QUALIFIER = "MEASUREMENT_INPUT"


def source_fixture() -> Source:
    return Source(
        source_id=SOURCE_ID,
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="deterministic offline Book 6 fixture",
        object_scope=(),
        locator=LocatorMetadata(
            base_locator="fixture://book6",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW,
                policy_version="book6-fixture-v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("book6-source-verification",),
        last_verified_at=NOW,
    )


def build_stores() -> tuple[ClaimStore, EvidenceStore, ClaimService]:
    """Build the accepted Book 2 stores with one registered offline source."""

    registry = SourceRegistry()
    registry.register(source_fixture())
    evidence_store = EvidenceStore(registry)
    claim_store = ClaimStore()
    service = ClaimService(evidence_store=evidence_store, claim_store=claim_store)
    return claim_store, evidence_store, service


def capture_evidence(evidence_store: EvidenceStore, tag: str) -> str:
    return evidence_store.capture(
        source_id=SOURCE_ID,
        retrieved_at=NOW,
        content=f"book6 offline evidence {tag}".encode(),
        content_locator=f"fixture://book6/{tag}",
        raw_snapshot_ref=f"snapshot://book6/{tag}",
        extractor_version="book6-fixture-1",
        parser_version="book6-fixture-1",
        evidence_tier=EvidenceTier.DEPLOYED_STATE,
    ).evidence_id


def make_claim(
    claim_id: str,
    *,
    evidence_ref: str,
    state: ClaimState | None = None,
    qualifier: str = MEASUREMENT_QUALIFIER,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        evidence_refs=(evidence_ref,),
        source_refs=(SOURCE_ID,),
        proposition=Proposition(
            subject_refs=(f"fixture:subject:{claim_id}",),
            predicate="has_measured_state",
            object_ref=claim_id,
            qualifier=qualifier,
        ),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=state if state is not None else ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="book6-offline-fixture",
            version="1",
            description="deterministic offline Book 6 fixture claim",
        ),
    )


def register_claim(
    claim_store: ClaimStore,
    evidence_store: EvidenceStore,
    claim_id: str,
    *,
    state: ClaimState | None = None,
) -> Claim:
    """Register a current, evidenced Book 2 claim (the only Book 6 authority)."""

    evidence_ref = capture_evidence(evidence_store, claim_id)
    return claim_store.add_initial(make_claim(claim_id, evidence_ref=evidence_ref, state=state))


def build_engine(
    *claim_ids: str,
) -> tuple[Book6MeasurementEngine, ClaimStore, EvidenceStore, ClaimService]:
    """Build an engine over fresh Book 2 stores with the named claims current."""

    claim_store, evidence_store, service = build_stores()
    for claim_id in claim_ids or ("fixture:claim:measurement",):
        register_claim(claim_store, evidence_store, claim_id)
    engine = Book6MeasurementEngine(Book6Provenance(claim_store, evidence_store))
    return engine, claim_store, evidence_store, service


def build_engine_with_definitions(
    *definitions: MetricDefinition,
    claim_ids: tuple[str, ...] = ("fixture:claim:measurement",),
) -> Book6MeasurementEngine:
    """Build an engine and register metric definitions against live Book 2 claims.

    Registration is not authority: every authority-bearing read still re-resolves
    the cited Book 2 claims through the provenance adapter.
    """

    engine, *_ = build_engine(*claim_ids)
    for metric in definitions:
        engine.registry.register_definition(metric)
    return engine


def methodology(ref: str = "book6-methodology", version: str = "1") -> MeasurementMethodology:
    return MeasurementMethodology(
        methodology_ref=ref,
        version=version,
        formula="value = f(declared inputs)",
        window_rule="declared window class of the metric",
        filters=("no-fabricated-absence",),
        denominator_rule="explicit measured denominator or not applicable",
        source_selection="first-party Book 2-backed source",
        identity_rule="subject identity rule declared per metric",
    )


def definition(
    metric_id: str,
    *,
    category: MeasurementCategory = MeasurementCategory.STOCK,
    unit: str = "native-unit",
    subject_domain: SubjectDomain = SubjectDomain.CHAIN,
    role: MeasurementRole = MeasurementRole.NATIVE,
    window_class: WindowClass = WindowClass.INSTANTANEOUS,
    denominator_rule: DenominatorRule = DenominatorRule.NOT_APPLICABLE,
    comparability_class: ComparabilityClass = ComparabilityClass.CHAIN_WITHIN_FAMILY,
    applies_to: tuple[str, ...] = (),
    source_families: tuple[SourceFamily, ...] = (SourceFamily.NATIVE_CHAIN,),
) -> MetricDefinition:
    return MetricDefinition(
        metric_id=metric_id,
        name=metric_id,
        semantic_definition=(
            f"a fully specified offline measurement definition for {metric_id}, "
            f"declaring unit, window, method, denominator rule and applicability"
        ),
        subject_domain=subject_domain,
        category=category,
        unit=unit,
        role=role,
        window_class=window_class,
        aggregation=AggregationSemantics.NONE,
        denominator_rule=denominator_rule,
        allowed_source_families=source_families,
        required_evidence_semantics="Book 2 evidenced and currently promotable",
        methodology=methodology(),
        comparability_class=comparability_class,
        applies_to_architectures=applies_to,
    )


def windowed_observation(
    measurement_id: str,
    metric_ref: str,
    *,
    value: float | None,
    missingness: MissingnessState,
    claim_refs: tuple[str, ...] = (),
    unit: str | None = "native-unit",
    category: MeasurementCategory = MeasurementCategory.STOCK,
    window_class: WindowClass = WindowClass.INSTANTANEOUS,
    architecture_family: str | None = ArchitectureFamily.POS.value,
    denominator: DenominatorRef | None = None,
    supersedes: str | None = None,
    restatement_reason: RestatementReason | None = None,
    status: ObservationStatus = ObservationStatus.OBSERVED,
    methodology_ref: str = "book6-methodology",
    methodology_version: str = "1",
    valid_time: datetime = T1,
) -> MeasurementObservation:
    """Build an observation carrying the ratified field set."""

    interval = window_class is not WindowClass.INSTANTANEOUS
    return MeasurementObservation(
        measurement_id=measurement_id,
        subject_ref="fixture:chain:alpha",
        metric_definition_ref=metric_ref,
        category=category,
        missingness_state=missingness,
        value=value,
        unit=unit,
        denominator=denominator,
        valid_time=valid_time,
        observed_at=valid_time,
        window_class=window_class,
        window_start=valid_time if interval else None,
        window_end=valid_time + timedelta(days=1) if interval else None,
        methodology_ref=methodology_ref,
        methodology_version=methodology_version,
        source_claim_refs=claim_refs,
        quality_flags=(QualityFlag.SYNTHETIC_FIXTURE,),
        native_scope="fixture:architecture:pos",
        architecture_family=architecture_family,
        status=status,
        supersedes_measurement_id=supersedes,
        restatement_reason=restatement_reason,
    )


def ratio_observation(
    measurement_id: str,
    metric_ref: str,
    *,
    value: float | None,
    denominator: DenominatorRef | None,
    claim_refs: tuple[str, ...] = (),
) -> MeasurementObservation:
    """Build a ratio observation, which must carry a denominator."""

    return windowed_observation(
        measurement_id,
        metric_ref,
        value=value,
        missingness=(
            MissingnessState.OBSERVED if value is not None else MissingnessState.NOT_COLLECTED
        ),
        claim_refs=claim_refs,
        unit="ratio",
        category=MeasurementCategory.RATIO,
        denominator=denominator,
    )


def coverage(measurement_id: str, fraction: float) -> CoverageObservation:
    return CoverageObservation(
        measurement_id=measurement_id,
        observed_fraction=fraction,
        basis="synthetic offline population coverage over the intended metric population",
        valid_time=T1,
    )


def present_denominator(identity: str = "den:supply") -> DenominatorRef:
    return DenominatorRef(
        denominator_measurement_id=f"obs:{identity}",
        denominator_identity=identity,
        state="PRESENT",
        value=4.0,
    )


def zero_denominator(identity: str = "den:zero") -> DenominatorRef:
    return DenominatorRef(
        denominator_measurement_id=f"obs:{identity}",
        denominator_identity=identity,
        state="ZERO",
        value=0.0,
    )


def absent_denominator(state: str = "UNKNOWN", identity: str = "den:absent") -> DenominatorRef:
    return DenominatorRef(
        denominator_measurement_id=f"obs:{identity}",
        denominator_identity=identity,
        state=state,
    )


__all__ = [
    "absent_denominator",
    "build_engine",
    "build_engine_with_definitions",
    "build_stores",
    "capture_evidence",
    "coverage",
    "definition",
    "make_claim",
    "MEASUREMENT_QUALIFIER",
    "methodology",
    "NOW",
    "present_denominator",
    "ratio_observation",
    "register_claim",
    "SOURCE_ID",
    "T1",
    "T2",
    "windowed_observation",
    "zero_denominator",
]
