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
I2_HEAD = "9bf76df45dca676ae7cafc4877f117a7dd64c3d2"
I2_MERGE = "018b164f249bbf075334d5d03ad37e80dcbbede0"
I3_SCOPE = f"{DOCS}/OCE_BLOCK_06_I3_SCOPE_DERIVATION_v1.0.json"
I3_CONTRACT = f"{DOCS}/OCE_BLOCK_06_I3_IMPLEMENTATION_CONTRACT_v1.0.json"
I3_REG = f"{DOCS}/OCE_BLOCK_06_I3_STAGE_SCOPE_REGISTRATION_v1.0.json"
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
    # The B6-I0 stage-contract suite must recognise the later-stage mode; adapting that one
    # assertion is part of admitting the B6-I2 identity without weakening the strict I0 replay.
    "infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
    ".github/workflows/block-06-i0-validation.yml",
    ".github/workflows/block-06-i1-validation.yml",
    ".github/workflows/block-06-i2-validation.yml",
    ".github/workflows/block-06-i2-paired-comparison.yml",
)
# Pinned: the surfaces the B6-I3 registration itself is allowed to author or amend.
I3_PINNED = (
    I3_REG,
    I3_SCOPE,
    I3_CONTRACT,
    f"{DOCS}/OCE_BLOCK_06_I3_MANIFEST_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I3_PAIRED_COMPARISON_CONTRACT_v1.0.json",
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    "infrastructure/control-plane/scripts/block_06_i2_validate.py",
    "infrastructure/control-plane/scripts/block_06_i2_stage_controls.py",
    "infrastructure/control-plane/scripts/block_06_i3_validate.py",
    "infrastructure/control-plane/scripts/block_06_i3_generate.py",
    "infrastructure/control-plane/scripts/block_06_i3_mutation_battery.py",
    "infrastructure/control-plane/scripts/block_06_i3_stage_controls.py",
    "infrastructure/control-plane/scripts/block_06_i3_paired.py",
    ".github/workflows/block-06-i3-validation.yml",
    ".github/workflows/block-06-i3-paired-comparison.yml",
    ".github/workflows/block-06-i2-validation.yml",
)


