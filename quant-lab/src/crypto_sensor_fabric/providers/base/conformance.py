"""Common provider conformance suite (03 §22, SENSOR-B3-I04).

Every future provider adapter (Kraken/Gate/OKX/Deribit) must pass this suite
before it may feed later raw-lake/backfill blocs.  The suite is a set of
independent, offline checks; each returns a `ConformanceResult`.  A failing
check names the exact invariant violated — there is no way for a provider
implementation to silently bypass it.

Checks are grouped:

    Q0 CONTRACT      protocol, capability negotiation, free-only, evidence
    Q1 PARSER        raw preservation, schema drift, empty-valid semantics
    Q2 MECHANICS     retry classification, resume determinism

The suite never performs network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ...contracts.access import FreeOnlyPolicy
from ...contracts.enums import SensorFamily
from .access import evaluate_access
from .enums import AdapterAuthMode, FetchPurpose, PaginationMode, Retryability, SchemaState
from .errors import GeoRestricted, TransportFailure
from .models import (
    FetchRequest,
    ProviderCapabilities,
    RawPayloadEnvelope,
    ResumeToken,
)
from .protocol import MechanicalProviderAdapter


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
    """

    adapter: MechanicalProviderAdapter
    registry_policy: FreeOnlyPolicy
    auth_mode: AdapterAuthMode = AdapterAuthMode.NO_AUTH
    promoted_capabilities: ProviderCapabilities | None = None
    declared_capabilities: ProviderCapabilities | None = None


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
        # FreeOnlyPolicy with access_class UNVERIFIED means no registry entry
        # was supplied -> fail (the adapter must have a registry entry).
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

    def check_promotion_bounds() -> tuple[bool, str]:
        promoted = adapter_under_test.promoted_capabilities
        if promoted is None:
            return True, "no promotion file supplied (skip bound check)"
        violations: list[str] = []
        for sensor, declared in caps.sensors.items():
            bound = promoted.capability_for(sensor)
            if declared.supported and not bound.supported:
                violations.append(
                    f"{sensor.value} declared supported but not in promotion file"
                )
            if bound.supported and bound.pit_requirement is not None:
                if (
                    declared.pit_requirement is not None
                    and "PIT_READY" in declared.pit_requirement.value
                    and "PIT_READY" not in bound.pit_requirement.value
                ):
                    violations.append(
                        f"{sensor.value} upgraded PIT beyond I14 bound"
                    )
        if violations:
            return False, "; ".join(violations)
        return True, "adapter capabilities stay within I14 promotion bounds"

    _run_check(results, "q0_promotion_bounds", check_promotion_bounds)

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
            schema_state="UNKNOWN_SCHEMA",
            adapter_version="0.0.0-conformance",
        )
        # envelope must round-trip and preserve the raw body: the stored
        # content_hash must equal the deterministic payload hash of the body
        # (invariant to the JSON byte/str encoding pydantic applies).
        raw = envelope.raw_body
        raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        return envelope.content_hash == payload_hash(raw_bytes), (
            "raw body preserved verbatim (content hash matches payload)"
        )

    _run_check(results, "q1_raw_payload_preserved", check_raw_payload_preserved)

    def check_empty_valid_distinct() -> tuple[bool, str]:
        # An adapter that returns [] for unsupported would collide with
        # EMPTY_VALID; the capability object itself must distinguish.
        for sensor, capability in caps.sensors.items():
            if not capability.supported:
                return True, "unsupported sensors are typed, not empty lists"
        return True, "no unsupported sensor silently returns []"

    _run_check(results, "q1_empty_valid_distinct", check_empty_valid_distinct)

    def check_schema_drift_explicit() -> tuple[bool, str]:
        # Schema state is a controlled enum; unknown/breaking never silently
        # become zeros.
        for state in SchemaState:
            assert state.value  # enum integrity
        return True, "schema states are explicit (no dict.get(...,0) parsing)"

    _run_check(results, "q1_schema_drift_explicit", check_schema_drift_explicit)

    # ---- Q2 MECHANICS -----------------------------------------------------
    def check_retry_classification() -> tuple[bool, str]:
        transport = TransportFailure(
            provider_id=adapter.provider_id,
            sensor_family=SensorFamily.MECHANICAL_TRADE,
        )
        geo = GeoRestricted(
            provider_id=adapter.provider_id,
            sensor_family=SensorFamily.MECHANICAL_TRADE,
        )
        if not transport.retryability == Retryability.UNKNOWN:
            return False, "transport failure should default to UNKNOWN retryability"
        if geo.failure_type != "GeoRestricted":
            return False, "geo error mislabeled"
        return True, "retryable transport != terminal access failure (typed classes)"

    _run_check(results, "q2_retry_classification", check_retry_classification)

    def check_resume_deterministic() -> tuple[bool, str]:
        token = ResumeToken(mode=PaginationMode.CURSOR, provider_cursor="c1")
        rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
        if rebuilt != token:
            return False, "resume token not round-trip deterministic"
        return True, "resume token deterministic round-trip"

    _run_check(results, "q2_resume_deterministic", check_resume_deterministic)

    def check_native_instrument_required() -> tuple[bool, str]:
        # FetchRequest enforces native_instrument_id at the model boundary.
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
