"""B6-I2 determinism and compatibility proofs: no silent latest, unproven rows, no stable API."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs/oce-golden-system"
PREFIX = "OCE_BLOCK_06_I2_"
sys.path.insert(0, str(ROOT))

from oce.templates import archive, refusals, skeleton  # noqa: E402


def load(name: str) -> dict:
    return json.loads((DOCS / f"{PREFIX}{name}").read_text(encoding="utf-8"))


def code(fn, *args):
    with pytest.raises(refusals.Refused) as exc:
        fn(*args)
    return exc.value


def test_no_silent_latest() -> None:
    good = skeleton.manifest()
    for version in ("v2", "latest", "V1", ""):
        bad = dict(good, version=version)
        err = code(archive.validate, bad)
        assert err.code == "REFUSED_UNKNOWN_VERSION"
        assert err.detail == version
    contract = load("IMPLEMENTATION_CONTRACT_v1.0.json")
    assert contract["compatibility"]["silent_latest"] is False
    assert contract["compatibility"]["unknown_refused"] is True


def test_compat_rows_remain_unproven() -> None:
    compat = load("COMPATIBILITY_MATRIX_v1.0.json")
    assert compat["rows_total"] == 2
    assert {row["surface"] for row in compat["rows"]} == {"C1.S3", "C1.S4"}
    assert all(row["state"] == "UNPROVEN" for row in compat["rows"])
    assert all(row["consumer_evidence"] == "none" for row in compat["rows"])
    assert compat["observed"]["proven_rows"] == 0
    assert compat["refusal"]["unknown_version"] == "REFUSED"
    assert compat["refusal"]["silent_latest"] is False
    assert compat["conformance"]["declaration_without_test"] == "UNPROVEN"


def test_private_symbol_not_stable() -> None:
    api = load("API_TEMPLATE_AND_HARNESS_CONTRACT_v1.0.json")
    rows = {row["symbol"]: row for row in api["symbols"]}
    assert set(rows) == {"template:oce-app-skeleton", "oce.harness.local.up"}
    assert rows["template:oce-app-skeleton"]["classification"] == "deferred"
    assert rows["template:oce-app-skeleton"]["exported"] is False
    assert rows["template:oce-app-skeleton"]["compatibility"] == "not_published"
    assert rows["oce.harness.local.up"]["classification"] == "public_experimental"
    assert rows["oce.harness.local.up"]["exported"] is True
    assert not any(row["classification"] == "stable" for row in rows.values())
    assert "no stable private symbol" in api["prohibitions"]


def test_dirty_build_input_refused(tmp_path: pathlib.Path) -> None:
    dest = tmp_path / "busy"
    dest.mkdir()
    (dest / "leftover.txt").write_text("stale\n", encoding="utf-8")
    err = code(skeleton.write, dest)
    assert err.code == "REFUSED_DIRTY_INPUT"
    assert (dest / "leftover.txt").read_text(encoding="utf-8") == "stale\n"
    clean = tmp_path / "clean"
    clean.mkdir()
    assert skeleton.write(clean)["installed"] == 8
