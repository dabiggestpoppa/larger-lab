"""SENSOR-B4-I06C — explicit declarations + fail-safe resolution modes.

Covers (I06 §33-§36, §54-§62):

- canonical declarations require explicit evidence and target existing
  revisions (§35);
- multiple distinct canonical revisions resolve AMBIGUOUS — never
  "latest wins" (§36/§60); multiple consistent declarations of the SAME
  revision resolve to it (§36);
- zero canonical declarations ⇒ typed unresolved (§60);
- ERROR_ON_AMBIGUITY (default) refuses to pick among >1 revisions (§55);
- ALL returns the complete segment sequence with no blob dedupe (§56);
- FIRST_SEEN/LATEST_SEEN are explicit opt-ins only (§57/§58);
- EXACT_REVISION requires an explicit number; unknown ⇒ NotFound (§59);
- unknown-revision state never appears from ordinary mutation (§38);
- resolution resolves VERSION IDENTITY only — it never asserts blob
  integrity or acquisition usability (§62);
- a malformed canonical declaration (unknown revision) is rejected.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from crypto_sensor_fabric.storage.revisions import (
    MutationSeverity,
    RevisionAmbiguityError,
    RevisionConfigurationError,
    RevisionNotFound,
    RevisionResolutionMode,
    RevisionResolutionUnavailable,
    RevisionState,
    SourceRevisionRegistry,
)

T1 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)


class CanonicalStack:
    """Registry stack with A→B→A history pre-seeded (three revisions)."""

    def __init__(self, tmp_path: Path) -> None:
        from _sibling_import import load_sibling

        _reg = load_sibling(
            "_i06_registry_mod", "test_source_revision_registry"
        )
        Stack = _reg.Stack
        _data = _reg._data

        self.stack = Stack(tmp_path)
        self._data = _data
        a = self.stack.seed(
            _data("A"),
            observed_at=T1,
            acq_id="acq-A1",
        )
        b = self.stack.seed(
            _data("B"),
            observed_at=T1 + timedelta(hours=1),
            acq_id="acq-B1",
        )
        a2 = self.stack.seed(
            _data("A"),
            observed_at=T1 + timedelta(hours=2),
            acq_id="acq-A2",
        )
        self.stack.registry.register_acquisition(a.acquisition_id)
        self.stack.registry.register_acquisition(b.acquisition_id)
        third = self.stack.registry.register_acquisition(a2.acquisition_id)
        self.key = third.source_revision_key
        self.blob_by_revision = {
            1: a.blob_sha256,
            2: b.blob_sha256,
            3: a2.blob_sha256,
        }

    def reopen(self) -> SourceRevisionRegistry:
        return self.stack.reopen()


class TestCanonicalDeclarations:
    def test_canonical_declaration_requires_existing_revision(
        self, tmp_path
    ) -> None:
        stack = CanonicalStack(tmp_path)
        with pytest.raises(RevisionNotFound):
            stack.stack.registry.declare_provider_canonical(
                source_revision_key=stack.key,
                revision_number=9,
                evidence_ref="evidence/provider-canonical-1",
            )

    def test_canonical_declaration_without_evidence_rejected(
        self, tmp_path
    ) -> None:
        stack = CanonicalStack(tmp_path)
        with pytest.raises((RevisionConfigurationError, TypeError)):
            stack.stack.registry.declare_provider_canonical(
                source_revision_key=stack.key,
                revision_number=2,
                evidence_ref="",
            )

    def test_unique_canonical_resolves(self, tmp_path) -> None:
        """§36/§60: ONE canonical designation resolves uniquely; the
        canonical revision need NOT be the latest (rev2 of three here)."""
        stack = CanonicalStack(tmp_path)
        stack.stack.registry.declare_provider_canonical(
            source_revision_key=stack.key,
            revision_number=2,
            evidence_ref="evidence/provider-canonical-1",
        )
        resolution = stack.stack.registry.resolve(
            stack.key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
        )
        assert resolution.selected_revision_numbers == [2]
        assert resolution.provider_canonical_revision_number == 2
        assert resolution.ambiguous is False

    def test_multiple_distinct_canonicals_ambiguous(self, tmp_path) -> None:
        """§36/§60: two distinct canonical revisions fail ambiguous — no
        'latest wins', ever."""
        stack = CanonicalStack(tmp_path)
        registry = stack.stack.registry
        registry.declare_provider_canonical(
            source_revision_key=stack.key,
            revision_number=1,
            evidence_ref="evidence/canon-1",
        )
        registry.declare_provider_canonical(
            source_revision_key=stack.key,
            revision_number=3,
            evidence_ref="evidence/canon-3",
        )
        with pytest.raises(RevisionAmbiguityError):
            registry.resolve(
                stack.key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
            )

    def test_duplicate_canonical_declarations_same_revision_resolve(
        self, tmp_path
    ) -> None:
        """§36: multiple records pointing to the SAME revision resolve to
        that one revision when internally consistent."""
        stack = CanonicalStack(tmp_path)
        registry = stack.stack.registry
        registry.declare_provider_canonical(
            source_revision_key=stack.key,
            revision_number=2,
            evidence_ref="evidence/canon-note-A",
        )
        registry.declare_provider_canonical(
            source_revision_key=stack.key,
            revision_number=2,
            evidence_ref="evidence/canon-note-B",
        )
        resolution = registry.resolve(
            stack.key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
        )
        assert resolution.selected_revision_numbers == [2]

    def test_zero_canonical_unresolved(self, tmp_path) -> None:
        """§60: PROVIDER_DECLARED_CANONICAL without any declaration is typed
        unresolved — never a silent fallback to latest."""
        stack = CanonicalStack(tmp_path)
        with pytest.raises(RevisionResolutionUnavailable):
            stack.stack.registry.resolve(
                stack.key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
            )

    def test_declared_revision_is_not_canonical(self, tmp_path) -> None:
        """§61: PROVIDER_DECLARED_REVISION segment state does NOT satisfy
        PROVIDER_DECLARED_CANONICAL resolution."""
        stack = CanonicalStack(tmp_path)
        registry = stack.stack.registry
        b = stack.stack.seed(
            stack._data("C"),
            observed_at=T1 + timedelta(hours=3),
            acq_id="acq-C1",
        )
        obs = registry.register_acquisition(
            b.acquisition_id,
            provider_declaration={
                "declaration_kind": "revision",
                "evidence_ref": "evidence/provider-rev-note",
            },
        )
        assert obs.observation_state == "PROVIDER_DECLARED_REVISION"
        with pytest.raises(RevisionResolutionUnavailable):
            registry.resolve(
                stack.key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
            )

    def test_canonical_survives_restart(self, tmp_path) -> None:
        stack = CanonicalStack(tmp_path)
        stack.stack.registry.declare_provider_canonical(
            source_revision_key=stack.key,
            revision_number=2,
            evidence_ref="evidence/provider-canonical-1",
        )
        reopened = stack.reopen()
        resolution = reopened.resolve(
            stack.key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
        )
        assert resolution.provider_canonical_revision_number == 2


class TestResolutionPolicies:
    def test_error_on_ambiguity_default_never_picks_latest(
        self, tmp_path
    ) -> None:
        """§55: >1 revisions under the default policy raises; a single
        revision resolves."""
        stack = CanonicalStack(tmp_path)
        registry = stack.stack.registry
        with pytest.raises(RevisionAmbiguityError):
            registry.resolve(stack.key, RevisionResolutionMode.ERROR_ON_AMBIGUITY)
        single = registry._segments_by_key[stack.key][:1]
        # A source with exactly one revision resolves under the default.
        lone_key = single[0].source_revision_key
        fresh = registry._segments_by_key.keys()
        assert lone_key in fresh
        # Demonstrate on a genuinely single-revision source.
        solo_stack_seed = stack.stack.seed(
            stack._data("SOLO"),
            observed_at=T1 + timedelta(hours=4),
            request_fp="fp-solo",
            acq_id="acq-SOLO",
        )
        registry.register_acquisition(solo_stack_seed.acquisition_id)
        solo_key = registry.revision_for_acquisition(
            solo_stack_seed.acquisition_id
        )[0]
        resolution = registry.resolve(
            solo_key, RevisionResolutionMode.ERROR_ON_AMBIGUITY
        )
        assert resolution.selected_revision_numbers == [1]
        del single

    def test_all_returns_complete_sequence_no_dedupe(self, tmp_path) -> None:
        """§56: A→B→A returns rev1 A, rev2 B, rev3 A — no blob dedupe."""
        stack = CanonicalStack(tmp_path)
        resolution = stack.stack.registry.resolve(
            stack.key, RevisionResolutionMode.ALL
        )
        assert resolution.selected_revision_numbers == [1, 2, 3]
        assert resolution.ambiguous is False
        revs = stack.stack.registry.list_revisions(stack.key)
        assert [r.blob_sha256 for r in revs] == [
            stack.blob_by_revision[1],
            stack.blob_by_revision[2],
            stack.blob_by_revision[3],
        ]

    def test_first_seen_explicit_only(self, tmp_path) -> None:
        stack = CanonicalStack(tmp_path)
        resolution = stack.stack.registry.resolve(
            stack.key, RevisionResolutionMode.FIRST_SEEN
        )
        assert resolution.selected_revision_numbers == [1]
        with pytest.raises(RevisionNotFound):
            stack.stack.registry.resolve(
                "f" * 64, RevisionResolutionMode.FIRST_SEEN
            )

    def test_latest_seen_explicit_only(self, tmp_path) -> None:
        """§58: LATEST_SEEN is the latest OBSERVED state — allowed only as
        an explicit policy, and it does not mean economic truth."""
        stack = CanonicalStack(tmp_path)
        resolution = stack.stack.registry.resolve(
            stack.key, RevisionResolutionMode.LATEST_SEEN
        )
        assert resolution.selected_revision_numbers == [3]
        with pytest.raises(RevisionNotFound):
            stack.stack.registry.resolve(
                "f" * 64, RevisionResolutionMode.LATEST_SEEN
            )

    def test_exact_revision_contract(self, tmp_path) -> None:
        """§59: explicit number required; unknown number ⇒ NotFound; no
        fallback."""
        stack = CanonicalStack(tmp_path)
        registry = stack.stack.registry
        resolution = registry.resolve(
            stack.key,
            RevisionResolutionMode.EXACT_REVISION,
            revision_number=2,
        )
        assert resolution.selected_revision_numbers == [2]
        with pytest.raises(RevisionConfigurationError):
            registry.resolve(stack.key, RevisionResolutionMode.EXACT_REVISION)
        with pytest.raises(RevisionNotFound):
            registry.resolve(
                stack.key,
                RevisionResolutionMode.EXACT_REVISION,
                revision_number=99,
            )

    def test_resolution_of_unknown_key_not_found(self, tmp_path) -> None:
        """§55/§59: unknown keys fail typed on selection policies; ALL is an
        empty (non-error) sequence for an unknown key."""
        stack = CanonicalStack(tmp_path)
        with pytest.raises(RevisionNotFound):
            stack.stack.registry.resolve(
                "0" * 64, RevisionResolutionMode.ERROR_ON_AMBIGUITY
            )
        empty = stack.stack.registry.resolve(
            "0" * 64, RevisionResolutionMode.ALL
        )
        assert empty.selected_revision_numbers == []
        assert empty.all_revision_numbers == []


class TestResolutionIsNotIntegrityPromotion:
    def test_resolution_does_not_assert_usability(self, tmp_path) -> None:
        """§62: selecting a revision resolves VERSION IDENTITY only.  A
        forensic birth acquisition (failure_ref) may define a revision whose
        selection carries NO usability claim — usability stays an
        acquisition-level property."""
        from _sibling_import import load_sibling

        _reg = load_sibling(
            "_i06_registry_mod", "test_source_revision_registry"
        )
        Stack = _reg.Stack
        _data = _reg._data

        stack = Stack(tmp_path)
        acq = stack.seed(
            _data("A"), failure_ref="ref-500", http_status="500"
        )
        obs = stack.registry.register_acquisition(acq.acquisition_id)
        assert obs.usable_provenance is False
        resolution = stack.registry.resolve(
            obs.source_revision_key,
            RevisionResolutionMode.ERROR_ON_AMBIGUITY,
        )
        assert resolution.selected_revision_numbers == [1]
        # The revision view exposes no usability/integrity promotion.
        rev = stack.registry.get_revision(obs.source_revision_key, 1)
        assert rev is not None
        assert not hasattr(rev, "usable_provenance")
        assert not hasattr(rev, "integrity_state")

    def test_mutation_severity_frozen_vocabulary(self, tmp_path) -> None:
        """§37: severity values are the frozen set, carried on observations."""
        assert {s.value for s in MutationSeverity} == {
            "INFO",
            "NOTICE",
            "WARNING",
            "BLOCKER",
        }


class TestUnknownRevisionDiscipline:
    def test_unknown_revision_reserved_not_default(self, tmp_path) -> None:
        """§38: ordinary mutation is KNOWN — UNKNOWN_REVISION never appears
        as a segment state in any ordinary classification path."""
        stack = CanonicalStack(tmp_path)
        states = {
            s.revision_state
            for segs in stack.stack.registry._segments_by_key.values()
            for s in segs
        }
        assert "UNKNOWN_REVISION" not in states
        assert states <= {state.value for state in RevisionState}
