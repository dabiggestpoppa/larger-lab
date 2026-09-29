"""One-OCE boundary — every temporary fixture, declared and replaceable.

The Foundry must not become a second OCE. Anything that looks like a generic
institutional service (identity, authority, evidence, artifacts, workflow,
scheduling, recovery, budget, resource routing, evaluator governance) is a
*temporary local stand-in* here, and every stand-in carries:

* ``canonical_oce_target`` — where the real service lives;
* ``replacement_condition`` — the trigger to replace it;
* ``retirement_evidence`` — what proves replacement happened.

:func:`scan_undeclared_doubles` walks the package and fails if any
``OceTestDouble`` instance is not registered below, so a new fixture cannot be
added quietly.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from typing import Any

from .core import OceTestDouble, fingerprint

#: Every local stand-in that exists in this build.
LOCAL_FIXTURES: dict[str, OceTestDouble] = {}


def _register(double: OceTestDouble) -> OceTestDouble:
    existing = LOCAL_FIXTURES.get(double.fixture)
    if existing is not None and existing.to_dict() != double.to_dict():
        raise RuntimeError(f"conflicting declaration for fixture {double.fixture!r}")
    LOCAL_FIXTURES[double.fixture] = double
    return double


@dataclass(frozen=True)
class FixtureBoundaryEntry:
    fixture: str
    module: str
    canonical_oce_target: str
    replacement_condition: str
    retirement_evidence: str
    noncanonical: bool
    present_scope: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture": self.fixture,
            "module": self.module,
            "noncanonical": self.noncanonical,
            "canonical_oce_target": self.canonical_oce_target,
            "replacement_condition": self.replacement_condition,
            "retirement_evidence": self.retirement_evidence,
            "present_scope": self.present_scope,
        }


#: Fixtures that exist only as *declarations* (not implemented locally) because
#: the Foundry simply does not need them yet. They must never appear as code.
DECLARED_ONLY: tuple[str, ...] = (
    "identity",
    "authority",
    "artifacts",
)

PRESENT_SCOPE: dict[str, str] = {
    "FoundryLocalEvidenceLedger": "MF-B2/B3 provenance links only; no generic evidence graph",
    "FoundryLocalOfferNormalizer": "read-only offer normalization + placement; no provider API calls",
    "FoundryLocalRunLifecycle": "dataset/experiment run records only; no scheduler",
    "FoundryLocalNegativeKnowledge": "negative results + reopen records only",
    "FoundryLocalEvaluationFreeze": "protocol freeze + sealed access boundary only",
    "FoundryLocalCheckpointRecovery": "portable checkpoint manifests + simulated resume only",
    "FoundryLocalBudgetLedger": "explicit operator budget arithmetic only; no spend path",
}


def register_all() -> dict[str, OceTestDouble]:
    """Discover every declaration (module-level and generic registry) and index it."""

    from .core import GENERIC_SERVICE_DOUBLES

    for double in GENERIC_SERVICE_DOUBLES.values():
        _register(double)
    for fixture, locations in scan_declared_doubles().items():
        for location in locations:
            module_name, _name = location.rsplit(".", 1)
            module = importlib.import_module(module_name)
            for value in vars(module).values():
                if isinstance(value, OceTestDouble) and value.fixture == fixture:
                    _register(value)
    return LOCAL_FIXTURES


def scan_declared_doubles() -> dict[str, list[str]]:
    """Find every ``OceTestDouble`` instance defined in the package."""

    import foundry as package

    found: dict[str, list[str]] = {}
    for module_info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{module_info.name}")
        for name, value in vars(module).items():
            if isinstance(value, OceTestDouble):
                found.setdefault(value.fixture, []).append(f"{module.__name__}.{name}")
    return found


def scan_undeclared_doubles() -> tuple[str, ...]:
    """Fixtures present in code but missing from the declared local registry."""

    found = scan_declared_doubles()
    register_all()
    return tuple(sorted(set(found) - set(LOCAL_FIXTURES)))


def boundary_registry() -> tuple[FixtureBoundaryEntry, ...]:
    register_all()
    entries: list[FixtureBoundaryEntry] = []
    found = scan_declared_doubles()
    for fixture, double in sorted(LOCAL_FIXTURES.items()):
        modules = found.get(fixture, ["declaration-only"])
        entries.append(
            FixtureBoundaryEntry(
                fixture=fixture,
                module=",".join(modules),
                canonical_oce_target=double.canonical_oce_target,
                replacement_condition=double.replacement_condition,
                retirement_evidence=double.retirement_evidence,
                noncanonical=double.noncanonical,
                present_scope=PRESENT_SCOPE.get(fixture, "declaration only"),
            )
        )
    return tuple(entries)


def assert_boundary_complete() -> None:
    """Fail closed if a fixture lacks a retirement path or is undeclared."""

    from .core import PolicyBlocked

    undeclared = scan_undeclared_doubles()
    if undeclared:
        raise PolicyBlocked(
            "OCE_DOUBLE_UNDECLARED",
            f"fixtures without a One-OCE boundary declaration: {', '.join(undeclared)}",
        )
    for entry in boundary_registry():
        if not (entry.canonical_oce_target and entry.replacement_condition and entry.retirement_evidence):
            raise PolicyBlocked(
                "OCE_DOUBLE_WITHOUT_RETIREMENT_PATH",
                f"{entry.fixture} has an incomplete replacement declaration",
            )
        if entry.noncanonical is not True:
            raise PolicyBlocked(
                "FIXTURE_CLAIMS_CANONICAL_AUTHORITY",
                f"{entry.fixture} is not marked noncanonical",
            )


def boundary_fingerprint() -> str:
    return fingerprint([entry.to_dict() for entry in boundary_registry()])


def declaration_payload() -> dict[str, Any]:
    """Serializable payload for docs/fixtures: the boundary as data."""

    return {
        "marker": "NONCANONICAL_OCE_TEST_DOUBLES",
        "declared_only_services": list(DECLARED_ONLY),
        "fixtures": [entry.to_dict() for entry in boundary_registry()],
        "boundary_fingerprint": boundary_fingerprint(),
        "second_oce_risk": "none declared; every local stand-in has a retirement path",
    }


def module_surface() -> dict[str, tuple[str, ...]]:
    """Public classes/functions per module, used by the integration map generator."""

    import foundry as package

    surface: dict[str, tuple[str, ...]] = {}
    for module_info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{module_info.name}")
        names = tuple(
            sorted(
                name
                for name, value in vars(module).items()
                if not name.startswith("_")
                and (inspect.isclass(value) or inspect.isfunction(value))
                and getattr(value, "__module__", "") == module.__name__
            )
        )
        surface[module.__name__] = names
    return dict(sorted(surface.items()))


__all__ = [
    "DECLARED_ONLY",
    "LOCAL_FIXTURES",
    "PRESENT_SCOPE",
    "FixtureBoundaryEntry",
    "assert_boundary_complete",
    "boundary_fingerprint",
    "boundary_registry",
    "declaration_payload",
    "module_surface",
    "scan_declared_doubles",
    "scan_undeclared_doubles",
]
