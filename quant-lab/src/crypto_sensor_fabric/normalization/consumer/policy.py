"""SENSOR-B5-P3 - policy-owned verification derivation (Rungs 2 and 4).

The production trust consumer.  Its whole reason to exist is one change of
shape from the conformance harness in ``tests/``:

    harness:  evaluate(candidate, rederive: Callable[[], RecordVerification])
    here:     evaluate(request: ConsumerRequest) -> ConsumerVerdict

A callback's *name* is not provenance.  The harness could not tell a lambda that
calls ``verify_trade_record`` from one that returns
``RecordVerification.model_construct(...)`` or a stale cached object, so it
compensated after the fact with ``assert_trustworthy`` and divergence checks --
detection of a value it never derived (threat A01/A02/A16).  Production has no
parameter, attribute or method argument of that shape, so the attack has no
place to arrive.

What the policy owns, in the design's normative order
(``06_ACCEPTANCE_MATRIX.md`` section 2, ``03_TRUST_BOUNDARY_SPEC.md``):

1. **The request is revalidated.**  An object with the right class is not
   evidence: ``model_construct`` skips every validator, so the request is
   round-tripped through its own schema before it is read.
2. **Replay is adjudicated** by ``assess_replay_eligibility`` over I05
   *evidence*.  A request that declares no replay evidence is not
   replay-admissible; there is no parameter for a caller-asserted evaluation.
3. **The cutoff must exist and be offset-aware.**  A missing cutoff is
   ``PIT_INADMISSIBLE``, a naive one is ``NAIVE_CUTOFF``; neither is repaired by
   assuming UTC.
4. **Claimed manifest bytes are compared, never adopted** (A04).
5. **Verification is derived**: the policy builds
   ``TrustedAuthorityContext`` over pinned bytes it holds and calls
   ``verify_trade_record`` / ``verify_liquidation_record`` itself, with its own
   custody provider and registry.  ``assert_trustworthy()`` re-runs the
   verifier's own laws over the result.
6. **Inspection**: trust scope, enumerated dimensions, evidence rebinding,
   required fields, PIT, replay, custody integrity -- in that order, so PIT and
   replay are settled **before** authority (A17).
7. **Authority is derived last**, per evaluation, from the pinned manifest
   (Rung 3).  ``AUTHORIZED`` is never read from the verification object: the
   verifier's own ``custody_source_authorized`` is a claim and is ignored
   (harness AT53).

Fail-closed, with bounded diagnostics: a typed verifier refusal becomes
``REFUSE`` with the mapped reason; an *absent integration* (no approval exists
in the manifest at all) becomes ``INTEGRATION_REQUIRED`` -- not a violation, and
not an acceptance; any other exception becomes ``REFUSE``/``VERIFIER_CRASH``
with the exception class and a truncated message.  No detail carries artifact
bytes, evidence bytes, a manifest or a digest the caller did not already supply.
``KeyboardInterrupt`` and ``SystemExit`` are never caught.

Bounded claim, stated rather than implied: this is a data boundary inside one
process.  It resists a hostile caller and hostile data.  It does not resist code
running with the application's privileges, and no in-process Python mechanism
can (threat-model X01-X03, X05).
"""

from __future__ import annotations

from datetime import datetime
from typing import NamedTuple

import crypto_sensor_fabric.normalization.authority as _authority_pkg
from pydantic import ValidationError

from ..authority import (
    SemanticAuthorityRefusal,
    evidence_digest,
    load_trusted_authority,
    manifest_digest,
    parse_approval_manifest,
)
from ..common.methodologies import NormalizationMethodologyRegistry
from ..sensors.liquidation import T1LiquidationRecord
from ..sensors.trade import T1TradeRecord
from ..sensors.verification import (
    RecordVerification,
    RecordVerificationError,
    RecordVerificationRefusal,
    TrustedAuthorityContext,
    TrustedCustodyProvider,
    verify_liquidation_record,
    verify_trade_record,
)
from ..time.replay_gate import (
    UnassessableReplayEvidence,
    assess_replay_eligibility,
)
from .custody_authority import (
    SUPPORTED_RECORD_KINDS,
    CustodyAuthorityBasis,
    CustodyAuthorityDerivation,
    CustodyAuthorityIdentity,
    CustodySourceAuthoritySource,
    ManifestCustodyAuthority,
)
from .models import (
    TRUST_SCOPE_ECONOMIC_FIELD_BINDING,
    ConsumerDecision,
    ConsumerRefusalReason,
    ConsumerRequest,
    ConsumerVerdict,
)