I3_MERGE = "f0bd9bdd3f776b33d3b70b5b441966e2c80e1f14"
I3_HEAD = "eda33f43e6d058891a8009e98e968c9f00252220"
I4_SCOPE = f"{DOCS}/OCE_BLOCK_06_I4_SCOPE_DERIVATION_v1.0.json"
I4_CONTRACT = f"{DOCS}/OCE_BLOCK_06_I4_IMPLEMENTATION_CONTRACT_v1.0.json"
I4_REG = f"{DOCS}/OCE_BLOCK_06_I4_STAGE_SCOPE_REGISTRATION_v1.0.json"
I3_PREFIXES = (
    "oce/operator/",
    f"{DOCS}/OCE_BLOCK_06_I3_",
    "infrastructure/control-plane/scripts/block_06_i3_",
    "infrastructure/control-plane/tests/test_block_06_i3_",
    "infrastructure/control-plane/tests/stage_scope/test_block_06_i3_",
    ".github/workflows/block-06-i3-validation.yml",
    ".github/workflows/block-06-i3-paired-comparison.yml",
)
# Pinned: the surfaces the B6-I4 registration itself is allowed to author or amend.
I4_PINNED = (
    I4_REG,
    I4_SCOPE,
    I4_CONTRACT,
    f"{DOCS}/OCE_BLOCK_06_I4_MANIFEST_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I4_PAIRED_COMPARISON_CONTRACT_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I4_COMPATIBILITY_MATRIX_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I4_FAILURE_AND_THREAT_PROOFS_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I4_OPERATOR_SURFACE_CONTRACT_v1.0.json",
    f"{DOCS}/OCE_BLOCK_06_I4_REQUIREMENT_TEST_REGISTRY_v1.0.json",
    "infrastructure/control-plane/scripts/block_06_stage_scope.py",
    "infrastructure/control-plane/scripts/block_06_i0_validate.py",
    "infrastructure/control-plane/scripts/block_06_i1_validate.py",
    "infrastructure/control-plane/scripts/block_06_i4_validate.py",
    "infrastructure/control-plane/scripts/block_06_i4_generate.py",
    "infrastructure/control-plane/scripts/block_06_i4_mutation_battery.py",
    "infrastructure/control-plane/scripts/block_06_i4_stage_controls.py",
    "infrastructure/control-plane/scripts/block_06_i4_paired.py",
    ".github/workflows/block-06-i4-validation.yml",
    ".github/workflows/block-06-i4-paired-comparison.yml",
)
I4_PREFIXES = (
    "oce/operator/",
    "oce/services/",
    f"{DOCS}/OCE_BLOCK_06_I4_",
    "infrastructure/control-plane/scripts/block_06_i4_",
    "infrastructure/control-plane/tests/test_block_06_i4_",
    "infrastructure/control-plane/tests/stage_scope/test_block_06_i4_",
    ".github/workflows/block-06-i4-validation.yml",
    ".github/workflows/block-06-i4-paired-comparison.yml",
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


def _reject_later_artifacts(root: pathlib.Path, start: int = 3) -> None:
    code, tree = _git(root, "ls-tree", "-r", "--name-only", "HEAD")
    if code != 0:
        raise StageScopeError("stage/identity_missing", "HEAD tree is unreadable")
    stages = tuple(f"I{i}" for i in range(start, 10))
    later = [p for p in tree.splitlines()
             if any(f"OCE_BLOCK_06_{stage}_" in p for stage in stages)]
    if later:
        raise StageScopeError("stage/later_stage_absent", later)


def _resolve_i2(root: pathlib.Path, base: str) -> dict:
    if base != I1_MERGE:
        raise StageScopeError("stage/base_moved", base)
    code, _ = _git(root, "merge-base", "--is-ancestor", I1_MERGE, "HEAD")
    if code != 0:
        raise StageScopeError("stage/base_moved", "HEAD does not descend from the B6-I1 merge")
    for rel in (I2_REG, I2_SCOPE, I2_CONTRACT, I1_SCOPE, I1_CONTRACT, AMENDMENT):
        _require_identity_file(root, rel)
    amendment = json.loads((root / AMENDMENT).read_text(encoding="utf-8"))
    if amendment.get("amendment_id") != AMENDMENT_ID or amendment.get("status") != "FROZEN":
        raise StageScopeError("stage/identity_unknown", amendment.get("amendment_id"))
    declared = tuple(amendment.get("authorized_paths", ()))
    if len(declared) != len(AMENDMENT_PATHS) or set(declared) != set(AMENDMENT_PATHS):
        raise StageScopeError("stage/identity_tampered",
                              "amendment allowlist differs from the pin")
    i1_identity = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    i1_contract_identity = json.loads((root / I1_CONTRACT).read_text(encoding="utf-8"))
    if i1_identity.get("stage") not in KNOWN_LATER_STAGES:
        raise StageScopeError("stage/identity_unknown", i1_identity.get("stage"))
    if i1_contract_identity.get("stage") != "B6-I1" or i1_contract_identity.get("status") != "FROZEN":
        raise StageScopeError("stage/identity_unknown", i1_contract_identity.get("status"))
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
    # Prior-packet byte immutability is enforced by the stage validators themselves
    # (boundary/i0_packet_frozen and I1's prior_packets_frozen), so identity resolution does not
    # duplicate it as a tamper error.
    _reject_later_artifacts(root)
    i1_scope = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    i1_owned = tuple(i1_scope.get("allowed_paths") or ())
    # The stage chain is cumulative: the B6-I2 identity admits the B6-I1 surface set unchanged and
    # adds only the B6-I2 paths proven by its contract.
    allowed = tuple(dict.fromkeys(i1_owned + AMENDMENT_PATHS + prefixes + I2_PINNED))
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
        "amendment": tuple(dict.fromkeys(AMENDMENT_PATHS + I2_PINNED)),
        "i0_merge": I1_MERGE,
    }


