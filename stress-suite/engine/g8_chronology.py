# --------------------------------------------------------------------------- #
# STRESS-G8R4 (R-G8-09) — contract chronology.
#
# A gate's verdict rules have to be frozen BEFORE the audit runs, or the audit is
# grading itself. Git can prove that only when the contract's containing commit
# precedes the commit that archives the result. When it does not, the honest
# disposition is to record the stage rather than to assert a freeze.
#
# This module makes the distinction machine-checkable instead of prose-only:
#
#   PRE_RUN_FROZEN_ARTIFACT        committed before the run it governs, with a
#                                  declared baseline it precedes
#   POST_FINDING_AMENDMENT         revised after findings, deliberately stricter
#   RETROSPECTIVE_RECONSTRUCTION   bytes are not recoverable from any object;
#                                  the record is a reconstruction, and may never
#                                  be presented as the pre-run artifact
#
# A reconstruction that claims pre-run freeze is a hard failure. So is an overall
# classification of PRE_RUN_FROZEN_ARTIFACT while any recorded artifact is
# weaker. Nothing here decides the gate: it decides only what the package is
# allowed to CLAIM about its own chronology.
# --------------------------------------------------------------------------- #
from __future__ import annotations

from typing import Any, List, Mapping

STAGES = ("PRE_RUN_FROZEN_ARTIFACT",
          "POST_FINDING_AMENDMENT",
          "RETROSPECTIVE_RECONSTRUCTION")

#: weakest (least provable) stage wins the overall classification. A record may
#: not be summarised as stronger than its weakest element.
_WEAKEST_FIRST = STAGES


class ChronologyError(ValueError):
    """Raised when a chronology record claims more than it can prove."""


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_chronology(record: Mapping[str, Any]) -> dict:
    """Fail closed unless every artifact entry is internally consistent and the
    overall classification is no stronger than the weakest entry."""
    if not isinstance(record, Mapping):
        raise ChronologyError(
            f"contract_chronology must be a mapping, got {type(record).__name__}")
    artifacts: List[Mapping[str, Any]] = [
        a for a in (record.get("artifacts") or [])
        if isinstance(a, Mapping)]
    if not artifacts:
        raise ChronologyError(
            "contract_chronology records no artifact, so its stated "
            "classification cannot be checked against anything")
    stages = []
    for art in artifacts:
        aid = art.get("artifact_id")
        if not _nonempty(aid):
            raise ChronologyError("a chronology entry names no artifact_id")
        stage = art.get("stage")
        if stage not in STAGES:
            raise ChronologyError(
                f"{aid}: stage {stage!r} is not one of {list(STAGES)}")
        stages.append(stage)
        if stage == "RETROSPECTIVE_RECONSTRUCTION":
            if art.get("claims_pre_run_freeze") is not False:
                raise ChronologyError(
                    f"{aid}: a RETROSPECTIVE_RECONSTRUCTION may not claim a "
                    "pre-run freeze — its bytes are not recoverable, so the "
                    "claim cannot be established")
            if not _nonempty(art.get("reconstruction_basis")):
                raise ChronologyError(
                    f"{aid}: a RETROSPECTIVE_RECONSTRUCTION must state the basis "
                    "on which it was reconstructed")
        if stage == "PRE_RUN_FROZEN_ARTIFACT":
            if art.get("claims_pre_run_freeze") is not True:
                raise ChronologyError(
                    f"{aid}: a PRE_RUN_FROZEN_ARTIFACT entry must set "
                    "claims_pre_run_freeze=true")
            if not _nonempty(art.get("introducing_commit_ref")):
                raise ChronologyError(
                    f"{aid}: a PRE_RUN_FROZEN_ARTIFACT must name the commit that "
                    "introduces it")
            if not _nonempty(art.get("pre_run_baseline_ref")):
                raise ChronologyError(
                    f"{aid}: a PRE_RUN_FROZEN_ARTIFACT must name the run/artifact "
                    "it precedes, which is what makes the freeze provable")
        if stage == "POST_FINDING_AMENDMENT":
            if art.get("claims_pre_run_freeze") is not False:
                raise ChronologyError(
                    f"{aid}: a POST_FINDING_AMENDMENT was revised after findings "
                    "and may not claim a pre-run freeze")
            if not (art.get("amendment_revision_refs") or []):
                raise ChronologyError(
                    f"{aid}: a POST_FINDING_AMENDMENT must name the revisions "
                    "that amended it")
    weakest = max(stages, key=_WEAKEST_FIRST.index)
    classification = record.get("classification")
    if classification not in _WEAKEST_FIRST:
        raise ChronologyError(
            f"contract_chronology.classification {classification!r} is not one of "
            f"{list(STAGES)}")
    if _WEAKEST_FIRST.index(classification) < _WEAKEST_FIRST.index(weakest):
        raise ChronologyError(
            f"contract_chronology.classification {classification!r} is stronger "
            f"than its weakest recorded artifact ({weakest}); a record may not be "
            "summarised as more provable than its weakest element")
    if not _nonempty(record.get("gate_blocking_policy_source")):
        raise ChronologyError(
            "contract_chronology must name which artifact supplied the gate's "
            "blocking policy, so blocking status is derived from a policy frozen "
            "before the run rather than from one authored after seeing it")
    return {"classification": classification, "weakest_stage": weakest,
            "artifacts": [a.get("artifact_id") for a in artifacts],
            "stages": stages}
