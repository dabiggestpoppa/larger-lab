"""The single owner of "does a closure row resolve?" (STRESS-G8ARCH6/ARCH7).

The closure matrix certifies each finding with RED evidence from an archived
transcript and GREEN evidence that runs in the authoritative suite. Both halves
used to be enforced by a SUBSTRING SCAN -- the red half inside the emitter (plus
eight literal copies of the annex names) and the green half beside the row table
-- which accepted:

  * a row claiming RED where the annex rendered GREEN at the head it named,
  * a head string that merely occurred anywhere in the transcript,
  * a green regression or artifact that is not in the tree,
  * a row citing no green regression at all.

All of these are the "no detected violation therefore proves the property"
pattern this gate exists to forbid -- the same class as R-G8-01, where merely
invoking the comparator counted as coverage. Every half is re-derived here: from
the harnesses' DECLARED probe ids and pre-pass heads and their PARSED verdicts,
from the test module the suite actually collects, and from the evidence directory
the package is written to. ONE call answers whether a row resolves, so no consumer
keeps a second opinion about it.

A row therefore declares only:
  * `red_probe` -- which harness declares it determines which annex it lives in,
    so a row cannot name an annex (and an unknown annex can no longer reach a
    dict lookup, which raised a bare KeyError);
  * `red_head` -- optional only when the harness declares exactly one head; a
    row citing a head the harness never ran against is refused, and so is a row
    whose probe is GREEN or ABSENT at the head it does name;
  * `green_tests` -- at least one, each defined in the G8 test module, so the
    matrix cannot cite a regression that does not run;
  * `artifacts` -- each an emitted output or a committed input of the package.
"""
from __future__ import annotations

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

#: the suite that collects the green regressions a row may cite, and the committed
#: evidence directory holding artifacts cited as INPUTS rather than emitted
#: outputs. Both are derived from this file's own location, so a row is checked
#: against the tree the package ships in.
_ROOT = Path(__file__).resolve().parents[1]
TEST_MODULE = _ROOT / "tests" / "test_g8_contradiction.py"
COMMITTED_EVIDENCE = _ROOT / "evidence"

#: controls that rerun the red harnesses inside the authoritative suite. The
#: matrix cites them as a set rather than per row, and they are resolved by the
#: same gate because they are the same kind of claim: this test runs.
RED_SURVIVAL_TESTS = (
    "test_the_pre_repair_red_transcript_still_reproduces_every_finding",
    "test_the_red_transcript_artifact_on_disk_matches_the_harness",
    "test_the_arch_red_transcript_still_reproduces_every_finding",
    "test_the_arch_red_transcript_artifact_on_disk_matches_the_harness",
)


def declared() -> List[Dict[str, Any]]:
    """What the harnesses declare (probe ids and heads), for diagnostics."""
    return [{"annex": harness.ANNEX,
             "probes": list(harness.PROBE_IDS),
             "heads": [sha for _, sha in harness.PRE_PASS_HEADS]}
            for harness in HARNESSES]


def survival_problems(tests_src: str | None = None) -> List[str]:
    """A cited survival control must itself be collected by the suite."""
    src = (TEST_MODULE.read_text(encoding="utf-8") if tests_src is None
           else tests_src)
    return [f"red-survival control {name} is not in the test module"
            for name in RED_SURVIVAL_TESTS if f"def {name}(" not in src]


def _harness_for(probe_id: str) -> Any:
    for harness in HARNESSES:
        if probe_id in harness.PROBE_IDS:
            return harness
    return None


def _red(entry: Mapping[str, Any], evidence_dir: Path) -> Dict[str, str]:
    """The RED half: the probe must be declared and genuinely RED at its head."""
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


def _green(name: str, tests_src: str) -> None:
    """The GREEN half: the regression must be defined in the collected module."""
    if f"def {name}(" not in tests_src:
        raise ValueError(
            f"green regression {name} is not in the test module "
            f"({TEST_MODULE.name}): a row may cite only a regression the "
            "authoritative suite collects")


def _artifact(name: str, evidence_dir: Path) -> None:
    """The artifact half: an emitted output, or a committed input of the package."""
    if not ((evidence_dir / name).exists() or (COMMITTED_EVIDENCE / name).exists()):
        raise ValueError(f"artifact {name} does not exist")


def resolve(entry: Mapping[str, Any],
            evidence_dir: str | Path) -> Dict[str, str]:
    """Everything a row resolves to, or ValueError saying why it cannot.

    One call covers all three halves, so a consumer cannot resolve the RED half
    and believe the row is fully resolved.
    """
    evidence_dir = Path(evidence_dir)
    resolved = _red(entry, evidence_dir)
    tests_src = TEST_MODULE.read_text(encoding="utf-8")
    green = entry.get("green_tests") or ()
    if not green:
        raise ValueError(
            f"row {entry.get('finding') or entry.get('red_probe')!r} cites no "
            "green regression: a row may not be closed without evidence that "
            "runs in the authoritative suite")
    for name in green:
        _green(str(name), tests_src)
    for name in entry.get("artifacts", ()):
        _artifact(str(name), evidence_dir)
    return resolved


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
    """Resolve every row ONCE, or refuse the whole matrix.

    The rows returned are the rows that were checked: resolving twice would let a
    row validate under one evaluation and the matrix publish the verdict of a
    second that no refusal inspected.
    """
    resolved: List[Dict[str, str]] = []
    found: List[str] = []
    for entry in entries:
        try:
            resolved.append(resolve(entry, evidence_dir))
        except ValueError as exc:
            found.append(str(exc))
    found.extend(survival_problems())
    if found:
        raise ValueError(
            "the closure matrix cites evidence that does not resolve: "
            + "; ".join(found))
    return resolved
