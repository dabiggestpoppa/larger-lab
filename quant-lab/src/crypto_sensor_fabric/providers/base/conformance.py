"""Common provider conformance suite (03 §22, SENSOR-B3-I04/I04R1).

Every future provider adapter (Kraken/Gate/OKX/Deribit) must pass this suite
before it may feed later raw-lake/backfill blocs.  The suite is a set of
independent, offline checks; each returns a `ConformanceResult`.  A failing
check names the exact invariant violated — there is no way for a provider
implementation to silently bypass it.

Checks are grouped:

    Q0 CONTRACT      protocol, capability negotiation, free-only, promotion bounds
    Q1 PARSER        raw preservation, empty-valid, schema drift fail-closed
    Q2 MECHANICS     retry classification (I03), resume determinism

Conformance context (I04R1 Repair 2):

- `FRAMEWORK_TEST` is the explicit internal mode used to exercise the harness.
- `PRODUCTION_CANDIDATE` is the ONLY mode an actual provider adapter may run
  under.  It REQUIRES the I14 promotion bounds; missing promotion evidence
  FAILS CLOSED (never an implicit None-based bypass).

The suite never performs network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ...contracts.access import FreeOnlyPolicy
from ...contracts.enums import SensorFamily
from .access import evaluate_access
from .capabilities import promotion_bound_violations
from .enums import (
    AdapterAuthMode,
    AdapterConformanceMode,
    FetchPurpose,
    PaginationMode,
    QualityFlagAcquisition,
    Retryability,
    SchemaState,
)
from .errors import (
    AccessClassViolation,
    AuthenticationRequired,
    CapabilityUnavailable,
    GeoRestricted,
    HistoricalRangeUnavailable,
    InvalidInstrument,
    ProviderUnavailable,
    RateLimited,
    SchemaDrift,
    TransportFailure,
    UnsupportedGranularity,
)
from .models import (
    FetchBatch,
    FetchRequest,
    ProviderCapabilities,
    RawPayloadEnvelope,
    ResumeToken,
)
from .native import (
    ProviderNativeCapabilityEvidence,
    native_evidence_violations,
)
from .retry import RetryPolicy, classify_retryability, is_retryable
from .schema import assert_no_zero_coercion, assess_schema
from .protocol import MechanicalProviderAdapter, dispatch_fetch


@dataclass(frozen=True)
class ConformanceResult:
    """One conformance check outcome."""

    check_id: str
    passed: bool
    detail: str = ""


@dataclass
class AdapterUnderTest:
    """Everything the conformance suite needs to know about an adapter.

    `registry_policy` is the frozen Bloc 1 `FreeOnlyPolicy` for this provider;
    `auth_mode` the adapter's declared auth class.  `promoted_capabilities`
    are the I14-bounded capabilities from source_promotion_candidates.yaml —
    the suite verifies the adapter never exceeds them.

    `mode` gates promotion-bound strictness (Repair 2): PRODUCTION_CANDIDATE
    requires `promoted_capabilities`; FRAMEWORK_TEST may run without them.
    """

    adapter: MechanicalProviderAdapter
    registry_policy: FreeOnlyPolicy
    auth_mode: AdapterAuthMode = AdapterAuthMode.NO_AUTH
    promoted_capabilities: ProviderCapabilities | None = None
    #: Deterministic offline conformance requests used to exercise the REAL
    #: adapter method-dispatch path (I04R2 Issue 1).  The common suite invokes
    #: the adapter and asserts behavior; it never fabricates the result itself.
    empty_valid_request: FetchRequest | None = None
    #: A request for a sensor the adapter declares UNSUPPORTED — dispatch must
    #: yield a typed CapabilityUnavailable, never []/0/None/EMPTY_VALID.
    unsupported_request: FetchRequest | None = None
    #: A request for a SUPPORTED sensor whose fixture is any normal non-empty
    #: response from the fake provider, used to prove the dispatch path returns
    #: a valid FetchBatch (Issue 2).
    fetch_request: FetchRequest | None = None
    #: Provider-native acquisition mode evidence (SENSOR-B3-I05).  A production
    #: adapter may set an exact `historical_mode` on a supported capability ONLY
    #: when a valid `ProviderNativeCapabilityEvidence` for that sensor is present.
    native_evidence: dict[SensorFamily, ProviderNativeCapabilityEvidence] = field(default_factory=dict)
    #: Fail-closed default: a PRODUCTION_CANDIDATE run (the only allowed mode
    #: for a real adapter) REQUIRES promotion bounds.  FRAMEWORK_TEST must be
    #: chosen explicitly by internal self-tests.
    mode: AdapterConformanceMode = AdapterConformanceMode.PRODUCTION_CANDIDATE


def _run_check(results: list[ConformanceResult], check_id: str, fn: Any) -> None:
    try:
        passed, detail = fn()
    except Exception as exc:  # noqa: BLE001 - suite must not crash silently
        passed, detail = False, f"raised {type(exc).__name__}: {exc}"
    results.append(ConformanceResult(check_id=check_id, passed=bool(passed), detail=detail))


def run_conformance_suite(adapter_under_test: AdapterUnderTest) -> list[ConformanceResult]:
    """Run the full common conformance suite; returns per-check results."""
    results: list[ConformanceResult] = []
    adapter = adapter_under_test.adapter
    caps = adapter.capabilities()

    # ---- Q0 CONTRACT ----------------------------------------------------
    def check_provider_metadata() -> tuple[bool, str]:
        if not adapter.provider_id:
            return False, "provider_id missing"
        return True, f"provider_id={adapter.provider_id}"

    _run_check(results, "q0_provider_metadata", check_provider_metadata)

    def check_registry_entry() -> tuple[bool, str]:
        policy = adapter_under_test.registry_policy
        if policy.access_class.value == "UNVERIFIED":
            return False, "provider registry entry missing (free-only policy unverified)"
        return True, "provider registry entry present"

    _run_check(results, "q0_registry_entry", check_registry_entry)

    def check_capability_sensor_specific() -> tuple[bool, str]:
        if not isinstance(caps, ProviderCapabilities):
            return False, "capabilities() must return ProviderCapabilities"
        return True, f"{len(caps.sensors)} sensor-specific capability entries"

    _run_check(results, "q0_capability_sensor_specific", check_capability_sensor_specific)

    def check_capability_evidence_ref() -> tuple[bool, str]:
        missing = [
            s.value
            for s, c in caps.sensors.items()
            if c.supported and c.probe_evidence_ref is None
        ]
        if missing:
            return False, f"supported sensors missing evidence_ref: {missing}"
        return True, "every supported sensor carries an evidence ref"

    _run_check(results, "q0_capability_evidence_ref", check_capability_evidence_ref)

    def check_free_only_gate() -> tuple[bool, str]:
        decision = evaluate_access(
            adapter.provider_id, adapter_under_test.registry_policy, adapter_under_test.auth_mode
        )
        if not decision.allowed:
            return False, "; ".join(decision.violations)
        return True, "free-only gate passes"

    _run_check(results, "q0_free_only", check_free_only_gate)

    def check_production_promotion_required() -> tuple[bool, str]:
        """Repair 2: a PRODUCTION_CANDIDATE run MUST have promotion evidence."""
        if adapter_under_test.mode is AdapterConformanceMode.PRODUCTION_CANDIDATE:
            if adapter_under_test.promoted_capabilities is None:
                return False, (
                    "PRODUCTION_CANDIDATE conformance requires I14 promotion "
                    "bounds; missing promotion evidence FAILS CLOSED (no "
                    "None-based bypass)"
                )
            return True, "production candidate carries I14 promotion bounds"
        return True, "framework-test mode does not require promotion bounds"

    _run_check(results, "q0_production_promotion_required", check_production_promotion_required)

    def check_promotion_provider_identity() -> tuple[bool, str]:
        """I04R2 Issue 5: the adapter provider identity must equal the bound."""
        promoted = adapter_under_test.promoted_capabilities
        if promoted is None or adapter_under_test.mode is not AdapterConformanceMode.PRODUCTION_CANDIDATE:
            return True, "no promotion provider to compare (framework/absent)"
        if promoted.provider_id != adapter.provider_id:
            return False, (
                f"promotion bound provider {promoted.provider_id!r} != adapter "
                f"{adapter.provider_id!r}"
            )
        return True, f"promotion provider id matches adapter ({adapter.provider_id})"

    _run_check(results, "q0_promotion_provider_identity", check_promotion_provider_identity)

    def check_promotion_bounds() -> tuple[bool, str]:
        promoted = adapter_under_test.promoted_capabilities
        if promoted is None:
            if adapter_under_test.mode is AdapterConformanceMode.PRODUCTION_CANDIDATE:
                return False, "production promotion bounds missing (fail closed)"
            return True, "framework-test mode: no promotion bounds to enforce"
        violations: list[str] = []
        for sensor, declared in caps.sensors.items():
            bound = promoted.capability_for(sensor)
            if not declared.supported:
                continue  # only declared-support capabilities are checked
            native = adapter_under_test.native_evidence.get(sensor)
            violations.extend(
                promotion_bound_violations(
                    declared,
                    bound,
                    native_evidence=native,
                    provider_id=adapter.provider_id,
                )
            )
        if violations:
            return False, "; ".join(violations)
        return True, "adapter capabilities stay within I14 promotion bounds"

    _run_check(results, "q0_promotion_bounds", check_promotion_bounds)

    def check_evidence_ref_resolves() -> tuple[bool, str]:
        """I04R2 Issue 5: the probe evidence ref must RESOLVE to I14 evidence.

        Not just non-None and not just 'basis is a superset' — the primary
        evidence pointer must match the adapter provider + the sensor being
        declared and its evidence_id must be one of that I14 candidate's
        evidence_basis IDs.  A correct evidence_basis with an unrelated
        primary ref must NOT pass.
        """
        promoted = adapter_under_test.promoted_capabilities
        failures: list[str] = []
        for sensor, declared in caps.sensors.items():
            if not declared.supported:
                continue
            ref = declared.probe_evidence_ref
            if ref is None:
                failures.append(f"{sensor.value}: no probe_evidence_ref")
                continue
            if ref.provider_id != adapter.provider_id:
                failures.append(
                    f"{sensor.value}: evidence ref provider {ref.provider_id!r} != "
                    f"adapter {adapter.provider_id!r}"
                )
            if ref.sensor_family != sensor:
                failures.append(
                    f"{sensor.value}: evidence ref sensor {ref.sensor_family} != "
                    f"declared {sensor}"
                )
            if promoted is not None:
                bound = promoted.capability_for(sensor)
                if bound.supported and ref.evidence_id not in bound.evidence_basis:
                    failures.append(
                        f"{sensor.value}: evidence ref id {ref.evidence_id!r} is "
                        "not in the I14 evidence_basis for this sensor"
                    )
        if failures:
            return False, "; ".join(failures)
        return True, "every supported evidence ref resolves to I14 lineage"

    _run_check(results, "q0_evidence_ref_resolves", check_evidence_ref_resolves)

    def check_native_mode_evidence() -> tuple[bool, str]:
        """I05 seam: an exact native historical_mode is allowed ONLY when a
        valid ProviderNativeCapabilityEvidence grants it from Bloc 2 evidence.

        - every provided evidence object must be valid against the I14 bound
        - every supported sensor that declares a concrete `historical_mode`
          must carry a valid evidence grant for that sensor
        - a CURRENT_ONLY / ARCHIVE surface can never be given a foreign
          historical/rest mode
        """
        promoted = adapter_under_test.promoted_capabilities
        evidence_map = adapter_under_test.native_evidence
        failures: list[str] = []

        if promoted is not None:
            for sensor, decl in caps.sensors.items():
                evidence = evidence_map.get(sensor)
                if not decl.supported or decl.historical_mode is None:
                    continue
                if evidence is None:
                    failures.append(
                        f"{sensor.value}: native historical_mode declared "
                        "without a NativeEvidence grant (never infer)"
                    )
                    continue
                # the declared exact mode must MATCH the grant — a grant may
                # refine the bound, but the capability cannot contradict its
                # own evidence (SENSOR-B3-I05 adversarial rule).
                if evidence.historical_mode != decl.historical_mode:
                    failures.append(
                        f"{sensor.value}: declared historical_mode "
                        f"{decl.historical_mode} contradicts evidence grant "
                        f"{evidence.historical_mode}"
                    )
                if evidence.pagination_mode != decl.pagination_mode:
                    failures.append(
                        f"{sensor.value}: declared pagination_mode "
                        f"{decl.pagination_mode} contradicts evidence grant "
                        f"{evidence.pagination_mode}"
                    )
                # production symbol scope must be PROVEN by the grant
                # (SENSOR-B3-I05R1): no probe-only symbols, no second list.
                if decl.symbol_scope:
                    if not evidence.instruments:
                        failures.append(
                            f"{sensor.value}: symbol_scope declared but evidence "
                            "grant proves no instruments"
                        )
                    else:
                        unproven = sorted(
                            set(decl.symbol_scope) - set(evidence.instruments)
                        )
                        if unproven:
                            failures.append(
                                f"{sensor.value}: symbol_scope {unproven} not "
                                "proven by the evidence grant"
                            )
                bound = promoted.capability_for(sensor)
                if not bound.supported:
                    failures.append(
                        f"{sensor.value}: native evidence on an unsupported sensor"
                    )
                    continue
                vio = native_evidence_violations(
                    adapter.provider_id, evidence, bound
                )
                if vio:
                    failures.append(f"{sensor.value}: " + "; ".join(vio))

        # every provided evidence object must itself be valid / attributable
        for sensor, evidence in evidence_map.items():
            if sensor not in caps.sensors or not caps.sensors[sensor].supported:
                failures.append(
                    f"{sensor.value}: native evidence attached to a sensor with "
                    "no supported capability"
                )
                continue
            if promoted is not None:
                bound = promoted.capability_for(sensor)
                vio = native_evidence_violations(
                    adapter.provider_id, evidence, bound
                )
                if vio:
                    failures.append(f"{sensor.value}: " + "; ".join(vio))

        if failures:
            return False, "; ".join(failures)
        return True, "every exact native historical_mode is evidence-backed and I14-bounded"

    _run_check(results, "q0_native_mode_evidence", check_native_mode_evidence)

    # ---- Q1 PARSER / RAW -------------------------------------------------
    def check_raw_payload_preserved() -> tuple[bool, str]:
        from .fingerprint import payload_hash

        body = b'{"rate": "0.0001"}'
        envelope = RawPayloadEnvelope(
            provider_id=adapter.provider_id,
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-conformance",
            raw_body=body,
            content_hash=payload_hash(body),
            schema_state=SchemaState.UNKNOWN_SCHEMA,
            adapter_version="0.0.0-conformance",
        )
        raw = envelope.raw_body
        raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        return envelope.content_hash == payload_hash(raw_bytes), (
            "raw body preserved verbatim (content hash matches payload)"
        )

    _run_check(results, "q1_raw_payload_preserved", check_raw_payload_preserved)

    def check_behavioral_dispatch() -> tuple[bool, str]:
        """I04R2 Issue 2: dispatch via adapter's real fetch method returns a
        valid FetchBatch for a supported sensor (never a silent substitute)."""
        request = adapter_under_test.fetch_request
        if request is None:
            return False, "conformance requires a fetch_request to exercise dispatch"
        batch = dispatch_fetch(adapter, request)
        if not isinstance(batch, FetchBatch):
            return False, f"dispatch returned {type(batch).__name__}, expected FetchBatch"
        if batch.provider_id != adapter.provider_id:
            return False, f"batch provider {batch.provider_id!r} != adapter provider"
        if batch.sensor_family != request.sensor_family:
            return False, "batch sensor family != request sensor family"
        return True, f"dispatch returned a valid {batch.sensor_family.value} FetchBatch"

    _run_check(results, "q0_behavioral_dispatch", check_behavioral_dispatch)

    def check_empty_valid_distinct() -> tuple[bool, str]:
        """I04R2 Issue 1: BEHAVIORAL — SUPPORTED + 0 rows => explicit EMPTY_VALID
        FetchBatch; UNSUPPORTED => typed CapabilityUnavailable (via dispatch).
        Never []/0/None for unsupported."""
        empty_request = adapter_under_test.empty_valid_request
        if empty_request is None:
            return False, "conformance requires an empty_valid_request"
        batch = dispatch_fetch(adapter, empty_request)
        if not isinstance(batch, FetchBatch):
            return False, f"supported-empty dispatch returned {type(batch).__name__}"
        if batch.row_count != 0:
            return False, "EMPTY_VALID batch must have zero rows"
        if QualityFlagAcquisition.EMPTY_VALID not in batch.quality_flags:
            return False, "EMPTY_VALID requires the explicit quality flag"

        unsupported_request = adapter_under_test.unsupported_request
        if unsupported_request is None:
            return False, "conformance requires an unsupported_request"
        try:
            dispatch_fetch(adapter, unsupported_request)
        except CapabilityUnavailable:
            pass
        else:
            return False, (
                "unsupported sensor returned a batch (must raise typed "
                "CapabilityUnavailable, never []/0/None/EMPTY_VALID)"
            )
        return True, (
            "supported + 0 rows = explicit EMPTY_VALID; unsupported = typed "
            "CapabilityUnavailable (via real dispatch; never []/0/None)"
        )

    _run_check(results, "q1_empty_valid_distinct", check_empty_valid_distinct)

    def check_schema_drift_fail_closed() -> tuple[bool, str]:
        """Repair 6: KNOWN -> parse; ADDITIVE -> explicit state; BREAKING and
        UNKNOWN -> raw preserved, semantic output blocked; no zero coercion."""
        expected = {"timestamp", "rate"}
        known = assess_schema(expected, {"timestamp", "rate"}, semantics_known=True)
        additive = assess_schema(expected, {"timestamp", "rate", "extra"}, semantics_known=True)
        breaking = assess_schema(expected, {"timestamp"}, semantics_known=True)
        unknown = assess_schema(set(), {"timestamp"}, semantics_known=False)

        if known.state is not SchemaState.KNOWN_SCHEMA or not known.semantic_output_allowed:
            return False, "KNOWN schema must allow parsed output"
        if (
            additive.state is not SchemaState.ADDITIVE_SCHEMA_CHANGE
            or not additive.semantic_output_allowed
        ):
            return False, "ADDITIVE schema must be an explicit permissive state"
        if breaking.state is not SchemaState.BREAKING_SCHEMA_CHANGE:
            return False, "missing required key must be BREAKING"
        if not breaking.raw_preserved or breaking.semantic_output_allowed:
            return False, "BREAKING must preserve raw and block parsed output"
        if unknown.state is not SchemaState.UNKNOWN_SCHEMA or unknown.semantic_output_allowed:
            return False, "UNKNOWN must block parsed output"
        # no zero coercion
        try:
            assert_no_zero_coercion(breaking, {"timestamp": 1}, "rate")
            return False, "missing field was silently coerce-defaulted (must raise)"
        except KeyError:
            pass
        return True, (
            "schema drift fail-closed proven: KNOWN parses, ADDITIVE flags, "
            "BREAKING/UNKNOWN block with raw preserved, no zero coercion"
        )

    _run_check(results, "q1_schema_drift_fail_closed", check_schema_drift_fail_closed)

    # ---- Q2 MECHANICS -----------------------------------------------------
    def check_retry_classification() -> tuple[bool, str]:
        """Repair 7: real I03 classifier — transient retryable, geo/access/
        payment/auth/instrument/history/schema terminal, bounded budget."""
        cases = {
            "timeout": (TransportFailure("P", SensorFamily.MECHANICAL_TRADE), Retryability.RETRYABLE),
            "rate_limited": (RateLimited("P", SensorFamily.MECHANICAL_TRADE), Retryability.RETRYABLE),
            "provider_unavailable": (ProviderUnavailable("P", SensorFamily.MECHANICAL_TRADE), Retryability.RETRYABLE),
            "geo": (GeoRestricted("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
            "access": (AccessClassViolation("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
            "auth": (AuthenticationRequired("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
            "instrument": (InvalidInstrument("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
            "history": (HistoricalRangeUnavailable("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
            "schema": (SchemaDrift("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
            "granularity": (UnsupportedGranularity("P", SensorFamily.MECHANICAL_TRADE), Retryability.TERMINAL),
        }
        for name, (error, expected) in cases.items():
            got = classify_retryability(error)
            if got is not expected:
                return False, f"{name}: expected {expected}, got {got}"
        # no retry of geo/access/payment/auth and machine-semantic failures
        # even when retries remain in the budget
        policy = RetryPolicy(max_attempts=5)
        terminal_never_retried = {
            "geo": GeoRestricted,
            "access_or_payment": AccessClassViolation,
            "auth": AuthenticationRequired,
            "instrument": InvalidInstrument,
            "history": HistoricalRangeUnavailable,
            "schema": SchemaDrift,
            "granularity": UnsupportedGranularity,
        }
        for name, cls in terminal_never_retried.items():
            err = cls("P", SensorFamily.MECHANICAL_TRADE)
            if is_retryable(err, policy):
                return False, f"{name} was retried as transient (must be terminal)"
        # bounded retry budget
        policy = RetryPolicy(max_attempts=3)
        if policy.should_retry(3):
            return False, "retry budget not bounded"
        if policy.should_retry(0) is False:
            return False, "budget too small for a retry"
        return True, (
            "I03 retry classifier verified: timeout/429/5xx retryable; "
            "geo/access/payment/auth/instrument/history/schema terminal and "
            "never retried; bounded budget"
        )

    _run_check(results, "q2_retry_classification", check_retry_classification)

    def check_resume_deterministic() -> tuple[bool, str]:
        token = ResumeToken(mode=PaginationMode.CURSOR, provider_cursor="c1")
        rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
        if rebuilt != token:
            return False, "resume token not round-trip deterministic"
        return True, "resume token deterministic round-trip"

    _run_check(results, "q2_resume_deterministic", check_resume_deterministic)

    def check_native_instrument_required() -> tuple[bool, str]:
        try:
            FetchRequest(
                provider_id=adapter.provider_id,
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument_id="",
                start_time=datetime(2026, 1, 1, tzinfo=UTC),
                end_time=datetime(2026, 1, 1, hour=1, tzinfo=UTC),
                request_id="r",
                purpose=FetchPurpose.PROBE,
                adapter_semantic_version="0.0.0",
            )
        except Exception:
            return True, "native instrument required (empty id rejected)"
        return False, "native instrument id may be empty"

    _run_check(results, "q2_native_instrument_required", check_native_instrument_required)

    return results


NOW_FIXTURE = datetime(2026, 1, 1, tzinfo=UTC)


def summarize_conformance(results: list[ConformanceResult]) -> dict[str, Any]:
    """Compact summary for evidence output."""
    failed = [r for r in results if not r.passed]
    return {
        "checks": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "failed_checks": [
            {"check_id": r.check_id, "detail": r.detail} for r in failed
        ],
    }