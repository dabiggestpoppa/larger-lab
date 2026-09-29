"""Provider adapters (MF-B1-I2/I3).

Two independent provider semantics (OctaSpace-like and RunPod-like) normalize
into one :class:`foundry.resources.ComputeOffer` contract. Adapters here are
**read-only observation adapters**:

* ``mode`` is ``OBSERVE`` or ``SIMULATE``; no adapter can rent, resize, or
  launch anything;
* ``live_read_only`` is False in this build, so every adapter serves deterministic
  fixtures (no network, no paid call);
* a raw observation is preserved alongside the normalized offer so that
  normalization losses stay visible.

Provider identity never changes scientific semantics: the normalized offer feeds
:func:`foundry.resources.simulate_placement`, which compares offers on
cost-to-close, not on names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import OceTestDouble, PolicyBlocked

PROVIDER_OFFER_DOUBLE = OceTestDouble(
    fixture="FoundryLocalOfferNormalizer",
    canonical_oce_target="OCE B10 Resource Intelligence (COMPUTE.GPU.RENT)",
    replacement_condition="replace when B10 exposes provider-neutral offer/routing",
    retirement_evidence="Foundry submits ComputeRequest to B10 and consumes routing receipts",
)


@dataclass(frozen=True)
class RawProviderObservation:
    """Exactly what a provider surface advertised, before normalization."""

    provider: str
    raw: dict[str, Any]
    observed_at_epoch_s: int
    freshness_window_s: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "raw": self.raw,
            "observed_at_epoch_s": self.observed_at_epoch_s,
            "freshness_window_s": self.freshness_window_s,
        }


@dataclass(frozen=True)
class ProviderAdapter:
    """A replaceable provider implementation, never required architecture."""

    name: str
    adapter_version: str
    mode: str
    live_read_only: bool
    normalize: str  # name of the normalization function
    notes: str
    double: OceTestDouble = field(default=PROVIDER_OFFER_DOUBLE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "adapter_version": self.adapter_version,
            "mode": self.mode,
            "live_read_only": self.live_read_only,
            "normalize": self.normalize,
            "notes": self.notes,
            "noncanonical_declaration": self.double.to_dict(),
            "can_launch_instances": False,
        }


ADAPTERS: dict[str, ProviderAdapter] = {
    "octa_fixture": ProviderAdapter(
        name="octa_fixture",
        adapter_version="1.0",
        mode="OBSERVE",
        live_read_only=False,
        normalize="_normalize_octa",
        notes="fixture-normalized OctaSpace-style offer semantics",
    ),
    "runpod_fixture": ProviderAdapter(
        name="runpod_fixture",
        adapter_version="1.0",
        mode="OBSERVE",
        live_read_only=False,
        normalize="_normalize_runpod",
        notes="fixture-normalized RunPod-style offer semantics",
    ),
    "local_cpu": ProviderAdapter(
        name="local_cpu",
        adapter_version="1.0",
        mode="SIMULATE",
        live_read_only=False,
        normalize="_normalize_local",
        notes="no-GPU dry run ladder rung 0",
    ),
}


#: Dialect spellings for the same normalized concept. Normalization exists so
#: that provider vocabulary never reaches scientific semantics.
_ALTERNATIVE_SPELLINGS: dict[str, tuple[str, ...]] = {
    "vram_gb": ("vram_gb", "vram_mb"),
    "price_usd_per_hour": ("price_usd_per_hour", "price_cents_per_hour"),
    "system_ram_gb": ("system_ram_gb", "ram_mb"),
    "scratch_gb": ("scratch_gb", "container_disk_gb"),
    "setup_overhead_minutes": ("setup_minutes", "startup_seconds"),
    "preempt_probability_per_hour": (
        "preempt_probability_per_hour",
        "interrupt_probability_per_hour",
    ),
    "accelerator_count": ("accelerator_count", "gpu_count"),
}


def _normalize_common(observation: RawProviderObservation) -> dict[str, Any]:
    """Validate the *required concepts*, not one provider's spelling of them."""

    raw = observation.raw
    required_concepts = (
        "offer_id",
        "accelerator",
        "vram_gb",
        "price_usd_per_hour",
        "region",
        "preemptible",
    )
    missing = [
        concept
        for concept in required_concepts
        if not any(spelling in raw for spelling in _ALTERNATIVE_SPELLINGS.get(concept, (concept,)))
    ]
    if missing:
        raise PolicyBlocked(
            "OFFER_OBSERVATION_INCOMPLETE",
            f"{observation.provider} observation is missing {', '.join(missing)}",
            provider=observation.provider,
        )
    return raw


