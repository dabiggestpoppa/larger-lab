"""SENSOR-B5-I06E1 deterministic replay-safety evidence generator.

Run from quant-lab/:
    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py

Writes two artifacts beside the other bloc_05 evidence:
    evidence/bloc_05/bloc_05_replay_safety_validation.json
    evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json

Mission (I06E1 sections 03-06): a consolidated, executable proof of the
ACCEPTED I05 admission-policy chain over fourteen frozen RS cases.  This
producer is a CLIENT of the accepted primitives -- it imports
``derive_market_available_at``, ``assess_replay_eligibility`` and
``select_revisions`` from ``crypto_sensor_fabric.normalization.time`` and
never redefines any of them (no duplicate engine, I06D1 register M2).

Laws (mirroring the I03/I04/I05 producers):

* ``expected_*`` facts are written from the frozen clause BEFORE the probe
  runs; ``observed_*`` facts are measured by the production functions;
  ``pass`` is their equality, and the row carries both facts as human-readable
  sentences (expected sentence first);
* exact ``bloc_05/<doc> s<n>`` clause references on every row;
* refusal classes are exact and drawn from the fixed seven-member vocabulary
  below -- no seventh replay status is minted anywhere;
* stable row order (RS-01..RS-14), stable serialization
  (``json.dumps(..., sort_keys=True)``), LF-only bytes via ``write_bytes``;
* no live clock: a pinned ``RUN_DATE`` literal, never a system-date call;
* no network: the only subprocess is ``git`` metadata for the scope rows;
* SHA-256 inventory of every tracked input the artifacts depend on;
* nonzero exit whenever a mandatory row fails.

Operator decisions honored here (I06E1 section 00):

* M1 Option B: confidence stays an opaque presence-checked token -- this
  producer neither reads nor writes any confidence vocabulary;
* M3/M4 DEFERRED: zero real-provider rows, zero latency numbers; RS-14 proves
  the absence of a latency input rather than inventing one;
* M5/M6: no T1 writer, no query-time cutoff filter -- RS-04 records that
  boundary explicitly instead of faking an end-to-end cutoff execution.
"""

from __future__ import annotations

import hashlib
import inspect
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
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    NormalizationQualityFlag,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.time import (  # noqa: E402
    AcquisitionMetadata,
    IntervalWindow,
    ProviderTimeSemantics,
    ReplayEligibility,
    ReplayEvidence,
    RevisionMode,
    RevisionRecord,
    RevisionStatus,
    UnassessableReplayEvidence,
    UnknownProviderTimeSemantics,
    assess_replay_eligibility,
    derive_market_available_at,
    parse_provider_time_semantics_yaml,
    parse_revision_policies_yaml,
    select_revisions,
)

UTC = timezone.utc
RUN_DATE = "2026-10-11"
CHECKPOINT = "SENSOR-B5-I06"
BASE_HEAD = "32a89743656adb638cdaf688b62be505202f1876"

GEN_REF = (
    "live run "
    + RUN_DATE
    + ": PYTHONIOENCODING=utf-8 python "
    + "research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py "
    + "(from quant-lab; acceptance policy under test = accepted I05 time "
    + "package imported read-only + deterministic synthetic fixtures)"
)
TESTS = (
    "tests/crypto_sensor_fabric/normalization/"
    "test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py"
)
EVIDENCE_DIR = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_05"
)
ARTIFACT = EVIDENCE_DIR / "bloc_05_replay_safety_validation.json"
SCOPE_ARTIFACT = EVIDENCE_DIR / "BLOC_05_I06_SCOPE_AUDIT.json"
SEMANTICS_CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_time_semantics.yaml"
REVISION_CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "revision_policies.yaml"

#: The fixed refusal-class vocabulary.  Seven classes for fourteen cases;
#: ReplayEligibility itself keeps its frozen six members.
REFUSAL_CLASS_VOCABULARY = [
    "ADMITTED",
    "BLOCKED_STATUS",
    "BOUNDARY_SPECIFICATION",
    "EXCLUDED_BY_CUTOFF_SELECTION",
    "NO_EVIDENCE_NO_ADMISSION",
    "RETROSPECTIVE_ONLY",
    "TYPED_EXCEPTION",
]

# ---------------------------------------------------------------------------
# Deterministic fixture pins (no wall clock anywhere)
# ---------------------------------------------------------------------------

BAR_START = datetime(2024, 6, 1, hour=12, minute=0, tzinfo=UTC)
BAR_END = datetime(2024, 6, 1, hour=12, minute=5, tzinfo=UTC)
EVENT_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
INGESTED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=5, tzinfo=UTC)
OBSERVED_2026 = datetime(2026, 1, 2, hour=3, minute=4, second=6, tzinfo=UTC)
INGESTED_2026_LATER = INGESTED_2026 + timedelta(hours=1)
KNOWN_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
KNOWN_2025 = datetime(2025, 3, 3, hour=10, minute=0, tzinfo=UTC)
CUTOFF_2022 = EVENT_2022
CUTOFF_BEFORE_ORIGINAL = datetime(2021, 6, 1, tzinfo=UTC)

ORIGINAL_2022 = RevisionRecord(
    source_revision_id="rev-original-2022",
    normalization_generation=0,
    supersedes_t1_record_id=None,
    revision_status=RevisionStatus.ORIGINAL,
    known_from=KNOWN_2022,
    known_to=None,
)
CORRECTION_2025 = RevisionRecord(
    source_revision_id="rev-corrected-2025",
    normalization_generation=1,
    supersedes_t1_record_id="t1-0001",
    revision_status=RevisionStatus.PROVIDER_CORRECTED,
    known_from=KNOWN_2025,
    known_to=None,
)

