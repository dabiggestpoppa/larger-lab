"""Provider probe interface (bloc_02/04 §5) + endpoint registry loader.

Each provider probe module implements the `ProviderCapabilityProbe` protocol.
Provider-specific query construction and payload interpretation stay below
this boundary.  Probe modules are pure characterizers: they map a fetched
HTTP response (status + body) into an immutable `CapabilityProbeAttempt`
without touching the network — the live executor (SENSOR-B2-I13) does the
fetching, keeping unit tests offline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml

from .._paths import CONFIG_DIR
from ..probes.enums import ProbeFailureClass
from ..probes.models import CapabilityProbeAttempt, CapabilityProbeRequest

DEFAULT_ENDPOINTS_PATH = CONFIG_DIR / "provider_probe_endpoints.yaml"


@runtime_checkable
class ProviderCapabilityProbe(Protocol):
    """Minimal capability-characterization boundary every probe satisfies."""

    provider_id: str

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        """Return the deterministic HTTP query shape: {"url", "params"}."""
        ...

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        """Map an unsuccessful response to one controlled failure class."""
        ...

    def characterize(
        self,
        request: CapabilityProbeRequest,
        http_status: int | None,
        body: Any,
    ) -> CapabilityProbeAttempt:
        """Map one fetched response into an immutable probe attempt."""
        ...

    def summarize_native_schema(self, body: Any) -> dict[str, Any]:
        """Structural schema summary of a payload (fingerprint, keys, types)."""
        ...


def load_endpoint_registry(path: Path | None = None) -> dict[str, Any]:
    """Load the provider probe endpoint registry (config/.../provider_probe_endpoints.yaml)."""
    config_path = path or DEFAULT_ENDPOINTS_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    providers = data.get("providers", {})
    if not isinstance(providers, dict) or not providers:
        raise ValueError(f"endpoint registry {config_path} has no providers")
    return providers
