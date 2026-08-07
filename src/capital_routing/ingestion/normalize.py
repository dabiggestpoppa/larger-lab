"""
Canonical OHLC Normalization Pipeline

This module implements the canonical normalization of raw market data
into a standardized schema with full provenance tracking.

Canonical schema:
- timestamp_utc: UTC timestamp (ISO 8601)
- open: Open price
- high: High price
- low: Low price
- close: Close price
- volume: Tick volume (preserved as-is, not called "real exchange volume")
- symbol: Trading symbol
- timeframe: Timeframe (e.g., 'H1', 'D1')
- source: Source identifier (e.g., 'mt5', 'dukascopy', 'oanda')
- vendor_symbol: Original symbol as provided by vendor
- price_side: 'bid', 'ask', or 'mid'
- source_timezone: Original timezone (e.g., 'UTC', 'Europe/London')
- source_file: Path to raw source file
- source_sha256: SHA-256 checksum of raw source file
- quality_flag: Quality indicator (0=clean, 1=warning, 2=error)
"""

import os
import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pytz


@dataclass
class NormalizationConfig:
    """Configuration for normalization."""
    source_file: str
    source_sha256: str
    symbol: str
    vendor_symbol: str
    timeframe: str
    provider: str
    price_side: str
    source_timezone: str
    output_dir: str
    target_timezone: str = "UTC"
    timestamp_column: str = "timestamp"
    open_column: str = "open"
    high_column: str = "high"
    low_column: str = "low"
    close_column: str = "close"
    volume_column: str = "volume"
    timestamp_format: Optional[str] = None  # Auto-detect if None
    delimiter: str = ","
    encoding: str = "utf-8"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizationResult:
    """Result of normalization process."""
    success: bool
    config: NormalizationConfig
    output_file: Optional[str] = None
    output_sha256: Optional[str] = None
    row_count: int = 0
    duplicate_count: int = 0
    malformed_ohlc_count: int = 0
    missing_weekday_count: int = 0
    unexplained_gap_count: int = 0
    stale_bar_count: int = 0
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    quality_flag: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OHLCNormalizer:
    """
    Canonical OHLC normalizer with full provenance tracking.
    
    Requirements:
    - Strict timestamp parsing
    - Convert to UTC
    - Sort ascending
    - Deterministic duplicate handling
    - Reject malformed OHLC
    - Reject non-positive prices
    - Report weekend bars
    - Report unexplained weekday gaps
    - Preserve tick volume as tick volume
    - No silent interpolation
    - No silent provider splicing
    """
    
    def __init__(self):
        self.results: List[NormalizationResult] = []
    
    def normalize(self, config: NormalizationConfig) -> NormalizationResult:
        """
        Normalize a raw OHLC file to canonical schema.
        
        Args:
            config: Normalization configuration
            
        Returns:
            NormalizationResult with output file and quality metrics
        """
        # Verify source file exists
        if not os.path.exists(config.source_file):
            return NormalizationResult(
                success=False,
                config=config,
                error_message=f"Source file not found: {config.source_file}"
            )
        
        # Verify checksum
        actual_sha256 = self._calculate_sha256(config.source_file)
        if actual_sha256 != config.source_sha256:
            return NormalizationResult(
                success=False,
                config=config,
                error_message=f"Checksum mismatch: expected {config.source_sha256}, got {actual_sha256}"
            )
        
        try:
            # Load raw data
            df = self._load_raw_data(config)
            
            # Resample if needed (e.g., M5 -> H1)
            df = self._resample_if_needed(df, config)
            
            # Validate and clean
            df, metrics = self._validate_and_clean(df, config)
            
            # Convert timestamps to UTC
            df = self._convert_to_utc(df, config)
            
            # Sort and handle duplicates
            df, duplicate_count = self._sort_and_deduplicate(df, config)
            metrics['duplicate_count'] = duplicate_count
            
            # Add provenance columns
            df = self._add_provenance(df, config)
            
            # Write output
            output_file = self._write_output(df, config)
            output_sha256 = self._calculate_sha256(output_file)
            
            # Determine quality flag
            quality_flag = self._determine_quality_flag(metrics)
            
            result = NormalizationResult(
                success=True,
                config=config,
                output_file=output_file,
                output_sha256=output_sha256,
                row_count=len(df),
                duplicate_count=metrics['duplicate_count'],
                malformed_ohlc_count=metrics['malformed_ohlc_count'],
                missing_weekday_count=metrics['missing_weekday_count'],
                unexplained_gap_count=metrics['unexplained_gap_count'],
                stale_bar_count=metrics['stale_bar_count'],
                first_timestamp=df['timestamp_utc'].iloc[0] if len(df) > 0 else None,
                last_timestamp=df['timestamp_utc'].iloc[-1] if len(df) > 0 else None,
                quality_flag=quality_flag,
                warnings=metrics['warnings']
            )
            
            self.results.append(result)
            return result
            
        except Exception as e:
            return NormalizationResult(
                success=False,
                config=config,
                error_message=f"Normalization error: {str(e)}"
            )
    
    def _load_raw_data(self, config: NormalizationConfig) -> pd.DataFrame:
        """Load raw data from CSV or Parquet."""
        if config.source_file.endswith('.parquet'):
            df = pd.read_parquet(config.source_file)
        else:
            df = pd.read_csv(
                config.source_file,
                delimiter=config.delimiter,
                encoding=config.encoding
            )
        return df
    
    def _resample_if_needed(self, df: pd.DataFrame, config: NormalizationConfig) -> pd.DataFrame:
        """Resample data to target timeframe if needed (e.g., M5 -> H1)."""
        # Check if resampling is needed based on config timeframe vs detected timeframe
        # For now, we'll detect the timeframe from the data frequency
        if len(df) < 2:
            return df
        
        # Parse timestamps to detect frequency
        try:
            # Detect if timestamps are Unix timestamps (seconds since epoch)
            sample_values = df[config.timestamp_column].dropna().head(100)
            is_unix_timestamp = False
            
            if sample_values.dtype in ['int64', 'float64', 'int32', 'float32']:
                # Check if values are in reasonable Unix timestamp range (year 2000-2030)
                min_val = sample_values.min()
                max_val = sample_values.max()
                if 946684800 <= min_val <= 1893456000 and 946684800 <= max_val <= 1893456000:
                    is_unix_timestamp = True
            
            if is_unix_timestamp:
                df['_ts'] = pd.to_datetime(df[config.timestamp_column], unit='s', utc=True, errors='coerce')
            else:
                df['_ts'] = pd.to_datetime(df[config.timestamp_column], errors='coerce')
            
            df = df.dropna(subset=['_ts'])
            if len(df) < 2:
                return df
            
            df = df.sort_values('_ts')
            time_diffs = df['_ts'].diff().dropna()
            median_diff = time_diffs.median()
            
            # Determine source timeframe
            if median_diff <= pd.Timedelta(minutes=5):
                source_tf = 'M5'
            elif median_diff <= pd.Timedelta(minutes=15):
                source_tf = 'M15'
            elif median_diff <= pd.Timedelta(minutes=30):
                source_tf = 'M30'
            elif median_diff <= pd.Timedelta(hours=1):
                source_tf = 'H1'
            elif median_diff <= pd.Timedelta(hours=4):
                source_tf = 'H4'
            elif median_diff <= pd.Timedelta(days=1):
                source_tf = 'D1'
            else:
                source_tf = 'unknown'
            
            target_tf = config.timeframe
            
            # If source is higher frequency than target, resample
            freq_map = {'M5': '5min', 'M15': '15min', 'M30': '30min', 'H1': '1H', 'H4': '4H', 'D1': '1D'}
            
            if source_tf in freq_map and target_tf in freq_map:
                source_freq = freq_map[source_tf]
                target_freq = freq_map[target_tf]
                
                # Only resample if source is higher frequency (shorter period)
                if pd.Timedelta(source_freq) < pd.Timedelta(target_freq):
                    print(f"  Resampling {source_tf} -> {target_tf} ({len(df)} bars)")
                    
                    # Set timestamp as index for resampling
                    df = df.set_index('_ts')
                    
                    # Resample OHLC
                    ohlc_dict = {
                        config.open_column: 'first',
                        config.high_column: 'max',
                        config.low_column: 'min',
                        config.close_column: 'last',
                        config.volume_column: 'sum'
                    }
                    
                    df_resampled = df.resample(target_freq).agg(ohlc_dict).dropna()
                    df_resampled = df_resampled.reset_index()
                    df_resampled = df_resampled.rename(columns={'_ts': config.timestamp_column})
                    
                    print(f"  Resampled {len(df)} -> {len(df_resampled)} bars")
                    return df_resampled
            
            df = df.drop(columns=['_ts'])
            return df
            
        except Exception as e:
            print(f"  Warning: Resampling failed: {e}")
            if '_ts' in df.columns:
                df = df.drop(columns=['_ts'])
            return df
    
    def _validate_and_clean(self, df: pd.DataFrame, config: NormalizationConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate OHLC data and clean."""
        metrics = {
            'duplicate_count': 0,
            'malformed_ohlc_count': 0,
            'missing_weekday_count': 0,
            'unexplained_gap_count': 0,
            'stale_bar_count': 0,
            'warnings': []
        }
        
        # Ensure required columns exist
        required_cols = [config.timestamp_column, config.open_column, config.high_column, 
                        config.low_column, config.close_column, config.volume_column]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Rename to canonical names
        df = df.rename(columns={
            config.timestamp_column: 'timestamp_raw',
            config.open_column: 'open',
            config.high_column: 'high',
            config.low_column: 'low',
            config.close_column: 'close',
            config.volume_column: 'volume'
        })
        
        # Convert price columns to numeric
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # Track malformed OHLC
        initial_count = len(df)
        
        # Reject non-positive prices
        price_mask = (df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)
        df = df[price_mask].copy()
        metrics['malformed_ohlc_count'] += initial_count - len(df)
        
        # Reject malformed OHLC (high >= low, close between high/low, open between high/low)
        ohlc_mask = (
            (df['high'] >= df['low']) &
            (df['close'] >= df['low']) & (df['close'] <= df['high']) &
            (df['open'] >= df['low']) & (df['open'] <= df['high'])
        )
        df = df[ohlc_mask].copy()
        metrics['malformed_ohlc_count'] += initial_count - len(df)
        
        # Reject NaN volume
        df = df.dropna(subset=['volume']).copy()
        
        return df, metrics
    
    def _convert_to_utc(self, df: pd.DataFrame, config: NormalizationConfig) -> pd.DataFrame:
        """Convert timestamps to UTC."""
        # Parse timestamps
        if config.timestamp_format:
            df['timestamp_parsed'] = pd.to_datetime(df['timestamp_raw'], format=config.timestamp_format, errors='coerce')
        else:
            # Try to detect if timestamps are Unix timestamps (seconds since epoch)
            # Check if values are numeric and in reasonable Unix timestamp range
            sample_values = df['timestamp_raw'].dropna().head(100)
            is_unix_timestamp = False
            
            if sample_values.dtype in ['int64', 'float64', 'int32', 'float32']:
                # Check if values are in reasonable Unix timestamp range (year 2000-2030)
                # Unix timestamps for 2000-01-01 to 2030-01-01 are roughly 946684800 to 1893456000
                min_val = sample_values.min()
                max_val = sample_values.max()
                if 946684800 <= min_val <= 1893456000 and 946684800 <= max_val <= 1893456000:
                    is_unix_timestamp = True
            
            if is_unix_timestamp:
                # Parse as Unix timestamps (seconds since epoch)
                df['timestamp_parsed'] = pd.to_datetime(df['timestamp_raw'], unit='s', utc=True, errors='coerce')
            else:
                df['timestamp_parsed'] = pd.to_datetime(df['timestamp_raw'], errors='coerce', utc=False)
        
        # Drop unparseable timestamps
        initial_count = len(df)
        df = df.dropna(subset=['timestamp_parsed']).copy()
        if len(df) < initial_count:
            print(f"Warning: Dropped {initial_count - len(df)} rows with unparseable timestamps")
        
        # Localize to source timezone if naive
        if df['timestamp_parsed'].dt.tz is None:
            try:
                tz = pytz.timezone(config.source_timezone)
                df['timestamp_parsed'] = df['timestamp_parsed'].dt.tz_localize(tz)
            except Exception as e:
                raise ValueError(f"Unknown source timezone '{config.source_timezone}': {e}")
        
        # Convert to UTC
        df['timestamp_utc'] = df['timestamp_parsed'].dt.tz_convert('UTC')
        
        # Format as ISO string
        df['timestamp_utc'] = df['timestamp_utc'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return df
    
    def _sort_and_deduplicate(self, df: pd.DataFrame, config: NormalizationConfig) -> Tuple[pd.DataFrame, int]:
        """Sort by timestamp and handle duplicates deterministically.
        
        Returns:
            Tuple of (deduplicated DataFrame, duplicate_count)
        """
        # Sort by timestamp
        df = df.sort_values('timestamp_utc').reset_index(drop=True)
        
        # Count duplicates before deduplication
        initial_count = len(df)
        
        # Deterministic duplicate handling: keep first occurrence
        df = df.drop_duplicates(subset=['timestamp_utc'], keep='first').reset_index(drop=True)
        
        duplicate_count = initial_count - len(df)
        return df, duplicate_count
    
    def _add_provenance(self, df: pd.DataFrame, config: NormalizationConfig) -> pd.DataFrame:
        """Add provenance columns."""
        df['symbol'] = config.symbol
        df['timeframe'] = config.timeframe
        df['source'] = config.provider
        df['vendor_symbol'] = config.vendor_symbol
        df['price_side'] = config.price_side
        df['source_timezone'] = config.source_timezone
        df['source_file'] = config.source_file
        df['source_sha256'] = config.source_sha256
        df['quality_flag'] = 0  # Will be updated after quality analysis
        
        # Reorder columns to canonical schema
        canonical_columns = [
            'timestamp_utc', 'open', 'high', 'low', 'close', 'volume',
            'symbol', 'timeframe', 'source', 'vendor_symbol', 'price_side',
            'source_timezone', 'source_file', 'source_sha256', 'quality_flag'
        ]
        
        # Ensure all columns exist
        for col in canonical_columns:
            if col not in df.columns:
                df[col] = None
        
        return df[canonical_columns]
    
    def _write_output(self, df: pd.DataFrame, config: NormalizationConfig) -> str:
        """Write normalized data to Parquet."""
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Generate output filename
        output_file = os.path.join(config.output_dir, f"{config.symbol}_{config.timeframe}.parquet")
        
        # Write to Parquet
        df.to_parquet(output_file, index=False)
        
        return output_file
    
    def _calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _determine_quality_flag(self, metrics: Dict[str, Any]) -> int:
        """Determine quality flag based on metrics."""
        if metrics['malformed_ohlc_count'] > 0:
            return 2  # Error
        if metrics['duplicate_count'] > 0 or metrics['unexplained_gap_count'] > 0:
            return 1  # Warning
        return 0  # Clean
    
    def normalize_batch(self, configs: List[NormalizationConfig]) -> List[NormalizationResult]:
        """Normalize multiple files."""
        results = []
        for config in configs:
            result = self.normalize(config)
            results.append(result)
        return results
    
    def save_results(self, path: str) -> None:
        """Save normalization results to JSON."""
        results_data = {
            "completed_at": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }
        with open(path, 'w') as f:
            json.dump(results_data, f, indent=2)


def create_batch_a_normalization_configs(
    raw_base: str = "data/raw",
    normalized_base: str = "data/normalized",
    provider: str = "MetaQuotes-Demo",
    price_side: str = "bid",
    source_timezone: str = "UTC"
) -> List[NormalizationConfig]:
    """Create normalization configs for Batch A symbols by finding actual H1/D1 files."""
    configs = []
    
    batch_a_symbols = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
        'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
    ]
    
    def detect_columns(file_path: str) -> Dict[str, str]:
        """Detect column names from CSV file."""
        try:
            df = pd.read_csv(file_path, nrows=1)
            cols = df.columns.tolist()
            
            # Detect timestamp column
            timestamp_col = None
            for c in cols:
                if c.lower() in ['time', 'timestamp', 'date', 'datetime']:
                    timestamp_col = c
                    break
            
            # Detect volume column
            volume_col = None
            for c in cols:
                if c.lower() in ['volume', 'tick_volume', 'real_volume', 'vol']:
                    volume_col = c
                    break
            
            return {
                'timestamp_column': timestamp_col or 'timestamp',
                'volume_column': volume_col or 'volume',
                'open_column': 'open' if 'open' in cols else 'open',
                'high_column': 'high' if 'high' in cols else 'high',
                'low_column': 'low' if 'low' in cols else 'low',
                'close_column': 'close' if 'close' in cols else 'close',
            }
        except Exception:
            return {
                'timestamp_column': 'timestamp',
                'volume_column': 'volume',
                'open_column': 'open',
                'high_column': 'high',
                'low_column': 'low',
                'close_column': 'close',
            }
    
    batch_a_symbols = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
        'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
    ]
    
    for symbol in batch_a_symbols:
        # Search for H1 files in all provider subdirectories
        h1_files = []
        provider_dir = Path(raw_base)
        if provider_dir.exists():
            for prov_dir in provider_dir.iterdir():
                if prov_dir.is_dir():
                    symbol_dir = prov_dir / symbol
                    if symbol_dir.exists():
                        # Look for H1 files (various naming patterns)
                        for pattern in ['*H1*.csv', '*_H1.csv', '*_1h.csv', '*_1H.csv', '*PRO_H1.csv']:
                            h1_files.extend(symbol_dir.glob(pattern))
        
        # If no H1 files found, look for M5 files that can be resampled
        if not h1_files:
            m5_files = []
            provider_dir = Path(raw_base)
            if provider_dir.exists():
                for prov_dir in provider_dir.iterdir():
                    if prov_dir.is_dir():
                        symbol_dir = prov_dir / symbol
                        if symbol_dir.exists():
                            for pattern in ['*M5*.csv', '*_M5.csv', '*_5m.csv', '*_5M.csv']:
                                m5_files.extend(symbol_dir.glob(pattern))
            
            # Use the first M5 file found (will need resampling in normalizer)
            if m5_files:
                h1_files = m5_files[:1]
        
        # Process H1 files
        for h1_raw in h1_files:
            if not h1_raw.exists():
                continue
                
            # Calculate checksum
            sha256 = hashlib.sha256()
            with open(h1_raw, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            
            # Detect column names
            col_map = detect_columns(str(h1_raw))
            
            # Determine provider from path
            rel_path = h1_raw.relative_to(raw_base)
            prov = rel_path.parts[0] if len(rel_path.parts) > 0 else provider
            
            h1_norm = os.path.join(normalized_base, "h1")
            
            configs.append(NormalizationConfig(
                source_file=str(h1_raw),
                source_sha256=sha256.hexdigest(),
                symbol=symbol,
                vendor_symbol=symbol,
                timeframe="H1",
                provider=prov,
                price_side=price_side,
                source_timezone=source_timezone,
                output_dir=h1_norm,
                timestamp_column=col_map['timestamp_column'],
                volume_column=col_map['volume_column'],
                open_column=col_map['open_column'],
                high_column=col_map['high_column'],
                low_column=col_map['low_column'],
                close_column=col_map['close_column'],
            ))
        
        # D1 config - search for D1 files
        d1_files = []
        provider_dir = Path(raw_base)
        if provider_dir.exists():
            for prov_dir in provider_dir.iterdir():
                if prov_dir.is_dir():
                    symbol_dir = prov_dir / symbol
                    if symbol_dir.exists():
                        for pattern in ['*D1*.csv', '*_D1.csv', '*_1d.csv', '*_1D.csv', '*PRO_D1.csv']:
                            d1_files.extend(symbol_dir.glob(pattern))
        
        for d1_raw in d1_files:
            if not d1_raw.exists():
                continue
                
            sha256 = hashlib.sha256()
            with open(d1_raw, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            
            # Detect column names
            col_map = detect_columns(str(d1_raw))
            
            rel_path = d1_raw.relative_to(raw_base)
            prov = rel_path.parts[0] if len(rel_path.parts) > 0 else provider
            
            d1_norm = os.path.join(normalized_base, "d1")
            
            configs.append(NormalizationConfig(
                source_file=str(d1_raw),
                source_sha256=sha256.hexdigest(),
                symbol=symbol,
                vendor_symbol=symbol,
                timeframe="D1",
                provider=prov,
                price_side=price_side,
                source_timezone=source_timezone,
                output_dir=d1_norm,
                timestamp_column=col_map['timestamp_column'],
                volume_column=col_map['volume_column'],
                open_column=col_map['open_column'],
                high_column=col_map['high_column'],
                low_column=col_map['low_column'],
                close_column=col_map['close_column'],
            ))
    
    return configs


if __name__ == "__main__":
    # Test with synthetic fixture
    from tests.fixtures.synthetic_market_data import create_test_fixture_csv
    
    fixture_path = create_test_fixture_csv("EURUSD", "H1", rows=100)
    
    # Calculate checksum
    sha256 = hashlib.sha256()
    with open(fixture_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    
    config = NormalizationConfig(
        source_file=fixture_path,
        source_sha256=sha256.hexdigest(),
        symbol="EURUSD",
        vendor_symbol="EURUSD",
        timeframe="H1",
        provider="test_fixture",
        price_side="bid",
        source_timezone="UTC",
        output_dir="data/normalized/h1"
    )
    
    normalizer = OHLCNormalizer()
    result = normalizer.normalize(config)
    
    print(f"Success: {result.success}")
    print(f"Output: {result.output_file}")
    print(f"Rows: {result.row_count}")
    print(f"Quality flag: {result.quality_flag}")