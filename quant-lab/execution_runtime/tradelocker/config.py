"""QL-EXEC-R5 — TradeLocker ``/config`` snapshot (provider truth).

The TradeLocker API returns dynamic column layouts and per-route rate limits
from ``/trade/config``. We NEVER hardcode column indices: every positions /
orders / executions / account-state row is resolved by column id from this
snapshot, and the snapshot is version-hashed so a config change is a visible
version bump (config drift detection).
"""
from __future__ import annotations

import hashlib
import json

from .types import TradeLockerConfigSnapshot, TradeLockerRateLimit


class TradeLockerConfigParser:
    """Parses the raw ``/config`` ``d`` payload into a hashed snapshot."""

    # object_name -> keys under which the column list may appear
    _COLUMN_OBJECTS = (
        "ordersConfig",
        "ordersHistoryConfig",
        "positionsConfig",
        "filledOrdersConfig",
        "executionsConfig",
        "accountDetailsConfig",
        "instrumentsConfig",
        "priceHistoryConfig",
    )

    def parse(self, d: dict) -> TradeLockerConfigSnapshot:
        columns: dict[str, tuple[str, ...]] = {}
        for obj in self._COLUMN_OBJECTS:
            entry = d.get(obj) if isinstance(d, dict) else None
            if isinstance(entry, dict) and isinstance(entry.get("columns"), list):
                cols = []
                for c in entry["columns"]:
                    if isinstance(c, dict) and c.get("id") is not None:
                        cols.append(str(c["id"]))
                columns[obj] = tuple(cols)
            else:
                columns[obj] = ()

        limits = tuple(d.get("limits") or ())
        rate_limits = tuple(self._parse_rate_limits(d.get("rateLimits") or ()))

        canonical = json.dumps(
            {
                "columns": columns,
                "limits": limits,
                "rateLimits": [rl.__dict__ for rl in rate_limits],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        version_hash = "cfg_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

        return TradeLockerConfigSnapshot(
            columns=columns,
            limits=limits,
            rate_limits=rate_limits,
            version_hash=version_hash,
        )

    @staticmethod
    def _parse_rate_limits(raw: list) -> list:
        out = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            route = item.get("rateLimitType")
            limit = item.get("limit")
            if route is None or limit is None:
                continue
            try:
                seconds = int(item.get("seconds", 60))
            except (TypeError, ValueError):
                seconds = 60
            out.append(
                TradeLockerRateLimit(
                    route_name=str(route),
                    limit=int(limit),
                    seconds=max(seconds, 1),
                )
            )
        return out
