"""Book 4 D4-6 HARD_RUNTIME stress tests A-J."""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book4_test_support import hard_evidence, kernel
from crypto_systems_intelligence_atlas.dependency import FallbackState, HardRuntimeGate, RuntimeScope
from crypto_systems_intelligence_atlas.temporal import UnknownBound


@pytest.mark.parametrize(
    ("case", "updates", "expected"),
    [
        ("A", {}, RuntimeScope.HARD_RUNTIME),
        ("B", {"fallback_state": FallbackState.ACTIVE_EQUIVALENT}, RuntimeScope.UNKNOWN),
        ("C", {"function": "compile contract", "scope": "build pipeline", "runtime_scope_hint": RuntimeScope.BUILD_TIME}, RuntimeScope.BUILD_TIME),
        ("D", {"function": "optional price display", "scope": "user interface", "runtime_scope_hint": RuntimeScope.SOFT_RUNTIME}, RuntimeScope.SOFT_RUNTIME),
        ("E", {"function": "liquidate account", "scope": "liquidation execution"}, RuntimeScope.HARD_RUNTIME),
        ("F", {"function": "optional bridge route", "scope": "optional integration", "runtime_scope_hint": RuntimeScope.SOFT_RUNTIME}, RuntimeScope.SOFT_RUNTIME),
        ("G", {"function": "frontend history query", "scope": "product UI", "runtime_scope_hint": RuntimeScope.SOFT_RUNTIME}, RuntimeScope.SOFT_RUNTIME),
        ("H", {"function": "normal transaction inclusion", "scope": "sequencer liveness", "escape_hatch_evidenced": True}, RuntimeScope.UNKNOWN),
        ("I", {"fallback_state": FallbackState.DECLARED_UNVERIFIED}, RuntimeScope.UNKNOWN),
        ("J", {"deployed_configuration_evidenced": False}, RuntimeScope.UNKNOWN),
    ],
)
def test_ratified_hard_runtime_cases(case: str, updates: dict[str, object], expected: RuntimeScope) -> None:
    _, _, provenance = kernel()
    result = HardRuntimeGate(provenance).classify(hard_evidence(**updates))
    if case == "B":
        assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    elif case == "I":
        assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    elif case == "J":
        assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    elif case in {"C", "D", "F", "G"}:
        assert result.runtime_scope is expected
    elif case == "H":
        assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    else:
        assert result.runtime_scope is expected


@pytest.mark.parametrize(
    "updates",
    [
        {"deployed_configuration_evidenced": False},
        {"runtime_necessity_evidenced": False},
        {"removal_makes_function_unavailable": False},
        {"fallback_state": FallbackState.ACTIVE_EQUIVALENT},
        {"fallback_state": FallbackState.DECLARED_UNVERIFIED},
        {"valid_time": UnknownBound()},
    ],
)
def test_any_missing_d4_6_condition_fails_closed(updates: dict[str, object]) -> None:
    _, _, provenance = kernel()
    result = HardRuntimeGate(provenance).classify(hard_evidence(**updates))
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert result.reasons


def test_hard_runtime_is_function_scoped_not_provider_ranked() -> None:
    _, _, provenance = kernel()
    gate = HardRuntimeGate(provenance)
    liquidation = gate.classify(hard_evidence())
    ui = gate.classify(
        hard_evidence(
            function="display optional price",
            scope="user interface",
            removal_makes_function_unavailable=False,
        )
    )
    assert liquidation.runtime_scope is RuntimeScope.HARD_RUNTIME
    assert ui.runtime_scope is RuntimeScope.UNKNOWN


def test_build_time_never_hard_runtime() -> None:
    _, _, provenance = kernel()
    result = HardRuntimeGate(provenance).classify(
        hard_evidence(
            function="compile SDK consumer",
            scope="build pipeline",
            removal_makes_function_unavailable=False,
        )
    )
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
