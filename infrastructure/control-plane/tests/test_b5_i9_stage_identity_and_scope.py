"""B5-I9 stage identity and scope — frozen nodes for SI-01..SI-06 and BD-01..BD-05."""
from __future__ import annotations

import json
import pathlib
import sys
import subprocess
import tempfile

import pytest

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import b5_i9_gate as gate

ROOT = gate.repo_root()
DOCS = ROOT / gate.DOCS_DIR
BASE = "833f7d1b9f2dfec2986fb9516d0abde06bf23dae"
P0_COMMIT = "f6b5448fd2fc0785209327e0f31b6ce199bacdb5"
IMPL_BASE = "e81bef4335de5e222fb6647c602080a129dea543"

ALLOWED_CHANGES = (
    "docs/oce-golden-system/OCE_B5_I9_",
    "docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md",
    "infrastructure/control-plane/tests/test_b5_i9_",
    "infrastructure/control-plane/scripts/b5_i9_gate.py",
    "infrastructure/control-plane/scripts/b5_i9_",
    "infrastructure/control-plane/evidence/b5-i9/",
    ".github/workflows/b5-i9-",
)


def repository():
    return gate.Repo(ROOT)


def context():
    return gate.ctx(repository())


class TestStageIdentity:
    def test_stage_identity_matches_governing_clauses(self):
        packet = json.loads((ROOT / gate.PACKET_DIR / "factory-gate-packet.json")
                            .read_bytes().decode("utf-8"))
        identity = packet["identity"]
        assert len(identity["components"]) == 4
        assert len(identity["non_identities"]) == 3
        names = [c["name"] for c in identity["components"]]
        assert names == ["factory gate", "learning closure",
                         "B6 reusable-extraction contract", "operator hold"]
        for claim in identity["components"] + identity["non_identities"]:
            ok, detail = gate.resolve_citation(repository(), claim["citation"])
            assert ok, detail

    def test_base_sha_is_the_merged_main(self):
        gate.CHECKS["test_base_sha_is_the_merged_main"](context())
        assert repository().registry()["base_sha"] == BASE

    def test_deliverable_set_is_complete(self):
        for name in (gate.CONTRACT, gate.BOUNDARY, gate.REGISTRY, gate.ACCEPTANCE,
                     gate.FAILURE, gate.PLAN, gate.RATIFICATION, gate.LEDGER):
            assert (DOCS / name).exists(), name
        assert (ROOT / "infrastructure/control-plane/scripts/b5_i9_p0_validate.py").exists()
        packet = ROOT / gate.PACKET_DIR
        for name in ("factory-gate-packet.json", "classification-census.json",
                     "learning-closure.json", "handoff-contract.json",
                     "handoff-input-readiness.json", "provenance.json",
                     "operator-hold.json", "manifest.json", "validation.json"):
            assert (packet / name).exists(), name

    def test_claims_resolve_in_their_sources(self):
        resolved = 0
        for row in repository().registry()["requirements"]:
            ok, detail = gate.resolve_citation(repository(), row["citation"])
            assert ok, "{}: {}".format(row["id"], detail)
            resolved += 1
        assert resolved == 51

    def test_no_implementation_artifact_at_p0(self):
        """Historical fact: the P0 commit created no test, source or workflow artifact."""
        proc = subprocess.run(["git", "show", "--name-only", "--pretty=format:", P0_COMMIT],
                              cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            pytest.skip("P0 commit not present in this clone; CI validates it with fetch-depth 0")
        paths = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        assert len(paths) == 8, paths
        assert not [p for p in paths if "test_b5_i9" in p]
        assert not [p for p in paths if p.startswith(".github/workflows/")]


class TestLocks:
    def test_merge_authorized_false(self):
        locks = repository().registry()["locks"]
        assert locks["merge_authorized"] is False
        hold = json.loads((ROOT / gate.PACKET_DIR / "operator-hold.json")
                          .read_bytes().decode("utf-8"))
        assert hold["merge_authorized"] is False
        assert hold["ratification_authorized"] is False

    def test_no_capital_or_execution_authority(self):
        locks = repository().registry()["locks"]
        assert locks["capital_authority"] == "none"
        assert locks["cost_usd"] == 0
        assert locks["cloud_mutations"] == 0
        contract = json.loads((ROOT / gate.PACKET_DIR / "handoff-contract.json")
                              .read_bytes().decode("utf-8"))
        owners = contract["authority_owners"]
        for name in ("spend", "execution", "broker"):
            assert owners[name] is None, name
        body = json.dumps(contract)
        assert "broker" not in body.replace('"broker"', "")
        assert "capital.authority = none" in (DOCS / gate.CONTRACT).read_text(encoding="utf-8")

    def test_changed_file_boundary(self):
        proc = subprocess.run(["git", "diff", "--name-only", IMPL_BASE + "..HEAD"],
                              cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            pytest.skip("implementation base commit not present in this clone")
        changed = [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]
        assert changed, "no change detected against the merged main"
        offenders = [p for p in changed if not p.startswith(ALLOWED_CHANGES)]
        assert not offenders, offenders

    def test_no_scratch_residue(self):
        scratch = []
        for pattern in (".b5i9*", "b5_i9_scratch*", "b5-i9-scratch*"):
            scratch.extend(ROOT.rglob(pattern))
        assert not scratch, scratch
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "packet"
            gate.emit(repository(), target)
            assert target.exists()
        assert not target.exists(), "temporary packet directory survived its context"


class TestLedgerAppend:
    def test_ledger_prefix_unchanged_and_appended(self):
        raw = (DOCS / gate.LEDGER).read_bytes()
        body = gate.normalize(raw)
        assert gate.sha256(body[:gate.LEDGER_PREFIX_LEN]) == gate.LEDGER_PREFIX_SHA
        assert len(body) > gate.LEDGER_PREFIX_LEN
        assert "## 22. B5-I9 P0" in body.decode("utf-8")
        assert b"## 23. B5-I9 implementation" in body
        tail = body[body.rindex(b"## 23."):].decode("utf-8")
        assert "BOOK_6_AUTHORIZED = false" in tail
