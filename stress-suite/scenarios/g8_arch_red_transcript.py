"""G8 — prior-pass red-evidence harness (STRESS-G8ARCH5).

The repairs after the first closure matrix (STRESS-G8ARCH..G8ARCH4) were reviewed
against *prose* red evidence: the two-tree probes that reproduced their defects
were run in a scratch directory and deleted, so a reviewer could not rerun them.
The mission requires red regressions or EXECUTABLE transcripts for every item,
and a deleted file is neither.

This harness closes that gap for every pass after the closure matrix was written.
It extracts each named pre-pass commit read-only (`git archive`, newline
conversions pinned off, into a temporary directory that is discarded), runs the
SAME probes against that code and against the working tree, and prints what it
observed. It never moves HEAD, never writes to the repository, and never touches
the working tree or its committed artifact.

  python scenarios/g8_arch_red_transcript.py            # print the transcript
  python scenarios/g8_arch_red_transcript.py --write    # also archive it

Archived copy: evidence/G8_ARCH_PRE_REPAIR_RED_TRANSCRIPT.md. Output is
deterministic: sorted iteration, no wall-clock field, relative paths only.

Each probe line ends in `verdict=RED` (the defect was present) or
`verdict=GREEN` (the property holds). A row of the closure matrix cites a probe
id from this file, and the emitter refuses to publish a row whose probe id or
cited head is absent from the archived annex.
"""
from __future__ import annotations

import io
import os
import shutil  # noqa: F401  (used by _copy_working_tree)
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO_ROOT = ROOT.parent

#: (label, commit) for each pass this harness reproduces. Each head is the commit
#: the repair corrected, i.e. the code that carried the defect, so a reviewer can
#: check out that commit and see the same RED lines themselves.
PRE_PASS_HEADS: Tuple[Tuple[str, str], ...] = (
    ("STRESS-G8ARCH2/3", "d859e26e2c7320dda517c623dcb4aaf8afd7060f"),
    ("STRESS-G8ARCH4", "36a84563ccaa0d132c56cda2802ed7996098ae05"),
)

#: every probe id this harness can render, in report order
PROBE_IDS: Tuple[str, ...] = ("ARCH-A", "ARCH-B", "ARCH-C", "ARCH-D",
                              "ARCH-E", "ARCH-F", "ARCH-G")

#: the artifact path is a DECLARED policy with one owner; this harness cites it
#: rather than keeping a second copy of it. Imported after the package root is on
#: the path, because this module doubles as a script (`python scenarios/...`).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from engine.g8_test_evidence import ARTIFACT_RELATIVE_PATH  # noqa: E402

ARCHIVE_PATHS = ("stress-suite",)

#: The probes and the control both run against a COPY whose declared evidence path
#: holds this SYNTHETIC artifact, bound to a fixed tree. A committed artifact is
#: therefore never read or overwritten, and every line of the transcript is
#: reproducible from the tree's code alone.
SYNTHETIC_TREE = "a" * 40
SYNTHETIC_ARTIFACT = (
    '<?xml version="1.0" encoding="utf-8"?>'
    f'<testsuite name="tests" tests="3">'
    f'<properties><property name="tested_sha" value="{SYNTHETIC_TREE}"/></properties>'
    '<testcase classname="t" name="ok_0"/><testcase classname="t" name="ok_1"/>'
    '<testcase classname="t" name="ok_2"/></testsuite>')


def write_synthetic_artifact(tree_root: Path) -> Path:
    """Write the synthetic artifact at the declared path inside a COPY of a tree."""
    target = tree_root / ARTIFACT_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SYNTHETIC_ARTIFACT, encoding="utf-8")
    return target

