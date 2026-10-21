"""Family clustering around representatives — canon 2.7.6, 2.7.9.

Candidates that declare the same lineage family are clustered around a
representative, so investigating one representative can stand in for its family.
The deferral row that follows from this ("same family as its representative")
is emitted by ``ranking``; this module only decides what a family *is* and who
represents it.

The only lineage signal available at discovery is the adapter-declared
``novelty_family``; richer lineage detection belongs to repository intelligence
(Block 3) and is deliberately *not* inferred here.

``family_identity_for`` is the single definition of "the same family" that this
package publishes and compares, so grouping, novelty sizing and saturation
accounting cannot disagree about it.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Mapping, Sequence, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.report import CandidateFamily

from qcae.discovery.planning.canonical import (
    descending_id,
    merge_canonical_candidates,
)

__all__ = ["build_families", "family_identity_for"]


def family_identity_for(candidate: CanonicalCandidate) -> str:
    """The one family identity this package publishes and compares (canon 2.7.6).

    Clustering, novelty sizing and saturation accounting must agree on what
    "the same family" means, or a caller using the ids ranking actually emitted
    can never match them and repeat families stay invisible to saturation.
    """
    label = candidate.novelty_family or f"singleton:{candidate.canonical_id}"
    return "fam-" + hashlib.sha256(label.encode("utf-8")).hexdigest()[:16]


def build_families(
    candidates: Sequence[CanonicalCandidate],
    scores: Mapping[str, float],
) -> Tuple[CandidateFamily, ...]:
    """Cluster candidates around representatives (canon 2.7.6).

    Candidates are aggregated first, so a family's membership is the set canon
    2.1.12 defines rather than however many merge passes happened to run.
    """
    candidates = merge_canonical_candidates(candidates)
    groups: Dict[str, List[CanonicalCandidate]] = {}
    for candidate in candidates:
        groups.setdefault(family_identity_for(candidate), []).append(candidate)

    families: List[CandidateFamily] = []
    for group_id in sorted(groups):
        members = sorted(groups[group_id], key=lambda c: c.canonical_id)
        representative = max(
            members,
            key=lambda c: (float(scores.get(c.canonical_id, 0.0)), descending_id(c.canonical_id)),
        )
        singleton = len(members) == 1
        family = CandidateFamily(
            family_id=group_id,
            representative_candidate_id=representative.canonical_id,
            member_candidate_ids=tuple(m.canonical_id for m in members),
            shared_lineage=(
                f"adapter-declared novelty family {representative.novelty_family!r}"
                if not singleton
                else "singleton candidate (no shared lineage declared)"
            ),
            independent_family=singleton,
        )
        family.validate()
        families.append(family)
    return tuple(families)
