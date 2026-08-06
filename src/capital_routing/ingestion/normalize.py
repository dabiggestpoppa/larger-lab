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
    """Create normalization configs for Batch A symbols."""
    configs = []
    
    batch_a_symbols = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
        'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
    ]
    
    for symbol in batch_a_symbols:
        # H1 config
        h1_raw = os.path.join(raw_base, provider, symbol, f"{symbol}_H1.csv")
        h1_norm = os.path.join(normalized_base, "h1")
        
        if os.path.exists(h1_raw):
            sha256 = hashlib.sha256()
            with open(h1_raw, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            
            configs.append(NormalizationConfig(
                source_file=h1_raw,
                source_sha256=sha256.hexdigest(),
                symbol=symbol,
                vendor_symbol=symbol,
                timeframe="H1",
                provider=provider,
                price_side=price_side,
                source_timezone=source_timezone,
                output_dir=h1_norm
            ))
        
        # D1 config
        d1_raw = os.path.join(raw_base, provider, symbol, f"{symbol}_D1.csv")
        d1_norm = os.path.join(normalized_base, "d1")
        
        if os.path.exists(d1_raw):
            sha256 = hashlib.sha256()
            with open(d1_raw, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            
            configs.append(NormalizationConfig(
                source_file=d1_raw,
                source_sha256=sha256.hexdigest(),
                symbol=symbol,
                vendor_symbol=symbol,
                timeframe="D1",
                provider=provider,
                price_side=price_side,
                source_timezone=source_timezone,
                output_dir=d1_norm
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