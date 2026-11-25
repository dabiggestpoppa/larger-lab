"""SENSOR-B5-P3 - production trust-consumer DATA CONTRACTS (Rung 1).

The production half of the P3 trust consumer that the design package
(``p3_production_design_r0``) specifies and that
``BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md`` deliberately left in ``tests/``.
This module is types and laws only:

* :class:`ConsumerRequest` -- what an untrusted caller may ask for.  It carries
  a complete T1 record, the artifact bytes, the evidence references, an
  offset-aware knowledge cutoff and replay *evidence*; it carries NO authority
  object, no verdict, no callback and no authorization flag.  There is no
  parameter a caller could use to assert an outcome, because
  ``extra="forbid"`` makes one unrepresentable.
* :class:`ConsumerVerdict` -- what the policy returns.  Three decisions, one
  trust scope, and four separate claims that are routinely collapsed into one
  badge by mistake: field binding, custody integrity, custody-source
  authorization, and PIT/replay admissibility.
* :class:`ConsumerDecision`, :class:`ConsumerRefusalReason`,
  :class:`CustodyAuthorityBasis` -- the closed vocabularies.

**A verdict is a data representation, not an authorization capability.**  A
model instance -- including one produced by ``model_construct`` or
``model_copy(update=...)``, which bypass every validator here -- proves
nothing about who derived it.  ``tests/.../test_b5_p3_consumer_contracts.py``
demonstrates both bypasses by executing them; the boundary that actually
matters is that the *policy* re-derives from evidence and never reads a
verdict as input.  ``frozen=True`` prevents attribute assignment on the
ordinary path and is not claimed to prevent either bypass.

Because it is data-only, this module performs no verification, opens no
custody store, loads no manifest and derives no authority.  It imports the two
concrete T1 record types because the request must name a real record, and the
I05 replay-evidence type because replay evidence is *data* the policy
adjudicates.  It does not import ``sensors/verification.py``: measured in a
clean subprocess by the contract suite, so the contract cannot become a second
source of truth for verification.

OFFLINE.  No network, no filesystem, no wall clock, no hashing, no id
generation.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from ..models import NormalizationModelBase, OpaqueIdentifier
from ..sensors.liquidation import T1LiquidationRecord
from ..sensors.trade import T1TradeRecord
from ..time.replay_gate import ReplayEvidence

__all__ = [
    "CustodyAuthorityBasis",
    "ConsumerDecision",
    "ConsumerEvidenceReference",
    "ConsumerRefusalReason",
    "ConsumerRequest",
    "ConsumerVerdict",
    "TRUST_SCOPE_ECONOMIC_FIELD_BINDING",
]

#: The only trust scope ``RecordVerification`` can carry
#: (``sensors/verification.py::TRUST_SCOPE_ECONOMIC_FIELD_BINDING``).  Repeated
#: here as a literal so a verdict cannot be constructed with a wider scope:
#: ``Literal`` makes the forged value unrepresentable rather than merely
#: refused at inspection time.
TRUST_SCOPE_ECONOMIC_FIELD_BINDING = "ECONOMIC_FIELD_BINDING"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_BARE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: A diagnostic string may name what failed; it may never carry payload.  The
#: bound is enforced by the type so no code path can widen it by accident.
_DETAIL_MAX = 400


class ConsumerDecision(str, Enum):
    """Exactly three outcomes.  ``ACCEPT`` and ``AUTHORIZED`` are not decisions.

    ``ACCEPT`` was refused by the design (A1.2): an unconditional accept would
    erase the field-scope distinction.  ``AUTHORIZED`` is a *basis*, not a
    decision; keeping them in separate vocabularies is what stops
    "authorized custody" being read as "trusted record".
    """

    ACCEPT_FIELD_BINDING = "ACCEPT_FIELD_BINDING"
    REFUSE = "REFUSE"
    INTEGRATION_REQUIRED = "INTEGRATION_REQUIRED"


class CustodyAuthorityBasis(str, Enum):
    """Exactly three bases.  ``SYNTHETIC_TEST_ONLY`` does not exist in ``src/``.

    The harness needed a synthetic basis so field-scope logic stayed testable
    under an empty manifest.  A production enum containing "not really
    authorized but let it through" is a permanent invitation to wire it to a
    config flag, so production removes the state instead of shipping it
    (design spec E).  The test seam is a wiring double in ``tests/``, not a
    value here.
    """

    AUTHORIZED = "AUTHORIZED"
    INTEGRATION_REQUIRED = "INTEGRATION_REQUIRED"
    UNAUTHORIZED = "UNAUTHORIZED"


class ConsumerRefusalReason(str, Enum):
    """The closed refusal vocabulary, in the design's normative order.

    Twelve codes come from the design (``03_RUNG1_IMPLEMENTATION_SPEC.md``
    section 1).  Two more were added because the later rungs need to name a
    specific control instead of laundering it into ``VERIFICATION_FAILED``:

    * ``TRUSTED_CONTEXT_MISMATCH`` -- named by ``03_TRUST_BOUNDARY_SPEC.md``
      section A for a claimed-manifest mismatch (Rung 2, A04);
    * ``EVIDENCE_NOT_BOUND_TO_ARTIFACT`` -- Rung 4's cross-record evidence
      control: the reference is intact but belongs to another artifact.

    ``CACHED_VERDICT_DIVERGENCE`` is reserved and deliberately unreachable in
    production: the divergence interface was omitted (design Rung 2 says to
    prefer omitting it), so no cached verdict can enter the intake path at all.
    A reserved code is honest; a reachable seam that exists only to emit it
    would not be.
    """

    FORGED_TRUST_SCOPE = "FORGED_TRUST_SCOPE"
    EMPTY_UNVERIFIED_DIMENSIONS = "EMPTY_UNVERIFIED_DIMENSIONS"
    EVIDENCE_BYTES_MISSING = "EVIDENCE_BYTES_MISSING"
    EVIDENCE_BYTES_MISMATCH = "EVIDENCE_BYTES_MISMATCH"
    EVIDENCE_NOT_BOUND_TO_ARTIFACT = "EVIDENCE_NOT_BOUND_TO_ARTIFACT"
    FIELD_NOT_IN_ALLOWLIST = "FIELD_NOT_IN_ALLOWLIST"
    PIT_INADMISSIBLE = "PIT_INADMISSIBLE"
    REPLAY_BLOCKED = "REPLAY_BLOCKED"
    NAIVE_CUTOFF = "NAIVE_CUTOFF"
    TRUSTED_CONTEXT_MISMATCH = "TRUSTED_CONTEXT_MISMATCH"
    CACHED_VERDICT_DIVERGENCE = "CACHED_VERDICT_DIVERGENCE"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    VERIFIER_CRASH = "VERIFIER_CRASH"
    UNAUTHORIZED_CUSTODY_SOURCE = "UNAUTHORIZED_CUSTODY_SOURCE"


# ---------------------------------------------------------------------------
# Cutoff laws -- measured, not assumed
# ---------------------------------------------------------------------------


def _reject_bare_date(value: object) -> object:
    """Refuse a date-only cutoff before pydantic coerces it to midnight.

    Measured on pydantic 2.13.4: a bare ``date`` supplied for a ``datetime``
    field is ACCEPTED and coerced to 00:00, and the string ``"2026-06-01"`` is
    accepted the same way.  A trust boundary that silently invents a midnight
    has invented a PIT answer, so both shapes are refused by name here rather
    than left to the library's default.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        raise ValueError(
            "a bare date cannot order a knowledge cutoff: it does not say when "
            "during the day the knowledge existed, and assuming midnight is a "
            "fabricated PIT answer (design F-R1-04)"
        )
    if isinstance(value, str) and _BARE_DATE_RE.match(value.strip()):
        raise ValueError(
            "a date-only cutoff string cannot order a knowledge cutoff; supply "
            "an offset-aware instant"
        )
    return value


