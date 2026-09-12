"""Probe planner (bloc_02/01 §13-14, 04 §9, T2-PLAN-01..05).

Deterministic plan construction:

1. RECENT CONTROL first — a hard recent-control failure suppresses deep-history
   probing for that scope (F2.7).
2. Exact target checkpoints (2021/2022/2024/2026).
3. Bounded earliest-history binary search between the last successful era and
   the first failed era, stopping at configured precision (month).
4. Provider-specific unsupported granularities never generate requests.

Plans are deterministic from config + provider capability hints (T2-PLAN-05):
no hash-order iteration, fixed ordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .._paths import CONFIG_DIR
from ..contracts.enums import SensorFamily
from .enums import AccessMode, Granularity, QueryMode
from .models import CapabilityProbeRequest

DEFAULT_CHECKPOINT_CONFIG_PATH = CONFIG_DIR / "historical_checkpoints.yaml"

RECENT_CONTROL_ERA = "RECENT_CONTROL"

WINDOW_PARSER: dict[str, timedelta] = {
    "1m": timedelta(hours=24),
    "5m": timedelta(hours=24),
    "15m": timedelta(hours=24),
    "1h": timedelta(days=7),
    "4h": timedelta(days=7),
    "1d": timedelta(days=30),
    "RAW_EVENT": timedelta(hours=1),
    "BOOK_SNAPSHOT": timedelta(hours=1),
}


class EraCheckpoint(BaseModel):
    """One named historical checkpoint."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    checkpoint_date: datetime


