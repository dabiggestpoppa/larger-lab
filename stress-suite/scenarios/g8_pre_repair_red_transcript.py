"""G8 — pre-repair red-evidence harness (STRESS-G8R0).

The closure review required each finding R-G8-01..R-G8-09 to be reproduced RED
against the pre-repair head before the repair, and the reproduction had to
survive in the repository rather than in an ephemeral scratch directory.

This harness materialises the pre-repair tree from Git (read-only: `git archive`
of the named commit, extracted to a temporary directory that is discarded), runs
the probes against THAT code, and prints exactly what it observed. It never
moves HEAD, never writes to the repository, and never touches the working tree.

  python scenarios/g8_pre_repair_red_transcript.py            # print the transcript
  python scenarios/g8_pre_repair_red_transcript.py --write    # also archive it

The archived copy is evidence/G8_PRE_REPAIR_RED_TRANSCRIPT.md. Output is
deterministic: no wall-clock field, sorted iteration, relative paths only.
"""
from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Sequence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO_ROOT = ROOT.parent

#: the head under review, i.e. the PROVISIONAL first G8 PASS this repair corrects
PRE_REPAIR_HEAD = "6c015f86408a56721f8999e4aa39b218fab0fd4d"

#: the paths the probes need. `quant-lab/.../CEREBUS_v4_Manual_EXTRACTED.txt`
#: is included because R-G8-08 is a statement about that source binding.
ARCHIVE_PATHS = ("stress-suite", "quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt")

CONTRACT_REL = "stress-suite/evidence/G8_EQUIVALENCE_CONTRACT.json"
S16_FIXTURE_REL = "stress-suite/scenarios/s16_cerebus_contradiction/doctrine_claims.json"
MANUAL_REL = "quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt"
AUDIT_REL = "stress-suite/scenarios/g8_run_audit.py"

