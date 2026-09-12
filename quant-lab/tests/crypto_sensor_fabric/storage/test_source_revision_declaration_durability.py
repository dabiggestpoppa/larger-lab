"""SENSOR-B4-I06R1D — declaration-durability and identity-tamper adversarial
proofs.

Covers (I06R1 §19-§29, §48):

- same-process vs restart birth re-registration equivalence (§20): original
  classification returned, never IDENTICAL_REFETCH, no new segment or
  observation;
- provider-declared birth re-registration keeps its classification (§19);
- IDENTICAL_REFETCH requires a distinct acquisition event (§21);
- provider-declaration crash boundary matrix (§27): before declaration,
  after declaration / before segment, after segment / before return — an
  unsupported provider classification is never visible, and an exact retry
  completes the intended classification without silent downgrade/upgrade;
- pending-declaration retry: same evidence completes (§28); different
  evidence conflicts;
- missing provider-declaration evidence fails restart (§26);
- declaration idempotence: exact repeat adopts committed record; different
  semantics under one id is a typed conflict (§37);
- cross-source default declaration ids are collision-free (§34/§36);
- coordinated descriptor+key+filename identity tamper fails restart against
  the UNCHANGED durable acquisition (§13);
- same-blob observation moved to a second logical source fails restart
  (§14) — byte identity never transfers source identity.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from crypto_sensor_fabric.storage.revisions import (
    MutationSeverity,
    ObservationState,
    ProviderRevisionDeclaration,
    RevisionDeclarationConflict,
    RevisionResolutionMode,
    SourceRevisionCatalogCorrupt,
    SourceRevisionRegistry,
)

T1 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=UTC)
DECL = ProviderRevisionDeclaration(
    evidence_ref="evidence/provider-rev-declaration",
    declared_at=T1 + timedelta(minutes=5),
)


class RevStack:
    def __init__(self, tmp_path: Path) -> None:
        from _sibling_import import load_sibling

        mod = load_sibling("_i06_registry_mod", "test_source_revision_registry")
        self._stack = mod.Stack(tmp_path)
        self._data = mod._data

    def __getattr__(self, name):  # delegate to the inner stack
        return getattr(self._stack, name)


def _observation_view(registry: SourceRevisionRegistry, acquisition_id: str):
    binding = registry.revision_for_acquisition(acquisition_id)
    assert binding is not None
    key, revision_number = binding
    segment = registry.segment_for_revision(key, revision_number)
    assert segment is not None
    obs = next(
        (
            o
            for o in registry.list_observations(key)
            if o.acquisition_id == acquisition_id
        ),
        None,
    )
    return key, segment, obs


class TestBirthIdempotence:
    def test_same_process_birth_reregister_is_classification_idempotent(
        self, tmp_path
    ) -> None:
        """§19/§20: re-registering the birth acquisition returns the ORIGINAL
        classification (STABLE/FIRST_REGISTRATION) — never IDENTICAL_REFETCH,
        no new segment, no new observation."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        first = stack.registry.register_acquisition(a.acquisition_id)
        assert first.observation_state == (
            ObservationState.FIRST_REGISTRATION.value
        )
        key = first.source_revision_key
        before_segments = stack.registry.list_revisions(key)
        before_observations = stack.registry.list_observations(key)

        again = stack.registry.register_acquisition(a.acquisition_id)

        assert again.observation_state == (
            ObservationState.FIRST_REGISTRATION.value
        )
        assert again.severity == MutationSeverity.INFO.value
        assert again.revision_number == 1
        assert again.source_revision_key == key
        assert stack.registry.list_revisions(key) == before_segments
        assert [
            o.acquisition_id for o in stack.registry.list_observations(key)
        ] == [o.acquisition_id for o in before_observations]

    def test_restart_birth_reregister_identical_to_same_process(
        self, tmp_path
    ) -> None:
        """§20: process lifetime may not change revision semantics — the
        restart re-registration result matches the same-process result on
        key, revision, blob, classification and usable_provenance."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        stack.registry.register_acquisition(a.acquisition_id)
        same_process = stack.registry.register_acquisition(a.acquisition_id)

        reopened = stack.reopen()
        restart = reopened.register_acquisition(a.acquisition_id)

        for field in (
            "acquisition_id",
            "source_revision_key",
            "revision_number",
            "blob_sha256",
            "observation_state",
            "usable_provenance",
            "severity",
            "seen_at",
        ):
            assert getattr(restart, field) == getattr(same_process, field)

    def test_mutation_birth_reregister_keeps_source_mutation(
        self, tmp_path
    ) -> None:
        """§19: re-registering a SOURCE_MUTATION birth returns SOURCE_MUTATION
        (WARNING) — the original classification, not a refetch."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(b.acquisition_id)
        key, segment, _ = _observation_view(stack.registry, "acq-B")
        assert segment.revision_state == "SOURCE_MUTATION"

        reopened = stack.reopen()
        again = reopened.register_acquisition("acq-B")

        assert again.observation_state == (
            ObservationState.SOURCE_MUTATION.value
        )
        assert again.severity == MutationSeverity.WARNING.value
        assert again.revision_number == 2
        assert again.source_revision_key == key
        assert len(reopened.list_revisions(key)) == 2

    def test_provider_declared_birth_reregister_keeps_classification(
        self, tmp_path
    ) -> None:
        """§19: a provider-declared birth re-registered after restart keeps
        PROVIDER_DECLARED_REVISION (NOTICE) and its resolution behavior."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(
            b.acquisition_id, provider_declaration=DECL
        )
        key, segment, _ = _observation_view(stack.registry, "acq-B")
        assert segment.revision_state == "PROVIDER_DECLARED_REVISION"

        reopened = stack.reopen()
        again = reopened.register_acquisition("acq-B")

        assert again.observation_state == (
            ObservationState.PROVIDER_DECLARED_REVISION.value
        )
        assert again.severity == MutationSeverity.NOTICE.value
        assert again.revision_number == 2

    def test_identical_refetch_requires_distinct_acquisition(
        self, tmp_path
    ) -> None:
        """§21: a NEW acquisition carrying the current bytes is an
        IDENTICAL_REFETCH observation; re-invoking the birth acquisition id
        is idempotence, never a refetch event."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        stack.registry.register_acquisition(a.acquisition_id)
        # Same BYTES, different acquisition event, later seen_at.
        a2 = stack.seed(stack._data("A"), observed_at=T1 + timedelta(hours=2), acq_id="acq-A2")
        refetch = stack.registry.register_acquisition(a2.acquisition_id)
        assert refetch.observation_state == (
            ObservationState.IDENTICAL_REFETCH.value
        )
        assert refetch.revision_number == 1
        # Birth re-registration is NOT classified as refetch.
        birth_again = stack.registry.register_acquisition("acq-A")
        assert birth_again.observation_state == (
            ObservationState.FIRST_REGISTRATION.value
        )
        assert len(stack.registry.list_revisions(refetch.source_revision_key)) == 1


