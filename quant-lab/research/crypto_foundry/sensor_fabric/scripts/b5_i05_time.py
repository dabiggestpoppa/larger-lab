"""SENSOR-B5-I05 deterministic evidence generator (tracked source, Stage H).

Run from quant-lab/:
    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i05_time.py

Writes two artifacts beside the other bloc_05 evidence:
    evidence/bloc_05/bloc_05_time_validation.json
    evidence/bloc_05/BLOC_05_I05_SCOPE_AUDIT.json

Laws (I05 directive section 06, mirroring the I03/I04 producers):

* every row is an EXECUTED probe -- ``observed`` is produced by the real
  production functions, ``expected`` is the literal written from the frozen
  contract (bloc_05/02, bloc_05/06 s13) BEFORE the probe runs, and ``pass`` is
  their equality;
* exact clause references on every row, in the compact ``bloc_05/<doc> s<n>``
  form;
* stable row order (build order, indexed), stable serialization
  (``json.dumps(..., sort_keys=True)``), LF-only bytes written with
  ``write_bytes`` so a Windows rerun cannot introduce CRLF churn;
* no live clock: a pinned ``RUN_DATE`` literal, never a system-date call;
* no untracked runtime dependency: imports are the tracked package, the
  tracked configs (read as text) and the standard library;
* SHA-256 inventory of every tracked input the artifact depends on;
* nonzero exit whenever a mandatory row fails.

Filesystem reads are limited to (a) the tracked source/config/test files named
in its own inventory and (b) ``git`` metadata for the scope rows; the only
write is the two evidence artifacts.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_QUANT_LAB = Path(__file__).resolve().parents[4]
_ROOT = _QUANT_LAB.parent
sys.path.insert(0, str(_QUANT_LAB / "src"))

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.normalization import time as time_package  # noqa: E402
from crypto_sensor_fabric.normalization.enums import (  # noqa: E402
    BLOCKING_QUALITY_FLAGS,
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    NormalizationQualityFlag,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.models import ObservationTimeEnvelope  # noqa: E402
from crypto_sensor_fabric.normalization.time import (  # noqa: E402
    TIMESTAMP_ROLE_FIELD,
    AcquisitionMetadata,
    AvailabilityResolution,
    CanonicalTimestamp,
    IntervalWindow,
    ProviderTimeSemantics,
    ReplayEvidence,
    ReplayEligibility,
    RevisionMode,
    RevisionRecord,
    RevisionStatus,
    UndecidableIntervalBoundary,
    UnassessableReplayEvidence,
    UnknownProviderTimeSemantics,
    UnsupportedRevisionMode,
    assess_replay_eligibility,
    derive_market_available_at,
    earliest_justified_availability_from,
    parse_provider_time_semantics_yaml,
    parse_revision_policies_yaml,
    select_revisions,
    serialize_provider_time_semantics_yaml,
)

UTC = timezone.utc
RUN_DATE = "2026-10-10"
CHECKPOINT = "SENSOR-B5-I05"

GEN_REF = (
    "live run "
    + RUN_DATE
    + ": PYTHONIOENCODING=utf-8 python "
    + "research/crypto_foundry/sensor_fabric/scripts/b5_i05_time.py "
    + "(from quant-lab; time surface under test = "
    + "src/crypto_sensor_fabric/normalization/time/ + "
    + "config/crypto_sensor_fabric/{provider_time_semantics,revision_policies}.yaml)"
)
TESTS = "tests/crypto_sensor_fabric/normalization/test_b5_i05_*.py"
EVIDENCE_DIR = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_05"
)
ARTIFACT = EVIDENCE_DIR / "bloc_05_time_validation.json"
SCOPE_ARTIFACT = EVIDENCE_DIR / "BLOC_05_I05_SCOPE_AUDIT.json"
SEMANTICS_CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_time_semantics.yaml"
REVISION_CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "revision_policies.yaml"
BASE_HEAD = "745b3797bfc3f69a1df4e8bc7171436c98996490"

BAR_START = datetime(2024, 6, 1, hour=12, minute=0, tzinfo=UTC)
BAR_END = datetime(2024, 6, 1, hour=12, minute=5, tzinfo=UTC)
EVENT_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
PUBLISHED = datetime(2024, 6, 1, hour=12, minute=0, second=2, tzinfo=UTC)
INGESTED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=5, tzinfo=UTC)
OBSERVED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=6, tzinfo=UTC)
KNOWN_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
KNOWN_2025 = datetime(2025, 3, 3, hour=10, tzinfo=UTC)
CUTOFF_2022 = EVENT_2022

REAL_PROVIDERS = (
    "KRAKEN_FUTURES",
    "GATE_FUTURES",
    "BINANCE_USDM",
    "BYBIT_LINEAR",
    "OKX_SWAP",
    "DERIBIT",
    "COINALYZE",
    "BITFINEX_COMMUNITY_ARCHIVE",
)

INVENTORY = [
    "quant-lab/src/crypto_sensor_fabric/normalization/time/__init__.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/enums.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/models.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/semantics_registry.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/intervals.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/availability.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/revision_policy.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/time/replay_gate.py",
    "quant-lab/config/crypto_sensor_fabric/provider_time_semantics.yaml",
    "quant-lab/config/crypto_sensor_fabric/revision_policies.yaml",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_time_models.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_semantics_registry.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_availability.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_intervals.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_revision_policy.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_replay_gate.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_frozen_scenarios.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py",
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_evidence.py",
    "quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i05_time.py",
]


# ---------------------------------------------------------------------------
# Row helpers
# ---------------------------------------------------------------------------


def _observed_outcome(action) -> str:
    """REFUSED/ACCEPTED, so a raised refusal is an observation, not a crash."""
    try:
        action()
    except Exception:  # noqa: BLE001 - the exception TYPE is not the claim
        return "REFUSED"
    return "ACCEPTED"


def _exception_name(action) -> str:
    """The exception TYPE raised by an action, for typed-refusal rows."""
    try:
        action()
    except Exception as exc:  # noqa: BLE001 - naming the type is the claim
        return type(exc).__name__
    return "NO_EXCEPTION"


def _row(row_id: str, clause: str, expected, observed) -> dict:
    return {
        "row_id": row_id,
        "clause": clause,
        "expected": expected,
        "observed": observed,
        "pass": bool(expected == observed),
    }


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=_QUANT_LAB,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout


def _semantics(
    *,
    convention: IntervalTimeConvention = IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    contemporaneous_public: bool = False,
    refs: tuple[str, ...] = (),
    family: SensorFamily = SensorFamily.MECHANICAL_OPEN_INTEREST,
    roles: dict | None = None,
) -> ProviderTimeSemantics:
    return ProviderTimeSemantics(
        provider="SYNTHETIC_EXCHANGE_A",
        sensor_family=family,
        timestamp_field_roles=roles
        if roles is not None
        else {time_package.TimestampRole.SOURCE_EVENT_AT: "timestamp"},
        interval_time_convention=convention,
        precision=TimestampPrecision.MILLISECOND,
        contemporaneous_public=contemporaneous_public,
        source_evidence_refs=refs,
    )


def _acquisition(
    *,
    observed_at: datetime | None = None,
    ingested_at: datetime | None = None,
    evidence: tuple[str, ...] = (),
) -> AcquisitionMetadata:
    return AcquisitionMetadata(
        observed_at=observed_at,
        ingested_at=ingested_at,
        contemporaneous_public_evidence_refs=evidence,
    )


def _derive(**kwargs):
    return derive_market_available_at(**kwargs)


def _resolution_signature(resolution: AvailabilityResolution) -> list:
    return [
        resolution.availability_basis.value,
        resolution.market_available_at.isoformat() if resolution.market_available_at else None,
        [flag.value for flag in resolution.quality_flags],
    ]


def _revisions() -> tuple[RevisionRecord, RevisionRecord]:
    original = RevisionRecord(
        source_revision_id="rev-oi-2022-original",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=KNOWN_2022,
        known_to=None,
    )
    correction = RevisionRecord(
        source_revision_id="rev-oi-2022-corrected-2025",
        normalization_generation=2,
        supersedes_t1_record_id="rev-oi-2022-original",
        revision_status=RevisionStatus.PROVIDER_CORRECTED,
        known_from=KNOWN_2025,
        known_to=None,
    )
    return original, correction


def _catalog():
    return parse_revision_policies_yaml(REVISION_CONFIG.read_text(encoding="utf-8"))


def _policy(mode: RevisionMode):
    return _catalog().policy_for(mode)


def _selection(mode: RevisionMode, cutoff: datetime = CUTOFF_2022):
    return select_revisions(_revisions(), _policy(mode), cutoff)


def _evidence(**overrides) -> ReplayEvidence:
    payload = dict(
        identity_pit_resolved=True,
        timestamp_semantics_verified=True,
        source_evidence_refs=("provider-docs:synth-a-public-feed",),
        availability_basis=AvailabilityBasis.PUBLIC_INTERVAL_CLOSE,
        availability_confidence="EVIDENCE_BACKED_DECLARATION",
        market_available_at=BAR_END,
        interval_complete=True,
        revision=_selection(RevisionMode.AS_KNOWN_THEN),
        lineage=LineageState.LINEAGE_COMPLETE,
        quality_flags=(NormalizationQualityFlag.LINEAGE_COMPLETE,),
    )
    payload.update(overrides)
    return ReplayEvidence(**payload)


def _eligibility(**overrides) -> str:
    return assess_replay_eligibility(_evidence(**overrides)).eligibility.value


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------


def _vocabulary_rows() -> list[dict]:
    rows = [
        _row(
            "vocab_timestamp_roles",
            "bloc_05/02 s2",
            [
                "SOURCE_EVENT_AT",
                "INTERVAL_START_AT",
                "INTERVAL_END_AT",
                "EFFECTIVE_AT",
                "PUBLISHED_AT",
                "MARKET_AVAILABLE_AT",
                "OBSERVED_AT",
                "INGESTED_AT",
                "NORMALIZED_AT",
            ],
            [member.value for member in time_package.TimestampRole],
        ),
        _row(
            "vocab_timestamp_role_field_map",
            "bloc_05/02 s2/s3",
            {
                "SOURCE_EVENT_AT": "source_event_at",
                "INTERVAL_START_AT": "interval_start_at",
                "INTERVAL_END_AT": "interval_end_at",
                "EFFECTIVE_AT": "effective_at",
                "PUBLISHED_AT": "published_at",
                "MARKET_AVAILABLE_AT": "market_available_at",
                "OBSERVED_AT": "observed_at",
                "INGESTED_AT": "ingested_at",
                "NORMALIZED_AT": "normalized_at",
            },
            {role.value: field for role, field in TIMESTAMP_ROLE_FIELD.items()},
        ),
        _row(
            "vocab_revision_status",
            "bloc_05/02 s10",
            [
                "ORIGINAL",
                "PROVIDER_CORRECTED",
                "SOURCE_MUTATION_REPARSED",
                "NORMALIZATION_REBUILD",
                "IDENTITY_REBUILD",
                "SEMANTIC_REINTERPRETATION",
            ],
            [member.value for member in RevisionStatus],
        ),
        _row(
            "vocab_revision_mode",
            "bloc_05/02 s11",
            [
                "AS_KNOWN_THEN",
                "LATEST_VERIFIED",
                "FIRST_SEEN",
                "EXACT_REVISION",
                "ALL_REVISIONS",
                "ERROR_ON_AMBIGUITY",
            ],
            [member.value for member in RevisionMode],
        ),
        _row(
            "vocab_replay_eligibility",
            "bloc_05/02 s15",
            [
                "ELIGIBLE",
                "RETROSPECTIVE_ONLY",
                "BLOCKED_TIMESTAMP",
                "BLOCKED_REVISION",
                "BLOCKED_IDENTITY",
                "BLOCKED_LINEAGE",
            ],
            [member.value for member in ReplayEligibility],
        ),
        _row(
            "vocab_i01_enums_reused_not_redeclared",
            "bloc_05/02 s5/s7/s8/s16",
            [],
            [
                name
                for name in (
                    "AvailabilityBasis",
                    "IntervalTimeConvention",
                    "TimestampPrecision",
                    "NormalizationQualityFlag",
                )
                if hasattr(
                    sys.modules[time_package.__name__ + ".enums"], name
                )
            ],
        ),
        _row(
            "vocab_availability_basis_eight",
            "bloc_05/02 s5",
            [
                "REALTIME_PUBLIC_EVENT",
                "REALTIME_PUBLIC_SNAPSHOT",
                "PUBLIC_INTERVAL_CLOSE",
                "DELAYED_PUBLICATION",
                "HISTORICAL_ARCHIVE_RECONSTRUCTION",
                "PROVIDER_DECLARED_PUBLIC_TIME",
                "SYSTEM_ONLY_OBSERVED",
                "UNKNOWN",
            ],
            [member.value for member in AvailabilityBasis],
        ),
        _row(
            "vocab_interval_conventions_four",
            "bloc_05/02 s7",
            [
                "LEFT_CLOSED_RIGHT_OPEN",
                "LEFT_OPEN_RIGHT_CLOSED",
                "PROVIDER_NATIVE_UNKNOWN",
                "POINT_SAMPLE",
            ],
            [member.value for member in IntervalTimeConvention],
        ),
    ]
    return rows


def _timestamp_model_rows() -> list[dict]:
    def naive_refused() -> None:
        CanonicalTimestamp(
            at=datetime(2023, 3, 12, hour=2, minute=30),
            role=time_package.TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.MILLISECOND,
        )

    def second_precision_refused() -> None:
        CanonicalTimestamp(
            at=datetime(2024, 6, 1, hour=12, microsecond=1, tzinfo=UTC),
            role=time_package.TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.SECOND,
        )

    def millisecond_precision_refused() -> None:
        CanonicalTimestamp(
            at=datetime(2024, 6, 1, hour=12, microsecond=123456, tzinfo=UTC),
            role=time_package.TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.MILLISECOND,
        )

    def date_only_refused() -> None:
        CanonicalTimestamp(
            at=datetime(2024, 6, 1, hour=12, tzinfo=UTC),
            role=time_package.TimestampRole.EFFECTIVE_AT,
            precision=TimestampPrecision.DATE_ONLY,
        )

    def methodology_without_skew_refused() -> None:
        CanonicalTimestamp(
            at=datetime(2024, 6, 1, hour=12, tzinfo=UTC),
            role=time_package.TimestampRole.SOURCE_EVENT_AT,
            precision=TimestampPrecision.SECOND,
            clock_skew_methodology_id="SKEW_METHOD_V1",
        )

    raw = datetime(2024, 6, 1, hour=12, tzinfo=UTC)
    skewed = CanonicalTimestamp(
        at=raw,
        role=time_package.TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.SECOND,
        clock_skew_ms=__import__("decimal").Decimal("250"),
    )
    aware = CanonicalTimestamp(
        at=datetime(2023, 7, 1, hour=14, tzinfo=timezone(timedelta(hours=2))),
        role=time_package.TimestampRole.SOURCE_EVENT_AT,
        precision=TimestampPrecision.SECOND,
    )
    immutable = _observed_outcome(
        lambda: setattr(
            CanonicalTimestamp(
                at=raw,
                role=time_package.TimestampRole.SOURCE_EVENT_AT,
                precision=TimestampPrecision.SECOND,
            ),
            "role",
            time_package.TimestampRole.PUBLISHED_AT,
        )
    )
    return [
        _row("model_naive_timestamp_refused", "bloc_05/02 s18 rule 1", "REFUSED", _observed_outcome(naive_refused)),
        _row("model_offset_normalized_to_utc", "bloc_05/02 s8", "2023-07-01T12:00:00+00:00", aware.at.isoformat()),
        _row("model_second_precision_refuses_subsecond", "bloc_05/02 s8", "REFUSED", _observed_outcome(second_precision_refused)),
        _row("model_millisecond_precision_refuses_microsecond", "bloc_05/02 s8", "REFUSED", _observed_outcome(millisecond_precision_refused)),
        _row("model_date_only_requires_midnight", "bloc_05/02 s8", "REFUSED", _observed_outcome(date_only_refused)),
        _row("model_skew_methodology_needs_a_measured_skew", "bloc_05/02 s9", "REFUSED", _observed_outcome(methodology_without_skew_refused)),
        _row("model_skew_never_mutates_the_raw_source_value", "bloc_05/02 s9", raw.isoformat(), skewed.at.isoformat()),
        _row("model_temporal_evidence_is_immutable", "bloc_05/02 s10", "REFUSED", immutable),
    ]


def _registry_rows() -> list[dict]:
    registry = parse_provider_time_semantics_yaml(SEMANTICS_CONFIG.read_text(encoding="utf-8"))
    synthetic = ProviderTimeSemantics(
        provider="SYNTHETIC_EXCHANGE_A",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        timestamp_field_roles={
            time_package.TimestampRole.SOURCE_EVENT_AT: "timestamp",
            time_package.TimestampRole.INTERVAL_END_AT: "end",
        },
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        precision=TimestampPrecision.MILLISECOND,
        contemporaneous_public=True,
        source_evidence_refs=("provider-docs:synthetic-a-public-feed",),
    )
    synthetic_registry = time_package.ProviderTimeSemanticsRegistry(
        schema_version="1.0", semantics=(synthetic,)
    )
    roundtrip = serialize_provider_time_semantics_yaml(synthetic_registry)
    roundtrip_stable = (
        roundtrip
        == serialize_provider_time_semantics_yaml(
            parse_provider_time_semantics_yaml(roundtrip)
        )
    )

    def duplicate_refused() -> None:
        parse_provider_time_semantics_yaml(
            SEMANTICS_CONFIG.read_text(encoding="utf-8").replace(
                "semantics: []",
                "semantics:\n"
                "  - provider: SYNTHETIC_EXCHANGE_A\n"
                "    sensor_family: MECHANICAL_TRADE\n"
                "    timestamp_field_roles: {}\n"
                "    interval_time_convention: POINT_SAMPLE\n"
                "    precision: MICROSECOND\n"
                "    contemporaneous_public: false\n"
                "    source_evidence_refs: []\n"
                "  - provider: SYNTHETIC_EXCHANGE_A\n"
                "    sensor_family: MECHANICAL_TRADE\n"
                "    timestamp_field_roles: {}\n"
                "    interval_time_convention: POINT_SAMPLE\n"
                "    precision: MICROSECOND\n"
                "    contemporaneous_public: false\n"
                "    source_evidence_refs: []\n",
            )
        )

    def unclassified_claim_refused() -> None:
        ProviderTimeSemantics(
            provider="SYNTHETIC_EXCHANGE_A",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            timestamp_field_roles={},
            interval_time_convention=IntervalTimeConvention.POINT_SAMPLE,
            precision=TimestampPrecision.MILLISECOND,
            contemporaneous_public=True,
            source_evidence_refs=(),
        )

    def unknown_provider_exception() -> str:
        try:
            registry.require("KRAKEN_FUTURES", SensorFamily.MECHANICAL_TRADE)
        except UnknownProviderTimeSemantics:
            return "UnknownProviderTimeSemantics"
        return "NO_EXCEPTION"

    return [
        _row(
            "registry_config_present_and_schema_versioned",
            "bloc_05/02 s17",
            "1.0",
            registry.schema_version,
        ),
        _row(
            "registry_carries_zero_real_exchange_rows",
            "bloc_05/02 s18 rule 7",
            0,
            len(registry.semantics),
        ),
        _row(
            "registry_every_real_provider_fails_closed",
            "bloc_05/02 s18 rule 7",
            {provider: "REFUSED" for provider in REAL_PROVIDERS},
            {
                provider: _observed_outcome(
                    lambda provider=provider: registry.require(
                        provider, SensorFamily.MECHANICAL_TRADE
                    )
                )
                for provider in REAL_PROVIDERS
            },
        ),
        _row(
            "registry_synthetic_row_resolves_all_declared_semantics",
            "bloc_05/02 s7/s8",
            ["timestamp", "end", "LEFT_CLOSED_RIGHT_OPEN", "MILLISECOND", True],
            [
                synthetic_registry.require_role(
                    "SYNTHETIC_EXCHANGE_A",
                    SensorFamily.MECHANICAL_OPEN_INTEREST,
                    time_package.TimestampRole.SOURCE_EVENT_AT,
                ),
                synthetic_registry.require_role(
                    "SYNTHETIC_EXCHANGE_A",
                    SensorFamily.MECHANICAL_OPEN_INTEREST,
                    time_package.TimestampRole.INTERVAL_END_AT,
                ),
                synthetic.interval_time_convention.value,
                synthetic.precision.value,
                synthetic.contemporaneous_public,
            ],
        ),
        _row(
            "registry_unmapped_role_fails_closed",
            "bloc_05/02 s7",
            "REFUSED",
            _observed_outcome(
                lambda: synthetic_registry.require_role(
                    "SYNTHETIC_EXCHANGE_A",
                    SensorFamily.MECHANICAL_OPEN_INTEREST,
                    time_package.TimestampRole.EFFECTIVE_AT,
                )
            ),
        ),
        _row(
            "registry_unknown_provider_returns_no_default",
            "bloc_05/02 s18 rule 7",
            "REFUSED",
            _observed_outcome(
                lambda: registry.require(
                    "SYNTHETIC_EXCHANGE_B", SensorFamily.MECHANICAL_TRADE
                )
            ),
        ),
        _row(
            "registry_duplicate_provider_family_row_refused",
            "bloc_05/02 s17",
            "REFUSED",
            _observed_outcome(duplicate_refused),
        ),
        _row(
            "registry_contemporaneous_public_requires_evidence",
            "bloc_05/02 s6",
            "REFUSED",
            _observed_outcome(unclassified_claim_refused),
        ),
        _row(
            "registry_serialization_is_byte_stable",
            "bloc_05/02 s17",
            True,
            roundtrip_stable,
        ),
        _row(
            "registry_unknown_provider_exception_type",
            "bloc_05/02 s18 rule 7",
            "UnknownProviderTimeSemantics",
            unknown_provider_exception(),
        ),
    ]


def _interval_rows() -> list[dict]:
    def window(convention, closed=True, end=BAR_END) -> IntervalWindow:
        return IntervalWindow(
            interval_start_at=BAR_START,
            interval_end_at=end,
            interval_closed=closed,
            interval_time_convention=convention,
        )

    probes = [
        BAR_START - timedelta(microseconds=1),
        BAR_START,
        BAR_END - timedelta(microseconds=1),
        BAR_END,
        BAR_END + timedelta(microseconds=1),
    ]

    def membership(convention) -> list[bool]:
        return [window(convention).contains(point) for point in probes]

    def undecidable() -> str:
        try:
            window(IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN).contains(BAR_START)
        except UndecidableIntervalBoundary:
            return "REFUSED"
        return "ACCEPTED"

    def unclosed() -> str:
        try:
            window(IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN, closed=False).earliest_justified_availability()
        except Exception:
            return "REFUSED"
        return "ACCEPTED"

    envelope = ObservationTimeEnvelope(
        interval_start_at=BAR_START,
        interval_end_at=BAR_END,
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        ingested_at=INGESTED_2026,
    )
    before = json.dumps(envelope.model_dump(), sort_keys=True, default=str)
    envelope_answer = earliest_justified_availability_from(envelope)
    after = json.dumps(envelope.model_dump(), sort_keys=True, default=str)

    return [
        _row(
            "interval_left_closed_right_open_edges",
            "bloc_05/02 s7",
            [False, True, True, False, False],
            membership(IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN),
        ),
        _row(
            "interval_left_open_right_closed_edges",
            "bloc_05/02 s7",
            [False, False, True, True, False],
            membership(IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED),
        ),
        _row(
            "interval_point_sample_is_a_single_instant",
            "bloc_05/02 s7",
            [False, True, False, False, False],
            [
                IntervalWindow(
                    interval_start_at=BAR_START,
                    interval_end_at=BAR_START,
                    interval_closed=True,
                    interval_time_convention=IntervalTimeConvention.POINT_SAMPLE,
                ).contains(point)
                for point in probes
            ],
        ),
        _row("interval_unknown_convention_is_undecidable", "bloc_05/02 s7", "REFUSED", undecidable()),
        _row(
            "interval_completion_is_the_close_never_the_start",
            "bloc_05/02 s6",
            [BAR_END.isoformat(), BAR_END.isoformat()],
            [
                window(IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN).earliest_justified_availability().isoformat(),
                window(IntervalTimeConvention.LEFT_OPEN_RIGHT_CLOSED).earliest_justified_availability().isoformat(),
            ],
        ),
        _row("interval_unclosed_window_cannot_claim_completion", "bloc_05/02 s18 rule 2", "REFUSED", unclosed()),
        _row(
            "interval_envelope_derivation_is_read_only",
            "bloc_05/02 s18 rule 8",
            [
                BAR_END.isoformat(),
                True,
                INGESTED_2026.isoformat(),
            ],
            [envelope_answer.isoformat(), before == after, envelope.ingested_at.isoformat()],
        ),
    ]


def _availability_rows() -> list[dict]:
    rows = []

    rows.append(
        _row(
            "avail_start_stamped_interval_is_not_available_at_start",
            "bloc_05/02 s6",
            [
                "PUBLIC_INTERVAL_CLOSE",
                BAR_END.isoformat(),
                [],
                True,
            ],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(),
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_END,
                    published_at=None,
                    acquisition_metadata=_acquisition(),
                )
            )
            + [
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(),
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_END,
                    published_at=None,
                    acquisition_metadata=_acquisition(),
                ).market_available_at
                > BAR_START
            ],
        )
    )

    later_published = BAR_END + timedelta(seconds=3)
    rows.append(
        _row(
            "avail_later_publication_pushes_availability_later",
            "bloc_05/02 s6",
            ["PUBLIC_INTERVAL_CLOSE", later_published.isoformat(), []],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(),
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_END,
                    published_at=later_published,
                    acquisition_metadata=_acquisition(),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_unknown_interval_convention_fails_closed",
            "bloc_05/02 s7/s18 rule 7",
            ["UNKNOWN", None, ["TIME_INTERVAL_BOUNDARY_UNVERIFIED", "TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(
                        convention=IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN
                    ),
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_END,
                    published_at=None,
                    acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_half_declared_interval_fails_closed",
            "bloc_05/02 s7",
            ["UNKNOWN", None, ["TIME_INTERVAL_BOUNDARY_UNVERIFIED", "TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(),
                    event_time=None,
                    interval_start=BAR_START,
                    interval_end=None,
                    published_at=None,
                    acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_interval_without_registered_semantics_fails_closed",
            "bloc_05/02 s18 rule 7",
            ["UNKNOWN", None, ["TIME_INTERVAL_BOUNDARY_UNVERIFIED", "TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=None,
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_END,
                    published_at=None,
                    acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_classified_point_sample_anchors_at_the_instant",
            "bloc_05/02 s5/s6",
            ["REALTIME_PUBLIC_SNAPSHOT", BAR_START.isoformat(), []],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
                    provider_semantics=_semantics(
                        convention=IntervalTimeConvention.POINT_SAMPLE,
                        contemporaneous_public=True,
                        refs=("provider-docs:synth-a-book",),
                        family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
                    ),
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_START,
                    published_at=None,
                    acquisition_metadata=_acquisition(ingested_at=BAR_START),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_unclassified_point_sample_fails_closed",
            "bloc_05/02 s18 rule 7",
            ["UNKNOWN", None, ["TIME_INTERVAL_BOUNDARY_UNVERIFIED", "TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
                    provider_semantics=_semantics(
                        convention=IntervalTimeConvention.POINT_SAMPLE,
                        family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
                    ),
                    event_time=BAR_START,
                    interval_start=BAR_START,
                    interval_end=BAR_START,
                    published_at=None,
                    acquisition_metadata=_acquisition(ingested_at=BAR_START),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_published_without_a_declared_field_is_delayed_publication",
            "bloc_05/02 s5/s6",
            ["DELAYED_PUBLICATION", PUBLISHED.isoformat(), []],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_FUNDING,
                    provider_semantics=_semantics(family=SensorFamily.MECHANICAL_FUNDING),
                    event_time=BAR_END,
                    interval_start=None,
                    interval_end=None,
                    published_at=PUBLISHED,
                    acquisition_metadata=_acquisition(ingested_at=INGESTED_2026),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_declared_published_field_is_provider_declared_public_time",
            "bloc_05/02 s3/s5",
            ["PROVIDER_DECLARED_PUBLIC_TIME", PUBLISHED.isoformat(), []],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_FUNDING,
                    provider_semantics=_semantics(
                        family=SensorFamily.MECHANICAL_FUNDING,
                        roles={time_package.TimestampRole.PUBLISHED_AT: "funding_publish_time"},
                    ),
                    event_time=BAR_END,
                    interval_start=None,
                    interval_end=None,
                    published_at=PUBLISHED,
                    acquisition_metadata=_acquisition(ingested_at=PUBLISHED),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_archive_with_contemporaneous_evidence_is_labeled",
            "bloc_05/02 s6/s16",
            [
                "HISTORICAL_ARCHIVE_RECONSTRUCTION",
                EVENT_2022.isoformat(),
                ["TIME_ARCHIVE_RECONSTRUCTION"],
            ],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(),
                    event_time=EVENT_2022,
                    interval_start=None,
                    interval_end=None,
                    published_at=None,
                    acquisition_metadata=_acquisition(
                        observed_at=OBSERVED_2026,
                        ingested_at=INGESTED_2026,
                        evidence=("archive-docs:oi-2022-public",),
                    ),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_archive_without_evidence_is_system_only",
            "bloc_05/02 s6/s14",
            ["SYSTEM_ONLY_OBSERVED", None, ["TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    provider_semantics=_semantics(),
                    event_time=EVENT_2022,
                    interval_start=None,
                    interval_end=None,
                    published_at=None,
                    acquisition_metadata=_acquisition(
                        observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
                    ),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_classified_realtime_event_anchors_at_event_time",
            "bloc_05/02 s5/s6",
            ["REALTIME_PUBLIC_EVENT", EVENT_2022.isoformat(), []],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_TRADE,
                    provider_semantics=_semantics(
                        family=SensorFamily.MECHANICAL_TRADE,
                        contemporaneous_public=True,
                        refs=("provider-docs:synth-a-trades",),
                    ),
                    event_time=EVENT_2022,
                    interval_start=None,
                    interval_end=None,
                    published_at=None,
                    acquisition_metadata=_acquisition(ingested_at=EVENT_2022),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_ingestion_only_never_becomes_a_market_time",
            "bloc_05/02 s4/s18 rule 3",
            ["SYSTEM_ONLY_OBSERVED", None, ["TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_TRADE,
                    provider_semantics=_semantics(family=SensorFamily.MECHANICAL_TRADE),
                    event_time=None,
                    interval_start=None,
                    interval_end=None,
                    published_at=None,
                    acquisition_metadata=_acquisition(
                        observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
                    ),
                )
            ),
        )
    )

    rows.append(
        _row(
            "avail_nothing_known_is_unknown_not_invented",
            "bloc_05/02 s5",
            ["UNKNOWN", None, ["TIME_MARKET_AVAILABILITY_UNKNOWN"]],
            _resolution_signature(
                _derive(
                    sensor_family=SensorFamily.MECHANICAL_TRADE,
                    provider_semantics=None,
                    event_time=None,
                    interval_start=None,
                    interval_end=None,
                    published_at=None,
                    acquisition_metadata=_acquisition(),
                )
            ),
        )
    )

    base = dict(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(
            family=SensorFamily.MECHANICAL_TRADE,
            contemporaneous_public=True,
            refs=("provider-docs:synth-a-trades",),
        ),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
    )
    with_ingest = _derive(
        acquisition_metadata=_acquisition(ingested_at=INGESTED_2026), **base
    )
    without_ingest = _derive(acquisition_metadata=_acquisition(), **base)
    rows.append(
        _row(
            "avail_ingested_at_is_not_an_input_to_the_derivation",
            "bloc_05/02 s4/s18 rule 3",
            True,
            with_ingest.market_available_at == without_ingest.market_available_at
            and with_ingest.availability_basis == without_ingest.availability_basis
            and with_ingest.market_available_at == EVENT_2022,
        )
    )

    false_claim = _observed_outcome(
        lambda: AvailabilityResolution(
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            availability_basis=AvailabilityBasis.SYSTEM_ONLY_OBSERVED,
            market_available_at=INGESTED_2026,
        )
    )
    rows.append(
        _row(
            "avail_false_availability_claim_is_refused_at_construction",
            "bloc_05/02 s5/s18 rule 3",
            "REFUSED",
            false_claim,
        )
    )
    return rows


def _revision_rows() -> list[dict]:
    original, correction = _revisions()
    as_known = select_revisions(
        (original, correction), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    only_correction = select_revisions(
        (correction,), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    latest = select_revisions(
        (original, correction), _policy(RevisionMode.LATEST_VERIFIED), CUTOFF_2022
    )

    def unsupported() -> dict:
        outcome = {}
        for mode in (
            RevisionMode.FIRST_SEEN,
            RevisionMode.EXACT_REVISION,
            RevisionMode.ALL_REVISIONS,
            RevisionMode.ERROR_ON_AMBIGUITY,
        ):
            outcome[mode.value] = _observed_outcome(
                lambda mode=mode: select_revisions(
                    (original,), _policy(mode), CUTOFF_2022
                )
            )
        return outcome

    catalog = _catalog()
    return [
        _row(
            "revision_as_known_then_excludes_the_future_correction",
            "bloc_05/02 s12",
            [["rev-oi-2022-original"], ["rev-oi-2022-corrected-2025"], True, False],
            [
                [record.source_revision_id for record in as_known.selected],
                [record.source_revision_id for record in as_known.excluded],
                as_known.pit_safe,
                as_known.pit_uncertain,
            ],
        ),
        _row(
            "revision_missing_original_is_pit_revision_uncertain",
            "bloc_05/02 s12",
            [[], ["rev-oi-2022-corrected-2025"], True, True],
            [
                [record.source_revision_id for record in only_correction.selected],
                [record.source_revision_id for record in only_correction.excluded],
                only_correction.pit_safe,
                only_correction.pit_uncertain,
            ],
        ),
        _row(
            "revision_latest_verified_selects_the_correction_and_is_not_pit_safe",
            "bloc_05/02 s11",
            [["rev-oi-2022-corrected-2025"], ["rev-oi-2022-original"], False, False],
            [
                [record.source_revision_id for record in latest.selected],
                [record.source_revision_id for record in latest.excluded],
                latest.pit_safe,
                latest.pit_uncertain,
            ],
        ),
        _row(
            "revision_undefined_modes_are_refused_not_improvised",
            "bloc_05/02 s11",
            {
                "FIRST_SEEN": "REFUSED",
                "EXACT_REVISION": "REFUSED",
                "ALL_REVISIONS": "REFUSED",
                "ERROR_ON_AMBIGUITY": "REFUSED",
            },
            unsupported(),
        ),
        _row(
            "revision_config_covers_exactly_the_six_frozen_modes",
            "bloc_05/02 s11/s17",
            [mode.value for mode in RevisionMode],
            [policy.mode.value for policy in catalog.policies],
        ),
        _row(
            "revision_config_defines_only_the_two_frozen_definitions",
            "bloc_05/02 s11",
            {
                "AS_KNOWN_THEN": "Select only values/revisions that were available by replay cutoff.",
                "LATEST_VERIFIED": "Useful for retrospective measurement but not automatically PIT-safe.",
                "FIRST_SEEN": None,
                "EXACT_REVISION": None,
                "ALL_REVISIONS": None,
                "ERROR_ON_AMBIGUITY": None,
            },
            {
                policy.mode.value: policy.definition for policy in catalog.policies
            },
        ),
    ]


def _gate_rows() -> list[dict]:
    return [
        _row(
            "gate_all_six_conditions_are_eligible",
            "bloc_05/02 s15",
            "ELIGIBLE",
            _eligibility(),
        ),
        _row(
            "gate_unresolved_identity_blocks_first",
            "bloc_05/02 s15(1)",
            "BLOCKED_IDENTITY",
            _eligibility(identity_pit_resolved=False),
        ),
        _row(
            "gate_unverified_timestamp_semantics_block",
            "bloc_05/02 s15(2)",
            "BLOCKED_TIMESTAMP",
            _eligibility(timestamp_semantics_verified=False),
        ),
        _row(
            "gate_missing_source_evidence_blocks",
            "bloc_05/02 s15(2)",
            "BLOCKED_TIMESTAMP",
            _eligibility(source_evidence_refs=()),
        ),
        _row(
            "gate_unknown_availability_basis_blocks",
            "bloc_05/02 s5",
            "BLOCKED_TIMESTAMP",
            _eligibility(availability_basis=AvailabilityBasis.UNKNOWN),
        ),
        _row(
            "gate_system_only_availability_blocks",
            "bloc_05/02 s5",
            "BLOCKED_TIMESTAMP",
            _eligibility(availability_basis=AvailabilityBasis.SYSTEM_ONLY_OBSERVED),
        ),
        _row(
            "gate_missing_market_available_at_blocks",
            "bloc_05/02 s5",
            "BLOCKED_TIMESTAMP",
            _eligibility(market_available_at=None),
        ),
        _row(
            "gate_missing_availability_confidence_blocks",
            "bloc_05/02 s5",
            "BLOCKED_TIMESTAMP",
            _eligibility(availability_confidence=None),
        ),
        _row(
            "gate_incomplete_interval_blocks",
            "bloc_05/02 s18 rule 2",
            "BLOCKED_TIMESTAMP",
            _eligibility(interval_complete=False),
        ),
        _row(
            "gate_no_revision_evaluation_blocks",
            "bloc_05/02 s15(4)",
            "BLOCKED_REVISION",
            _eligibility(revision=None),
        ),
        _row(
            "gate_uncertain_pit_revision_blocks",
            "bloc_05/02 s12",
            "BLOCKED_REVISION",
            _eligibility(
                revision=select_revisions(
                    (), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
                )
            ),
        ),
        _row(
            "gate_latest_verified_is_retrospective_only",
            "bloc_05/02 s11/s15",
            "RETROSPECTIVE_ONLY",
            _eligibility(revision=_selection(RevisionMode.LATEST_VERIFIED)),
        ),
        _row(
            "gate_broken_lineage_blocks",
            "bloc_05/02 s15(5)",
            "BLOCKED_LINEAGE",
            _eligibility(
                lineage=LineageState.LINEAGE_BROKEN,
                quality_flags=(NormalizationQualityFlag.LINEAGE_BROKEN,),
            ),
        ),
        _row(
            "gate_blocking_flag_without_a_frozen_bucket_refuses",
            "bloc_05/02 s15",
            "REFUSED",
            _observed_outcome(
                lambda: assess_replay_eligibility(
                    _evidence(
                        quality_flags=(NormalizationQualityFlag.SEMANTICS_UNVERIFIED,)
                    )
                )
            ),
        ),
        _row(
            "gate_label_only_flags_never_block",
            "bloc_05/02 s16",
            ["ELIGIBLE", "ELIGIBLE", "ELIGIBLE"],
            [
                _eligibility(
                    quality_flags=(flag,)
                )
                for flag in (
                    NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,
                    NormalizationQualityFlag.TIME_PRECISION_COARSE,
                    NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY,
                )
            ],
        ),
        _row(
            "gate_condition_order_is_frozen_not_input_order",
            "bloc_05/02 s15",
            "BLOCKED_IDENTITY",
            _eligibility(
                identity_pit_resolved=False,
                timestamp_semantics_verified=False,
                interval_complete=False,
                lineage=LineageState.LINEAGE_BROKEN,
            ),
        ),
        _row(
            "gate_blocking_flag_set_is_the_frozen_nine",
            "bloc_05/02 s5/s16",
            [
                "IDENTITY_AMBIGUOUS",
                "IDENTITY_TERMS_UNVERIFIED",
                "LINEAGE_BROKEN",
                "REFERENCE_PRICE_UNAVAILABLE",
                "SEMANTICS_UNVERIFIED",
                "STABLECOIN_CONVERSION_UNAVAILABLE",
                "TIME_MARKET_AVAILABILITY_UNKNOWN",
                "TIME_SEMANTICS_UNVERIFIED",
                "UNIT_CONVERSION_BLOCKED",
            ],
            sorted(flag.value for flag in BLOCKING_QUALITY_FLAGS),
        ),
    ]


def _scenario_rows() -> list[dict]:
    """The six frozen acceptance scenarios, executed end to end."""
    rows = []

    # F05-01
    window = IntervalWindow(
        interval_start_at=BAR_START,
        interval_end_at=BAR_END,
        interval_closed=True,
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
    )
    resolution = _derive(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=BAR_START,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=_acquisition(observed_at=BAR_START, ingested_at=BAR_END),
    )
    rows.append(
        _row(
            "F05_01_start_stamped_interval_not_available_at_start",
            "bloc_05/06 s13",
            [True, BAR_END.isoformat()],
            [
                resolution.market_available_at
                >= window.earliest_justified_availability()
                and resolution.market_available_at > BAR_START,
                resolution.market_available_at.isoformat(),
            ],
        )
    )

    # F05-02
    archive = _derive(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        provider_semantics=_semantics(),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026,
            ingested_at=INGESTED_2026,
            evidence=("archive-docs:oi-2022-public",),
        ),
    )
    archive_gate = _eligibility(
        availability_basis=archive.availability_basis,
        market_available_at=archive.market_available_at,
        quality_flags=(NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,),
    )
    rows.append(
        _row(
            "F05_02_contemporaneous_archive_row_is_historical_reconstruction",
            "bloc_05/06 s13",
            ["HISTORICAL_ARCHIVE_RECONSTRUCTION", "ELIGIBLE"],
            [archive.availability_basis.value, archive_gate],
        )
    )

    # F05-03 / F05-04
    original, correction = _revisions()
    as_known = select_revisions(
        (original, correction), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    rows.append(
        _row(
            "F05_03_late_correction_excluded_from_as_known_then_replay",
            "bloc_05/06 s13",
            [False, True],
            [
                any(record.revision_status is RevisionStatus.PROVIDER_CORRECTED
                     for record in as_known.selected),
                _eligibility(revision=as_known) == "ELIGIBLE",
            ],
        )
    )
    latest = select_revisions(
        (original, correction), _policy(RevisionMode.LATEST_VERIFIED), CUTOFF_2022
    )
    rows.append(
        _row(
            "F05_04_retrospective_correction_eligible_only_in_retrospective_mode",
            "bloc_05/06 s13",
            ["rev-oi-2022-corrected-2025", "RETROSPECTIVE_ONLY"],
            [
                [record.source_revision_id for record in latest.selected][0],
                _eligibility(revision=latest),
            ],
        )
    )

    # F05-05
    unknown_registry = parse_provider_time_semantics_yaml(
        SEMANTICS_CONFIG.read_text(encoding="utf-8")
    )
    system_only = _derive(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(family=SensorFamily.MECHANICAL_TRADE),
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
        ),
    )
    rows.append(
        _row(
            "F05_05_unknown_market_availability_blocks_strict_replay",
            "bloc_05/06 s13",
            ["SYSTEM_ONLY_OBSERVED", "BLOCKED_TIMESTAMP", "REFUSED"],
            [
                system_only.availability_basis.value,
                _eligibility(
                    availability_basis=system_only.availability_basis,
                    market_available_at=system_only.market_available_at,
                ),
                _observed_outcome(
                    lambda: unknown_registry.require(
                        "KRAKEN_FUTURES", SensorFamily.MECHANICAL_TRADE
                    )
                ),
            ],
        )
    )

    # F05-06
    ingestion_only = _derive(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_semantics(family=SensorFamily.MECHANICAL_TRADE),
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_acquisition(
            observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
        ),
    )
    rows.append(
        _row(
            "F05_06_ingestion_time_cannot_replace_market_availability",
            "bloc_05/06 s13",
            [None, True, "BLOCKED_TIMESTAMP"],
            [
                ingestion_only.market_available_at,
                ingestion_only.market_available_at != INGESTED_2026,
                _eligibility(
                    availability_basis=ingestion_only.availability_basis,
                    market_available_at=ingestion_only.market_available_at,
                ),
            ],
        )
    )
    return rows


def _adversarial_rows() -> list[dict]:
    def dst_gap_refused() -> str:
        try:
            ObservationTimeEnvelope(
                source_event_at=datetime(2023, 3, 12, hour=2, minute=30)
            )
        except Exception:
            return "REFUSED"
        return "ACCEPTED"

    def unsupported_mode_error() -> str:
        original, _ = _revisions()
        try:
            select_revisions(
                (original,), _policy(RevisionMode.ALL_REVISIONS), CUTOFF_2022
            )
        except UnsupportedRevisionMode:
            return "UnsupportedRevisionMode"
        return "NO_EXCEPTION"

    def undecidable_error() -> str:
        try:
            IntervalWindow(
                interval_start_at=BAR_START,
                interval_end_at=BAR_END,
                interval_closed=True,
                interval_time_convention=IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN,
            ).earliest_justified_availability()
        except UndecidableIntervalBoundary:
            return "UndecidableIntervalBoundary"
        return "NO_EXCEPTION"

    def unbucketed_error() -> str:
        try:
            assess_replay_eligibility(
                _evidence(quality_flags=(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,))
            )
        except UnassessableReplayEvidence:
            return "UnassessableReplayEvidence"
        return "NO_EXCEPTION"

    def unknown_semantics_error() -> str:
        try:
            parse_provider_time_semantics_yaml(
                SEMANTICS_CONFIG.read_text(encoding="utf-8").replace(
                    "semantics: []",
                    "semantics:\n"
                    "  - provider: SYNTHETIC_EXCHANGE_A\n"
                    "    sensor_family: MECHANICAL_TRADE\n"
                    "    timestamp_field_roles: {}\n"
                    "    interval_time_convention: LEFT_ONLY\n"
                    "    precision: MICROSECOND\n"
                    "    contemporaneous_public: false\n"
                    "    source_evidence_refs: []\n",
                )
            )
        except ValueError:
            return "ValueError"
        return "NO_EXCEPTION"

    time_sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(
            (_QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "time").glob(
                "*.py"
            )
        )
    }
    # The tokens are assembled so this producer's own source text -- which
    # necessarily NAMES the tokens it scans for -- does not trip its own scan.
    clock_tokens = (
        "datetime" + ".now(",
        "datetime" + ".utcnow(",
        "date" + ".today(",
        "time" + ".time(",
        "hash" + "lib",
        "u" + "uid",
    )
    wall_clock_hits = sorted(
        name
        for name, text in time_sources.items()
        for token in clock_tokens
        if token in text
    )

    original, correction = _revisions()
    leakage = []
    for cutoff in (CUTOFF_2022, CUTOFF_2022 + timedelta(days=1), KNOWN_2025):
        selection = select_revisions(
            (original, correction), _policy(RevisionMode.AS_KNOWN_THEN), cutoff
        )
        leakage.append(
            all(
                record.known_from <= cutoff
                and (record.known_to is None or record.known_to > cutoff)
                for record in selection.selected
            )
        )

    return [
        _row("adv_dst_gap_naive_timestamp_refused", "bloc_05/02 s18 rule 1", "REFUSED", dst_gap_refused()),
        _row("adv_unsupported_revision_mode_names_itself", "bloc_05/02 s11", "UnsupportedRevisionMode", unsupported_mode_error()),
        _row("adv_unknown_boundary_convention_names_itself", "bloc_05/02 s7", "UndecidableIntervalBoundary", undecidable_error()),
        _row("adv_unbucketed_blocking_flag_names_itself", "bloc_05/02 s15", "UnassessableReplayEvidence", unbucketed_error()),
        _row("adv_unknown_interval_convention_token_refused", "bloc_05/02 s7", "ValueError", unknown_semantics_error()),
        _row("adv_time_package_has_no_wall_clock_or_hashing", "bloc_05/02 s18 rule 8", [], wall_clock_hits),
        _row("adv_no_future_correction_leaks_into_any_as_known_then_selection", "bloc_05/02 s12", [True, True, True], leakage),
        _row(
            "adv_naive_knowledge_time_is_refused",
            "bloc_05/02 s18 rule 1",
            "REFUSED",
            _observed_outcome(
                lambda: RevisionRecord(
                    source_revision_id="rev-naive",
                    normalization_generation=1,
                    supersedes_t1_record_id=None,
                    revision_status=RevisionStatus.ORIGINAL,
                    known_from=datetime(2022, 5, 12),
                )
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


def build_rows() -> list[dict]:
    rows: list[dict] = []
    rows.extend(_vocabulary_rows())
    rows.extend(_timestamp_model_rows())
    rows.extend(_registry_rows())
    rows.extend(_interval_rows())
    rows.extend(_availability_rows())
    rows.extend(_revision_rows())
    rows.extend(_gate_rows())
    rows.extend(_scenario_rows())
    rows.extend(_adversarial_rows())
    for index, row in enumerate(rows):
        row["index"] = index
    return rows


def build_scope_rows() -> list[dict]:
    package = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "time"
    files = sorted(path.name for path in package.glob("*.py"))
    configs = sorted(
        name
        for name in ("provider_time_semantics.yaml", "revision_policies.yaml")
        if (_QUANT_LAB / "config" / "crypto_sensor_fabric" / name).is_file()
    )
    test_files = sorted(
        path.name
        for path in (
            _QUANT_LAB / "tests" / "crypto_sensor_fabric" / "normalization"
        ).glob("test_b5_i05_*.py")
    )
    protected = [
        "src/crypto_sensor_fabric/normalization/__init__.py",
        "src/crypto_sensor_fabric/normalization/enums.py",
        "src/crypto_sensor_fabric/normalization/models.py",
        "src/crypto_sensor_fabric/normalization/identity",
        "src/crypto_sensor_fabric/normalization/terms",
    ]
    changed_protected = sorted(
        {
            line
            for path in protected
            for line in _git("diff", "--name-only", BASE_HEAD, "--", path).splitlines()
            if line.strip()
        }
    )
    import crypto_sensor_fabric.normalization as normalization

    time_names = {
        "CanonicalTimestamp",
        "AvailabilityResolution",
        "derive_market_available_at",
        "assess_replay_eligibility",
        "ReplayEligibility",
        "TimestampRole",
    }
    forbidden_imports = sorted(
        {
            token
            for name in files
            for token in (
                "requests",
                "httpx",
                "socket",
                "pathlib",
                "duckdb",
                "hashlib",
                "uuid",
                "os.path",
            )
            if token in (package / name).read_text(encoding="utf-8")
        }
    )
    gate_language = sorted(
        name
        for name in files
        for token in ("OPERATOR_ACCEPTED", "IMPLEMENTATION_PASS", "_GATE =")
        if token in (package / name).read_text(encoding="utf-8")
    )

    rows = [
        _row(
            "scope_time_package_is_the_frozen_seven_modules_plus_init",
            "bloc_05/02 s17",
            [
                "__init__.py",
                "availability.py",
                "enums.py",
                "intervals.py",
                "models.py",
                "replay_gate.py",
                "revision_policy.py",
                "semantics_registry.py",
            ],
            files,
        ),
        _row(
            "scope_two_frozen_configurations_present",
            "bloc_05/02 s17",
            ["provider_time_semantics.yaml", "revision_policies.yaml"],
            configs,
        ),
        _row(
            "scope_i01_to_i04_sources_unchanged_since_base",
            "I05 directive section 03",
            [],
            changed_protected,
        ),
        _row(
            "scope_i01_top_level_api_not_expanded",
            "bloc_05/06 s19/s20",
            [24, []],
            [
                len(normalization.__all__),
                sorted(time_names & set(normalization.__all__)),
            ],
        ),
        _row(
            "scope_no_forbidden_import_in_the_time_package",
            "I05 directive section 03",
            [],
            forbidden_imports,
        ),
        _row(
            "scope_no_gate_or_acceptance_language_in_the_time_package",
            "I05 directive section 09",
            [],
            gate_language,
        ),
        _row(
            "scope_nine_i05_test_modules_present",
            "I05 directive section 04",
            [
                "test_b5_i05_availability.py",
                "test_b5_i05_evidence.py",
                "test_b5_i05_frozen_scenarios.py",
                "test_b5_i05_intervals.py",
                "test_b5_i05_replay_gate.py",
                "test_b5_i05_revision_policy.py",
                "test_b5_i05_scope_audit.py",
                "test_b5_i05_semantics_registry.py",
                "test_b5_i05_time_models.py",
            ],
            test_files,
        ),
    ]
    for index, row in enumerate(rows):
        row["index"] = index
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_payload() -> dict:
    rows = build_rows()
    return {
        "artifact": "bloc_05_time_validation",
        "checkpoint": CHECKPOINT,
        "generator": GEN_REF,
        "tests": TESTS,
        "run_date": RUN_DATE,
        "authority": [
            "bloc_05/02 sections 2-18",
            "bloc_05/06 section 1 G2",
            "bloc_05/06 section 13",
            "bloc_05/06 section 17",
            "bloc_05/07 F8/F9",
        ],
        "evidence_truth": (
            "Every row is an executed probe: `observed` is produced by the real "
            "production functions over deterministic fixtures, `expected` is the "
            "literal written from the frozen contract, and `pass` is their "
            "equality.  No live clock, no network, no untracked dependency."
        ),
        "sha256_inventory": {relpath: _sha256(_ROOT / relpath) for relpath in INVENTORY},
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "pass": sum(1 for row in rows if row["pass"]),
            "fail": sum(1 for row in rows if not row["pass"]),
        },
        "all_results_pass": all(row["pass"] for row in rows),
    }


def build_scope_payload() -> dict:
    rows = build_scope_rows()
    return {
        "artifact": "BLOC_05_I05_SCOPE_AUDIT",
        "checkpoint": CHECKPOINT,
        "generator": GEN_REF,
        "run_date": RUN_DATE,
        "base_head": BASE_HEAD,
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "pass": sum(1 for row in rows if row["pass"]),
            "fail": sum(1 for row in rows if not row["pass"]),
        },
        "all_results_pass": all(row["pass"] for row in rows),
    }


def mandatory_exit_code(payload: dict) -> int:
    """Nonzero for any failed mandatory check (I05 directive section 06)."""
    rows = payload.get("rows", [])
    failed = [row for row in rows if not row.get("pass")]
    if failed or not payload.get("all_results_pass"):
        return 1
    if payload.get("summary", {}).get("fail"):
        return 1
    if payload.get("summary", {}).get("rows") != len(rows):
        return 1
    return 0


def _dump(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    scope = build_scope_payload()
    ARTIFACT.write_bytes(_dump(payload))
    SCOPE_ARTIFACT.write_bytes(_dump(scope))
    print(f"{ARTIFACT.name}: {payload['summary']['rows']} rows, {payload['summary']['pass']} pass, {payload['summary']['fail']} fail")
    print(f"{SCOPE_ARTIFACT.name}: {scope['summary']['rows']} rows, {scope['summary']['pass']} pass, {scope['summary']['fail']} fail")
    code = max(mandatory_exit_code(payload), mandatory_exit_code(scope))
    if code:
        print("MANDATORY CHECK FAILED", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
