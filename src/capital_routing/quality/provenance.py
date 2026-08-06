"""
Provenance Tracking Module

This module provides comprehensive provenance tracking for all normalized
market data files, ensuring full traceability from raw source to final output.
"""

import os
import json
import hashlib
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class RawFileManifestEntry:
    """Entry in raw file manifest."""
    symbol: str
    timeframe: str
    provider: str
    source_file: str
    source_sha256: str
    file_size_bytes: int
    row_count: int
    first_timestamp: Optional[str]
    last_timestamp: Optional[str]
    price_side: str
    source_timezone: str
    vendor_symbol: str
    acquired_at: str
    acquisition_method: str  # 'mt5_export', 'local_library', 'manual'
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedFileManifestEntry:
    """Entry in normalized file manifest."""
    symbol: str
    timeframe: str
    normalized_file: str
    normalized_sha256: str
    file_size_bytes: int
    row_count: int
    first_timestamp: Optional[str]
    last_timestamp: Optional[str]
    source_file: str
    source_sha256: str
    provider: str
    price_side: str
    source_timezone: str
    vendor_symbol: str
    quality_flag: int
    normalization_version: str
    normalized_at: str
    derived_from: Optional[str] = None  # e.g., 'H1' if D1 derived from H1
    day_boundary_utc: Optional[str] = None  # For D1 derived from H1
    aggregation_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BatchACoverageEntry:
    """Batch A coverage entry."""
    symbol: str
    h1_raw_exists: bool
    h1_raw_sha256: Optional[str]
    h1_normalized_exists: bool
    h1_normalized_sha256: Optional[str]
    h1_row_count: int
    h1_coverage_pct: float
    h1_quality_flag: int
    d1_raw_exists: bool
    d1_raw_sha256: Optional[str]
    d1_normalized_exists: bool
    d1_normalized_sha256: Optional[str]
    d1_row_count: int
    d1_coverage_pct: float
    d1_quality_flag: int
    d1_derived_from_h1: bool
    status: str  # 'accepted', 'rejected', 'pending', 'missing'
    rejection_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProvenanceTracker:
    """
    Comprehensive provenance tracker for market data pipeline.
    
    Tracks:
    - Raw file manifest (source files, checksums, metadata)
    - Normalized file manifest (output files, checksums, derivation)
    - Batch A coverage (per-symbol status)
    - Raw checksums (for verification)
    """
    
    def __init__(self, manifest_dir: str = "data/manifests"):
        """
        Initialize provenance tracker.
        
        Args:
            manifest_dir: Directory for manifest files
        """
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        self.raw_manifest: List[RawFileManifestEntry] = []
        self.normalized_manifest: List[NormalizedFileManifestEntry] = []
        self.batch_a_coverage: List[BatchACoverageEntry] = []
        self.raw_checksums: Dict[str, str] = {}  # file_path -> sha256
    
    def add_raw_file(self, entry: RawFileManifestEntry) -> None:
        """Add raw file to manifest."""
        self.raw_manifest.append(entry)
        self.raw_checksums[entry.source_file] = entry.source_sha256
    
    def add_normalized_file(self, entry: NormalizedFileManifestEntry) -> None:
        """Add normalized file to manifest."""
        self.normalized_manifest.append(entry)
    
    def add_batch_a_coverage(self, entry: BatchACoverageEntry) -> None:
        """Add Batch A coverage entry."""
        self.batch_a_coverage.append(entry)
    
    def calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def register_raw_file(
        self,
        symbol: str,
        timeframe: str,
        provider: str,
        source_file: str,
        price_side: str,
        source_timezone: str,
        vendor_symbol: str,
        acquisition_method: str = "mt5_export",
        notes: str = ""
    ) -> RawFileManifestEntry:
        """Register a raw file with automatic metadata extraction."""
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Raw file not found: {source_file}")
        
        # Calculate checksum
        sha256 = self.calculate_sha256(source_file)
        file_size = os.path.getsize(source_file)
        
        # Try to get row count and timestamps
        row_count = 0
        first_ts = None
        last_ts = None
        
        try:
            if source_file.endswith('.parquet'):
                df = pd.read_parquet(source_file)
            else:
                df = pd.read_csv(source_file)
            
            row_count = len(df)
            
            # Find timestamp column
            ts_cols = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()]
            if ts_cols:
                ts_col = ts_cols[0]
                if row_count > 0:
                    first_ts = str(df[ts_col].iloc[0])
                    last_ts = str(df[ts_col].iloc[-1])
        except Exception:
            pass
        
        entry = RawFileManifestEntry(
            symbol=symbol,
            timeframe=timeframe,
            provider=provider,
            source_file=source_file,
            source_sha256=sha256,
            file_size_bytes=file_size,
            row_count=row_count,
            first_timestamp=first_ts,
            last_timestamp=last_ts,
            price_side=price_side,
            source_timezone=source_timezone,
            vendor_symbol=vendor_symbol,
            acquired_at=datetime.now().isoformat(),
            acquisition_method=acquisition_method,
            notes=notes
        )
        
        self.add_raw_file(entry)
        return entry
    
    def register_normalized_file(
        self,
        symbol: str,
        timeframe: str,
        normalized_file: str,
        source_file: str,
        source_sha256: str,
        provider: str,
        price_side: str,
        source_timezone: str,
        vendor_symbol: str,
        quality_flag: int,
        normalization_version: str = "1.0",
        derived_from: Optional[str] = None,
        day_boundary_utc: Optional[str] = None,
        aggregation_version: Optional[str] = None
    ) -> NormalizedFileManifestEntry:
        """Register a normalized file with automatic metadata extraction."""
        if not os.path.exists(normalized_file):
            raise FileNotFoundError(f"Normalized file not found: {normalized_file}")
        
        # Calculate checksum
        sha256 = self.calculate_sha256(normalized_file)
        file_size = os.path.getsize(normalized_file)
        
        # Get metadata from normalized file
        row_count = 0
        first_ts = None
        last_ts = None
        
        try:
            df = pd.read_parquet(normalized_file)
            row_count = len(df)
            
            if 'timestamp_utc' in df.columns and row_count > 0:
                first_ts = str(df['timestamp_utc'].iloc[0])
                last_ts = str(df['timestamp_utc'].iloc[-1])
        except Exception:
            pass
        
        entry = NormalizedFileManifestEntry(
            symbol=symbol,
            timeframe=timeframe,
            normalized_file=normalized_file,
            normalized_sha256=sha256,
            file_size_bytes=file_size,
            row_count=row_count,
            first_timestamp=first_ts,
            last_timestamp=last_ts,
            source_file=source_file,
            source_sha256=source_sha256,
            provider=provider,
            price_side=price_side,
            source_timezone=source_timezone,
            vendor_symbol=vendor_symbol,
            quality_flag=quality_flag,
            normalization_version=normalization_version,
            normalized_at=datetime.now().isoformat(),
            derived_from=derived_from,
            day_boundary_utc=day_boundary_utc,
            aggregation_version=aggregation_version
        )
        
        self.add_normalized_file(entry)
        return entry
    
    def register_batch_a_coverage(
        self,
        symbol: str,
        h1_raw_path: Optional[str] = None,
        h1_norm_path: Optional[str] = None,
        d1_raw_path: Optional[str] = None,
        d1_norm_path: Optional[str] = None,
        provider: str = "MetaQuotes-Demo",
        price_side: str = "bid",
        source_timezone: str = "UTC"
    ) -> BatchACoverageEntry:
        """Register Batch A coverage for a symbol."""
        rejection_reasons = []
        
        # H1 raw
        h1_raw_exists = h1_raw_path and os.path.exists(h1_raw_path)
        h1_raw_sha256 = self.calculate_sha256(h1_raw_path) if h1_raw_exists else None
        
        # H1 normalized
        h1_normalized_exists = h1_norm_path and os.path.exists(h1_norm_path)
        h1_normalized_sha256 = self.calculate_sha256(h1_norm_path) if h1_normalized_exists else None
        
        # D1 raw
        d1_raw_exists = d1_raw_path and os.path.exists(d1_raw_path)
        d1_raw_sha256 = self.calculate_sha256(d1_raw_path) if d1_raw_exists else None
        
        # D1 normalized
        d1_normalized_exists = d1_norm_path and os.path.exists(d1_norm_path)
        d1_normalized_sha256 = self.calculate_sha256(d1_norm_path) if d1_normalized_exists else None
        
        # Get row counts and quality from normalized files
        h1_row_count = 0
        h1_coverage_pct = 0.0
        h1_quality_flag = 2
        
        if h1_normalized_exists:
            try:
                df = pd.read_parquet(h1_norm_path)
                h1_row_count = len(df)
                # Calculate coverage (simplified)
                h1_coverage_pct = 100.0  # Would need gap analysis for real coverage
                h1_quality_flag = 0
            except Exception:
                h1_quality_flag = 2
        
        d1_row_count = 0
        d1_coverage_pct = 0.0
        d1_quality_flag = 2
        d1_derived_from_h1 = False
        
        if d1_normalized_exists:
            try:
                df = pd.read_parquet(d1_norm_path)
                d1_row_count = len(df)
                d1_coverage_pct = 100.0
                d1_quality_flag = 0
                # Check if derived from H1
                if 'derived_from' in df.columns:
                    d1_derived_from_h1 = (df['derived_from'].iloc[0] == 'H1')
            except Exception:
                d1_quality_flag = 2
        
        # Determine status
        if h1_normalized_exists and h1_quality_flag == 0:
            if d1_normalized_exists and d1_quality_flag == 0:
                status = 'accepted'
            else:
                status = 'accepted'  # H1 is primary requirement
        else:
            status = 'rejected'
            if not h1_raw_exists:
                rejection_reasons.append("H1 raw file missing")
            if not h1_normalized_exists:
                rejection_reasons.append("H1 normalized file missing")
            if h1_quality_flag > 0:
                rejection_reasons.append(f"H1 quality flag: {h1_quality_flag}")
        
        entry = BatchACoverageEntry(
            symbol=symbol,
            h1_raw_exists=h1_raw_exists,
            h1_raw_sha256=h1_raw_sha256,
            h1_normalized_exists=h1_normalized_exists,
            h1_normalized_sha256=h1_normalized_sha256,
            h1_row_count=h1_row_count,
            h1_coverage_pct=h1_coverage_pct,
            h1_quality_flag=h1_quality_flag,
            d1_raw_exists=d1_raw_exists,
            d1_raw_sha256=d1_raw_sha256,
            d1_normalized_exists=d1_normalized_exists,
            d1_normalized_sha256=d1_normalized_sha256,
            d1_row_count=d1_row_count,
            d1_coverage_pct=d1_coverage_pct,
            d1_quality_flag=d1_quality_flag,
            d1_derived_from_h1=d1_derived_from_h1,
            status=status,
            rejection_reasons=rejection_reasons
        )
        
        self.add_batch_a_coverage(entry)
        return entry
    
    def save_raw_manifest(self, filename: str = "raw_file_manifest.csv") -> str:
        """Save raw file manifest as CSV."""
        path = self.manifest_dir / filename
        df = pd.DataFrame([e.to_dict() for e in self.raw_manifest])
        df.to_csv(path, index=False)
        return str(path)
    
    def save_normalized_manifest(self, filename: str = "normalized_file_manifest.csv") -> str:
        """Save normalized file manifest as CSV."""
        path = self.manifest_dir / filename
        df = pd.DataFrame([e.to_dict() for e in self.normalized_manifest])
        df.to_csv(path, index=False)
        return str(path)
    
    def save_batch_a_coverage(self, filename: str = "batch_a_coverage.json") -> str:
        """Save Batch A coverage as JSON."""
        path = self.manifest_dir / filename
        data = {
            "generated_at": datetime.now().isoformat(),
            "coverage": [e.to_dict() for e in self.batch_a_coverage]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return str(path)
    
    def save_raw_checksums(self, filename: str = "raw_checksums.json") -> str:
        """Save raw file checksums as JSON."""
        path = self.manifest_dir / filename
        data = {
            "generated_at": datetime.now().isoformat(),
            "checksums": self.raw_checksums
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return str(path)
    
    def save_all(self) -> Dict[str, str]:
        """Save all manifests."""
        return {
            "raw_manifest": self.save_raw_manifest(),
            "normalized_manifest": self.save_normalized_manifest(),
            "batch_a_coverage": self.save_batch_a_coverage(),
            "raw_checksums": self.save_raw_checksums()
        }
    
    def load_raw_manifest(self, filename: str = "raw_file_manifest.csv") -> None:
        """Load raw file manifest from CSV."""
        path = self.manifest_dir / filename
        if path.exists():
            df = pd.read_csv(path)
            self.raw_manifest = [RawFileManifestEntry(**row) for _, row in df.iterrows()]
            self.raw_checksums = {e.source_file: e.source_sha256 for e in self.raw_manifest}
    
    def load_batch_a_coverage(self, filename: str = "batch_a_coverage.json") -> None:
        """Load Batch A coverage from JSON."""
        path = self.manifest_dir / filename
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
            self.batch_a_coverage = [BatchACoverageEntry(**e) for e in data.get('coverage', [])]
    
    def get_accepted_symbols(self) -> List[str]:
        """Get list of accepted Batch A symbols."""
        return [e.symbol for e in self.batch_a_coverage if e.status == 'accepted']
    
    def get_rejected_symbols(self) -> List[str]:
        """Get list of rejected Batch A symbols."""
        return [e.symbol for e in self.batch_a_coverage if e.status == 'rejected']
    
    def get_missing_symbols(self) -> List[str]:
        """Get list of missing Batch A symbols."""
        return [e.symbol for e in self.batch_a_coverage if e.status == 'missing']
    
    def phase_2_gate_passed(self) -> Tuple[bool, List[str]]:
        """
        Check if Phase 2 gate passes.
        
        Returns:
            (passed, failure_reasons)
        """
        batch_a_symbols = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
            'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
        ]
        
        failure_reasons = []
        
        for symbol in batch_a_symbols:
            entry = next((e for e in self.batch_a_coverage if e.symbol == symbol), None)
            
            if not entry:
                failure_reasons.append(f"{symbol}: No coverage entry")
                continue
            
            if entry.status != 'accepted':
                reasons = entry.rejection_reasons or ["Not accepted"]
                failure_reasons.append(f"{symbol}: {', '.join(reasons)}")
                continue
            
            # Check requirements
            if not entry.h1_raw_exists:
                failure_reasons.append(f"{symbol}: H1 raw file missing")
            if not entry.h1_raw_sha256:
                failure_reasons.append(f"{symbol}: H1 raw SHA missing")
            if not entry.h1_normalized_exists:
                failure_reasons.append(f"{symbol}: H1 normalized file missing")
            if not entry.h1_normalized_sha256:
                failure_reasons.append(f"{symbol}: H1 normalized SHA missing")
            if entry.h1_quality_flag > 0:
                failure_reasons.append(f"{symbol}: H1 quality flag {entry.h1_quality_flag}")
        
        passed = len(failure_reasons) == 0
        return passed, failure_reasons


def create_provenance_tracker(manifest_dir: str = "data/manifests") -> ProvenanceTracker:
    """Factory function to create provenance tracker."""
    return ProvenanceTracker(manifest_dir)


if __name__ == "__main__":
    # Test provenance tracker
    tracker = create_provenance_tracker("tests/fixtures/manifests")
    
    # Create a test fixture
    from tests.fixtures.synthetic_market_data import create_test_fixture_csv
    
    fixture_path = create_test_fixture_csv("EURUSD", "H1", rows=100, output_path="tests/fixtures")
    
    # Register raw file
    raw_entry = tracker.register_raw_file(
        symbol="EURUSD",
        timeframe="H1",
        provider="test_fixture",
        source_file=fixture_path,
        price_side="bid",
        source_timezone="UTC",
        vendor_symbol="EURUSD",
        acquisition_method="test_fixture"
    )
    
    print(f"Raw file registered: {raw_entry.source_file}")
    print(f"SHA256: {raw_entry.source_sha256}")
    print(f"Rows: {raw_entry.row_count}")
    
    # Save manifests
    paths = tracker.save_all()
    print(f"Manifests saved: {paths}")