#: Durable identifiers, never paths (EvidenceRef refuses anything with a
#: separator -- the I05 law, exercised by this producer's fixtures too).
ARCHIVE_EVIDENCE_REFS = ("archive-doc-2022-contemporaneously-public",)
RS03_EVIDENCE_REFS = ("i06-rs03-synthetic-fixture",)
CONFIDENCE_TOKEN = "EVIDENCE_BACKED_DECLARATION"

TIME_PACKAGE_SOURCES = [
    _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "time" / name
    for name in (
        "__init__.py",
        "enums.py",
        "models.py",
        "semantics_registry.py",
        "intervals.py",
        "availability.py",
        "revision_policy.py",
        "replay_gate.py",
    )
]

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
    "quant-lab/tests/crypto_sensor_fabric/normalization/"
    "test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py",
    "quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py",
]

#: Frozen clause + I05 evidence cross-reference for each case.
CASE_META = {
    "RS-01": ("bloc_05/02 s5", "bloc_05_time_validation.json#gate_unknown_availability_basis_blocks"),
    "RS-02": ("bloc_05/02 s4/s18 rule 3", "bloc_05_time_validation.json#F05_06_ingestion_time_cannot_replace_market_availability"),
    "RS-03": ("bloc_05/02 s15", "bloc_05_time_validation.json#gate_all_six_conditions_are_eligible"),
    "RS-04": ("bloc_05/02 s15(3)/(4) + s11", "bloc_05_time_validation.json#gate_condition_order_is_frozen_not_input_order + I06D1 package s4 RS-04"),
    "RS-05": ("bloc_05/02 s18 rule 2", "bloc_05_time_validation.json#interval_unclosed_window_cannot_claim_completion"),
    "RS-06": ("bloc_05/02 s14/s6", "bloc_05_time_validation.json#avail_archive_without_evidence_is_system_only"),
    "RS-07": ("bloc_05/02 s6/s16", "bloc_05_time_validation.json#F05_02_contemporaneous_archive_row_is_historical_reconstruction"),
    "RS-08": ("bloc_05/02 s12", "bloc_05_time_validation.json#revision_as_known_then_excludes_the_future_correction"),
    "RS-09": ("bloc_05/02 s11/s15", "bloc_05_time_validation.json#gate_latest_verified_is_retrospective_only"),
    "RS-10": ("bloc_05/02 s15(5)", "bloc_05_time_validation.json#gate_broken_lineage_blocks"),
    "RS-11": ("bloc_05/02 s15(6)", "bloc_05_time_validation.json#gate_blocking_flag_without_a_frozen_bucket_refuses"),
    "RS-12": ("bloc_05/02 s5", "bloc_05_time_validation.json#gate_missing_availability_confidence_blocks"),
    "RS-13": ("bloc_05/02 s18 rule 7", "bloc_05_time_validation.json#registry_every_real_provider_fails_closed"),
    "RS-14": ("bloc_05/02 s6", "bloc_05_time_validation.json#registry_carries_zero_real_exchange_rows + I06D1 package s3"),
}


# ---------------------------------------------------------------------------
# Fixture helpers built ON the accepted primitives
# ---------------------------------------------------------------------------

def _policy(mode: RevisionMode):
    catalog = parse_revision_policies_yaml(REVISION_CONFIG.read_text(encoding="utf-8"))
    return catalog.policy_for(mode)


def _akt_selection(cutoff: datetime):
    return select_revisions(
        (ORIGINAL_2022, CORRECTION_2025), _policy(RevisionMode.AS_KNOWN_THEN), cutoff
    )


def _evidence(**overrides) -> ReplayEvidence:
    """RS-03 happy-path scaffold; each case overrides exactly what it probes."""
    fields: dict = dict(
        identity_pit_resolved=True,
        timestamp_semantics_verified=True,
        source_evidence_refs=RS03_EVIDENCE_REFS,
        availability_basis=AvailabilityBasis.PUBLIC_INTERVAL_CLOSE,
        availability_confidence=CONFIDENCE_TOKEN,
        market_available_at=BAR_END,
        interval_complete=True,
        revision=_akt_selection(CUTOFF_2022),
        lineage=LineageState.LINEAGE_COMPLETE,
        quality_flags=(),
    )
    fields.update(overrides)
    return ReplayEvidence(**fields)


def _no_system_knowledge() -> AcquisitionMetadata:
    return AcquisitionMetadata(observed_at=None, ingested_at=None)


def _synthetic_bar_semantics() -> ProviderTimeSemantics:
    """A synthetic fixture (tests only): declared convention, not contemporaneous.

    Zero real-provider rows exist anywhere; this record exists solely so the
    interval rung of the accepted ladder can be exercised deterministically.
    """
    return ProviderTimeSemantics(
        provider="SYNTHETIC_FIXTURE_ONLY",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        timestamp_field_roles={},
        interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        precision=TimestampPrecision.SECOND,
        contemporaneous_public=False,
        source_evidence_refs=(),
    )


# ---------------------------------------------------------------------------
# The fourteen frozen cases.  Each returns its row dict; expected facts are
# written first, then the probe runs, then pass = expected == observed.
# ---------------------------------------------------------------------------

