"""B6-I2 template proofs: deterministic skeleton, start, manifest refusal, provenance."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from oce.templates import archive, refusals, skeleton  # noqa: E402


def write(dest: pathlib.Path, name: str = "app") -> dict:
    return skeleton.write(dest, name)


def test_generated_app_starts_locally(tmp_path: pathlib.Path) -> None:
    dest = tmp_path / "fresh"
    write(dest)
    assert not [p for p in dest.rglob("*.pyc")]
    first = skeleton.start(dest)
    second = skeleton.start(dest)
    for record in (first, second):
        assert record["started"] is True
        assert record["transport"] == "subprocess"
        assert record["network"] is False
        assert record["readiness"] == "READY app"
        assert record["shutdown"] == "STOPPED"
        assert record["exit_code"] == 0
        assert record["artifacts"] == sorted(skeleton.FILES)
        assert len(record["digest"]) == 64
    assert first["digest"] == second["digest"]
    entry = (dest / "app" / "__main__.py").read_text(encoding="utf-8")
    for forbidden in ("socket", "urllib", "http.client", "requests", "aiohttp"):
        assert forbidden not in entry
    assert not [p for p in dest.rglob("*.pyc")]


def test_template_declares_inherited_versions(tmp_path: pathlib.Path) -> None:
    write(tmp_path / "app")
    app = json.loads((tmp_path / "app" / "app.json").read_text(encoding="utf-8"))
    deploy = json.loads((tmp_path / "app" / "deploy.json").read_text(encoding="utf-8"))
    assert app["version"] == "v1"
    assert app["schema"] == "oce.template.app.v1"
    assert app["python"] == "3.12"
    assert app["telemetry"] == "local-file"
    assert deploy["publication"] == "NOT_AUTHORIZED"
    assert deploy["requires_cloud"] is False


def test_deterministic_build_byte_identical(tmp_path: pathlib.Path) -> None:
    first = skeleton.build()
    second = skeleton.build()
    assert first == second
    write(tmp_path / "one")
    write(tmp_path / "two")
    for relative in sorted(first):
        left = (tmp_path / "one" / relative).read_bytes()
        right = (tmp_path / "two" / relative).read_bytes()
        assert left == right
        assert b"\r\n" not in left
    assert skeleton.manifest() == skeleton.manifest()


def test_invalid_manifest_refused(tmp_path: pathlib.Path) -> None:
    good = skeleton.manifest()
    extra = dict(good, unexpected=True)
    with pytest.raises(refusals.Refused) as exc:
        archive.install(extra, tmp_path / "bad")
    assert exc.value.code == "REFUSED_MALFORMED_ARCHIVE"
    assert not (tmp_path / "bad").exists()


def test_template_readme_present(tmp_path: pathlib.Path) -> None:
    write(tmp_path / "app")
    readme = (tmp_path / "app" / "README.md").read_text(encoding="utf-8")
    assert "OCE Book 6 skeleton" in readme
    assert "python app/__main__.py" in readme
    assert "READY app" in readme
    assert "cloud" in readme


def test_cloud_dependency_declared_absent(tmp_path: pathlib.Path) -> None:
    write(tmp_path / "app")
    skeleton.start(tmp_path / "app")
    app_path = tmp_path / "app" / "app.json"
    app = json.loads(app_path.read_text(encoding="utf-8"))
    app["cloud"] = True
    app_path.write_text(json.dumps(app, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(refusals.Refused) as exc:
        skeleton.start(tmp_path / "app")
    assert exc.value.code == "REFUSED_CLOUD"
