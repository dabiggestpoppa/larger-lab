"""Cross-provider offline closure: deterministic production inventory (SENSOR-B3-I09).

Provider-by-provider construction is finished (KRAKEN_FUTURES, GATE_FUTURES,
OKX_SWAP, DERIBIT; 4 adapters).  This module does NOT build another provider.
It proves the four independently-built adapters form ONE coherent,
evidence-bounded acquisition fabric under the common protocol, and produces a
deterministic `AdapterReadinessRecord` per CURRENT I14 production path.

Authority flow (no self-attestation loop):

    I14 promotion packet (source_promotion_candidates.yaml)
    + actual adapter capabilities() declarations
    + committed evidence refs (which must resolve to bloc_02 evidence)
    + test/conformance results (supplied as inputs, never invented here)
    -> DERIVED readiness matrix

The generated matrix is NEVER an input to adapter capability declaration.

Provider data is EVIDENCE, not interpretation.  Same SensorFamily != same
numerical observable.  No averaging, no merging, no standardization, no
canonical identity/unit resolution, no failover.  LIMITED is a valid final
readiness state; false completeness is not.

This module is OFFLINE by construction: it instantiates real adapters but only
ever calls `capabilities()`, never a transport, so zero network occurs.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast

from .._paths import QUANT_LAB_ROOT
from ..contracts.enums import SensorFamily
from .base import (
    ALLOWED_AUTH_MODES,
    ProviderCapabilities,
    capabilities_from_promotion,
    load_promotion_candidates,
)
from .base.enums import FreeOnlyStatus
from .base.models import SensorCapability
from .deribit import DeribitAdapter
from .gate import GateAdapter
from .kraken import KrakenAdapter
from .okx import OkxAdapter

# ---------------------------------------------------------------------------
# Production adapter registry (CURRENT I14; CONFIGURATION, not economic order)
# ---------------------------------------------------------------------------

AdapterFactory = Callable[[], Any]


def _make_kraken() -> KrakenAdapter:
    return KrakenAdapter()


def _make_gate() -> GateAdapter:
    return GateAdapter()


def _make_okx() -> OkxAdapter:
    return OkxAdapter()


def _make_deribit() -> DeribitAdapter:
    return DeribitAdapter()


#: Explicit PRODUCTION adapter registry for CURRENT I14.  This is wiring that
#: maps provider_id -> concrete production adapter factory.  It is NOT a
#: fallback order, provider ranking, or economic preference.  Excluded
#: providers (BINANCE_USDM / BYBIT_LINEAR / COINALYZE /
#: BITFINEX_COMMUNITY_ARCHIVE) live in the repository as characterization
#: packages but must NOT be instanced here or counted toward the 17.
PRODUCTION_PROVIDER_REGISTRY: dict[str, AdapterFactory] = {
    "KRAKEN_FUTURES": _make_kraken,
    "GATE_FUTURES": _make_gate,
    "OKX_SWAP": _make_okx,
    "DERIBIT": _make_deribit,
}

#: Providers that are explicitly OUT of the CURRENT production registry.  They
#: keep their characterization/evidence packages but never count as production.
EXCLUDED_PRODUCTION_PROVIDERS: frozenset[str] = frozenset(
    {
        "BINANCE_USDM",
        "BYBIT_LINEAR",
        "COINALYZE",
        "BITFINEX_COMMUNITY_ARCHIVE",
    }
)

#: Controlled verification states for resume / completion.  LIMITED is a valid
#: final state; nothing is "improved" here to make the matrix look cleaner.
RESUME_YES = "YES"
RESUME_LIMITED = "LIMITED"
RESUME_NA = "n/a"
COMPLETION_YES = "YES"
COMPLETION_LIMITED = "LIMITED"
COMPLETION_NA = "n/a"


# ---------------------------------------------------------------------------
# Readiness model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadinessVerification:
    """Externally-supplied, non-self-attested readiness state for one path.

    The generator REFUSES to invent these: `offline_conformance_pass` and
    `schema_pass` must come from an actual conformance/inventory run supplied
    by the caller (the closure harness runs real conformance first).  The
    `resume_status` / `completion_status` are recorded per-provider-seal truth
    (LIMITED is valid and never upgraded here).
    """

    offline_conformance_pass: bool
    schema_pass: bool
    framework_status: str = "COMMON_FRAMEWORK_READY"
    adapter_status: str = "ADAPTER_READY"
    access_class: str = "FREE_AUTOMATED"
    network_smoke_status: str = "NOT_RUN"
    resume_status: str = RESUME_LIMITED
    completion_status: str = COMPLETION_LIMITED
    semantic_class: str = ""
    limitations: str = ""


@dataclass(frozen=True)
class AdapterReadinessRecord:
    """One deterministic production readiness record (provider x promoted sensor).

    `promoted`/`implemented`/roles/scope are DERIVED from I14 + adapter
    declaration.  Verification-state fields (`adapter_status`,
    `offline_conformance_pass`, `schema_pass`, `network_smoke_status`,
    `resume_status`, `completion_status`, `access_class`, `semantic_class`,
    `limitations`) come from the supplied `ReadinessVerification` input and are
    never invented by the generator.
    """

    provider_id: str
    sensor_family: SensorFamily
    role: str
    promoted: bool
    implemented: bool
    adapter_id: str
    adapter_version: str
    framework_status: str
    adapter_status: str
    access_path: str
    access_class: str
    auth_mode: str
    free_only_pass: bool
    history_scope: str
    native_historical_mode: str | None
    pagination_mode: str | None
    resume_status: str
    completion_status: str
    pit_readiness: str
    methodology_pin: str | None
    evidence_refs: list[str]
    production_symbol_scope: list[str]
    redundancy_class: str
    offline_conformance_pass: bool
    schema_pass: bool
    network_smoke_status: str
    semantic_class: str
    limitations: str

    @property
    def key(self) -> tuple[str, SensorFamily]:
        return (self.provider_id, self.sensor_family)


# ---------------------------------------------------------------------------
# Seal-derived verification table (recorded, never upgraded)
# ---------------------------------------------------------------------------


def _semantic_class(provider_id: str, sensor: SensorFamily) -> str:
    """Provider-native semantic class for one promoted path (I14 + seals)."""
    if sensor is SensorFamily.MECHANICAL_LIQUIDATION and provider_id == "DERIBIT":
        return "trade-level mechanism microscope (forced-liquidation events)"
    if sensor is SensorFamily.MECHANICAL_TRADE and provider_id == "DERIBIT":
        return "trade-level mechanism microscope (native trade events)"
    if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
        return "current-only raw book snapshot"
    if sensor is SensorFamily.MECHANICAL_FUNDING:
        return "provider-native funding records"
    if sensor is SensorFamily.MECHANICAL_TRADE:
        return "provider-native trade events"
    # Kraken/Gate mechanical analytics + interval views.
    return "provider-native mechanical analytics/interval view"


def _limitations(provider_id: str, sensor: SensorFamily, resume: str) -> str:
    return "no invented resume token" if resume == RESUME_LIMITED else "none"


def _resume_completion(provider_id: str, sensor: SensorFamily) -> tuple[str, str]:
    """Seal-derived resume/completion status per provider x promoted sensor.

    Matches the frozen per-provider seals: Kraken Market Analytics resume is
    proven (result.more -> since at oldest bucket); Gate is LIMITED on all
    promoted historical paths; OKX/Deribit historical continuation stays
    LIMITED (single evidenced window, truthful completion); CURRENT_ONLY book
    snapshots are n/a for pagination/resume.
    """
    if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
        return RESUME_NA, COMPLETION_NA
    if provider_id == "KRAKEN_FUTURES":
        return RESUME_YES, COMPLETION_YES
    return RESUME_LIMITED, COMPLETION_LIMITED


def default_verification(
    provider_id: str,
    sensor: SensorFamily,
    *,
    offline_conformance_pass: bool,
    schema_pass: bool,
) -> ReadinessVerification:
    """Seal-derived `ReadinessVerification` for one path.

    Conformance/schema pass flags are REQUIRED inputs (from a real run); all
    other verification fields derive from the frozen per-provider seals.
    """
    resume, completion = _resume_completion(provider_id, sensor)
    return ReadinessVerification(
        offline_conformance_pass=offline_conformance_pass,
        schema_pass=schema_pass,
        resume_status=resume,
        completion_status=completion,
        semantic_class=_semantic_class(provider_id, sensor),
        limitations=_limitations(provider_id, sensor, resume),
    )


# ---------------------------------------------------------------------------
# Record building
# ---------------------------------------------------------------------------


def _check_ready_consistency(
    key: tuple[str, SensorFamily], v: ReadinessVerification
) -> None:
    """Fail-closed consistency for an explicit verification record.

    - ADAPTER_READY may NOT coexist with a failed conformance/schema flag
      (never invent readiness from a failed validation result).
    - network_smoke_status must stay NOT_RUN while I09/I09R1 is OFFLINE (before
      I10); a caller cannot prematurely upgrade network state.
    """
    if v.adapter_status == "ADAPTER_READY":
        if not v.offline_conformance_pass or not v.schema_pass:
            raise ValueError(
                f"{key}: ADAPTER_READY cannot coexist with "
                f"offline_conformance_pass={v.offline_conformance_pass}, "
                f"schema_pass={v.schema_pass} (fail closed)"
            )
    if v.network_smoke_status != "NOT_RUN":
        raise ValueError(
            f"{key}: network_smoke_status {v.network_smoke_status!r} != NOT_RUN "
            "while I09 is OFFLINE (network smoke not authorized before I10)"
        )


def _resolve_explicit_verification(
    i14_pairs: set[tuple[str, SensorFamily]],
    verification: dict[tuple[str, SensorFamily], ReadinessVerification] | None,
    conformance_pass: dict[tuple[str, SensorFamily], bool] | None,
    schema_pass: dict[tuple[str, SensorFamily], bool] | None,
) -> dict[tuple[str, SensorFamily], ReadinessVerification]:
    """Resolve verification for every I14 path with EXPLICIT full coverage.

    Missing validation evidence != failed validation evidence.  Three
    acceptable sources:
      A) an explicit `verification` dict covering every I14 key;
      B) complete `conformance_pass` AND `schema_pass` maps covering every key;
    Absence of ANY key raises.  No defaulting of a missing key to False.
    """
    resolved: dict[tuple[str, SensorFamily], ReadinessVerification] = {}

    if verification is not None:
        missing = sorted(
            (p, s.value) for (p, s) in i14_pairs if (p, s) not in verification
        )
        if missing:
            raise ValueError(
                "missing ReadinessVerification for "
                + str(len(missing))
                + " I14 path(s) (missing validation evidence != failed "
                f"validation): {missing}"
            )
        for key in i14_pairs:
            v = verification[key]
            _check_ready_consistency(key, v)
            resolved[key] = v
        return resolved

    if conformance_pass is None and schema_pass is None:
        raise ValueError(
            "no verification input supplied (missing validation evidence is not "
            "a validation result; every I14 path requires explicit coverage)"
        )
    cf = conformance_pass if conformance_pass is not None else {}
    sf = schema_pass if schema_pass is not None else {}
    missing_c = sorted(
        (p, s.value) for (p, s) in i14_pairs if (p, s) not in cf
    )
    missing_s = sorted(
        (p, s.value) for (p, s) in i14_pairs if (p, s) not in sf
    )
    if missing_c or missing_s:
        raise ValueError(
            "verification coverage incomplete: "
            + str(len(missing_c))
            + " missing conformance key(s), "
            + str(len(missing_s))
            + " missing schema key(s); every I14 path needs explicit coverage "
            "(missing != explicit False): conformance="
            + str(missing_c)
            + ", schema="
            + str(missing_s)
        )
    for key in i14_pairs:
        provider_id, sensor = key
        v = default_verification(
            provider_id,
            sensor,
            offline_conformance_pass=cf[key],
            schema_pass=sf[key],
        )
        _check_ready_consistency(key, v)
        resolved[key] = v
    return resolved


def _free_only_pass(cap: SensorCapability) -> bool:
    return (
        cap.auth_requirement in ALLOWED_AUTH_MODES
        and cap.free_access_status is FreeOnlyStatus.FREE_COMPLIANT
    )


def build_readiness_records(
    registry: dict[str, AdapterFactory] | None = None,
    candidates: list[dict[str, object]] | None = None,
    verification: dict[tuple[str, SensorFamily], ReadinessVerification] | None = None,
    *,
    conformance_pass: dict[tuple[str, SensorFamily], bool] | None = None,
    schema_pass: dict[tuple[str, SensorFamily], bool] | None = None,
) -> list[AdapterReadinessRecord]:
    """Build the deterministic production inventory from I14 + adapter code.

    Fail-closed rules:
    - I14 promotion authority must be structurally unique (no duplicate
      provider x sensor rows, identical or conflicting) BEFORE any set/dict
      conversion;
    - the registry provider set must EXACTLY equal the I14 production provider
      set (no fifth provider, no missing provider);
    - every I14 promoted path must be declared `implemented` by its adapter;
    - every promoted path requires EXPLICIT verification coverage: either a
      `verification` dict or complete `conformance_pass` + `schema_pass` maps
      covering ALL 17 keys (a missing key FAILS CLOSED — missing validation
      evidence != explicit False);
    - ADAPTER_READY may not coexist with a failed conformance/schema flag;
    - network_smoke_status must stay NOT_RUN while I09 is OFFLINE (pre-I10);
    - a registry key must match the adapter's own `provider_id`.
    """
    providers = (
        registry
        if registry is not None
        else PRODUCTION_PROVIDER_REGISTRY
    )
    if candidates is None:
        candidates = load_promotion_candidates()

    _validate_registry(providers)
    validate_promotion_candidate_uniqueness(candidates)

    # Adapter capabilities (real adapter code + evidence-derived symbols).
    caps_by_provider: dict[str, ProviderCapabilities] = {
        pid: factory().capabilities() for pid, factory in providers.items()
    }

    i14_pairs = {
        (str(c["provider"]), SensorFamily(str(c["sensor"]))) for c in candidates
    }
    _validate_registry_provider_set(providers, i14_pairs)

    # Every I14 path must have EXPLICIT verification coverage (missing evidence
    # of validation != explicit validation failure).  Fails closed otherwise.
    verification_map = _resolve_explicit_verification(
        i14_pairs, verification, conformance_pass, schema_pass
    )

    records: list[AdapterReadinessRecord] = []
    for (provider_id, sensor) in sorted(i14_pairs, key=lambda k: (k[0], k[1].value)):
        bound_set = capabilities_from_promotion(provider_id, candidates)
        bound = bound_set.capability_for(sensor)
        if not bound.supported:
            raise ValueError(
                f"{provider_id}/{sensor.value} promoted in I14 but has no "
                "capability (fail closed)"
            )
        factory = providers[provider_id]
        adapter = factory()
        caps = caps_by_provider[provider_id]
        cap = caps.capability_for(sensor)
        if not cap.supported:
            raise ValueError(
                f"{provider_id}/{sensor.value}: promoted in I14 but the real "
                "adapter declares it UNSUPPORTED (adapter/I14 mismatch)"
            )

        key = (provider_id, sensor)
        v = verification_map[key]

        records.append(
            AdapterReadinessRecord(
                provider_id=provider_id,
                sensor_family=sensor,
                role=_role(bound),
                promoted=True,
                implemented=True,
                adapter_id=provider_id,
                adapter_version=_adapter_version(adapter),
                framework_status=v.framework_status,
                adapter_status=v.adapter_status,
                access_path=_access_path(bound) or (cap.access_mode or ""),
                access_class=v.access_class,
                auth_mode=_auth_mode(cap),
                free_only_pass=_free_only_pass(cap),
                history_scope=_history_scope(bound),
                native_historical_mode=_hist_mode(cap),
                pagination_mode=_page_mode(cap),
                resume_status=v.resume_status,
                completion_status=v.completion_status,
                pit_readiness=_pit(bound),
                methodology_pin=cap.methodology_pin,
                evidence_refs=list(bound.evidence_basis),
                production_symbol_scope=list(cap.symbol_scope),
                redundancy_class=_redundancy(bound),
                offline_conformance_pass=v.offline_conformance_pass,
                schema_pass=v.schema_pass,
                network_smoke_status=v.network_smoke_status,
                semantic_class=v.semantic_class,
                limitations=v.limitations,
            )
        )

    _validate_no_duplicates(records)
    return records


def _role(bound: SensorCapability) -> str:
    return str(bound.allowed_role.value if bound.allowed_role else "")


def _access_path(bound: SensorCapability) -> str:
    return (bound.access_mode or "")


def _history_scope(bound: SensorCapability) -> str:
    return str(bound.history_scope.value if bound.history_scope else "")


def _hist_mode(cap: SensorCapability) -> str | None:
    return str(cap.historical_mode.value) if cap.historical_mode else None


def _page_mode(cap: SensorCapability) -> str | None:
    if cap.pagination_mode is None:
        return None
    return str(cap.pagination_mode.value)


def _pit(bound: SensorCapability) -> str:
    return str(bound.pit_requirement.value) if bound.pit_requirement else ""


def _redundancy(bound: SensorCapability) -> str:
    return str(bound.redundancy_class.value) if bound.redundancy_class else ""


def _auth_mode(cap: SensorCapability) -> str:
    return str(cap.auth_requirement.value) if cap.auth_requirement else ""


def _adapter_version(adapter: Any) -> str:
    version = getattr(adapter, "adapter_version", None)
    return str(version) if version else ""


# ---------------------------------------------------------------------------
# Auditors
# ---------------------------------------------------------------------------


def _validate_registry(registry: dict[str, AdapterFactory]) -> None:
    """Duplicate/identity checks on the registry (duplicates are defects)."""
    for key, factory in registry.items():
        adapter = factory()
        pid = getattr(adapter, "provider_id", None)
        if pid != key:
            raise ValueError(
                f"registry key {key!r} does not match adapter provider_id {pid!r}"
            )
    # dict keys are unique by construction; confirm no excluded provider leaks in.
    leaks = sorted(set(registry) & EXCLUDED_PRODUCTION_PROVIDERS)
    if leaks:
        raise ValueError(
            f"excluded provider leaked into the production registry: {leaks}"
        )


def _validate_registry_provider_set(
    registry: dict[str, AdapterFactory],
    i14_pairs: set[tuple[str, SensorFamily]],
) -> None:
    i14_providers = {p for p, _ in i14_pairs}
    registry_providers = set(registry)
    if i14_providers != registry_providers:
        raise ValueError(
            "registry provider set != I14 production provider set "
            f"(registry-only={sorted(registry_providers - i14_providers)}, "
            f"I14-only={sorted(i14_providers - registry_providers)})"
        )


def _validate_no_duplicates(records: list[AdapterReadinessRecord]) -> None:
    seen: set[tuple[str, SensorFamily]] = set()
    for record in records:
        key = record.key
        if key in seen:
            raise ValueError(f"duplicate provider x sensor readiness record: {key}")
        seen.add(key)


def validate_record_bound(
    record: AdapterReadinessRecord,
    candidates: list[dict[str, object]] | None = None,
) -> list[str]:
    """Audit ONE record against its I14 promotion bound (roles/history/PIT/etc.

    Catches a drifted record (e.g. a CURRENT_ONLY path relabeled HISTORICAL,
    a MECHANISM_MICROSCOPE reclassified PRIMARY, a pin or PIT changed).  The
    record is DERIVED from the capability, so in the normal healthy state this
    is empty; the I09 drift tests mutate a record and assert these fire.
    """
    if candidates is None:
        candidates = load_promotion_candidates()
    bound_set = capabilities_from_promotion(record.provider_id, candidates)
    bound = bound_set.capability_for(record.sensor_family)
    validate_promotion_candidate_uniqueness(candidates)
    violations: list[str] = []
    sensor = record.sensor_family.value

    expected_role = str(bound.allowed_role.value) if bound.allowed_role else ""
    if record.role != expected_role:
        violations.append(
            f"{sensor}: role {record.role!r} != I14 {expected_role!r}"
        )

    expected_scope = (
        str(bound.history_scope.value) if bound.history_scope else ""
    )
    if record.history_scope != expected_scope:
        violations.append(
            f"{sensor}: history_scope {record.history_scope!r} != I14 "
            f"{expected_scope!r}"
        )

    # A CURRENT_ONLY surface may not be given a native historical mode.
    if bound.history_scope is not None and bound.history_scope.value == "CURRENT_ONLY":
        if record.native_historical_mode is not None:
            violations.append(
                f"{sensor}: CURRENT_ONLY path granted native historical mode "
                f"{record.native_historical_mode!r}"
            )

    expected_pit = str(bound.pit_requirement.value) if bound.pit_requirement else ""
    if record.pit_readiness != expected_pit:
        violations.append(
            f"{sensor}: PIT {record.pit_readiness!r} != I14 {expected_pit!r}"
        )

    if bound.methodology_pin and record.methodology_pin != bound.methodology_pin:
        violations.append(
            f"{sensor}: methodology_pin {record.methodology_pin!r} != I14 "
            f"{bound.methodology_pin!r}"
        )

    expected_red = (
        str(bound.redundancy_class.value) if bound.redundancy_class else ""
    )
    if record.redundancy_class != expected_red:
        violations.append(
            f"{sensor}: redundancy_class {record.redundancy_class!r} != I14 "
            f"{expected_red!r}"
        )
    return violations


def promotion_authority_stats(
    candidates: list[dict[str, object]] | None = None,
) -> dict[str, int]:
    """Raw / unique / duplicate counts of I14 promotion candidate rows.

    `raw_candidate_count` counts every promotion row verbatim; a duplicated
    OKX_SWAP/MECHANICAL_FUNDING row (identical or conflicting) shows up as
    raw=18 / unique=17 / duplicate_count=1.  Both raw and unique must be 17 for
    a valid CURRENT I14 authority when they are equal.
    """
    if candidates is None:
        candidates = load_promotion_candidates()
    keys = [
        (str(c["provider"]), SensorFamily(str(c["sensor"]))) for c in candidates
    ]
    raw = len(keys)
    unique = len(set(keys))
    return {
        "raw_candidate_count": raw,
        "unique_candidate_count": unique,
        "duplicate_count": raw - unique,
    }


def validate_promotion_candidate_uniqueness(
    candidates: list[dict[str, object]] | None = None,
) -> None:
    """Fail closed on ANY duplicate I14 provider x sensor promotion row.

    Promotion authority must be structurally unique BEFORE any set/dict
    conversion (a set silently drops a second row; a dict silently picks a
    winner).  Both an exact duplicate and a same-key/different-role-or-pin row
    are authority contradictions and must raise.  Callers never silently keep
    first/last or merge evidence_basis.
    """
    stats = promotion_authority_stats(candidates)
    if stats["duplicate_count"]:
        raise ValueError(
            "I14 promotion authority contains "
            f"{stats['duplicate_count']} duplicate provider x sensor row(s) "
            f"(raw={stats['raw_candidate_count']}, "
            f"unique={stats['unique_candidate_count']}); authority must be "
            "structurally unique before any set/dict conversion (fail closed)"
        )


def compute_exact_sets(
    records: list[AdapterReadinessRecord],
    candidates: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    """Three-level exact-set equality: I14 vs adapter-supported vs matrix."""
    if candidates is None:
        candidates = load_promotion_candidates()
    validate_promotion_candidate_uniqueness(candidates)
    i14_pairs = {
        (str(c["provider"]), SensorFamily(str(c["sensor"]))) for c in candidates
    }
    adapter_pairs: set[tuple[str, SensorFamily]] = set()
    for pid, factory in PRODUCTION_PROVIDER_REGISTRY.items():
        caps = factory().capabilities()
        for sensor in caps.supported_sensors():
            adapter_pairs.add((pid, sensor))
    matrix_pairs = {r.key for r in records}

    return {
        "i14": i14_pairs,
        "adapter": adapter_pairs,
        "matrix": matrix_pairs,
        "i14_vs_adapter": set_diff(i14_pairs, adapter_pairs),
        "adapter_vs_matrix": set_diff(adapter_pairs, matrix_pairs),
        "i14_vs_matrix": set_diff(i14_pairs, matrix_pairs),
        "equal": i14_pairs == adapter_pairs == matrix_pairs,
    }


def set_diff(a: set[Any], b: set[Any]) -> set[Any]:
    left = a - b
    right = b - a
    return left | right


def provider_path_counts(records: list[AdapterReadinessRecord]) -> dict[str, int]:
    return dict(sorted(Counter(r.provider_id for r in records).items()))


def role_counts(records: list[AdapterReadinessRecord]) -> dict[str, int]:
    return dict(sorted(Counter(r.role for r in records).items()))


def sensor_coverage(records: list[AdapterReadinessRecord]) -> dict[str, Any]:
    """Per-sensor source map (OBSERVABILITY COVERAGE, not ranking)."""
    by_sensor: dict[SensorFamily, list[str]] = {}
    for r in records:
        by_sensor.setdefault(r.sensor_family, []).append(r.provider_id)
    result: dict[str, Any] = {}
    for sensor in sorted(by_sensor, key=lambda s: s.value):
        providers = sorted(set(by_sensor[sensor]))
        count = len(providers)
        count_class = {
            1: "SINGLE_SOURCE",
            2: "TWO_SOURCE",
            3: "THREE_SOURCE",
            4: "FOUR_SOURCE",
        }.get(count, f"{count}_SOURCE")
        result[sensor.value] = {
            "sources": providers,
            "coverage_class": count_class,
            "count": count,
        }
    return result


def evidence_ref_audit(
    records: list[AdapterReadinessRecord],
    candidates: list[dict[str, object]] | None = None,
    bloc_02_dir: Path | None = None,
) -> list[str]:
    """Verify every production evidence_ref resolves to committed evidence.

    Per path: (1) the evidence_refs equal that path's I14 evidence_basis;
    (2) every evidence_id string appears somewhere in the committed bloc_02
    evidence tree (a resolved, committed artifact — no 'see docs' placeholders).
    Returns a list of violations (empty = audit passed).
    """
    if candidates is None:
        candidates = load_promotion_candidates()
    violations: list[str] = []

    validate_promotion_candidate_uniqueness(candidates)
    evidence_basis_by_key: dict[tuple[str, SensorFamily], set[str]] = {}
    for c in candidates:
        provider_id = str(c["provider"])
        try:
            sensor = SensorFamily(str(c["sensor"]))
        except ValueError:
            continue
        basis = set(
            str(e) for e in cast(list[object], c.get("evidence_basis", []))
        )
        evidence_basis_by_key[(provider_id, sensor)] = basis

    search_root = bloc_02_dir or (
        QUANT_LAB_ROOT
        / "research"
        / "crypto_foundry"
        / "sensor_fabric"
        / "evidence"
        / "bloc_02"
    )
    if not search_root.is_dir():
        violations.append(f"bloc_02 evidence directory missing: {search_root}")
        return violations

    resolved_ids = _evidence_ids_present(search_root)
    for r in records:
        key = (r.provider_id, r.sensor_family)
        basis = evidence_basis_by_key.get(key, set())
        if set(r.evidence_refs) != basis:
            violations.append(
                f"{r.provider_id}/{r.sensor_family.value}: evidence_refs "
                f"{sorted(set(r.evidence_refs) ^ basis)} do not match I14 basis"
            )
        for evidence_id in r.evidence_refs:
            if evidence_id not in resolved_ids:
                violations.append(
                    f"{r.provider_id}/{r.sensor_family.value}: evidence_id "
                    f"{evidence_id!r} does not resolve to a committed bloc_02 artifact"
                )
    return violations


def _evidence_ids_present(search_root: Path) -> set[str]:
    """Collect every distinct evidence-id-like token present in bloc_02 text."""
    found: set[str] = set()
    for path in search_root.iterdir():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            tokens = line.replace(",", " ").replace('"', " ").split()
            for token in tokens:
                if ("_" in token or "-" in token) and (
                    "2021" in token
                    or "2022" in token
                    or "2024" in token
                    or "2026" in token
                    or "RECENT_CONTROL" in token
                    or "book_snapshot" in token
                    or "raw_event" in token
                    or "1h" in token
                    or "book_snapshot" in token
                ):
                    found.add(token.strip())
    return found


# ---------------------------------------------------------------------------
# Deterministic serialization (canonical inventory; byte-for-byte stable)
# ---------------------------------------------------------------------------

_MATRIX_COLUMNS = [
    "provider_id",
    "sensor_family",
    "role",
    "promoted",
    "implemented",
    "adapter_id",
    "adapter_version",
    "framework_status",
    "adapter_status",
    "access_path",
    "access_class",
    "auth_mode",
    "free_only_pass",
    "history_scope",
    "native_historical_mode",
    "pagination_mode",
    "resume_status",
    "completion_status",
    "pit_readiness",
    "methodology_pin",
    "evidence_refs",
    "production_symbol_scope",
    "redundancy_class",
    "offline_conformance_pass",
    "schema_pass",
    "network_smoke_status",
    "semantic_class",
    "limitations",
]


def _record_to_row(record: AdapterReadinessRecord) -> dict[str, Any]:
    return {
        "provider_id": record.provider_id,
        "sensor_family": record.sensor_family.value,
        "role": record.role,
        "promoted": str(record.promoted),
        "implemented": str(record.implemented),
        "adapter_id": record.adapter_id,
        "adapter_version": record.adapter_version,
        "framework_status": record.framework_status,
        "adapter_status": record.adapter_status,
        "access_path": record.access_path,
        "access_class": record.access_class,
        "auth_mode": record.auth_mode,
        "free_only_pass": str(record.free_only_pass),
        "history_scope": record.history_scope,
        "native_historical_mode": record.native_historical_mode or "",
        "pagination_mode": record.pagination_mode or "",
        "resume_status": record.resume_status,
        "completion_status": record.completion_status,
        "pit_readiness": record.pit_readiness,
        "methodology_pin": record.methodology_pin or "",
        "evidence_refs": "|".join(record.evidence_refs),
        "production_symbol_scope": "|".join(record.production_symbol_scope),
        "redundancy_class": record.redundancy_class,
        "offline_conformance_pass": str(record.offline_conformance_pass),
        "schema_pass": str(record.schema_pass),
        "network_smoke_status": record.network_smoke_status,
        "semantic_class": record.semantic_class,
        "limitations": record.limitations,
    }


def render_inventory_csv(records: list[AdapterReadinessRecord]) -> str:
    """Render the DERIVED canonical production matrix as CSV text."""
    rows = [_record_to_row(r) for r in _sorted(records)]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_MATRIX_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def render_inventory_json(records: list[AdapterReadinessRecord]) -> str:
    """Render the DERIVED canonical production matrix as JSON text."""
    rows = [_record_to_row(r) for r in _sorted(records)]
    return json.dumps(
        {"schema": "PRODUCTION_ADAPTER_MATRIX", "version": "1.0", "rows": rows},
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def _sorted(records: list[AdapterReadinessRecord]) -> list[AdapterReadinessRecord]:
    return sorted(records, key=lambda r: (r.provider_id, r.sensor_family.value))


def deterministic_identity(records: list[AdapterReadinessRecord]) -> str:
    """Canonical identity string for a byte-for-byte determinism comparison."""
    return render_inventory_csv(records)


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

DEFAULT_BLOC_03_EVIDENCE_DIR = (
    QUANT_LAB_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_03"
)


def write_matrix_files(
    records: list[AdapterReadinessRecord],
    *,
    csv_path: Path | None = None,
    json_path: Path | None = None,
) -> None:
    """Write the canonical PRODUCTION_ADAPTER_MATRIX.csv / .json."""
    out_dir = DEFAULT_BLOC_03_EVIDENCE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_path or (out_dir / "PRODUCTION_ADAPTER_MATRIX.csv")
    json_path = json_path or (out_dir / "PRODUCTION_ADAPTER_MATRIX.json")
    csv_path.write_text(render_inventory_csv(records), encoding="utf-8")
    json_path.write_text(render_inventory_json(records), encoding="utf-8")


def load_matrix_records(csv_path: Path) -> list[dict[str, str]]:
    """Load a generated production matrix CSV back into raw row dicts."""
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({k: (v or "") for k, v in row.items()})
    return rows


# ---------------------------------------------------------------------------
# Human-facing readiness matrix reconciliation
# ---------------------------------------------------------------------------


def load_human_readiness_matrix(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load ADAPTER_READINESS_MATRIX.csv keyed by (provider_id, sensor_family).

    Duplicate nonempty (provider_id, sensor_family) rows are a contradiction
    and fail closed (no last-write-wins / silent overwrite / dedupe).  The
    human matrix is not authority, but contradictory duplicate rows must never
    be accepted as a clean reconciled artifact.
    """
    result: dict[tuple[str, str], dict[str, str]] = {}
    seen_keys: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            provider = (row.get("provider_id") or "").strip()
            sensor = (row.get("sensor_family") or "").strip()
            if provider and sensor:
                key = (provider, sensor)
                if key in seen_keys:
                    raise ValueError(
                        f"duplicate nonempty (provider_id, sensor_family) row in "
                        f"human readiness matrix: {key} (fail closed)"
                    )
                seen_keys.add(key)
                result[key] = {k: (v or "").strip() for k, v in row.items()}
    return result


def reconcile_human_matrix(
    records: list[AdapterReadinessRecord],
    human_rows: dict[tuple[str, str], dict[str, str]],
) -> list[str]:
    """Reconcile the generated canonical inventory against the human matrix.

    The human matrix is NOT an authority; this validates it is CONSISTENT with
    the derived 17-path production state (every generated promoted path present
    and ADAPTER_READY, no extra promoted YES rows for a production provider,
    excluded providers stay NOT_PLANNED / promoted NO).
    """
    violations: list[str] = []
    canonical_keys = {(r.provider_id, r.sensor_family.value) for r in records}
    production_providers = {r.provider_id for r in records}

    for r in records:
        human = human_rows.get((r.provider_id, r.sensor_family.value))
        if human is None:
            violations.append(
                f"h:{r.provider_id}/{r.sensor_family.value} missing from human matrix"
            )
            continue
        if human.get("adapter_status", "NOT_STARTED") != "ADAPTER_READY":
            violations.append(
                f"h:{r.provider_id}/{r.sensor_family.value} adapter_status != "
                "ADAPTER_READY"
            )
        if human.get("promoted", "NO") != "YES":
            violations.append(
                f"h:{r.provider_id}/{r.sensor_family.value} promoted != YES"
            )
        if human.get("implemented", "NO") != "YES":
            violations.append(
                f"h:{r.provider_id}/{r.sensor_family.value} implemented != YES"
            )

    # No extra promoted YES row for a CURRENT production provider.
    for key, human in human_rows.items():
        provider, sensor = key
        if provider not in production_providers:
            continue
        if key in canonical_keys:
            continue
        if human.get("promoted") == "YES" or human.get("implemented") == "YES":
            violations.append(
                f"h:{provider}/{sensor} is an EXTRA promoted/implemented row "
                "beyond the derived 17-path inventory"
            )

    # Excluded providers must remain NOT_PLANNED / promoted NO.
    excluded_ready = [
        f"{p}/{s}"
        for (p, s), human in human_rows.items()
        if p in EXCLUDED_PRODUCTION_PROVIDERS
        and (human.get("adapter_status") == "ADAPTER_READY"
             or human.get("promoted") == "YES")
    ]
    if excluded_ready:
        violations.append(
            "excluded provider present as ADAPTER_READY/promoted YES: "
            + "; ".join(excluded_ready)
        )
    return violations


__all__ = [
    "AdapterReadinessRecord",
    "COMPLETION_LIMITED",
    "COMPLETION_NA",
    "COMPLETION_YES",
    "DEFAULT_BLOC_03_EVIDENCE_DIR",
    "EXCLUDED_PRODUCTION_PROVIDERS",
    "PRODUCTION_PROVIDER_REGISTRY",
    "RESUME_LIMITED",
    "RESUME_NA",
    "RESUME_YES",
    "ReadinessVerification",
    "build_readiness_records",
    "compute_exact_sets",
    "deterministic_identity",
    "evidence_ref_audit",
    "load_human_readiness_matrix",
    "load_matrix_records",
    "provider_path_counts",
    "promotion_authority_stats",
    "reconcile_human_matrix",
    "render_inventory_csv",
    "render_inventory_json",
    "role_counts",
    "sensor_coverage",
    "validate_promotion_candidate_uniqueness",
    "validate_record_bound",
    "write_matrix_files",
]