# --------------------------------------------------------------------------- #
# The probe. Executed as a SUBPROCESS with cwd set to the extracted pre-repair
# tree, so this session's repaired modules can never be imported by accident.
# --------------------------------------------------------------------------- #
PROBE = r'''
import hashlib, inspect, json, re, sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "scenarios")

import g8_run_audit as A
import g8_emit_evidence as E
from engine.g8_contradiction import decide_gate, load_contract, mandated_pair_coverage

lines = []


def emit(tag, text):
    lines.append("%s: %s" % (tag, text))


contract = load_contract("evidence/G8_EQUIVALENCE_CONTRACT.json")

# ---- R-G8-01 ------------------------------------------------------------ #
families = [A.run_comparison_family(contract, f, A.collect_observations(contract))
            for f in contract["comparison_families"]
            if f["family_id"] != "F7"]
coverage = mandated_pair_coverage(contract, families)
guarded = [g for f in families for g in f.guarded]
mandated_nc = [c for f in families for c in f.comparisons
               if c.verdict == "NOT_COMPARABLE" and c.mandated]
decision = decide_gate(contract, families, guarded, [],
                       measured_full=973, collected_full=973)
emit("R-G8-01",
     "mandated_observed=%s/%s  uncovered_reported=%s  "
     "NOT_COMPARABLE(mandated)=%s  gate=%s  (F7 excluded from this probe: it "
     "needs the archived evidence tree)"
     % (coverage["mandated_comparisons_observed"], coverage["mandated_pairs"],
        len(coverage["uncovered_mandated_pairs"]), len(mandated_nc),
        decision["exit"]))
f2_nc = sorted({(c.left_ref, c.right_ref, c.verdict) for c in mandated_nc
                if c.family_id == "F2"})
emit("R-G8-01", "mandated NOT_COMPARABLE pairs in F2: %s"
     % json.dumps([list(x) for x in f2_nc], sort_keys=True))

# ---- R-G8-02 ------------------------------------------------------------ #
emit("R-G8-02",
     "_profit_never_reduced({'profit': 10, 'items': [{'disposition': "
     "'VALIDATED'}]}) -> %r"
     % A._profit_never_reduced({"profit": 10,
                                "items": [{"disposition": "VALIDATED"}]}))
emit("R-G8-02", "inspect.getsource(_profit_never_reduced) tail: %s"
     % json.dumps([ln.strip() for ln in
                   inspect.getsource(A._profit_never_reduced).splitlines()
                   if "or True" in ln]))

# ---- R-G8-03 ------------------------------------------------------------ #
emit("R-G8-03",
     "_has_provenance({'evidence_provenance': 'UNKNOWN', 'evidence_lineage': "
     "'UNKNOWN'}) -> %r"
     % A._has_provenance({"evidence_provenance": "UNKNOWN",
                          "evidence_lineage": "UNKNOWN"}))

# ---- R-G8-04 ------------------------------------------------------------ #
emit("R-G8-04", "_g4_runtime_neutral('S13') -> %r ; "
     "_g4_runtime_neutral('S99_NO_SUCH_SCENARIO') -> %r"
     % (A._g4_runtime_neutral("S13"), A._g4_runtime_neutral("S99_NO_SUCH_SCENARIO")))
emit("R-G8-04", "inspect.getsource(_g4_runtime_neutral): %s"
     % json.dumps(inspect.getsource(A._g4_runtime_neutral).strip()))

# ---- R-G8-05 ------------------------------------------------------------ #
class _Res(object):
    """The minimum shape `_refusal_observed` reads: `.phases` of mappings."""

    def __init__(self, phases):
        self.phases = phases


emit("R-G8-05", "_refusal_observed(single refusal phase, nothing else) -> %r"
     % A._refusal_observed(_Res([{"phase": "DIRECTIVE_REFUSED"}])))
emit("R-G8-05", "_refusal_observed(refusal AFTER an escalation phase) -> %r"
     % A._refusal_observed(_Res([{"phase": "DIRECTIVE_APPLIED"},
                                 {"phase": "DIRECTIVE_REFUSED"}])))
emit("R-G8-05", "P8 declared in the G6 observation as: %s"
     % json.dumps(re.findall(r'"P8":\s*([A-Za-z]+)', Path(AUDIT_REL_LITERAL).read_text(
         encoding="utf-8"))))
emit("R-G8-05", "_availability_derived({'operator_availability': 'UNAVAILABLE'}) "
     "-> %r" % A._availability_derived({"operator_availability": "UNAVAILABLE"}))

# ---- R-G8-06 ------------------------------------------------------------ #
audit_src = Path(AUDIT_REL_LITERAL).read_text(encoding="utf-8")
p6_lines = [ln.strip() for ln in audit_src.splitlines()
            if re.match(r"^\s*p6 = \(True if \(raw_reviewers", ln)]
emit("R-G8-06", "the P6 derivation in the G3 observation builder: %s"
     % json.dumps(p6_lines))

# ---- R-G8-07 ------------------------------------------------------------ #
emit("R-G8-07", "inspect.signature(emit) -> %s" % inspect.signature(E.emit))
for scalar in (1, 9999):
    receipt = E.emit(scalar)["receipt"]
    emit("R-G8-07",
         "emit(%s)['receipt'] -> collected=%r passed=%r failed=%r "
         "inherited=%r new_g8_test_count=%r; receipt records a test-results "
         "artifact -> %r; receipt records an artifact digest -> %r"
         % (scalar, receipt["collected"], receipt["passed"], receipt["failed"],
            receipt["inherited_test_count"], receipt["new_g8_test_count"],
            "test_evidence_artifact" in receipt, "artifact_digest" in receipt))

# ---- R-G8-08 ------------------------------------------------------------ #
raw = Path(MANUAL_REL).read_bytes()
lf = raw.replace(b"\r\n", b"\n")
crlf = lf.replace(b"\n", b"\r\n")
declared = json.loads(Path(S16_FIXTURE_REL).read_text(encoding="utf-8"))[0][
    "source_fingerprint"]
emit("R-G8-08", "this (archive) checkout: bytes=%s sha256=%s"
     % (len(raw), hashlib.sha256(raw).hexdigest()))
emit("R-G8-08", "synthetic LF:   bytes=%s sha256=%s" % (len(lf), hashlib.sha256(lf).hexdigest()))
emit("R-G8-08", "synthetic CRLF: bytes=%s sha256=%s" % (len(crlf), hashlib.sha256(crlf).hexdigest()))
emit("R-G8-08", "the S16 fixture declares: %s" % declared)
emit("R-G8-08", "fixture digest == LF digest -> %r ; == CRLF digest -> %r"
     % (declared == hashlib.sha256(lf).hexdigest(),
        declared == hashlib.sha256(crlf).hexdigest()))

# ---- R-G8-09 ------------------------------------------------------------ #
emit("R-G8-09", "contract status: %s" % json.dumps(contract.get("status")))
emit("R-G8-09", "contract version: %s" % json.dumps(contract.get("version")))
emit("R-G8-09", "contract freeze_note: %s" % json.dumps(contract.get("freeze_note")))
emit("R-G8-09", "contract declares contract_chronology -> %r"
     % ("contract_chronology" in contract))

print("\n".join(lines))
'''

#: the probe runs with cwd set to the extracted `stress-suite` directory, so it
#: needs the audit path relative to that directory (not to the repo root).
_PROBE = PROBE.replace("AUDIT_REL_LITERAL", repr(AUDIT_REL.split("stress-suite/", 1)[1]))
_PROBE = _PROBE.replace('Path(MANUAL_REL)',
                        "Path(%s)" % repr("../" + MANUAL_REL))
_PROBE = _PROBE.replace(
    'Path(S16_FIXTURE_REL)',
    "Path(%s)" % repr(S16_FIXTURE_REL.split("stress-suite/", 1)[1]))

