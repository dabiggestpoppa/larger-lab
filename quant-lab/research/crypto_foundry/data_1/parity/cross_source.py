"""
Crypto Foundry DATA-1: Cross-Source Parity

Descriptive comparison between:
- Binance spot (BTCUSDT/ETHUSDT)
- Hyperliquid perp (BTC-PERP/ETH-PERP)

DATA QUALITY ONLY. No alpha interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ParityReport:
    """Parity comparison between two data sources."""
    comparison_name: str
    source_a_name: str
    source_b_name: str
    overlap_start: Optional[str] = None
    overlap_end: Optional[str] = None
    source_a_count: int = 0
    source_b_count: int = 0
    overlapping_timestamps: int = 0
    timestamp_alignment_pct: float = 0.0
    median_basis_bps: float = 0.0
    p95_basis_bps: float = 0.0
    max_basis_bps: float = 0.0
    correlation: float = 0.0
    source_a_only_gaps: int = 0
    source_b_only_gaps: int = 0
    extreme_divergence_count: int = 0
    extreme_divergence_threshold_bps: float = 100.0
    status: str = "VALID"
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CrossSourceParity:
    """Compare data quality between Binance and Hyperliquid."""

    def compare_price_series(
        self,
        source_a_records: List[Dict],  # Binance
        source_b_records: List[Dict],  # Hyperliquid
        source_a_name: str = "Binance",
        source_b_name: str = "Hyperliquid",
        comparison_name: str = "BTC_spot_vs_perp",
        price_field_a: str = "close",
        price_field_b: str = "close",
        ts_field: str = "event_time_utc",
        time_tolerance_seconds: int = 300,  # 5 min tolerance
        extreme_threshold_bps: float = 100.0,
    ) -> ParityReport:
        """Compare two price series by timestamp alignment."""
        # Extract timestamps and prices
        a_by_ts: Dict[str, float] = {}
        for r in source_a_records:
            if "error" in r:
                continue
            ts = r.get(ts_field, "")
            price = r.get(price_field_a)
            if ts and price and isinstance(price, (int, float)) and price > 0:
                a_by_ts[_normalize_ts(ts)] = price

        b_by_ts: Dict[str, float] = {}
        for r in source_b_records:
            if "error" in r:
                continue
            ts = r.get(ts_field, "")
            price = r.get(price_field_b)
            if ts and price and isinstance(price, (int, float)) and price > 0:
                b_by_ts[_normalize_ts(ts)] = price

        a_timestamps = sorted(a_by_ts.keys())
        b_timestamps = sorted(b_by_ts.keys())

        # Find overlapping timestamps
        a_set = set(a_timestamps)
        b_set = set(b_timestamps)
        overlap = a_set & b_set

        # For timestamps that don't match exactly, find closest within tolerance.
        # Use bisect on sorted float timestamps for O(log n) nearest lookup.
        import bisect

        b_sorted = sorted(b_timestamps, key=_ts_to_float)
        b_float = [_ts_to_float(ts) for ts in b_sorted]
        fuzzy_matches = []
        a_only = []
        b_only = []

        for a_ts in a_timestamps:
            if a_ts in overlap:
                fuzzy_matches.append((a_ts, a_ts))
                continue
            a_f = _ts_to_float(a_ts)
            idx = bisect.bisect_left(b_float, a_f)
            best_diff = float("inf")
            best_b = None
            for cand in (idx - 1, idx):
                if 0 <= cand < len(b_sorted):
                    diff = abs(b_float[cand] - a_f)
                    if diff < best_diff:
                        best_diff = diff
                        best_b = b_sorted[cand]
            if best_diff <= time_tolerance_seconds and best_b is not None:
                fuzzy_matches.append((a_ts, best_b))
            else:
                a_only.append(a_ts)

        b_matched = set(m[1] for m in fuzzy_matches)
        b_only = [ts for ts in b_timestamps if ts not in b_matched]

        # Calculate basis
        bases_bps = []
        prices_a = []
        prices_b = []

        for a_ts, b_ts in fuzzy_matches:
            pa = a_by_ts.get(a_ts, 0)
            pb = b_by_ts.get(b_ts, 0)
            if pa > 0 and pb > 0:
                basis_bps = (pb - pa) / pa * 10000
                bases_bps.append(basis_bps)
                prices_a.append(pa)
                prices_b.append(pb)

        bases_arr = np.array(bases_bps) if bases_bps else np.array([0.0])
        pa_arr = np.array(prices_a) if prices_a else np.array([0.0])
        pb_arr = np.array(prices_b) if prices_b else np.array([0.0])

        # Correlation
        corr = 0.0
        if len(pa_arr) > 1 and np.std(pa_arr) > 0 and np.std(pb_arr) > 0:
            corr = float(np.corrcoef(pa_arr, pb_arr)[0, 1])

        extreme_count = int(np.sum(np.abs(bases_arr) > extreme_threshold_bps))

        # Determine overlap time range
        overlap_start = min(overlap) if overlap else None
        overlap_end = max(overlap) if overlap else None

        total_a = len(a_timestamps)
        total_b = len(b_timestamps)
        overlap_count = len(overlap)

        # Alignment percentage
        alignment_pct = overlap_count / max(total_a, total_b) * 100 if max(total_a, total_b) > 0 else 0

        report = ParityReport(
            comparison_name=comparison_name,
            source_a_name=source_a_name,
            source_b_name=source_b_name,
            overlap_start=overlap_start,
            overlap_end=overlap_end,
            source_a_count=total_a,
            source_b_count=total_b,
            overlapping_timestamps=overlap_count,
            timestamp_alignment_pct=round(alignment_pct, 2),
            median_basis_bps=round(float(np.median(bases_arr)), 2),
            p95_basis_bps=round(float(np.percentile(np.abs(bases_arr), 95)), 2),
            max_basis_bps=round(float(np.max(np.abs(bases_arr))), 2),
            correlation=round(corr, 6),
            source_a_only_gaps=len(a_only),
            source_b_only_gaps=len(b_only),
            extreme_divergence_count=extreme_count,
            extreme_divergence_threshold_bps=extreme_threshold_bps,
            status="VALID" if len(bases_bps) > 10 else "INSUFFICIENT_OVERLAP",
        )

        if overlap_count == 0:
            report.notes.append("No exact timestamp overlap found")
        if len(bases_bps) > 0 and report.median_basis_bps > 50:
            report.notes.append(f"Large median basis ({report.median_basis_bps} bps) — may reflect spot vs perp spread")

        return report


def _normalize_ts(ts) -> str:
    """Normalize timestamp to string for comparison."""
    if isinstance(ts, (int, float)):
        return str(int(ts))
    return str(ts)


def _ts_to_float(ts) -> float:
    """Convert timestamp to float."""
    from datetime import datetime, timezone
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0
    return 0.0