__all__ = ["TrustConsumerPolicy"]

_DETAIL_MAX = 400

#: Refusals that mean "there is no integration here", not "a rule was broken".
#: The reviewed manifest ships empty, so this is the *expected* production path:
#: it produces ``INTEGRATION_REQUIRED``, which is never an acceptance.  A wrong
#: digest, a revoked approval or a bad transformation is NOT in this set -- those
#: stay `REFUSE`.
_INTEGRATION_ABSENT_REFUSALS = frozenset(
    {
        RecordVerificationRefusal.NO_APPROVAL,
        RecordVerificationRefusal.ARTIFACT_NOT_APPROVED,
        RecordVerificationRefusal.APPROVAL_NOT_YET_AVAILABLE,
    }
)

#: Placeholder artifact identity for a record that names none.  The verifier
#: refuses such a record with PROVENANCE_MISSING; the token only gives the trust
#: context a well-formed id until that refusal happens.
_UNRESOLVED_ARTIFACT = "UNRESOLVED_PROVENANCE"


class _ReplayAdjudication(NamedTuple):
    status: str
    blocked: bool
    detail: str


#: An unexpected exception's message is relayed for diagnosis, and 200
#: characters is all the design allows (06_ACCEPTANCE_MATRIX.md section 3).  The
#: shorter bound is deliberate: a crash message is the one string this code did
#: not author.
_CRASH_DETAIL_MAX = 200


def _bounded(text: object, limit: int = _DETAIL_MAX) -> str:
    """One line, hard length bound.  Never a traceback."""
    flattened = " ".join(str(text).split())
    return flattened[:limit]