class TestProviderDeclarationCrashMatrix:
    def test_crash_before_declaration_leaves_no_classification(
        self, tmp_path
    ) -> None:
        """§27 boundary 1: the provider declaration fails validation before
        ANY durable state — no segment, no declaration, plain mutation
        classification for the same bytes without evidence."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        with pytest.raises(Exception):
            stack.registry.register_acquisition(
                b.acquisition_id,
                provider_declaration=ProviderRevisionDeclaration(
                    evidence_ref="   ", declared_at=T1
                ),
            )
        reopened = stack.reopen()
        key = reopened.revision_for_acquisition("acq-A")[0]
        assert len(reopened.list_revisions(key)) == 1
        assert reopened._declarations_by_key.get(key, []) == []

    def test_crash_after_declaration_before_segment_is_safe(
        self, tmp_path
    ) -> None:
        """§25A/§27 boundary 2: a crash between the pending declaration and
        the segment leaves declaration evidence ONLY — the pending state
        never masquerades as revision truth."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        # Simulate the crash: declaration published, segment not.
        stack.registry._commit_declaration(
            declaration_id=stack.registry._declaration_id(
                key=stack.key_of("acq-A"),
                declaration_kind="revision",
                revision_number=None,
                acquisition_id="acq-B",
                blob_sha256=b.blob_sha256,
                evidence_ref=DECL.evidence_ref,
                declared_at=DECL.declared_at,
            ),
            key=stack.key_of("acq-A"),
            revision_number=None,
            declaration_kind="revision",
            evidence_ref=DECL.evidence_ref,
            declared_at=DECL.declared_at,
            bound_acquisition_id="acq-B",
            blob_sha256=b.blob_sha256,
        )
        reopened = stack.reopen()
        key = reopened.revision_for_acquisition("acq-A")[0]
        assert len(reopened.list_revisions(key)) == 1
        # The pending declaration survived (durable evidence), but no
        # PROVIDER_DECLARED segment exists.
        pending = [
            d
            for d in reopened._declarations_by_key.get(key, [])
            if d.declaration_kind == "revision" and d.revision_number is None
        ]
        assert len(pending) == 1

    def test_retry_with_same_evidence_completes_intended_classification(
        self, tmp_path
    ) -> None:
        """§28: after a pending-evidence crash, the same acquisition with the
        SAME declaration completes the exact intended provider-declared
        revision — never a downgrade to SOURCE_MUTATION."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry._commit_declaration(
            declaration_id=stack.registry._declaration_id(
                key=stack.key_of("acq-A"),
                declaration_kind="revision",
                revision_number=None,
                acquisition_id="acq-B",
                blob_sha256=b.blob_sha256,
                evidence_ref=DECL.evidence_ref,
                declared_at=DECL.declared_at,
            ),
            key=stack.key_of("acq-A"),
            revision_number=None,
            declaration_kind="revision",
            evidence_ref=DECL.evidence_ref,
            declared_at=DECL.declared_at,
            bound_acquisition_id="acq-B",
            blob_sha256=b.blob_sha256,
        )
        reopened = stack.reopen()
        obs = reopened.register_acquisition(
            "acq-B", provider_declaration=DECL
        )
        assert obs.observation_state == (
            ObservationState.PROVIDER_DECLARED_REVISION.value
        )
        assert obs.revision_number == 2
        assert len(reopened.list_revisions(obs.source_revision_key)) == 2
        assert reopened.list_revisions(obs.source_revision_key)[
            1
        ].revision_state == "PROVIDER_DECLARED_REVISION"

    def test_retry_with_divergent_evidence_conflicts(self, tmp_path) -> None:
        """§28: divergent evidence_ref or declared_at for the same pending
        transition is a typed conflict — never a silent classification
        change."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry._commit_declaration(
            declaration_id=stack.registry._declaration_id(
                key=stack.key_of("acq-A"),
                declaration_kind="revision",
                revision_number=None,
                acquisition_id="acq-B",
                blob_sha256=b.blob_sha256,
                evidence_ref=DECL.evidence_ref,
                declared_at=DECL.declared_at,
            ),
            key=stack.key_of("acq-A"),
            revision_number=None,
            declaration_kind="revision",
            evidence_ref=DECL.evidence_ref,
            declared_at=DECL.declared_at,
            bound_acquisition_id="acq-B",
            blob_sha256=b.blob_sha256,
        )
        reopened = stack.reopen()
        with pytest.raises(RevisionDeclarationConflict):
            reopened.register_acquisition(
                "acq-B",
                provider_declaration=ProviderRevisionDeclaration(
                    evidence_ref="evidence/OTHER",
                    declared_at=DECL.declared_at,
                ),
            )
        # The pending evidence and the single-revision chain are untouched.
        key = reopened.revision_for_acquisition("acq-A")[0]
        assert len(reopened.list_revisions(key)) == 1

    def test_missing_declaration_evidence_fails_restart(self, tmp_path) -> None:
        """§26: a durable PROVIDER_DECLARED_REVISION segment whose declaration
        evidence is removed fails closed on reload."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(
            b.acquisition_id, provider_declaration=DECL
        )

        dec_dir = stack.root / "declarations"
        # Remove the declaration fragment that supports the classification.
        removed = False
        for fragment in dec_dir.glob("*.json"):
            payload = json.loads(fragment.read_text(encoding="utf-8"))
            if payload.get("declaration_kind") == "revision":
                fragment.unlink()
                removed = True
        assert removed
        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()


class TestDeclarationIdentity:
    def test_exact_repeat_is_idempotent_no_duplicate(self, tmp_path) -> None:
        """§37: repeating the exact declaration adopts the committed record —
        no duplicate append, same id."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(b.acquisition_id)
        key = stack.key_of("acq-A")
        first = stack.registry.declare_provider_revision(
            source_revision_key=key,
            revision_number=2,
            evidence_ref="evidence/rev-note",
            declared_at=T1 + timedelta(minutes=1),
        )
        count_before = len(stack.registry._declarations_by_key[key])
        second = stack.registry.declare_provider_revision(
            source_revision_key=key,
            revision_number=2,
            evidence_ref="evidence/rev-note",
            declared_at=T1 + timedelta(minutes=1),
        )
        assert second.declaration_id == first.declaration_id
        assert len(stack.registry._declarations_by_key[key]) == count_before

    def test_same_id_different_semantics_conflict(self, tmp_path) -> None:
        """§37: the same declaration id with different semantics is a typed
        conflict — never overwritten."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        b = stack.seed(
            stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="acq-B"
        )
        stack.registry.register_acquisition(a.acquisition_id)
        stack.registry.register_acquisition(b.acquisition_id)
        key = stack.key_of("acq-A")
        record = stack.registry.declare_provider_revision(
            source_revision_key=key,
            revision_number=2,
            evidence_ref="evidence/rev-note",
            declared_at=T1 + timedelta(minutes=1),
        )
        with pytest.raises(RevisionDeclarationConflict):
            stack.registry._commit_declaration(
                declaration_id=record.declaration_id,
                key=key,
                revision_number=2,
                declaration_kind="revision",
                evidence_ref="evidence/DIFFERENT",
                declared_at=T1 + timedelta(minutes=1),
            )

    def test_cross_source_default_ids_never_collide(self, tmp_path) -> None:
        """§34/§36: two unrelated source keys can create default revision AND
        canonical declarations independently — distinct ids, both commit."""
        stack = RevStack(tmp_path)
        a1 = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-S1")
        stack.registry.register_acquisition(a1.acquisition_id)
        # A second, DIFFERENT logical source: different request fingerprint.
        a2 = stack.seed(
            stack._data("A2"),
            observed_at=T1,
            acq_id="acq-S2",
            request_fp="fp-2",
        )
        stack.registry.register_acquisition(a2.acquisition_id)
        key1 = stack.key_of("acq-S1")
        key2 = stack.key_of("acq-S2")
        assert key1 != key2

        rev1 = stack.registry.declare_provider_revision(
            source_revision_key=key1,
            revision_number=1,
            evidence_ref="evidence/s1",
            declared_at=T1,
        )
        rev2 = stack.registry.declare_provider_revision(
            source_revision_key=key2,
            revision_number=1,
            evidence_ref="evidence/s2",
            declared_at=T1,
        )
        assert rev1.declaration_id != rev2.declaration_id

        can1 = stack.registry.declare_provider_canonical(
            source_revision_key=key1,
            revision_number=1,
            evidence_ref="evidence/s1-canon",
            declared_at=T1,
        )
        can2 = stack.registry.declare_provider_canonical(
            source_revision_key=key2,
            revision_number=1,
            evidence_ref="evidence/s2-canon",
            declared_at=T1,
        )
        assert can1.declaration_id != can2.declaration_id
        assert can1.declaration_id != rev1.declaration_id

        # Both sources resolve their own canonical revision independently.
        assert (
            stack.registry.resolve(
                key1, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
            ).provider_canonical_revision_number
            == 1
        )
        assert (
            stack.registry.resolve(
                key2, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
            ).provider_canonical_revision_number
            == 1
        )

    def test_empty_evidence_ref_rejected_everywhere(self, tmp_path) -> None:
        """§30: no declaration path accepts an empty/whitespace evidence
        reference."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        stack.registry.register_acquisition(a.acquisition_id)
        key = stack.key_of("acq-A")
        with pytest.raises(Exception):
            ProviderRevisionDeclaration(evidence_ref="", declared_at=T1)
        with pytest.raises(Exception):
            ProviderRevisionDeclaration(evidence_ref="  ", declared_at=T1)
        with pytest.raises(Exception):
            ProviderRevisionDeclaration(
                evidence_ref="ok", declared_at=T1.replace(tzinfo=None)
            )
        with pytest.raises(Exception):
            stack.registry.declare_provider_revision(
                source_revision_key=key,
                revision_number=1,
                evidence_ref="",
                declared_at=T1,
            )
        with pytest.raises(Exception):
            stack.registry.declare_provider_canonical(
                source_revision_key=key,
                revision_number=1,
                evidence_ref="   ",
                declared_at=T1,
            )


