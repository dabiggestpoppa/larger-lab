"""SENSOR-B5-P3-R1 — production consumer contract laws (A1.1–A1.5).

Every assertion here is executed.  Two of them exist specifically to keep the
documentation honest:

* ``test_model_construct_bypasses_every_law`` and
  ``test_model_copy_update_bypasses_validation`` *succeed* at building an object
  the schema forbids.  A frozen pydantic model is a data representation, not an
  authorization capability, and a suite that claimed otherwise would be lying
  about the boundary.  What protects the pipeline is that the policy never reads
  a verdict as input and revalidates every request -- proved in
  ``test_b5_p3_consumer_policy.py``.
* ``test_importing_the_models_does_not_load_the_verifier`` runs in a **clean
  subprocess**, because an in-process check would be contaminated by whichever
  module this suite imported first.

Fixtures are synthetic and labelled as such.  A record here is built directly
through ``T1TradeRecord.model_validate`` with ``NATIVE_ONLY`` status: no
normalizer runs, no registry exists, and no canonical side is claimed.
"""

from __future__ import annotations

import ast
import os
import pathlib
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.consumer.models import (
    TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
    ConsumerDecision,
    ConsumerEvidenceReference,
    ConsumerRefusalReason,
    ConsumerRequest,
    ConsumerVerdict,
    CustodyAuthorityBasis,
)
from crypto_sensor_fabric.normalization.enums import (
    LineageState,
    NormalizationQualityFlag,
    NormalizationStatus,
    QualityDimensionState,
)
from crypto_sensor_fabric.normalization.sensors.trade import T1TradeRecord
from crypto_sensor_fabric.storage import CoverageState, RevisionState

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
MODELS_PATH = (
    QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "consumer" / "models.py"
)
CONSUMER_PACKAGE = MODELS_PATH.parent
CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64
ARTIFACT = b"synthetic registry bytes (not a provider document)"


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------


def _quality() -> dict[str, Any]:
    return {name: QualityDimensionState.UNKNOWN for name in (
        "identity_quality",
        "time_quality",
        "semantic_quality",
        "unit_quality",
        "lineage_quality",
        "source_integrity_quality",
        "coverage_quality",
        "replay_quality",
    )}


def _trade_record(**overrides: Any) -> T1TradeRecord:
    payload: dict[str, Any] = {
        "sensor_family": SensorFamily.MECHANICAL_TRADE,
        "provider": "BINANCE_USDM",
        "venue": "BINANCE",
        "native_instrument": "BTCUSDT",
        "normalization_generation": "gen-p3-contract",
        "source_revision_id": "rev-p3-contract",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "time": {},
        "native_values": (),
        "normalization_status": NormalizationStatus.NATIVE_ONLY,
        "lineage_state": LineageState.LINEAGE_COMPLETE,
        "lineage": {
            "raw_projection_refs": ("proj:p3:1",),
            "acquisition_refs": ("acq:p3:1",),
            "evidence_blob_hashes": (DIGEST,),
            "code_version": "p3-contract",
            "config_version": "cfg-p3-contract",
        },
        "quality": _quality(),
        "quality_flags": (NormalizationQualityFlag.LINEAGE_COMPLETE,),
        "versions": {},
    }
    payload.update(overrides)
    return T1TradeRecord.model_validate(payload)


def _request(**overrides: Any) -> ConsumerRequest:
    payload: dict[str, Any] = {
        "record": _trade_record(),
        "artifact_bytes": ARTIFACT,
        "knowledge_cutoff": CUTOFF,
    }
    payload.update(overrides)
    return ConsumerRequest(**payload)


def _verdict(**overrides: Any) -> ConsumerVerdict:
    payload: dict[str, Any] = {
        "decision": ConsumerDecision.ACCEPT_FIELD_BINDING,
        "verified_field_allowlist": ("aggressor_side",),
        "unverified_dimensions": ("SOURCE_LINEAGE",),
        "pit_status": "ADMISSIBLE",
        "replay_status": "ELIGIBLE",
        "custody_status": "VERIFIED",
        "custody_source_authorization_status": CustodyAuthorityBasis.AUTHORIZED,
        "custody_source_authorized": True,
    }
    payload.update(overrides)
    return ConsumerVerdict(**payload)


