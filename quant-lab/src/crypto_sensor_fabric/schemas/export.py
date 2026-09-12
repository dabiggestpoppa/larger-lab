"""Deterministic JSON-schema export and committed snapshot management (B1-T63).

Snapshots are committed under `config/crypto_sensor_fabric/schema_snapshots/`
so breaking schema drift is visible in Git.  Regenerate with:

    python tools/export_sensor_fabric_schemas.py

The snapshot test (`tests/.../contracts/test_versioning.py`) fails when the
committed snapshots drift from what the models currently export.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .._paths import CONFIG_DIR
from ..contracts.access import FreeOnlyPolicy
from ..contracts.base import CanonicalObservationBase, MissingObservation
from ..contracts.identity import InstrumentIdentity
from .basis import MechanicalBasis
from .book import MechanicalBookMetric, MechanicalBookSnapshot, PriceLevel
from .funding import MechanicalFunding
from .liquidation import MechanicalLiquidation
from .open_interest import MechanicalOpenInterest
from .positioning import MechanicalPositioning
from .provider_envelope import ProviderEnvelope
from .trade import MechanicalTrade

SCHEMA_SNAPSHOT_DIR = CONFIG_DIR / "schema_snapshots"

#: Every snapshotted model.  Adding a canonical schema requires adding it here
#: so its JSON Schema is frozen in Git.
SNAPSHOT_MODELS: dict[str, type[BaseModel]] = {
    "CanonicalObservationBase": CanonicalObservationBase,
    "ProviderEnvelope": ProviderEnvelope,
    "PriceLevel": PriceLevel,
    "MechanicalTrade": MechanicalTrade,
    "MechanicalLiquidation": MechanicalLiquidation,
    "MechanicalOpenInterest": MechanicalOpenInterest,
    "MechanicalFunding": MechanicalFunding,
    "MechanicalBookSnapshot": MechanicalBookSnapshot,
    "MechanicalBookMetric": MechanicalBookMetric,
    "MechanicalPositioning": MechanicalPositioning,
    "MechanicalBasis": MechanicalBasis,
    "MissingObservation": MissingObservation,
    "FreeOnlyPolicy": FreeOnlyPolicy,
    "InstrumentIdentity": InstrumentIdentity,
}


def export_schema(model_cls: type[BaseModel]) -> str:
    """Deterministic JSON-schema text for one model (sorted keys)."""
    schema = model_cls.model_json_schema()
    return json.dumps(schema, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def export_all_schemas() -> dict[str, str]:
    """Model name → deterministic JSON-schema text for every snapshotted model."""
    return {name: export_schema(cls) for name, cls in SNAPSHOT_MODELS.items()}


def snapshot_path(name: str, directory: Path | None = None) -> Path:
    return (directory or SCHEMA_SNAPSHOT_DIR) / f"{name}.schema.json"


def write_snapshots(directory: Path | None = None) -> dict[str, Path]:
    """Write all schema snapshots; returns {model name: written path}."""
    target = directory or SCHEMA_SNAPSHOT_DIR
    target.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for name, content in export_all_schemas().items():
        path = snapshot_path(name, target)
        path.write_text(content, encoding="utf-8")
        written[name] = path
    return written


def load_snapshot(name: str, directory: Path | None = None) -> str:
    """Read a committed snapshot as text."""
    return snapshot_path(name, directory).read_text(encoding="utf-8")


def main() -> None:
    written = write_snapshots()
    print(f"Wrote {len(written)} JSON-schema snapshots to {SCHEMA_SNAPSHOT_DIR}")


if __name__ == "__main__":
    main()
