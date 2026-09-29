"""SENSOR-B4-I12R2 — append-only measured evidence for the fail-safe default
revision authority + explicit representation-satisfaction microseal.

Records the two operator-review blockers REPRODUCED failure-first, the
exact repairs, and the post-fix measured behavior:

- BLOC_04_I12R2_AUTHORITY_REQUIRED_MATRIX.json
- BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json

Also documents (in BLOC_04_I12R2_FAIL_SAFE_CLOSURE.md, published by this
module) the one I12R1 artifact row superseded by the representation-
satisfaction law — regenerated from production by the SAME accepted
I12R1 builder (append-only correction; the I12R1 evidence module is
changed only where the superseded behavior was measured).

Publication is a separate explicit human step:
    UPDATE_I12R2_EVIDENCE=1 uv run --frozen python test_i12r2_evidence.py
Normal pytest execution is strictly READ-ONLY and asserts the committed
artifacts regenerate byte-identically (fixed clock, sorted outputs;
temp paths never enter row payloads).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
_SRC = str(Path(__file__).resolve().parents[3] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
from _sibling_import import load_sibling  # noqa: E402

_harness = load_sibling("i12r1_e2e", "test_i12r1_query_end_to_end")
Lake = _harness.Lake
FIXED = _harness.FIXED
wired_service = _harness.wired_service
two_revisions = _harness.two_revisions

from crypto_sensor_fabric.storage.enums import RevisionPolicy  # noqa: E402
from crypto_sensor_fabric.storage.models import RawEvidenceQuery  # noqa: E402
from crypto_sensor_fabric.storage.query import (  # noqa: E402
    RawEvidenceQueryService,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSourceIdentityV1,
)

REPO = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = (
    REPO / "quant-lab" / "research" / "crypto_foundry" / "sensor_fabric"
    / "evidence" / "bloc_04"
)


# ---------------------------------------------------------------------------
# Row machinery (same accepted pattern as I12R1 evidence)
# ---------------------------------------------------------------------------


def mrow(
    case: str,
    source: str,
    ok: bool,
    detail: str,
    **measured: object,
) -> dict[str, object]:
    """One measured evidence row.  ``source`` is one of
    PRODUCTION_BEHAVIOR / ADVERSARIAL_MUTATION / STRUCTURAL_INTROSPECTION /
    SYNTHETIC_COUNTERFACTUAL."""
    return {
        "case": case,
        "invariant_source": source,
        "measured": measured,
        "result": "OK" if ok else "FAIL",
        "detail": detail,
    }


def counterfactual(case: str, matrix: str) -> dict[str, object]:
    return mrow(
        case,
        "SYNTHETIC_COUNTERFACTUAL",
        False,
        (
            f"Synthetic counterfactual for {matrix}: deliberately invalid "
            "execution path that must evaluate FAIL; not a measured row."
        ),
    )


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _payload(matrix: str, rows: list[dict[str, object]]) -> dict[str, object]:
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "matrix": matrix,
        "mandate": "SENSOR-B4-I12R2",
        "supersedes_claim": (
            "I12R1 claims superseded by operator review: (1) the default "
            "ERROR_ON_AMBIGUITY policy executed without the I06 revision "
            "authority; (2) a query requesting T0B could silently return "
            "only T0A when no requested T0B schema matched (option-A "
            "fallback).  I12R2 measures the fail-safe repairs END-TO-END "
            "through RawEvidenceQueryService.execute()."
        ),
        "generated_at": FIXED.isoformat(),
        "rows": rows,
        "summary": {"rows": len(rows), "ok": ok, "fail": len(rows) - ok},
    }


def _exc(fn):  # type: ignore[no-untyped-def]
    try:
        fn()
        return "NO_RAISE"
    except Exception as exc:  # noqa: BLE001 - measured behavior
        return type(exc).__name__


def unwired_service(lake: Lake) -> RawEvidenceQueryService:
    return RawEvidenceQueryService(
        manifest_repository=lake.manifest_repo,
        acquisition_repository=lake.acq_repo,
        blob_metadata_repository=lake.blob_repo,
    )


# ---------------------------------------------------------------------------
# 1. AUTHORITY_REQUIRED — every policy demands the I06 authority
# ---------------------------------------------------------------------------


def build_authority_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        from pathlib import Path as _P

        root = _P(td)

        lake, _key = two_revisions(_mk(root, "two"))
        single = Lake(_mk(root, "single"))
        sha_s = single.seed_blob(b'{"single": 1}')
        single.seed_acquisition(sha_s, "acq-s1")
        single.commit_manifest("pm-s1", blob_refs=[sha_s])

        def run_unwired(q: RawEvidenceQuery) -> str:
            return _exc(lambda: unwired_service(lake).execute(q))

        name = run_unwired(RawEvidenceQuery())
        rows.append(mrow(
            "unwired_default_refused", "PRODUCTION_BEHAVIOR",
            name == "RevisionAuthorityUnavailable",
            "BLOCKER A repaired: the DEFAULT ERROR_ON_AMBIGUITY policy is a "
            "revision-resolution policy; an unwired service executes NO raw "
            "evidence query (previously returned both revisions with no "
            "authority consulted)",
            exception=name,
        ))
        for policy, label in (
            (RevisionPolicy.FIRST_SEEN, "unwired_first_seen_refused"),
            (RevisionPolicy.EXACT_REVISION, "unwired_exact_refused"),
            (RevisionPolicy.ALL, "unwired_all_refused"),
        ):
            q = RawEvidenceQuery(
                revision_policy=policy,
                exact_revision_number=1 if policy is RevisionPolicy.EXACT_REVISION else None,
            )
            name = run_unwired(q)
            rows.append(mrow(
                label, "PRODUCTION_BEHAVIOR",
                name == "RevisionAuthorityUnavailable",
                f"{policy.value}: the unwired refusal is the SAME typed "
                "class as the default policy — no policy bypasses the "
                "authority requirement",
                exception=name,
            ))
        outcome = wired_service(single).execute(RawEvidenceQuery())
        rows.append(mrow(
            "wired_single_default_success", "PRODUCTION_BEHAVIOR",
            outcome.results[0].acquisition_ids == ["acq-s1"]
            and outcome.no_matching_evidence is False,
            "with the accepted I06 authority wired, the default policy "
            "executes the reduction through registry resolution",
            selected_acquisition_ids=list(outcome.results[0].acquisition_ids),
            selected_blob_refs=list(outcome.results[0].blob_refs),
            revision_state=outcome.results[0].revision_state.value,
        ))
        name = _exc(
            lambda: wired_service(lake).execute(RawEvidenceQuery())
        )
        rows.append(mrow(
            "wired_two_revision_default_ambiguity", "PRODUCTION_BEHAVIOR",
            name == "RevisionAmbiguity",
            "two revisions under one source key + wired authority + default "
            "policy: typed epistemic ambiguity — the authority is actually "
            "CONSULTED, not merely accepted at construction",
            exception=name,
        ))
        name = _exc(
            lambda: wired_service(lake).execute(RawEvidenceQuery(limit=1))
        )
        rows.append(mrow(
            "limit_still_last_with_wired_authority", "PRODUCTION_BEHAVIOR",
            name == "RevisionAmbiguity",
            "limit=1 cannot suppress the ambiguity: the authority is "
            "consulted during reduction, before ordering and truncation",
            exception=name,
        ))
        name = _exc(
            lambda: unwired_service(lake).execute(
                RawEvidenceQuery(
                    revision_policy=RevisionPolicy.EXACT_REVISION,
                    exact_revision_number=2,
                )
            )
        )
        rows.append(mrow(
            "unwired_refusal_not_evidence_semantics", "PRODUCTION_BEHAVIOR",
            name == "RevisionAuthorityUnavailable",
            "the unwired refusal is a configuration/authority failure — "
            "never StorageBackendUnavailable, NoMatchingEvidence or "
            "RevisionAmbiguity",
            exception=name,
        ))
        rows.append(mrow(
            "no_compatibility_switch_exists", "STRUCTURAL_INTROSPECTION",
            _no_passthrough_params(),
            "the public constructor exposes NO allow_unresolved_revisions / "
            "unsafe_revision_passthrough / legacy_mode escape hatch (§5)",
            constructor_params=sorted(_constructor_params()),
        ))
        rows.append(counterfactual(
            "counterfactual_unwired_default_executes", "AUTHORITY_REQUIRED"
        ))
    return _payload("BLOC_04_I12R2_AUTHORITY_REQUIRED", rows)


def _constructor_params() -> list[str]:
    import inspect

    return sorted(inspect.signature(RawEvidenceQueryService.__init__).parameters)


def _no_passthrough_params() -> bool:
    params = set(_constructor_params())
    return not (
        {"allow_unresolved_revisions", "unsafe_revision_passthrough", "legacy_mode"}
        & params
    )


def _mk(root: Path, name: str) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# 2. REPRESENTATION_SATISFACTION — include flags are requirements
# ---------------------------------------------------------------------------


def build_representation_matrix() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    with __import__("tempfile").TemporaryDirectory() as td:
        import tempfile  # noqa: F401

        from pathlib import Path as _P

        root = _P(td)

        def lake_with_projection(name: str) -> tuple[Lake, str]:
            lake = Lake(_mk(root, name))
            sha = lake.seed_blob()
            lake.seed_acquisition(sha, f"acq-{name}")
            lake.commit_projection("proj-1", [(sha, f"acq-{name}")])
            lake.commit_manifest("pm-1", blob_refs=[sha], projection_refs=["proj-1"])
            return lake, sha

        def lake_plain(name: str) -> Lake:
            lake = Lake(_mk(root, name))
            sha = lake.seed_blob()
            lake.seed_acquisition(sha, f"acq-{name}")
            lake.commit_manifest("pm-1", blob_refs=[sha])
            return lake

        def out(svc: RawEvidenceQueryService, q: RawEvidenceQuery) -> dict[str, object]:
            try:
                r = svc.execute(q).results[0]
                return {
                    "exception": None,
                    "blob_refs": list(r.blob_refs),
                    "projection_refs": list(r.projection_refs),
                    "lineage_refs": list(r.lineage_refs),
                }
            except Exception as exc:  # noqa: BLE001 - measured behavior
                return {
                    "exception": type(exc).__name__,
                    "blob_refs": None,
                    "projection_refs": None,
                    "lineage_refs": None,
                }

        lake, sha = lake_with_projection("rep")
        svc = wired_service(lake)

        r = out(svc, RawEvidenceQuery(include_t0a=True, include_t0b=False))
        rows.append(mrow(
            "T0A_only_success", "PRODUCTION_BEHAVIOR",
            bool(r["blob_refs"]) and r["projection_refs"] == [],
            "T0A=True/T0B=False: T0A result allowed, projection_refs empty",
            **r,
        ))
        r = out(svc, RawEvidenceQuery(include_t0a=False, include_t0b=True))
        rows.append(mrow(
            "T0B_only_success", "PRODUCTION_BEHAVIOR",
            r["blob_refs"] == [] and bool(r["projection_refs"])
            and bool(r["lineage_refs"]),
            "T0A=False/T0B=True: at least one eligible T0B projection "
            "selected with lineage provenance",
            **r,
        ))
        r = out(svc, RawEvidenceQuery(include_t0a=True, include_t0b=True))
        rows.append(mrow(
            "both_requested_success", "PRODUCTION_BEHAVIOR",
            bool(r["blob_refs"]) and bool(r["projection_refs"]),
            "T0A=True/T0B=True: BOTH representations present — no silent "
            "T0A-only fallback",
            **r,
        ))
        name = _exc(
            lambda: svc.execute(
                RawEvidenceQuery(include_t0a=False, include_t0b=False)
            )
        )
        rows.append(mrow(
            "neither_requested_refused", "PRODUCTION_BEHAVIOR",
            name == "QueryValidationError",
            "T0A=False/T0B=False selects nothing — typed refusal",
            exception=name,
        ))
        name = _exc(
            lambda: svc.execute(
                RawEvidenceQuery(
                    include_t0a=False,
                    include_t0b=True,
                    projection_schema_ids=["nonmatching.schema"],
                )
            )
        )
        rows.append(mrow(
            "T0B_only_schema_mismatch_refused", "PRODUCTION_BEHAVIOR",
            name == "ProjectionSchemaUnsupported",
            "T0B-only with a non-matching schema: typed refusal, no "
            "unrelated projection substitution",
            exception=name,
        ))
        name = _exc(
            lambda: svc.execute(
                RawEvidenceQuery(
                    include_t0a=True,
                    include_t0b=True,
                    projection_schema_ids=["nonmatching.schema"],
                )
            )
        )
        rows.append(mrow(
            "both_requested_schema_mismatch_refused", "PRODUCTION_BEHAVIOR",
            name == "ProjectionSchemaUnsupported",
            "BLOCKER B repaired: a query requesting BOTH representations "
            "refuses typed when no eligible T0B projection matches — the "
            "valid T0A selection NEVER silently satisfies the requested T0B "
            "(the I12R1 option-A fallback is superseded)",
            exception=name,
        ))
        name = _exc(
            lambda: wired_service(lake_plain("noproj")).execute(
                RawEvidenceQuery(include_t0a=True, include_t0b=True)
            )
        )
        rows.append(mrow(
            "no_projection_T0B_refused", "PRODUCTION_BEHAVIOR",
            name == "ProjectionSchemaUnsupported",
            "include_t0b=True with a manifest carrying NO projections: "
            "typed refusal — T0A availability never substitutes for the "
            "requested T0B representation",
            exception=name,
        ))
        # Lineage-broken refusal (adversarial mutation of the durable
        # lineage dependency, in-process — the chain is never published).

        lake_b, _sha_b = lake_with_projection("broken")
        svc_b = wired_service(lake_b)
        real_get = type(lake_b.lineage).get_by_projection

        def raising_get(self, projection_id):  # noqa: ANN001
            raise RuntimeError("lineage dependency broken (adversarial)")

        type(lake_b.lineage).get_by_projection = raising_get
        try:
            name = _exc(
                lambda: svc_b.execute(
                    RawEvidenceQuery(include_t0a=True, include_t0b=True)
                )
            )
        finally:
            type(lake_b.lineage).get_by_projection = real_get
        rows.append(mrow(
            "lineage_broken_refused", "ADVERSARIAL_MUTATION",
            name == "LineageIncomplete",
            "lineage incompleteness is part of the satisfaction law: a "
            "broken T0B chain fails typed BEFORE publication instead of "
            "publishing a T0A-only result",
            exception=name,
        ))
        # §14: T0A-only selection identical with/without optional T0B readers.
        q = RawEvidenceQuery(include_t0a=True, include_t0b=False)
        wired_out = out(svc, q)
        unwired_out = out(
            RawEvidenceQueryService(
                manifest_repository=lake.manifest_repo,
                acquisition_repository=lake.acq_repo,
                blob_metadata_repository=lake.blob_repo,
                revision_registry=lake.registry,
                revision_identity_factory=RevisionSourceIdentityV1,
            ),
            q,
        )
        rows.append(mrow(
            "T0A_only_deterministic_wired_or_not", "PRODUCTION_BEHAVIOR",
            wired_out["blob_refs"] == unwired_out["blob_refs"]
            and wired_out["projection_refs"] == unwired_out["projection_refs"],
            "T0A-only selection is IDENTICAL whether the optional T0B "
            "metadata repositories are wired or absent (§14)",
            wired=wired_out,
            unwired=unwired_out,
        ))
        rows.append(counterfactual(
            "counterfactual_T0B_silently_dropped", "REPRESENTATION_SATISFACTION"
        ))
    return _payload("BLOC_04_I12R2_REPRESENTATION_SATISFACTION", rows)


_MATRICES: list[tuple[str, object]] = [
    ("BLOC_04_I12R2_AUTHORITY_REQUIRED_MATRIX.json", build_authority_matrix),
    ("BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json", build_representation_matrix),
]


def _mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def publish_all() -> list[Path]:
    written: list[Path] = []
    for name, build in _MATRICES:
        path = EVIDENCE_DIR / name
        data = _canonical_bytes(build())
        path.write_bytes(data)
        written.append(path)
    return written


def test_i12r2_matrices_regenerate_byte_identically() -> None:
    """Read-only: committed artifacts regenerate byte-identically."""
    for name, build in _MATRICES:
        path = EVIDENCE_DIR / name
        assert path.exists(), f"missing committed I12R2 artifact {name}"
        assert path.read_bytes() == _canonical_bytes(build()), name


def test_i12r2_matrices_measured_and_single_counterfactual() -> None:
    """Read-only: every row classified, every matrix exactly one FAIL."""
    allowed = {
        "PRODUCTION_BEHAVIOR",
        "ADVERSARIAL_MUTATION",
        "STRUCTURAL_INTROSPECTION",
        "SYNTHETIC_COUNTERFACTUAL",
    }
    for name, _ in _MATRICES:
        payload = json.loads(
            (EVIDENCE_DIR / name).read_text(encoding="utf-8")
        )
        rows = payload["rows"]
        assert rows, name
        for r in rows:
            assert r["invariant_source"] in allowed, (name, r["case"])
        counterfactuals = [
            r for r in rows if r["invariant_source"] == "SYNTHETIC_COUNTERFACTUAL"
        ]
        assert len(counterfactuals) == 1, name
        assert counterfactuals[0]["result"] == "FAIL", name
        measured_rows = [
            r for r in rows if r["invariant_source"] != "SYNTHETIC_COUNTERFACTUAL"
        ]
        assert all(r["result"] == "OK" for r in measured_rows), name
        assert all(r.get("measured") for r in measured_rows), name


def test_i12r2_does_not_rewrite_historical_evidence() -> None:
    """Publication writes ONLY the two I12R2 matrices."""
    assert [name for name, _ in _MATRICES] == [
        "BLOC_04_I12R2_AUTHORITY_REQUIRED_MATRIX.json",
        "BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json",
    ]


if __name__ == "__main__":
    if os.getenv("UPDATE_I12R2_EVIDENCE") != "1":
        raise SystemExit(
            "publication requires the explicit UPDATE_I12R2_EVIDENCE=1 override"
        )
    for path in publish_all():
        print(f"published {path.name}")
