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

Fail-closed, with bounded diagnostics that never RELAY foreign text: a typed
verifier refusal becomes ``REFUSE`` with the mapped reason; an *absent
integration* (no approval exists in the manifest at all) becomes
``INTEGRATION_REQUIRED`` -- not a violation, and not an acceptance; an
unexpected exception becomes ``REFUSE``/``VERIFIER_CRASH`` naming only its
CLASS.

H01 (final hardening).  A length bound limits how much of a foreign message
leaks, not whether any does: an ``OSError``, a ``RuntimeError`` from a custody
adapter or a serializer error can carry a credential, a local path, artifact
bytes or an evidence digest, and a verdict travels to whoever consumes the
record.  So an unexpected exception contributes its class and nothing else.
F5 (final hardening): a TYPED refusal contributes its refusal TOKEN from the
approved vocabulary and a fixed diagnostic, and never its authored ``detail``.
An authored sentence is still free text assembled at the failing layer, and one
path -- ``str(exc)`` of a typed refusal, whose message is
``"<CODE>: <detail>"`` -- would have relayed the payload even where the detail
was never formatted here.  ``KeyboardInterrupt`` and ``SystemExit`` propagate,
and no exception text is written to a log as a substitute.

H02 (final hardening).  Running the I05 gate over structurally valid evidence
does not establish that the evidence describes THIS record.  ``ReplayEvidence``
carries no record id, provider, record kind or artifact identity, so the policy
binds every axis the frozen schema does carry -- the record's own
``source_revision_id`` against the selection, the selection against this
request's cutoff, and the evidence's market-availability instant against the
record's declared one -- and refuses when they disagree.  The axes the schema
cannot express are named in :data:`UNRESOLVED_REPLAY_BINDING` rather than
invented, on the same precedent as
``OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1``.

F4 (final hardening).  The cutoff law orders EVERY selected revision, not only
the record's own.  A selection assembled at a later replay can agree with this
record's revision and still contain another revision that did not exist at this
cutoff: agreement about ``WHICH`` revisions was never an answer about ``WHEN``.
The sweep runs over the ORIGINAL selected sequence, before any id-keyed mapping,
so a duplicate identity cannot hide a late entry behind an early one; the
excluded half is deliberately NOT ordered against the cutoff, because an
excluded revision is retained precisely as evidence that it was not known here.

F1 residual (unresolved record binding).  Temporal eligibility, revision
identity compatibility, complete record/provider/artifact evidence binding and
authority to consume are FOUR claims, and the frozen I05 ``ReplayEvidence``
schema can carry only the first two plus the record's own revision identity.  So
complete binding is not establishable here at all, and it is executable rather
than documentary: :data:`REPLAY_RECORD_BINDING_ESTABLISHED` is ``False``, and a
evaluation that satisfies every other claim terminates in
``INTEGRATION_REQUIRED`` naming ``REPLAY_EVIDENCE_RECORD_BINDING_V1`` instead of
an acceptance that would imply a binding the schema cannot support.  Minting the
contract is an operator decision; flipping this guard without implementing it
is a mutation the suite detects.

H04 (final hardening).  The boundary is TOTAL.  ``evaluate`` is a thin guard
around ``_evaluate``; anything data-shaped that escapes the named handling --
serialization of a ``model_construct`` request, an inspection over a verification
whose fields are not the declared types, an identity that fails its own laws, a
verdict that fails its own laws -- answers ``REFUSE``.  Only the two programmer-
error boundaries raise: a non-``ConsumerRequest`` argument and construction-time
type checks.

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
    AuthorityRefusal,
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
    custody_authority_identity_digest,
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
    }
)

#: Every refusal code this repository owns.  F5: a verdict may carry a member of
#: this vocabulary, and nothing else that looks like a code.
_APPROVED_REFUSAL_TOKENS = frozenset(
    [item.value for item in RecordVerificationRefusal]
    + [item.value for item in AuthorityRefusal]
)

#: What a verdict says when the failing layer named no approved code at all.
#: Fixed text: a fallback that echoed the payload would be the leak itself.
_UNSPECIFIED_REFUSAL = "UNSPECIFIED_REFUSAL"

