"""Canonical candidate identity and merge — canon 2.1.12.

Leads that point at the same normalized locator become one canonical candidate
with every path preserved. Identity is content-addressed, so merging is
deterministic across runs and duplicate paths are counted as duplication rather
than as corroboration (2.7.16 invariant 3).

Normalization is deliberately conservative: over-normalizing would merge
genuinely distinct candidates, so only well-defined equivalences are applied.
Anything more provider-specific belongs in the adapter that owns that
provider's quirks (Book V 15.3 adapter isolation).

``descending_id`` lives here because it is the deterministic tie-break over
canonical identity that grouping and ordering both use.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Sequence, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import CandidateKind, CandidateLead

__all__ = [
    "canonical_key_for",
    "descending_id",
    "merge_canonical_candidates",
    "merge_leads",
]

#: Kinds whose provider itself defines identity case-insensitively.
_CASE_INSENSITIVE_KINDS = {
    CandidateKind.REPOSITORY: "case-insensitive",
    CandidateKind.PACKAGE: "case-insensitive",
}


def canonical_key_for(candidate_kind: CandidateKind, source_locator: str) -> str:
    """Normalize a locator into a merge key (deliberately conservative).

    Over-normalizing would merge genuinely distinct candidates, so only
    well-defined equivalences are applied: surrounding whitespace, a trailing
    slash, a ``.git`` suffix, and — for repository/package identity, where the
    provider itself defines case-insensitive identity — letter case. Anything
    more provider-specific belongs in the adapter that owns that provider's
    quirks (Book V 15.3 adapter isolation).
    """
    locator = (source_locator or "").strip()
    while locator.endswith("/"):
        locator = locator[:-1]
    if locator.endswith(".git"):
        locator = locator[:-4]
    if candidate_kind in _CASE_INSENSITIVE_KINDS:
        locator = locator.lower()
    return f"{candidate_kind.value}:{locator}"


def _canonical_id_for(key: str) -> str:
    """Content-addressed candidate identity (deterministic across runs)."""
    return "cand-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def descending_id(canonical_id: str) -> str:
    """Tie-break: prefer the lexicographically smallest ID deterministically."""
    return "".join(chr(0x10FFFF - ord(ch)) if ord(ch) < 0x10FFFF else ch for ch in canonical_id)


def merge_canonical_candidates(
    candidates: Sequence[CanonicalCandidate],
) -> Tuple[CanonicalCandidate, ...]:
    """Aggregate candidate records that share one canonical identity (2.1.12).

    Real runs merge leads per adapter outcome and then aggregate the passes, so
    the same project can arrive as two records carrying the same
    content-addressed ``canonical_id``. Aggregating unions the fields that
    preserve discovery paths — lead ids, locators, source classes, claims,
    revisions, readiness and conflicts — rather than dropping a record, because
    canon 2.1.12 requires every path that found the candidate to survive. The
    first record for an identity supplies its kind and canonical locator (both
    are functions of that identity). Every unioned field is order-insensitive and
    record order follows first appearance, so aggregating is idempotent and
    independent of the order in which adapter passes happen to complete.
    """
    aggregated: Dict[str, CanonicalCandidate] = {}
    for candidate in candidates:
        previous = aggregated.get(candidate.canonical_id)
        if previous is None:
            aggregated[candidate.canonical_id] = candidate
            continue
        aggregated[candidate.canonical_id] = CanonicalCandidate(
            canonical_id=previous.canonical_id,
            canonical_key=previous.canonical_key,
            candidate_kind=previous.candidate_kind,
            canonical_locator=previous.canonical_locator,
            merged_locators=tuple(sorted(set(previous.merged_locators)
                                         | set(candidate.merged_locators))),
            lead_ids=tuple(sorted(set(previous.lead_ids) | set(candidate.lead_ids))),
            ready_lead_ids=tuple(sorted(
                set(previous.ready_lead_ids) | set(candidate.ready_lead_ids))),
            source_classes=tuple(sorted(
                set(previous.source_classes) | set(candidate.source_classes),
                key=lambda sc: sc.value,
            )),
            claims_atoms=tuple(sorted(set(previous.claims_atoms)
                                     | set(candidate.claims_atoms))),
            retrieved_revisions=tuple(sorted(set(previous.retrieved_revisions)
                                             | set(candidate.retrieved_revisions))),
            license_claims=tuple(sorted(set(previous.license_claims)
                                       | set(candidate.license_claims))),
            constraint_conflicts=tuple(sorted(set(previous.constraint_conflicts)
                                             | set(candidate.constraint_conflicts))),
            languages=tuple(sorted(set(previous.languages) | set(candidate.languages))),
            novelty_family=previous.novelty_family or candidate.novelty_family,
            notes=previous.notes or candidate.notes,
        )
    for candidate in aggregated.values():
        candidate.validate()
    return tuple(aggregated.values())


def merge_leads(leads: Sequence[CandidateLead]) -> Tuple[CanonicalCandidate, ...]:
    """Merge discovery paths into canonical candidates (canon 2.1.12)."""
    groups: Dict[str, List[CandidateLead]] = {}
    for lead in leads:
        lead.validate()
        key = canonical_key_for(lead.candidate_kind, lead.source_locator)
        groups.setdefault(key, []).append(lead)

    merged: List[CanonicalCandidate] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda item: item.lead_id)
        kind = members[0].candidate_kind
        locators = sorted({m.source_locator.strip() for m in members})
        canonical_locator = min(
            locators, key=lambda value: (canonical_key_for(kind, value), value)
        )
        claims: List[str] = []
        conflicts: List[str] = []
        licenses: List[str] = []
        languages: List[str] = []
        families: List[str] = []
        revisions: List[str] = []
        for member in members:
            for claim in member.claimed_capabilities + member.possible_atom_matches:
                if claim not in claims:
                    claims.append(claim)
            for conflict in member.initial_constraint_conflicts:
                if conflict not in conflicts:
                    conflicts.append(conflict)
            if member.license_claim and member.license_claim not in licenses:
                licenses.append(member.license_claim)
            if member.language_runtime and member.language_runtime not in languages:
                languages.append(member.language_runtime)
            if member.novelty_family and member.novelty_family not in families:
                families.append(member.novelty_family)
            if member.retrieved_revision and member.retrieved_revision not in revisions:
                revisions.append(member.retrieved_revision)

        candidate = CanonicalCandidate(
            canonical_id=_canonical_id_for(key),
            canonical_key=key,
            candidate_kind=kind,
            canonical_locator=canonical_locator,
            merged_locators=tuple(locators),
            lead_ids=tuple(m.lead_id for m in members),
            source_classes=tuple(
                sorted({m.source_class for m in members}, key=lambda sc: sc.value)
            ),
            claims_atoms=tuple(sorted(claims)),
            ready_lead_ids=tuple(m.lead_id for m in members if m.deeper_intelligence_ready),
            retrieved_revisions=tuple(sorted(revisions)),
            license_claims=tuple(licenses),
            constraint_conflicts=tuple(conflicts),
            languages=tuple(sorted(languages)),
            novelty_family=min(families) if families else "",
        )
        candidate.validate()
        merged.append(candidate)
    return tuple(merged)