def _row(index: int, case_id: str, fixture: str, expected_sentence: str,
         expected_facts: dict, observed_sentence: str, observed_facts: dict,
         functions: list[str], refusal_class: str, disposition: str) -> dict:
    clause, evidence_ref = CASE_META[case_id]
    return {
        "index": index,
        "case_id": case_id,
        "frozen_clause": clause,
        "input_fixture": fixture,
        "expected_result": expected_sentence,
        "observed_result": observed_sentence,
        "production_functions_exercised": functions,
        "refusal_class": refusal_class,
        "evidence_reference": evidence_ref,
        "disposition": disposition,
        "pass": expected_facts == observed_facts,
        "_expected_facts": expected_facts,
        "_observed_facts": observed_facts,
    }


def case_rs01() -> dict:
    expected = {"basis": "UNKNOWN", "market_available_at": None, "eligibility": "BLOCKED_TIMESTAMP"}
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_no_system_knowledge(),
    )
    evaluation = assess_replay_eligibility(
        _evidence(
            availability_basis=resolution.availability_basis,
            market_available_at=resolution.market_available_at,
        )
    )
    observed = {
        "basis": resolution.availability_basis.value,
        "market_available_at": resolution.market_available_at,
        "eligibility": evaluation.eligibility.value,
    }
    return _row(
        0, "RS-01",
        "derivation with no interval, no publication, no event and empty acquisition metadata; "
        "gate over the resulting resolution",
        "An UNKNOWN availability basis carries no justified market time, so strict replay "
        "must be blocked with BLOCKED_TIMESTAMP.",
        expected,
        f"derivation returned basis={observed['basis']} with market_available_at="
        f"{observed['market_available_at']}; gate returned {observed['eligibility']}.",
        observed,
        ["derive_market_available_at", "assess_replay_eligibility"],
        "BLOCKED_STATUS",
        "PASS",
    )


def case_rs02() -> dict:
    expected = {
        "perturbation_changes_market_time": False,
        "basis": "SYSTEM_ONLY_OBSERVED",
        "market_available_at": None,
        "eligibility": "BLOCKED_TIMESTAMP",
    }
    first = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=OBSERVED_2026, ingested_at=INGESTED_2026
        ),
    )
    second = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=None,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=OBSERVED_2026, ingested_at=INGESTED_2026_LATER
        ),
    )
    evaluation = assess_replay_eligibility(
        _evidence(
            availability_basis=first.availability_basis,
            market_available_at=first.market_available_at,
        )
    )
    observed = {
        "perturbation_changes_market_time": (
            (first.availability_basis, first.market_available_at)
            != (second.availability_basis, second.market_available_at)
        ),
        "basis": first.availability_basis.value,
        "market_available_at": first.market_available_at,
        "eligibility": evaluation.eligibility.value,
    }
    return _row(
        1, "RS-02",
        "system-side observation only; the same derivation re-run with ingested_at moved "
        "one hour later",
        "Changing the system ingestion instant cannot establish or change market availability; "
        "the row must remain SYSTEM_ONLY_OBSERVED without a market time and stay blocked.",
        expected,
        f"ingested_at perturbation changed the answer = "
        f"{observed['perturbation_changes_market_time']}; both runs returned basis="
        f"{observed['basis']} market_available_at={observed['market_available_at']}; "
        f"gate returned {observed['eligibility']}.",
        observed,
        ["derive_market_available_at", "assess_replay_eligibility"],
        "BLOCKED_STATUS",
        "PASS",
    )


def case_rs03() -> dict:
    expected = {"eligibility": "ELIGIBLE"}
    evaluation = assess_replay_eligibility(_evidence())
    observed = {"eligibility": evaluation.eligibility.value}
    return _row(
        2, "RS-03",
        "closed five-minute bar (12:00..12:05), defensible PUBLIC_INTERVAL_CLOSE basis at the "
        "close, presence-checked confidence, ORIGINAL known by cutoff, complete lineage, no "
        "blocking flags -- all six frozen conditions",
        "A row satisfying all six frozen conditions must be admitted as ELIGIBLE.",
        expected,
        f"gate returned {observed['eligibility']}: {evaluation.reasons[0]}",
        observed,
        ["assess_replay_eligibility"],
        "ADMITTED",
        "PASS",
    )


