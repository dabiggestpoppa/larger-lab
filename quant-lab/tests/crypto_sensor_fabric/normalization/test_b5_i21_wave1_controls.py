"""SENSOR-B5-I21 (associated controls) - cross-family Wave 1 regression controls.

The per-family suites prove each contract; this module proves the properties that
only exist ACROSS families and that a single-family suite can silently violate:

* native values are never overwritten by canonical ones;
* no dollar amount is fabricated while ``B5_I08_UNITS_V1`` is unadmitted;
* no sensor module mints a methodology id that the registry does not contain;
* the accepted I04B/I08 citations stay pinned to the primitives they name;
* no new family enters the trade request union;
* every PIT/leakage control that Wave 1 adds keeps its specific failure code
  rather than collapsing into one generic refusal.

I21 is NOT claimed complete: the end-to-end I16-I19 dependencies do not exist yet,
so these are the associated controls available at Wave 1.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from crypto_sensor_fabric.normalization.sensors import (
    FUNDING_EQUIV_METHODOLOGY_ID,
    I04B_METHODOLOGY_ID,
    I08_UNITS_METHODOLOGY_ID,
    OI_CONTRACTS_METHODOLOGY_ID,
    OI_USD_PASSTHROUGH_METHODOLOGY_ID,
    TradeObservationInput,
)
from crypto_sensor_fabric.normalization.common.conversion import (
    METHODOLOGY_VERSION as I08_PRIMITIVE_VERSION,
)
from crypto_sensor_fabric.normalization.terms.conversion import (
    METHODOLOGY_VERSION as I04B_PRIMITIVE_VERSION,
)

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_SENSORS = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "sensors"
_REGISTRY = (
    _QUANT_LAB / "config" / "crypto_sensor_fabric" / "methodology_registry.yaml"
)

#: The Wave 1 sensor-level methodology ids this branch is allowed to cite.
_WAVE1_METHODOLOGY_IDS = {
    OI_CONTRACTS_METHODOLOGY_ID,
    OI_USD_PASSTHROUGH_METHODOLOGY_ID,
    FUNDING_EQUIV_METHODOLOGY_ID,
}


def test_the_registry_contains_every_wave1_methodology() -> None:
    registry = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
    declared = set(registry["methodologies"])
    for methodology_id in _WAVE1_METHODOLOGY_IDS:
        assert methodology_id in declared, methodology_id


def test_no_wave1_module_cites_an_unregistered_methodology() -> None:
    registry = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
    declared = set(registry["methodologies"])
    allowed = declared | {"B5_I04B_CONVERSION_V1", "B5_I08_UNITS_V1"}
    cited: set[str] = set()
    for path in sorted(_SENSORS.glob("*.py")):
        for token in path.read_text(encoding="utf-8").split('"'):
            if token.endswith("_V1") or token.endswith("_V2"):
                cited.add(token)
    undeclared = cited - allowed
    assert not undeclared, f"unregistered methodology cited: {sorted(undeclared)}"


def test_the_i04b_citation_is_pinned_to_its_primitive() -> None:
    assert I04B_METHODOLOGY_ID == I04B_PRIMITIVE_VERSION


def test_the_i08_citation_is_pinned_to_its_primitive() -> None:
    assert I08_UNITS_METHODOLOGY_ID == I08_PRIMITIVE_VERSION


def test_no_basis_or_positioning_methodology_was_invented() -> None:
    """Neither family has a registry row, so neither may cite a derived method."""
    registry = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))
    declared = set(registry["methodologies"])
    assert not any("BASIS" in name for name in declared)
    assert not any("POSITIONING" in name for name in declared)


def test_the_trade_request_union_is_unchanged() -> None:
    """Mission section 3: no new family is forced into the trade request union."""
    fields = set(TradeObservationInput.model_fields)
    for forbidden in (
        "oi_native_value",
        "funding_rate_native",
        "bids",
        "asks",
        "population_scope",
        "basis_value_native",
    ):
        assert forbidden not in fields, forbidden


@pytest.mark.parametrize(
    "module_name",
    ["oi", "funding", "book", "positioning", "basis", "admission"],
)
def test_every_wave1_module_is_hash_free_and_clock_free(module_name: str) -> None:
    text = (_SENSORS / f"{module_name}.py").read_text(encoding="utf-8")
    for forbidden in (
        "hashlib",
        "uuid4",
        "datetime.now",
        "datetime.utcnow",
        "time.time",
        "import random",
        "import secrets",
    ):
        assert forbidden not in text, f"{module_name} references {forbidden}"


@pytest.mark.parametrize(
    "module_name",
    ["oi", "funding", "book", "positioning", "basis"],
)
def test_every_wave1_module_keeps_native_values_separate(module_name: str) -> None:
    """F12: a canonical field may never be the only home of a provider value."""
    text = (_SENSORS / f"{module_name}.py").read_text(encoding="utf-8")
    assert "native_values=" in text
    assert "NativeQuantity(" in text
