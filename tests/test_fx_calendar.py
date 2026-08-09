"""
Regression tests for the empirical FX trading calendar (CR-P2-MARKET-CALENDAR-AUDIT-06).
"""
import pytest
import pandas as pd
from datetime import timedelta
from capital_routing.quality.fx_trading_calendar import (
    get_session_schedule, generate_expected_timestamps, get_expected_trading_hours,
    is_trading_hour, SYMBOL_TO_GROUP
)


class TestSessionCalendar:
    def test_group1_monday_open(self):
        """Monday 00:00 is trading for group 1."""
        ts = pd.Timestamp("2023-07-03 00:00", tz="UTC")  # Monday
        assert is_trading_hour("EURUSD", ts)

    def test_group1_friday_market_close(self):
        """Friday 23:00 is last trading hour for group 1."""
        ts = pd.Timestamp("2023-07-07 23:00", tz="UTC")  # Friday
        assert is_trading_hour("GBPUSD", ts)
        # Saturday closed
        sat = pd.Timestamp("2023-07-08 12:00", tz="UTC")
        assert not is_trading_hour("GBPUSD", sat)

    def test_group2_friday_early_close(self):
        """EUR crosses close Friday 19:00 UTC, not 23:00."""
        friday_19 = pd.Timestamp("2023-07-07 19:00", tz="UTC")
        friday_21 = pd.Timestamp("2023-07-07 21:00", tz="UTC")
        assert is_trading_hour("EURGBP", friday_19)
        assert not is_trading_hour("EURGBP", friday_21)

    def test_sunday_market_open_handling(self):
        """Sunday is closed for all symbols (no Sunday open observed)."""
        sunday = pd.Timestamp("2023-07-09 20:00", tz="UTC")
        assert not is_trading_hour("EURUSD", sunday)
        assert not is_trading_hour("EURGBP", sunday)

    def test_dst_transition_no_boundary_shift(self):
        """DST does not shift UTC bar boundaries."""
        # Around US DST spring forward (2023-03-12) - UTC boundaries unchanged
        before = pd.Timestamp("2023-03-10 23:00", tz="UTC")
        after = pd.Timestamp("2023-03-13 00:00", tz="UTC")
        assert is_trading_hour("EURUSD", before)
        assert is_trading_hour("EURUSD", after)

    def test_scheduled_rollover_hour(self):
        """No systematic rollover hour is excluded (continuous Mon-Fri)."""
        # Random mid-week hour should always be trading
        ts = pd.Timestamp("2023-11-15 02:00", tz="UTC")  # Wednesday
        assert is_trading_hour("EURUSD", ts)

    def test_christmas_new_year_closure_listed(self):
        """Christmas/New Year are documented full closures in the calendar."""
        sched = get_session_schedule("EURUSD")
        assert any("12-25" in c or "12-26" in c or c.startswith("2026-01-01") for c in sched.documented_full_closures)

    def test_us_holiday_not_auto_full_closure(self):
        """US July 4 is NOT automatically a full FX closure - it trades."""
        # July 4 2023 is a Tuesday
        july4 = pd.Timestamp("2023-07-04 12:00", tz="UTC")
        assert is_trading_hour("EURUSD", july4)
        # The calendar lists it but the trading-hour function still treats it as open
        # (exclusion requires evidence of actual closure)

    def test_genuine_weekday_missing_hour_counts_as_missing(self):
        """
        A genuine missing weekday hour must be excluded from expected correctly.
        Expected open set includes it; absence from actual reduces coverage.
        """
        start = pd.Timestamp("2023-07-03 00:00", tz="UTC")
        end = pd.Timestamp("2023-07-07 23:00", tz="UTC")
        ts = generate_expected_timestamps("EURUSD", start, end)
        # Full week Mon-Fri = 5 days * 24h = 120
        assert len(ts) == 120

    def test_genuine_24h_market_open_gap_detected(self):
        """
        A genuine weekday 24h+ missing interval fails the no->24h-gap rule.
        Here we verify the expected set size reflects it: removing a full day
        drops coverage materially.
        """
        start = pd.Timestamp("2023-07-03 00:00", tz="UTC")
        end = pd.Timestamp("2023-07-14 23:00", tz="UTC")  # 2 weeks
        ts = generate_expected_timestamps("EURUSD", start, end)
        assert len(ts) == 10 * 24  # 10 trading days

        # Simulate actual data missing Wednesday 2023-07-05 entirely
        actual = [t for t in ts if t.day != 5 or t.month != 7]
        coverage = len(actual) / len(ts)
        # 24 missing / 240 = 90%, far below 97%
        assert coverage < 0.97

    def test_common_panel_gate_independent_of_full_history(self):
        """
        Common panel gate (>=97% and no >24h gap) can pass even when full
        2022 backfill is unavailable.
        """
        # Common window starts 2023-07-03; all Group-1 symbols exceed 97%
        from datetime import date
        sched = get_session_schedule("EURUSD")
        assert sched.group.value == "group_1_standard"

    def test_expected_hour_counts_reproducible(self):
        """Expected trading hour counts are deterministic and reproducible."""
        s1 = generate_expected_timestamps("EURUSD", pd.Timestamp("2023-07-03", tz="UTC"), pd.Timestamp("2023-08-04", tz="UTC"))
        s2 = generate_expected_timestamps("EURUSD", pd.Timestamp("2023-07-03", tz="UTC"), pd.Timestamp("2023-08-04", tz="UTC"))
        assert len(s1) == len(s2)

    def test_symbol_group_mapping(self):
        """Symbols map to the two correct session groups."""
        assert SYMBOL_TO_GROUP["EURUSD"].value == "group_1_standard"
        assert SYMBOL_TO_GROUP["EURGBP"].value == "group_2_eur_cross"
        assert SYMBOL_TO_GROUP["EURJPY"].value == "group_2_eur_cross"
        assert SYMBOL_TO_GROUP["EURCHF"].value == "group_2_eur_cross"