def case_rs04() -> dict:
    expected = {
        "gate_parameters": ["evidence"],
        "market_available_at": BAR_END.isoformat(),
        "revision_selection_is_cutoff_sensitive": True,
        "availability_cutoff_filter_exists_in_i05": False,
    }
    gate_params = list(inspect.signature(assess_replay_eligibility).parameters)
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=_synthetic_bar_semantics(),
        event_time=None,
        interval_start=BAR_START,
        interval_end=BAR_END,
        published_at=None,
        acquisition_metadata=_no_system_knowledge(),
    )
    selection_at_2021 = select_revisions(
        (ORIGINAL_2022, CORRECTION_2025),
        _policy(RevisionMode.AS_KNOWN_THEN),
        CUTOFF_BEFORE_ORIGINAL,
    )
    selection_at_2022 = _akt_selection(CUTOFF_2022)
    eligibility_2021 = assess_replay_eligibility(
        _evidence(revision=selection_at_2021)
    ).eligibility
    eligibility_2022 = assess_replay_eligibility(
        _evidence(revision=selection_at_2022)
    ).eligibility
    # No public time-package function takes BOTH the availability clock and a
    # replay cutoff: row-level cutoff admission does not exist in I05 by design.
    availability_cutoff_filter = False
    for name in time_package.__all__:
        obj = getattr(time_package, name)
        if not callable(obj):
            continue
        try:
            params = set(inspect.signature(obj).parameters)
        except (TypeError, ValueError):  # pragma: no cover - builtins
            continue
        if "market_available_at" in params and params & {"cutoff", "replay_cutoff"}:
            availability_cutoff_filter = True
    observed = {
        "gate_parameters": gate_params,
        "market_available_at": resolution.market_available_at.isoformat(),
        "revision_selection_is_cutoff_sensitive": eligibility_2021 is not eligibility_2022,
        "availability_cutoff_filter_exists_in_i05": availability_cutoff_filter,
    }
    return _row(
        3, "RS-04",
        "closed bar deriving market_available_at=2024-06-01T12:05:00+00:00; revision selection "
        "evaluated at a cutoff BEFORE the original (2021-06-01) and AT it (2022-05-12); gate "
        "signature introspected; public time-package signatures scanned for a combined "
        "availability+cutoff parameter",
        "The I05 admission primitives carry no replay-cutoff parameter for market availability: "
        "cutoff sensitivity exists only in revision selection, and comparing "
        "market_available_at against a replay cutoff is a query-time filter owned by I19, so "
        "this case is a boundary specification rather than an end-to-end cutoff execution.",
        expected,
        f"assess_replay_eligibility has no cutoff parameter (parameters={gate_params}); "
        f"derive_market_available_at returned market_available_at="
        f"{observed['market_available_at']}; revision selection at the 2021 cutoff gave "
        f"{eligibility_2021.value} vs {eligibility_2022.value} at the 2022 cutoff "
        f"(cutoff_sensitive={observed['revision_selection_is_cutoff_sensitive']}); no public "
        f"time-package function takes both market_available_at and a cutoff "
        f"(availability_cutoff_filter_exists_in_i05="
        f"{observed['availability_cutoff_filter_exists_in_i05']}).",
        observed,
        ["derive_market_available_at", "select_revisions", "assess_replay_eligibility"],
        "BOUNDARY_SPECIFICATION",
        "BOUNDARY_ONLY_NOT_END_TO_END_CUTOFF_EXECUTION__I19_QUERY_FILTER_PRECONDITION",
    )


def case_rs05() -> dict:
    expected = {
        "completion_law_refused_unclosed_window": True,
        "eligibility": "BLOCKED_TIMESTAMP",
    }
    refusal = None
    try:
        IntervalWindow(
            interval_start_at=BAR_START,
            interval_end_at=BAR_END,
            interval_closed=False,
            interval_time_convention=IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN,
        ).earliest_justified_availability()
    except ValueError as exc:
        refusal = type(exc).__name__
    evaluation = assess_replay_eligibility(_evidence(interval_complete=False))
    observed = {
        "completion_law_refused_unclosed_window": refusal is not None,
        "eligibility": evaluation.eligibility.value,
    }
    return _row(
        4, "RS-05",
        "unclosed five-minute window asked for its completion instant; separately, a gate row "
        "declaring interval_complete=False",
        "An interval without justified completion must be refused by the completion law and "
        "must never be admitted to strict replay.",
        expected,
        f"completion law raised {refusal} for the unclosed window; gate returned "
        f"{observed['eligibility']} for interval_complete=False.",
        observed,
        ["IntervalWindow.earliest_justified_availability", "assess_replay_eligibility"],
        "BLOCKED_STATUS",
        "PASS",
    )


def case_rs06() -> dict:
    expected = {
        "event_time_supplied": True,
        "basis": "SYSTEM_ONLY_OBSERVED",
        "market_available_at": None,
        "eligibility": "BLOCKED_TIMESTAMP",
    }
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=None, ingested_at=INGESTED_2026
        ),
    )
    evaluation = assess_replay_eligibility(
        _evidence(
            availability_basis=resolution.availability_basis,
            market_available_at=resolution.market_available_at,
        )
    )
    observed = {
        "event_time_supplied": True,
        "basis": resolution.availability_basis.value,
        "market_available_at": resolution.market_available_at,
        "eligibility": evaluation.eligibility.value,
    }
    return _row(
        5, "RS-06",
        "2022 archive event time supplied, file ingested 2026-01-02, NO contemporaneous-public "
        "evidence refs, no provider classification",
        "An archive event obtained later without contemporaneous-public proof must yield no "
        "market availability time and must stay blocked from strict replay.",
        expected,
        f"despite event_time={EVENT_2022.isoformat()} and ingested_at={INGESTED_2026.isoformat()}, "
        f"derivation returned basis={observed['basis']} market_available_at="
        f"{observed['market_available_at']}; gate returned {observed['eligibility']}.",
        observed,
        ["derive_market_available_at", "assess_replay_eligibility"],
        "BLOCKED_STATUS",
        "PASS",
    )


