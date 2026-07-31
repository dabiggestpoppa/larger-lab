"""
Phase 1.2: No-Trash Structural Firewall
=========================================
Crypto-specific structural validity filter.
Runs BEFORE any clustering or backtesting.

Rejects assets that lack the liquidity depth to sustain atomic resolution.
80% of crypto assets fail this filter.

Firewall Criteria:
  1. Age >= 180 days (proven structure)
  2. Daily volume >= $10M (real liquidity, not wash)
  3. Top-3 book depth >= 0.5% (manipulation resistance)
  4. Abs funding rate < 0.1% (not in mania/panic regime)
  5. Max data gap < 4 hours (data integrity)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pandas as pd


class RejectReason(Enum):
    AGE = "REJECT: Age < 180 days — unproven structure"
    VOLUME = "REJECT: Daily volume < $10M — illiquid/wash"
    DEPTH = "REJECT: Book depth < 0.5% — manipulation risk"
    FUNDING = "REJECT: Funding rate > 0.1% — mania/panic regime"
    GAPS = "REJECT: Data gap > 4 hours — data integrity"
    INSUFFICIENT_SESSIONS = "REJECT: < 60 valid Asian sessions"


@dataclass
class FirewallResult:
    symbol: str
    is_valid: bool
    reason: str
    details: dict = field(default_factory=dict)


@dataclass
class FirewallConfig:
    min_age_days: int = 180
    min_daily_vol_usd: float = 10_000_000
    min_book_depth_pct: float = 0.005
    max_funding_rate: float = 0.001
    max_gap_hours: int = 4
    min_sessions: int = 60


class NoTrashFirewall:
    """
    Structural validity filter for crypto assets.
    Runs BEFORE K-Means or backtesting.
    """

    def __init__(self, config: FirewallConfig | None = None):
        self.config = config or FirewallConfig()

    def check(
        self,
        symbol: str,
        metadata: dict,
        ohlcv_df: pd.DataFrame,
    ) -> FirewallResult:
        """
        Run all 5 firewall checks.
        Returns FirewallResult with pass/fail + reason.
        """
        cfg = self.config

        # 1. Age check
        age_days = metadata.get("age_days", 0)
        if age_days < cfg.min_age_days:
            return FirewallResult(symbol, False, RejectReason.AGE.value,
                                 {"age_days": age_days, "min": cfg.min_age_days})

        # 2. Volume check
        daily_vol = metadata.get("daily_volume_usd", 0)
        if daily_vol < cfg.min_daily_vol_usd:
            return FirewallResult(symbol, False, RejectReason.VOLUME.value,
                                 {"daily_vol": daily_vol, "min": cfg.min_daily_vol_usd})

        # 3. Book depth check
        depth = metadata.get("book_depth_pct", 0)
        if depth < cfg.min_book_depth_pct:
            return FirewallResult(symbol, False, RejectReason.DEPTH.value,
                                 {"depth": depth, "min": cfg.min_book_depth_pct})

        # 4. Funding rate check
        funding = abs(metadata.get("funding_rate", 0))
        if funding > cfg.max_funding_rate:
            return FirewallResult(symbol, False, RejectReason.FUNDING.value,
                                 {"funding": funding, "max": cfg.max_funding_rate})

        # 5. Data gap check
        if ohlcv_df.index.is_monotonic_increasing:
            diffs = ohlcv_df.index.to_series().diff()
        else:
            diffs = ohlcv_df.sort_index().index.to_series().diff()
        max_gap = diffs.max()
        if max_gap > pd.Timedelta(hours=cfg.max_gap_hours):
            return FirewallResult(symbol, False, RejectReason.GAPS.value,
                                 {"max_gap": str(max_gap), "max_hours": cfg.max_gap_hours})

        return FirewallResult(symbol, True, "VALID — passes all structural checks",
                             {"age_days": age_days, "daily_vol": daily_vol})


def run_firewall_batch(
    assets: list[dict],
    data_dir: Path | None = None,
) -> tuple[list[FirewallResult], list[FirewallResult]]:
    """
    Run firewall on multiple assets.
    assets: list of {"symbol": str, "metadata": dict, "csv_path": str}
    Returns (passed, rejected) lists.
    """
    firewall = NoTrashFirewall()
    passed, rejected = [], []

    for asset in assets:
        symbol = asset["symbol"]
        meta = asset["metadata"]
        csv_path = asset.get("csv_path")

        df = None
        if csv_path:
            try:
                df = pd.read_csv(csv_path, parse_dates=["dt"]).set_index("dt").sort_index()
            except Exception:
                df = pd.DataFrame()

        if df is None or df.empty:
            result = FirewallResult(symbol, False, "REJECT: Cannot load data")
            rejected.append(result)
            continue

        result = firewall.check(symbol, meta, df)
        if result.is_valid:
            passed.append(result)
        else:
            rejected.append(result)

    print(f"\n🔥 No-Trash Firewall Results:")
    print(f"   Passed:  {len(passed)}")
    print(f"   Rejected: {len(rejected)}")
    for r in rejected:
        print(f"     ❌ {r.symbol}: {r.reason}")

    return passed, rejected


if __name__ == "__main__":
    # Demo with sample metadata
    firewall = NoTrashFirewall()

    sample_meta = {
        "age_days": 365,
        "daily_volume_usd": 50_000_000,
        "book_depth_pct": 0.008,
        "funding_rate": 0.0005,
    }

    # Create a minimal valid DataFrame
    idx = pd.date_range("2024-01-01", periods=1000, freq="5min", tz="UTC")
    df = pd.DataFrame({
        "open": range(1000), "high": range(1, 1001),
        "low": range(-1, 999), "close": range(1000),
    }, index=idx)

    result = firewall.check("BTCUSD", sample_meta, df)
    print(f"\nBTCUSD: {'✅' if result.is_valid else '❌'} {result.reason}")
