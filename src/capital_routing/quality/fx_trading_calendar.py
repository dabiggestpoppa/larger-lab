"""
Empirical FX Trading Calendar for MT5 Provider

This module derives the actual trading session calendar from observed
MT5 provider behavior, not from assumptions about market hours.

Calendar ID: mt5_pro_v1
Provider: mt5_pro
Version: 1.0
Effective Date Range: 2015-10-11 through present
Evidence Source: Raw MT5 M5 exports for 10 major pairs
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import pandas as pd
import json
import os


class SessionGroup(Enum):
    """Two distinct session groups observed in MT5 data."""
    GROUP_1_STANDARD = "group_1_standard"  # Mon 00:00 - Fri 23:00 UTC
    GROUP_2_EUR_CROSS = "group_2_eur_cross"  # Mon 00:00 - Fri 19:00 UTC


@dataclass
class SessionSchedule:
    """Trading session schedule for a symbol group."""
    group: SessionGroup
    weekly_open_utc: Tuple[int, int]  # (weekday, hour) - 0=Mon, 6=Sun
    weekly_close_utc: Tuple[int, int]  # (weekday, hour)
    rollover_missing_hours: List[int] = field(default_factory=list)  # Hours typically missing due to rollover
    dst_regime: str = "none"  # "none", "us_eu", "custom"
    documented_full_closures: List[str] = field(default_factory=list)  # Date strings
    documented_partial_closures: List[Dict] = field(default_factory=list)  # {date, hours_missing, reason}
    symbols: List[str] = field(default_factory=list)
    
    def is_trading_hour(self, timestamp: pd.Timestamp) -> bool:
        """Check if a given UTC timestamp falls within trading hours."""
        wd = timestamp.weekday()  # 0=Mon, 6=Sun
        hour = timestamp.hour
        
        if self.group == SessionGroup.GROUP_1_STANDARD:
            # Mon 00:00 to Fri 23:00
            if wd == 0:  # Monday
                return hour >= 0
            elif wd == 4:  # Friday
                return hour <= 23
            elif 1 <= wd <= 3:  # Tue-Thu
                return True
            else:  # Sat, Sun
                return False
        else:  # GROUP_2_EUR_CROSS - Mon 00:00 to Fri 19:00
            if wd == 4:  # Friday
                return hour <= 19
            elif 0 <= wd <= 3:  # Mon-Thu
                return True
            else:  # Fri>19, Sat, Sun
                return False
    
    def get_expected_hours_in_range(self, start: pd.Timestamp, end: pd.Timestamp) -> int:
        """Calculate expected trading hours in a date range."""
        expected = 0
        current = start.floor('h')
        while current <= end:
            if self.is_trading_hour(current):
                expected += 1
            current += timedelta(hours=1)
        return expected


# Empirically derived session schedules from MT5 data
SESSION_SCHEDULES = {
    SessionGroup.GROUP_1_STANDARD: SessionSchedule(
        group=SessionGroup.GROUP_1_STANDARD,
        weekly_open_utc=(0, 0),    # Monday 00:00 UTC
        weekly_close_utc=(4, 23),  # Friday 23:00 UTC
        rollover_missing_hours=[],  # No systematic rollover gaps observed
        dst_regime="none",
        documented_full_closures=[
            "2022-01-01", "2022-04-15", "2022-04-18", "2022-05-30", "2022-07-04", 
            "2022-09-05", "2022-11-24", "2022-12-26",
            "2023-01-02", "2023-04-07", "2023-04-10", "2023-05-29", "2023-07-04", 
            "2023-09-04", "2023-11-23", "2023-12-25",
            "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-27", "2024-07-04", 
            "2024-09-02", "2024-11-28", "2024-12-25",
            "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-26", "2025-07-04", 
            "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-25",
        ],
        documented_partial_closures=[],
        symbols=["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "GBPJPY", "CHFJPY", "GBPCHF"]
    ),
    SessionGroup.GROUP_2_EUR_CROSS: SessionSchedule(
        group=SessionGroup.GROUP_2_EUR_CROSS,
        weekly_open_utc=(0, 0),    # Monday 00:00 UTC
        weekly_close_utc=(4, 19),  # Friday 19:00 UTC
        rollover_missing_hours=[],
        dst_regime="none",
        documented_full_closures=[
            "2022-01-01", "2022-04-15", "2022-04-18", "2022-05-30", "2022-07-04", 
            "2022-09-05", "2022-11-24", "2022-12-26",
            "2023-01-02", "2023-04-07", "2023-04-10", "2023-05-29", "2023-07-04", 
            "2023-09-04", "2023-11-23", "2023-12-25",
            "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-27", "2024-07-04", 
            "2024-09-02", "2024-11-28", "2024-12-25",
            "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-26", "2025-07-04", 
            "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-25",
        ],
        documented_partial_closures=[],
        symbols=["EURGBP", "EURJPY", "EURCHF"]
    )
}

SYMBOL_TO_GROUP = {
    "EURUSD": SessionGroup.GROUP_1_STANDARD,
    "GBPUSD": SessionGroup.GROUP_1_STANDARD,
    "USDJPY": SessionGroup.GROUP_1_STANDARD,
    "USDCHF": SessionGroup.GROUP_1_STANDARD,
    "GBPJPY": SessionGroup.GROUP_1_STANDARD,
    "CHFJPY": SessionGroup.GROUP_1_STANDARD,
    "GBPCHF": SessionGroup.GROUP_1_STANDARD,
    "EURGBP": SessionGroup.GROUP_2_EUR_CROSS,
    "EURJPY": SessionGroup.GROUP_2_EUR_CROSS,
    "EURCHF": SessionGroup.GROUP_2_EUR_CROSS,
}


def get_session_schedule(symbol: str) -> SessionSchedule:
    """Get the session schedule for a symbol."""
    group = SYMBOL_TO_GROUP.get(symbol)
    if group is None:
        raise ValueError(f"Unknown symbol: {symbol}")
    return SESSION_SCHEDULES[group]


def get_expected_trading_hours(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> int:
    """Get expected trading hours for a symbol in a date range."""
    schedule = get_session_schedule(symbol)
    return schedule.get_expected_hours_in_range(start, end)


def is_trading_hour(symbol: str, timestamp: pd.Timestamp) -> bool:
    """Check if a timestamp is a trading hour for the symbol."""
    schedule = get_session_schedule(symbol)
    return schedule.is_trading_hour(timestamp)


def generate_expected_timestamps(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Generate all expected trading timestamps for a symbol in range."""
    schedule = get_session_schedule(symbol)
    timestamps = []
    current = start.floor('h')
    while current <= end:
        if schedule.is_trading_hour(current):
            timestamps.append(current)
        current += timedelta(hours=1)
    return pd.DatetimeIndex(timestamps, tz='UTC')


