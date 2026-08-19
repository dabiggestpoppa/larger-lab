"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · STATS
====================================================

Historical cadence distributions + rolling-activity classification.

Distributions are built from the INDEPENDENT replay of the frozen
development window (the same canonical replay that reproduces the sealed
405/194 reference counts). They are:

  * deterministic — pure functions of the replayed entry times
  * diagnostic only — they NEVER alter strategy parameters, thresholds,
    sessions, capital, or execution in any way (see test 27)

Frequency monitoring is diagnostic. Low frequency is never permission to
lower the z threshold, change the exit, force a trade, or change capital.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from tb_audit_core import (
    CONTROL_STRATEGY_ID,
    PRIMARY_STRATEGY_ID,
    STRATEGY_IDS,
)

MIN_ROLLING_WEEKS = 4      # fewer complete weeks => INSUFFICIENT_FORWARD_HISTORY


def _isoweek_key(ts: datetime) -> str:
    iso = ts.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def week_counts(entry_times: List[datetime]) -> Dict[str, int]:
    c: Counter = Counter()
    for t in entry_times:
        c[_isoweek_key(t)] += 1
    return dict(c)


def month_counts(entry_times: List[datetime]) -> Dict[str, int]:
    c: Counter = Counter()
    for t in entry_times:
        c[t.strftime("%Y-%m")] += 1
    return dict(c)


def _pct(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    # linear interpolation on sorted list, index = p*(n-1)
    n = len(sorted_vals)
    pos = p * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def weekly_distribution(entry_times: List[datetime]) -> dict:
    counts = sorted(week_counts(entry_times).values())
    frac = Counter()
    for c in counts:
        frac[min(c, 4)] += 1
    n = len(counts) or 1
    return {
        "weeks": len(counts),
        "mean": round(statistics.mean(counts), 3) if counts else 0.0,
        "median": float(statistics.median(counts)) if counts else 0.0,
        "p5": round(_pct(counts, 0.05), 3),
        "p25": round(_pct(counts, 0.25), 3),
        "p75": round(_pct(counts, 0.75), 3),
        "p95": round(_pct(counts, 0.95), 3),
        "max": max(counts) if counts else 0,
        "frac_weeks_0": round(frac[0] / n, 3),
        "frac_weeks_1": round(frac[1] / n, 3),
        "frac_weeks_2": round(frac[2] / n, 3),
        "frac_weeks_3": round(frac[3] / n, 3),
        "frac_weeks_4plus": round(frac[4] / n, 3),
    }


def monthly_distribution(entry_times: List[datetime]) -> dict:
    counts = sorted(month_counts(entry_times).values())
    return {
        "months": len(counts),
        "mean": round(statistics.mean(counts), 3) if counts else 0.0,
        "median": float(statistics.median(counts)) if counts else 0.0,
        "p5": round(_pct(counts, 0.05), 3),
        "p25": round(_pct(counts, 0.25), 3),
        "p75": round(_pct(counts, 0.75), 3),
        "p95": round(_pct(counts, 0.95), 3),
        "max": max(counts) if counts else 0,
    }


class ActivityClassification(str):
    NORMAL = "NORMAL_ACTIVITY"
    LOW_NORMAL = "LOW_BUT_HISTORICALLY_NORMAL"
    UNUSUALLY_LOW = "UNUSUALLY_LOW_ACTIVITY"
    UNUSUALLY_HIGH = "UNUSUALLY_HIGH_ACTIVITY"
    INSUFFICIENT = "INSUFFICIENT_FORWARD_HISTORY"


def classify_count(count: int, dist: dict) -> str:
    """Band a single weekly count against the historical distribution."""
    if dist.get("weeks", 0) < 1:
        return ActivityClassification.INSUFFICIENT
    if count > dist["p95"]:
        return ActivityClassification.UNUSUALLY_HIGH
    if count < dist["p5"]:
        return ActivityClassification.UNUSUALLY_LOW
    if count < dist["p25"]:
        return ActivityClassification.LOW_NORMAL
    return ActivityClassification.NORMAL


def rolling_activity(historical_entries: List[datetime],
                     audit_entries: List[datetime],
                     audit_week_start: datetime) -> dict:
    """Current week + trailing 4/8/12-week counts vs historical distribution.

    historical_entries: entry datetimes from the frozen dev-window replay.
    audit_entries:      entry datetimes from THIS audit's replay window(s).
    audit_week_start:   Monday of the current audited week.
    """
    dist = weekly_distribution(historical_entries)
    # rolling context: all entries within the trailing windows (historical +
    # audit period). Only counts of COMPLETE weeks are used for trailing
    # windows (a partial current week would bias them).
    ws = audit_week_start
    all_entries = list(historical_entries) + list(audit_entries)

    def trailing(weeks: int, end: datetime) -> Optional[int]:
        start = end - timedelta(weeks=weeks)
        n = 0
        for t in all_entries:
            if start <= t < end:
                n += 1
        return n

    cur = sum(1 for t in audit_entries if ws <= t < ws + timedelta(days=7))
    out = {
        "current_week": cur,
        "current_week_class": classify_count(cur, dist),
        "dist": dist,
    }
    for w in (4, 8, 12):
        end = ws                      # trailing windows END at this week's Monday
        n = trailing(w, end)
        complete = [t for t in all_entries if end - timedelta(weeks=w) <= t < end]
        # weeks with data: approximate complete-week count by unique weeks
        wk_keys = {_isoweek_key(t) for t in complete}
        if len(wk_keys) < MIN_ROLLING_WEEKS:
            out[f"trailing_{w}_week"] = n
            out[f"trailing_{w}_week_class"] = \
                ActivityClassification.INSUFFICIENT
            out[f"trailing_{w}_week_weeks_covered"] = len(wk_keys)
        else:
            out[f"trailing_{w}_week"] = n
            out[f"trailing_{w}_week_class"] = classify_count(n, dist)
            out[f"trailing_{w}_week_weeks_covered"] = len(wk_keys)
    return out


class Cadence:
    """Per-strategy historical cadence (deterministic, dev-window derived)."""

    def __init__(self, dev_entry_times: Dict[str, List[datetime]]):
        self.entries = dev_entry_times
        self._weekly = {s: weekly_distribution(v) for s, v in entries_items(dev_entry_times)}
        self._monthly = {s: monthly_distribution(v) for s, v in entries_items(dev_entry_times)}

    def weekly(self, strategy_id: str) -> dict:
        return self._weekly[strategy_id]

    def monthly(self, strategy_id: str) -> dict:
        return self._monthly[strategy_id]

    def context(self, audit_entries: Dict[str, List[datetime]],
                audit_week_start: datetime) -> dict:
        out = {}
        for s in STRATEGY_IDS:
            out[s] = rolling_activity(
                self.entries.get(s, []), audit_entries.get(s, []),
                audit_week_start)
            out[s]["weekly_distribution"] = self.weekly(s)
            out[s]["monthly_distribution"] = self.monthly(s)
        return out


def entries_items(d: Dict[str, List[datetime]]):
    return [(k, v) for k, v in d.items() if k in STRATEGY_IDS]