def _resolve_i3(root: pathlib.Path, base: str) -> dict:
    if base != I2_MERGE:
        raise StageScopeError("stage/base_moved", base)
    code, _ = _git(root, "merge-base", "--is-ancestor", I2_MERGE, "HEAD")
    if code != 0:
        raise StageScopeError("stage/base_moved", "HEAD does not descend from the B6-I2 merge")
    for rel in (I3_REG, I3_SCOPE, I3_CONTRACT, I2_REG, I2_SCOPE, I1_SCOPE, I1_CONTRACT,
                AMENDMENT):
        _require_identity_file(root, rel)
    amendment = json.loads((root / AMENDMENT).read_text(encoding="utf-8"))
    if amendment.get("amendment_id") != AMENDMENT_ID or amendment.get("status") != "FROZEN":
        raise StageScopeError("stage/identity_unknown", amendment.get("amendment_id"))
    declared = tuple(amendment.get("authorized_paths", ()))
    if len(declared) != len(AMENDMENT_PATHS) or set(declared) != set(AMENDMENT_PATHS):
        raise StageScopeError("stage/identity_tampered",
                              "amendment allowlist differs from the pin")
    i1_identity = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    if i1_identity.get("stage") not in KNOWN_LATER_STAGES:
        raise StageScopeError("stage/identity_unknown", i1_identity.get("stage"))
    i2_registration = json.loads((root / I2_REG).read_text(encoding="utf-8"))
    i2_scope = json.loads((root / I2_SCOPE).read_text(encoding="utf-8"))
    if (i2_registration.get("document_id") != "OCE-B6-I2-STAGE-SCOPE-REGISTRATION-001"
            or i2_registration.get("status") != "FROZEN"):
        raise StageScopeError("stage/identity_unknown", i2_registration.get("status"))
    if i2_scope.get("stage") != "B6-I2":
        raise StageScopeError("stage/identity_unknown", i2_scope.get("stage"))
    registration = json.loads((root / I3_REG).read_text(encoding="utf-8"))
    scope = json.loads((root / I3_SCOPE).read_text(encoding="utf-8"))
    contract = json.loads((root / I3_CONTRACT).read_text(encoding="utf-8"))
    if (registration.get("document_id") != "OCE-B6-I3-STAGE-SCOPE-REGISTRATION-001"
            or registration.get("status") != "FROZEN"
            or registration.get("frozen_before_results") is not True):
        raise StageScopeError("stage/identity_unknown", registration.get("document_id"))
    if scope.get("stage") != "B6-I3" or contract.get("stage") != "B6-I3":
        raise StageScopeError("stage/identity_unknown", (scope.get("stage"),
                                                         contract.get("stage")))
    if contract.get("status") != "FROZEN" or contract.get("frozen_before_results") is not True:
        raise StageScopeError("stage/identity_unknown", contract.get("status"))
    prior = registration.get("prior_stages") or {}
    if (prior.get("B6-I0", {}).get("head") != I0_HEAD
            or prior.get("B6-I1", {}).get("head") != I1_HEAD
            or prior.get("B6-I2", {}).get("head") != I2_HEAD):
        raise StageScopeError("stage/identity_tampered", prior)
    this = registration.get("this_stage") or {}
    if this.get("base") != I2_MERGE or this.get("base_tree") != scope.get("base_tree"):
        raise StageScopeError("stage/identity_tampered", this.get("base"))
    prefixes = tuple(this.get("allowed_prefixes") or ())
    if not prefixes or "oce/operator/" not in prefixes:
        raise StageScopeError("stage/identity_unknown", "B6-I3 registration declares no authority")
    _reject_later_artifacts(root, start=4)
    i1_scope = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    i1_owned = tuple(i1_scope.get("allowed_paths") or ())
    # The stage chain is cumulative: I1 law, the frozen I0 amendment, the I2 surfaces and pins,
    # then the I3 registration and pins. No later-stage path is ever inherited.
    allowed = tuple(dict.fromkeys(i1_owned + AMENDMENT_PATHS
                                  + tuple(i2_registration["this_stage"]["allowed_prefixes"])
                                  + I2_PINNED + prefixes + I3_PINNED))
    oce_authority = tuple(dict.fromkeys(i1_owned + tuple(p for p in allowed
                                                         if p.startswith("oce/"))))
    return {
        "mode": "i3",
        "requested": "auto",
        "stage": "B6-I3",
        "identity": {
            "registration_sha256": hashlib.sha256((root / I3_REG).read_bytes()).hexdigest(),
            "scope_sha256": hashlib.sha256((root / I3_SCOPE).read_bytes()).hexdigest(),
            "contract_sha256": hashlib.sha256((root / I3_CONTRACT).read_bytes()).hexdigest(),
            "i0_head": I0_HEAD,
            "i1_head": I1_HEAD,
            "i2_head": I2_HEAD,
            "i2_merge": I2_MERGE,
        },
        "allowed": allowed,
        "i1_allowed": oce_authority,
        "amendment": tuple(dict.fromkeys(AMENDMENT_PATHS + I2_PINNED + I3_PINNED)),
        "i0_merge": I2_MERGE,
    }


