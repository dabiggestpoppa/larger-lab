"""The single owner of "does a closure row's RED evidence resolve?" (STRESS-G8ARCH6).

The closure matrix certifies each finding with RED evidence from an archived
transcript. That guarantee was enforced by a SUBSTRING SCAN inside the emitter
(plus eight literal copies of the annex names), which accepted:

  * a row claiming RED where the annex rendered GREEN at the head it named, and
  * a head string that merely occurred anywhere in the transcript.

Both are the "no detected violation therefore proves the property" pattern this
gate exists to forbid -- the same class as R-G8-01, where merely invoking the
comparator counted as coverage. The rule is re-derived here from the harnesses'
DECLARED probe ids and pre-pass heads and their PARSED verdicts, so it has one
implementation for every row and every consumer.

A row therefore declares only:
  * `red_probe` -- which harness declares it determines which annex it lives in,
    so a row cannot name an annex (and an unknown annex can no longer reach a
    dict lookup, which raised a bare KeyError);
  * `red_head` -- optional only when the harness declares exactly one head; a
    row citing a head the harness never ran against is refused, and so is a row
    whose probe is GREEN or ABSENT at the head it does name.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

try:  # imported as a package member (the emitter)
    from scenarios import g8_arch_red_transcript as ARCH
    from scenarios import g8_pre_repair_red_transcript as RED
except ImportError:  # imported top-level (the authoritative suite's path setup)
    import g8_arch_red_transcript as ARCH  # type: ignore
    import g8_pre_repair_red_transcript as RED  # type: ignore

#: every harness that publishes red evidence, in a fixed order. Adding a harness
#: HERE is the only way a row can cite one.
HARNESSES = (RED, ARCH)


def declared() -> List[Dict[str, Any]]:
    """What the harnesses declare (probe ids and heads), for diagnostics."""
    return [{"annex": harness.ANNEX,
             "probes": list(harness.PROBE_IDS),
             "heads": [sha for _, sha in harness.PRE_PASS_HEADS]}
            for harness in HARNESSES]


def _harness_for(probe_id: str) -> Any:
    for harness in HARNESSES:
        if probe_id in harness.PROBE_IDS:
            return harness
    return None


def resolve(entry: Mapping[str, Any], evidence_dir: str | Path) -> Dict[str, str]:
    """The RED evidence a row resolves to, or ValueError saying why it cannot.

    The check is a RE-DERIVATION: the probe must be declared, the head must be
    one the harness ran against, and the harness's own parsed verdict for that
    probe at that head must be RED.
    """
    evidence_dir = Path(evidence_dir)
    probe = str(entry.get("red_probe", ""))
    harness = _harness_for(probe)
    if harness is None:
        every = sorted(p for h in HARNESSES for p in h.PROBE_IDS)
        raise ValueError(
            f"RED probe {probe!r} is not declared by any red-evidence harness "
            f"(declared: {every})")
    heads = [sha for _, sha in harness.PRE_PASS_HEADS]
    head = str(entry.get("red_head") or "")
    if not head:
        if len(heads) != 1:
            raise ValueError(
                f"{probe} is rendered against {len(heads)} heads in "
                f"{harness.ANNEX} and its verdict differs by head, so the row "
                f"must name one of {heads}")
        head = heads[0]
    elif head not in heads:
        raise ValueError(
            f"head {head} is not declared by {harness.ANNEX} (declared: {heads}): "
            "a row may cite only a head the harness actually ran against")
    annex = evidence_dir / harness.ANNEX
    if not annex.exists():
        raise ValueError(f"the annex {harness.ANNEX} is absent from {evidence_dir}")
    verdict = harness.verdicts(annex.read_text(encoding="utf-8"), head).get(
        probe, "ABSENT")
    if verdict != "RED":
        raise ValueError(
            f"row {entry.get('finding') or probe!r} claims RED evidence for "
            f"{probe} at {head}, but {harness.ANNEX} renders {verdict} there: a "
            "row may cite only evidence that is genuinely RED at the head it "
            "names")
    return {"red_probe": probe, "red_head": head, "red_annex": harness.ANNEX,
            "annex_verdict": verdict}


def problems(entries: Sequence[Mapping[str, Any]],
             evidence_dir: str | Path) -> List[str]:
    """Every row that cannot resolve, so one refusal names them all."""
    found: List[str] = []
    for entry in entries:
        try:
            resolve(entry, evidence_dir)
        except ValueError as exc:
            found.append(str(exc))
    return found


def require(entries: Sequence[Mapping[str, Any]],
            evidence_dir: str | Path) -> List[Dict[str, str]]:
    """Resolve every row, or refuse the whole matrix."""
    found = problems(entries, evidence_dir)
    if found:
        raise ValueError(
            "the closure matrix cites evidence that does not resolve: "
            + "; ".join(found))
    return [resolve(entry, evidence_dir) for entry in entries]
