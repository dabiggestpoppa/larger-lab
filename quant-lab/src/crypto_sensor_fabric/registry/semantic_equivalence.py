"""Semantic equivalence registry (02 §15 / B1-T40..T43).

Config: `config/crypto_sensor_fabric/semantic_equivalence.yaml`.

Rules:

- every mapping carries a SemanticEquivalence class (B1-T40)
- `NORMALIZABLE_COMPARABLE` mappings require a methodology ID (B1-T41)
- `EXACT_EQUIVALENT` mappings require an evidence reference (B1-T43)
- `CORROBORATION_ONLY` and `NOT_COMPARABLE` are ineligible for automatic
  pooled numeric synthesis (B1-T42)
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .._paths import CONFIG_DIR
from ..contracts.enums import SemanticEquivalence, SensorFamily

DEFAULT_SEMANTIC_EQUIVALENCE_PATH = CONFIG_DIR / "semantic_equivalence.yaml"


class EquivalenceMapping(BaseModel):
    """One provider→canonical semantic mapping."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    source_metric: str = Field(min_length=1)
    canonical_sensor: SensorFamily
    canonical_field: str = Field(min_length=1)
    equivalence: SemanticEquivalence
    methodology_id: str | None = None
    evidence_reference: str | None = None
    version: str = "1"
    source_definition: str | None = None
    transformation_method: str | None = None

    @model_validator(mode="after")
    def _comparable_requires_methodology(self) -> EquivalenceMapping:
        if (
            self.equivalence is SemanticEquivalence.NORMALIZABLE_COMPARABLE
            and not self.methodology_id
        ):
            raise ValueError(
                "NORMALIZABLE_COMPARABLE mapping requires methodology_id (B1-T41)"
            )
        return self

    @model_validator(mode="after")
    def _exact_requires_evidence(self) -> EquivalenceMapping:
        if (
            self.equivalence is SemanticEquivalence.EXACT_EQUIVALENT
            and not self.evidence_reference
        ):
            raise ValueError(
                "EXACT_EQUIVALENT mapping requires evidence_reference (B1-T43)"
            )
        return self


class SemanticEquivalenceRegistry(BaseModel):
    """Full semantic equivalence registry."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    mappings: list[EquivalenceMapping] = Field(min_length=1)


def load_semantic_equivalence(
    path: Path | None = None,
) -> SemanticEquivalenceRegistry:
    """Load and validate the semantic equivalence registry from YAML."""
    config_path = path or DEFAULT_SEMANTIC_EQUIVALENCE_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return SemanticEquivalenceRegistry.model_validate(data)


def is_poolable(equivalence: SemanticEquivalence) -> bool:
    """Whether numeric pooling across providers is allowed by default.

    Only EXACT_EQUIVALENT and NORMALIZABLE_COMPARABLE may be pooled
    numerically; CORROBORATION_ONLY and NOT_COMPARABLE must stay independent
    (B1-T42).  Cross-venue synthesis additionally requires Bloc 6 eligibility.
    """
    return equivalence in {
        SemanticEquivalence.EXACT_EQUIVALENT,
        SemanticEquivalence.NORMALIZABLE_COMPARABLE,
    }