def load_calendar_metadata() -> Dict:
    """Load calendar metadata for serialization."""
    return {
        "calendar_id": "mt5_pro_v1",
        "provider": "mt5_pro",
        "version": "1.0",
        "effective_date_range": {
            "start": "2015-10-11",
            "end": "present"
        },
        "evidence_source": "Raw MT5 M5 exports for 10 major pairs (2015-2026)",
        "session_groups": {
            "group_1_standard": {
                "weekly_open_utc": "Monday 00:00",
                "weekly_close_utc": "Friday 23:00",
                "symbols": SESSION_SCHEDULES[SessionGroup.GROUP_1_STANDARD].symbols,
                "full_closures": SESSION_SCHEDULES[SessionGroup.GROUP_1_STANDARD].documented_full_closures
            },
            "group_2_eur_cross": {
                "weekly_open_utc": "Monday 00:00",
                "weekly_close_utc": "Friday 19:00",
                "symbols": SESSION_SCHEDULES[SessionGroup.GROUP_2_EUR_CROSS].symbols,
                "full_closures": SESSION_SCHEDULES[SessionGroup.GROUP_2_EUR_CROSS].documented_full_closures
            }
        },
        "symbol_to_group": {k: v.value for k, v in SYMBOL_TO_GROUP.items()}
    }


if __name__ == "__main__":
    # Test the calendar
    for sym in ["EURUSD", "EURGBP", "GBPUSD", "EURJPY"]:
        schedule = get_session_schedule(sym)
        print(f"{sym}: {schedule.group.value}")
        print(f"  Open: {schedule.weekly_open_utc}, Close: {schedule.weekly_close_utc}")
        
        # Test a few timestamps
        test_times = [
            pd.Timestamp("2023-07-03 00:00", tz="UTC"),  # Monday
            pd.Timestamp("2023-07-07 23:00", tz="UTC"),  # Friday
            pd.Timestamp("2023-07-08 12:00", tz="UTC"),  # Saturday
            pd.Timestamp("2023-07-09 20:00", tz="UTC"),  # Sunday
        ]
        for t in test_times:
            print(f"  {t}: trading={schedule.is_trading_hour(t)}")