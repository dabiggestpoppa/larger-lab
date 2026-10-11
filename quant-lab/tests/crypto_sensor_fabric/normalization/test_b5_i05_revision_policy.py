"""SENSOR-B5-I05 - RED-first revision policy and AS_KNOWN_THEN selection.

Frozen authority: bloc_05/02 s10 (revision statuses), s11 (the six research
revision modes and the two defined semantics), s12 (provider correction
leakage, ``PIT_REVISION_UNCERTAIN``), s15.4 (revision policy compatible with
the replay cutoff), bloc_05/06 s13 rows 3-4 (late correction / retrospective
mode), scenarios F05-03 and F05-04.

Scope law (I05 directive phase F): the two frozen distinctions are implemented
as PURE selection over caller-supplied revision records.  There is no revision
store, no supersession graph walk and no persistence here -- ``B5-I07`` owns
the revision engine, and building one would be an unauthorized expansion.

Knowledge windows follow the I03 boundary semantics already ratified for
identity: ``known_from <= cutoff < known_to``.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from crypto_sensor_fabric.normalization.time import (
    RevisionMode,
    RevisionPolicy,
    RevisionPolicyCatalog,
    RevisionRecord,
    RevisionSelection,
    RevisionStatus,
    UnsupportedRevisionMode,
    parse_revision_policies_yaml,
    select_revisions,
    serialize_revision_policies_yaml,
)

UTC = timezone.utc
_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "revision_policies.yaml"

CUTOFF_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
KNOWN_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
KNOWN_2025 = datetime(2025, 3, 3, hour=10, tzinfo=UTC)

ORIGINAL = RevisionRecord(
    source_revision_id="rev-oi-2022-original",
    normalization_generation=1,
    supersedes_t1_record_id=None,
    revision_status=RevisionStatus.ORIGINAL,
    known_from=KNOWN_2022,
    known_to=None,
)
CORRECTION = RevisionRecord(
    source_revision_id="rev-oi-2022-corrected-2025",
    normalization_generation=2,
    supersedes_t1_record_id="rev-oi-2022-original",
    revision_status=RevisionStatus.PROVIDER_CORRECTED,
    known_from=KNOWN_2025,
    known_to=None,
)


def _catalog() -> RevisionPolicyCatalog:
    return parse_revision_policies_yaml(CONFIG.read_text(encoding="utf-8"))


def _policy(mode: RevisionMode) -> RevisionPolicy:
    return _catalog().policy_for(mode)


# ---------------------------------------------------------------------------
# The committed configuration IS the frozen vocabulary
# ---------------------------------------------------------------------------


def test_the_frozen_configuration_file_exists() -> None:
    assert CONFIG.is_file(), "bloc_05/02 s17 requires revision_policies.yaml"


def test_committed_configuration_covers_exactly_the_six_frozen_modes() -> None:
    catalog = _catalog()
    assert catalog.schema_version == "1.0"
    assert [policy.mode for policy in catalog.policies] == list(RevisionMode)


def test_every_frozen_mode_resolves_to_a_declared_policy() -> None:
    catalog = _catalog()
    for mode in RevisionMode:
        policy = catalog.policy_for(mode)
        assert policy.mode is mode


def test_the_two_defined_modes_carry_the_verbatim_frozen_definition() -> None:
    catalog = _catalog()
    known_then = catalog.policy_for(RevisionMode.AS_KNOWN_THEN)
    assert known_then.definition == (
        "Select only values/revisions that were available by replay cutoff."
    )
    latest = catalog.policy_for(RevisionMode.LATEST_VERIFIED)
    assert latest.definition == (
        "Useful for retrospective measurement but not automatically PIT-safe."
    )


def test_undefined_modes_carry_no_invented_definition() -> None:
    """s11 names four modes and defines none of them; invention is refused."""
    catalog = _catalog()
    for mode in (
        RevisionMode.FIRST_SEEN,
        RevisionMode.EXACT_REVISION,
        RevisionMode.ALL_REVISIONS,
        RevisionMode.ERROR_ON_AMBIGUITY,
    ):
        assert catalog.policy_for(mode).definition is None


def _without_mode(config_text: str, drop: str) -> str:
    """Remove one complete policy block from the committed configuration."""
    kept: list[str] = []
    skipping = False
    for line in config_text.splitlines(keepends=True):
        if line.startswith("  - mode: "):
            skipping = drop in line
        if not skipping:
            kept.append(line)
    return "".join(kept)


def test_configuration_missing_a_frozen_mode_is_refused() -> None:
    text = _without_mode(CONFIG.read_text(encoding="utf-8"), "FIRST_SEEN")
    assert "FIRST_SEEN" not in text
    with pytest.raises(ValueError):
        parse_revision_policies_yaml(text)


def test_configuration_with_an_unknown_mode_is_refused() -> None:
    text = CONFIG.read_text(encoding="utf-8").replace(
        "mode: FIRST_SEEN", "mode: WHATEVER_WE_LIKE"
    )
    with pytest.raises(ValueError):
        parse_revision_policies_yaml(text)


def test_configuration_with_a_duplicate_mode_is_refused() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    blocks: list[str] = []
    current: list[str] | None = None
    for line in text.splitlines(keepends=True):
        if line.startswith("  - mode: "):
            if current is not None:
                blocks.append("".join(current))
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append("".join(current))
    first_seen = next(block for block in blocks if "FIRST_SEEN" in block)
    poisoned = text + first_seen
    with pytest.raises(ValueError):
        parse_revision_policies_yaml(poisoned)


def test_configuration_with_an_extra_key_is_refused() -> None:
    text = CONFIG.read_text(encoding="utf-8").replace(
        "mode: LATEST_VERIFIED", "mode: LATEST_VERIFIED\n    retro: true"
    )
    with pytest.raises(ValueError):
        parse_revision_policies_yaml(text)


def test_a_defined_mode_without_its_definition_is_refused() -> None:
    text = CONFIG.read_text(encoding="utf-8").replace(
        "Select only values/revisions that were available by replay cutoff.",
        "",
    )
    with pytest.raises(ValueError):
        parse_revision_policies_yaml(text)


def test_catalog_serialization_is_deterministic() -> None:
    catalog = _catalog()
    first = serialize_revision_policies_yaml(catalog)
    second = serialize_revision_policies_yaml(catalog)
    assert first == second
    assert parse_revision_policies_yaml(first) == catalog


# ---------------------------------------------------------------------------
# AS_KNOWN_THEN -- no future correction leaks backward
# ---------------------------------------------------------------------------


def test_as_known_then_excludes_a_later_correction() -> None:
    """F05-03: a 2025 correction must not enter a 2022 replay."""
    selection = select_revisions(
        (ORIGINAL, CORRECTION), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assert selection.selected == (ORIGINAL,)
    assert selection.excluded == (CORRECTION,)
    assert selection.pit_safe is True
    assert selection.pit_uncertain is False


def test_as_known_then_selects_nothing_when_the_original_is_unavailable() -> None:
    """s12: if the original revision is unavailable -> PIT_REVISION_UNCERTAIN."""
    selection = select_revisions(
        (CORRECTION,), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assert selection.selected == ()
    assert selection.excluded == (CORRECTION,)
    assert selection.pit_uncertain is True


def test_as_known_then_of_a_modern_cutoff_sees_the_correction() -> None:
    selection = select_revisions(
        (ORIGINAL, CORRECTION), _policy(RevisionMode.AS_KNOWN_THEN), KNOWN_2025
    )
    assert selection.selected == (ORIGINAL, CORRECTION)


def test_knowledge_window_boundaries_match_the_ratified_i03_semantics() -> None:
    """known_from == cutoff is inside; known_to == cutoff is outside."""
    on_boundary = RevisionRecord(
        source_revision_id="rev-boundary",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=CUTOFF_2022,
        known_to=None,
    )
    closed = RevisionRecord(
        source_revision_id="rev-closed",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=CUTOFF_2022 - timedelta(days=1),
        known_to=CUTOFF_2022,
    )
    one_tick = RevisionRecord(
        source_revision_id="rev-open-one-tick",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=CUTOFF_2022 - timedelta(days=1),
        known_to=CUTOFF_2022 + timedelta(microseconds=1),
    )
    selection = select_revisions(
        (on_boundary, closed, one_tick),
        _policy(RevisionMode.AS_KNOWN_THEN),
        CUTOFF_2022,
    )
    # Ordering is the deterministic (known_from, source_revision_id) order,
    # independent of the order the caller passed the records in.
    assert [record.source_revision_id for record in selection.selected] == [
        "rev-open-one-tick",
        "rev-boundary",
    ]
    assert [record.source_revision_id for record in selection.excluded] == [
        "rev-closed"
    ]


def test_as_known_then_of_an_empty_revision_set_is_uncertain() -> None:
    selection = select_revisions(
        (), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assert selection.selected == ()
    assert selection.pit_uncertain is True
    assert selection.pit_safe is True


def test_selection_order_is_deterministic_not_input_dependent() -> None:
    later_first = RevisionRecord(
        source_revision_id="a-later",
        normalization_generation=2,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.SOURCE_MUTATION_REPARSED,
        known_from=KNOWN_2025,
        known_to=None,
    )
    earlier = RevisionRecord(
        source_revision_id="b-earlier",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=KNOWN_2022,
        known_to=None,
    )
    forward = select_revisions(
        (later_first, earlier), _policy(RevisionMode.AS_KNOWN_THEN), KNOWN_2025
    )
    backward = select_revisions(
        (earlier, later_first), _policy(RevisionMode.AS_KNOWN_THEN), KNOWN_2025
    )
    assert forward.selected == backward.selected
    assert forward.selected == (earlier, later_first)


# ---------------------------------------------------------------------------
# LATEST_VERIFIED -- explicitly retrospective, never silently PIT-safe
# ---------------------------------------------------------------------------


def test_latest_verified_selects_the_correction_explicitly() -> None:
    """F05-04: the retrospective mode may select a verified correction."""
    selection = select_revisions(
        (ORIGINAL, CORRECTION), _policy(RevisionMode.LATEST_VERIFIED), CUTOFF_2022
    )
    assert selection.selected == (CORRECTION,)
    assert selection.excluded == (ORIGINAL,)
    assert selection.pit_safe is False
    assert selection.pit_uncertain is False
    assert selection.mode is RevisionMode.LATEST_VERIFIED


def test_latest_verified_never_claims_pit_safety_even_with_no_correction() -> None:
    selection = select_revisions(
        (ORIGINAL,), _policy(RevisionMode.LATEST_VERIFIED), CUTOFF_2022
    )
    assert selection.selected == (ORIGINAL,)
    assert selection.pit_safe is False


# ---------------------------------------------------------------------------
# Refusals: unsupported modes and invalid records
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode",
    [
        RevisionMode.FIRST_SEEN,
        RevisionMode.EXACT_REVISION,
        RevisionMode.ALL_REVISIONS,
        RevisionMode.ERROR_ON_AMBIGUITY,
    ],
)
def test_unimplemented_modes_are_refused_not_improvised(mode: RevisionMode) -> None:
    """s11 names them; implementing them is B5-I07 work, so we refuse."""
    with pytest.raises(UnsupportedRevisionMode):
        select_revisions((ORIGINAL,), _policy(mode), CUTOFF_2022)


def test_a_revision_record_needs_an_explicit_knowledge_window() -> None:
    with pytest.raises(ValueError):
        RevisionRecord(
            source_revision_id="rev-no-knowledge",
            normalization_generation=1,
            supersedes_t1_record_id=None,
            revision_status=RevisionStatus.ORIGINAL,
        )  # type: ignore[call-arg]


def test_naive_knowledge_time_is_refused() -> None:
    with pytest.raises(ValueError):
        RevisionRecord(
            source_revision_id="rev-naive",
            normalization_generation=1,
            supersedes_t1_record_id=None,
            revision_status=RevisionStatus.ORIGINAL,
            known_from=datetime(2022, 5, 12, hour=8),
        )


def test_knowledge_window_must_order_forward() -> None:
    with pytest.raises(ValueError):
        RevisionRecord(
            source_revision_id="rev-inverted",
            normalization_generation=1,
            supersedes_t1_record_id=None,
            revision_status=RevisionStatus.ORIGINAL,
            known_from=KNOWN_2025,
            known_to=KNOWN_2022,
        )


def test_negative_generation_and_blank_revision_id_are_refused() -> None:
    with pytest.raises(ValueError):
        RevisionRecord(
            source_revision_id="rev-negative",
            normalization_generation=-1,
            supersedes_t1_record_id=None,
            revision_status=RevisionStatus.ORIGINAL,
            known_from=KNOWN_2022,
        )
    with pytest.raises(ValueError):
        RevisionRecord(
            source_revision_id="  ",
            normalization_generation=1,
            supersedes_t1_record_id=None,
            revision_status=RevisionStatus.ORIGINAL,
            known_from=KNOWN_2022,
        )


def test_duplicate_revision_ids_in_one_call_are_refused() -> None:
    with pytest.raises(ValueError):
        select_revisions(
            (ORIGINAL, ORIGINAL),
            _policy(RevisionMode.AS_KNOWN_THEN),
            CUTOFF_2022,
        )


def test_selection_is_immutable_and_records_its_mode() -> None:
    selection = select_revisions(
        (ORIGINAL, CORRECTION), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assert isinstance(selection, RevisionSelection)
    with pytest.raises(Exception):
        selection.pit_safe = False  # type: ignore[misc]


def test_selection_does_not_mutate_its_inputs() -> None:
    before = (ORIGINAL.model_dump(), CORRECTION.model_dump())
    select_revisions((ORIGINAL, CORRECTION), _policy(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022)
    assert (ORIGINAL.model_dump(), CORRECTION.model_dump()) == before


def test_cutoff_is_always_explicit_never_a_default() -> None:
    with pytest.raises(TypeError):
        select_revisions((ORIGINAL,), _policy(RevisionMode.AS_KNOWN_THEN))  # type: ignore[call-arg]