# ---------------------------------------------------------------------------
# A1.2 / A1.3 -- the vocabularies are exactly what the design froze
# ---------------------------------------------------------------------------


def test_decision_has_exactly_three_members() -> None:
    assert [member.value for member in ConsumerDecision] == [
        "ACCEPT_FIELD_BINDING",
        "REFUSE",
        "INTEGRATION_REQUIRED",
    ]
    assert {member.name for member in ConsumerDecision} == {
        "ACCEPT_FIELD_BINDING",
        "REFUSE",
        "INTEGRATION_REQUIRED",
    }


def test_no_bare_accept_or_authorized_decision_exists() -> None:
    for absent in ("ACCEPT", "AUTHORIZED", "TRUSTED", "ACCEPT_WHOLE_RECORD"):
        assert absent not in ConsumerDecision.__members__, absent


def test_custody_basis_has_exactly_three_members() -> None:
    assert {member.value for member in CustodyAuthorityBasis} == {
        "AUTHORIZED",
        "INTEGRATION_REQUIRED",
        "UNAUTHORIZED",
    }


def test_synthetic_basis_does_not_exist_in_production() -> None:
    for absent in ("SYNTHETIC_TEST_ONLY", "SYNTHETIC", "TEST_ONLY"):
        assert absent not in CustodyAuthorityBasis.__members__, absent
    # The name may appear in PROSE (it is documented as deliberately absent);
    # it may not appear as a class-body string value, which is what an enum
    # member is.  Checking the declaration form, not the word, is the difference
    # between a law and a lint.
    tree = ast.parse(MODELS_PATH.read_text(encoding="utf-8"))
    declared: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            value = statement.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                declared.append(value.value)
    offending = [value for value in declared if "SYNTHETIC" in value]
    assert offending == [], offending


def test_refusal_vocabulary_covers_the_design_codes() -> None:
    required = {
        "FORGED_TRUST_SCOPE",
        "EMPTY_UNVERIFIED_DIMENSIONS",
        "EVIDENCE_BYTES_MISSING",
        "EVIDENCE_BYTES_MISMATCH",
        "FIELD_NOT_IN_ALLOWLIST",
        "PIT_INADMISSIBLE",
        "REPLAY_BLOCKED",
        "NAIVE_CUTOFF",
        "CACHED_VERDICT_DIVERGENCE",
        "VERIFICATION_FAILED",
        "VERIFIER_CRASH",
        "UNAUTHORIZED_CUSTODY_SOURCE",
    }
    assert required <= {member.value for member in ConsumerRefusalReason}
    # the two additions are named by the later rungs' controls, not invented here
    assert {"TRUSTED_CONTEXT_MISMATCH", "EVIDENCE_NOT_BOUND_TO_ARTIFACT"} <= {
        member.value for member in ConsumerRefusalReason
    }


def test_trust_scope_constant_matches_the_verifier_scope() -> None:
    from crypto_sensor_fabric.normalization.sensors.verification import (
        TRUST_SCOPE_ECONOMIC_FIELD_BINDING as VERIFIER_SCOPE,
    )

    assert TRUST_SCOPE_ECONOMIC_FIELD_BINDING == VERIFIER_SCOPE


# ---------------------------------------------------------------------------
# A1.1 -- the request cannot carry authority, a verdict or a callback
# ---------------------------------------------------------------------------

_FORBIDDEN_TYPE_NAMES = {
    "RecordVerification",
    "ConsumerVerdict",
    "SemanticAuthority",
    "TrustedAuthorityContext",
    "MappingProvenance",
    "CustodyAuthorityDerivation",
    "CustodyAuthorityIdentity",
    "ConsumerDecision",
    "CustodyAuthorityBasis",
    "Callable",
    "Any",
}

_FORBIDDEN_FIELD_NAMES = {
    "authority",
    "authorized",
    "custody_authority",
    "trusted",
    "verdict",
    "decision",
    "callback",
    "rederive",
    "candidate",
    "synthetic",
}


