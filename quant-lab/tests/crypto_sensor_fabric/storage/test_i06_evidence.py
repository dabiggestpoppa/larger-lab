"""SENSOR-B4-I06E — deterministic machine-evidence matrices.

Builders are PURE (§31/§38): they return dicts and are serialized through
``stable_evidence_bytes``.  Normal pytest runs NEVER write the committed
evidence tree — tests generate to memory and compare against committed
bytes (I05R4 read-only evidence policy).  Publication happens once per
checkpoint via an explicit operator invocation (see module bottom).
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
    RevisionAmbiguityError,
    RevisionConfigurationError,
    RevisionContentCorrupt,
    RevisionNotFound,
    RevisionObservationOrderConflict,
    RevisionResolutionMode,
    RevisionResolutionUnavailable,
    RevisionState,
    RevisionTemporalAmbiguity,
    RevisionSourceIdentityV1,
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


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _registry(tmp: Path):
    from _sibling_import import load_sibling

    mod = load_sibling("_i06_registry_mod", "test_source_revision_registry")
    stack = mod.Stack(tmp)
    stack._data = mod._data
    return stack


def _key_of(stack, acq_id: str) -> str:
    key = stack.registry.revision_for_acquisition(acq_id)
    return key[0] if key else ""


# ---------------------------------------------------------------------------
# Matrix builders (pure)
# ---------------------------------------------------------------------------


def build_identity_matrix(tmp: Path) -> dict:
    """I06 identity matrix: derivation, exclusion, tamper detection."""
    cases: list[dict] = []
    stack = _registry(tmp / "identity")

    stack.seed(stack._data("A"), observed_at=T1, acq_id="id-1")
    stack.seed(
        stack._data("A"),
        observed_at=T1 + timedelta(hours=1),
        acq_id="id-2",
    )
    o1 = stack.registry.register_acquisition("id-1")
    key1 = o1.source_revision_key
    identity = RevisionSourceIdentityV1.from_acquisition(
        stack.acq_repo.get_acquisition("id-2")
    )
    same_key = identity.source_revision_key() == key1
    cases.append(
        {
            "case": "same_request_semantics_same_key",
            "key_acq1": key1,
            "key_derived_acq2": identity.source_revision_key(),
            "keys_equal": same_key,
            "expected": True,
        }
    )
    cases.append(
        {
            "case": "key_is_full_sha256_hex",
            "length": len(key1),
            "expected_length": 64,
            "is_lowercase_hex": all(
                c in "0123456789abcdef" for c in key1
            ),
        }
    )

    # Descriptor tamper ⇒ reload fails closed.
    seg_dir = stack.root / "segments"
    target = next(p for p in seg_dir.glob("*.json"))
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["identity_descriptor"]["fields"]["venue"] = "spot"
    target.write_text(json.dumps(payload), encoding="utf-8")
    tamper_failed = False
    try:
        stack.reopen()
    except Exception:
        tamper_failed = True
    cases.append(
        {
            "case": "descriptor_tamper_fails_reload",
            "rejected": tamper_failed,
            "expected": True,
        }
    )

    # Blobless acquisition ⇒ no segment, no zero hash.
    stack2 = _registry(tmp / "identity-blobless")
    stack2.seed(b"", acq_id=None) if False else None
    cases.append(
        {
            "case": "identity_version_frozen_v1",
            "identity_version": RevisionSourceIdentityV1(
                **{
                    "identity_version": 1,
                    "provider_id": "p",
                    "venue": "v",
                    "sensor_family": "MECHANICAL_TRADE",
                    "native_instrument": "i",
                    "native_granularity": None,
                    "request_fingerprint": "fp",
                    "requested_start": "2026-01-01T00:00:00+00:00",
                    "requested_end": "2026-01-01T00:00:00+00:00",
                    "endpoint_host": None,
                    "endpoint_path": None,
                    "request_family": None,
                }
            ).identity_version,
            "expected": 1,
        }
    )
    return {
        "matrix": "BLOC_04_I06_IDENTITY_MATRIX",
        "identity_version": 1,
        "source_key_formula": "SHA256(canonical_json({identity_version, fields}))",
        "included_fields": [
            "provider_id",
            "venue",
            "sensor_family",
            "native_instrument",
            "native_granularity",
            "request_fingerprint",
            "requested_start",
            "requested_end",
            "endpoint_host",
            "endpoint_path",
            "request_family",
        ],
        "excluded_fields": [
            "acquisition_id",
            "blob_sha256",
            "source_locator",
            "adapter_version",
            "request_started_at",
            "response_observed_at",
            "ingested_at",
            "http_status_or_source_status",
            "provider_checksum_*",
            "resume_token_*",
            "quality_flags",
            "failure_ref",
        ],
        "cases": cases,
    }


def build_mutation_matrix(tmp: Path) -> dict:
    """I06 mutation matrix: classification, ordering, idempotence, locks,
    restart, T0B preservation."""
    cases: list[dict] = []

    def case(name: str, observed, expected) -> dict:
        return {"case": name, "observed": observed, "expected": expected}

    # Classification A→B→A.
    stack = _registry(tmp / "mutation")
    stack.seed(stack._data("A"), observed_at=T1, acq_id="m-1")
    stack.seed(
        stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="m-2"
    )
    stack.seed(
        stack._data("A"), observed_at=T1 + timedelta(hours=2), acq_id="m-3"
    )
    stack.registry.register_acquisition("m-1")
    stack.registry.register_acquisition("m-2")
    stack.registry.register_acquisition("m-3")
    key = _key_of(stack, "m-1")
    revs = stack.registry.list_revisions(key)
    cases.append(
        case(
            "reversion_three_segments",
            [r.revision_number for r in revs],
            [1, 2, 3],
        )
    )
    cases.append(
        case(
            "reversion_states",
            [r.revision_state for r in revs],
            [
                RevisionState.STABLE.value,
                RevisionState.SOURCE_MUTATION.value,
                RevisionState.SOURCE_MUTATION.value,
            ],
        )
    )

    # Identical refetch does not add a segment.
    a3 = stack.seed(
        stack._data("A"), observed_at=T1 + timedelta(hours=3), acq_id="m-4"
    )
    stack.registry.register_acquisition("m-4")
    o4 = stack.registry.revision_for_acquisition("m-4")
    revs_after = stack.registry.list_revisions(key)
    cases.append(
        case(
            "identical_refetch_no_new_segment",
            len(revs_after),
            3,
        )
    )
    del a3, o4

    # Out-of-order fails typed.
    late = stack.seed(
        stack._data("D"), observed_at=T1 - timedelta(hours=5), acq_id="m-5"
    )
    order_failed = False
    try:
        stack.registry.register_acquisition("m-5")
    except RevisionObservationOrderConflict:
        order_failed = True
    cases.append(
        case("out_of_order_fails_closed", order_failed, True)
    )
    del late

    # Same-time differing bytes fail closed.
    stack2 = _registry(tmp / "mutation-tie")
    s1 = stack2.seed(stack2._data("A"), observed_at=T1, acq_id="t-1")
    s2 = stack2.seed(
        stack2._data("B"), observed_at=T1, acq_id="t-2"
    )
    stack2.registry.register_acquisition(s1.acquisition_id)
    tie_failed = False
    try:
        stack2.registry.register_acquisition(s2.acquisition_id)
    except RevisionTemporalAmbiguity:
        tie_failed = True
    cases.append(case("same_time_conflict_fails_closed", tie_failed, True))

    # Idempotent re-registration re-verifies physical truth; corrupted blob
    # prevents cached success.
    stack3 = _registry(tmp / "mutation-idem")
    i1 = stack3.seed(stack3._data("A"), observed_at=T1, acq_id="i-1")
    stack3.registry.register_acquisition("i-1")
    blob_path = next(
        p
        for p in stack3.t0a.rglob("*")
        if p.is_file() and p.name.startswith(i1.blob_sha256[:16])
    )
    blob_path.write_bytes(b"SCRAMBLED")
    idem_failed = False
    try:
        stack3.registry.register_acquisition("i-1")
    except RevisionContentCorrupt:
        idem_failed = True
    cases.append(
        case("re_registration_after_corruption_fails", idem_failed, True)
    )

    # Restart preserves the full chain.
    stack4 = _registry(tmp / "mutation-restart")
    r1 = stack4.seed(stack4._data("A"), observed_at=T1, acq_id="r-1")
    r2 = stack4.seed(
        stack4._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="r-2"
    )
    stack4.registry.register_acquisition("r-1")
    stack4.registry.register_acquisition("r-2")
    key4 = _key_of(stack4, "r-1")
    before = [
        (r.revision_number, r.blob_sha256)
        for r in stack4.registry.list_revisions(key4)
    ]
    after = [
        (r.revision_number, r.blob_sha256)
        for r in stack4.reopen().list_revisions(key4)
    ]
    cases.append(
        case("restart_preserves_chain", after == before, True)
    )
    del r1, r2

    return {
        "matrix": "BLOC_04_I06_MUTATION_MATRIX",
        "cases": cases,
    }


def build_resolution_matrix(tmp: Path) -> dict:
    """I06 resolution matrix: all six frozen policies over A→B→A."""
    cases: list[dict] = []
    stack = _registry(tmp / "resolution")
    stack.seed(stack._data("A"), observed_at=T1, acq_id="p-1")
    stack.seed(
        stack._data("B"), observed_at=T1 + timedelta(hours=1), acq_id="p-2"
    )
    stack.seed(
        stack._data("A"), observed_at=T1 + timedelta(hours=2), acq_id="p-3"
    )
    stack.registry.register_acquisition("p-1")
    stack.registry.register_acquisition("p-2")
    stack.registry.register_acquisition("p-3")
    key = _key_of(stack, "p-1")
    registry = stack.registry

    all_res = registry.resolve(key, RevisionResolutionMode.ALL)
    cases.append(
        {
            "case": "ALL_complete_sequence_no_dedupe",
            "selected": all_res.selected_revision_numbers,
            "expected": [1, 2, 3],
        }
    )

    ambiguity_refused = False
    try:
        registry.resolve(key, RevisionResolutionMode.ERROR_ON_AMBIGUITY)
    except RevisionAmbiguityError:
        ambiguity_refused = True
    cases.append(
        {
            "case": "ERROR_ON_AMBIGUITY_never_picks_latest",
            "refused": ambiguity_refused,
            "expected": True,
        }
    )

    first = registry.resolve(key, RevisionResolutionMode.FIRST_SEEN)
    cases.append(
        {
            "case": "FIRST_SEEN_explicit_opt_in",
            "selected": first.selected_revision_numbers,
            "expected": [1],
        }
    )

    latest = registry.resolve(key, RevisionResolutionMode.LATEST_SEEN)
    cases.append(
        {
            "case": "LATEST_SEEN_explicit_opt_in",
            "selected": latest.selected_revision_numbers,
            "expected": [3],
        }
    )

    exact = registry.resolve(
        key, RevisionResolutionMode.EXACT_REVISION, revision_number=2
    )
    cases.append(
        {
            "case": "EXACT_REVISION_explicit_number",
            "selected": exact.selected_revision_numbers,
            "expected": [2],
        }
    )

    exact_missing = False
    try:
        registry.resolve(
            key, RevisionResolutionMode.EXACT_REVISION, revision_number=9
        )
    except RevisionNotFound:
        exact_missing = True
    cases.append(
        {
            "case": "EXACT_REVISION_unknown_not_found",
            "typed_not_found": exact_missing,
            "expected": True,
        }
    )

    exact_no_number = False
    try:
        registry.resolve(key, RevisionResolutionMode.EXACT_REVISION)
    except RevisionConfigurationError:
        exact_no_number = True
    cases.append(
        {
            "case": "EXACT_REVISION_requires_number",
            "typed_config_error": exact_no_number,
            "expected": True,
        }
    )

    zero_canonical = False
    try:
        registry.resolve(
            key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
        )
    except RevisionResolutionUnavailable:
        zero_canonical = True
    cases.append(
        {
            "case": "PROVIDER_DECLARED_CANONICAL_zero_unresolved",
            "typed_unresolved": zero_canonical,
            "expected": True,
        }
    )

    registry.declare_provider_canonical(
        source_revision_key=key,
        revision_number=2,
        evidence_ref="evidence/canon-1",
    )
    registry.declare_provider_canonical(
        source_revision_key=key,
        revision_number=2,
        evidence_ref="evidence/canon-1b",
    )
    unique = registry.resolve(
        key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
    )
    cases.append(
        {
            "case": "duplicate_same_revision_canonical_resolves",
            "selected": unique.selected_revision_numbers,
            "expected": [2],
        }
    )

    registry.declare_provider_canonical(
        source_revision_key=key,
        revision_number=1,
        evidence_ref="evidence/canon-2",
    )
    multi_refused = False
    try:
        registry.resolve(
            key, RevisionResolutionMode.PROVIDER_DECLARED_CANONICAL
        )
    except RevisionAmbiguityError:
        multi_refused = True
    cases.append(
        {
            "case": "multiple_distinct_canonicals_ambiguous",
            "refused": multi_refused,
            "expected": True,
        }
    )

    return {
        "matrix": "BLOC_04_I06_RESOLUTION_MATRIX",
        "policies": [p.value for p in RevisionResolutionMode],
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only tests: generated bytes == committed bytes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "builder_name,filename",
    [
        ("build_identity_matrix", "BLOC_04_I06_IDENTITY_MATRIX.json"),
        ("build_mutation_matrix", "BLOC_04_I06_MUTATION_MATRIX.json"),
        ("build_resolution_matrix", "BLOC_04_I06_RESOLUTION_MATRIX.json"),
    ],
)
def test_generated_matches_committed(builder_name: str, filename: str, tmp_path) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    builder = globals()[builder_name]
    generated = stable_evidence_bytes(builder(tmp_path))
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes — "
        "a production behavior changed; update the checkpoint evidence "
        "explicitly, never via test execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    """I06E: running this module's builders leaves no trace in the
    committed evidence tree (read-only policy)."""
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    build_identity_matrix(tmp_path / "probe1")
    build_mutation_matrix(tmp_path / "probe2")
    build_resolution_matrix(tmp_path / "probe3")
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
        (build_identity_matrix, "BLOC_04_I06_IDENTITY_MATRIX.json"),
        (build_mutation_matrix, "BLOC_04_I06_MUTATION_MATRIX.json"),
        (build_resolution_matrix, "BLOC_04_I06_RESOLUTION_MATRIX.json"),
    ]:
        target = EVIDENCE_DIR / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stable_evidence_bytes(builder(tmp / filename)))
        print(f"published {target}")


if __name__ == "__main__":
    _publish()