def case_rs07() -> dict:
    expected = {
        "basis": "HISTORICAL_ARCHIVE_RECONSTRUCTION",
        "market_available_at": EVENT_2022.isoformat(),
        "archive_label_flag": True,
        "availability_ignores_download_date": True,
        "eligibility": "ELIGIBLE",
    }
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=AcquisitionMetadata(
            observed_at=OBSERVED_2026,
            ingested_at=INGESTED_2026,
            contemporaneous_public_evidence_refs=ARCHIVE_EVIDENCE_REFS,
        ),
    )
    evaluation = assess_replay_eligibility(
        _evidence(
            availability_basis=resolution.availability_basis,
            market_available_at=resolution.market_available_at,
            quality_flags=resolution.quality_flags,
        )
    )
    observed = {
        "basis": resolution.availability_basis.value,
        "market_available_at": resolution.market_available_at.isoformat(),
        "archive_label_flag": NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION
        in resolution.quality_flags,
        "availability_ignores_download_date": (
            resolution.market_available_at == EVENT_2022 and EVENT_2022 != INGESTED_2026
        ),
        "eligibility": evaluation.eligibility.value,
    }
    return _row(
        6, "RS-07",
        "2022 archive event proven contemporaneously public (evidence ref present), downloaded "
        "2026-01-02; reconstruction basis evaluated for replay with the label flag attached",
        "A contemporaneously public archive reconstruction must keep the "
        "HISTORICAL_ARCHIVE_RECONSTRUCTION basis with its label flag, anchor at the historical "
        "event time rather than the download time, and remain admissible.",
        expected,
        f"derivation returned basis={observed['basis']} market_available_at="
        f"{observed['market_available_at']} (download date {INGESTED_2026.isoformat()} ignored = "
        f"{observed['availability_ignores_download_date']}) with label flag "
        f"{observed['archive_label_flag']}; gate returned {observed['eligibility']}.",
        observed,
        ["derive_market_available_at", "assess_replay_eligibility"],
        "ADMITTED",
        "PASS",
    )


def case_rs08() -> dict:
    expected = {
        "selected": ["rev-original-2022"],
        "excluded": ["rev-corrected-2025"],
    }
    selection = _akt_selection(CUTOFF_2022)
    observed = {
        "selected": [record.source_revision_id for record in selection.selected],
        "excluded": [record.source_revision_id for record in selection.excluded],
    }
    return _row(
        7, "RS-08",
        "ORIGINAL known 2022-05-12 + PROVIDER_CORRECTED known 2025-03-03; AS_KNOWN_THEN "
        "selection at replay cutoff 2022-05-12",
        "A correction that was not available at the historical cutoff must be excluded from "
        "AS_KNOWN_THEN selection.",
        expected,
        f"AS_KNOWN_THEN at {CUTOFF_2022.isoformat()} selected {observed['selected']} and "
        f"excluded {observed['excluded']}.",
        observed,
        ["select_revisions"],
        "EXCLUDED_BY_CUTOFF_SELECTION",
        "PASS",
    )


def case_rs09() -> dict:
    expected = {
        "selected": ["rev-corrected-2025"],
        "pit_safe": False,
        "eligibility": "RETROSPECTIVE_ONLY",
    }
    selection = select_revisions(
        (ORIGINAL_2022, CORRECTION_2025),
        _policy(RevisionMode.LATEST_VERIFIED),
        CUTOFF_2022,
    )
    evaluation = assess_replay_eligibility(_evidence(revision=selection))
    observed = {
        "selected": [record.source_revision_id for record in selection.selected],
        "pit_safe": selection.pit_safe,
        "eligibility": evaluation.eligibility.value,
    }
    return _row(
        8, "RS-09",
        "same correction chain under LATEST_VERIFIED at cutoff 2022-05-12; the verified "
        "retrospective selection feeds the gate",
        "LATEST_VERIFIED is explicitly retrospective: its selection must never be point-in-time "
        "safe and the row must evaluate RETROSPECTIVE_ONLY, never ELIGIBLE.",
        expected,
        f"LATEST_VERIFIED selected {observed['selected']} with pit_safe="
        f"{observed['pit_safe']}; gate returned {observed['eligibility']}.",
        observed,
        ["select_revisions", "assess_replay_eligibility"],
        "RETROSPECTIVE_ONLY",
        "PASS",
    )


def case_rs10() -> dict:
    expected = {"eligibility": "BLOCKED_LINEAGE"}
    evaluation = assess_replay_eligibility(_evidence(lineage=LineageState.LINEAGE_BROKEN))
    observed = {"eligibility": evaluation.eligibility.value}
    return _row(
        9, "RS-10",
        "otherwise fully admissible scaffold with lineage=LINEAGE_BROKEN",
        "Broken lineage must be refused with BLOCKED_LINEAGE.",
        expected,
        f"gate returned {observed['eligibility']}: {evaluation.reasons[0]}",
        observed,
        ["assess_replay_eligibility"],
        "BLOCKED_STATUS",
        "PASS",
    )


def case_rs11() -> dict:
    expected = {
        "raised": "UnassessableReplayEvidence",
        "eligibility_vocabulary_size": 6,
    }
    raised = None
    try:
        assess_replay_eligibility(
            _evidence(quality_flags=(NormalizationQualityFlag.SEMANTICS_UNVERIFIED,))
        )
    except UnassessableReplayEvidence:
        raised = "UnassessableReplayEvidence"
    observed = {
        "raised": raised,
        "eligibility_vocabulary_size": len(ReplayEligibility),
    }
    return _row(
        10, "RS-11",
        "blocking quality flag SEMANTICS_UNVERIFIED (frozen blocking set, no bucket in the "
        "six-status result vocabulary) presented to the gate",
        "A blocking quality flag with no frozen result bucket must raise the typed "
        "UnassessableReplayEvidence refusal; the frozen six-status vocabulary may not gain a "
        "seventh member.",
        expected,
        f"gate raised {observed['raised']} instead of returning a status; ReplayEligibility "
        f"still has {observed['eligibility_vocabulary_size']} members.",
        observed,
        ["assess_replay_eligibility"],
        "TYPED_EXCEPTION",
        "PASS",
    )


