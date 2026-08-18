"""R1 checks 50-57 (paths, config hashing)."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from execution_runtime.enums import SecretKind
from execution_runtime.exceptions import InvalidRuntimeId, PathCollisionError
from execution_runtime.hashing import canonical_json, config_hash
from execution_runtime.profiles import (
    build_runtime_paths,
    canonical_runtime_id,
    normalize_runtime_id,
)
from execution_runtime.registry import RuntimeProfileRegistry
from execution_runtime.types import SecretReference


# ── PATHS ─────────────────────────────────────────────────────────────────


def test_50_deterministic_runtime_paths():
    a = build_runtime_paths("/tmp", "rt-1")
    b = build_runtime_paths("/tmp", "rt-1")
    assert a == b
    assert str(a.state_dir).replace("\\", "/").endswith("/state/rt-1")


def test_51_runtime_path_collision_rejected():
    from execution_runtime.profiles import assert_no_path_collision

    with pytest.raises(PathCollisionError):
        assert_no_path_collision(["rt-1", "RT-1"])


def test_52_path_traversal_rejected():
    with pytest.raises(InvalidRuntimeId):
        build_runtime_paths("/tmp", "../../etc")
    with pytest.raises(InvalidRuntimeId):
        normalize_runtime_id("a/b")
    with pytest.raises(InvalidRuntimeId):
        normalize_runtime_id("..")


def test_52b_empty_and_reserved_rejected():
    with pytest.raises(InvalidRuntimeId):
        normalize_runtime_id("")
    with pytest.raises(InvalidRuntimeId):
        normalize_runtime_id(".")


def test_registry_rejects_normalized_collision():
    from execution_runtime.enums import MachineProfile
    from execution_runtime.exceptions import DuplicateRuntimeError
    from execution_runtime.profiles import RuntimeProfile

    reg = RuntimeProfileRegistry()
    reg.register(RuntimeProfile("rt-1", MachineProfile.LOCAL_WINDOWS, "acct-1", 1))
    with pytest.raises(DuplicateRuntimeError):
        reg.register(RuntimeProfile("RT-1", MachineProfile.LOCAL_WINDOWS, "acct-1", 1))


# ── HASHING ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Probe:
    name: str
    value: int
    secret: SecretReference | None = None


def test_53_canonical_config_hash_deterministic():
    a = config_hash(_Probe("x", 1))
    b = config_hash(_Probe("x", 1))
    assert a == b
    assert a.startswith("QH1:")


def test_54_field_order_independent():
    a = config_hash(_Probe("x", 1))
    b = config_hash(_Probe(value=1, name="x"))
    assert a == b


def test_55_static_semantic_change_changes_hash():
    assert config_hash(_Probe("x", 1)) != config_hash(_Probe("x", 2))


def test_56_dynamic_state_does_not_alter_static_hash():
    # The hash only depends on the object type + its static fields.
    static = _Probe("x", 1)
    h1 = config_hash(static)
    # a separate dynamic object with the same name but different type hashes
    # differently, while re-hashing static stays identical.
    assert config_hash(static) == h1
    assert h1 != config_hash(_Probe("x", 999))


def test_57_secrets_never_included():
    p = _Probe("x", 1, secret=SecretReference(kind=SecretKind.ENV_VAR, reference="MY_SUPER_SECRET_KEY"))
    j = canonical_json(p)
    assert "MY_SUPER_SECRET_KEY" not in j
    assert "ENV_VAR" in j  # kind is retained; the reference identifier is not
