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
CLAIM_ID = "fixture:claim:measurement"


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
    """Build an engine over fresh Book 2 stores with the named claims current.

    R1: the canonical fixture methodology is registered here, because the
    methodology store is SEPARATED and authority-bearing operations resolve
    methodology identity against it. Registration is still not authority — every
    read re-resolves the cited Book 2 claims and the methodology.
    """

    claim_store, evidence_store, service = build_stores()
    for claim_id in claim_ids or (CLAIM_ID,):
        register_claim(claim_store, evidence_store, claim_id)
    engine = Book6MeasurementEngine(Book6Provenance(claim_store, evidence_store))
    engine.registry.register_methodology(methodology())
    return engine, claim_store, evidence_store, service


def decay_claim(
    service: ClaimService,
    claim_store: ClaimStore,
    claim_id: str,
    new_state: str,
    *,
    at: datetime = T2,
) -> object:
    """Transition a claim through the ACCEPTED Book 2 machinery to a new state.

    Book 6 never mutates epistemic state itself. A claim decays because Book 2's
    ``ClaimStateEngine`` moved it, with triggering evidence, through the
    ratified transition table — and Book 6's job is only to notice that the
    authority it cited is no longer current.
    """

    from crypto_systems_intelligence_atlas.claims import ClaimState
    from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine

    claim = claim_store.require(claim_id)
    return ClaimStateEngine(service).transition(
        claim_id,
        ClaimState(new_state),
        triggering_evidence_refs=claim.evidence_refs,
        transitioned_at=at,
    )


def register_definition(engine, metric: MetricDefinition) -> MetricDefinition:
    """Register a metric definition and the methodology it declares.

    R1: the methodology store is SEPARATED, so registering a definition requires
    its methodology to be registered too. Tests use this helper rather than
    touching ``registry`` directly, which keeps the registration order explicit
    instead of hiding it behind an implicit side effect.
    """

    _ensure_methodology(engine, metric.methodology)
    return engine.registry.register_definition(metric)


def register_measurement(engine, observation: MeasurementObservation):
    """Register a measurement, registering its declared methodology first."""

    _ensure_methodology(
        engine,
        methodology(observation.methodology_ref, observation.methodology_version),
    )
    return engine.registry.register_measurement(observation)


def _ensure_methodology(engine, candidate: MeasurementMethodology) -> None:
    """Register a methodology only if its identity is not already current."""

    if not engine.registry.methodologies.methodology_is_current(candidate.identity):
        engine.registry.register_methodology(candidate)


def build_engine_with_definitions(
    *definitions: MetricDefinition,
    claim_ids: tuple[str, ...] = ("fixture:claim:measurement",),
    methodologies: tuple[MeasurementMethodology, ...] = (),
) -> Book6MeasurementEngine:
    """Build an engine and register metric definitions against live Book 2 claims.

    R1: the methodology store is separated and required, so every methodology a
    definition (or a test) needs is registered here alongside the definition.

    Registration is not authority: every authority-bearing read still re-resolves
    the cited Book 2 claims through the provenance adapter.
    """

    engine, *_ = build_engine(*claim_ids)
    for candidate in methodologies:
        _ensure_methodology(engine, candidate)
    for metric in definitions:
        register_definition(engine, metric)
    return engine


def normalization_methodology(
    *,
    ref: str = "book6-normalization",
    version: str = "1",
    input_methodology_refs: tuple[str, ...] = ("book6-methodology@1",),
) -> MeasurementMethodology:
    """Build the methodology a normalization rule must name.

    R1: a normalization rule's methodology must DECLARE the methodology identity
    of the metric it normalizes, so a rule may not reinterpret inputs it was not
    defined over. The default input is the canonical fixture methodology.
    """

    return MeasurementMethodology(
        methodology_ref=ref,
        version=version,
        formula="normalized = deterministic f(native, declared divisor or base)",
        window_rule="declared window class of the input metric",
        filters=("no-fabricated-absence",),
        denominator_rule="explicit measured denominator observation",
        source_selection="first-party Book 2-backed source",
        identity_rule="native lineage is explicit and immutable",
        input_methodology_refs=input_methodology_refs,
    )


