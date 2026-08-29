"""Free-only provider registry (Bloc 1 §7, §12-13; 02 §12-13).

Config: `config/crypto_sensor_fabric/provider_registry.yaml`.

Invariants:

- every provider entry carries an evidence class (B1-T30)
- capability claims default to `verified=false` until Bloc 2 probes (B1-T31)
- a provider may be a required automated runtime dependency only when its
  `FreeOnlyPolicy` passes the frozen F9 gate (B1-T20..T24)
- provider ordering is explicit config, never hard-coded application logic
  (B1-T33)
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .._paths import CONFIG_DIR
from ..contracts.access import FreeOnlyPolicy, free_only_violations
from ..contracts.enums import EvidenceClass, ProviderStatus, SemanticEquivalence

DEFAULT_PROVIDER_REGISTRY_PATH = CONFIG_DIR / "provider_registry.yaml"

#: Provider IDs currently in the frozen candidate set.  Registry-controlled
#: strings — the enum vocabulary for provider capability keys is below.
PROVIDER_IDS: tuple[str, ...] = (
    "KRAKEN_FUTURES",
    "GATE_FUTURES",
    "BINANCE_USDM",
    "BYBIT_LINEAR",
    "OKX_SWAP",
    "DERIBIT",
    "COINALYZE",
    "BITFINEX_COMMUNITY_ARCHIVE",
)

#: Canonical capability keys (map to sensor states in sensor_priority.yaml).
CAPABILITY_KEYS: tuple[str, ...] = (
    "liquidations",
    "open_interest",
    "funding",
    "order_flow",
    "order_book",
)


class ProviderCapability(BaseModel):
    """One capability claim.  Claims are never verification."""

    model_config = ConfigDict(extra="forbid")

    claimed: bool = False
    verified: bool = False
    equivalence_default: SemanticEquivalence | None = None


class ProviderEntry(BaseModel):
    """One provider candidate entry."""

    model_config = ConfigDict(extra="forbid")

    evidence_class: EvidenceClass
    status: ProviderStatus = ProviderStatus.CANDIDATE
    access: FreeOnlyPolicy = Field(default_factory=FreeOnlyPolicy)
    capabilities: dict[str, ProviderCapability] = Field(default_factory=dict)
    fallback_candidates: dict[str, list[str]] = Field(default_factory=dict)
    notes: str | None = None

    @model_validator(mode="after")
    def _capability_keys_controlled(self) -> ProviderEntry:
        unexpected = set(self.capabilities) - set(CAPABILITY_KEYS)
        if unexpected:
            raise ValueError(
                f"unknown capability keys {sorted(unexpected)}; "
                f"allowed={list(CAPABILITY_KEYS)}"
            )
        return self

    @model_validator(mode="after")
    def _verified_requires_claimed(self) -> ProviderEntry:
        for key, capability in self.capabilities.items():
            if capability.verified and not capability.claimed:
                raise ValueError(
                    f"capability {key!r} marked verified but not claimed"
                )
        return self


class ProviderRegistry(BaseModel):
    """The full provider candidate registry."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    providers: dict[str, ProviderEntry] = Field(min_length=1)


def load_provider_registry(path: Path | None = None) -> ProviderRegistry:
    """Load and validate the provider registry from YAML."""
    config_path = path or DEFAULT_PROVIDER_REGISTRY_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return ProviderRegistry.model_validate(data)


def validate_required_runtime(
    registry: ProviderRegistry, required: Iterable[str]
) -> list[str]:
    """Return F9 violations for providers marked required automated.

    Empty result means every required provider passes the frozen gate.  This
    function never silently promotes a provider: `UNVERIFIED`,
    `FREE_REFERENCE_ONLY` and `PAID_EXCLUDED` all fail closed (B1-T20..T22).
    """
    violations: list[str] = []
    for provider in required:
        entry = registry.providers.get(provider)
        if entry is None:
            violations.append(f"{provider}: unknown provider id")
            continue
        for violation in free_only_violations(entry.access):
            violations.append(f"{provider}: {violation}")
    return violations


def is_required_runtime_allowed(registry: ProviderRegistry, provider: str) -> bool:
    """True when a provider may be treated as a required automated source."""
    return not validate_required_runtime(registry, [provider])


def eligible_required_providers(registry: ProviderRegistry) -> list[str]:
    """Providers currently allowed as required automated dependencies.

    With the default Bloc 1 registry (everything UNVERIFIED) this is empty,
    which is correct: nothing may be required until Bloc 2 verifies it.
    """
    return [p for p in registry.providers if is_required_runtime_allowed(registry, p)]