#: Refusals that mean "this record cannot be placed in time at this cutoff".
#: They are violations of an approval that *exists*, so they are PIT
#: inadmissibility, never "integration absent": an approval that was not yet
#: operative at the cutoff is a time violation, not a missing integration.
_PIT_REFUSALS = frozenset(
    {
        RecordVerificationRefusal.APPROVAL_NOT_YET_AVAILABLE,
        RecordVerificationRefusal.INTRADAY_PIT_AMBIGUOUS,
        RecordVerificationRefusal.PIT_CUTOFF_REQUIRED,
        RecordVerificationRefusal.PIT_AVAILABILITY_MISSING,
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


#: H02: the binding axes the frozen I05 replay schema cannot express.  Named,
#: not invented -- minting a record type or a field to carry them is an operator
#: decision, exactly like ``OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1``.
UNRESOLVED_REPLAY_BINDING = (
    "REPLAY_EVIDENCE_RECORD_BINDING_V1 is unresolved: the frozen I05 "
    "ReplayEvidence schema carries no record id, provider, record kind or "
    "artifact identity, so replay evidence cannot be proven to belong to this "
    "record on those axes. Revision identity, cutoff and declared availability "
    "are bound here; the remaining axes are not invented."
)

#: The contract that would carry the missing axes.  Named, never minted here.
REPLAY_EVIDENCE_RECORD_BINDING_CONTRACT = "REPLAY_EVIDENCE_RECORD_BINDING_V1"

#: F1 residual: is complete record-level replay binding established?
#:
#: ``False`` is the measured state: the frozen I05 schema carries no record id,
#: provider, record kind or artifact identity, so the policy can establish
#: temporal eligibility and revision identity compatibility and nothing more.
#: This is an executable guard rather than a docstring -- while it is ``False``
#: no evaluation reaches :attr:`ConsumerDecision.ACCEPT_FIELD_BINDING`, however
#: well every other claim holds.  An operator mission that mints
#: :data:`REPLAY_EVIDENCE_RECORD_BINDING_CONTRACT` flips it by implementing the
#: binding; flipping it alone is a mutation the security suite detects.
REPLAY_RECORD_BINDING_ESTABLISHED: bool = False

#: The four independent claims an authoritative consumption needs.  Kept as a
#: tuple so a test can assert the guard names each one and refuses to collapse
#: them into one badge.
REPLAY_BINDING_CLAIMS = (
    "TEMPORAL_ELIGIBILITY",
    "REVISION_IDENTITY_COMPATIBILITY",
    "RECORD_PROVIDER_ARTIFACT_BINDING",
    "AUTHORITY_TO_CONSUME",
)


def _bounded(text: object, limit: int = _DETAIL_MAX) -> str:
    """One line, hard length bound.  Never a traceback, and never a raise."""
    try:
        flattened = " ".join(str(text).split())
    except Exception:  # noqa: BLE001 - a diagnostic that cannot render is data
        return "<unrenderable diagnostic>"
    return flattened[:limit]


def _withheld(exc: BaseException) -> str:
    """Name the exception CLASS and refuse to relay its message (H01).

    The class is supplied by the runtime and carries no payload.  The message is
    whatever the failing layer happened to format, which in production can be a
    credential in a connection string, a local path, an artifact blob or an
    evidence digest -- and a verdict is read by whoever consumes the record, so
    relaying it would turn the consumer into an error-message exfiltration
    channel.  Diagnosis keeps the class; payload stays where it was raised.
    """
    return _bounded(
        f"an unexpected {type(exc).__name__} was raised; the message is withheld "
        "because it is untrusted text that may carry credentials, artifacts or "
        "evidence"
    )


def _approved_refusal(value: object) -> str | None:
    """Reduce a refusal to an APPROVED token, or ``None`` (F5).

    A typed refusal's ``detail`` is authored free text assembled at the failing
    layer, so it may not travel into a verdict; the CODE may, because the code
    is the closed vocabulary this repository defines.  An object that claims to
    be a refusal without naming a member of that vocabulary gets ``None`` -- the
    caller then reports :data:`_UNSPECIFIED_REFUSAL`, never the claimed text.
    """
    if isinstance(value, (RecordVerificationRefusal, AuthorityRefusal)):
        return value.value
    if isinstance(value, str) and value in _APPROVED_REFUSAL_TOKENS:
        return value
    return None


def _refusal_token(value: object) -> str:
    """``_approved_refusal`` or the fixed fallback; never interpolated text."""
    return _approved_refusal(value) or _UNSPECIFIED_REFUSAL


def _identifiers(derived: object, name: str) -> tuple[str, ...]:
    """Read an identifier tuple defensively (H04).

    ``_refuse`` runs on the way out of a failure, so it must not be the thing
    that fails: a verification produced by ``model_construct`` can hold anything
    at all under an attribute the inspector still wants to report.
    """
    value = getattr(derived, name, ())
    try:
        return tuple(
            item for item in value if isinstance(item, str) and item.strip()
        )
    except TypeError:
        return ()


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
        # H03: the pinned root's approved artifact ids, read once from bytes the
        # constructor already proved are the reviewed root.  They are the only
        # set an ``AUTHORIZED`` basis may name: a source cannot authorize an
        # artifact the reviewed manifest does not approve, and an empty manifest
        # approves no artifact, so no empty-manifest request can become
        # authorized by any source.
        try:
            pinned = parse_approval_manifest(manifest_bytes)
        except SemanticAuthorityRefusal as exc:
            raise ValueError(
                "the pinned root does not parse as an approval manifest, so no "
                "artifact is approved under it"
            ) from exc
        self._manifest_bytes = manifest_bytes
        self._manifest_sha256 = digest
        self._approved_artifact_ids = frozenset(pinned.artifacts)
        self._registry = methodology_registry
        self._custody = custody
        self._authority_source = source

    # -- public entry point ---------------------------------------------------

    def evaluate(self, request: ConsumerRequest) -> ConsumerVerdict:
        """Evaluate one request.  Never raises for data; never accepts without
        every one of the four claims holding.

        H04: the boundary is total.  ``_evaluate`` names every failure this code
        expects; this wrapper exists for the ones it does not -- a
        ``model_construct`` request whose serialization raises, an inspection
        over a verification whose fields are not the declared types, an identity
        that fails its own laws, a verdict that fails its own laws.  Every one of
        those is data-shaped, so every one answers ``REFUSE`` instead of
        escaping to the caller as a stack trace.

        The two boundaries that still raise are deliberate programmer errors: a
        non-``ConsumerRequest`` argument here, and the construction-time type
        checks.  ``KeyboardInterrupt`` and ``SystemExit`` are ``BaseException``
        and are never caught.
        """
        if not isinstance(request, ConsumerRequest):
            raise TypeError(
                "evaluate takes a ConsumerRequest; a verdict, a record or a "
                "callback is not a request"
            )
        try:
            return self._evaluate(request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:  # noqa: BLE001 - fail closed on everything else
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"{_withheld(exc)}; the evaluation did not complete, so no field "
                "binding was established",
                replay_status="NOT_RESOLVED",
            )

    def _evaluate(self, request: ConsumerRequest) -> ConsumerVerdict:
        # 1. Revalidate at the consumption boundary.  ``model_construct`` and
        #    ``model_copy(update=...)`` skip validators, so the class of an
        #    object proves nothing about its contents -- and the round trip is
        #    itself an operation over untrusted input, so its failure is a
        #    refusal, not a traceback.
        try:
            request = ConsumerRequest.model_validate(request.model_dump())
        except ValidationError as exc:
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"the request does not satisfy its own schema ({exc.error_count()} "
                "violation(s)); a validator bypass is not a request",
                replay_status="NOT_RESOLVED",
            )
        except Exception as exc:  # noqa: BLE001 - serialization is untrusted too
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"{_withheld(exc)}; the request could not be serialized for "
                "revalidation, so it cannot be admitted",
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
        if not isinstance(cutoff, datetime):
            return self._refuse(
                ConsumerRefusalReason.PIT_INADMISSIBLE,
                "the request's knowledge cutoff is not a datetime at all; a "
                "consumption that cannot name its PIT instant cannot be admitted",
                replay_status=replay.status,
            )
        if cutoff.tzinfo is None or cutoff.utcoffset() is None:
            return self._refuse(
                ConsumerRefusalReason.NAIVE_CUTOFF,
                "the knowledge cutoff is naive; assuming UTC would fabricate a PIT "
                "answer (a validator bypass is the only way to reach this)",
                replay_status=replay.status,
            )

        # 3b. H02: the replay evidence must belong to THIS consumption.  The I05
        #     gate answers "is this evidence eligible"; it cannot answer "is it
        #     this record's evidence", so the policy binds what the frozen schema
        #     carries before any acceptance can rest on it.
        unbound = self._bind_replay(request.replay_evidence, record, cutoff)
        if unbound is not None:
            reason, detail = unbound
            return self._refuse(reason, detail, replay_status="NOT_BOUND")

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
            # F5: the CODE travels, the authored ``detail`` does not.  The
            # classification still reads the mutable refusal SETS, so the
            # reporting mutations that empty them keep their meaning.
            code = getattr(exc, "refusal", None)
            try:
                pit = code in _PIT_REFUSALS
                absent = code in _INTEGRATION_ABSENT_REFUSALS
            except TypeError:  # an unhashable claimed code is not a code
                pit = absent = False
            token = _refusal_token(code)
            if pit:
                return self._refuse(
                    ConsumerRefusalReason.PIT_INADMISSIBLE,
                    f"{token}: the approval or its evidence was not admissible at "
                    "this request's knowledge cutoff",
                    replay_status=replay.status,
                )
            if absent:
                return self._integration_required(
                    f"no integration to evaluate: {token}",
                    replay_status=replay.status,
                    pit_status="INADMISSIBLE",
                    custody_status="NOT_PROVIDED",
                )
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"{token}: record verification did not establish economic field "
                "binding for this record",
                replay_status=replay.status,
            )
        except SemanticAuthorityRefusal as exc:
            # F5: ``str(exc)`` is "<CODE>: <detail>", so it is never used here.
            token = _refusal_token(getattr(exc, "refusal", None))
            if token in {item.value for item in _INTEGRATION_ABSENT_REFUSALS}:
                return self._integration_required(
                    f"no integration to evaluate: {token}",
                    replay_status=replay.status,
                    pit_status="INADMISSIBLE",
                    custody_status="NOT_PROVIDED",
                )
            return self._refuse(
                ConsumerRefusalReason.VERIFICATION_FAILED,
                f"{token}: the semantic authority did not establish an approval "
                "for this record; its authored detail is not relayed",
                replay_status=replay.status,
            )
        except Exception as exc:  # noqa: BLE001 - fail closed, class only
            # KeyboardInterrupt/SystemExit are BaseException and propagate above.
            return self._refuse(
                ConsumerRefusalReason.VERIFIER_CRASH,
                _withheld(exc),
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
        except UnassessableReplayEvidence:
            # F5: the gate's message is assembled from evidence values, so it is
            # exception text like any other and does not become verdict text.
            return _ReplayAdjudication(
                status="UNASSESSABLE",
                blocked=True,
                detail=(
                    "the replay gate could not express this evidence in its frozen "
                    "eligibility vocabulary; its message is withheld because it is "
                    "assembled from the evidence it read"
                ),
            )
        except Exception as exc:  # noqa: BLE001 - a broken gate blocks, never opens
            return _ReplayAdjudication(
                status="UNASSESSABLE",
                blocked=True,
                detail=f"the replay gate failed closed: {_withheld(exc)}",
            )
        blocked = evaluation.eligibility.value != "ELIGIBLE"
        return _ReplayAdjudication(
            status=evaluation.eligibility.value,
            blocked=blocked,
            detail="; ".join(evaluation.reasons) if blocked else "",
        )

    # -- replay binding (H02) -------------------------------------------------

    def _bind_replay(
        self, evidence: object, record: object, cutoff: datetime
    ) -> tuple[ConsumerRefusalReason, str] | None:
        """Bind the replay evidence to this record and this cutoff.

        The I05 gate is a law about *evidence*, not about *whose* evidence: the
        same eligible row passes whether it was derived from this record or from
        an unrelated one, and whether it was selected at this cutoff or a later
        one.  What the frozen schema does carry is bound here, in the order the
        design settles PIT questions:

        1. the record's own ``source_revision_id`` must appear in the selection;
           a selection that EXCLUDES it is a row that was not known at the
           cutoff, and a selection that does not mention it at all describes a
           different observation;
        2. EVERY selected revision must have become known by the cutoff -- not
           only the record's own.  A selection assembled at a later replay can
           agree with this record's revision and still contain another revision
           that did not exist here, so the cutoff law is ordered over the whole
           selected sequence (F4);
        3. the evidence's market-availability instant may not be after the
           cutoff, and must agree with the record's own declared one when the
           record declares it (an availability instant that contradicts the
           record is another row's instant).

        Returns a refusal reason and detail, or ``None`` when every available axis
        binds.  A binding failure about ``WHEN`` is reported as
        ``PIT_INADMISSIBLE`` (a time violation) and a binding failure about
        ``WHICH`` as ``REPLAY_BLOCKED`` (evidence that is not this row's evidence);
        collapsing the two would make a wrong-row attack read as a clock problem.
        The axes this schema cannot express are named in
        :data:`UNRESOLVED_REPLAY_BINDING` and are not fabricated here.
        """
        revision = getattr(evidence, "revision", None)
        if revision is None or isinstance(revision, bool):
            # The gate already blocks an absent selection (BLOCKED_REVISION);
            # this is the belt-and-braces path for a malformed one.
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                "the replay evidence declares no revision selection, so nothing "
                "ties it to this record; cutoff compatibility is unproven",
            )
        try:
            selected_items = tuple(revision.selected)
            excluded_items = tuple(revision.excluded)
        except Exception:  # noqa: BLE001 - a malformed selection is not evidence
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                "the replay evidence carries a revision selection that cannot be "
                "read; malformed evidence certifies nothing",
            )

        # F4: the ORIGINAL selected sequence is validated before any id-keyed
        # mapping.  A dict built from the entries keeps the LAST one for an id,
        # so an early admissible entry could stand in front of a late entry for
        # the same revision and the late entry would never be read.
        selected_ids: list[str] = []
        selected_instants: list[object] = []
        for item in selected_items:
            identity = getattr(item, "source_revision_id", None)
            if not isinstance(identity, str) or not identity.strip():
                return (
                    ConsumerRefusalReason.REPLAY_BLOCKED,
                    "a selected revision declares no source revision identity; a "
                    "selection whose entries cannot be named certifies nothing",
                )
            selected_ids.append(identity)
            selected_instants.append(getattr(item, "known_from", None))
        excluded_ids: list[str] = []
        for item in excluded_items:
            identity = getattr(item, "source_revision_id", None)
            if not isinstance(identity, str) or not identity.strip():
                return (
                    ConsumerRefusalReason.REPLAY_BLOCKED,
                    "an excluded revision declares no source revision identity; a "
                    "selection whose entries cannot be named certifies nothing",
                )
            excluded_ids.append(identity)

        repeated = sorted(
            {identity for identity in selected_ids if selected_ids.count(identity) > 1}
        )
        if repeated:
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                f"the replay selection names revision(s) {repeated} more than "
                "once; two entries for one revision are a contradiction, and a "
                "contradictory selection certifies nothing",
            )
        both = sorted(set(selected_ids) & set(excluded_ids))
        if both:
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                f"revision(s) {both} are BOTH selected and excluded; a selection "
                "that contradicts itself cannot manufacture admissibility",
            )

        selected = frozenset(selected_ids)
        excluded = frozenset(excluded_ids)

        record_revision = getattr(record, "source_revision_id", None)
        if not isinstance(record_revision, str) or not record_revision.strip():
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                "the record declares no source revision, so replay evidence "
                "cannot be bound to it",
            )

        if record_revision in excluded:
            return (
                ConsumerRefusalReason.PIT_INADMISSIBLE,
                f"the replay evidence excludes revision {record_revision!r}; a "
                "revision that was not known at the cutoff cannot be replayed "
                "at it",
            )
        if record_revision not in selected:
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                f"the replay evidence selects {sorted(selected)} but the "
                f"evaluated record is revision {record_revision!r}; evidence "
                "about another observation certifies nothing here",
            )

        # F4: the cutoff law orders EVERY selected revision, read from the
        # original sequence so the answer cannot depend on entry order.  The
        # excluded half is deliberately not ordered: an excluded revision is
        # retained BECAUSE it was not known here, and requiring its instant to be
        # inside the window would delete the evidence of its exclusion.
        future: list[str] = []
        for identity, known_from in zip(selected_ids, selected_instants):
            if not isinstance(known_from, datetime):
                return (
                    ConsumerRefusalReason.REPLAY_BLOCKED,
                    "a selected revision's knowledge instant is not a timestamp; "
                    "the selection cannot be placed in time and certifies nothing",
                )
            try:
                placeable = (
                    known_from.tzinfo is not None
                    and known_from.utcoffset() is not None
                )
            except Exception:  # noqa: BLE001 - a hostile tzinfo is malformed
                placeable = False
            if not placeable:
                return (
                    ConsumerRefusalReason.REPLAY_BLOCKED,
                    "a selected revision's knowledge instant is naive, so it "
                    "occupies no position on a timeline; ordering it against the "
                    "cutoff would fabricate a PIT answer",
                )
            if known_from > cutoff:
                future.append(identity)
        if future:
            return (
                ConsumerRefusalReason.PIT_INADMISSIBLE,
                "the replay selection was computed for a LATER cutoff: selected "
                f"revision(s) {sorted(set(future))} became known after this "
                "request's knowledge cutoff, so the selection does not describe "
                "what was known here",
            )

        available = getattr(evidence, "market_available_at", None)
        try:
            if available is not None and available > cutoff:
                return (
                    ConsumerRefusalReason.PIT_INADMISSIBLE,
                    "the replay evidence became market-available after this "
                    "request's knowledge cutoff, so it was not knowable at it",
                )
            declared = getattr(getattr(record, "time", None), "market_available_at", None)
            if declared is not None and available is None:
                return (
                    ConsumerRefusalReason.REPLAY_BLOCKED,
                    "the record declares a market-availability instant that the "
                    "replay evidence does not carry; the availability claim is "
                    "about another row",
                )
            if declared is not None and available is not None and declared != available:
                return (
                    ConsumerRefusalReason.REPLAY_BLOCKED,
                    "the replay evidence names a market-availability instant that "
                    "is not the record's own; two instants for one row mean the "
                    "evidence belongs to another",
                )
        except TypeError:  # noqa: BLE001 - incomparable instants are malformed
            return (
                ConsumerRefusalReason.REPLAY_BLOCKED,
                "the replay evidence's availability instant cannot be compared "
                "with this cutoff or record; malformed evidence certifies nothing",
            )
        return None

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
            # F5: the approved token or the exception CLASS -- never the detail.
            return (
                ConsumerRefusalReason.VERIFICATION_FAILED,
                "the approved evidence set could not be re-derived: "
                f"{_approved_refusal(getattr(exc, 'refusal', None)) or type(exc).__name__}",
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
        try:
            identity = CustodyAuthorityIdentity(
                manifest_sha256=self._manifest_sha256,
                artifact_id=derived.artifact_id,
                approval_id=derived.approval_id,
                registry_digest=derived.registry_digest,
                record_kind=derived.record_kind,
                provider=derived.provider,
                knowledge_cutoff=cutoff,
            )
            expected_identity = custody_authority_identity_digest(identity)
        except Exception as exc:  # noqa: BLE001 - an unbuildable identity is no authority
            # H04: the identity is built from a verification object, and a
            # verification produced by ``model_construct`` can hold values that
            # fail the identity's own laws.  That is a refusal, not a traceback.
            return self._refuse(
                ConsumerRefusalReason.VERIFIER_CRASH,
                f"{_withheld(exc)}; the verification could not be bound to a "
                "complete custody-authority identity, so no basis applies",
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
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
        # H03: an ``AUTHORIZED`` basis is accepted only when it is bound to THIS
        # identity and to an artifact the reviewed root actually approves.  The
        # first check closes "a source that authorizes a record it was not asked
        # about"; the second closes "an empty manifest plus an authorizing
        # source", which is the one configuration where a permissive wiring could
        # otherwise turn the whole integration gate into a rubber stamp.
        if derivation.basis is CustodyAuthorityBasis.AUTHORIZED:
            if derivation.identity_sha256 != expected_identity:
                return self._refuse(
                    ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE,
                    "the authorized basis was not derived for this identity; an "
                    "authorization that does not name the record, approval, "
                    "registry, provider and cutoff it covers is a wildcard",
                    derived=derived,
                    replay_status=replay.status,
                    pit_status=pit_status,
                    custody_status=custody_status,
                )
            if identity.artifact_id not in self._approved_artifact_ids:
                return self._refuse(
                    ConsumerRefusalReason.UNAUTHORIZED_CUSTODY_SOURCE,
                    "the reviewed manifest approves no artifact with this "
                    "identity's artifact id, so no custody source can be "
                    "authorized for it; an empty manifest approves nothing and "
                    "no empty-manifest request may become authorized",
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
                # The token goes FIRST so a bounded field can never truncate the
                # one part an operator has to act on.
                detail = f"unmet {token}: {detail}"
            return self._integration_required(
                detail,
                derived=derived,
                replay_status=replay.status,
                pit_status=pit_status,
                custody_status=custody_status,
            )

        # F1 residual.  Every claim the frozen schema CAN carry now holds:
        # temporal eligibility, revision identity compatibility, and an
        # AUTHORIZED custody basis bound to this exact identity.  The fourth
        # claim -- complete record / provider / artifact evidence binding -- is
        # not expressible in ``ReplayEvidence`` at all, and an
        # ``ACCEPT_FIELD_BINDING`` would read as though it had been established.
        # So the terminal outcome names the unmet contract instead.  Removing
        # this guard is mutation M-BIND: the suite then reports the acceptance
        # that the frozen schema cannot support.
        if not REPLAY_RECORD_BINDING_ESTABLISHED:
            return self._integration_required(
                f"unmet {REPLAY_EVIDENCE_RECORD_BINDING_CONTRACT}: the frozen "
                "replay schema carries no record id, provider, record kind or "
                "artifact identity, so complete evidence binding for this record "
                "cannot be established; met: temporal eligibility, revision "
                "identity compatibility, authority to consume",
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
        """Build a refusal.  Runs on the way out of a failure, so it cannot fail.

        H04: every read of ``derived`` is defensive.  A verification handed in by
        a replaced verifier can be a ``model_construct`` result whose attributes
        hold anything; a refusal builder that raised on such an object would turn
        a fail-closed answer into a crash, which is strictly worse.
        """
        return ConsumerVerdict(
            decision=ConsumerDecision.REFUSE,
            verified_field_allowlist=_identifiers(derived, "fields_verified"),
            unverified_dimensions=_identifiers(derived, "unverified_dimensions"),
            pit_status=pit_status
            or (
                "ADMISSIBLE"
                if bool(getattr(derived, "pit_admissible", False))
                else "INADMISSIBLE"
            ),
            replay_status=_bounded(replay_status, 64),
            custody_status=custody_status
            or (
                "VERIFIED"
                if bool(getattr(derived, "custody_verified", False))
                else "UNVERIFIED"
            ),
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
            verified_field_allowlist=_identifiers(derived, "fields_verified"),
            unverified_dimensions=_identifiers(derived, "unverified_dimensions"),
            pit_status=pit_status,
            replay_status=_bounded(replay_status, 64),
            custody_status=custody_status,
            custody_source_authorization_status=CustodyAuthorityBasis.INTEGRATION_REQUIRED,
            custody_source_authorized=False,
            custody_authorization_detail=_bounded(detail),
        )