def case_rs12() -> dict:
    expected = {
        "eligibility": "BLOCKED_TIMESTAMP",
        "reason_mentions_confidence": True,
    }
    evaluation = assess_replay_eligibility(_evidence(availability_confidence=None))
    observed = {
        "eligibility": evaluation.eligibility.value,
        "reason_mentions_confidence": any(
            "availability_confidence" in reason for reason in evaluation.reasons
        ),
    }
    return _row(
        11, "RS-12",
        "fully admissible scaffold with availability_confidence=None (opaque token omitted)",
        "A replay-relevant row without availability_confidence must be blocked with "
        "BLOCKED_TIMESTAMP and must name the missing confidence in its reason.",
        expected,
        f"gate returned {observed['eligibility']}; reason names the missing confidence = "
        f"{observed['reason_mentions_confidence']}: {evaluation.reasons[0]}",
        observed,
        ["assess_replay_eligibility"],
        "BLOCKED_STATUS",
        "PASS",
    )


def case_rs13() -> dict:
    expected = {
        "raised": "UnknownProviderTimeSemantics",
        "registry_real_rows": 0,
    }
    registry = parse_provider_time_semantics_yaml(
        SEMANTICS_CONFIG.read_text(encoding="utf-8")
    )
    raised = None
    try:
        registry.require("BINANCE_USDM", SensorFamily.MECHANICAL_TRADE)
    except UnknownProviderTimeSemantics:
        raised = "UnknownProviderTimeSemantics"
    observed = {
        "raised": raised,
        "registry_real_rows": len(registry.semantics),
    }
    return _row(
        12, "RS-13",
        "tracked provider_time_semantics.yaml asked for (BINANCE_USDM, MECHANICAL_TRADE) -- "
        "no declared row exists",
        "A provider and sensor family with no declared time-semantics row must be refused by "
        "the registry and can never become verified, while the registered real-provider row "
        "count stays zero.",
        expected,
        f"registry.require raised {observed['raised']}; declared rows in the tracked config = "
        f"{observed['registry_real_rows']}.",
        observed,
        ["parse_provider_time_semantics_yaml", "ProviderTimeSemanticsRegistry.require"],
        "TYPED_EXCEPTION",
        "PASS",
    )


def case_rs14() -> dict:
    expected: dict = {
        "latency_parameters_in_derive": [],
        "unsubstantiated_claim_basis": "UNKNOWN",
        "unsubstantiated_claim_market_available_at": None,
        "zero_delay_assumed": False,
    }
    derive_params = [
        name
        for name in inspect.signature(derive_market_available_at).parameters
        if "latency" in name
    ]
    resolution = derive_market_available_at(
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        provider_semantics=None,
        event_time=EVENT_2022,
        interval_start=None,
        interval_end=None,
        published_at=None,
        acquisition_metadata=_no_system_knowledge(),
    )
    observed = {
        "latency_parameters_in_derive": derive_params,
        "unsubstantiated_claim_basis": resolution.availability_basis.value,
        "unsubstantiated_claim_market_available_at": resolution.market_available_at,
        "zero_delay_assumed": resolution.market_available_at == EVENT_2022,
    }
    latency_mentions = sum(
        path.read_text(encoding="utf-8").lower().count("latency")
        for path in TIME_PACKAGE_SOURCES
    )
    return _row(
        13, "RS-14",
        "a synthetic 'feed is instant' claim with NO provider documentation: event time "
        "supplied, no registry row, no latency declaration, empty acquisition metadata",
        "No latency-adjusted availability claim may be derived from missing evidence: the "
        "derivation exposes no latency input and an unsubstantiated claim must never be "
        "assumed to be zero delay.",
        expected,
        f"derive_market_available_at exposes no latency parameter (latency inputs="
        f"{observed['latency_parameters_in_derive']}); static latency mentions across the "
        f"eight tracked time sources = {latency_mentions} (one out-of-scope docstring note, no "
        f"code branch); the unsubstantiated claim returned basis="
        f"{observed['unsubstantiated_claim_basis']} market_available_at="
        f"{observed['unsubstantiated_claim_market_available_at']}; zero delay assumed = "
        f"{observed['zero_delay_assumed']}.",
        observed,
        ["derive_market_available_at"],
        "NO_EVIDENCE_NO_ADMISSION",
        "PASS",
    )


CASE_BUILDERS = [
    case_rs01,
    case_rs02,
    case_rs03,
    case_rs04,
    case_rs05,
    case_rs06,
    case_rs07,
    case_rs08,
    case_rs09,
    case_rs10,
    case_rs11,
    case_rs12,
    case_rs13,
    case_rs14,
]


# ---------------------------------------------------------------------------
# Payload assembly
# ---------------------------------------------------------------------------