def _annotation_names(annotation: object) -> set[str]:
    """Every type name reachable from one annotation, without following models."""
    names: set[str] = set()
    stack: list[object] = [annotation]
    seen: set[int] = set()
    while stack:
        item = stack.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if hasattr(item, "model_fields"):
            # A nested pydantic model is inspected by its own row, not here.
            names.add(getattr(item, "__name__", str(item)))
            continue
        name = getattr(item, "__name__", None)
        if name:
            names.add(name)
        for argument in getattr(item, "__args__", ()) or ():
            stack.append(argument)
    return names


def test_request_annotations_name_no_authority_verdict_or_callback() -> None:
    for field_name, field in ConsumerRequest.model_fields.items():
        reached = _annotation_names(field.annotation)
        offending = reached & _FORBIDDEN_TYPE_NAMES
        assert not offending, (field_name, sorted(offending))


def test_request_field_names_do_not_read_as_authority() -> None:
    for name in ConsumerRequest.model_fields:
        assert name not in _FORBIDDEN_FIELD_NAMES, name


def test_request_record_slot_is_exactly_the_two_t1_types() -> None:
    annotation = ConsumerRequest.model_fields["record"].annotation
    assert set(getattr(annotation, "__args__", ())) == {T1TradeRecord} or {
        getattr(item, "__name__", "") for item in annotation.__args__
    } == {"T1TradeRecord", "T1LiquidationRecord"}


def test_request_exposes_no_callable_method_that_derives_a_verdict() -> None:
    for name in dir(ConsumerRequest):
        if name.startswith("_"):
            continue
        assert not name.startswith("rederive"), name
        assert name not in {"evaluate", "derive", "verify"}, name


def test_a_verdict_cannot_be_smuggled_into_a_request() -> None:
    with pytest.raises(ValidationError):
        _request(verdict=_verdict())
    with pytest.raises(ValidationError):
        _request(decision="ACCEPT_FIELD_BINDING")
    with pytest.raises(ValidationError):
        _request(custody_source_authorized=True)
    with pytest.raises(ValidationError):
        _request(custody_authority=object())


def test_a_non_t1_record_cannot_be_smuggled_into_a_request() -> None:
    with pytest.raises(ValidationError):
        _request(record={"sensor_family": "MECHANICAL_TRADE"})
    with pytest.raises(ValidationError):
        _request(record=_verdict())


# ---------------------------------------------------------------------------
# A1.4 -- model laws, measured
# ---------------------------------------------------------------------------


def test_models_are_frozen() -> None:
    request = _request()
    with pytest.raises(ValidationError):
        request.artifact_bytes = b"other"  # type: ignore[misc]
    verdict = _verdict()
    with pytest.raises(ValidationError):
        verdict.decision = ConsumerDecision.REFUSE  # type: ignore[misc]
    reference = ConsumerEvidenceReference(reference="ref-1", approved_digest=DIGEST)
    with pytest.raises(ValidationError):
        reference.approved_digest = OTHER_DIGEST  # type: ignore[misc]


def test_unknown_fields_are_refused_everywhere() -> None:
    with pytest.raises(ValidationError):
        _request(unexpected="x")
    with pytest.raises(ValidationError):
        _verdict(unexpected="x")
    with pytest.raises(ValidationError):
        ConsumerEvidenceReference(
            reference="ref-1", approved_digest=DIGEST, unexpected="x"
        )


def test_naive_cutoff_is_refused() -> None:
    with pytest.raises(ValidationError):
        _request(knowledge_cutoff=datetime(2026, 6, 1, 12, 0))


def test_bare_date_cutoff_is_refused() -> None:
    with pytest.raises(ValidationError):
        _request(knowledge_cutoff=date(2026, 6, 1))


def test_date_only_string_cutoff_is_refused() -> None:
    with pytest.raises(ValidationError):
        _request(knowledge_cutoff="2026-06-01")


def test_objective_pydantic_would_have_accepted_a_bare_date() -> None:
    """The refusal is ours, not the library's -- measured, not assumed."""
    from pydantic import BaseModel

    class _Probe(BaseModel):
        at: datetime

    coerced = _Probe(at=date(2026, 6, 1))
    assert coerced.at == datetime(2026, 6, 1, 0, 0)