class TestIdentityTamper:
    def test_coordinated_descriptor_key_filename_tamper_fails_restart(
        self, tmp_path
    ) -> None:
        """§13: an attacker rewrites identity_descriptor, source_revision_key,
        segment_id AND the physical filename so the descriptor hashes to the
        new key — restart STILL fails closed because the durable birth
        acquisition's request semantics derive the ORIGINAL key."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        stack.registry.register_acquisition(a.acquisition_id)
        key = stack.key_of("acq-A")

        import hashlib

        seg_dir = stack.root / "segments"
        old_fragment = seg_dir / (
            hashlib.sha256(f"{key}:1".encode()).hexdigest() + ".json"
        )
        payload = json.loads(old_fragment.read_text(encoding="utf-8"))
        # Forge a new descriptor whose fields differ (venue flipped) and
        # recompute the forged key consistently.
        payload["identity_descriptor"]["fields"]["venue"] = "venue-evil"
        forged_fields = dict(payload["identity_descriptor"]["fields"])
        descriptor = {
            "identity_version": 1,
            "fields": forged_fields,
        }
        from crypto_sensor_fabric.storage.json_catalog import (
            canonical_json_bytes,
        )

        forged_key = hashlib.sha256(
            canonical_json_bytes(descriptor)
        ).hexdigest()
        payload["identity_descriptor"] = descriptor
        payload["source_revision_key"] = forged_key
        payload["segment_id"] = f"{forged_key}:1"
        new_fragment = seg_dir / (
            hashlib.sha256(f"{forged_key}:1".encode()).hexdigest() + ".json"
        )
        new_fragment.write_text(
            json.dumps(payload), encoding="utf-8"
        )
        old_fragment.unlink()

        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_same_blob_observation_moved_to_other_source_fails_restart(
        self, tmp_path
    ) -> None:
        """§14: two logical sources with the SAME bytes — moving an
        observation of source A to claim source B fails restart: the durable
        acquisition's request semantics still derive source A's key."""
        stack = RevStack(tmp_path)
        a1 = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-S1")
        stack.registry.register_acquisition(a1.acquisition_id)
        # Same bytes, different logical source (request fingerprint).
        a2 = stack.seed(
            stack._data("A"),
            observed_at=T1,
            acq_id="acq-S2",
            request_fp="fp-2",
        )
        stack.registry.register_acquisition(a2.acquisition_id)
        key2 = stack.key_of("acq-S2")
        # A subsequent observation of source S2 (same bytes, new acquisition
        # event) IS a durable observation record — births are segments.
        a3 = stack.seed(
            stack._data("A"),
            observed_at=T1 + timedelta(hours=1),
            acq_id="acq-S3",
            request_fp="fp-2",
        )
        stack.registry.register_acquisition(a3.acquisition_id)


        key1 = stack.key_of("acq-S1")
        obs_dir = stack.root / "observations"
        tampered = False
        for fragment in obs_dir.glob("*.json"):
            payload = json.loads(fragment.read_text(encoding="utf-8"))
            if payload.get("acquisition_id") == "acq-S3":
                # Move the observation of source S2 to claim source S1's key
                # — blob stays valid, request semantics do not.
                assert payload["source_revision_key"] == key2
                payload["source_revision_key"] = key1
                fragment.write_text(json.dumps(payload), encoding="utf-8")
                tampered = True
        assert tampered

        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()

    def test_duplicate_birth_acquisition_across_segments_fails_restart(
        self, tmp_path
    ) -> None:
        """§15: one acquisition_id cannot be the birth of two revision
        segments even when the blob matches — restart fails closed."""
        stack = RevStack(tmp_path)
        a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
        stack.registry.register_acquisition(a.acquisition_id)
        key = stack.key_of("acq-A")

        import hashlib

        # Forge a second segment (rev 2) claiming the SAME birth acquisition.
        seg_dir = stack.root / "segments"
        original = seg_dir / (
            hashlib.sha256(f"{key}:1".encode()).hexdigest() + ".json"
        )
        payload = json.loads(original.read_text(encoding="utf-8"))
        payload["segment_id"] = f"{key}:2"
        payload["revision_number"] = 2
        forged = seg_dir / (
            hashlib.sha256(f"{key}:2".encode()).hexdigest() + ".json"
        )
        forged.write_text(json.dumps(payload), encoding="utf-8")

        with pytest.raises(SourceRevisionCatalogCorrupt):
            stack.reopen()