def _normalize_octa(observation: RawProviderObservation) -> dict[str, Any]:
    raw = _normalize_common(observation)
    return {
        "provider": observation.provider,
        "offer_id": f"{observation.provider}:{raw['offer_id']}",
        "accelerator": raw["accelerator"],
        "accelerator_count": raw.get("accelerator_count", 1),
        "vram_gb": float(raw["vram_gb"]),
        "system_ram_gb": float(raw.get("system_ram_gb", raw["vram_gb"] * 2)),
        "scratch_gb": float(raw.get("scratch_gb", 100.0)),
        "price_usd_per_hour": float(raw["price_usd_per_hour"]),
        "storage_usd_per_gb_month": float(raw.get("storage_usd_per_gb_month", 0.07)),
        "egress_usd_per_gb": float(raw.get("egress_usd_per_gb", 0.0)),
        "region": raw["region"],
        "preemptible": bool(raw["preemptible"]),
        "preempt_probability_per_hour": float(raw.get("preempt_probability_per_hour", 0.05 if raw["preemptible"] else 0.0)),
        "setup_overhead_minutes": float(raw.get("setup_minutes", 6.0)),
        "container_support": raw.get("container_support", "docker"),
        "trust_class": raw.get("trust_class", "PUBLIC_RESEARCH"),
        "observed_at_epoch_s": observation.observed_at_epoch_s,
        "freshness_window_s": observation.freshness_window_s,
        "normalization_losses": tuple(raw.get("normalization_losses", ())),
    }


def _normalize_runpod(observation: RawProviderObservation) -> dict[str, Any]:
    raw = _normalize_common(observation)
    # RunPod-style surfaces express price in cents per hour and VRAM in MB.
    price_cents = raw.get("price_cents_per_hour")
    price = float(price_cents) / 100.0 if price_cents is not None else float(raw["price_usd_per_hour"])
    vram = raw.get("vram_mb")
    vram_gb = float(vram) / 1024.0 if vram is not None else float(raw["vram_gb"])
    return {
        "provider": observation.provider,
        "offer_id": f"{observation.provider}:{raw['offer_id']}",
        "accelerator": raw["accelerator"],
        "accelerator_count": raw.get("gpu_count", raw.get("accelerator_count", 1)),
        "vram_gb": vram_gb,
        "system_ram_gb": float(raw.get("ram_mb", raw.get("system_ram_gb", vram_gb * 2 * 1024)) / 1024.0)
        if "ram_mb" in raw
        else float(raw.get("system_ram_gb", vram_gb * 2)),
        "scratch_gb": float(raw.get("container_disk_gb", raw.get("scratch_gb", 60.0))),
        "price_usd_per_hour": price,
        "storage_usd_per_gb_month": float(raw.get("storage_usd_per_gb_month", 0.10)),
        "egress_usd_per_gb": float(raw.get("egress_usd_per_gb", 0.0)),
        "region": raw["region"],
        "preemptible": bool(raw["preemptible"]),
        "preempt_probability_per_hour": float(raw.get("interrupt_probability_per_hour", 0.10 if raw["preemptible"] else 0.0)),
        "setup_overhead_minutes": float(raw.get("startup_seconds", 240.0)) / 60.0,
        "container_support": raw.get("container_support", "docker"),
        "trust_class": raw.get("trust_class", "PUBLIC_RESEARCH"),
        "observed_at_epoch_s": observation.observed_at_epoch_s,
        "freshness_window_s": observation.freshness_window_s,
        "normalization_losses": tuple(raw.get("normalization_losses", ())),
    }


def _normalize_local(observation: RawProviderObservation) -> dict[str, Any]:
    raw = _normalize_common(observation)
    return {
        "provider": observation.provider,
        "offer_id": f"{observation.provider}:{raw['offer_id']}",
        "accelerator": raw["accelerator"],
        "accelerator_count": 1,
        "vram_gb": float(raw["vram_gb"]),
        "system_ram_gb": float(raw.get("system_ram_gb", 16.0)),
        "scratch_gb": float(raw.get("scratch_gb", 200.0)),
        "price_usd_per_hour": 0.0,
        "storage_usd_per_gb_month": 0.0,
        "egress_usd_per_gb": 0.0,
        "region": raw["region"],
        "preemptible": False,
        "preempt_probability_per_hour": 0.0,
        "setup_overhead_minutes": 0.5,
        "container_support": raw.get("container_support", "process"),
        "trust_class": raw.get("trust_class", "PRIVATE_OPERATOR"),
        "observed_at_epoch_s": observation.observed_at_epoch_s,
        "freshness_window_s": observation.freshness_window_s,
        "normalization_losses": tuple(raw.get("normalization_losses", ())),
    }


_NORMALIZERS = {
    "_normalize_octa": _normalize_octa,
    "_normalize_runpod": _normalize_runpod,
    "_normalize_local": _normalize_local,
}


def normalize_offer(observation: RawProviderObservation) -> Any:
    """Normalize a provider observation into the shared offer contract."""

    from .resources import ComputeOffer  # circular-safe local import

    adapter = ADAPTERS.get(observation.provider)
    if adapter is None:
        raise PolicyBlocked(
            "PROVIDER_ADAPTER_UNKNOWN",
            f"no adapter for provider {observation.provider!r}; providers are replaceable implementations",
        )
    if adapter.mode not in {"OBSERVE", "SIMULATE"}:
        raise PolicyBlocked(
            "ADAPTER_MODE_REFUSED",
            f"{adapter.name} is not in a read-only observation mode",
        )
    normalized = _NORMALIZERS[adapter.normalize](observation)
    offer = ComputeOffer(
        **normalized,
        adapter=adapter.name,
        raw_observation=observation.to_dict(),
    )
    return offer


__all__ = [
    "ADAPTERS",
    "PROVIDER_OFFER_DOUBLE",
    "ProviderAdapter",
    "RawProviderObservation",
    "normalize_offer",
]
