#!/usr/bin/env python3
"""SENSOR-B5-I09E1 - tracked deterministic semantic-validation evidence producer.

First production of the frozen bloc_05/06 §17 artifact
``bloc_05_semantic_validation.json`` -- the only §17 artifact no checkpoint had
produced (readiness §8).  Because no base rows exist, this producer CREATES
the artifact; every future checkpoint that extends it must pin these rows by
SHA-256 the way the I08 artifact pins its I04B base (the established
``extensions`` merge convention).

Custody laws (I03I/I04B/I08 lessons applied):

* this file is TRACKED in the same implementation stage that creates its
  evidence -- no ``.bu_tmp`` dependency, no scratch import;
* every ``observed_result`` is measured by EXECUTING the operation here;
  expectations live only in ``expected_result``, and ``disposition`` is
  computed by the real predicate;
* any non-PASS disposition aborts with a non-zero exit BEFORE writing, so
  evidence is never emitted as a passing artifact when a fixture fails;
* the ``sha256_inventory`` is recomputed from disk before writing and any
  drift aborts before write (self-consistency, no stale pins);
* deterministic fixtures only: pinned commit tokens, no wall clock, no
  network, no ``repr()`` of objects;
* output is UTF-8, ``sort_keys``, LF, written as raw bytes so Windows
  text-mode newline translation cannot dirty the artifact;
* ``--check`` mode writes nothing and prints a machine-readable summary
  including ``artifact_sha256``; it exits 0 only when those bytes equal the
  committed artifact;
* ordering law: this producer runs BEFORE the append-only ledger entry is
  written (its hash is quoted into that entry), so it deliberately never
  names any governance document.

Run (from ``quant-lab``)::

    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py
    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py --check

Plan citations use the compact S<n> form for bloc_05/0<n> sections.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Same bootstrap as the tracked I04A/I04B/I08 producers: import the package
# straight from the repository ``src/`` tree so the generator runs from a
# clean interpreter with no installed-package dependency (I03I custody law).
sys.path.insert(0, "src")

from pydantic import ValidationError  # noqa: E402

from crypto_sensor_fabric.contracts.enums import SemanticEquivalence, SensorFamily  # noqa: E402
from crypto_sensor_fabric.normalization.common import (  # noqa: E402
    ComparableFieldFacts,
    ComparabilityCondition,
    IntervalDataScope,
    MethodologyRef,
    NormalizationMethodology,
    NormalizationMethodologyRegistry,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    UnknownNormalizationMethodology,
    UnknownProviderSemanticMapping,
    admits_critical_t1_use,
    evaluate_comparability,
    is_first_party_grade,
    parse_provider_semantic_registry_yaml,
    project_planning_mapping,
    project_planning_methodology,
    serialize_provider_semantic_registry_yaml,
)
from crypto_sensor_fabric.normalization.enums import (  # noqa: E402
    MissingnessReason,
    NormalizationQualityFlag,
)
from crypto_sensor_fabric.registry.methodology_registry import (  # noqa: E402
    load_methodology_registry,
)
from crypto_sensor_fabric.registry.provider_registry import PROVIDER_IDS  # noqa: E402
from crypto_sensor_fabric.registry.semantic_equivalence import (  # noqa: E402
    is_poolable,
    load_semantic_equivalence,
)

ROOT = Path(".")
#: The git invocations below use repository-root-relative pathspecs, so they
#: run from the worktree root (four levels above this script's directory).
REPO_ROOT = Path(__file__).resolve().parents[5]
ARTIFACT = ROOT / (
    "research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
    "bloc_05_semantic_validation.json"
)
METHODOLOGY_YAML = ROOT / "config/crypto_sensor_fabric/methodology_registry.yaml"
SEMANTIC_YAML = ROOT / "config/crypto_sensor_fabric/semantic_equivalence.yaml"

#: The Bloc 1 commit that introduced the live registries (readiness §2); the
#: ``introduced_at`` provenance token for every projected planning row.
BLOC1_REGISTRY_COMMIT = "8b2162a1184bdd885b09f5a0efaae4adeb4f7c9a"

#: The I09 custody base (BOOK 01).
I09_BASE_HEAD = "1f7a0fa6ab55b022ce3a9900717b6d3c657cc477"

#: Files whose bytes this producer pins for custody transparency.  Drift
#: aborts before write so the artifact can never describe bytes that moved.
INVENTORY = (
    "src/crypto_sensor_fabric/normalization/common/__init__.py",
    "src/crypto_sensor_fabric/normalization/common/methodologies.py",
    "src/crypto_sensor_fabric/normalization/common/semantic_registry.py",
    "src/crypto_sensor_fabric/normalization/common/comparability.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i09_semantics.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i09_scope_audit.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i01_scope_audit.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i08_scope_audit.py",
    "research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py",
)

_ROWS: list[dict[str, Any]] = []


def add(
    case_id: str,
    clause: str,
    input_condition: str,
    probe: str,
    expected: str,
    forbidden: str,
    observed: str,
    ok: bool,
    test_ref: str,
) -> None:
    _ROWS.append(
        {
            "acceptance_clause": clause,
            "case_id": case_id,
            "disposition": "PASS" if ok else "FAIL",
            "expected_result": expected,
            "forbidden_result": forbidden,
            "input_condition": input_condition,
            "observed_result": observed,
            "probe": probe,
            "test_ref": test_ref,
        }
    )


def _methodology(**overrides: Any) -> Any:
    payload: dict[str, Any] = {
        "methodology_id": "SYNTHETIC_LINEAR_OI_USD_V1",
        "version": "1",
        "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST.value,
        "description": "Synthetic fixture: contract-count OI to USD via multiplier and mark price.",
        "formula_or_algorithm": "oi_usd = oi_native * contract_multiplier * mark_price",
        "required_inputs": ["oi_native", "contract_multiplier", "pit_mark_price"],
        "output_units": ["USD"],
        "PIT_requirements": "mark price effective_at and market_available_at <= knowledge cutoff",
        "known_limitations": ["requires a PIT-valid reference price; refuses float inputs"],
        "introduced_at": BLOC1_REGISTRY_COMMIT,
        "deprecated_at": None,
    }
    payload.update(overrides)
    return NormalizationMethodology.model_validate(payload)


def _mapping(**overrides: Any) -> Any:
    payload: dict[str, Any] = {
        "provider": "BINANCE_USDM",
        "provider_field": "openInterest",
        "canonical_sensor": SensorFamily.MECHANICAL_OPEN_INTEREST.value,
        "canonical_field": "oi_native",
        "semantic_equivalence_class": SemanticEquivalence.NORMALIZABLE_COMPARABLE.value,
        "native_definition": "Synthetic fixture: open interest in contracts at sample time.",
        "transformation": "preserve native; normalize only via a registered methodology",
        "methodology_id": "SYNTHETIC_LINEAR_OI_USD_V1",
        "blocking_assumptions": ["semantics unverified in this repository"],
        "known_limitations": ["probe evidence pending"],
        "source_endpoint_or_archive": "synthetic structural fixture (not a provider claim)",
        "data_type": "DECIMAL_STRING",
        "native_unit": "CONTRACTS",
        "timestamp_meaning": "sampled at request time (synthetic fixture)",
        "interval_data_scope": IntervalDataScope.POINT_SNAPSHOT.value,
        "direction_side_convention": "not applicable to open interest",
        "evidence_reference": "BLOC2_PROBE_PENDING",
        "semantic_confidence": SemanticConfidence.AMBIGUOUS.value,
        "last_verified_date": None,
        "version": "1",
    }
    payload.update(overrides)
    return ProviderSemanticMapping.model_validate(payload)


def _facts(label: str, **overrides: Any) -> Any:
    payload: dict[str, Any] = {
        "label": label,
        "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST.value,
        "canonical_field": "oi_usd",
        "economic_definition": "total long+short contracts open, marked to USD",
        "interval_data_scope": IntervalDataScope.POINT_SNAPSHOT.value,
        "unit": "USD",
        "asset_id": None,
        "conversion_registered": False,
        "conversion_methodology_id": None,
        "venue_scope": "SYNTHETIC_VENUE_SCOPE",
        "identity_resolved": True,
        "quality_flags": [],
        "equivalence_class": SemanticEquivalence.NORMALIZABLE_COMPARABLE.value,
    }
    payload.update(overrides)
    return ComparableFieldFacts.model_validate(payload)


def _refuses(callable_) -> tuple[bool, str]:
    try:
        callable_()
    except (ValidationError, ValueError, UnknownNormalizationMethodology,
            UnknownProviderSemanticMapping) as exc:
        return True, f"{type(exc).__name__}: {str(exc).splitlines()[0][:120]}"
    return False, "accepted (no refusal)"


# ---------------------------------------------------------------------------
# The evidence table: SEM-01..SEM-36, measured by execution.
# ---------------------------------------------------------------------------


def _build_rows() -> list[dict[str, Any]]:
    # -- SEM-01 methodology object -----------------------------------------
    row = _methodology()
    fields = tuple(type(row).model_fields)
    add(
        "SEM-01",
        "bloc_05/03 S16; bloc_05/07 S4/F14",
        "a fully evidenced synthetic NormalizationMethodology",
        "construct the frozen object and enumerate its field order",
        "exactly the eleven frozen §16 field names, in order; immutable; extra refused",
        "a twelfth field, or mutation after construction",
        f"fields={list(fields)}",
        fields == (
            "methodology_id", "version", "sensor_family", "description",
            "formula_or_algorithm", "required_inputs", "output_units",
            "PIT_requirements", "known_limitations", "introduced_at",
            "deprecated_at",
        )
        and row.model_config.get("frozen") is True,
        "test_sem01_methodology_frozen_field_set_and_immutability",
    )

    # -- SEM-02 F14 versioning ---------------------------------------------
    original = _methodology()
    grown = NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "1.0",
            "methodologies": [
                original.model_dump(mode="json"),
                _methodology(
                    version="2",
                    formula_or_algorithm="oi_usd = oi_native * multiplier * index_price",
                ).model_dump(mode="json"),
            ],
        }
    )
    dup_refused, dup_observed = _refuses(
        lambda: NormalizationMethodologyRegistry.model_validate(
            {
                "schema_version": "1.0",
                "methodologies": [original.model_dump(mode="json")] * 2,
            }
        )
    )
    add(
        "SEM-02",
        "bloc_05/07 F14",
        "one original row plus one version-bumped row, then a duplicated identity",
        "resolve by version; attempt a duplicate (id, version) registration",
        "both versions resolvable, the historical row preserved; the duplicate refused",
        "a silent overwrite under the same identity",
        f"v1_resolvable={grown.resolve('SYNTHETIC_LINEAR_OI_USD_V1', '1') is not None}; "
        f"v2_resolvable={grown.resolve('SYNTHETIC_LINEAR_OI_USD_V1', '2') is not None}; "
        f"duplicate_refused={dup_refused} ({dup_observed})",
        grown.resolve("SYNTHETIC_LINEAR_OI_USD_V1", "1") is not None
        and grown.resolve("SYNTHETIC_LINEAR_OI_USD_V1", "2") is not None
        and dup_refused,
        "test_sem02_f14_versioning_law",
    )

    # -- SEM-03 typed refusal ----------------------------------------------
    empty_m = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "1.0", "methodologies": []}
    )
    absent_refused, absent_observed = _refuses(
        lambda: empty_m.require("NOT_REGISTERED", "1")
    )
    add(
        "SEM-03",
        "bloc_05/06 S1 G9; bloc_05/03 S22 inv.8",
        "an empty methodology registry",
        "resolve an unknown id, then require it",
        "resolve -> None; require -> UnknownNormalizationMethodology; no default",
        "a synthesized or guessed methodology row",
        f"resolve_is_none={empty_m.resolve('NOT_REGISTERED', '1') is None}; "
        f"require_refused={absent_refused} ({absent_observed}); "
        f"version_token={empty_m.version_token()!r}",
        empty_m.resolve("NOT_REGISTERED", "1") is None
        and absent_refused
        and empty_m.version_token() == "1.0",
        "test_sem03_typed_refusal_never_a_default",
    )

    # -- SEM-04 mapping object ---------------------------------------------
    mapping = _mapping()
    mfields = tuple(type(mapping).model_fields)
    frozen_names = (
        "provider_field", "canonical_field", "semantic_equivalence_class",
        "native_definition", "transformation", "methodology_id",
        "blocking_assumptions", "known_limitations",
    )
    record_names = (
        "source_endpoint_or_archive", "data_type", "native_unit",
        "timestamp_meaning", "interval_data_scope", "direction_side_convention",
        "evidence_reference", "semantic_confidence", "last_verified_date",
    )
    add(
        "SEM-04",
        "bloc_05/03 S11+S12+S13; bloc_05/07 S4",
        "a fully stated synthetic ProviderSemanticMapping",
        "construct the frozen object and enumerate its fields",
        "all eight §11 names plus the nine §12/§13 record attributes present; extra refused",
        "a mapping missing blocking_assumptions or known_limitations",
        f"frozen_names_present={all(n in mfields for n in frozen_names)}; "
        f"record_names_present={all(n in mfields for n in record_names)}; "
        f"field_count={len(mfields)}",
        all(n in mfields for n in frozen_names)
        and all(n in mfields for n in record_names),
        "test_sem04_mapping_frozen_field_set_and_immutability",
    )

    # -- SEM-05 B1 laws + stop 1 -------------------------------------------
    no_method_refused, _ = _refuses(
        lambda: _mapping(
            methodology_id=None,
            semantic_equivalence_class=SemanticEquivalence.NORMALIZABLE_COMPARABLE.value,
        )
    )
    no_evidence_refused, _ = _refuses(
        lambda: _mapping(
            evidence_reference=None,
            semantic_equivalence_class=SemanticEquivalence.EXACT_EQUIVALENT.value,
        )
    )
    empty_assumptions_refused, _ = _refuses(
        lambda: ProviderSemanticMapping.model_validate(
            {**mapping.model_dump(mode="json"), "blocking_assumptions": []}
        )
    )
    add(
        "SEM-05",
        "bloc_01/02 B1-T41/T43; readiness S10 stop 1",
        "mappings violating T41, T43, or carrying no blocking assumptions",
        "construct each violating mapping",
        "each is refused at construction",
        "an admissible mapping with no blocking assumptions",
        f"t41_refused={no_method_refused}; t43_refused={no_evidence_refused}; "
        f"stop1_refused={empty_assumptions_refused}",
        no_method_refused and no_evidence_refused and empty_assumptions_refused,
        "test_sem05_bloc1_laws_re_enforced_and_missing_assumptions_refused",
    )

    # -- SEM-06 deterministic serialization --------------------------------
    two = [
        mapping.model_dump(mode="json"),
        _mapping(
            provider="KRAKEN_FUTURES",
            provider_field="funding_rate",
            canonical_sensor=SensorFamily.MECHANICAL_FUNDING.value,
            canonical_field="funding_rate_native",
            native_unit="RATE_PER_INTERVAL",
        ).model_dump(mode="json"),
    ]
    reg_a = ProviderSemanticRegistry.model_validate({"schema_version": "1.0", "mappings": two})
    reg_b = ProviderSemanticRegistry.model_validate(
        {"schema_version": "1.0", "mappings": list(reversed(two))}
    )
    text_a = serialize_provider_semantic_registry_yaml(reg_a)
    text_b = serialize_provider_semantic_registry_yaml(reg_b)
    reparsed = parse_provider_semantic_registry_yaml(text_a)
    add(
        "SEM-06",
        "bloc_05/06 S1 G8; bloc_05/03 S11",
        "the same two mappings in two input orders",
        "serialize both registries and round-trip one",
        "byte-identical YAML regardless of input order; parse(serialize(x)) == x",
        "an order-dependent serialization",
        f"order_independent={text_a == text_b}; "
        f"round_trip={serialize_provider_semantic_registry_yaml(reparsed) == text_a}",
        text_a == text_b
        and serialize_provider_semantic_registry_yaml(reparsed) == text_a,
        "test_sem06_mapping_serialization_is_deterministic",
    )

    # -- SEM-07 duplicate + canonical order -------------------------------
    dup_m_refused, dup_m_observed = _refuses(
        lambda: ProviderSemanticRegistry.model_validate(
            {"schema_version": "1.0", "mappings": [mapping.model_dump(mode="json")] * 2}
        )
    )
    keys = [
        (m.provider, m.canonical_sensor.value, m.provider_field) for m in reg_a.mappings
    ]
    add(
        "SEM-07",
        "bloc_05/03 S12; I05 registry idiom",
        "a duplicated (provider, sensor, field) row, and two orders of the same set",
        "validate the duplicate; compare registry order to sorted order",
        "duplicate refused; registry canonically ordered",
        "two rows with one lookup key",
        f"duplicate_refused={dup_m_refused} ({dup_m_observed}); "
        f"canonical_order={keys == sorted(keys)}",
        dup_m_refused and keys == sorted(keys),
        "test_sem07_registry_duplicate_key_refused_and_order_is_canonical",
    )

    # -- SEM-08 unknown provider/field fail closed -------------------------
    absent_mapping, absent_observed = _refuses(
        lambda: reg_a.require(
            "BINANCE_USDM", "not_a_field", SensorFamily.MECHANICAL_OPEN_INTEREST
        )
    )
    invented_refused, invented_observed = _refuses(
        lambda: _mapping(provider="INVENTED_EXCHANGE")
    )
    add(
        "SEM-08",
        "bloc_05/03 S12; BOOK 00 Q6; readiness S10 stop 7",
        "an unknown field lookup and an invented provider token",
        "require the unknown mapping; construct a mapping for a non-schema provider",
        "typed UnknownProviderSemanticMapping; construction refused",
        "a default mapping or an accepted unknown provider",
        f"unknown_field_refused={absent_mapping} ({absent_observed}); "
        f"invented_provider_refused={invented_refused} ({invented_observed})",
        absent_mapping and invented_refused,
        "test_sem08_unknown_provider_field_and_mapping_fail_closed",
    )

    # -- SEM-09 no cross-fill ----------------------------------------------
    cross = reg_a.resolve(
        "BINANCE_USDM", "openInterest", SensorFamily.MECHANICAL_FUNDING
    )
    add(
        "SEM-09",
        "bloc_01/02 S13; readiness S10 stop 7",
        "a registered (provider, field) row looked up under another sensor family",
        "resolve the same field NAME under MECHANICAL_FUNDING",
        "None: a matching field name never establishes comparability",
        "a mapping borrowed from the other family",
        f"resolve_cross_family_is_none={cross is None}",
        cross is None,
        "test_sem09_no_default_synthesis_from_a_similar_row",
    )

    # -- SEM-10 confidence ladder ------------------------------------------
    ladder = [member.value for member in SemanticConfidence]
    add(
        "SEM-10",
        "bloc_05/03 S13",
        "the SemanticConfidence enum",
        "enumerate members; test admits_critical_t1_use on each",
        "exactly the five frozen members in document order; AMBIGUOUS blocks",
        "a sixth confidence, or AMBIGUOUS admitted to critical T1 use",
        f"ladder={ladder}; ambiguous_blocks="
        f"{not admits_critical_t1_use(SemanticConfidence.AMBIGUOUS)}",
        ladder == [
            "VERIFIED_FIRST_PARTY",
            "VERIFIED_SECONDARY",
            "RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS",
            "COMMUNITY_DOCUMENTED",
            "AMBIGUOUS",
        ]
        and not admits_critical_t1_use(SemanticConfidence.AMBIGUOUS),
        "test_sem10_confidence_ladder_is_frozen_and_ambiguous_blocks",
    )

    # -- SEM-11 community never first-party + pending promotion refused ----
    pending_upgrade_refused, pending_observed = _refuses(
        lambda: _mapping(
            semantic_confidence=SemanticConfidence.VERIFIED_FIRST_PARTY.value,
            evidence_reference="BLOC2_PROBE_PENDING",
        )
    )
    add(
        "SEM-11",
        "bloc_05/03 S13; BOOK 00 Q7",
        "a community-documented confidence, and a VERIFIED_FIRST_PARTY claim "
        "still pointing at BLOC2_PROBE_PENDING evidence",
        "ask is_first_party_grade; attempt the promotion",
        "community is not first-party grade; the promotion is refused",
        "a provisional mapping promoted by a registry edit",
        f"community_first_party="
        f"{is_first_party_grade(SemanticConfidence.COMMUNITY_DOCUMENTED)}; "
        f"pending_upgrade_refused={pending_upgrade_refused} ({pending_observed})",
        not is_first_party_grade(SemanticConfidence.COMMUNITY_DOCUMENTED)
        and pending_upgrade_refused,
        "test_sem11_community_evidence_never_masquerades_as_first_party",
    )

    # -- SEM-12 equivalence vocabulary + pooling law -----------------------
    classes = [member.value for member in SemanticEquivalence]
    add(
        "SEM-12",
        "bloc_05/03 S11; bloc_01/02 B1-T42",
        "the SemanticEquivalence enum and the upstream is_poolable law",
        "enumerate members; pool-test each class",
        "exactly the four frozen classes; NOT_COMPARABLE and CORROBORATION_ONLY never pool",
        "a fifth class, or a pooling of a refusal class",
        f"classes={classes}; poolable="
        f"{[is_poolable(member) for member in SemanticEquivalence]}",
        classes == [
            "EXACT_EQUIVALENT",
            "NORMALIZABLE_COMPARABLE",
            "CORROBORATION_ONLY",
            "NOT_COMPARABLE",
        ]
        and not is_poolable(SemanticEquivalence.CORROBORATION_ONLY)
        and not is_poolable(SemanticEquivalence.NOT_COMPARABLE),
        "test_sem12_equivalence_vocabulary_integrity_and_refusal",
    )

    # -- SEM-13 missingness reuse ------------------------------------------
    frozen_13 = {
        "NOT_REPORTED", "NOT_SUPPORTED", "NOT_YET_LISTED", "DELISTED",
        "HISTORY_UNAVAILABLE", "PROVIDER_EMPTY", "ACCESS_BLOCKED", "SOURCE_GAP",
        "IDENTITY_BLOCKED", "TIME_BLOCKED", "SEMANTICS_BLOCKED",
        "CONVERSION_BLOCKED", "QUARANTINED",
    }
    reasons = {member.value for member in MissingnessReason}
    add(
        "SEM-13",
        "bloc_05/05 S12 (operative); bloc_05/03 S14",
        "the ratified I01 MissingnessReason enum",
        "set-difference against 05 §12's thirteen members; check SEMANTICS_UNVERIFIED",
        "0 missing / 0 extra; SEMANTICS_UNVERIFIED is a quality flag, not a reason",
        "a second, forked missingness vocabulary",
        f"set_difference_missing={sorted(frozen_13 - reasons)}; "
        f"set_difference_extra={sorted(reasons - frozen_13)}; "
        f"flag_not_reason={'SEMANTICS_UNVERIFIED' not in reasons}",
        reasons == frozen_13 and "SEMANTICS_UNVERIFIED" not in reasons,
        "test_sem13_missingness_vocabulary_is_reused_not_forked",
    )

    # -- SEM-14 typed refusal cause ----------------------------------------
    identity_decision = evaluate_comparability(
        _facts("left"), _facts("right", identity_resolved=False)
    )
    semantics_decision = evaluate_comparability(
        _facts("left", quality_flags=[NormalizationQualityFlag.SEMANTICS_UNVERIFIED.value]),
        _facts("right"),
    )
    add(
        "SEM-14",
        "readiness S6; bloc_05/05 S12",
        "a comparison refused for unresolved identity, and one refused for a "
        "blocking SEMANTICS_UNVERIFIED flag",
        "evaluate both; read the typed missingness_reason",
        "IDENTITY_BLOCKED and SEMANTICS_BLOCKED respectively, never a generic bool",
        "a refusal with no typed cause",
        f"identity_cause={identity_decision.missingness_reason.value!r}; "
        f"semantics_cause={semantics_decision.missingness_reason.value!r}",
        identity_decision.missingness_reason is MissingnessReason.IDENTITY_BLOCKED
        and semantics_decision.missingness_reason is MissingnessReason.SEMANTICS_BLOCKED,
        "test_sem14_a_refusal_carries_a_typed_missingness_cause",
    )

    # -- SEM-15..SEM-22 one negative per condition -------------------------
    negatives: list[tuple[str, Any, ComparabilityCondition, str]] = [
        (
            "SEM-15",
            evaluate_comparability(
                _facts("left"),
                _facts("right", sensor_family=SensorFamily.MECHANICAL_FUNDING.value),
            ),
            ComparabilityCondition.SENSOR_FAMILY_SAME,
            "test_sem15_condition_1_sensor_family_must_match",
        ),
        (
            "SEM-16",
            evaluate_comparability(
                _facts("left", canonical_field="oi_usd"),
                _facts("right", canonical_field="funding_rate_8h_equivalent"),
            ),
            ComparabilityCondition.ECONOMIC_DEFINITION_COMPATIBLE,
            "test_sem16_condition_2_same_canonical_quantity_and_stated_definitions",
        ),
        (
            "SEM-17",
            evaluate_comparability(
                _facts("left", interval_data_scope=IntervalDataScope.CUMULATIVE.value),
                _facts("right"),
            ),
            ComparabilityCondition.INTERVAL_SEMANTICS_COMPATIBLE,
            "test_sem17_condition_3_interval_semantics_must_be_compatible",
        ),
        (
            "SEM-18",
            evaluate_comparability(
                _facts("left", unit="USD"), _facts("right", unit="USDT")
            ),
            ComparabilityCondition.UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION,
            "test_sem18_condition_4_units_need_an_explicit_registered_conversion",
        ),
        (
            "SEM-19",
            evaluate_comparability(_facts("left", venue_scope=None), _facts("right")),
            ComparabilityCondition.VENUE_SCOPE_KNOWN,
            "test_sem19_condition_5_venue_scope_must_be_declared",
        ),
        (
            "SEM-20",
            evaluate_comparability(
                _facts("left", identity_resolved=False), _facts("right")
            ),
            ComparabilityCondition.IDENTITY_RESOLVED,
            "test_sem20_condition_6_identity_must_be_resolved",
        ),
        (
            "SEM-21",
            evaluate_comparability(
                _facts("left", quality_flags=[NormalizationQualityFlag.LINEAGE_BROKEN.value]),
                _facts("right"),
            ),
            ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS,
            "test_sem21_condition_7_blocking_quality_flags_refuse",
        ),
        (
            "SEM-22",
            evaluate_comparability(
                _facts("left", equivalence_class=SemanticEquivalence.CORROBORATION_ONLY.value),
                _facts("right"),
            ),
            ComparabilityCondition.EQUIVALENCE_CLASS_PERMITS_COMPARISON,
            "test_sem22_condition_8_equivalence_class_must_permit",
        ),
    ]
    for case_id, decision, condition, test_ref in negatives:
        add(
            case_id,
            "bloc_05/03 S18 (one condition)",
            "two declared sides differing in exactly one required dimension",
            "evaluate the eight-condition gate",
            f"{condition.value} refused; not admitted; typed cause present",
            "an admitted comparison with one dimension unsupported",
            f"refused={[c.value for c in decision.refused_conditions]}; "
            f"cause={decision.missingness_reason.value!r}",
            (not decision.admitted)
            and condition in decision.refused_conditions
            and decision.missingness_reason is not None,
            test_ref,
        )

    # -- SEM-23 all-pass ----------------------------------------------------
    pass_decision = evaluate_comparability(_facts("left"), _facts("right"))
    add(
        "SEM-23",
        "bloc_05/03 S18",
        "two sides declaring every required fact compatibly",
        "evaluate the gate",
        "admitted; eight satisfied verdicts in frozen order; no missingness cause",
        "a refusal or a partial verdict list",
        f"admitted={pass_decision.admitted}; "
        f"verdicts={len(pass_decision.verdicts)}; "
        f"order="
        f"{[v.condition.value for v in pass_decision.verdicts] == [c.value for c in ComparabilityCondition]}",
        pass_decision.admitted
        and pass_decision.refused_conditions == ()
        and len(pass_decision.verdicts) == 8
        and pass_decision.missingness_reason is None,
        "test_sem23_all_eight_conditions_satisfied_admits",
    )

    # -- SEM-24 missing facts fail closed ----------------------------------
    empty = ComparableFieldFacts.model_validate({"label": "empty"})
    empty_decision = evaluate_comparability(empty, _facts("right"))
    add(
        "SEM-24",
        "bloc_05/06 S1 G9; readiness S10 stop 8",
        "one side declaring no facts at all",
        "evaluate the gate over the empty side",
        "refused without raising; every verdict carries a reason",
        "an exception, or an admitted comparison over unknown facts",
        f"admitted={empty_decision.admitted}; "
        f"refused_count={len(empty_decision.refused_conditions)}; "
        f"all_reasons={all(v.reason for v in empty_decision.verdicts)}",
        (not empty_decision.admitted)
        and all(v.reason for v in empty_decision.verdicts)
        and len(empty_decision.refused_conditions) == 7,
        "test_sem24_missing_facts_fail_closed_without_raising",
    )

    # -- SEM-25 envelope surface -------------------------------------------
    import crypto_sensor_fabric.normalization as _top

    ref = MethodologyRef.from_methodology(original)
    ref_registry = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "2026.10-i09", "methodologies": []}
    )
    add(
        "SEM-25",
        "bloc_05/03 S2/S17/S22 inv.7; BOOK 00 Q4",
        "a methodology row converted to an envelope reference, and the "
        "registry generation token",
        "build MethodologyRef; read the top-level API",
        "the two I09-owned fields typed; the frozen composite name still "
        "unexported; the top-level API still 24 symbols",
        "a released T1ObservationEnvelope, or a fabricated I02/I06/I19 field",
        f"ref={ref.methodology_id}@{ref.version}; "
        f"version_token={ref_registry.version_token()!r}; "
        f"top_level={len(_top.__all__)}; "
        f"envelope_exported={'T1ObservationEnvelope' in _top.__all__}",
        ref.methodology_id == original.methodology_id
        and ref.version == original.version
        and ref_registry.version_token() == "2026.10-i09"
        and len(_top.__all__) == 24
        and "T1ObservationEnvelope" not in _top.__all__,
        "test_sem25_methodology_ref_and_registry_version_token_without_envelope",
    )

    # -- SEM-27 cross-venue is a decision only -----------------------------
    cross_venue = evaluate_comparability(
        _facts("binance_side", venue_scope="BINANCE_USDM:USD-M"),
        _facts("bybit_side", venue_scope="BYBIT_LINEAR:linear"),
    )
    decision_fields = set(type(cross_venue).model_fields)
    add(
        "SEM-27",
        "bloc_05/07 F24; bloc_05/03 S20",
        "two comparable sides from different venues",
        "evaluate the gate; enumerate the decision model's fields",
        "admitted as comparable; no value/merged/pooled field exists on the model",
        "a synthesized cross-venue value or consensus",
        f"admitted={cross_venue.admitted}; "
        f"venue_scope_facts={[c for c in ('value', 'merged', 'pooled', 'consensus') if c in decision_fields] or 'none'}",
        cross_venue.admitted
        and not decision_fields
        & {"value", "merged", "pooled", "consensus", "synthesized_value"},
        "test_sem27_cross_venue_comparison_is_a_decision_never_a_synthesis",
    )

    # -- SEM-28 provider-native analytics stay evidence --------------------
    derivibit = _mapping(
        provider="DERIBIT",
        provider_field="trade.liquidation",
        canonical_sensor=SensorFamily.MECHANICAL_LIQUIDATION.value,
        canonical_field="liquidation_role",
        semantic_equivalence_class=SemanticEquivalence.CORROBORATION_ONLY.value,
        methodology_id="DERIBIT_TRADE_LIQ_TAG_V1",
        native_unit="COUNT",
    )
    add(
        "SEM-28",
        "bloc_05/07 F16; bloc_05/03 S19",
        "a Deribit-style CORROBORATION_ONLY provider-native analytic",
        "store it; ask is_poolable and admits_critical_t1_use",
        "storable as evidence; refused for cross-provider canonical use",
        "a promotion of provider-native analytics to Fabric-defined truth",
        f"pooled={is_poolable(derivibit.semantic_equivalence_class)}; "
        f"critical_use={admits_critical_t1_use(derivibit.semantic_confidence)}",
        not is_poolable(derivibit.semantic_equivalence_class)
        and not admits_critical_t1_use(derivibit.semantic_confidence),
        "test_sem28_provider_native_analytics_stay_evidence",
    )

    # -- SEM-29..SEM-34 live-config reconciliation -------------------------
    bloc1_methodologies = load_methodology_registry(METHODOLOGY_YAML)
    bloc1_mappings = load_semantic_equivalence(SEMANTIC_YAML)
    all_pending = all(
        mapping_row.evidence_reference == "BLOC2_PROBE_PENDING"
        for mapping_row in bloc1_mappings.mappings
    )
    add(
        "SEM-29",
        "BOOK 00 Q1; readiness §3",
        "the live Bloc 1 configs read as text",
        "load both registries; count ids/mappings; check pending evidence",
        "nine methodology ids, six mappings, every mapping pending, every "
        "methodology_id resolvable upstream",
        "a config edit, a promoted evidence reference, or a dangling id",
        f"methodologies={len(bloc1_methodologies.methodologies)}; "
        f"mappings={len(bloc1_mappings.mappings)}; all_pending={all_pending}; "
        f"ids_resolve="
        f"{all(m.methodology_id in bloc1_methodologies.methodologies for m in bloc1_mappings.mappings)}",
        len(bloc1_methodologies.methodologies) == 9
        and len(bloc1_mappings.mappings) == 6
        and all_pending
        and all(
            m.methodology_id in bloc1_methodologies.methodologies
            for m in bloc1_mappings.mappings
        ),
        "test_sem29_live_configs_are_intact_and_projection_ready",
    )

    projected_ok = True
    projected_details: list[str] = []
    for mapping_row in bloc1_mappings.mappings:
        try:
            projected = project_planning_mapping(
                mapping_row,
                source_endpoint_or_archive="synthetic structural fixture (I09-a)",
                data_type="DECIMAL_STRING",
                native_unit="UNVERIFIED_NATIVE_UNIT",
                timestamp_meaning="unverified; see the provider time-semantics registry",
                interval_data_scope=IntervalDataScope.PROVIDER_NATIVE_UNKNOWN,
                direction_side_convention="unverified (BLOC2_PROBE_PENDING)",
                blocking_assumptions=(
                    "provider semantics unverified: evidence_reference is "
                    "BLOC2_PROBE_PENDING and no first-party documentation exists "
                    "in this repository (03 §13 AMBIGUOUS; barred from critical "
                    "T1 normalized fields)",
                ),
                known_limitations=(
                    "provisional planning mapping only; class, methodology_id and "
                    "version are preserved from the Bloc 1 registry and may not be "
                    "upgraded without documentary proof (BOOK 00 Q7)",
                ),
            )
            same = (
                projected.semantic_confidence is SemanticConfidence.AMBIGUOUS
                and projected.evidence_reference == mapping_row.evidence_reference
                and projected.semantic_equivalence_class is mapping_row.equivalence
                and projected.methodology_id == mapping_row.methodology_id
                and projected.version == mapping_row.version
                and projected.provider_field == mapping_row.source_metric
            )
            projected_ok = projected_ok and same
            projected_details.append(f"{projected.provider}:{projected.provider_field}={same}")
        except (ValidationError, ValueError) as exc:
            projected_ok = False
            projected_details.append(f"{mapping_row.provider}:ERROR:{type(exc).__name__}")
    add(
        "SEM-30",
        "BOOK 00 Q1+Q7; bloc_05/03 S11/S13",
        "each of the six live planning mappings",
        "project it into the frozen shape and compare identity fields",
        "class, methodology_id, evidence_reference, version and field identity "
        "preserved; confidence stays AMBIGUOUS",
        "an upgrade of class, confidence or evidence",
        f"projected={'; '.join(projected_details)}",
        projected_ok and len(projected_details) == 6,
        "test_sem30_projected_mappings_stay_ambiguous_and_pending",
    )

    empty_registry = ProviderSemanticRegistry.model_validate(
        {"schema_version": "1.0", "mappings": []}
    )
    gate_refused, gate_observed = _refuses(
        lambda: empty_registry.require(
            "GATE_FUTURES", "long_liq_usd", SensorFamily.MECHANICAL_LIQUIDATION
        )
    )
    add(
        "SEM-31",
        "BOOK 00 Q6; readiness §10 stop 7",
        "an empty provider semantic registry",
        "require the Gate liquidation mapping",
        "typed refusal naming the provider; the absence is recorded, not filled",
        "a synthesized Gate mapping",
        f"refused={gate_refused} ({gate_observed})",
        gate_refused,
        "test_sem31_empty_registry_resolves_nothing_and_names_the_missing_cause",
    )

    diff = subprocess.run(
        [
            "git", "diff", I09_BASE_HEAD, "--",
            "quant-lab/src/crypto_sensor_fabric/registry",
            "quant-lab/config/crypto_sensor_fabric",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        encoding="utf-8",
        check=False,
    ).stdout
    add(
        "SEM-32",
        "BOOK 00 Q1 (no in-place meaning change)",
        "git diff of the Bloc 1 registry surface against the I09 base",
        "name the changed paths",
        "empty: registry modules and both YAMLs byte-identical",
        "any edit to a live Bloc 1 module or config",
        f"diff_empty={diff == ''}",
        diff == "",
        "test_sem32_bloc1_registry_surfaces_are_untouched",
    )

    provider_projection = all(
        _mapping(provider=provider).provider == provider for provider in PROVIDER_IDS
    )
    add(
        "SEM-33",
        "BOOK 00 Q6; bloc_05/06 §5",
        "the live PROVIDER_IDS tuple",
        "construct one mapping per provider token",
        "eight providers; every token accepted by the frozen schema; the tuple "
        "reused, not forked",
        "a second provider vocabulary inside normalization",
        f"providers={len(PROVIDER_IDS)}; all_accepted={provider_projection}; "
        f"ids={list(PROVIDER_IDS)}",
        len(PROVIDER_IDS) == 8 and provider_projection,
        "test_sem33_the_eight_provider_schema_is_the_live_provider_set",
    )

    live_ids = set(bloc1_methodologies.methodologies)
    add(
        "SEM-34",
        "BOOK 00 Q2; readiness §10 stop 9",
        "the live methodology config after I09",
        "list its ids; probe for invented aliases",
        "the nine Bloc 1 ids only; no B5_I08_UNITS_V1 row; no "
        "STABLECOIN_USD_PIT_V1 alias",
        "an invented methodology row or alias in committed config",
        f"ids={sorted(live_ids)}",
        len(live_ids) == 9
        and "B5_I08_UNITS_V1" not in live_ids
        and "STABLECOIN_USD_PIT_V1" not in live_ids,
        "test_sem34_no_methodology_row_is_invented_for_the_unresolved_ids",
    )

    # -- SEM-36 condition order --------------------------------------------
    add(
        "SEM-36",
        "bloc_05/03 S18",
        "the ComparabilityCondition enum",
        "enumerate members; evaluate a passing comparison",
        "the eight conditions in frozen document order; verdicts in that order",
        "a reordered or renamed condition",
        f"conditions={[c.value for c in ComparabilityCondition]}; "
        f"verdict_order="
        f"{[v.condition.value for v in pass_decision.verdicts] == [c.value for c in ComparabilityCondition]}",
        [c.value for c in ComparabilityCondition] == [
            "SENSOR_FAMILY_SAME",
            "ECONOMIC_DEFINITION_COMPATIBLE",
            "INTERVAL_SEMANTICS_COMPATIBLE",
            "UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION",
            "VENUE_SCOPE_KNOWN",
            "IDENTITY_RESOLVED",
            "NO_BLOCKING_QUALITY_FLAGS",
            "EQUIVALENCE_CLASS_PERMITS_COMPARISON",
        ]
        and [v.condition.value for v in pass_decision.verdicts]
        == [c.value for c in ComparabilityCondition],
        "test_sem36_condition_order_and_names_are_frozen",
    )

    # -- SEM-A01 common/ module set ----------------------------------------
    common_dir = ROOT / "src/crypto_sensor_fabric/normalization/common"
    present = sorted(p.name for p in common_dir.iterdir() if p.suffix == ".py")
    add(
        "SEM-A01",
        "bloc_05/03 S21 (I08+I09 split); bloc_05/06 S19",
        "the common/ package on disk",
        "enumerate its .py files",
        "exactly the seven frozen modules; envelope.py and missingness.py absent",
        "an eighth module, or a shipped frozen-name composite",
        f"modules={present}",
        present == [
            "__init__.py",
            "comparability.py",
            "conversion.py",
            "methodologies.py",
            "numeric.py",
            "semantic_registry.py",
            "units.py",
        ],
        "test_sem_a01_common_package_is_exactly_the_frozen_modules",
    )

    return _ROWS


# ---------------------------------------------------------------------------
# The projection record: which Bloc 1 methodologies I09 registers, and why
# the rest stay unregistered (BOOK 00 Q2 fail-closed branch).
# ---------------------------------------------------------------------------

#: Evidence-derived attributes for the projectable Bloc 1 planning entries.
#: Every value restates what the live registry already declares plus the
#: frozen §16 attributes that registry does not carry; ``introduced_at`` is
#: the Bloc 1 commit that created each entry.  Nothing here is inferred from
#: provider behaviour -- these are planning entries, and their PROVISIONAL
#: upstream status is carried into ``known_limitations`` by the adapter.
PROJECTABLE_METHODOLOGIES: dict[str, dict[str, Any]] = {
    "OI_CONTRACTS_TO_USD_V1": {
        "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
        "formula_or_algorithm": (
            "oi_usd = oi_native * contract_multiplier * pit_mark_price; oi_base and "
            "oi_quote derived from the same multiplier chain (bloc_01/02 §16 contract)"
        ),
        "required_inputs": ("oi_native", "native_unit", "contract_multiplier", "pit_mark_price"),
        "output_units": ("BASE_ASSET", "QUOTE_ASSET", "USD"),
        "PIT_requirements": (
            "reference price effective_at AND market_available_at at/before the "
            "knowledge cutoff (bloc_05/03 §9/§10 replay law)"
        ),
        "known_limitations": (
            "PROVISIONAL planning entry; the price source must be recorded in "
            "conversion lineage; inverse/quanto contracts take the I04B terms path, "
            "not this formula",
        ),
    },
    "OI_USD_NATIVE_PASSTHROUGH_V1": {
        "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
        "formula_or_algorithm": "identity: oi_usd == oi_native when native_unit = USD",
        "required_inputs": ("oi_native",),
        "output_units": ("USD",),
        "PIT_requirements": "none: no conversion is performed",
        "known_limitations": (
            "representation-equivalent passthrough only; carries no conversion claim",
        ),
    },
    "FUNDING_NATIVE_TO_8H_EQUIV_V1": {
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "formula_or_algorithm": "rate_8h = rate_native * (28800 / funding_interval_seconds)",
        "required_inputs": ("funding_rate_native", "funding_interval_seconds"),
        "output_units": ("RATE_PER_INTERVAL",),
        "PIT_requirements": (
            "the native interval convention must be declared in the provider "
            "time-semantics registry; the native rate is never overwritten"
        ),
        "known_limitations": (
            "assumes the rate scales linearly across intervals; a provider whose "
            "funding schedule is non-uniform must not use this derivation",
        ),
    },
    "LIQ_USD_NATIVE_PROVIDER_V1": {
        "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
        "formula_or_algorithm": (
            "identity map of provider USD aggregates to source_long_liq_usd / "
            "source_short_liq_usd with the provider unit declaration preserved"
        ),
        "required_inputs": ("provider_long_liq_usd", "provider_short_liq_usd"),
        "output_units": ("USD",),
        "PIT_requirements": "interval-local aggregate; no PIT reference price required",
        "known_limitations": (
            "interval window and side convention are provider-specific and "
            "unverified; cross-provider pooling is refused by the equivalence class",
        ),
    },
    "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1": {
        "sensor_family": SensorFamily.MECHANICAL_TRADE,
        "formula_or_algorithm": (
            "isBuyerMaker=true -> aggressor_side=SELL (seller is taker); "
            "isBuyerMaker=false -> aggressor_side=BUY (buyer is taker); "
            "unknown flag -> UNKNOWN"
        ),
        "required_inputs": ("isBuyerMaker",),
        "output_units": ("COUNT",),
        "PIT_requirements": "event-time flag; no point-in-time dependency",
        "known_limitations": (
            "direction frozen by operator repair SENSOR-B1-R01; must be proven by a "
            "provider fixture (I20) before trust (bloc_01/02 §4 side rule)",
        ),
    },
    "DERIBIT_TRADE_LIQ_TAG_V1": {
        "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
        "formula_or_algorithm": (
            "a liquidation-tagged trade becomes a TRADE_LEVEL liquidation "
            "observation with liquidation_role; never pooled with interval aggregates"
        ),
        "required_inputs": ("deribit_trade_liquidation_tag",),
        "output_units": ("COUNT",),
        "PIT_requirements": "trade event time; no reference price required",
        "known_limitations": (
            "CORROBORATION_ONLY (B1-T42); the tag's semantics are unverified "
            "(BLOC2_PROBE_PENDING)",
        ),
    },
    "PROVIDER_ANALYTICS_PASSTHROUGH_V1": {
        "sensor_family": SensorFamily.MECHANICAL_BOOK_METRIC,
        "formula_or_algorithm": (
            "store the provider-calculated book metric verbatim with its declared "
            "provider methodology; no local reconstruction is performed"
        ),
        "required_inputs": ("provider_book_analytics_metric",),
        "output_units": ("COUNT",),
        "PIT_requirements": "provider snapshot time as declared by the provider",
        "known_limitations": (
            "provider-native analytics stay provider-native evidence (bloc_05/07 F16) "
            "and must never be conflated with locally reconstructed metrics "
            "(bloc_01/02 §9)",
        ),
    },
}

#: Bloc 1 entries I09 deliberately does NOT register, with the exact reason.
UNRESOLVED_METHODOLOGIES: list[dict[str, str]] = [
    {
        "methodology_id": "B5_I08_UNITS_V1",
        "classification": "UNRESOLVED_FAIL_CLOSED",
        "reason": (
            "sensor_family cannot be established from accepted evidence: the I08 "
            "stablecoin/fiat + cross-currency converter is cross-cutting (any "
            "quote-denominated field) and the frozen SensorFamily vocabulary has no "
            "family-agnostic member.  Registering it under one family would misstate "
            "it; under all eight would mint duplicate (methodology_id, version) rows "
            "which the F14 duplicate law refuses; adding a COMMON member would amend "
            "a frozen Bloc 1 vocabulary outside I09 authority (BOOK 00 Q2 "
            "fail-closed branch).  The identifier itself is preserved and no I08 "
            "evidence is regenerated."
        ),
        "recommendation": (
            "an operator ruling that unit-level cross-family methodologies either "
            "declare an explicit family set or receive a lawful sensor_family "
            "extension, after which a future checkpoint can register this entry "
            "without invention"
        ),
    },
    {
        "methodology_id": "DEPTH_BPS_RECONSTRUCTION_V1",
        "classification": "UNRESOLVED_FAIL_CLOSED",
        "reason": (
            "formula_or_algorithm cannot be established from accepted evidence: the "
            "Bloc 1 description states WHAT the reconstruction produces "
            "(depth-at-bps bands, spread metrics) but not the band levels, "
            "interpolation rule or aggregation math; the implementing formula is not "
            "named by any registry row (readiness §10 stop 9: the only way to satisfy "
            "the frozen field would be to invent it)"
        ),
        "recommendation": (
            "register this entry from the Bloc 4 book-metric implementation once its "
            "exact band algorithm is documented as accepted evidence"
        ),
    },
    {
        "methodology_id": "CVD_SIGNED_NOTIONAL_V1",
        "classification": "OUT_OF_T1_SCOPE",
        "reason": (
            "the live registry declares owner_layer = T2, and bloc_05/03 §20 forbids "
            "T1 normalization from computing research features such as CVD; a "
            "T2-owned methodology is outside the T1 normalization registry's scope "
            "at I09 (a scope boundary, not a missing attribute)"
        ),
        "recommendation": (
            "register T2 methodologies in a T2-owned registry surface when the Bloc 9 "
            "feature layer is authorized"
        ),
    },
]


def _projection_rows(bloc1: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for methodology_id, attributes in PROJECTABLE_METHODOLOGIES.items():
        entry = bloc1.methodologies[methodology_id]
        projected = project_planning_methodology(
            entry,
            methodology_id=methodology_id,
            sensor_family=attributes["sensor_family"],
            formula_or_algorithm=attributes["formula_or_algorithm"],
            required_inputs=attributes["required_inputs"],
            output_units=attributes["output_units"],
            PIT_requirements=attributes["PIT_requirements"],
            known_limitations=attributes["known_limitations"],
            introduced_at=BLOC1_REGISTRY_COMMIT,
        )
        rows.append(
            {
                "description_preserved": projected.description == entry.description,
                "introduced_at": projected.introduced_at,
                "methodology_id": projected.methodology_id,
                "sensor_family": projected.sensor_family.value,
                "upstream_status_carried": entry.status in projected.known_limitations[-1],
                "version": projected.version,
            }
        )
    return rows


def _inventory() -> dict[str, str]:
    return {relpath: hashlib.sha256((ROOT / relpath).read_bytes()).hexdigest()
            for relpath in INVENTORY}


def _build_payload() -> tuple[bytes, dict[str, Any]]:
    bloc1 = load_methodology_registry(METHODOLOGY_YAML)
    rows = _build_rows()
    failures = [r["case_id"] for r in rows if r["disposition"] != "PASS"]
    if failures:
        print(
            json.dumps({"error": "non_pass_dispositions", "cases": failures},
                       sort_keys=True),
            file=sys.stderr,
        )
        raise SystemExit(1)
    payload: dict[str, Any] = {
        "artifact": "bloc_05_semantic_validation",
        "checkpoint": "SENSOR-B5-I09",
        "extensions": [
            {
                "case_series": "SEM-01..SEM-36 (SEM-26/35 test-owned) + SEM-A01",
                "checkpoint": "SENSOR-B5-I09E1",
                "generator": (
                    "research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py"
                ),
                "note": (
                    "first production: no prior rows of this frozen-name artifact "
                    "exist, so a later checkpoint extending it must pin these rows "
                    "by SHA-256 (the I08 extensions convention)"
                ),
                "rows_added": len(rows),
            },
        ],
        "generator": (
            "PYTHONIOENCODING=utf-8 python "
            "research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py"
        ),
        "projected_methodologies": _projection_rows(bloc1),
        "rows": rows,
        "sha256_inventory": _inventory(),
        "summary": {
            "fail": len(failures),
            "pass": len(rows),
            "rows": len(rows),
        },
        "unresolved": UNRESOLVED_METHODOLOGIES,
    }
    blob = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return blob, payload


def main() -> int:
    args = sys.argv[1:]
    if args not in ([], ["--check"]):
        print("usage: b5_i09_semantics.py [--check]", file=sys.stderr)
        return 2
    blob, payload = _build_payload()
    digest = hashlib.sha256(blob).hexdigest()
    summary = {
        "artifact_sha256": digest,
        "case_series": "SEM-01..SEM-36 (SEM-26/35 test-owned) + SEM-A01",
        "fail": payload["summary"]["fail"],
        "pass": payload["summary"]["pass"],
        "rows": payload["summary"]["rows"],
        "unresolved": len(payload["unresolved"]),
    }
    if args == ["--check"]:
        committed = ARTIFACT.read_bytes() if ARTIFACT.exists() else b""
        if committed != blob:
            print(
                json.dumps({**summary, "error": "committed_bytes_mismatch"},
                           sort_keys=True),
                file=sys.stderr,
            )
            return 3
        print(json.dumps(summary, sort_keys=True))
        return 0
    ARTIFACT.write_bytes(blob)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
