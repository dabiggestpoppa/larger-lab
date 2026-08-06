"""
OHLC Validation Module

This module provides strict validation of OHLC market data according to
canonical requirements. No silent interpolation or provider splicing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class OHLCValidationResult:
    """Result of OHLC validation."""
    symbol: str
    timeframe: str
    total_rows: int
    valid_rows: int
    malformed_ohlc_count: int
    non_positive_price_count: int
    high_lt_low_count: int
    close_out_of_range_count: int
    open_out_of_range_count: int
    nan_volume_count: int
    duplicate_timestamp_count: int
    weekend_bar_count: int
    missing_weekday_bar_count: int
    unexplained_gap_count: int
    stale_bar_count: int
    first_timestamp: Optional[str]
    last_timestamp: Optional[str]
    expected_bars: int
    coverage_pct: float
    quality_flag: int  # 0=clean, 1=warning, 2=error
    issues: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OHLCValidator:
    """
    Strict OHLC validator with no silent interpolation.
    
    Validates:
    - OHLC relationships (high >= low, close/open within high/low)
    - Non-positive prices
    - Timestamp ordering and duplicates
    - Weekend bars (reporting only)
    - Missing weekday bars
    - Unexplained gaps
    - Stale bars (identical OHLC)
    """
    
    def __init__(self, expected_freq: str = "1H"):
        """
        Initialize validator.
        
        Args:
            expected_freq: Expected frequency string (e.g., '1H', '1D')
        """
        self.expected_freq = expected_freq
        self.results: List[OHLCValidationResult] = []
    
    def validate(self, df: pd.DataFrame, symbol: str, timeframe: str) -> OHLCValidationResult:
        """
        Validate OHLC DataFrame.
        
        Args:
            df: DataFrame with canonical schema columns
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            OHLCValidationResult with all validation metrics
        """
        issues = []
        total_rows = len(df)
        
        if total_rows == 0:
            return OHLCValidationResult(
                symbol=symbol,
                timeframe=timeframe,
                total_rows=0,
                valid_rows=0,
                malformed_ohlc_count=0,
                non_positive_price_count=0,
                high_lt_low_count=0,
                close_out_of_range_count=0,
                open_out_of_range_count=0,
                nan_volume_count=0,
                duplicate_timestamp_count=0,
                weekend_bar_count=0,
                missing_weekday_bar_count=0,
                unexplained_gap_count=0,
                stale_bar_count=0,
                first_timestamp=None,
                last_timestamp=None,
                expected_bars=0,
                coverage_pct=0.0,
                quality_flag=2,
                issues=["Empty DataFrame"]
            )
        
        # Ensure timestamp is datetime
        if 'timestamp_utc' in df.columns:
            df = df.copy()
            df['timestamp_dt'] = pd.to_datetime(df['timestamp_utc'], utc=True)
        else:
            raise ValueError("DataFrame must have 'timestamp_utc' column")
        
        # 1. Check OHLC relationships
        malformed_ohlc = 0
        non_positive_price = 0
        high_lt_low = 0
        close_out_of_range = 0
        open_out_of_range = 0
        
        # Non-positive prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            non_positive = (df[col] <= 0).sum()
            non_positive_price += non_positive
        
        # High < Low
        high_lt_low = (df['high'] < df['low']).sum()
        
        # Close outside [low, high]
        close_out_of_range = ((df['close'] < df['low']) | (df['close'] > df['high'])).sum()
        
        # Open outside [low, high]
        open_out_of_range = ((df['open'] < df['low']) | (df['open'] > df['high'])).sum()
        
        malformed_ohlc = (non_positive_price + high_lt_low + close_out_of_range + open_out_of_range)
        
        if malformed_ohlc > 0:
            issues.append(f"Malformed OHLC: {malformed_ohlc} rows (non-positive: {non_positive_price}, high<low: {high_lt_low}, close OOB: {close_out_of_range}, open OOB: {open_out_of_range})")
        
        # 2. NaN volume
        nan_volume = df['volume'].isna().sum()
        if nan_volume > 0:
            issues.append(f"NaN volume: {nan_volume} rows")
        
        # 3. Duplicate timestamps
        duplicate_timestamps = df['timestamp_utc'].duplicated().sum()
        if duplicate_timestamps > 0:
            issues.append(f"Duplicate timestamps: {duplicate_timestamps}")
        
        # 4. Weekend bars (report only)
        weekend_bars = df['timestamp_dt'].dt.dayofweek.isin([5, 6]).sum()  # Sat=5, Sun=6
        if weekend_bars > 0:
            issues.append(f"Weekend bars present: {weekend_bars} (reporting only)")
        
        # 5. Missing weekday bars / unexplained gaps
        missing_weekday, unexplained_gaps = self._analyze_gaps(df, timeframe)
        if missing_weekday > 0:
            issues.append(f"Missing weekday bars: {missing_weekday}")
        if unexplained_gaps > 0:
            issues.append(f"Unexplained gaps: {unexplained_gaps}")
        
        # 6. Stale bars (identical OHLC)
        stale_bars = self._detect_stale_bars(df)
        if stale_bars > 0:
            issues.append(f"Stale bars (identical OHLC): {stale_bars}")
        
        # 7. Coverage calculation
        first_ts = df['timestamp_dt'].min()
        last_ts = df['timestamp_dt'].max()
        expected_bars = self._calculate_expected_bars(first_ts, last_ts, timeframe)
        coverage_pct = (total_rows / expected_bars * 100) if expected_bars > 0 else 0.0
        
        if coverage_pct < 90:
            issues.append(f"Low coverage: {coverage_pct:.1f}% ({total_rows}/{expected_bars} expected bars)")
        
        # Determine quality flag
        quality_flag = 0
        if malformed_ohlc > 0 or nan_volume > 0 or duplicate_timestamps > 0:
            quality_flag = 2  # Error
        elif unexplained_gaps > 0 or stale_bars > 0 or coverage_pct < 95:
            quality_flag = 1  # Warning
        
        result = OHLCValidationResult(
            symbol=symbol,
            timeframe=timeframe,
            total_rows=total_rows,
            valid_rows=total_rows - malformed_ohlc - nan_volume,
            malformed_ohlc_count=int(malformed_ohlc),
            non_positive_price_count=int(non_positive_price),
            high_lt_low_count=int(high_lt_low),
            close_out_of_range_count=int(close_out_of_range),
            open_out_of_range_count=int(open_out_of_range),
            nan_volume_count=int(nan_volume),
            duplicate_timestamp_count=int(duplicate_timestamps),
            weekend_bar_count=int(weekend_bars),
            missing_weekday_bar_count=int(missing_weekday),
            unexplained_gap_count=int(unexplained_gaps),
            stale_bar_count=int(stale_bars),
            first_timestamp=str(first_ts) if pd.notna(first_ts) else None,
            last_timestamp=str(last_ts) if pd.notna(last_ts) else None,
            expected_bars=expected_bars,
            coverage_pct=coverage_pct,
            quality_flag=quality_flag,
            issues=issues
        )
        
        self.results.append(result)
        return result
    
    def _analyze_gaps(self, df: pd.DataFrame, timeframe: str) -> Tuple[int, int]:
        """Analyze gaps in the time series."""
        # Expected frequency
        freq_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W',
            'H1': '1H', 'D1': '1D', 'H4': '4H'
        }
        freq = freq_map.get(timeframe, '1H')
        
        # Generate expected timestamps (weekdays only)
        expected_range = pd.date_range(
            start=df['timestamp_dt'].min(),
            end=df['timestamp_dt'].max(),
            freq=freq,
            tz='UTC'
        )
        
        # Filter to weekdays only (Mon-Fri)
        expected_weekday = expected_range[expected_range.dayofweek < 5]
        
        # Actual timestamps (rounded to frequency)
        actual_timestamps = df['timestamp_dt'].dt.floor(freq).unique()
        
        # Missing weekday bars
        missing = set(expected_weekday) - set(actual_timestamps)
        missing_weekday = len(missing)
        
        # Unexplained gaps (gaps larger than 1 period on weekdays)
        sorted_actual = sorted(actual_timestamps)
        unexplained_gaps = 0
        for i in range(1, len(sorted_actual)):
            diff = (sorted_actual[i] - sorted_actual[i-1]).total_seconds()
            expected_diff = pd.Timedelta(freq).total_seconds()
            if diff > expected_diff * 1.5:  # Allow 50% tolerance
                # Check if gap spans weekend
                gap_start = sorted_actual[i-1]
                gap_end = sorted_actual[i]
                # If gap doesn't include weekend, it's unexplained
                if not self._spans_weekend(gap_start, gap_end):
                    unexplained_gaps += 1
        
        return missing_weekday, unexplained_gaps
    
    def _spans_weekend(self, start: pd.Timestamp, end: pd.Timestamp) -> bool:
        """Check if a time range spans a weekend."""
        current = start
        while current < end:
            if current.dayofweek >= 5:  # Saturday or Sunday
                return True
            current += timedelta(days=1)
        return False
    
    def _detect_stale_bars(self, df: pd.DataFrame) -> int:
        """Detect bars with identical OHLC values."""
        # Group by OHLC and count
        ohlc_cols = ['open', 'high', 'low', 'close']
        stale = df.groupby(ohlc_cols).size()
        stale_count = (stale > 1).sum()
        return int(stale_count)
    
    def _calculate_expected_bars(self, start: pd.Timestamp, end: pd.Timestamp, timeframe: str) -> int:
        """Calculate expected number of bars in date range (weekdays only)."""
        freq_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W',
            'H1': '1H', 'D1': '1D', 'H4': '4H'
        }
        freq = freq_map.get(timeframe, '1H')
        
        expected_range = pd.date_range(start=start, end=end, freq=freq, tz='UTC')
        expected_weekday = expected_range[expected_range.dayofweek < 5]
        return len(expected_weekday)
    
    def validate_batch(self, data_dict: Dict[str, pd.DataFrame]) -> List[OHLCValidationResult]:
        """Validate multiple DataFrames."""
        results = []
        for key, df in data_dict.items():
            # Parse key as symbol_timeframe
            parts = key.split('_')
            if len(parts) >= 2:
                symbol = parts[0]
                timeframe = '_'.join(parts[1:])
            else:
                symbol = key
                timeframe = 'unknown'
            result = self.validate(df, symbol, timeframe)
            results.append(result)
        return results
    
    def save_results(self, path: str) -> None:
        """Save validation results to JSON."""
        results_data = {
            "completed_at": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }
        with open(path, 'w') as f:
            json.dump(results_data, f, indent=2)


def validate_normalized_file(file_path: str, symbol: str, timeframe: str) -> OHLCValidationResult:
    """Convenience function to validate a normalized Parquet file."""
    df = pd.read_parquet(file_path)
    validator = OHLCValidator()
    return validator.validate(df, symbol, timeframe)


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
    
    validator = OHLCValidator()
    result = validator.validate(df, 'EURUSD', 'H1')
    
    print(f"Symbol: {result.symbol}")
    print(f"Total rows: {result.total_rows}")
    print(f"Valid rows: {result.valid_rows}")
    print(f"Malformed OHLC: {result.malformed_ohlc_count}")
    print(f"Duplicate timestamps: {result.duplicate_timestamp_count}")
    print(f"Weekend bars: {result.weekend_bar_count}")
    print(f"Missing weekday: {result.missing_weekday_bar_count}")
    print(f"Unexplained gaps: {result.unexplained_gap_count}")
    print(f"Stale bars: {result.stale_bar_count}")
    print(f"Coverage: {result.coverage_pct:.1f}%")
    print(f"Quality flag: {result.quality_flag}")
    print(f"Issues: {result.issues}")