def _resolve_i4(root: pathlib.Path, base: str) -> dict:
    if base != I3_MERGE:
        raise StageScopeError("stage/base_moved", base)
    code, _ = _git(root, "merge-base", "--is-ancestor", I3_MERGE, "HEAD")
    if code != 0:
        raise StageScopeError("stage/base_moved", "HEAD does not descend from the B6-I3 merge")
    for rel in (I4_REG, I4_SCOPE, I4_CONTRACT, I3_REG, I3_SCOPE, I3_CONTRACT, I2_REG, I2_SCOPE,
                I1_SCOPE, I1_CONTRACT, AMENDMENT):
        _require_identity_file(root, rel)
    amendment = json.loads((root / AMENDMENT).read_text(encoding="utf-8"))
    if amendment.get("amendment_id") != AMENDMENT_ID or amendment.get("status") != "FROZEN":
        raise StageScopeError("stage/identity_unknown", amendment.get("amendment_id"))
    declared = tuple(amendment.get("authorized_paths", ()))
    if len(declared) != len(AMENDMENT_PATHS) or set(declared) != set(AMENDMENT_PATHS):
        raise StageScopeError("stage/identity_tampered", "amendment allowlist differs from the pin")
    i3_registration = json.loads((root / I3_REG).read_text(encoding="utf-8"))
    i3_scope = json.loads((root / I3_SCOPE).read_text(encoding="utf-8"))
    if (i3_registration.get("document_id") != "OCE-B6-I3-STAGE-SCOPE-REGISTRATION-001"
            or i3_registration.get("status") != "FROZEN"):
        raise StageScopeError("stage/identity_unknown", i3_registration.get("status"))
    if i3_scope.get("stage") != "B6-I3":
        raise StageScopeError("stage/identity_unknown", i3_scope.get("stage"))
    registration = json.loads((root / I4_REG).read_text(encoding="utf-8"))
    scope = json.loads((root / I4_SCOPE).read_text(encoding="utf-8"))
    contract = json.loads((root / I4_CONTRACT).read_text(encoding="utf-8"))
    if (registration.get("document_id") != "OCE-B6-I4-STAGE-SCOPE-REGISTRATION-001"
            or registration.get("status") != "FROZEN"
            or registration.get("frozen_before_results") is not True):
        raise StageScopeError("stage/identity_unknown", registration.get("document_id"))
    if scope.get("stage") != "B6-I4" or contract.get("stage") != "B6-I4":
        raise StageScopeError("stage/identity_unknown", (scope.get("stage"),
                                                         contract.get("stage")))
    if contract.get("status") != "FROZEN" or contract.get("frozen_before_results") is not True:
        raise StageScopeError("stage/identity_unknown", contract.get("status"))
    prior = registration.get("prior_stages") or {}
    if (prior.get("B6-I0", {}).get("head") != I0_HEAD
            or prior.get("B6-I1", {}).get("head") != I1_HEAD
            or prior.get("B6-I2", {}).get("head") != I2_HEAD
            or prior.get("B6-I3", {}).get("head") != I3_HEAD):
        raise StageScopeError("stage/identity_tampered", prior)
    this = registration.get("this_stage") or {}
    if this.get("base") != I3_MERGE or this.get("base_tree") != scope.get("base_tree"):
        raise StageScopeError("stage/identity_tampered", this.get("base"))
    prefixes = tuple(this.get("allowed_prefixes") or ())
    if "oce/services/" not in prefixes or "oce/operator/" not in prefixes:
        raise StageScopeError("stage/identity_unknown", "B6-I4 registration declares no authority")
    _reject_later_artifacts(root, start=5)
    i1_scope = json.loads((root / I1_SCOPE).read_text(encoding="utf-8"))
    i1_owned = tuple(i1_scope.get("allowed_paths") or ())
    i2_prefixes = tuple(json.loads((root / I2_REG).read_text(encoding="utf-8"))
                        ["this_stage"]["allowed_prefixes"])
    i3_prefixes = tuple(i3_registration["this_stage"]["allowed_prefixes"])
    allowed = tuple(dict.fromkeys(i1_owned + AMENDMENT_PATHS + i2_prefixes + I2_PINNED
                                  + i3_prefixes + I3_PINNED + prefixes + I4_PINNED))
    oce_authority = tuple(dict.fromkeys(i1_owned + tuple(p for p in allowed
                                                         if p.startswith("oce/"))))
    return {
        "mode": "i4",
        "requested": "auto",
        "stage": "B6-I4",
        "identity": {
            "registration_sha256": hashlib.sha256((root / I4_REG).read_bytes()).hexdigest(),
            "scope_sha256": hashlib.sha256((root / I4_SCOPE).read_bytes()).hexdigest(),
            "contract_sha256": hashlib.sha256((root / I4_CONTRACT).read_bytes()).hexdigest(),
            "i0_head": I0_HEAD,
            "i1_head": I1_HEAD,
            "i2_head": I2_HEAD,
            "i3_head": I3_HEAD,
            "i3_merge": I3_MERGE,
        },
        "allowed": allowed,
        "i1_allowed": oce_authority,
        "amendment": tuple(dict.fromkeys(AMENDMENT_PATHS + I2_PINNED + I3_PINNED + I4_PINNED)),
        "i0_merge": I3_MERGE,
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

    if (root / I4_REG).exists():
        return _resolve_i4(root, base)
    if (root / I3_REG).exists():
        return _resolve_i3(root, base)
    if (root / I2_REG).exists():
        return _resolve_i2(root, base)
    if (root / I1_SCOPE).exists():
        return _resolve_i1(root, base)
    if base != I0_MERGE:
        raise StageScopeError("stage/base_moved", base)
    raise StageScopeError("stage/identity_missing", "no stage identity is committed")
