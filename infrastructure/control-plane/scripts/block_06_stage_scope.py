"""Fail-closed stage identity resolution for the Book 6 validators.

The B6-I0 validator was frozen while B6-I0 was the terminal stage. Its boundary laws read
origin/main, the changed-file set and the added-module set, so on any later stage they report the
later stage's authorized work as a violation. This module resolves stage identity mechanically and
refuses to guess: an unknown, missing, dirty or tampered identity is a failure, never a fallback.

Mode "i0" is the strict historical replay and does not consult any later-stage file.
Mode "auto" resolves exactly one committed, clean, self-consistent identity:

* B6-I2 when the B6-I2 registration, scope and contract are committed and origin/main is the
  B6-I1 merge. I0 and I1 packets must be byte-identical to their pinned heads, and B6-I3..I9
  artifacts must be absent.
* B6-I1 otherwise, but only when origin/main is still the B6-I0 merge.

Later-stage authority is never inferred from a branch name, a PR title, or a working-copy file.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

DOCS = "docs/oce-golden-system"
I0_BASE = "5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6"
I0_HEAD = "c5d7bfcc5ea99837985ba82a3c91fd1e76d85a81"
I0_MERGE = "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e"
I1_SCOPE = f"{DOCS}/OCE_BLOCK_06_I1_SCOPE_DERIVATION_v1.0.json"
I1_CONTRACT = f"{DOCS}/OCE_BLOCK_06_I1_IMPLEMENTATION_CONTRACT_v1.0.json"
I1_HEAD = "96e3b81714321f4eea7abcb300ef471e93be0962"
I1_MERGE = "4496d548078660efd7ad4f93e7fff461d34ea538"
I2_SCOPE = f"{DOCS}/OCE_BLOCK_06_I2_SCOPE_DERIVATION_v1.0.json"
I2_CONTRACT = f"{DOCS}/OCE_BLOCK_06_I2_IMPLEMENTATION_CONTRACT_v1.0.json"
I2_REG = f"{DOCS}/OCE_BLOCK_06_I2_STAGE_SCOPE_REGISTRATION_v1.0.json"
AMENDMENT = f"{DOCS}/OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json"
AMENDMENT_ID = "B6-I0-STAGE-SCOPE-AMENDMENT-001"
SUPERSEDED_BLOB = "6648043b24b0010f6bd405e0ea6098097b4de78d"
SUPERSEDED_SHA256 = "a6ed3314881c1a0ed4587b8dfc1a09c18da2b34c29d86b7406c66bbd50a0c6e1"
MODES = ("i0", "auto")
KNOWN_LATER_STAGES = ("B6-I1",)
LATER_STAGES = tuple(f"I{i}" for i in range(3, 10))
# Pinned: a committed amendment cannot widen its own allowlist.
AMENDMENT_PATHS = (
    AMENDMENT,
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    "infrastructure/control-plane/tests/block_06_i0_support.py",
    "infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
    "infrastructure/control-plane/tests/stage_scope/test_i0_stage_scope_amendment_controls.py",
    "infrastructure/control-plane/tests/test_block_06_i0_book5_regression.py",
    ".github/workflows/block-06-i0-validation.yml",
)
# Pinned: the surfaces the B6-I2 registration itself is allowed to author or amend.
I2_PINNED = (
    I2_REG,
    I2_SCOPE,
    I2_CONTRACT,
    f"{DOCS}/OCE_BLOCK_06_I2_ACCOUNTING_CORRECTION_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I2_MANIFEST_v1.0.json",
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    "infrastructure/control-plane/scripts/block_06_i2_validate.py",
    "infrastructure/control-plane/scripts/block_06_i2_mutation_battery.py",
    "infrastructure/control-plane/scripts/block_06_i2_paired.py",
    "infrastructure/control-plane/scripts/block_06_i2_stage_controls.py",
    "infrastructure/control-plane/scripts/block_06_i2_generate.py",
    "infrastructure/control-plane/tests/stage_scope/test_i0_stage_scope_amendment_controls.py",
    ".github/workflows/block-06-i0-validation.yml",
    ".github/workflows/block-06-i1-validation.yml",
    ".github/workflows/block-06-i2-validation.yml",
    ".github/workflows/block-06-i2-paired-comparison.yml",
)


class StageScopeError(Exception):
    def __init__(self, check: str, detail) -> None:
        super().__init__(f"{check}: {detail}")
        self.check = check
        self.detail = detail


def _git(root: pathlib.Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _require_identity_file(root: pathlib.Path, rel: str) -> None:
    path = root / rel
    if not path.exists():
        raise StageScopeError("stage/identity_missing", rel)
    code, _ = _git(root, "cat-file", "-e", f"HEAD:{rel}")
    if code != 0:
        raise StageScopeError("stage/identity_missing", f"not tracked at HEAD: {rel}")
    code, _ = _git(root, "diff", "--quiet", "HEAD", "--", rel)
    if code != 0:
        raise StageScopeError("stage/identity_spoofed", f"working copy differs from HEAD: {rel}")


def _reject_later_artifacts(root: pathlib.Path) -> None:
    code, tree = _git(root, "ls-tree", "-r", "--name-only", "HEAD")
    if code != 0:
        raise StageScopeError("stage/identity_missing", "HEAD tree is unreadable")
    later = [p for p in tree.splitlines()
             if any(f"OCE_BLOCK_06_{stage}_" in p for stage in LATER_STAGES)]
    if later:
        raise StageScopeError("stage/later_stage_absent", later)


def _resolve_i2(root: pathlib.Path, base: str) -> dict:
    if base != I1_MERGE:
        raise StageScopeError("stage/base_moved", base)
    code, _ = _git(root, "merge-base", "--is-ancestor", I1_MERGE, "HEAD")
    if code != 0:
        raise StageScopeError("stage/base_moved", "HEAD does not descend from the B6-I1 merge")
    for rel in (I2_REG, I2_SCOPE, I2_CONTRACT):
        _require_identity_file(root, rel)
    registration = json.loads((root / I2_REG).read_text(encoding="utf-8"))
    scope = json.loads((root / I2_SCOPE).read_text(encoding="utf-8"))
    contract = json.loads((root / I2_CONTRACT).read_text(encoding="utf-8"))
    if registration.get("status") != "FROZEN" or registration.get("frozen_before_results") is not True:
        raise StageScopeError("stage/identity_unknown", registration.get("status"))
    if registration.get("document_id") != "OCE-B6-I2-STAGE-SCOPE-REGISTRATION-001":
        raise StageScopeError("stage/identity_unknown", registration.get("document_id"))
    if scope.get("stage") != "B6-I2" or contract.get("stage") != "B6-I2":
        raise StageScopeError("stage/identity_unknown", (scope.get("stage"), contract.get("stage")))
    if contract.get("status") != "FROZEN" or contract.get("frozen_before_results") is not True:
        raise StageScopeError("stage/identity_unknown", contract.get("status"))
    prior = registration.get("prior_stages") or {}
    if prior.get("B6-I0", {}).get("head") != I0_HEAD or prior.get("B6-I1", {}).get("head") != I1_HEAD:
        raise StageScopeError("stage/identity_tampered", prior)
    this = registration.get("this_stage") or {}
    if this.get("base") != I1_MERGE or this.get("base_tree") != scope.get("base_tree"):
        raise StageScopeError("stage/identity_tampered", this.get("base"))
    prefixes = tuple(this.get("allowed_prefixes") or ())
    if not prefixes or "oce/templates/" not in prefixes or "oce/harness/" not in prefixes:
        raise StageScopeError("stage/identity_unknown", "B6-I2 registration declares no authority")
    # The B6-I1 ratification head is the frozen baseline for both prior packets: the B6-I0
    # amendment was legitimately revised at B6-I1, so I0_HEAD is not the immutable baseline.
    for label in ("I0", "I1"):
        code, diff = _git(root, "diff", "--name-only", f"{I1_HEAD}..HEAD", "--", DOCS)
        if code != 0:
            raise StageScopeError("stage/identity_missing", f"cannot compare {label} packet")
        frozen = [line for line in diff.splitlines()
                  if f"OCE_BLOCK_06_{label}_" in line]
        if frozen:
            raise StageScopeError("stage/identity_tampered", frozen)
    _reject_later_artifacts(root)
    allowed = tuple(dict.fromkeys(prefixes + I2_PINNED))
    i1_scope = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    i1_owned = tuple(i1_scope.get("allowed_paths") or ())
    i2_owned = tuple(p for p in allowed if p.startswith("oce/"))
    # The I0 validator's later-stage mode treats this as the complete oce authority of the stage
    # chain, so the B6-I1 surfaces stay admitted and only the I2 surfaces are added.
    oce_authority = tuple(dict.fromkeys(i1_owned + i2_owned))
    return {
        "mode": "i2",
        "requested": "auto",
        "stage": "B6-I2",
        "identity": {
            "registration_sha256": hashlib.sha256((root / I2_REG).read_bytes()).hexdigest(),
            "scope_sha256": hashlib.sha256((root / I2_SCOPE).read_bytes()).hexdigest(),
            "contract_sha256": hashlib.sha256((root / I2_CONTRACT).read_bytes()).hexdigest(),
            "i0_head": I0_HEAD,
            "i1_head": I1_HEAD,
            "i1_merge": I1_MERGE,
        },
        "allowed": allowed,
        "i1_allowed": oce_authority,
        "amendment": I2_PINNED,
        "i0_merge": I1_MERGE,
    }


def _resolve_i1(root: pathlib.Path, base: str) -> dict:
    if base != I0_MERGE:
        raise StageScopeError("stage/base_moved", base)
    code, _ = _git(root, "merge-base", "--is-ancestor", I0_MERGE, "HEAD")
    if code != 0:
        raise StageScopeError("stage/base_moved", "HEAD does not descend from the B6-I0 merge")

    for rel in (I1_SCOPE, I1_CONTRACT, AMENDMENT):
        _require_identity_file(root, rel)

    scope = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    contract = json.loads((root / I1_CONTRACT).read_text(encoding="utf-8"))
    amendment = json.loads((root / AMENDMENT).read_text(encoding="utf-8"))

    if scope.get("stage") not in KNOWN_LATER_STAGES:
        raise StageScopeError("stage/identity_unknown", scope.get("stage"))
    if contract.get("stage") != "B6-I1" or contract.get("status") != "FROZEN":
        raise StageScopeError("stage/identity_unknown",
                              (contract.get("stage"), contract.get("status")))
    if amendment.get("amendment_id") != AMENDMENT_ID or amendment.get("status") != "FROZEN":
        raise StageScopeError("stage/identity_unknown", amendment.get("amendment_id"))

    code, blob = _git(root, "rev-parse",
                      f"{I0_HEAD}:infrastructure/control-plane/scripts/block_06_i0_validate.py")
    if code != 0 or blob.split()[0] != SUPERSEDED_BLOB:
        raise StageScopeError("stage/identity_tampered", "I0 head validator blob differs")
    raw = subprocess.run(["git", "cat-file", "blob", SUPERSEDED_BLOB], cwd=root,
                         capture_output=True)
    if raw.returncode != 0 or hashlib.sha256(raw.stdout).hexdigest() != SUPERSEDED_SHA256:
        raise StageScopeError("stage/identity_tampered", "I0 head validator bytes differ")
    superseded = amendment.get("superseded_validator", {})
    if superseded.get("blob") != SUPERSEDED_BLOB or superseded.get("sha256") != SUPERSEDED_SHA256:
        raise StageScopeError("stage/identity_tampered", "amendment superseded pointer differs")
    declared = tuple(amendment.get("authorized_paths", ()))
    if len(declared) != len(AMENDMENT_PATHS) or set(declared) != set(AMENDMENT_PATHS):
        raise StageScopeError("stage/identity_tampered", "amendment allowlist differs from the pin")

    i1_allowed = tuple(scope.get("allowed_paths") or ())
    if not i1_allowed:
        raise StageScopeError("stage/identity_unknown", "B6-I1 contract declares no allowed paths")

    _reject_later_artifacts(root)

    allowed = tuple(dict.fromkeys(i1_allowed + AMENDMENT_PATHS))
    return {
        "mode": "later",
        "requested": "auto",
        "stage": "B6-I1",
        "identity": {
            "scope_sha256": hashlib.sha256((root / I1_SCOPE).read_bytes()).hexdigest(),
            "contract_sha256": hashlib.sha256((root / I1_CONTRACT).read_bytes()).hexdigest(),
            "amendment_sha256": hashlib.sha256((root / AMENDMENT).read_bytes()).hexdigest(),
            "i0_merge": I0_MERGE,
            "i0_head": I0_HEAD,
            "superseded_blob": SUPERSEDED_BLOB,
        },
        "allowed": allowed,
        "i1_allowed": i1_allowed,
        "amendment": AMENDMENT_PATHS,
        "i0_merge": I0_MERGE,
    }


def resolve(root, requested: str = "auto") -> dict:
    root = pathlib.Path(root)
    if requested not in MODES:
        raise StageScopeError("stage/unknown_mode", requested)
    if requested == "i0":
        return {"mode": "i0", "requested": "i0", "stage": "B6-I0", "allowed": (),
                "i1_allowed": (), "amendment": (), "i0_merge": I0_MERGE}

    code, base = _git(root, "rev-parse", "origin/main")
    if code != 0:
        raise StageScopeError("stage/identity_missing", "origin/main is not resolvable")

    if (root / I2_REG).exists():
        return _resolve_i2(root, base)
    if (root / I1_SCOPE).exists():
        return _resolve_i1(root, base)
    if base != I0_MERGE:
        raise StageScopeError("stage/base_moved", base)
    raise StageScopeError("stage/identity_missing", "no stage identity is committed")