HEADER = (
    "# G8 — pre-repair red evidence (STRESS-G8R0)\n"
    "\n"
    "Transcript of the audit-closure defects reproduced against the pre-repair\n"
    "head, before any repair was applied. Regenerate with:\n"
    "\n"
    "```\n"
    "cd stress-suite && PYTHONIOENCODING=utf-8 python scenarios/g8_pre_repair_red_transcript.py\n"
    "```\n"
    "\n"
    "The harness extracts the named commit read-only into a temporary directory,\n"
    "runs the probes against THAT code in a subprocess, and discards it. It never\n"
    "moves HEAD and never writes to the working tree.\n"
    "\n"
)


def _extract(sha: str, dest: Path) -> None:
    """Extract the named commit's bytes DETERMINISTICALLY.

    `git archive` is subject to the invoker's newline conversion (`core.autocrlf`),
    so on a CRLF checkout the same commit would export CRLF bytes and the probe
    would report a different digest of the very artifact this transcript is
    about — the harness would inherit exactly the defect it documents (R-G8-08).
    The conversions are therefore pinned off for the extraction: the transcript
    is byte-identical in any checkout.
    """
    archive = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
         "archive", "--format=tar", sha, *ARCHIVE_PATHS],
        cwd=str(REPO_ROOT), check=True, capture_output=True)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(str(dest))


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(REPO_ROOT), check=True,
                          capture_output=True, text=True).stdout.strip()


def transcript(with_git_log: bool = True) -> str:
    """Build the transcript.

    The PROBE section is deterministic: it depends only on the pre-repair commit,
    never on this repository's later history. The Git-evidence section is a
    snapshot of the history AS OF the archive commit and therefore grows when the
    contract is amended again (which is the point of R-G8-09), so callers that
    need a stable comparison ask for the probe section alone.
    """
    revision = _git("rev-parse", PRE_REPAIR_HEAD)
    subject = _git("log", "-1", "--format=%s", PRE_REPAIR_HEAD)
    lines: List[str] = [HEADER,
                        f"pre-repair commit: `{revision}`\n",
                        f"pre-repair subject: `{subject}`\n\n",
                        "## Probes against the pre-repair code\n\n```\n"]
    with tempfile.TemporaryDirectory(prefix="g8-prerepair-") as tmp:
        tree = Path(tmp)
        _extract(PRE_REPAIR_HEAD, tree)
        probe = subprocess.run(
            [sys.executable, "-c", _PROBE], cwd=str(tree / "stress-suite"),
            capture_output=True, text=True,
            env={**dict(__import__("os").environ), "PYTHONIOENCODING": "utf-8"})
        lines.append(probe.stdout.strip() + "\n")
        if probe.returncode != 0:
            lines.append(f"PROBE EXIT {probe.returncode}\n{probe.stderr.strip()}\n")
    lines.append("```\n")
    if not with_git_log:
        return "".join(lines)
    lines.append("\n## Git evidence for R-G8-09 (contract chronology)\n\n"
                 "Snapshot of the history as of the commit that archived this "
                 "transcript; the list grows if the contract is amended again, "
                 "which is itself the recorded finding.\n\n```\n")
    lines.append("$ git log --all --oneline -- %s\n" % CONTRACT_REL)
    log_text = _git("log", "--all", "--oneline", "--", CONTRACT_REL) or ""
    lines.append((log_text or "(no commit)") + "\n")
    lines.append("```\n\n")
    # the commit count is DERIVED from the log above, never asserted: an earlier
    # revision of this harness hardcoded "one commit", which the live log
    # falsified as soon as the repair itself amended the contract.
    touched = [ln for ln in log_text.splitlines() if ln.strip()]
    earliest = touched[-1].split(" ", 1)[0] if touched else "none"
    lines.append(
        "Git resolves %d commit(s) touching the contract; the earliest is\n"
        "`%s`. That earliest snapshot already carries the revisions motivated\n"
        "by the first run's own findings, so Git cannot show that those verdict\n"
        "rules were frozen before the first comparison ran. The claim recorded\n"
        "in the pre-repair contract (`FROZEN_AT_STRESS-G8P0`, `authored BEFORE\n"
        "any cross-scenario comparison runs`) is therefore retracted as\n"
        "unsupported and replaced by the staged chronology record in\n"
        "`contract_chronology`.\n" % (len(touched), earliest))
    return "".join(lines)


def main(argv: Sequence[str] = ()) -> Dict[str, Any]:
    text = transcript()
    wrote = ""
    if "--write" in list(argv):
        target = ROOT / "evidence" / "G8_PRE_REPAIR_RED_TRANSCRIPT.md"
        # deterministic newline policy: evidence artifacts are LF, never
        # whatever the host's default translation would produce
        target.write_text(text, encoding="utf-8", newline="\n")
        wrote = str(target.relative_to(ROOT))
    else:
        sys.stdout.write(text)
    return {"transcript_chars": len(text), "wrote": wrote}


if __name__ == "__main__":
    main(sys.argv[1:])
