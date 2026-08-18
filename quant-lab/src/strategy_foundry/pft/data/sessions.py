"""Session-structure measurement and expected-closure rules.

The weekly bar pattern is measured empirically from each series (bars per
day, daily gap location, weekend structure). Expected-closed periods are
derived from the measured pattern, never assumed.
"""

from __future__ import annotations

import pandas as pd


def measure_session_structure(frame: pd.DataFrame, expected_bars_per_day: int | None = None) -> dict:
    """Measure bars/day, gap locations and weekend structure of a series.

    The gap analysis is adaptive to the bar interval (median diff) and
    records the UTC hour at which trading RESUMES after a gap (the
    post-gap bar's hour-of-day), which reveals session open hours.
    """
    from collections import Counter

    idx = frame.index
    if len(idx) < 3:
        return {"median_bars_per_day": 0.0, "p90_bars_per_day": 0.0,
                "weekend_fraction": 0.0, "top_gap_resume_hours": [],
                "weekday_gap_frac": 0.0}
    bars_per_day = idx.to_series().dt.date.value_counts()
    median_bpd = float(bars_per_day.median()) if len(bars_per_day) else 0.0
    diffs = idx.to_series().diff()
    median_diff = float(diffs.median().total_seconds())
    threshold = pd.Timedelta(seconds=max(median_diff * 1.5, 60))
    gaps = diffs[diffs > threshold]
    post_gap = idx.to_series().loc[gaps.index]
    resume_hours = Counter(int(ts.hour) for ts in post_gap)
    weekday_gap_frac = float((diffs > threshold).mean())
    dow = idx.dayofweek
    weekend_frac = float(((dow >= 5).sum()) / max(len(idx), 1))
    return {
        "median_bars_per_day": median_bpd,
        "p90_bars_per_day": float(bars_per_day.quantile(0.90)) if len(bars_per_day) else 0.0,
        "weekend_fraction": weekend_frac,
        "top_gap_resume_hours": [{"resume_utc_hour": k, "count": v}
                                 for k, v in resume_hours.most_common(6)],
        "weekday_gap_frac": weekday_gap_frac,
        "expected_bars_per_day": expected_bars_per_day,
    }


def measure_hourly_coverage(frame: pd.DataFrame) -> dict:
    """Weekday and weekend bar frequency by UTC hour-of-day."""
    idx = frame.index.to_series()
    weekday = idx[idx.dt.dayofweek < 5]
    weekend = idx[idx.dt.dayofweek >= 5]
    wd_hist = weekday.dt.hour.value_counts().sort_index()
    we_hist = weekend.dt.hour.value_counts().sort_index()
    return {
        "weekday_hour_counts": {int(k): int(v) for k, v in wd_hist.items()},
        "weekend_hour_counts": {int(k): int(v) for k, v in we_hist.items()},
    }


def derive_weekday_closed(hour_counts: dict, min_fraction: float = 0.10) -> list:
    """Hours whose weekday bar frequency is below min_fraction of the busiest
    hour are treated as expected-closed. Deterministic from data."""
    if not hour_counts:
        return []
    peak = max(hour_counts.values())
    return sorted(h for h, count in hour_counts.items() if count < min_fraction * peak)


def derive_expected_closed(
    session: dict,
    weekday_closed_utc_hours: set[int],
    weekend_start_utc: int = 48,
    weekend_end_utc: int = 48,
) -> dict:
    """Derive an expected-closed rule from measured structure.

    weekday_closed_utc_hours: set of UTC hours (bucket start) when the
    market is closed on weekdays (e.g. Brent's measured daily gap).
    weekend_start_utc / weekend_end_utc: (day_index*24 + hour) marks; the
    default 48/48 means "no weekend closure rule" (weeks treated as
    7 continuous days where only weekday gaps apply).
    """
    return {
        "weekday_closed_utc_hours": sorted(weekday_closed_utc_hours),
        "weekend_start": weekend_start_utc,
        "weekend_end": weekend_end_utc,
        "measured_median_bars_per_day": session.get("median_bars_per_day"),
    }


def is_expected_closed(dt_utc: pd.Timestamp, rule: dict) -> bool:
    """True when a canonical slot falls in the measured closed period."""
    weekday = dt_utc.dayofweek
    hour = dt_utc.hour
    if weekday < 5:
        return hour in set(rule.get("weekday_closed_utc_hours", []))
    slot_index = weekday * 24 + hour
    weekend_start = rule.get("weekend_start", 48)
    weekend_end = rule.get("weekend_end", 48)
    if weekend_start < weekend_end and weekend_start <= slot_index < weekend_end:
        return True
    if weekend_start > weekend_end:  # wraparound weekend
        if slot_index >= weekend_start or slot_index < weekend_end:
            return True
    return False