def test_offset_cutoff_is_normalised_to_utc() -> None:
    offset = timezone(timedelta(hours=2))
    request = _request(knowledge_cutoff=datetime(2026, 6, 1, 14, 0, tzinfo=offset))
    assert request.knowledge_cutoff == datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    assert request.knowledge_cutoff.utcoffset() == timedelta(0)


def test_arbitrary_binary_bytes_round_trip() -> None:
    binary = bytes(range(256))
    request = _request(artifact_bytes=binary)
    serialised = request.model_dump_json()
    restored = ConsumerRequest.model_validate_json(serialised)
    assert restored.artifact_bytes == binary
    assert restored == request


def test_canonical_serialisation_is_stable() -> None:
    first = _request().model_dump_json()
    second = _request().model_dump_json()
    assert first == second


def test_artifact_bytes_are_hidden_from_repr() -> None:
    marker = b"SECRET-ARTIFACT-MARKER"
    request = _request(artifact_bytes=marker)
    assert "SECRET-ARTIFACT-MARKER" not in repr(request)
    assert "SECRET-ARTIFACT-MARKER" not in str(request)


def test_claimed_manifest_bytes_are_hidden_from_repr() -> None:
    marker = b"SECRET-MANIFEST-MARKER"
    request = _request(claimed_manifest_bytes=marker)
    assert "SECRET-MANIFEST-MARKER" not in repr(request)


def test_evidence_references_must_be_canonical_and_unique() -> None:
    a = ConsumerEvidenceReference(reference="alpha", approved_digest=DIGEST)
    b = ConsumerEvidenceReference(reference="beta", approved_digest=OTHER_DIGEST)
    _request(evidence_references=(a, b))
    with pytest.raises(ValidationError):
        _request(evidence_references=(b, a))
    with pytest.raises(ValidationError):
        _request(evidence_references=(a, a))


def test_evidence_reference_digest_must_be_a_sha256_hex_digest() -> None:
    for bad in ("not-a-digest", "A" * 64, "a" * 63, "a" * 65):
        with pytest.raises(ValidationError):
            ConsumerEvidenceReference(reference="ref-1", approved_digest=bad)


def test_required_fields_must_be_unique() -> None:
    with pytest.raises(ValidationError):
        _request(required_fields=("aggressor_side", "aggressor_side"))


def test_verdict_laws_hold_on_the_ordinary_path() -> None:
    _verdict()
    with pytest.raises(ValidationError):
        _verdict(decision=ConsumerDecision.REFUSE)
    with pytest.raises(ValidationError):
        _verdict(refusal_reason=ConsumerRefusalReason.VERIFICATION_FAILED)
    # A refusal may name any basis: violating a rule is not integrating.
    _verdict(
        decision=ConsumerDecision.REFUSE,
        refusal_reason=ConsumerRefusalReason.VERIFICATION_FAILED,
        custody_source_authorization_status=CustodyAuthorityBasis.INTEGRATION_REQUIRED,
        custody_source_authorized=False,
    )
    # an empty dimension list is not an acceptance
    with pytest.raises(ValidationError):
        _verdict(unverified_dimensions=())
    # an acceptance that binds nothing is not an acceptance
    with pytest.raises(ValidationError):
        _verdict(verified_field_allowlist=())


def test_verdict_boolean_and_basis_may_not_disagree() -> None:
    with pytest.raises(ValidationError):
        _verdict(custody_source_authorized=False)
    # The honest production pair: everything verified, no authority yet.
    _verdict(
        decision=ConsumerDecision.INTEGRATION_REQUIRED,
        custody_source_authorization_status=CustodyAuthorityBasis.INTEGRATION_REQUIRED,
        custody_source_authorized=False,
    )
    with pytest.raises(ValidationError):
        _verdict(
            decision=ConsumerDecision.REFUSE,
            refusal_reason=ConsumerRefusalReason.VERIFICATION_FAILED,
            custody_source_authorization_status=CustodyAuthorityBasis.AUTHORIZED,
            custody_source_authorized=True,
        )


def test_verdict_refuses_a_widened_trust_scope() -> None:
    with pytest.raises(ValidationError):
        _verdict(trust_scope="FULL_RECORD_TRUST")