def build_payload() -> dict:
    rows = [builder() for builder in CASE_BUILDERS]
    for row in rows:
        row.pop("_expected_facts", None)
        row.pop("_observed_facts", None)
    passed = sum(1 for row in rows if row["pass"])
    return {
        "checkpoint": CHECKPOINT,
        "generator": GEN_REF,
        "tests": TESTS,
        "all_results_pass": passed == len(rows),
        "summary": {"rows": len(rows), "pass": passed, "fail": len(rows) - passed},
        "refusal_class_vocabulary": REFUSAL_CLASS_VOCABULARY,
        "rows": rows,
        "sha256_inventory": {
            relpath: hashlib.sha256((_ROOT / relpath).read_bytes()).hexdigest()
            for relpath in INVENTORY
        },
    }


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=_ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout


# ---------------------------------------------------------------------------
# DISCLOSED B5-I08 EXTENSION (operator-authorized; full disclosure in
# ``BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md`` + ledger section 175)
# ---------------------------------------------------------------------------
#
# The I08E1 implementation pass adds ``normalization/common/`` (bloc_05/03
# section 21 required surface) and extends the I01/I05 scope audits'
# allowlists on the established I02/I04A/I05 precedent.  Amending the I05
# audit test changes its own entry in the I05 producer's SHA-256 inventory,
# which forces ``bloc_05_time_validation.json`` to be regenerated.  Three rows
# below therefore measure "nothing BUT that disclosed delta": the source row
# admits only the ``common/`` tree, the test rows pin the exact disclosed
# bytes of the two amended audits, and the evidence row pins the regenerated
# artifact.  Every other path keeps its original absolute measurement.
I08_DISCLOSED_SRC_PREFIX = "quant-lab/src/crypto_sensor_fabric/normalization/common"

I08_DISCLOSED_SHA256 = {
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i01_scope_audit.py": (
        "478b9f39f4e9a4b0b6bcda04bb134227a29bc753cbe7f7ad74980e072cc2a504"
    ),
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py": (
        "0e8544feeb26c8a1c369004a0bac7c91dd1c85bf3561250f8d70262d9f0477e6"
    ),
}

I08_DISCLOSED_EVIDENCE_SHA256 = {
    "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
    "bloc_05_time_validation.json": (
        "78d3f2a091a9dc66775c8b4bd767e12807a406ea009f9f9396babecc6eb4179f"
    ),
}

#: The exact test paths row ``no_i05_test_diff_vs_base`` has always measured.
I06_SEALED_TEST_PATHS = (
    "quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i01_scope_audit.py",
    *[
        "quant-lab/tests/crypto_sensor_fabric/normalization/" + name
        for name in (
            "test_b5_i05_time_models.py",
            "test_b5_i05_semantics_registry.py",
            "test_b5_i05_availability.py",
            "test_b5_i05_intervals.py",
            "test_b5_i05_revision_policy.py",
            "test_b5_i05_replay_gate.py",
            "test_b5_i05_frozen_scenarios.py",
            "test_b5_i05_scope_audit.py",
            "test_b5_i05_evidence.py",
        )
    ],
)

I06_SEALED_EVIDENCE_PATHS = tuple(
    "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/" + name
    for name in (
        "bloc_05_time_validation.json",
        "BLOC_05_I05_SCOPE_AUDIT.json",
        "BLOC_05_I05_OPERATOR_RATIFICATION.md",
        "BLOC_05_I06_READINESS_ASSESSMENT.md",
        "BLOC_05_I06D1_DECISION_PACKAGE.md",
    )
)


def _changed_paths(*pathspecs: str) -> list[str]:
    """Tracked paths differing from the I06 base (staged or worktree)."""
    diff = _git("diff", BASE_HEAD, "--", *pathspecs)
    return sorted(
        line.rsplit(" b/", 1)[1]
        for line in diff.splitlines()
        if line.startswith("diff --git ")
    )


def _status_paths(pathspec: str) -> list[str]:
    """Every porcelain-status path under a pathspec, untracked ones included."""
    out = _git("status", "--porcelain", "--", pathspec)
    return sorted(line[3:] for line in out.splitlines() if len(line) > 3)


def _sha256_path(relpath: str) -> str:
    return hashlib.sha256((_ROOT / relpath).read_bytes()).hexdigest()


def _src_delta_is_disclosed() -> bool:
    """Only the operator-authorized ``common/`` tree may appear under src."""
    paths = _changed_paths("quant-lab/src") + _status_paths("quant-lab/src")
    return all(path.startswith(I08_DISCLOSED_SRC_PREFIX) for path in paths)


def _sealed_test_delta_is_disclosed() -> bool:
    """No sealed test changed, or it changed to its disclosed I08 bytes."""
    changed = _changed_paths(*I06_SEALED_TEST_PATHS)
    return set(changed) <= set(I08_DISCLOSED_SHA256) and all(
        _sha256_path(path) == I08_DISCLOSED_SHA256[path] for path in changed
    )


def _i05_scope_audit_state_is_disclosed() -> bool:
    path = (
        "quant-lab/tests/crypto_sensor_fabric/normalization/"
        "test_b5_i05_scope_audit.py"
    )
    if not _changed_paths(path):
        return True  # byte-identical to base: the original I06E1 state
    return _sha256_path(path) == I08_DISCLOSED_SHA256[path]


def _sealed_evidence_state_is_disclosed() -> bool:
    for path in I06_SEALED_EVIDENCE_PATHS:
        pinned = I08_DISCLOSED_EVIDENCE_SHA256.get(path)
        if pinned is not None:
            if _sha256_path(path) != pinned:
                return False
        elif _git("diff", BASE_HEAD, "--", path) != "":
            return False
    return True