def _require_offset(value: datetime) -> datetime:
    """Refuse a naive instant; normalise an offset-aware one to UTC.

    Both facts are measured rather than assumed: pydantic accepts a naive
    ``datetime`` for a ``datetime`` field, and ``astimezone`` on a naive value
    would silently adopt the host's local zone -- a wall-clock dependency inside
    a PIT law.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "knowledge_cutoff must be offset-aware; a naive instant has no "
            "position on a timeline and cannot order anything"
        )
    return value.astimezone(timezone.utc)


#: A validated knowledge cutoff: no bare date, no naive instant, UTC-normalised.
KnowledgeCutoffInstant = Annotated[
    datetime,
    BeforeValidator(_reject_bare_date),
    AfterValidator(_require_offset),
]


# ---------------------------------------------------------------------------
# Evidence references
# ---------------------------------------------------------------------------


class ConsumerEvidenceReference(NormalizationModelBase):
    """One requested evidence reference and the digest the caller believes it has.

    A bare ``tuple[str, str]`` cannot reject a malformed digest, and a ``dict``
    field is a mutable caller-owned mapping whose iteration order a consumer
    cannot rely on.  A frozen pair with two laws gives an immutable, ordered,
    self-validating value.

    The digest is a *claim to be checked*, never custody: Rung 4 re-reads the
    bytes through the policy's provider and re-hashes them (P2B-11/F-R1-01 --
    a digest that travels alone is not custody).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    reference: OpaqueIdentifier
    approved_digest: OpaqueIdentifier

    @model_validator(mode="after")
    def _digest_law(self) -> ConsumerEvidenceReference:
        if not _SHA256_HEX_RE.match(self.approved_digest):
            raise ValueError(
                "approved_digest must be 64 lowercase hex characters; a reference "
                "whose digest cannot be compared certifies nothing"
            )
        return self


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class ConsumerRequest(NormalizationModelBase):
    """What a caller may ask the policy to evaluate.  Nothing here is authority.

    Field-by-field, and why each one is safe to accept from an untrusted actor:

    ``record``
        A complete T1 record.  Pinned to the two concrete types, so an
        authority object, a verdict or an arbitrary mapping cannot ride in
        through it.  The record may itself carry an upstream
        ``authority_provenance`` *claim* -- that is the claim under test, not a
        grant.
    ``artifact_bytes``
        The registry bytes the record's approval should cover.  Hidden from
        ``repr`` so a log line cannot leak the artifact.
    ``required_fields``
        A narrowing filter, never a grant: an unknown name refuses with
        ``FIELD_NOT_IN_ALLOWLIST`` because it will not be in the derived
        allowlist.
    ``evidence_references``
        Ordered claims about evidence.  Refused (not sorted) when out of
        canonical order or duplicated, on the same precedent as the T1 quality
        flag ordering law: silently sorting rewrites caller data.
    ``knowledge_cutoff``
        Required for evaluation; offset-aware; no bare date, no naive instant.
    ``replay_evidence``
        I05 *evidence*.  The policy applies ``assess_replay_eligibility``
        itself; a caller-supplied evaluation has no field to arrive in.
    ``claimed_manifest_bytes``
        Compared against the policy's pinned root and never adopted.  Present
        so a caller's approval never follows its own record (spec A / A04).

    There is deliberately no ``candidate``/``rederive``/``verdict`` field: the
    divergence interface is omitted rather than shipped as an unused seam.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        ser_json_bytes="base64",
        val_json_bytes="base64",
    )

    record: T1TradeRecord | T1LiquidationRecord
    artifact_bytes: bytes = Field(repr=False, min_length=1)
    required_fields: tuple[OpaqueIdentifier, ...] = ()
    evidence_references: tuple[ConsumerEvidenceReference, ...] = ()
    knowledge_cutoff: KnowledgeCutoffInstant | None = None
    replay_evidence: ReplayEvidence | None = None
    claimed_manifest_bytes: bytes | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def _required_fields_unique(self) -> ConsumerRequest:
        if len(set(self.required_fields)) != len(self.required_fields):
            raise ValueError("required_fields contains duplicates")
        return self

    @model_validator(mode="after")
    def _evidence_canonical(self) -> ConsumerRequest:
        references = [item.reference for item in self.evidence_references]
        if len(set(references)) != len(references):
            raise ValueError(
                "evidence_references names one reference twice; two claims about "
                "one reference are a contradiction, not a stronger claim"
            )
        keyed = [(item.reference, item.approved_digest) for item in self.evidence_references]
        if keyed != sorted(keyed):
            raise ValueError(
                "evidence_references is not in canonical ascending (reference, "
                "digest) order; it is refused rather than silently sorted so the "
                "caller's data is never rewritten under them"
            )
        return self


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


class ConsumerVerdict(NormalizationModelBase):
    """The policy's answer.  Four separate claims, never one badge.

    ``verified_field_allowlist`` names the canonical fields the verifier
    re-derived.  ``unverified_dimensions`` names what the answer does NOT
    cover, and an acceptance with an empty list is refused by this model's own
    laws -- an empty list reads as whole-record authentication, which no
    evaluator in this repository can support (P2cR1 F-R1-02).

    ``custody_status`` (the approved bytes were handed over and hashed here) and
    ``custody_source_authorization_status`` (an operator-authorized custody
    source covers this exact identity) stay independent, and
    ``custody_source_authorized`` may only agree with ``AUTHORIZED``.  Today the
    only reachable pair is verified-with-``INTEGRATION_REQUIRED``, because the
    shipped manifest approves nothing.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: ConsumerDecision
    trust_scope: Literal["ECONOMIC_FIELD_BINDING"] = TRUST_SCOPE_ECONOMIC_FIELD_BINDING
    verified_field_allowlist: tuple[OpaqueIdentifier, ...] = ()
    unverified_dimensions: tuple[OpaqueIdentifier, ...] = ()
    pit_status: OpaqueIdentifier
    replay_status: OpaqueIdentifier
    custody_status: OpaqueIdentifier
    custody_source_authorization_status: CustodyAuthorityBasis
    custody_source_authorized: bool = False
    #: Why the authority requirement is met, unmet or violated -- a bounded
    #: diagnostic, never authority itself.  ``INTEGRATION_REQUIRED`` carries no
    #: ``refusal_reason`` (nothing was violated), so without this field the
    #: consumer could not say which requirement is missing.
    custody_authorization_detail: str | None = Field(default=None, max_length=_DETAIL_MAX)
    refusal_reason: ConsumerRefusalReason | None = None
    refusal_detail: str | None = Field(default=None, max_length=_DETAIL_MAX)

    @model_validator(mode="after")
    def _decision_laws(self) -> ConsumerVerdict:
        refuses = self.decision is ConsumerDecision.REFUSE
        if refuses and self.refusal_reason is None:
            raise ValueError("REFUSE requires a refusal_reason")
        if not refuses and self.refusal_reason is not None:
            raise ValueError(
                f"{self.decision.value} must not carry refusal metadata; a "
                "non-refusal that names a violation is two answers at once"
            )
        if not refuses and self.refusal_detail is not None:
            raise ValueError(f"{self.decision.value} must not carry refusal_detail")

        authorized = (
            self.custody_source_authorization_status is CustodyAuthorityBasis.AUTHORIZED
        )
        if self.custody_source_authorized != authorized:
            raise ValueError(
                "custody_source_authorized must equal "
                "(custody_source_authorization_status is AUTHORIZED); the boolean "
                "and the basis may not disagree"
            )
        if authorized and self.decision is not ConsumerDecision.ACCEPT_FIELD_BINDING:
            raise ValueError(
                "an AUTHORIZED custody source with a non-accepting decision is "
                "contradictory: authorization is not an outcome by itself"
            )
        if self.decision is ConsumerDecision.ACCEPT_FIELD_BINDING:
            if not self.verified_field_allowlist:
                raise ValueError(
                    "ACCEPT_FIELD_BINDING requires at least one verified field; an "
                    "acceptance that binds nothing is not an acceptance"
                )
            if not self.unverified_dimensions:
                raise ValueError(
                    "ACCEPT_FIELD_BINDING requires the dimensions it does NOT cover "
                    "to be enumerated; an empty list claims whole-record "
                    "authentication (P2cR1 F-R1-02)"
                )
        if (
            self.decision is ConsumerDecision.INTEGRATION_REQUIRED
            and self.custody_source_authorization_status
            is not CustodyAuthorityBasis.INTEGRATION_REQUIRED
        ):
            raise ValueError(
                "INTEGRATION_REQUIRED means the authority requirement is unmet, so "
                "the basis must say INTEGRATION_REQUIRED"
            )
        return self

    @property
    def accepted(self) -> bool:
        """True only for ``ACCEPT_FIELD_BINDING`` -- and that is field scope only."""
        return self.decision is ConsumerDecision.ACCEPT_FIELD_BINDING
