"""B6-I2 evidence and cleanup proofs: manifest recomputation, no residue, prior stages frozen."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I2_"
I1_HEAD = "96e3b81714321f4eea7abcb300ef471e93be0962"


def load(name: str) -> dict:
    return json.loads((DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                          text=True).stdout.strip()


def test_manifest_hashes_recompute() -> None:
    manifest = load("MANIFEST_v1.0.json")
    assert manifest["status"] == "FROZEN"
    assert manifest["base_sha"] == "4496d548078660efd7ad4f93e7fff461d34ea538"
    assert manifest["totals"]["artifacts"] == 9
    rows = manifest["artifacts"] + manifest["code"]
    assert len(rows) >= 15
    for row in rows:
        path = ROOT / row["path"]
        assert path.is_file(), row["path"]
        data = path.read_bytes()
        assert row["sha256"] == hashlib.sha256(data).hexdigest(), row["path"]
        assert row["bytes"] == len(data), row["path"]
    assert manifest["verification"] == {"independent": True, "excludes_manifest": True}
    assert manifest["locks"]["MERGE_AUTHORIZED"] is False


def test_cleanup_no_scratch_residue() -> None:
    residue = sorted(str(path.relative_to(ROOT)) for path in ROOT.rglob(".b6i2-*"))
    assert residue == []
    assert git("status", "--porcelain", "--untracked-files=all") == ""
    for name in ("SCOPE_DERIVATION", "IMPLEMENTATION_CONTRACT", "MANIFEST"):
        raw = (DOCS / f"{PREFIX}{name}_v1.0.json").read_bytes()
        assert b"\r\n" not in raw and raw.endswith(b"\n")


def test_prior_stage_artifacts_unchanged() -> None:
    for rel in ("infrastructure/control-plane/tests/test_block_06_i0_stage_contract.py",
                "infrastructure/control-plane/tests/test_block_06_i1_authority_and_boundary.py"):
        code = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet",
                               "4496d548078660efd7ad4f93e7fff461d34ea538..HEAD", "--", rel])
        assert code.returncode == 0, rel
    for prefix in ("OCE_BLOCK_06_I0_", "OCE_BLOCK_06_I1_", "OCE_BLOCK_06_P0_"):
        changed = [line for line in git("diff", "--name-only", f"{I1_HEAD}..HEAD", "--",
                                        "docs/oce-golden-system").splitlines()
                   if prefix in line]
        assert changed == [], changed
    assert git("rev-parse", f"{I1_HEAD}:docs/oce-golden-system/"
               "OCE_BLOCK_06_I1_IMPLEMENTATION_CONTRACT_v1.0.json") != ""
    assert git("merge-base", "--is-ancestor", I1_HEAD, "HEAD") == ""
