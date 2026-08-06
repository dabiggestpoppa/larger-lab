"""
Gap Analysis Module

This module provides detailed gap analysis for normalized market data,
including missing bars, unexplained gaps, and coverage reporting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class GapInfo:
    """Information about a single gap."""
    gap_start: str
    gap_end: str
    gap_duration_seconds: float
    expected_bars_missing: int
    spans_weekend: bool
    is_unexplained: bool
    gap_type: str  # 'weekend', 'holiday', 'unexplained', 'data_missing'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GapAnalysisResult:
    """Result of gap analysis for a symbol/timeframe."""
    symbol: str
    timeframe: str
    first_timestamp: str
    last_timestamp: str
    total_expected_bars: int
    total_actual_bars: int
    coverage_pct: float
    weekend_bars: int
    missing_weekday_bars: int
    unexplained_gaps: List[GapInfo]
    holiday_gaps: List[GapInfo]
    data_missing_gaps: List[GapInfo]
    longest_gap_seconds: float
    longest_gap_start: Optional[str]
    longest_gap_end: Optional[str]
    quality_flag: int
    issues: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GapAnalyzer:
    """
    Detailed gap analyzer for market data.
    
    Analyzes:
    - Weekend gaps (expected)
    - Holiday gaps (expected, if calendar provided)
    - Unexplained gaps (data quality issue)
    - Data missing gaps (provider issues)
    - Coverage percentage
    """
    
    def __init__(self, holiday_calendar: Optional[List[str]] = None):
        """
        Initialize gap analyzer.
        
        Args:
            holiday_calendar: List of holiday dates in 'YYYY-MM-DD' format
        """
        self.holiday_calendar = set(holiday_calendar) if holiday_calendar else set()
        self.results: List[GapAnalysisResult] = []
    
    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> GapAnalysisResult:
        """
        Analyze gaps in normalized DataFrame.
        
        Args:
            df: DataFrame with canonical schema (must have timestamp_utc)
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            GapAnalysisResult with detailed gap information
        """
        issues = []
        
        if len(df) == 0:
            return GapAnalysisResult(
                symbol=symbol,
                timeframe=timeframe,
                first_timestamp="",
                last_timestamp="",
                total_expected_bars=0,
                total_actual_bars=0,
                coverage_pct=0.0,
                weekend_bars=0,
                missing_weekday_bars=0,
                unexplained_gaps=[],
                holiday_gaps=[],
                data_missing_gaps=[],
                longest_gap_seconds=0.0,
                longest_gap_start=None,
                longest_gap_end=None,
                quality_flag=2,
                issues=["Empty DataFrame"]
            )
        
        # Ensure timestamp is datetime
        df = df.copy()
        df['timestamp_dt'] = pd.to_datetime(df['timestamp_utc'], utc=True)
        df = df.sort_values('timestamp_dt').reset_index(drop=True)
        
        first_ts = df['timestamp_dt'].min()
        last_ts = df['timestamp_dt'].max()
        
        # Expected frequency
        freq_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W',
            'H1': '1H', 'D1': '1D', 'H4': '4H'
        }
        freq = freq_map.get(timeframe, '1H')
        
        # Generate expected timestamps (weekdays only)
        expected_range = pd.date_range(
            start=first_ts.floor(freq),
            end=last_ts.ceil(freq),
            freq=freq,
            tz='UTC'
        )
        
        # Filter to weekdays only (Mon-Fri)
        expected_weekday = expected_range[expected_range.dayofweek < 5]
        
        # Remove holidays if calendar provided
        if self.holiday_calendar:
            holiday_mask = ~expected_weekday.date.astype(str).isin(self.holiday_calendar)
            expected_weekday = expected_weekday[holiday_mask]
        
        total_expected = len(expected_weekday)
        total_actual = len(df)
        coverage_pct = (total_actual / total_expected * 100) if total_expected > 0 else 0.0
        
        # Actual timestamps (rounded to frequency)
        actual_timestamps = df['timestamp_dt'].dt.floor(freq).unique()
        actual_set = set(actual_timestamps)
        
        # Find missing timestamps
        missing_timestamps = [ts for ts in expected_weekday if ts not in actual_set]
        missing_weekday = len(missing_timestamps)
        
        # Weekend bars in actual data
        weekend_bars = df['timestamp_dt'].dt.dayofweek.isin([5, 6]).sum()
        
        # Analyze gaps
        unexplained_gaps = []
        holiday_gaps = []
        data_missing_gaps = []
        
        sorted_actual = sorted(actual_timestamps)
        expected_diff = pd.Timedelta(freq).total_seconds()
        
        for i in range(1, len(sorted_actual)):
            gap_start = sorted_actual[i-1]
            gap_end = sorted_actual[i]
            gap_duration = (gap_end - gap_start).total_seconds()
            
            if gap_duration > expected_diff * 1.5:  # Gap larger than 1.5 periods
                expected_bars_missing = int(gap_duration / expected_diff) - 1
                spans_weekend = self._spans_weekend(gap_start, gap_end)
                
                # Check if gap is explained by holiday
                is_holiday = self._is_holiday_gap(gap_start, gap_end)
                
                if spans_weekend:
                    gap_type = 'weekend'
                    holiday_gaps.append(GapInfo(
                        gap_start=str(gap_start),
                        gap_end=str(gap_end),
                        gap_duration_seconds=gap_duration,
                        expected_bars_missing=expected_bars_missing,
                        spans_weekend=True,
                        is_unexplained=False,
                        gap_type=gap_type
                    ))
                elif is_holiday:
                    gap_type = 'holiday'
                    holiday_gaps.append(GapInfo(
                        gap_start=str(gap_start),
                        gap_end=str(gap_end),
                        gap_duration_seconds=gap_duration,
                        expected_bars_missing=expected_bars_missing,
                        spans_weekend=False,
                        is_unexplained=False,
                        gap_type=gap_type
                    ))
                else:
                    gap_type = 'unexplained'
                    unexplained_gaps.append(GapInfo(
                        gap_start=str(gap_start),
                        gap_end=str(gap_end),
                        gap_duration_seconds=gap_duration,
                        expected_bars_missing=expected_bars_missing,
                        spans_weekend=False,
                        is_unexplained=True,
                        gap_type=gap_type
                    ))
        
        # Data missing gaps (missing individual bars within expected range)
        for missing_ts in missing_timestamps:
            # Check if this missing timestamp is part of a larger gap already recorded
            is_part_of_gap = False
            for gap in unexplained_gaps + holiday_gaps:
                gap_start = pd.Timestamp(gap.gap_start)
                gap_end = pd.Timestamp(gap.gap_end)
                if gap_start <= missing_ts <= gap_end:
                    is_part_of_gap = True
                    break
            
            if not is_part_of_gap:
                data_missing_gaps.append(GapInfo(
                    gap_start=str(missing_ts),
                    gap_end=str(missing_ts),
                    gap_duration_seconds=expected_diff,
                    expected_bars_missing=1,
                    spans_weekend=False,
                    is_unexplained=True,
                    gap_type='data_missing'
                ))
        
        # Longest gap
        all_gaps = unexplained_gaps + holiday_gaps + data_missing_gaps
        if all_gaps:
            longest = max(all_gaps, key=lambda g: g.gap_duration_seconds)
            longest_gap_seconds = longest.gap_duration_seconds
            longest_gap_start = longest.gap_start
            longest_gap_end = longest.gap_end
        else:
            longest_gap_seconds = 0.0
            longest_gap_start = None
            longest_gap_end = None
        
        # Quality flag
        quality_flag = 0
        if unexplained_gaps:
            quality_flag = 2
            issues.append(f"Unexplained gaps: {len(unexplained_gaps)}")
        if data_missing_gaps:
            quality_flag = max(quality_flag, 1)
            issues.append(f"Missing data bars: {len(data_missing_gaps)}")
        if coverage_pct < 95:
            quality_flag = max(quality_flag, 1)
            issues.append(f"Low coverage: {coverage_pct:.1f}%")
        
        result = GapAnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            first_timestamp=str(first_ts),
            last_timestamp=str(last_ts),
            total_expected_bars=total_expected,
            total_actual_bars=total_actual,
            coverage_pct=coverage_pct,
            weekend_bars=int(weekend_bars),
            missing_weekday_bars=missing_weekday,
            unexplained_gaps=unexplained_gaps,
            holiday_gaps=holiday_gaps,
            data_missing_gaps=data_missing_gaps,
            longest_gap_seconds=longest_gap_seconds,
            longest_gap_start=longest_gap_start,
            longest_gap_end=longest_gap_end,
            quality_flag=quality_flag,
            issues=issues
        )
        
        self.results.append(result)
        return result
    
    def _spans_weekend(self, start: pd.Timestamp, end: pd.Timestamp) -> bool:
        """Check if a time range spans a weekend."""
        current = start
        while current < end:
            if current.dayofweek >= 5:  # Saturday or Sunday
                return True
            current += timedelta(days=1)
        return False
    
    def _is_holiday_gap(self, start: pd.Timestamp, end: pd.Timestamp) -> bool:
        """Check if gap is explained by holiday calendar."""
        if not self.holiday_calendar:
            return False
        
        current = start
        while current < end:
            if current.date().isoformat() in self.holiday_calendar:
                return True
            current += timedelta(days=1)
        return False
    
    def analyze_batch(self, data_dict: Dict[str, pd.DataFrame]) -> List[GapAnalysisResult]:
        """Analyze gaps for multiple DataFrames."""
        results = []
        for key, df in data_dict.items():
            parts = key.split('_')
            if len(parts) >= 2:
                symbol = parts[0]
                timeframe = '_'.join(parts[1:])
            else:
                symbol = key
                timeframe = 'unknown'
            result = self.analyze(df, symbol, timeframe)
            results.append(result)
        return results
    
    def save_results(self, path: str) -> None:
        """Save gap analysis results to JSON."""
        results_data = {
            "completed_at": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }
        with open(path, 'w') as f:
            json.dump(results_data, f, indent=2)
    
    def generate_coverage_report(self) -> pd.DataFrame:
        """Generate coverage summary DataFrame."""
        rows = []
        for r in self.results:
            rows.append({
                'symbol': r.symbol,
                'timeframe': r.timeframe,
                'first_timestamp': r.first_timestamp,
                'last_timestamp': r.last_timestamp,
                'expected_bars': r.total_expected_bars,
                'actual_bars': r.total_actual_bars,
                'coverage_pct': r.coverage_pct,
                'weekend_bars': r.weekend_bars,
                'missing_weekday_bars': r.missing_weekday_bars,
                'unexplained_gaps': len(r.unexplained_gaps),
                'holiday_gaps': len(r.holiday_gaps),
                'data_missing_gaps': len(r.data_missing_gaps),
                'longest_gap_seconds': r.longest_gap_seconds,
                'quality_flag': r.quality_flag
            })
        return pd.DataFrame(rows)


def analyze_normalized_file(file_path: str, symbol: str, timeframe: str, 
                           holiday_calendar: Optional[List[str]] = None) -> GapAnalysisResult:
    """Convenience function to analyze a normalized Parquet file."""
    df = pd.read_parquet(file_path)
    analyzer = GapAnalyzer(holiday_calendar)
    return analyzer.analyze(df, symbol, timeframe)


if __name__ == "__main__":
    # Test with synthetic fixture
    from tests.fixtures.synthetic_market_data import create_test_fixture_csv
    
    fixture_path = create_test_fixture_csv("EURUSD", "H1", rows=100)
    df = pd.read_csv(fixture_path)
    
    # Add required columns for canonical schema
    df['timestamp_utc'] = df['timestamp']
    df['symbol'] = 'EURUSD'
    df['timeframe'] = 'H1'
    df['source'] = 'test_fixture'
    df['vendor_symbol'] = 'EURUSD'
    df['price_side'] = 'bid'
    df['source_timezone'] = 'UTC'
    df['source_file'] = fixture_path
    df['source_sha256'] = 'test'
    df['quality_flag'] = 0
    
    analyzer = GapAnalyzer()
    result = analyzer.analyze(df, 'EURUSD', 'H1')
    
    print(f"Symbol: {result.symbol}")
    print(f"Coverage: {result.coverage_pct:.1f}%")
    print(f"Expected bars: {result.total_expected_bars}")
    print(f"Actual bars: {result.total_actual_bars}")
    print(f"Weekend bars: {result.weekend_bars}")
    print(f"Missing weekday: {result.missing_weekday_bars}")
    print(f"Unexplained gaps: {len(result.unexplained_gaps)}")
    print(f"Holiday gaps: {len(result.holiday_gaps)}")
    print(f"Data missing gaps: {len(result.data_missing_gaps)}")
    print(f"Quality flag: {result.quality_flag}")
    print(f"Issues: {result.issues}")