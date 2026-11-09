"""B6-I2 archive safety: traversal, symlink, absolute, malformed, oversize, digest refusals."""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.templates import archive, refusals, skeleton  # noqa: E402


def manifest(entries, template: str = "probe") -> dict:
    return {"schema": archive.SCHEMA, "template": template, "version": archive.VERSION,
            "payload_digest": archive.payload_digest(entries), "entries": entries}


def entry(path: str, content: str = "x\n", mode: str = "file") -> dict:
    return {"path": path, "content": content, "mode": mode}


def code(fn, *args):
    with pytest.raises(refusals.Refused) as exc:
        fn(*args)
    return exc.value


def test_path_traversal_refused(tmp_path: pathlib.Path) -> None:
    doc = manifest([entry("../escape.txt")])
    err = code(archive.install, doc, tmp_path / "dest")
    assert err.code == "REFUSED_PATH_TRAVERSAL"
    assert not (tmp_path / "escape.txt").exists()


def test_symlink_escape_refused(tmp_path: pathlib.Path) -> None:
    err = code(archive.install, manifest([entry("link", "/etc/passwd", "symlink")]),
               tmp_path / "dest")
    assert err.code == "REFUSED_SYMLINK_ESCAPE"
    assert not (tmp_path / "dest").exists()


def test_malformed_archive_refused(tmp_path: pathlib.Path) -> None:
    for bad in ({}, {"schema": "other"}, {"schema": archive.SCHEMA, "entries": "no"},
                [], "archive"):
        assert code(archive.validate, bad).code == "REFUSED_MALFORMED_ARCHIVE"
    assert not (tmp_path / "dest").exists()


def test_absolute_entry_refused(tmp_path: pathlib.Path) -> None:
    for bad in ("/etc/passwd", "\\windows\\x", "C:/tmp/x"):
        assert code(archive.validate, manifest([entry(bad)])).code == "REFUSED_ABSOLUTE_PATH"


def test_oversized_archive_refused(tmp_path: pathlib.Path) -> None:
    big = "x" * (refusals.MAX_ENTRY_BYTES + 1)
    err = code(archive.install, manifest([entry("big.txt", big)]), tmp_path / "dest")
    assert err.code == "REFUSED_OVERSIZE"
    many = [entry(f"f{i}.txt") for i in range(refusals.MAX_ENTRIES + 1)]
    assert code(archive.validate, manifest(many)).code == "REFUSED_OVERSIZE"


def test_digest_mismatch_refused(tmp_path: pathlib.Path) -> None:
    doc = manifest([entry("app.txt")])
    doc["payload_digest"] = "0" * 64
    assert code(archive.validate, doc).code == "REFUSED_DIGEST_MISMATCH"
    good = skeleton.manifest()
    assert archive.install(good, tmp_path / "dest")["installed"] == 6
    assert code(archive.install, good, tmp_path / "dest").code == "REFUSED_DIRTY_INPUT"
