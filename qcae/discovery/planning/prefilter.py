"""Hard-prefilter enforcement — canon 2.7.3.

A prefilter decision is a judgement about a candidate, and canon 2.7.3 forbids
taking one on evidence weaker than the prefilter declares it needs. This module
owns that floor: the caller states what evidence actually exists, and a decision
taken on weaker evidence is refused rather than recorded.

Enforcement lives here rather than in the ranking pass because the pass consumes
decisions and never makes them — "reject because a README did not mention a
license" must not be expressible anywhere.
"""

from __future__ import annotations

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.plan import HardPrefilter
from qcae.core.discovery.report import PrefilterDecision, PrefilterDecisionRecord
from qcae.core.errors import QcaeValidationError
from qcae.core.vocabulary import EVIDENCE_STRENGTH_ORDER, EvidenceClass

__all__ = ["apply_hard_prefilter"]


def apply_hard_prefilter(
    prefilter: HardPrefilter,
    candidate: CanonicalCandidate,
    decision: PrefilterDecision,
    evidence_class: EvidenceClass,
    rationale: str,
) -> PrefilterDecisionRecord:
    """Record a prefilter judgement, enforcing its evidence floor (2.7.3).

    The caller states what evidence actually exists. A decision taken on
    evidence weaker than the prefilter's own floor is refused, so "reject because
    a README did not mention a license" is not expressible.
    """
    if EVIDENCE_STRENGTH_ORDER.index(evidence_class) < EVIDENCE_STRENGTH_ORDER.index(
        prefilter.min_evidence_class
    ):
        raise QcaeValidationError(
            f"prefilter {prefilter.prefilter_id!r} requires at least "
            f"{prefilter.min_evidence_class.value} evidence; {evidence_class.value} was "
            "supplied (canon 2.7.3: weak metadata cannot justify a decision)"
        )
    record = PrefilterDecisionRecord(
        candidate_id=candidate.canonical_id,
        prefilter_id=prefilter.prefilter_id,
        decision=decision,
        evidence_class=evidence_class,
        rationale=rationale,
    )
    record.validate()
    return record