# --------------------------------------------------------------------------- #
# The probe. Executed as a SUBPROCESS whose cwd is a COPY of the tree under test
# (`<copy>/stress-suite`), so the current session's modules can never be imported
# by accident and the tree's committed artifact is never overwritten.
# --------------------------------------------------------------------------- #
PROBE = r'''
import inspect
import sys
from pathlib import Path

sys.path[:0] = [".", "scenarios", "tests"]

import engine.g8_test_evidence as EV
from engine.g8_test_evidence import (ARTIFACT_RELATIVE_PATH, check_baseline,
                                     junit_document, read_test_evidence,
                                     verify_citation)
from engine.g8_contradiction import decide_gate

lines = []


def emit(tag, observed, red):
    lines.append("%s: %s | verdict=%s" % (tag, observed, "RED" if red else "GREEN"))


TREE = "a" * 40
OTHER = "b" * 40
root = Path("..").resolve()
artifact = root / ARTIFACT_RELATIVE_PATH
artifact.parent.mkdir(parents=True, exist_ok=True)
artifact.write_text(junit_document(cases=3, tested_sha=TREE), encoding="utf-8")
record = read_test_evidence(artifact, expected_tested_sha=TREE, repo_root=root)
published = record.to_dict()

# ARCH-A -- an undeclared tree SKIPPED the baseline's tree comparison, so an
# unknown tree was read as "any tree will do".
verified = check_baseline(record, tested_sha="")["verified"]
emit("ARCH-A", "check_baseline(record, tested_sha='')['verified']=%r" % verified,
     red=bool(verified))

# ARCH-B -- a citation re-derived against its OWN recorded tree, i.e. the evidence
# verified against the evidence's self-report.
params = inspect.signature(verify_citation).parameters
if "expected_tested_sha" not in params:
    emit("ARCH-B", "verify_citation has no declared-tree parameter at all",
         red=True)
else:
    bare = verify_citation(published, repo_root=root, expected_tested_sha="")
    emit("ARCH-B",
         "verify_citation(..., expected_tested_sha='')['verified']=%r "
         "(signature default %r)"
         % (bare["verified"], params["expected_tested_sha"].default),
         red=bool(bare["verified"]))

# ARCH-C -- an unobserved run outcome published as success.
value = published.get("exit_status", "<absent>")
emit("ARCH-C", "the citation publishes exit_status=%r" % (value,),
     red=value != "<absent>")

# ARCH-D -- the citation check was an INPUT a caller could omit (the CLI omitted
# it), so an unverified citation passed the gate.
omittable = "citation_check" in inspect.signature(decide_gate).parameters
emit("ARCH-D", "decide_gate declares citation_check=%r" % (omittable,),
     red=bool(omittable))

# ARCH-E/ARCH-F -- the tree rule the suite applies to a committed package.
try:
    import test_g8_contradiction as T
    rule = getattr(T, "_lagging_tested_tree", None)
except Exception as exc:  # a tree whose test module cannot even import
    rule = None
    lines.append("ARCH-E: importing the tree's test module failed: %r" % (exc,))
if rule is None:
    emit("ARCH-E", "the tree declares no lag rule at all", red=True)
    emit("ARCH-F", "the tree declares no lag rule at all", red=True)
else:
    lagging = rule(TREE, OTHER)
    emit("ARCH-E",
         "rule(package=%s.., code=%s..) -> %r" % (TREE[:8], OTHER[:8], lagging),
         red=not lagging)
    underivable = rule(TREE, "")
    emit("ARCH-F", "rule(package=%s.., code='') -> %r" % (TREE[:8], underivable),
         red=not underivable)

# ARCH-G -- the published canonicalization rule was a LABEL with no resolvable
# definition: the name could stay fixed while the bytes it describes moved.
resolve = hasattr(EV, "canonical_rule")
fingerprint = EV.canonical_rule_fingerprint()[:16] if resolve else None
emit("ARCH-G",
     "published rule %r : resolvable definition=%r fingerprint=%r"
     % (EV.ARTIFACT_CANONICALIZATION_RULE, resolve, fingerprint),
     red=not resolve)

print("\n".join(lines))
'''

HEADER = (
    "# G8 — prior-pass red evidence (STRESS-G8ARCH5)\n"
    "\n"
    "Transcript of the defects fixed by the passes AFTER the first closure\n"
    "matrix, reproduced against the code that carried them. Regenerate with:\n"
    "\n"
    "```\n"
    "cd stress-suite && PYTHONIOENCODING=utf-8 python scenarios/g8_arch_red_transcript.py\n"
    "```\n"
    "\n"
    "The harness extracts each named commit read-only into a temporary directory,\n"
    "copies the working tree into another, and runs the SAME probes against both\n"
    "in a subprocess. It never moves HEAD, never writes to the working tree, and\n"
    "never overwrites a committed artifact. Each probe line ends in\n"
    "`verdict=RED` (the defect was present) or `verdict=GREEN` (the property\n"
    "holds), so every row of the closure matrix that cites this annex resolves to\n"
    "a rerunnable line here.\n"
    "\n"
)


def _extract(sha: str, dest: Path) -> None:
    """Extract the named commit's bytes with newline conversions pinned OFF, so
    the transcript is byte-identical in an LF or a CRLF checkout."""
    archive = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
         "archive", "--format=tar", sha, *ARCHIVE_PATHS],
        cwd=str(REPO_ROOT), check=True, capture_output=True)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(str(dest))


def _copy_working_tree(dest: Path) -> None:
    shutil.copytree(ROOT, dest / "stress-suite",
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))


def _run_probe(tree_root: Path) -> str:
    """Run the probe with cwd set to `<tree_root>/stress-suite`."""
    write_synthetic_artifact(tree_root)
    proc = subprocess.run(
        [sys.executable, "-c", PROBE], cwd=str(tree_root / "stress-suite"),
        capture_output=True, text=True,
        env={**dict(os.environ), "PYTHONIOENCODING": "utf-8"})
    out = proc.stdout.strip()
    if proc.returncode != 0:
        out += f"\nPROBE EXIT {proc.returncode}\n{proc.stderr.strip()}"
    return out