def test_verdict_refusal_detail_is_bounded() -> None:
    with pytest.raises(ValidationError):
        _verdict(
            decision=ConsumerDecision.REFUSE,
            refusal_reason=ConsumerRefusalReason.VERIFIER_CRASH,
            refusal_detail="x" * 401,
            custody_source_authorization_status=CustodyAuthorityBasis.UNAUTHORIZED,
            custody_source_authorized=False,
        )


# ---------------------------------------------------------------------------
# Section 6 of the Rung 1 record, preserved: the bypasses that DO work
# ---------------------------------------------------------------------------


def test_model_construct_bypasses_every_law() -> None:
    """A forged object of the right class exists.  That is the honest boundary."""
    forged = ConsumerVerdict.model_construct(
        decision="ACCEPT_FIELD_BINDING",
        trust_scope="FULL_RECORD_TRUST",
        verified_field_allowlist=(),
        unverified_dimensions=(),
        pit_status="ADMISSIBLE",
        replay_status="ELIGIBLE",
        custody_status="VERIFIED",
        custody_source_authorization_status="AUTHORIZED",
        custody_source_authorized=True,
        refusal_reason=None,
        refusal_detail=None,
        custody_authorization_detail=None,
    )
    assert isinstance(forged, ConsumerVerdict)
    assert forged.trust_scope == "FULL_RECORD_TRUST"  # no law ran
    assert forged.decision == "ACCEPT_FIELD_BINDING"  # a raw string, not the enum


def test_model_copy_update_bypasses_validation() -> None:
    copy = _verdict().model_copy(update={"trust_scope": "FULL_RECORD_TRUST"})
    assert copy.trust_scope == "FULL_RECORD_TRUST"
    with pytest.raises(ValidationError):
        ConsumerVerdict.model_validate(copy.model_dump())


def test_the_boundary_is_revalidation_not_immutability() -> None:
    """The request survives a round-trip only if it was valid to begin with."""
    forged = ConsumerRequest.model_construct(
        record=_trade_record(),
        artifact_bytes=ARTIFACT,
        required_fields=(),
        evidence_references=(),
        knowledge_cutoff=datetime(2026, 6, 1, 12, 0),  # naive: no validator ran
        replay_evidence=None,
        claimed_manifest_bytes=None,
    )
    assert forged.knowledge_cutoff.tzinfo is None
    with pytest.raises(ValidationError):
        ConsumerRequest.model_validate(forged.model_dump())


# ---------------------------------------------------------------------------
# A1.5 -- import isolation, measured in a clean subprocess
# ---------------------------------------------------------------------------


def test_importing_the_models_does_not_load_the_verifier() -> None:
    program = (
        "import sys\n"
        "import crypto_sensor_fabric.normalization.consumer.models\n"
        "loaded = [name for name in sys.modules "
        "if name.endswith('sensors.verification')]\n"
        "print(repr(loaded))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program],
        cwd=str(QUANT_LAB),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": str(QUANT_LAB / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", result.stdout


def test_the_models_module_imports_no_io_hashing_or_clock() -> None:
    tree = ast.parse(MODELS_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in (
        "os",
        "io",
        "socket",
        "pathlib",
        "subprocess",
        "hashlib",
        "json",
        "yaml",
        "urllib",
        "shutil",
        "time",
        "random",
    ):
        assert forbidden not in imported, forbidden
    text = MODELS_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "verify_trade_record(",
        "verify_liquidation_record(",
        "load_trusted_authority(",
        "parse_approval_manifest(",
        "verify_evidence_custody(",
        "assess_replay_eligibility(",
        "manifest_digest(",
        "evidence_digest(",
        "now(",
        "utcnow(",
        "sha256(",
        "open(",
    ):
        assert forbidden not in text, forbidden


def test_the_consumer_package_exposes_no_eager_imports() -> None:
    """A re-export would break A1.5 through the package ``__init__``."""
    init = CONSUMER_PACKAGE / "__init__.py"
    assert init.is_file()
    tree = ast.parse(init.read_text(encoding="utf-8"))
    assert not [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
