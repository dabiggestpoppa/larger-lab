"""B5-I9 stage identity and scope — frozen nodes for SI-01..SI-06 and BD-01..BD-05."""
from __future__ import annotations

import hashlib
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

# --------------------------------------------------------- boundary law (B5-I9-AMEND-001)
# The original law inspected IMPL_BASE..HEAD, and HEAD moves with every future branch, so it
# demanded that every later stage name its paths with B5-I9 prefixes. The amended node proves
# the frozen historical range instead, and guards the protected B5-I9 surfaces against any
# change no pinned amendment names.
FROZEN_IMPL_BASE = "e81bef4335de5e222fb6647c602080a129dea543"
FROZEN_IMPL_HEAD = "9db35aac5c1d9cfbdc5bd902b74c2bb09bfd9d3c"
FUTURE_BASE = "a794a9af80ae8deddacf2991de17b7d71e445756"
AMENDMENT_ID = "B5-I9-AMEND-001"
AMENDMENT_DOC = ("docs/oce-golden-system/"
                 "OCE_B5_I9_AMENDMENT_001_FUTURE_STAGE_BOUNDARY_COMPATIBILITY_v1.0.md")
AMENDMENT_SHA256 = "9ebfbd659f76c4a1fd2605b6f8db40774dc4d2eeb1e191a433444da378430a71"
HISTORICAL_PATH_FLOOR = 20
PROTECTED_PATH_FLOOR = 31
BACKSLASH = chr(92)


def _git_text(*args):
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


def _diff_paths(base, head):
    proc = _git_text("diff", "--name-only", base + ".." + head)
    assert proc.returncode == 0, proc.stderr
    return [line.strip().replace(BACKSLASH, "/") for line in proc.stdout.splitlines()
            if line.strip()]


def _amendment():
    """The pinned amendment. A fake filename or an edited body is refused."""
    path = ROOT / AMENDMENT_DOC
    assert path.exists(), "amendment document missing: " + AMENDMENT_DOC
    body = path.read_bytes().replace(bytes([13, 10]), bytes([10]))
    assert hashlib.sha256(body).hexdigest() == AMENDMENT_SHA256, "amendment body changed"
    text = body.decode("utf-8")
    assert AMENDMENT_ID in text, "amendment id absent"
    blob = text.split("```json", 1)[1].split("```", 1)[0]
    doc = json.loads(blob)
    assert doc["amendment_id"] == AMENDMENT_ID, doc
    assert doc["node"] == "TestLocks::test_changed_file_boundary", doc
    assert doc["no_waiver"] is True and doc["no_retroactive_rewrite"] is True, doc
    return doc


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
        """B5I9-BD-04 as amended by B5-I9-AMEND-001.

        A. the frozen B5-I9 branch changed only its own authorized paths;
        B. a later branch may add its own paths, but no protected B5-I9 surface changes
           unless the pinned amendment names that exact path.
        """
        for rev in (FROZEN_IMPL_BASE, FROZEN_IMPL_HEAD, FUTURE_BASE):
            assert _git_text("cat-file", "-e", rev + "^{commit}").returncode == 0, rev

        historical = _diff_paths(FROZEN_IMPL_BASE, FROZEN_IMPL_HEAD)
        assert historical, "no historical B5-I9 change detected"
        assert len(historical) >= HISTORICAL_PATH_FLOOR, historical
        historical_outside = [p for p in historical if not p.startswith(ALLOWED_CHANGES)]
        assert not historical_outside, historical_outside

        tree = _git_text("ls-tree", "-r", "--name-only", FROZEN_IMPL_HEAD)
        assert tree.returncode == 0, tree.stderr
        protected = [p for p in tree.stdout.splitlines() if p.startswith(ALLOWED_CHANGES)]
        assert len(protected) >= PROTECTED_PATH_FLOOR, len(protected)
        assert any(p.startswith("infrastructure/control-plane/evidence/b5-i9/") for p in protected)
        assert any(p.endswith("b5-i9-factory-gate-validation.yml") for p in protected)
        assert any(p.endswith("b5_i9_gate.py") for p in protected)
        protected_set = set(protected)

        future = _diff_paths(FUTURE_BASE, "HEAD")
        anomalies = [p for p in future
                     if not p or p.startswith("/") or BACKSLASH in p or ".." in p.split("/")]
        assert not anomalies, anomalies

        doc = _amendment()
        authorized = set(doc["authorized_paths"])
        assert authorized, "amendment authorizes nothing"
        claimable = protected_set | {AMENDMENT_DOC}
        assert authorized <= claimable, sorted(authorized - claimable)

        touched = [p for p in future if p in protected_set]
        unauthorized = [p for p in touched if p not in authorized]
        assert not unauthorized, unauthorized

        added = [p for p in future if p.startswith(ALLOWED_CHANGES)
                 and p not in protected_set and p not in authorized]
        assert not added, added

        unexercised = sorted(p for p in authorized if p not in future)
        assert not unexercised, unexercised

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
