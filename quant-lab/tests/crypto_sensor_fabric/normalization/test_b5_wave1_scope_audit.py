"""SENSOR-B5-WAVE1 - scope audit for the Wave 1 sensor implementation.

A checkpoint that proves what it added has also to prove what it did not.  This
audit is the Wave 1 counterpart of the I01/I02/I03/I05/I08/I09/I10/I11 scope
audits, and it records the EXACT-FILE admission this wave performs:

* ``sensors/`` is exactly the eleven authorized modules -- the six historical
  ones plus ``admission.py``, ``oi.py``, ``funding.py``, ``book.py``,
  ``positioning.py`` and ``basis.py``, each named individually, with no prefix or
  wildcard admission;
* ``normalization/lineage/`` is exactly one package module (I16 preliminary);
* the ratified 24-symbol root API is unchanged and the sensor surface is still
  reachable only by its explicit path;
* the unfinished composite envelope stays unexported;
* the frozen eight-member sensor family vocabulary is untouched;
* no I17-I23 module exists (no duplicate engine, no generation writer, no query
  layer);
* the approval manifest, its pinned digest and the ``INTEGRATION_REQUIRED`` state
  are unchanged: Wave 1 authorizes no provider approval and no manifest
  activation;
* the lineage gate is not closed.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_PACKAGE = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization"
_SENSORS = _PACKAGE / "sensors"
_LINEAGE = _PACKAGE / "lineage"

#: The exact-file admission of SENSOR-B5-P3-RATIFICATION-AND-SENSOR-WAVE1-R1.
#: Historical entries are preserved verbatim; the six Wave 1 modules are named
#: one by one.  A twelfth module is still an unapproved surface.
FROZEN_MODULES = [
    "__init__.py",
    # DISCLOSED Wave 1: the shared semantic-admission ladder + derived amounts.
    "admission.py",
    # DISCLOSED Wave 1 (B5-I15b): the basis normalizer.
    "basis.py",
    # DISCLOSED Wave 1 (B5-I14): book snapshot + book metric.
    "book.py",
    # DISCLOSED Wave 1 (B5-I13): the funding normalizer.
    "funding.py",
    "liquidation.py",
    # DISCLOSED Wave 1 (B5-I12): the open-interest normalizer.
    "oi.py",
    # DISCLOSED Wave 1 (B5-I15a): the positioning normalizer.
    "positioning.py",
    "side_maps.py",
    "trade.py",
    "verification.py",
]

FROZEN_SENSOR_FAMILIES = [
    "MECHANICAL_BASIS",
    "MECHANICAL_BOOK_METRIC",
    "MECHANICAL_BOOK_SNAPSHOT",
    "MECHANICAL_FUNDING",
    "MECHANICAL_LIQUIDATION",
    "MECHANICAL_OPEN_INTEREST",
    "MECHANICAL_POSITIONING",
    "MECHANICAL_TRADE",
]

#: Directories/modules that belong to LATER checkpoints and must not exist.
FORBIDDEN_LATER_PATHS = ("duplicates", "query", "generation", "writer")

#: The reviewed production approval root and its pinned digest (I09P2A).
MANIFEST = (
    _QUANT_LAB
    / "config"
    / "crypto_sensor_fabric"
    / "provider_semantics"
    / "approval_manifest.json"
)
MANIFEST_SHA256 = "3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654"


def _sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_SENSORS.glob("*.py"))
    }


# ---------------------------------------------------------------------------
# Exact implementation scope
# ---------------------------------------------------------------------------


def test_the_sensor_package_is_exactly_the_eleven_admitted_modules() -> None:
    files = sorted(entry.name for entry in _SENSORS.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


def test_the_lineage_package_is_one_module() -> None:
    files = sorted(entry.name for entry in _LINEAGE.iterdir() if entry.suffix == ".py")
    assert files == ["__init__.py"]


def test_no_later_checkpoint_surface_exists() -> None:
    present = {entry.name for entry in _PACKAGE.iterdir()}
    for forbidden in FORBIDDEN_LATER_PATHS:
        assert forbidden not in present, f"later-checkpoint surface leaked: {forbidden}"


def test_the_ratified_root_api_is_unchanged() -> None:
    import crypto_sensor_fabric.normalization as normalization

    assert len(normalization.__all__) == 24
    for absent in (
        "normalize_open_interest",
        "normalize_funding",
        "normalize_book_snapshot",
        "normalize_positioning",
        "normalize_basis",
    ):
        assert absent not in normalization.__all__
        assert not hasattr(normalization, absent)


def test_the_unfinished_composite_envelope_is_still_not_exported() -> None:
    import crypto_sensor_fabric.normalization.sensors as sensors

    assert "T1ObservationEnvelope" not in sensors.__all__
    assert not hasattr(sensors, "T1ObservationEnvelope")


def test_every_wave1_normalizer_is_exported_explicitly() -> None:
    import crypto_sensor_fabric.normalization.sensors as sensors

    for name in (
        "normalize_open_interest",
        "T1OpenInterestRecord",
        "OpenInterestObservationInput",
        "normalize_funding",
        "T1FundingRecord",
        "FundingObservationInput",
        "normalize_book_snapshot",
        "normalize_book_metric",
        "T1BookSnapshotRecord",
        "T1BookMetricRecord",
        "normalize_positioning",
        "T1PositioningRecord",
        "normalize_basis",
        "T1BasisRecord",
        "SensorFieldAdmission",
        "admit_sensor_field",
    ):
        assert name in sensors.__all__, name
        assert hasattr(sensors, name), name


def test_the_frozen_sensor_family_set_is_untouched() -> None:
    from crypto_sensor_fabric.contracts.enums import SensorFamily

    assert sorted(member.value for member in SensorFamily) == FROZEN_SENSOR_FAMILIES


def test_no_frozen_enum_is_duplicated_in_the_sensor_tree() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "class AggressorSide(",
            "class SensorFamily(",
            "class AggregationType(",
            "class NormalizationStatus(",
            "class MissingnessReason(",
            "class NormalizationQualityFlag(",
            "class SemanticEquivalence(",
        ):
            assert forbidden not in text, f"{name} re-declares {forbidden}"


# ---------------------------------------------------------------------------
# Boundary firewalls
# ---------------------------------------------------------------------------


def test_no_network_or_provider_import() -> None:
    imported: set[str] = set()
    for text in _sources().values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    imported.add("." * node.level + (node.module or ""))
                elif node.module:
                    imported.add(node.module)
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib.request",
        "ccxt",
        "crypto_sensor_fabric.providers",
    ):
        assert forbidden not in imported, forbidden


def test_the_sensor_tree_stays_hash_free() -> None:
    """Hashing lives in ``normalization/lineage/``, not in a normalizer."""
    for name, text in _sources().items():
        for forbidden in ("hashlib", "sha256(", "uuid4", "import random"):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_the_identity_layer_does_not_read_a_clock_or_an_environment() -> None:
    text = (_LINEAGE / "__init__.py").read_text(encoding="utf-8")
    for forbidden in (
        "datetime.now",
        "datetime.utcnow",
        "time.time",
        "uuid4",
        "import random",
        "import socket",
        "import platform",
        "os.environ",
    ):
        assert forbidden not in text, forbidden


def test_no_gate_language_in_the_sensor_tree() -> None:
    for name, text in _sources().items():
        for forbidden in ("OPERATOR_ACCEPTED", "IMPLEMENTATION_PASS", "_GATE ="):
            assert forbidden not in text, f"{name} references {forbidden}"


# ---------------------------------------------------------------------------
# No approval, no activation, no closure
# ---------------------------------------------------------------------------


def test_the_approval_manifest_is_unchanged() -> None:
    digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert digest == MANIFEST_SHA256


def test_the_production_consumer_still_requires_integration() -> None:
    text = (
        _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "sensors"
        / "verification.py"
    ).read_text(encoding="utf-8")
    assert 'INTEGRATION_STATE = "INTEGRATION_REQUIRED"' in text


def test_the_lineage_gate_is_still_open() -> None:
    from crypto_sensor_fabric.normalization.lineage import (
        LINEAGE_GATE_CLOSED,
        LINEAGE_GATE_STATE,
    )

    assert LINEAGE_GATE_CLOSED is False
    assert LINEAGE_GATE_STATE == "NOT_CLOSED"


def test_the_i08_units_methodology_is_still_unadmitted() -> None:
    from crypto_sensor_fabric.normalization.sensors import (
        OI_CONTRACTS_METHODOLOGY_ID,
        OI_USD_PASSTHROUGH_METHODOLOGY_ID,
    )

    assert OI_CONTRACTS_METHODOLOGY_ID == "OI_CONTRACTS_TO_USD_V1"
    assert OI_USD_PASSTHROUGH_METHODOLOGY_ID == "OI_USD_NATIVE_PASSTHROUGH_V1"
    # There is no admitted-units constant anywhere: the dependency is explicit.
    text = (_SENSORS / "oi.py").read_text(encoding="utf-8")
    assert "B5_I08_UNITS_V1 remains unresolved" in text or (
        "I08_UNITS_METHODOLOGY_ID" in text
    )