class HistoricalCheckpointConfig(BaseModel):
    """Frozen checkpoint matrix (04 §9 / T2-HIST-01)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    eras: list[EraCheckpoint] = Field(min_length=4)
    recent_control: str = RECENT_CONTROL_ERA
    window_sizes: dict[str, str] = Field(default_factory=dict)
    boundary_search: dict[str, object] = Field(default_factory=dict)

    def era_names(self) -> list[str]:
        return [era.name for era in self.eras] + [RECENT_CONTROL_ERA]

    def window_for(self, granularity: Granularity) -> timedelta:
        value = self.window_sizes.get(granularity.value)
        if value is None:
            return WINDOW_PARSER.get(granularity.value, timedelta(hours=1))
        return _parse_window(value)

    def boundary_precision(self) -> str:
        return str(self.boundary_search.get("precision", "month"))

    def boundary_max_probes(self) -> int:
        return int(self.boundary_search.get("max_probes", 12))


def _parse_window(value: str) -> timedelta:
    """Parse window strings like '24h', '7d', '30d'."""
    unit = value[-1]
    amount = int(value[:-1])
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    raise ValueError(f"unsupported window unit in {value!r}")


def load_historical_checkpoints(path: Path | None = None) -> HistoricalCheckpointConfig:
    config_path = path or DEFAULT_CHECKPOINT_CONFIG_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return HistoricalCheckpointConfig.model_validate(data)


@dataclass(frozen=True)
class ProbePlanStep:
    """One planned request plus its era label and ordering key."""

    era: str
    order: int
    request: CapabilityProbeRequest

    @property
    def probe_id(self) -> str:
        parts = [
            self.request.provider_id.lower(),
            self.request.sensor_family.value.lower().replace("mechanical_", ""),
            self.request.instrument_native.lower(),
            self.era.lower(),
            self.request.requested_granularity.value.lower(),
        ]
        return "_".join(parts)


@dataclass
class ProbePlan:
    """Ordered plan; recent control first, then historical eras."""

    steps: list[ProbePlanStep] = field(default_factory=list)

    def recent_control_steps(self) -> list[ProbePlanStep]:
        return [s for s in self.steps if s.era == RECENT_CONTROL_ERA]

    def historical_steps(self) -> list[ProbePlanStep]:
        return [s for s in self.steps if s.era != RECENT_CONTROL_ERA]


def recent_control_date(now: datetime | None = None) -> datetime:
    """Runtime recent-control date (today, UTC)."""
    return (now or datetime.now(UTC)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _checkpoint_window(
    checkpoint: datetime, granularity: Granularity, config: HistoricalCheckpointConfig
) -> tuple[datetime, datetime]:
    window = config.window_for(granularity)
    return checkpoint, checkpoint + window


def build_probe_request(
    provider_id: str,
    sensor_family: SensorFamily,
    venue_market: str,
    instrument_native: str,
    canonical_asset_hint: str | None,
    checkpoint_date: datetime,
    granularity: Granularity,
    access_mode: AccessMode,
    query_mode: QueryMode,
    probe_run_id: str,
    config: HistoricalCheckpointConfig,
    era: str = "",
) -> CapabilityProbeRequest:
    """Build one windowed probe request around a checkpoint date.

    The era label is stamped into provider_hints so every attempt record is
    traceable to the checkpoint it probes (RECENT_CONTROL / 2021 / ...).
    """
    start, end = _checkpoint_window(checkpoint_date, granularity, config)
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": provider_id,
            "sensor_family": sensor_family,
            "venue_market": venue_market,
            "instrument_native": instrument_native,
            "canonical_asset_hint": canonical_asset_hint,
            "requested_start": start,
            "requested_end": end,
            "requested_granularity": granularity,
            "access_mode": access_mode,
            "query_mode": query_mode,
            "probe_run_id": probe_run_id,
            "provider_hints": {"era": era},
        }
    )


@dataclass(frozen=True)
class ProbeTarget:
    """One provider/sensor scope to plan (config-driven)."""

    provider_id: str
    sensor_family: SensorFamily
    venue_market: str
    instruments: tuple[str, ...]
    asset_hints: tuple[str | None, ...]
    granularities: tuple[Granularity, ...]
    access_mode: AccessMode
    query_mode: QueryMode
    supported_granularities: frozenset[Granularity] = frozenset()


def plan_probe_matrix(
    target: ProbeTarget,
    probe_run_id: str,
    config: HistoricalCheckpointConfig,
    now: datetime | None = None,
) -> ProbePlan:
    """Deterministic plan: recent control + the four frozen eras.

    Recent control comes first (T2-PLAN-01).  Granularities not in the
    provider's supported set never generate requests (T2-PLAN-04).  Ordering
    is fixed by (era-order, instrument, granularity) — never dict-hash order
    (T2-PLAN-05).
    """
    plan = ProbePlan()
    era_order = {
        RECENT_CONTROL_ERA: 0,
        **{era.name: i + 1 for i, era in enumerate(config.eras)},
    }
    eras_in_order = [RECENT_CONTROL_ERA] + [e.name for e in config.eras]
    order = 0
    granularities = [
        g for g in target.granularities if g in target.supported_granularities
    ] or list(target.granularities)
    for era in eras_in_order:
        checkpoint = (
            recent_control_date(now)
            if era == RECENT_CONTROL_ERA
            else next(e.checkpoint_date for e in config.eras if e.name == era)
        )
        for instrument, hint in zip(target.instruments, target.asset_hints, strict=True):
            for granularity in granularities:
                request = build_probe_request(
                    provider_id=target.provider_id,
                    sensor_family=target.sensor_family,
                    venue_market=target.venue_market,
                    instrument_native=instrument,
                    canonical_asset_hint=hint,
                    checkpoint_date=checkpoint,
                    granularity=granularity,
                    access_mode=target.access_mode,
                    query_mode=target.query_mode,
                    probe_run_id=probe_run_id,
                    config=config,
                    era=era,
                )
                plan.steps.append(
                    ProbePlanStep(era=era, order=order, request=request)
                )
                order += 1
    plan.steps.sort(key=lambda s: (era_order[s.era], s.order))
    return plan


def plan_earliest_history_search(
    provider_id: str,
    sensor_family: SensorFamily,
    venue_market: str,
    instrument_native: str,
    canonical_asset_hint: str | None,
    granularity: Granularity,
    access_mode: AccessMode,
    query_mode: QueryMode,
    probe_run_id: str,
    config: HistoricalCheckpointConfig,
    era_successes: dict[str, bool],
) -> list[CapabilityProbeRequest]:
    """Bounded binary search for the earliest-verified-history boundary.

    Uses the era probe results: the boundary lies between the newest
    successful era and the oldest failed era.  Search proceeds by month steps
    and stops at configured precision / max probes (T2-PLAN-03).
    """
    ordered = list(config.eras)  # chronological (config order)
    successes = [era.name for era in ordered if era_successes.get(era.name)]
    if not successes:
        return []
    newest_success = max(
        (era for era in ordered if era.name in successes),
        key=lambda e: e.checkpoint_date,
    )
    failed_after = [
        era
        for era in ordered
        if era.checkpoint_date > newest_success.checkpoint_date
        and not era_successes.get(era.name)
    ]
    upper = min(
        (era.checkpoint_date for era in failed_after),
        default=datetime.now(UTC),
    )
    lower = newest_success.checkpoint_date
    probes: list[CapabilityProbeRequest] = []
    precision = config.boundary_precision()
    max_probes = config.boundary_max_probes()
    step = timedelta(days=30 if precision == "month" else 90)
    cursor = lower
    while cursor < upper and len(probes) < max_probes:
        cursor = min(cursor + step, upper)
        if cursor >= upper:
            break
        probes.append(
            build_probe_request(
                provider_id=provider_id,
                sensor_family=sensor_family,
                venue_market=venue_market,
                instrument_native=instrument_native,
                canonical_asset_hint=canonical_asset_hint,
                checkpoint_date=cursor,
                granularity=granularity,
                access_mode=access_mode,
                query_mode=query_mode,
                probe_run_id=probe_run_id,
                config=config,
                era="BOUNDARY",
            )
        )
    return probes
