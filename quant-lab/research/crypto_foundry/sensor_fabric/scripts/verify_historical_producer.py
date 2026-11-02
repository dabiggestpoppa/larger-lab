#!/usr/bin/env python3
"""SENSOR-B5-I10E1 - H1 external historical reproduction harness (read-only).

The I10D1 decision package chose option **H1** (section 7.6) to settle the L8
reproducibility debt: prove a sealed evidence artifact against the exact source
snapshot it measured, from OUTSIDE the sealed producer, without amending it.

Why this exists
---------------
``scripts/b5_i08_units.py`` row ``U08-19`` is a checkpoint-time SOURCE-INVENTORY
assertion ("at B5-I08E1 exactly four modules exist in ``normalization/common/``,
the deferred I09 modules do not exist, and the 24-symbol top-level API is
unchanged") evaluated against the LIVE tree.  Once I09 was authorized to add
three modules to ``common/`` the row could no longer pass on the current tree,
so the accepted pytest pin degenerated from "re-derivable" to "digest-pinned".

That is a CURRENT-TREE answer to a HISTORICAL question.  This harness restores
the historical half at full strength and keeps the two jobs separate:

* **historical reproducibility** (here) -- materialize the recorded source ref
  in a disposable detached worktree, run the historical producer against THAT
  snapshot, require its NORMAL SUCCESS exit code, and require the regenerated
  artifact to equal the ratified SHA-256;
* **current-tree protection** (the pytest scope audits) -- unchanged, and still
  the thing that refuses unauthorized additions to the live tree.

Both are needed.  Neither substitutes for the other.

What this harness deliberately does NOT do
------------------------------------------
* It does not modify, regenerate or re-pin ``bloc_05_unit_validation.json``.
* It does not edit ``b5_i08_units.py`` (that would be option H2, which the
  decision package routed to a separate remediation checkpoint).
* It does not accept an arbitrary producer exit 1.  A refusal payload naming
  rows is reported as a refusal, never as health: the harness requires exit 0
  AND byte equality, and if either fails it reports FAIL with the producer's
  own case list.
* It removes only the temporary worktree it created, addressed by its own
  path; it never prunes unrelated worktrees and never touches the scratch
  paths the checkpoint is required to preserve.

Usage
-----
    python research/crypto_foundry/sensor_fabric/scripts/verify_historical_producer.py
    python .../verify_historical_producer.py --json

Exit codes
----------
    0  reproduces: ref resolved, producer exited 0, artifact equals the pin
    1  could not reproduce (every reason is stated in the payload)
    2  usage error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT = Path(__file__).resolve()
_QUANT_LAB = _SCRIPT.parents[3]
_ROOT = _QUANT_LAB.parent

#: The historical source ref the I08E1 artifact was measured against, recorded
#: by the I10D1 decision package section 7.3/7.6 (the ref that added the I08E1
#: extension block).
SOURCE_REF = "03522870d40b839a2eac28eff7841bfb161e05f3"

#: The ratified artifact and its sealed digest (``BLOC_05_I08_IMPLEMENTATION_
#: EVIDENCE.md`` section 4; also pinned by the I08 scope audit).
ARTIFACT = (
    "quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/"
    "bloc_05_unit_validation.json"
)
EXPECTED_SHA256 = "260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4"

#: The sealed historical producer.
PRODUCER = "quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i08_units.py"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=_ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_ref(ref: str) -> tuple[bool, str, str]:
    """Verify the ref exists and resolves to the expected immutable commit."""
    kind = _git("cat-file", "-t", ref)
    if kind.returncode != 0:
        return False, "", f"ref {ref} does not exist in this repository"
    if kind.stdout.strip() != "commit":
        return (
            False,
            "",
            f"ref {ref} resolves to a {kind.stdout.strip()!r}, not a commit",
        )
    resolved = _git("rev-parse", f"{ref}^{{commit}}")
    if resolved.returncode != 0:
        return False, "", f"ref {ref} does not resolve to a commit"
    sha = resolved.stdout.strip()
    if sha != ref:
        return False, sha, f"ref {ref} resolved to {sha}: not the expected immutable commit"
    return True, sha, ""


def _create_worktree(ref: str, base: Path) -> tuple[bool, str, str]:
    """Materialize the ref in a disposable detached worktree."""
    target = base / "snapshot"
    created = _git("worktree", "add", "--detach", str(target), ref)
    if created.returncode != 0:
        return False, str(target), (created.stderr or created.stdout).strip()
    return True, str(target), ""


def _remove_worktree(target: str) -> str:
    """Remove ONLY the worktree this harness created, by path."""
    removed = _git("worktree", "remove", "--force", target)
    if removed.returncode != 0:
        shutil.rmtree(target, ignore_errors=True)
        _git("worktree", "prune")
        return (removed.stderr or removed.stdout).strip()
    return ""


def verify() -> dict:
    """Run the full H1 proof and return a machine-readable record."""
    payload: dict = {
        "harness": "SENSOR-B5-I10E1-H1",
        "approach": "external historical-snapshot verification (no sealed code touched)",
        "source_ref": SOURCE_REF,
        "producer": PRODUCER,
        "artifact": ARTIFACT,
        "expected_sha256": EXPECTED_SHA256,
        "scope": "historical source-snapshot reproduction",
    }

    ok, sha, why = _resolve_ref(SOURCE_REF)
    payload["ref_exists"] = ok
    payload["resolved_commit"] = sha
    if not ok:
        payload["verdict"] = "FAIL"
        payload["blocked_by"] = why
        return payload
    payload["ref_is_immutable_commit"] = True

    base = Path(tempfile.mkdtemp(prefix="b5i08-repro-"))
    target = ""
    try:
        created, target, why = _create_worktree(SOURCE_REF, base)
        payload["worktree_created"] = created
        if not created:
            payload["verdict"] = "FAIL"
            payload["blocked_by"] = f"cannot materialize the snapshot: {why}"
            return payload

        snapshot_root = Path(target)
        producer = snapshot_root / PRODUCER
        artifact = snapshot_root / ARTIFACT
        if not producer.is_file():
            payload["verdict"] = "FAIL"
            payload["blocked_by"] = f"the snapshot does not carry {PRODUCER}"
            return payload

        # Run the HISTORICAL producer against the HISTORICAL snapshot.  Its
        # ``--check`` mode writes nothing and prints a JSON summary.
        run = subprocess.run(
            [sys.executable, str(producer), "--check"],
            cwd=snapshot_root / "quant-lab",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        payload["producer_exit_code"] = run.returncode
        payload["producer_stdout"] = run.stdout.strip()[-2000:]
        if run.returncode != 0:
            # A refusal payload names its rows.  Exit 1 here is NOT health: the
            # harness reports the named cases instead of accepting the refusal.
            named = ""
            for stream in (run.stderr, run.stdout):
                for line in stream.splitlines():
                    line = line.strip()
                    if line.startswith("{") and "cases" in line:
                        named = line
            payload["verdict"] = "FAIL"
            payload["blocked_by"] = (
                "the historical producer did not exit 0 against its own snapshot"
            )
            payload["named_cases"] = named
            return payload

        if not artifact.is_file():
            payload["verdict"] = "FAIL"
            payload["blocked_by"] = f"the snapshot does not carry {ARTIFACT}"
            return payload

        measured = _sha256(artifact)
        payload["measured_sha256"] = measured
        payload["bytes_match_pin"] = measured == EXPECTED_SHA256
        payload["producer_reported"] = run.stdout.strip()[-500:]
        if measured != EXPECTED_SHA256:
            payload["verdict"] = "FAIL"
            payload["blocked_by"] = (
                "the historical artifact does not equal the ratified digest"
            )
            return payload

        payload["verdict"] = "PASS"
        payload["distinction"] = (
            "This proves the SEALED I08 artifact against the source snapshot it "
            "measured.  It is not a statement about the current tree: the "
            "current-tree U08-19 refusal remains documented and is owned by the "
            "pytest scope audits."
        )
        return payload
    finally:
        if target:
            cleaned = _remove_worktree(target)
            payload["worktree_removed"] = cleaned == ""
            if cleaned:
                payload["worktree_removal_note"] = cleaned
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit only the machine-readable payload",
    )
    args = parser.parse_args(sys.argv[1:])

    payload = verify()
    blob = json.dumps(payload, indent=2, sort_keys=True)
    if args.json:
        print(blob)
    else:
        print(f"historical reproduction: {payload['verdict']}")
        print(f"  source ref        : {SOURCE_REF}")
        print(f"  producer exit     : {payload.get('producer_exit_code')}")
        print(f"  expected sha256   : {EXPECTED_SHA256}")
        print(f"  measured sha256   : {payload.get('measured_sha256')}")
        if payload["verdict"] != "PASS":
            print(f"  blocked by        : {payload.get('blocked_by')}")
        print(blob)
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