def _review_command_control(tree_root: Path) -> str:
    """CONTROL: on a tree with no Git, the reviewer entry point must REFUSE.

    The tree cannot be derived there, so any verdict it produced would rest on no
    tree at all. This is a must-refuse control rather than a red probe: the CLI
    already refused before this pass, and what these passes changed is that the
    tree RULE refuses too (`rule(package, '')` above).
    """
    # written explicitly rather than relied on as a side effect of the probe, so
    # this line cannot depend on the order the two are called in
    write_synthetic_artifact(tree_root)
    proc = subprocess.run(
        [sys.executable, "scenarios/g8_run_audit.py",
         "evidence/G8_TEST_RESULTS.xml"],
        cwd=str(tree_root / "stress-suite"), capture_output=True, text=True,
        env={**dict(os.environ), "PYTHONIOENCODING": "utf-8"})
    tail = [ln.strip() for ln in (proc.stderr or "").splitlines() if ln.strip()]
    derives = subprocess.run(
        [sys.executable, "-c",
         "from scenarios.g8_tested_tree import derived_tested_tree;"
         "print(repr(derived_tested_tree()))"],
        cwd=str(tree_root / "stress-suite"), capture_output=True, text=True,
        env={**dict(os.environ), "PYTHONIOENCODING": "utf-8"})
    derived = derives.stdout.strip() if derives.returncode == 0 else (
        "no derivation available: the tree rule this pass introduces does not "
        "exist in this tree")
    return ("derived tested tree: %s\nreviewer command exit=%s accepted=%r\n%s"
            % (derived or "''", proc.returncode, proc.returncode == 0,
               tail[-1] if tail else "(no output)"))


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(REPO_ROOT), check=True,
                          capture_output=True, text=True).stdout.strip()


def transcript() -> str:
    lines: List[str] = [HEADER, "pre-pass commits:\n\n"]
    for label, commit in PRE_PASS_HEADS:
        lines.append(f"- {label}: `{commit}` — {_git('log', '-1', '--format=%s', commit)}\n")
    lines.append("\n")
    for label, commit in PRE_PASS_HEADS:
        lines.append(f"## Probes against `{commit}` ({label})\n\n```\n")
        with tempfile.TemporaryDirectory(prefix="g8-arch-") as tmp:
            tree = Path(tmp)
            _extract(commit, tree)
            lines.append(_run_probe(tree) + "\n")
            lines.append("CONTROL: " + _review_command_control(tree) + "\n")
        lines.append("```\n\n")
    lines.append("## Probes against the working tree\n\n```\n")
    with tempfile.TemporaryDirectory(prefix="g8-arch-now-") as tmp:
        tree = Path(tmp)
        _copy_working_tree(tree)
        lines.append(_run_probe(tree) + "\n")
        lines.append("CONTROL: " + _review_command_control(tree) + "\n")
    lines.append("```\n")
    return "".join(lines)


def verdicts(text: str, head: str | None = None) -> Dict[str, str]:
    """Parse `PROBE_ID: ... | verdict=RED|GREEN` lines.

    The same probe is rendered RED against old code and GREEN against the working
    tree, so `head` selects a section: a commit name selects the section extracted
    from that commit, and `None` selects the WORKING-TREE section (the last one).
    Ambiguity between the two is exactly what must not happen here.
    """
    if head is None:
        section = text[text.index("## Probes against the working tree"):]
    else:
        marker = f"## Probes against `{head}`"
        start = text.index(marker)
        # a section ends at the NEXT section header, not at the working-tree
        # header: taking the latter would fold the following commit's probes into
        # this one and report its verdicts under this head (a parser bug that
        # read a later GREEN as this head's RED)
        working = text.index("## Probes against the working tree", start)
        following = text.find("## Probes against `", start + len(marker))
        end = following if 0 <= following < working else working
        section = text[start:end]
    found: Dict[str, str] = {}
    for line in section.splitlines():
        for probe in PROBE_IDS:
            if line.startswith(probe + ":") and "verdict=" in line:
                found[probe] = line.rsplit("verdict=", 1)[1].strip()
    return found


def main(argv: Sequence[str] = ()) -> Dict[str, Any]:
    text = transcript()
    wrote = ""
    if "--write" in list(argv):
        target = ROOT / "evidence" / "G8_ARCH_PRE_REPAIR_RED_TRANSCRIPT.md"
        target.write_text(text, encoding="utf-8", newline="\n")
        wrote = str(target.relative_to(ROOT))
    else:
        sys.stdout.write(text)
    return {"transcript_chars": len(text), "wrote": wrote}


if __name__ == "__main__":
    main(sys.argv[1:])