class TrustConsumerPolicy:
    """The production consumer.  Owns the root, replay, evidence and authority.

    Construction takes the *pinned* manifest bytes, the methodology registry and
    a custody provider -- the trusted composition (threat principal T3).  Nothing
    an untrusted actor supplies may enter here: manifest bytes that are not the
    reviewed root are refused at construction, and a custody provider that does
    not hold bytes fails the verifier's own hashing.
    """

    def __init__(
        self,
        *,
        manifest_bytes: bytes,
        methodology_registry: NormalizationMethodologyRegistry,
        custody: TrustedCustodyProvider | None = None,
        authority_source: CustodySourceAuthoritySource | None = None,
    ) -> None:
        if not isinstance(manifest_bytes, bytes):
            raise TypeError(
                "manifest_bytes must be bytes: a manifest object supplied at "
                "runtime is not a reviewed root"
            )
        digest = manifest_digest(manifest_bytes)
        pin = _authority_pkg.TRUSTED_MANIFEST_SHA256
        if digest != pin:
            raise ValueError(
                "TrustConsumerPolicy refuses manifest bytes that are not the "
                "reviewed production root; a policy built over the caller's own "
                "manifest would approve the caller (spec A / A04)"
            )
        if not isinstance(methodology_registry, NormalizationMethodologyRegistry):
            raise TypeError(
                "methodology_registry must be a NormalizationMethodologyRegistry: "
                "the policy re-derives approvals against the real registry"
            )
        if custody is not None and not isinstance(custody, TrustedCustodyProvider):
            raise TypeError(
                "custody must implement TrustedCustodyProvider, which hands over "
                "BYTES; a {reference: digest} mapping is the claim, not the custody"
            )
        source: CustodySourceAuthoritySource = (
            authority_source
            if authority_source is not None
            else ManifestCustodyAuthority(manifest_bytes=manifest_bytes)
        )
        if not isinstance(source, CustodySourceAuthoritySource):
            raise TypeError(
                "authority_source must expose authorize(identity); the policy calls "
                "it per evaluation and never stores a granted basis"
            )
        self._manifest_bytes = manifest_bytes
        self._manifest_sha256 = digest
        self._registry = methodology_registry
        self._custody = custody
        self._authority_source = source

    # -- public entry point ---------------------------------------------------

    def evaluate(self, request: ConsumerRequest) -> ConsumerVerdict:
        """Evaluate one request.  Never raises for data; never returns acceptance
        without every one of the four claims holding."""
        if not isinstance(request, ConsumerRequest):
            raise TypeError(
                "evaluate takes a ConsumerRequest; a verdict, a record or a "
                "callback is not a request"
            )

        # 1. Revalidate at the consumption boundary.  ``model_construct`` and
        #    ``model_copy(update=...)`` skip validators, so the class of an
        #    object proves nothing about its contents.
        try:
            request = ConsumerRequest.model_validate(request.model_dump())
        except ValidationError as exc:
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"the request does not satisfy its own schema ({exc.error_count()} "
                "violation(s)); a validator bypass is not a request",
                replay_status="NOT_RESOLVED",
            )

        record = request.record

        # 2. Replay, from evidence, by the policy.
        replay = self._adjudicate_replay(request.replay_evidence)
        if replay.blocked:
            return self._refuse(
                ConsumerRefusalReason.REPLAY_BLOCKED,
                replay.detail,
                replay_status=replay.status,
            )

        # 3. The cutoff must exist and be offset-aware.
        cutoff = request.knowledge_cutoff
        if cutoff is None:
            return self._refuse(
                ConsumerRefusalReason.PIT_INADMISSIBLE,
                "the request declares no knowledge cutoff; a consumption that "
                "cannot name its PIT instant cannot be admitted",
                replay_status=replay.status,
            )
        if cutoff.tzinfo is None or cutoff.utcoffset() is None:
            return self._refuse(
                ConsumerRefusalReason.NAIVE_CUTOFF,
                "the knowledge cutoff is naive; assuming UTC would fabricate a PIT "
                "answer (a validator bypass is the only way to reach this)",
                replay_status=replay.status,
            )

        # 4. Claimed manifest bytes are compared against the pinned root, never
        #    adopted (A04).
        claimed = request.claimed_manifest_bytes
        if claimed is not None and claimed != self._manifest_bytes:
            return self._refuse(
                ConsumerRefusalReason.TRUSTED_CONTEXT_MISMATCH,
                "the claimed manifest bytes are not the reviewed root; a manifest "
                "supplied beside the record is compared, never adopted",
                replay_status=replay.status,
            )

        # 5. Derive the verification.  The policy owns the context, the registry
        #    and the custody provider; the caller supplied none of them.
        try:
            derived = self._derive(record, request.artifact_bytes, cutoff)
            if not isinstance(derived, RecordVerification):
                raise TypeError(
                    f"the verifier returned {type(derived).__name__}, not a "
                    "RecordVerification"
                )
            derived.assert_trustworthy()
        except RecordVerificationError as exc:
            if exc.refusal in _INTEGRATION_ABSENT_REFUSALS:
                return self._integration_required(
                    f"no integration to evaluate: {exc.refusal.value}",
                    replay_status=replay.status,
                    pit_status="INADMISSIBLE",
                    custody_status="NOT_PROVIDED",
                )
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"{exc.refusal.value}: {exc.detail}",
                replay_status=replay.status,
            )
        except SemanticAuthorityRefusal as exc:
            refusal = str(getattr(exc, "refusal", exc))
            if refusal in {item.value for item in _INTEGRATION_ABSENT_REFUSALS}:
                return self._integration_required(
                    f"no integration to evaluate: {refusal}",
                    replay_status=replay.status,
                    pit_status="INADMISSIBLE",
                    custody_status="NOT_PROVIDED",
                )
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"{refusal}: {getattr(exc, 'detail', '')}",
                replay_status=replay.status,
            )
        except Exception as exc:  # noqa: BLE001 - fail closed, bounded detail
            # KeyboardInterrupt/SystemExit are BaseException and propagate above.
            return self._refuse(
                ConsumerRefusalReason.VERIFIER_CRASH,
                _bounded(f"{type(exc).__name__}: {exc}", _CRASH_DETAIL_MAX),
                replay_status=replay.status,
            )

        return self._inspect(
            request=request,
            derived=derived,
            cutoff=cutoff,
            replay=replay,
        )

    # -- replay ---------------------------------------------------------------

    def _adjudicate_replay(self, evidence: object) -> _ReplayAdjudication:
        """Apply the I05 gate to the request's own evidence.

        No replay evidence is *not* replay admissibility: Rung 4 requires PIT and
        replay to be resolved before any authoritative acceptance, so an
        unadjudicated request is blocked rather than waved through.
        """
        if evidence is None:
            return _ReplayAdjudication(
                status="NOT_POLICY_DERIVED",
                blocked=True,
                detail=(
                    "the request declares no replay evidence, so no replay gate was "
                    "applied; acceptance requires a policy-derived evaluation"
                ),
            )
        try:
            evaluation = assess_replay_eligibility(evidence)  # type: ignore[arg-type]
        except UnassessableReplayEvidence as exc:
            return _ReplayAdjudication(
                status="UNASSESSABLE", blocked=True, detail=_bounded(exc)
            )
        except Exception as exc:  # noqa: BLE001 - a broken gate blocks, never opens
            return _ReplayAdjudication(
                status="UNASSESSABLE",
                blocked=True,
                detail=f"{type(exc).__name__}: {_bounded(exc)}",
            )
        blocked = evaluation.eligibility.value != "ELIGIBLE"
        return _ReplayAdjudication(
            status=evaluation.eligibility.value,
            blocked=blocked,
            detail="; ".join(evaluation.reasons) if blocked else "",
        )

    # -- derivation -----------------------------------------------------------

    def _derive(
        self, record: object, artifact_bytes: bytes, cutoff: datetime
    ) -> RecordVerification:
        """Call the real verifier with policy-owned context, registry and custody."""
        if isinstance(record, T1TradeRecord):
            provenance = record.authority_provenance
            artifact_id = (
                provenance.artifact_id if provenance is not None else _UNRESOLVED_ARTIFACT
            )
            context = TrustedAuthorityContext.from_reviewed_root(
                manifest_bytes=self._manifest_bytes, artifact_id=artifact_id
            )
            return verify_trade_record(
                record,
                trusted_context=context,
                artifact_bytes=artifact_bytes,
                methodology_registry=self._registry,
                knowledge_cutoff=cutoff,
                custody=self._custody,
            )
        if isinstance(record, T1LiquidationRecord):
            # A liquidation record carries no record-level provenance; its
            # approvals live on the per-field admissions, so the artifact id is
            # resolved from the pinned manifest by exact (approval, digest).
            context = TrustedAuthorityContext.from_reviewed_root(
                manifest_bytes=self._manifest_bytes,
                artifact_id=self._liquidation_artifact_id(record),
            )
            return verify_liquidation_record(
                record,
                trusted_context=context,
                artifact_bytes=artifact_bytes,
                methodology_registry=self._registry,
                knowledge_cutoff=cutoff,
                custody=self._custody,
            )
        raise RecordVerificationError(
            RecordVerificationRefusal.RECORD_KIND_MISMATCH,
            f"a consumer request may carry a T1 trade or liquidation record, not "
            f"{type(record).__name__}",
        )

    def _liquidation_artifact_id(self, record: T1LiquidationRecord) -> str:
        """Resolve the artifact id from the admissions, or say it is unresolved.

        Never guesses: zero matches and several matches both leave the id
        unresolved, and the loader then refuses the approval.
        """
        admitted = [
            admission for admission in record.side_admissions if admission.admitted
        ]
        if not admitted:
            return _UNRESOLVED_ARTIFACT
        try:
            manifest = parse_approval_manifest(self._manifest_bytes)
        except SemanticAuthorityRefusal:
            return _UNRESOLVED_ARTIFACT
        matches = [
            artifact_id
            for artifact_id, entry in manifest.artifacts.items()
            if all(
                admission.admission_approval_id == entry.approval_id
                and admission.admission_registry_digest == entry.sha256
                for admission in admitted
            )
        ]
        return matches[0] if len(matches) == 1 else _UNRESOLVED_ARTIFACT

    # -- inspection -----------------------------------------------------------

    def _inspect(
        self,
        *,
        request: ConsumerRequest,
        derived: RecordVerification,
        cutoff: datetime,
        replay: _ReplayAdjudication,
    ) -> ConsumerVerdict:
        pit_status = "ADMISSIBLE" if derived.pit_admissible else "INADMISSIBLE"
        custody_status = "VERIFIED" if derived.custody_verified else "UNVERIFIED"

        # Inspection 1 -- scope laundering (A10).
        if derived.trust_scope != TRUST_SCOPE_ECONOMIC_FIELD_BINDING:
            return self._refuse(
                ConsumerRefusalReason.FORGED_TRUST_SCOPE,
                f"trust_scope is {derived.trust_scope!r}; only "
                f"{TRUST_SCOPE_ECONOMIC_FIELD_BINDING!r} may be consumed",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        # Inspection 2 -- an empty dimension list reads as whole-record
        # authentication (A11).  The verifier already refuses to set
        # downstream_trusted with an empty list; this is the consumer's own law.
        if not derived.unverified_dimensions:
            return self._refuse(
                ConsumerRefusalReason.EMPTY_UNVERIFIED_DIMENSIONS,
                "the verification enumerates none of the dimensions it does not "
                "cover; an empty list claims whole-record authentication",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        # Inspection 3 -- the record kind the verifier reported must be the kind
        # of record that was actually supplied.
        expected_kind = (
            "TRADE" if isinstance(request.record, T1TradeRecord) else "LIQUIDATION"
        )
        if derived.record_kind not in SUPPORTED_RECORD_KINDS or (
            derived.record_kind != expected_kind
        ):
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"the verification reports record_kind {derived.record_kind!r} for a "
                f"{expected_kind} record; a verification of something else is not "
                "evidence about this record",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        # Inspection 4 -- evidence rebinding (A13/A14) and cross-record binding
        # (A07).  Bytes are re-read and re-hashed once per reference.
        rebind = self._rebind(request, derived, cutoff)
        if rebind is not None:
            reason, detail = rebind
            return self._refuse(
                reason,
                detail,
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        # Inspection 5 -- the field allowlist is the only grant (A12).
        if not derived.fields_verified:
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                "the verification establishes no canonical field, so there is "
                "nothing to bind",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )
        verified = set(derived.fields_verified)
        for name in request.required_fields:
            if name not in verified:
                return self._refuse(
                    ConsumerRefusalReason.FIELD_NOT_IN_ALLOWLIST,
                    f"required field {name!r} is not in the verified field allowlist",
                    derived=derived,
                    replay_status=replay.status,
                    pit_status=pit_status,
                    custody_status=custody_status,
                )

        # Inspection 6 -- PIT and replay, settled before any authority question.
        if not derived.pit_admissible:
            return self._refuse(
                ConsumerRefusalReason.PIT_INADMISSIBLE,
                "the verification is PIT-inadmissible at this cutoff",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )
        if replay.blocked:  # pragma: no cover - adjudicated before verification
            return self._refuse(
                ConsumerRefusalReason.REPLAY_BLOCKED,
                replay.detail,
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        # Custody integrity is a prerequisite of acceptance, and it is separate
        # from source authorization.  The verifier's own
        # ``custody_source_authorized`` flag is deliberately never consulted.
        if not derived.custody_verified:
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                "custody of the approved evidence bytes was not established; "
                "field binding cannot substitute for it",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        return self._conclude(
            request=request,
            derived=derived,
            cutoff=cutoff,
            replay=replay,
            pit_status=pit_status,
            custody_status=custody_status,
        )

    # -- evidence rebinding ---------------------------------------------------

    def _rebind(
        self, request: ConsumerRequest, derived: RecordVerification, cutoff: datetime
    ) -> tuple[ConsumerRefusalReason, str] | None:
        """Re-read required evidence at the consumption boundary.

        Two independent comparisons, because they answer different questions:
        the bytes must match what the *caller* claimed (their claim is checked,
        not trusted) and what the *approval* names (the artifact they belong to).
        A reference that is intact but approved for another artifact is
        cross-record reuse (A07), not a digest mismatch.
        """
        if not request.evidence_references:
            return None
        try:
            authority = load_trusted_authority(
                manifest_bytes=self._manifest_bytes,
                artifact_id=derived.artifact_id,
                artifact_bytes=request.artifact_bytes,
                methodology_registry=self._registry,
                evaluation_at=cutoff,
            )
        except (RecordVerificationError, SemanticAuthorityRefusal) as exc:
            refusal = getattr(exc, "refusal", None)
            return (
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"the approved evidence set could not be re-derived: "
                f"{getattr(refusal, 'value', refusal) or type(exc).__name__}",
            )

        approved = dict(authority.evidence_blobs)
        for item in request.evidence_references:
            expected = approved.get(item.reference)
            if expected is None:
                return (
                    ConsumerRefusalReason.EVIDENCE_NOT_BOUND_TO_ARTIFACT,
                    f"evidence reference {item.reference!r} is not bound to this "
                    "artifact by the approval; another record's evidence certifies "
                    "nothing here",
                )
            if self._custody is None:
                return (
                    ConsumerRefusalReason.EVIDENCE_BYTES_MISSING,
                    f"evidence reference {item.reference!r} was requested but the "
                    "policy holds no custody provider",
                )
            try:
                blob = self._custody.read_evidence(item.reference)
            except Exception:  # noqa: BLE001 - an unreadable store is not custody
                return (
                    ConsumerRefusalReason.EVIDENCE_BYTES_MISSING,
                    f"evidence reference {item.reference!r} could not be read from "
                    "the custody provider",
                )
            if blob is None:
                return (
                    ConsumerRefusalReason.EVIDENCE_BYTES_MISSING,
                    f"evidence reference {item.reference!r} holds no bytes at "
                    "consumption; a digest alone is not custody",
                )
            observed = evidence_digest(blob)
            if observed != item.approved_digest:
                return (
                    ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH,
                    f"evidence reference {item.reference!r} hashes to a different "
                    "value than the request claimed; the bytes changed after "
                    "verification",
                )
            if observed != expected:
                return (
                    ConsumerRefusalReason.EVIDENCE_BYTES_MISMATCH,
                    f"evidence reference {item.reference!r} does not hash to the "
                    "blob the approval names",
                )
        return None

    # -- authority ------------------------------------------------------------

    def _conclude(
        self,
        *,
        request: ConsumerRequest,
        derived: RecordVerification,
        cutoff: datetime,
        replay: _ReplayAdjudication,
        pit_status: str,
        custody_status: str,
    ) -> ConsumerVerdict:
        """Derive the basis for this exact identity, per evaluation."""
        identity = CustodyAuthorityIdentity(
            manifest_sha256=self._manifest_sha256,
            artifact_id=derived.artifact_id,
            approval_id=derived.approval_id,
            registry_digest=derived.registry_digest,
            record_kind=derived.record_kind,
            provider=derived.provider,
            knowledge_cutoff=cutoff,
        )
        try:
            derivation: CustodyAuthorityDerivation = self._authority_source.authorize(
                identity
            )
        except Exception as exc:  # noqa: BLE001 - an authority failure never grants
            return self._refuse(
                ConsumerRefusalReason.VERIFIER_CRASH,
                f"the custody-authority derivation raised {type(exc).__name__}",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )
        if not isinstance(derivation, CustodyAuthorityDerivation):
            return self._refuse(
                ConsumerRefusalReason.VERIFIER_CRASH,
                "the authority source did not return a CustodyAuthorityDerivation",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )
        if (
            derivation.basis is CustodyAuthorityBasis.AUTHORIZED
            and identity.manifest_sha256 != self._manifest_sha256
        ):  # pragma: no cover - the identity is built from that digest
            return self._refuse(
                ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE,
                "an authorized basis was returned for an identity derived under "
                "another root",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        if derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED:
            return self._refuse(
                ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE,
                derivation.detail,
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
                custody_detail=derivation.detail,
            )
        if derivation.basis is CustodyAuthorityBasis.INTEGRATION_REQUIRED:
            # Name the unmet requirement in the verdict: an operator reading an
            # INTEGRATION_REQUIRED has to know which contract to supply, and no
            # refusal_reason exists for "nothing was violated but nothing is
            # authorized either".
            detail = derivation.detail
            if derivation.unresolved_contract:
                token = derivation.unresolved_contract.split(" ", 1)[0].rstrip(":")
                detail = f"{detail} (unmet: {token})"
            return self._integration_required(
                detail,
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )
        return ConsumerVerdict(
            decision=ConsumerDecision.ACCEPT_FIELD_BINDING,
            verified_field_allowlist=derived.fields_verified,
            unverified_dimensions=derived.unverified_dimensions,
            pit_status=pit_status,
            replay_status=replay.status,
            custody_status=custody_status,
            custody_source_authorization_status=CustodyAuthorityBasis.AUTHORIZED,
            custody_source_authorized=True,
            custody_authorization_detail=_bounded(derivation.detail),
        )

    # -- verdict builders -----------------------------------------------------

    def _refuse(
        self,
        reason: ConsumerRefusalReason,
        detail: str,
        *,
        derived: RecordVerification | None = None,
        replay_status: str = "NOT_RESOLVED",
        pit_status: str | None = None,
        custody_status: str | None = None,
        custody_detail: str | None = None,
    ) -> ConsumerVerdict:
        return ConsumerVerdict(
            decision=ConsumerDecision.REFUSE,
            verified_field_allowlist=derived.fields_verified if derived else (),
            unverified_dimensions=derived.unverified_dimensions if derived else (),
            pit_status=pit_status
            or ("ADMISSIBLE" if derived and derived.pit_admissible else "INADMISSIBLE"),
            replay_status=replay_status,
            custody_status=custody_status
            or ("VERIFIED" if derived and derived.custody_verified else "UNVERIFIED"),
            custody_source_authorization_status=CustodyAuthorityBasis.UNAUTHORIZED,
            custody_source_authorized=False,
            refusal_reason=reason,
            refusal_detail=_bounded(detail),
            custody_authorization_detail=(
                _bounded(custody_detail) if custody_detail else None
            ),
        )

    def _integration_required(
        self,
        detail: str,
        *,
        derived: RecordVerification | None = None,
        replay_status: str = "NOT_RESOLVED",
        pit_status: str = "INADMISSIBLE",
        custody_status: str = "NOT_PROVIDED",
    ) -> ConsumerVerdict:
        return ConsumerVerdict(
            decision=ConsumerDecision.INTEGRATION_REQUIRED,
            verified_field_allowlist=derived.fields_verified if derived else (),
            unverified_dimensions=derived.unverified_dimensions if derived else (),
            pit_status=pit_status,
            replay_status=replay_status,
            custody_status=custody_status,
            custody_source_authorization_status=CustodyAuthorityBasis.INTEGRATION_REQUIRED,
            custody_source_authorized=False,
            custody_authorization_detail=_bounded(detail),
        )
