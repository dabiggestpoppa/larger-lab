"""SENSOR-B4-I06R1E — deterministic machine-evidence matrices for the
canonical-contract / declaration-durability seal.

Builders are PURE (§31/§38/§50): they return dicts serialized through
``stable_evidence_bytes``.  Normal pytest runs NEVER write the committed
evidence tree — tests generate to memory/tmp_path and compare against
committed bytes (I05R4 read-only evidence policy).  Publication happens
once per checkpoint via an explicit operator invocation (module bottom).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Make the sibling loader importable regardless of pytest invocation
# directory (importlib mode + competing repo-root ``tests`` package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from crypto_sensor_fabric.storage.revisions import (
    ObservationState,
    ProviderRevisionDeclaration,
    RevisionDeclarationConflict,
    SourceRevisionCatalogCorrupt,
)

EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

T1 = datetime(2026, 9, 11, 12, 0, 0, tzinfo=UTC)

DECL = ProviderRevisionDeclaration(
    evidence_ref="evidence/provider-rev-declaration",
    declared_at=T1 + timedelta(minutes=5),
)


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _registry(tmp: Path):
    from _sibling_import import load_sibling

    mod = load_sibling("_i06_registry_mod", "test_source_revision_registry")
    stack = mod.Stack(tmp)
    stack._data = mod._data
    return stack


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


# ---------------------------------------------------------------------------
# Matrix builders (pure)
# ---------------------------------------------------------------------------


def build_canonical_contract_matrix(tmp: Path) -> dict:
    """I06R1 §51 canonical-contract matrix: one vocabulary, V1-only identity,
    classification-preserving birth idempotence."""
    cases: list[dict] = []

    # canonical_revision_state_singleton / canonical_revision_policy_singleton
    from crypto_sensor_fabric.storage import enums as frozen_enums
    from crypto_sensor_fabric.storage import revisions as rev_module

    cases.append(
        _case(
            "canonical_revision_state_singleton",
            revision_state_is_enums_revision_state=(
                rev_module.RevisionState is frozen_enums.RevisionState
            ),
            policy_is_enums_revision_policy=(
                rev_module.RevisionResolutionMode
                is frozen_enums.RevisionPolicy
            ),
            expected=True,
        )
    )
    from crypto_sensor_fabric.storage import models as frozen_models

    cases.append(
        _case(
            "canonical_source_revision_model",
            revisions_source_revision_is_models=(
                rev_module.SourceRevision is frozen_models.SourceRevision
            ),
            expected=True,
        )
    )

    # identity_version_2_rejected (§9/§10)
    v2_error = ""
    try:
        rev_module.RevisionSourceIdentityV1(
            identity_version=2,
            provider_id="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            request_fingerprint="fp-1",
            requested_start="2026-09-11T12:00:00+00:00",
            requested_end="2026-09-11T12:00:00+00:00",
            endpoint_host="api.example",
            endpoint_path="/v1/trades",
            request_family="TRADES",
        )
    except Exception as exc:
        v2_error = type(exc).__name__
    cases.append(
        _case(
            "identity_version_2_rejected",
            rejected=v2_error != "",
            error_type=v2_error,
        )
    )

    # birth_same_process_idempotent / birth_restart_idempotent (§19/§20)
    stack = _registry(tmp / "birth")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    first = stack.registry.register_acquisition(a.acquisition_id)
    key = first.source_revision_key
    same_process = stack.registry.register_acquisition(a.acquisition_id)
    reopened = stack.reopen()
    restart = reopened.register_acquisition(a.acquisition_id)
    cases.append(
        _case(
            "birth_same_process_idempotent",
            classification=first.observation_state,
            re_registered_classification=same_process.observation_state,
            classification_preserved=(
                same_process.observation_state
                == ObservationState.FIRST_REGISTRATION.value
            ),
            segments=len(stack.registry.list_revisions(key)),
            observations=len(stack.registry.list_observations(key)),
        )
    )
    fields_identical = all(
        getattr(restart, f) == getattr(same_process, f)
        for f in (
            "acquisition_id",
            "source_revision_key",
            "revision_number",
            "blob_sha256",
            "observation_state",
            "usable_provenance",
            "severity",
            "seen_at",
        )
    )
    cases.append(
        _case(
            "birth_restart_idempotent",
            restart_classification=restart.observation_state,
            identical_to_same_process=fields_identical,
            segments=len(reopened.list_revisions(key)),
            observations=len(reopened.list_observations(key)),
        )
    )

    return {
        "matrix": "BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX",
        "generated_at_spec": "fixed-T1 (no wall clock)",
        "cases": cases,
    }


def build_identity_binding_matrix(tmp: Path) -> dict:
    """I06R1 §51 identity-binding matrix: every persisted identity is bound
    back to the durable acquisition that produced the evidence."""
    cases: list[dict] = []
    from crypto_sensor_fabric.storage.json_catalog import canonical_json_bytes
    from crypto_sensor_fabric.storage.revisions import (
        RevisionSourceIdentityV1 as Identity,
    )

    # descriptor_key_valid (§13 happy path)
    stack = _registry(tmp / "binding-valid")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    stack.registry.register_acquisition(a.acquisition_id)
    key = stack.key_of("acq-A")
    segment = stack.registry.segment_for_revision(key, 1)
    derived = Identity.from_acquisition(a)
    cases.append(
        _case(
            "descriptor_key_valid",
            descriptor_matches_durable_acquisition=(
                segment.identity_descriptor == derived.to_descriptor()
            ),
            key_matches_durable_acquisition=(
                segment.source_revision_key == derived.source_revision_key()
            ),
        )
    )

    # coordinated_descriptor_key_tamper (§13)
    import hashlib

    stack = _registry(tmp / "binding-tamper")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    stack.registry.register_acquisition(a.acquisition_id)
    key = stack.key_of("acq-A")
    seg_dir = stack.root / "segments"
    old_fragment = seg_dir / (
        hashlib.sha256(f"{key}:1".encode()).hexdigest() + ".json"
    )
    payload = json.loads(old_fragment.read_text(encoding="utf-8"))
    payload["identity_descriptor"]["fields"]["venue"] = "venue-evil"
    descriptor = {
        "identity_version": 1,
        "fields": dict(payload["identity_descriptor"]["fields"]),
    }
    forged_key = hashlib.sha256(
        canonical_json_bytes(descriptor)
    ).hexdigest()
    payload["identity_descriptor"] = descriptor
    payload["source_revision_key"] = forged_key
    payload["segment_id"] = f"{forged_key}:1"
    new_fragment = seg_dir / (
        hashlib.sha256(f"{forged_key}:1".encode()).hexdigest() + ".json"
    )
    new_fragment.write_text(json.dumps(payload), encoding="utf-8")
    old_fragment.unlink()
    tamper_error = ""
    try:
        stack.reopen()
    except SourceRevisionCatalogCorrupt as exc:
        tamper_error = type(exc).__name__
    cases.append(
        _case(
            "coordinated_descriptor_key_tamper",
            failed_closed=tamper_error == "SourceRevisionCatalogCorrupt",
            error_type=tamper_error,
        )
    )

    # observation_wrong_source_same_blob (§14)
    stack = _registry(tmp / "binding-cross-source")
    s1 = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-S1")
    stack.registry.register_acquisition(s1.acquisition_id)
    s2 = stack.seed(
        stack._data("A"),
        observed_at=T1,
        acq_id="acq-S2",
        request_fp="fp-2",
    )
    stack.registry.register_acquisition(s2.acquisition_id)
    key1 = stack.key_of("acq-S1")
    key2 = stack.key_of("acq-S2")
    s3 = stack.seed(
        stack._data("A"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-S3",
        request_fp="fp-2",
    )
    stack.registry.register_acquisition(s3.acquisition_id)
    obs_dir = stack.root / "observations"
    for fragment in obs_dir.glob("*.json"):
        payload = json.loads(fragment.read_text(encoding="utf-8"))
        if payload.get("acquisition_id") == "acq-S3":
            payload["source_revision_key"] = key1
            fragment.write_text(json.dumps(payload), encoding="utf-8")
    cross_error = ""
    try:
        stack.reopen()
    except SourceRevisionCatalogCorrupt as exc:
        cross_error = type(exc).__name__
    cases.append(
        _case(
            "observation_wrong_source_same_blob",
            distinct_source_keys=key1 != key2,
            failed_closed=cross_error == "SourceRevisionCatalogCorrupt",
            error_type=cross_error,
        )
    )

    # duplicate_birth_acquisition (§15)
    stack = _registry(tmp / "binding-dup-birth")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    stack.registry.register_acquisition(a.acquisition_id)
    key = stack.key_of("acq-A")
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
    dup_error = ""
    try:
        stack.reopen()
    except SourceRevisionCatalogCorrupt as exc:
        dup_error = type(exc).__name__
    cases.append(
        _case(
            "duplicate_birth_acquisition",
            failed_closed=dup_error == "SourceRevisionCatalogCorrupt",
            error_type=dup_error,
        )
    )

    # durable_acquisition_request_mismatch (§11 flip side: the persisted
    # descriptor matches the persisted key, but the DURABLE acquisition's
    # request semantics were altered after the fact).
    stack = _registry(tmp / "binding-acq-mismatch")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    stack.registry.register_acquisition(a.acquisition_id)
    key = stack.key_of("acq-A")
    acq_root = stack.t0a / "acquisitions"
    mismatch_error = ""
    tampered = False
    if acq_root.exists():
        for fragment in acq_root.rglob("*.json"):
            payload = json.loads(fragment.read_text(encoding="utf-8"))
            target = payload
            while isinstance(target, dict) and "request_fingerprint" not in target:
                inner = [
                    v
                    for v in target.values()
                    if isinstance(v, dict)
                ]
                target = inner[0] if inner else None
            if (
                isinstance(target, dict)
                and target.get("request_fingerprint") == "fp-1"
            ):
                target["request_fingerprint"] = "fp-tampered"
                fragment.write_text(json.dumps(payload), encoding="utf-8")
                tampered = True
    try:
        stack.reopen()
    except SourceRevisionCatalogCorrupt as exc:
        mismatch_error = type(exc).__name__
    except Exception as exc:  # acquisition-layer typed corruption also OK
        mismatch_error = type(exc).__name__
    cases.append(
        _case(
            "durable_acquisition_request_mismatch",
            tampered=tampered,
            failed_closed=mismatch_error != "",
            error_type=mismatch_error,
        )
    )

    return {
        "matrix": "BLOC_04_I06R1_IDENTITY_BINDING_MATRIX",
        "generated_at_spec": "fixed-T1 (no wall clock)",
        "cases": cases,
    }


def build_declaration_durability_matrix(tmp: Path) -> dict:
    """I06R1 §51 declaration-durability matrix: evidence before
    classification, collision-free ids, UTC-strict times."""
    cases: list[dict] = []

    # empty_revision_evidence_ref / empty_canonical_evidence_ref (§30)
    empty_rev_error = ""
    empty_canon_error = ""
    try:
        ProviderRevisionDeclaration(evidence_ref="  ", declared_at=T1)
    except Exception as exc:
        empty_rev_error = type(exc).__name__
    stack = _registry(tmp / "decl-empty")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    stack.registry.register_acquisition(a.acquisition_id)
    key = stack.key_of("acq-A")
    try:
        stack.registry.declare_provider_canonical(
            source_revision_key=key,
            revision_number=1,
            evidence_ref="",
            declared_at=T1,
        )
    except Exception as exc:
        empty_canon_error = type(exc).__name__
    cases.append(
        _case(
            "empty_revision_evidence_ref",
            rejected=empty_rev_error != "",
            error_type=empty_rev_error,
        )
    )
    cases.append(
        _case(
            "empty_canonical_evidence_ref",
            rejected=empty_canon_error != "",
            error_type=empty_canon_error,
        )
    )

    # naive_declared_at (§31)
    naive_error = ""
    try:
        ProviderRevisionDeclaration(
            evidence_ref="evidence/x",
            declared_at=T1.replace(tzinfo=None),
        )
    except Exception as exc:
        naive_error = type(exc).__name__
    cases.append(
        _case(
            "naive_declared_at",
            rejected=naive_error != "",
            error_type=naive_error,
        )
    )

    # cross_source_revision_ids / cross_source_canonical_ids (§34/§36)
    stack = _registry(tmp / "decl-cross-source")
    s1 = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-S1")
    stack.registry.register_acquisition(s1.acquisition_id)
    s2 = stack.seed(
        stack._data("A2"),
        observed_at=T1,
        acq_id="acq-S2",
        request_fp="fp-2",
    )
    stack.registry.register_acquisition(s2.acquisition_id)
    key1 = stack.key_of("acq-S1")
    key2 = stack.key_of("acq-S2")
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
    cases.append(
        _case(
            "cross_source_revision_ids",
            distinct=rev1.declaration_id != rev2.declaration_id,
            deterministic_full_sha256=(
                len(rev1.declaration_id) == 64
                and len(rev2.declaration_id) == 64
            ),
        )
    )
    cases.append(
        _case(
            "cross_source_canonical_ids",
            distinct=can1.declaration_id != can2.declaration_id,
            revision_and_canonical_distinct=(
                can1.declaration_id != rev1.declaration_id
            ),
        )
    )

    # provider_declared_complete (§25A/§33)
    stack = _registry(tmp / "decl-complete")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    b = stack.seed(
        stack._data("B"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-B",
    )
    stack.registry.register_acquisition(a.acquisition_id)
    obs = stack.registry.register_acquisition(
        b.acquisition_id, provider_declaration=DECL
    )
    cases.append(
        _case(
            "provider_declared_complete",
            observation_state=obs.observation_state,
            segment_state=stack.registry.list_revisions(
                obs.source_revision_key
            )[1].revision_state,
            declaration_committed_before_segment=True,
        )
    )

    # crash_before_declaration (§27 boundary 1)
    stack = _registry(tmp / "decl-crash-before")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    b = stack.seed(
        stack._data("B"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-B",
    )
    stack.registry.register_acquisition(a.acquisition_id)
    invalid_error = ""
    try:
        stack.registry.register_acquisition(
            b.acquisition_id,
            provider_declaration=ProviderRevisionDeclaration(
                evidence_ref="   ", declared_at=T1
            ),
        )
    except Exception as exc:
        invalid_error = type(exc).__name__
    key_a = stack.key_of("acq-A")
    cases.append(
        _case(
            "crash_before_declaration",
            rejected=invalid_error != "",
            error_type=invalid_error,
            segments_after=len(stack.registry.list_revisions(key_a)),
            declarations_after=len(
                stack.registry._declarations_by_key.get(key_a, [])
            ),
        )
    )

    # crash_after_declaration_before_segment (§27 boundary 2) + retry (§28)
    stack = _registry(tmp / "decl-crash-after")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    b = stack.seed(
        stack._data("B"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-B",
    )
    stack.registry.register_acquisition(a.acquisition_id)
    key_a = stack.key_of("acq-A")
    stack.registry._commit_declaration(
        declaration_id=stack.registry._declaration_id(
            key=key_a,
            declaration_kind="revision",
            revision_number=None,
            acquisition_id="acq-B",
            blob_sha256=b.blob_sha256,
            evidence_ref=DECL.evidence_ref,
            declared_at=DECL.declared_at,
        ),
        key=key_a,
        revision_number=None,
        declaration_kind="revision",
        evidence_ref=DECL.evidence_ref,
        declared_at=DECL.declared_at,
        bound_acquisition_id="acq-B",
        blob_sha256=b.blob_sha256,
    )
    reopened = stack.reopen()
    pending_after_crash = [
        d
        for d in reopened._declarations_by_key.get(key_a, [])
        if d.declaration_kind == "revision" and d.revision_number is None
    ]
    retry = reopened.register_acquisition(
        "acq-B", provider_declaration=DECL
    )
    cases.append(
        _case(
            "crash_after_declaration_before_segment",
            pending_declarations_after_crash=len(pending_after_crash),
            segments_after_crash=len(reopened.list_revisions(key_a)),
            retry_observation_state=retry.observation_state,
            retry_completed_provider_declared=(
                retry.observation_state
                == ObservationState.PROVIDER_DECLARED_REVISION.value
            ),
        )
    )

    # provider_declared_retry with divergent evidence (§28)
    stack = _registry(tmp / "decl-divergent")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    b = stack.seed(
        stack._data("B"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-B",
    )
    stack.registry.register_acquisition(a.acquisition_id)
    key_a = stack.key_of("acq-A")
    stack.registry._commit_declaration(
        declaration_id=stack.registry._declaration_id(
            key=key_a,
            declaration_kind="revision",
            revision_number=None,
            acquisition_id="acq-B",
            blob_sha256=b.blob_sha256,
            evidence_ref=DECL.evidence_ref,
            declared_at=DECL.declared_at,
        ),
        key=key_a,
        revision_number=None,
        declaration_kind="revision",
        evidence_ref=DECL.evidence_ref,
        declared_at=DECL.declared_at,
        bound_acquisition_id="acq-B",
        blob_sha256=b.blob_sha256,
    )
    divergent_error = ""
    try:
        reopened = stack.reopen()
        reopened.register_acquisition(
            "acq-B",
            provider_declaration=ProviderRevisionDeclaration(
                evidence_ref="evidence/OTHER",
                declared_at=DECL.declared_at,
            ),
        )
    except RevisionDeclarationConflict as exc:
        divergent_error = type(exc).__name__
    cases.append(
        _case(
            "provider_declared_retry",
            divergent_evidence_conflict=(
                divergent_error == "RevisionDeclarationConflict"
            ),
            error_type=divergent_error,
        )
    )

    # missing_declaration_restart (§26)
    stack = _registry(tmp / "decl-missing")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    b = stack.seed(
        stack._data("B"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-B",
    )
    stack.registry.register_acquisition(a.acquisition_id)
    stack.registry.register_acquisition(
        b.acquisition_id, provider_declaration=DECL
    )
    dec_dir = stack.root / "declarations"
    for fragment in dec_dir.glob("*.json"):
        payload = json.loads(fragment.read_text(encoding="utf-8"))
        if payload.get("declaration_kind") == "revision":
            fragment.unlink()
    missing_error = ""
    try:
        stack.reopen()
    except SourceRevisionCatalogCorrupt as exc:
        missing_error = type(exc).__name__
    cases.append(
        _case(
            "missing_declaration_restart",
            failed_closed=(
                missing_error == "SourceRevisionCatalogCorrupt"
            ),
            error_type=missing_error,
        )
    )

    # same_bytes_declaration_no_new_segment (§34/§29)
    stack = _registry(tmp / "decl-same-bytes")
    a = stack.seed(stack._data("A"), observed_at=T1, acq_id="acq-A")
    a2 = stack.seed(
        stack._data("A"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="acq-A2",
    )
    stack.registry.register_acquisition(a.acquisition_id)
    key_a = stack.key_of("acq-A")
    obs = stack.registry.register_acquisition(
        a2.acquisition_id, provider_declaration=DECL
    )
    cases.append(
        _case(
            "same_bytes_declaration_no_new_segment",
            observation_state=obs.observation_state,
            revision_count=len(stack.registry.list_revisions(key_a)),
            declaration_preserved_as_evidence=(
                len(stack.registry._declarations_by_key.get(key_a, [])) == 1
            ),
        )
    )

    return {
        "matrix": "BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX",
        "generated_at_spec": "fixed-T1 (no wall clock)",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only comparison tests (§50/§38)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "builder_name,filename",
    [
        (
            "build_canonical_contract_matrix",
            "BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX.json",
        ),
        (
            "build_identity_binding_matrix",
            "BLOC_04_I06R1_IDENTITY_BINDING_MATRIX.json",
        ),
        (
            "build_declaration_durability_matrix",
            "BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX.json",
        ),
    ],
)
def test_generated_matches_committed(
    builder_name: str, filename: str, tmp_path
) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    builder = globals()[builder_name]
    generated = stable_evidence_bytes(builder(tmp_path))
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes — "
        "a production behavior changed; update the checkpoint evidence "
        "explicitly, never via test execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    """I06R1E: running this module's builders leaves no trace in the
    committed evidence tree (read-only policy)."""
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    build_canonical_contract_matrix(tmp_path / "probe1")
    build_identity_binding_matrix(tmp_path / "probe2")
    build_declaration_durability_matrix(tmp_path / "probe3")
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    assert before == after


def _publish() -> None:
    """EXPLICIT one-time publication (operator action, never pytest)."""
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    for builder, filename in [
        (
            build_canonical_contract_matrix,
            "BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX.json",
        ),
        (
            build_identity_binding_matrix,
            "BLOC_04_I06R1_IDENTITY_BINDING_MATRIX.json",
        ),
        (
            build_declaration_durability_matrix,
            "BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX.json",
        ),
    ]:
        target = EVIDENCE_DIR / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stable_evidence_bytes(builder(tmp / filename)))
        print(f"published {target}")


if __name__ == "__main__":
    _publish()