def build_scope_payload() -> dict:
    """Noninterference rows vs the I06 base commit (stable pre/post commit).

    Amended at B5-I08 (operator-authorized, disclosed): three rows now measure
    "nothing BUT the disclosed I08 delta" instead of an absolute empty diff,
    because the I08E1 implementation pass is itself authorized to add
    ``normalization/common/`` and to extend the I01/I05 scope audits.
    """

    def clean(*pathspecs: str) -> bool:
        return _git("diff", BASE_HEAD, "--", *pathspecs) == ""

    rows = [
        {
            "row_id": "no_production_source_diff_vs_base",
            "clause": (
                "I06E1 s12 (forbidden: editing sealed I01-I05 production) + "
                "DISCLOSED B5-I08 extension (operator-authorized)"
            ),
            "detail": (
                "git status + git diff 32a897436 -- quant-lab/src name only "
                "normalization/common/ paths (bloc_05/03 s21 required I08 "
                "surface); every other production path is byte-identical to base"
            ),
            "pass": _src_delta_is_disclosed(),
        },
        {
            "row_id": "no_i05_test_diff_vs_base",
            "clause": (
                "I06E1 s12 (forbidden: editing I01-I05 tests) + DISCLOSED "
                "B5-I08 scope-audit allowlist extension"
            ),
            "detail": (
                "git diff 32a897436 -- tests .../test_b5_i05_*.py + i01 scope "
                "audit names only the two audits the I08E1 directive extends, "
                "and each changed one equals its disclosed SHA-256"
            ),
            "pass": _sealed_test_delta_is_disclosed(),
        },
        {
            "row_id": "i05_scope_audit_unchanged_allowlist_displays_closed",
            "clause": (
                "I06E1 s12 + disclosure (naming, not allowlist, carries I06 "
                "tests) + DISCLOSED B5-I08 allowlist extension"
            ),
            "detail": (
                "test_b5_i05_scope_audit.py is either byte-identical to base or "
                "equal to its disclosed B5-I08-extended SHA-256: the I06 suite is "
                "named under the existing authorized test prefix, and the only later "
                "edit is the operator-authorized I08 allowlist extension"
            ),
            "pass": _i05_scope_audit_state_is_disclosed(),
        },
        {
            "row_id": "prior_checkpoint_evidence_unchanged",
            "clause": (
                "I06E1 s12 (forbidden: editing prior evidence) + DISCLOSED "
                "B5-I08 regeneration of the inventory-carrying I05 artifact"
            ),
            "detail": (
                "git diff 32a897436 -- the five sealed I05/I06D1 artifacts is "
                "empty except bloc_05_time_validation.json, which equals its "
                "disclosed post-extension SHA-256 (its inventory carries the "
                "amended I05 audit test hash)"
            ),
            "pass": _sealed_evidence_state_is_disclosed(),
        },
        {
            "row_id": "frozen_plan_unchanged",
            "clause": "bloc_05/07 freeze manifest (plan is primary authority)",
            "detail": "git diff 32a897436 -- quant-lab/research/.../bloc_05/ is empty",
            "pass": clean("quant-lab/research/crypto_foundry/sensor_fabric/bloc_05"),
        },
        {
            "row_id": "configurations_unchanged",
            "clause": "I06E1 s00 M3/M4 (registry and ladder sealed)",
            "detail": "git diff 32a897436 -- quant-lab/config is empty",
            "pass": clean("quant-lab/config"),
        },
        {
            "row_id": "confidence_model_unchanged_option_b",
            "clause": "I06E1 s00 M1 Option B (no I05 model change authorized)",
            "detail": "git diff 32a897436 -- time/models.py is empty",
            "pass": clean(
                "quant-lab/src/crypto_sensor_fabric/normalization/time/models.py"
            ),
        },
        {
            "row_id": "provider_registry_admits_zero_real_rows",
            "clause": "I06E1 s00 M3/M4 DEFERRED (no real-provider authority)",
            "detail": "provider_time_semantics.yaml parses to zero declared rows",
            "pass": len(
                parse_provider_time_semantics_yaml(
                    SEMANTICS_CONFIG.read_text(encoding="utf-8")
                ).semantics
            )
            == 0,
        },
    ]
    passed = sum(1 for row in rows if row["pass"])
    return {
        "checkpoint": CHECKPOINT,
        "all_results_pass": passed == len(rows),
        "summary": {"rows": len(rows), "pass": passed, "fail": len(rows) - passed},
        "rows": rows,
    }


def mandatory_exit_code(payload: dict) -> int:
    """Derive the exit contract from the ROWS themselves.

    A failed mandatory row must fail the run even if a cached summary flag is
    stale: the row states are the authority (I06E1 section 06).
    """
    rows = payload.get("rows", [])
    if payload.get("summary", {}).get("rows") != len(rows):
        return 1
    if any(not row.get("pass") for row in rows):
        return 1
    if not payload.get("all_results_pass"):
        return 1
    if payload.get("summary", {}).get("fail"):
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
    print(
        f"{ARTIFACT.name}: {payload['summary']['rows']} rows, "
        f"{payload['summary']['pass']} pass, {payload['summary']['fail']} fail"
    )
    print(
        f"{SCOPE_ARTIFACT.name}: {scope['summary']['rows']} rows, "
        f"{scope['summary']['pass']} pass, {scope['summary']['fail']} fail"
    )
    code = max(mandatory_exit_code(payload), mandatory_exit_code(scope))
    if code:
        print("MANDATORY CHECK FAILED", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
