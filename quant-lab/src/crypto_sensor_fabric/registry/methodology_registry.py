"""Methodology registry (02 §16).

Config: `config/crypto_sensor_fabric/methodology_registry.yaml`.

Every non-trivial derived canonical value references one methodology ID.
Changing a formula under the same methodology ID is a forbidden silent change
(02 §18): implementations must bump the methodology version instead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .._paths import CONFIG_DIR

DEFAULT_METHODOLOGY_REGISTRY_PATH = CONFIG_DIR / "methodology_registry.yaml"

MethodologyKind = Literal["NORMALIZATION", "RECONSTRUCTION", "AGGREGATION", "CLASSIFICATION", "OTHER"]
Layer = Literal["T0", "T1", "T2"]


class MethodologyEntry(BaseModel):
    """One versioned methodology contract."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1"
    kind: MethodologyKind = "OTHER"
    description: str = Field(min_length=1)
    input_contract: str | None = None
    output_contract: str | None = None
    owner_layer: Layer | None = None
    status: str = "PROVISIONAL"
    notes: str | None = None


class MethodologyRegistry(BaseModel):
    """Full methodology registry keyed by methodology ID."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    methodologies: dict[str, MethodologyEntry] = Field(min_length=1)


def load_methodology_registry(path: Path | None = None) -> MethodologyRegistry:
    """Load and validate the methodology registry from YAML."""
    config_path = path or DEFAULT_METHODOLOGY_REGISTRY_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return MethodologyRegistry.model_validate(data)


def require_methodology_id(registry: MethodologyRegistry, methodology_id: str) -> None:
    """Fail closed when a referenced methodology ID is not registered."""
    if methodology_id not in registry.methodologies:
        raise KeyError(f"methodology_id {methodology_id!r} not found in methodology registry")