def comparison_methodology(
    corpus_row_id: str,
    *,
    ref: str | None = None,
    version: str = "1",
) -> MeasurementMethodology:
    """Build the methodology a CONDITIONAL corpus row requires.

    R1-D1: the identity must equal the row's ``required_methodology`` EXACTLY and
    the methodology must declare authority for that row, or the comparison is
    refused. Building it from the ratified corpus means a test cannot pass a
    fake name and still expect authorization.
    """

    from crypto_systems_intelligence_atlas.book6_comparability import (
        corpus_row_for,
    )
    from crypto_systems_intelligence_atlas.book6_methodology import (
        parse_methodology_identity,
    )

    left, right = conditional_row_pair(corpus_row_id)
    row = corpus_row_for(left, right)
    assert row.required_methodology is not None
    required_ref, _version = parse_methodology_identity(row.required_methodology)
    return MeasurementMethodology(
        methodology_ref=ref or required_ref,
        version=version,
        formula=f"reconcile {row.left_metric} against {row.right_metric}",
        window_rule="declared window class of the compared metrics",
        filters=("no-cross-window-comparison",),
        denominator_rule="explicit measured denominator or not applicable",
        source_selection="first-party Book 2-backed source",
        identity_rule="subject identity rule declared per metric",
        authorized_corpus_row_ids=(corpus_row_id,),
    )


def conditional_row_pair(row_id: str) -> tuple[str, str]:
    """The (left, right) metric pair a CONDITIONAL corpus row governs."""

    from crypto_systems_intelligence_atlas.book6_comparability import (
        FALSE_COMPARISON_CORPUS,
    )

    row = next(r for r in FALSE_COMPARISON_CORPUS if r.row_id == row_id)
    return row.left_metric, row.right_metric


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


def coverage(
    measurement_id: str, fraction: float, *, sufficiency_rule_ref: str | None = None
) -> CoverageObservation:
    return CoverageObservation(
        measurement_id=measurement_id,
        observed_fraction=fraction,
        basis="synthetic offline population coverage over the intended metric population",
        sufficiency_rule_ref=sufficiency_rule_ref,
        valid_time=T1,
    )


def coverage_rule(
    rule_id: str,
    *,
    scope_metric_id: str = "metric.native",
    required_fraction: float = 0.8,
    version: str = "1",
):
    """Build an UNRATIFIED coverage-sufficiency candidate for synthetic tests."""

    from crypto_systems_intelligence_atlas.book6_definitions import CoverageSufficiencyRule

    return CoverageSufficiencyRule(
        rule_id=rule_id,
        version=version,
        required_fraction=required_fraction,
        scope_metric_id=scope_metric_id,
        rationale="synthetic offline coverage-sufficiency candidate for tests",
    )


def price(
    price_id: str = "price:1",
    *,
    price_class: str = "MARKET_OBSERVATION",
    source_ref: str = "venue:index",
    claim_refs: tuple[str, ...] = (CLAIM_ID,),
    value: float = 100.0,
    observed_at=NOW,
    coverage_fraction: float = 1.0,
):
    """Build a Book 2-backed price observation for valuation fixtures."""

    from crypto_systems_intelligence_atlas.book6_valuation import (
        PriceObservation,
        PriceObservationClass,
    )

    return PriceObservation(
        price_observation_id=price_id,
        price_class=PriceObservationClass(price_class),
        source_ref=source_ref,
        source_claim_refs=claim_refs,
        price=value,
        valid_time=observed_at,
        observed_at=observed_at,
        coverage=coverage_fraction,
    )


def valuation(
    valuation_id: str = "val:1",
    *,
    purpose: str = "PROTOCOL_COLLATERAL_MARK",
    price_observation=None,
    claim_refs: tuple[str, ...] = (CLAIM_ID,),
    native_quantity: float = 5.0,
    numeraire: str = "USD",
    conversion_methodology_ref: str = "book6-methodology@1",
    observed_at=NOW,
    valid_time=NOW,
    staleness_bound_seconds: int = 3600,
):
    """Build a valuation observation over a Book 2-backed price."""

    from crypto_systems_intelligence_atlas.book6_valuation import (
        ValuationObservation,
        ValuationPurpose,
    )

    cited = price_observation or price(claim_refs=claim_refs, observed_at=observed_at)
    return ValuationObservation(
        valuation_id=valuation_id,
        subject_ref="fixture:position",
        native_quantity=native_quantity,
        native_unit="token",
        numeraire=numeraire,
        purpose=ValuationPurpose(purpose),
        price=cited,
        conversion_methodology_ref=conversion_methodology_ref,
        valid_time=valid_time,
        observed_at=observed_at,
        coverage=1.0,
        staleness_bound_seconds=staleness_bound_seconds,
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
    "CLAIM_ID",
    "comparison_methodology",
    "conditional_row_pair",
    "coverage",
    "coverage_rule",
    "decay_claim",
    "definition",
    "make_claim",
    "MEASUREMENT_QUALIFIER",
    "methodology",
    "normalization_methodology",
    "NOW",
    "present_denominator",
    "price",
    "ratio_observation",
    "register_claim",
    "register_definition",
    "register_measurement",
    "SOURCE_ID",
    "T1",
    "T2",
    "valuation",
    "windowed_observation",
    "zero_denominator",
]
