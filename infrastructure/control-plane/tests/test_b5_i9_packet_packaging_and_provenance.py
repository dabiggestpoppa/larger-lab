"""B5-I9 packet packaging, provenance and reproducibility — PK-01..PK-09."""
from __future__ import annotations

import ast
import json
import pathlib
import tempfile

import pytest

from oce_control import b5_i9_gate as gate

ROOT = gate.repo_root()
PACKET = ROOT / gate.PACKET_DIR
SCRIPTS = ROOT / "infrastructure/control-plane/scripts"

STDLIB_ALLOWED = {
    "__future__", "argparse", "ast", "copy", "dataclasses", "hashlib", "json", "os",
    "pathlib", "re", "shutil", "subprocess", "sys", "tempfile", "textwrap", "typing",
    "xml", "collections", "itertools", "difflib", "enum", "io", "unicodedata",
}
NETWORK_MODULES = {"socket", "ssl", "urllib", "http", "requests", "httpx", "ftplib",
                   "smtplib", "telnetlib", "asyncio"}


def manifest():
    return json.loads((PACKET / "manifest.json").read_bytes().decode("utf-8"))


def imports_of(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


class TestProvenance:
    def test_every_artifact_records_identity(self):
        rows = manifest()["artifacts"]
        assert len(rows) == 10
        for row in rows:
            assert row["document_id"], row["path"]
            assert row["version"] == gate.VERSION
            assert row["stage"] == gate.STAGE
            assert row["status"] == gate.STATUS
            body = json.loads((PACKET / row["path"]).read_bytes().decode("utf-8"))
            assert body["document_id"] == row["document_id"]

    def test_manifest_rows_recomputed_from_bytes(self):
        for row in manifest()["artifacts"]:
            raw = (PACKET / row["path"]).read_bytes()
            body = raw.replace(b"\r\n", b"\n")
            assert gate.sha256(body) == row["sha256"], row["path"]
            assert len(body) == row["size_bytes"], row["path"]
            assert row["size_bytes"] <= gate.MAX_ARTIFACT_BYTES

    def test_generation_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            gate.emit(gate.Repo(ROOT), pathlib.Path(first))
            gate.emit(gate.Repo(ROOT), pathlib.Path(second))
            names = sorted(p.name for p in pathlib.Path(first).iterdir())
            assert names == sorted(p.name for p in pathlib.Path(second).iterdir())
            for name in names:
                left = (pathlib.Path(first) / name).read_bytes().replace(b"\r\n", b"\n")
                right = (pathlib.Path(second) / name).read_bytes().replace(b"\r\n", b"\n")
                assert left == right, name

    def test_second_run_matches_first(self):
        digests = []
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            for target in (one, two):
                gate.emit(gate.Repo(ROOT), pathlib.Path(target))
                rows = gate.manifest_rows(target)
                digests.append(gate.sha256("".join(
                    "{}{}{}".format(r["path"], r["sha256"], r["size_bytes"]) for r in rows).encode()))
        assert digests[0] == digests[1]
        assert gate.diff_packet(gate.Repo(ROOT), PACKET) == []

    def test_artifact_size_rule_enforced(self):
        for row in manifest()["artifacts"]:
            assert row["size_bytes"] <= gate.MAX_ARTIFACT_BYTES
        oversized = {"big": "x" * (gate.MAX_ARTIFACT_BYTES + 1)}
        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(gate.GateViolation) as exc:
                gate.write_packet(pathlib.Path(tmp), oversized)
            assert exc.value.check == "test_artifact_size_rule_enforced"

    def test_no_secret_material(self):
        for path in sorted(PACKET.iterdir()):
            if not path.is_file():
                continue
            body = path.read_bytes().decode("utf-8", "replace")
            for pattern in gate.SECRET_PATTERNS:
                assert not pattern.search(body), path.name
        for name in ("b5_i9_gate.py",):
            body = (ROOT / "infrastructure/control-plane/src/oce_control" / name).read_text(
                encoding="utf-8")
            for pattern in gate.SECRET_PATTERNS:
                assert not pattern.search(body), name

    def test_validator_stdlib_only_and_offline(self):
        targets = [
            ROOT / "infrastructure/control-plane/src/oce_control/b5_i9_gate.py",
            SCRIPTS / "b5_i9_p0_validate.py",
            SCRIPTS / "b5_i9_factory_gate.py",
            SCRIPTS / "b5_i9_mutation_battery.py",
        ]
        for path in targets:
            names = imports_of(path)
            external = {n for n in names if n not in STDLIB_ALLOWED and n != "oce_control"}
            assert not external, (path.name, external)
            assert not (names & NETWORK_MODULES), (path.name, names & NETWORK_MODULES)
            body = path.read_text(encoding="utf-8")
            assert "import requests" not in body
            assert "urlopen" not in body

    def test_validator_performs_no_network_access(self):
        validator = SCRIPTS / "b5_i9_p0_validate.py"
        tree = ast.parse(validator.read_text(encoding="utf-8"))
        assert not [n for n in ast.walk(tree) if isinstance(n, ast.Import)
                    and n.names[0].name.split(".")[0] in NETWORK_MODULES]
        body = validator.read_text(encoding="utf-8")
        for token in ("http://", "https://", "socket.", "urlopen", "fetch("):
            assert token not in body, token
        provenance = json.loads((PACKET / "provenance.json").read_bytes().decode("utf-8"))
        assert provenance["network_access"] is False
        assert provenance["wall_clock_values"] is False
