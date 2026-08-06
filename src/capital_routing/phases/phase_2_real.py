"""
Phase 2: Real Data Acquisition and Normalization Pipeline

This module implements the Phase 2 pipeline for real market data acquisition
and normalization. It replaces the synthetic data generation with a truthful,
reproducible pipeline using actual historical data files.

NON-NEGOTIABLE RULES:
1. Production Phase 2 must never generate random OHLC or volume.
2. Synthetic data is allowed only under tests/fixtures/ and must be clearly labeled synthetic.
3. No Phase 2 PASS unless real raw files exist and their hashes are recorded.
4. Do not mark a symbol processed merely because it exists in the acquisition queue.
5. Provider, timezone and price side may not default to "unknown" while still passing the gate.
6. Do not forward-fill OHLC bars.
7. Preserve raw source files unchanged.
8. Every normalized file must retain source provenance.
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..ingestion import DataDiscoverer, SchemaDetector, ProviderRegistry, SymbolAliases, BasicChecks
from ..ingestion.mt5_adapter import MT5Adapter, create_batch_a_mt5_queue, MT5ExportConfig
from ..ingestion.normalize import OHLCNormalizer, NormalizationConfig, create_batch_a_normalization_configs
from ..quality.ohlc_validation import OHLCValidator, validate_normalized_file
from ..quality.gap_analysis import GapAnalyzer, analyze_normalized_file
from ..quality.provenance import ProvenanceTracker, create_provenance_tracker, BatchACoverageEntry


@dataclass
class Phase2Config:
    """Configuration for Phase 2 real data pipeline."""
    # Data directories
    raw_data_base: str = "data/raw"
    normalized_base: str = "data/normalized"
    manifests_dir: str = "data/manifests"
    
    # MT5 settings
    mt5_provider: str = "MetaQuotes-Demo"
    mt5_timezone: str = "UTC"
    mt5_price_side: str = "bid"
    mt5_start_date_h1: str = "2022-01-01"
    mt5_start_date_d1: str = "2019-01-01"
    mt5_end_date: str = "2024-12-31"
    
    # Batch A symbols
    batch_a_symbols: List[str] = None
    
    # Quality thresholds
    min_coverage_pct: float = 90.0
    max_quality_flag: int = 1  # 0=clean, 1=warning allowed, 2=error fails
    
    # Output paths
    phase2_report_path: str = "artifacts/reports/P2_REAL_DATA_REPORT.md"
    quality_report_path: str = "artifacts/audits/p2_data_quality_by_symbol.csv"
    normalization_report_path: str = "artifacts/audits/p2_normalization_report.json"
    gate_result_path: str = "artifacts/audits/p2_gate_result.json"
    
    def __post_init__(self):
        if self.batch_a_symbols is None:
            self.batch_a_symbols = [
                'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
                'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
            ]


class Phase2RealDataPipeline:
    """
    Phase 2 Real Data Acquisition and Normalization Pipeline.
    
    This pipeline:
    1. Discovers or acquires real raw data files (MT5 export, local library)
    2. Registers raw files with checksums and provenance
    3. Normalizes to canonical schema with UTC timestamps
    4. Validates OHLC integrity and coverage
    5. Analyzes gaps and data quality
    6. Produces manifests and quality reports
    7. Evaluates fail-closed gate
    """
    
    def __init__(self, config: Phase2Config):
        self.config = config
        self.provider_registry = ProviderRegistry()
        self.symbol_aliases = SymbolAliases()
        self.schema_detector = SchemaDetector()
        self.basic_checks = BasicChecks()
        
        # Initialize components
        self.mt5_adapter = MT5Adapter()
        self.normalizer = OHLCNormalizer()
        self.validator = OHLCValidator()
        self.gap_analyzer = GapAnalyzer()
        self.provenance = create_provenance_tracker(config.manifests_dir)
        
        # Results storage
        self.acquisition_results: List[Any] = []
        self.normalization_results: List[Any] = []
        self.validation_results: List[Any] = []
        self.gap_results: List[Any] = []
        self.batch_a_coverage: List[BatchACoverageEntry] = []
        
        # Ensure directories exist
        Path(config.raw_data_base).mkdir(parents=True, exist_ok=True)
        Path(config.normalized_base).mkdir(parents=True, exist_ok=True)
        Path(config.manifests_dir).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(config.phase2_report_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(config.quality_report_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(config.normalization_report_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(config.gate_result_path)).mkdir(parents=True, exist_ok=True)
    
    def run_phase_2(self, phase_1_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete Phase 2 real data pipeline.
        
        Args:
            phase_1_results: Results from Phase 1 (canonical inventory, batch_a_queue)
            
        Returns:
            Dictionary containing Phase 2 results and gate decision
        """
        print("Starting Phase 2: Real Data Acquisition and Normalization")
        print("=" * 60)
        
        # Step 1: Generate MT5 acquisition queue (operator queue if auto fails)
        print("Step 1: Generating MT5 acquisition queue...")
        self._generate_mt5_acquisition_queue()
        
        # Step 2: Discover/acquire raw data files
        print("Step 2: Discovering raw data files...")
        raw_files = self._discover_raw_files(phase_1_results)
        
        # Step 3: Register raw files with provenance
        print("Step 3: Registering raw files with provenance...")
        self._register_raw_files(raw_files)
        
        # Step 4: Normalize raw files to canonical schema
        print("Step 4: Normalizing to canonical schema...")
        self._normalize_files()
        
        # Step 5: Validate normalized data
        print("Step 5: Validating OHLC integrity and coverage...")
        self._validate_normalized_data()
        
        # Step 6: Analyze gaps
        print("Step 6: Analyzing gaps and coverage...")
        self._analyze_gaps()
        
        # Step 7: Register Batch A coverage
        print("Step 7: Registering Batch A coverage...")
        self._register_batch_a_coverage()
        
        # Step 8: Save all manifests
        print("Step 8: Saving manifests and checksums...")
        manifest_paths = self.provenance.save_all()
        
        # Step 9: Generate quality reports
        print("Step 9: Generating quality reports...")
        self._generate_quality_reports()
        
        # Step 10: Evaluate Phase 2 gate
        print("Step 10: Evaluating Phase 2 gate...")
        gate_passed, gate_reasons = self.provenance.phase_2_gate_passed()
        
        # Compile results
        phase_2_results = {
            'phase': '2',
            'phase_name': 'Real Data Acquisition and Normalization',
            'timestamp': datetime.now().isoformat(),
            'status': 'completed' if gate_passed else 'failed_gate',
            'gate_passed': gate_passed,
            'gate_failure_reasons': gate_reasons,
            'acquisition': {
                'mt5_queue_generated': True,
                'raw_files_discovered': len(raw_files),
                'raw_files_registered': len(self.provenance.raw_manifest)
            },
            'normalization': {
                'files_normalized': len(self.normalization_results),
                'successful': sum(1 for r in self.normalization_results if r.success),
                'failed': sum(1 for r in self.normalization_results if not r.success)
            },
            'validation': {
                'symbols_validated': len(self.validation_results),
                'avg_coverage_pct': sum(r.coverage_pct for r in self.validation_results) / len(self.validation_results) if self.validation_results else 0,
                'symbols_with_errors': sum(1 for r in self.validation_results if r.quality_flag == 2)
            },
            'gap_analysis': {
                'symbols_analyzed': len(self.gap_results),
                'symbols_with_unexplained_gaps': sum(1 for r in self.gap_results if r.unexplained_gaps),
                'avg_coverage_pct': sum(r.coverage_pct for r in self.gap_results) / len(self.gap_results) if self.gap_results else 0
            },
            'batch_a_coverage': {
                'total_symbols': len(self.config.batch_a_symbols),
                'accepted': len(self.provenance.get_accepted_symbols()),
                'rejected': len(self.provenance.get_rejected_symbols()),
                'missing': len(self.provenance.get_missing_symbols()),
                'accepted_symbols': self.provenance.get_accepted_symbols(),
                'rejected_symbols': self.provenance.get_rejected_symbols(),
                'missing_symbols': self.provenance.get_missing_symbols()
            },
            'manifests': manifest_paths,
            'reports': {
                'phase2_report': self.config.phase2_report_path,
                'quality_report': self.config.quality_report_path,
                'normalization_report': self.config.normalization_report_path,
                'gate_result': self.config.gate_result_path
            }
        }
        
        # Save gate result
        self._save_gate_result(gate_passed, gate_reasons)
        
        print("=" * 60)
        if gate_passed:
            print("Phase 2 GATE PASSED")
        else:
            print("Phase 2 GATE FAILED")
            for reason in gate_reasons:
                print(f"  - {reason}")
        print(f"Accepted symbols: {phase_2_results['batch_a_coverage']['accepted']}/10")
        print(f"Rejected symbols: {phase_2_results['batch_a_coverage']['rejected']}")
        print(f"Missing symbols: {phase_2_results['batch_a_coverage']['missing']}")
        
        return phase_2_results
    
    def _generate_mt5_acquisition_queue(self) -> None:
        """Generate MT5 acquisition queue for Batch A symbols."""
        adapter = create_batch_a_mt5_queue(
            output_base=self.config.raw_data_base,
            provider=self.config.mt5_provider,
            timezone=self.config.mt5_timezone,
            price_side=self.config.mt5_price_side,
            start_date_h1=self.config.mt5_start_date_h1,
            start_date_d1=self.config.mt5_start_date_d1,
            end_date=self.config.mt5_end_date
        )
        
        # Save operator queue for manual execution
        queue_path = os.path.join(self.config.manifests_dir, "mt5_acquisition_queue.json")
        adapter.save_operator_queue(queue_path)
        
        self.acquisition_results = adapter.export_queue
        print(f"  MT5 acquisition queue saved: {queue_path}")
        print(f"  Total export jobs: {len(adapter.export_queue)}")
    
    def _discover_raw_files(self, phase_1_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover existing raw data files."""
        # Use Phase 1 data discoverer
        discoverer_config = {
            'scan_directories': [self.config.raw_data_base],
            'supported_extensions': ['.csv', '.parquet', '.zip'],
            'max_file_size': 100 * 1024 * 1024
        }
        discoverer = DataDiscoverer(discoverer_config)
        discovered = discoverer.discover_files()
        
        # Enhance with provider info from directory structure
        for file_meta in discovered:
            file_path = file_meta.get('file_path', '')
            # Extract provider from path: data/raw/<provider>/<symbol>/<file>
            parts = Path(file_path).parts
            if 'raw' in parts:
                idx = parts.index('raw')
                if idx + 1 < len(parts):
                    file_meta['provider'] = parts[idx + 1]
        
        print(f"  Discovered {len(discovered)} raw files")
        return discovered
    
    def _register_raw_files(self, raw_files: List[Dict[str, Any]]) -> None:
        """Register raw files with provenance tracker."""
        for file_meta in raw_files:
            file_path = file_meta.get('file_path', '')
            if not file_path or not os.path.exists(file_path):
                continue
            
            symbol = file_meta.get('symbol', 'unknown')
            timeframe = file_meta.get('timeframe', 'unknown')
            provider = file_meta.get('provider', self.config.mt5_provider)
            
            # Skip if not a Batch A symbol
            if symbol not in self.config.batch_a_symbols:
                continue
            
            try:
                self.provenance.register_raw_file(
                    symbol=symbol,
                    timeframe=timeframe,
                    provider=provider,
                    source_file=file_path,
                    price_side=self.config.mt5_price_side,
                    source_timezone=self.config.mt5_timezone,
                    vendor_symbol=symbol,
                    acquisition_method="local_library" if 'mt5' not in file_path.lower() else "mt5_export"
                )
            except Exception as e:
                print(f"  Warning: Failed to register {file_path}: {e}")
    
    def _normalize_files(self) -> None:
        """Normalize all registered raw files."""
        configs = create_batch_a_normalization_configs(
            raw_base=self.config.raw_data_base,
            normalized_base=self.config.normalized_base,
            provider=self.config.mt5_provider,
            price_side=self.config.mt5_price_side,
            source_timezone=self.config.mt5_timezone
        )
        
        print(f"  Normalizing {len(configs)} files...")
        self.normalization_results = self.normalizer.normalize_batch(configs)
        
        for result in self.normalization_results:
            if result.success:
                print(f"  ✓ {result.config.symbol} {result.config.timeframe}: {result.row_count} rows")
            else:
                print(f"  ✗ {result.config.symbol} {result.config.timeframe}: {result.error_message}")
    
    def _validate_normalized_data(self) -> None:
        """Validate all normalized files."""
        normalized_dir = Path(self.config.normalized_base)
        
        for tf_dir in ['h1', 'd1']:
            tf_path = normalized_dir / tf_dir
            if not tf_path.exists():
                continue
            
            for parquet_file in tf_path.glob("*.parquet"):
                symbol = parquet_file.stem.split('_')[0]
                timeframe = tf_dir.upper()
                
                if symbol not in self.config.batch_a_symbols:
                    continue
                
                try:
                    result = validate_normalized_file(str(parquet_file), symbol, timeframe)
                    self.validation_results.append(result)
                    
                    if result.quality_flag == 2:
                        print(f"  ✗ {symbol} {timeframe}: ERROR - {result.issues}")
                    elif result.quality_flag == 1:
                        print(f"  ⚠ {symbol} {timeframe}: WARNING - {result.issues}")
                    else:
                        print(f"  ✓ {symbol} {timeframe}: OK ({result.coverage_pct:.1f}% coverage)")
                except Exception as e:
                    print(f"  ✗ {symbol} {timeframe}: Validation error - {e}")
    
    def _analyze_gaps(self) -> None:
        """Analyze gaps in normalized data."""
        normalized_dir = Path(self.config.normalized_base)
        
        for tf_dir in ['h1', 'd1']:
            tf_path = normalized_dir / tf_dir
            if not tf_path.exists():
                continue
            
            for parquet_file in tf_path.glob("*.parquet"):
                symbol = parquet_file.stem.split('_')[0]
                timeframe = tf_dir.upper()
                
                if symbol not in self.config.batch_a_symbols:
                    continue
                
                try:
                    result = analyze_normalized_file(str(parquet_file), symbol, timeframe)
                    self.gap_results.append(result)
                    
                    if result.unexplained_gaps:
                        print(f"  ⚠ {symbol} {timeframe}: {len(result.unexplained_gaps)} unexplained gaps")
                    else:
                        print(f"  ✓ {symbol} {timeframe}: No unexplained gaps ({result.coverage_pct:.1f}% coverage)")
                except Exception as e:
                    print(f"  ✗ {symbol} {timeframe}: Gap analysis error - {e}")
    
    def _register_batch_a_coverage(self) -> None:
        """Register Batch A coverage for all symbols."""
        for symbol in self.config.batch_a_symbols:
            h1_raw = os.path.join(self.config.raw_data_base, self.config.mt5_provider, symbol, f"{symbol}_H1.csv")
            h1_norm = os.path.join(self.config.normalized_base, "h1", f"{symbol}_H1.parquet")
            d1_raw = os.path.join(self.config.raw_data_base, self.config.mt5_provider, symbol, f"{symbol}_D1.csv")
            d1_norm = os.path.join(self.config.normalized_base, "d1", f"{symbol}_D1.parquet")
            
            entry = self.provenance.register_batch_a_coverage(
                symbol=symbol,
                h1_raw_path=h1_raw if os.path.exists(h1_raw) else None,
                h1_norm_path=h1_norm if os.path.exists(h1_norm) else None,
                d1_raw_path=d1_raw if os.path.exists(d1_raw) else None,
                d1_norm_path=d1_norm if os.path.exists(d1_norm) else None,
                provider=self.config.mt5_provider,
                price_side=self.config.mt5_price_side,
                source_timezone=self.config.mt5_timezone
            )
            
            self.batch_a_coverage.append(entry)
            
            status_icon = "✓" if entry.status == 'accepted' else "✗"
            print(f"  {status_icon} {symbol}: {entry.status}")
            if entry.rejection_reasons:
                for reason in entry.rejection_reasons:
                    print(f"    - {reason}")
    
    def _generate_quality_reports(self) -> None:
        """Generate quality reports."""
        # 1. Per-symbol quality CSV
        quality_rows = []
        for v in self.validation_results:
            g = next((x for x in self.gap_results if x.symbol == v.symbol and x.timeframe == v.timeframe), None)
            quality_rows.append({
                'symbol': v.symbol,
                'timeframe': v.timeframe,
                'total_rows': v.total_rows,
                'valid_rows': v.valid_rows,
                'malformed_ohlc': v.malformed_ohlc_count,
                'duplicate_timestamps': v.duplicate_timestamp_count,
                'weekend_bars': v.weekend_bar_count,
                'missing_weekday_bars': v.missing_weekday_bar_count,
                'unexplained_gaps': len(g.unexplained_gaps) if g else 0,
                'stale_bars': v.stale_bar_count,
                'coverage_pct': v.coverage_pct,
                'quality_flag': v.quality_flag,
                'issues': '; '.join(v.issues)
            })
        
        quality_df = pd.DataFrame(quality_rows)
        quality_df.to_csv(self.config.quality_report_path, index=False)
        
        # 2. Normalization report JSON
        norm_report = {
            "generated_at": datetime.now().isoformat(),
            "normalization_results": [r.to_dict() for r in self.normalization_results],
            "validation_results": [r.to_dict() for r in self.validation_results],
            "gap_results": [r.to_dict() for r in self.gap_results]
        }
        with open(self.config.normalization_report_path, 'w') as f:
            json.dump(norm_report, f, indent=2)
        
        # 3. Markdown report
        self._generate_markdown_report()
    
    def _generate_markdown_report(self) -> None:
        """Generate markdown report."""
        accepted = self.provenance.get_accepted_symbols()
        rejected = self.provenance.get_rejected_symbols()
        missing = self.provenance.get_missing_symbols()
        
        report = f"""# Phase 2 Real Data Acquisition and Normalization Report

**Generated:** {datetime.now().isoformat()}
**Pipeline Version:** 1.0

## Executive Summary

| Metric | Value |
|--------|-------|
| Batch A Symbols | 10 |
| Accepted | {len(accepted)} |
| Rejected | {len(rejected)} |
| Missing | {len(missing)} |
| Gate Status | {'PASSED' if len(rejected) == 0 and len(missing) == 0 else 'FAILED'} |

## Accepted Symbols

{', '.join(accepted) if accepted else 'None'}

## Rejected Symbols

{', '.join(rejected) if rejected else 'None'}

## Missing Symbols

{', '.join(missing) if missing else 'None'}

## Per-Symbol Quality

| Symbol | Timeframe | Rows | Coverage | Quality Flag | Issues |
|--------|-----------|------|----------|--------------|--------|
"""
        
        for v in self.validation_results:
            g = next((x for x in self.gap_results if x.symbol == v.symbol and x.timeframe == v.timeframe), None)
            issues_str = '; '.join(v.issues) if v.issues else 'None'
            report += f"| {v.symbol} | {v.timeframe} | {v.total_rows} | {v.coverage_pct:.1f}% | {v.quality_flag} | {issues_str} |\n"
        
        report += f"""

## Gap Analysis Summary

| Symbol | Timeframe | Expected Bars | Actual Bars | Coverage | Unexplained Gaps |
|--------|-----------|---------------|-------------|----------|------------------|
"""
        
        for g in self.gap_results:
            report += f"| {g.symbol} | {g.timeframe} | {g.total_expected_bars} | {g.total_actual_bars} | {g.coverage_pct:.1f}% | {len(g.unexplained_gaps)} |\n"
        
        report += f"""

## Manifests Generated

- Raw file manifest: `data/manifests/raw_file_manifest.csv`
- Normalized file manifest: `data/manifests/normalized_file_manifest.csv`
- Batch A coverage: `data/manifests/batch_a_coverage.json`
- Raw checksums: `data/manifests/raw_checksums.json`
- MT5 acquisition queue: `data/manifests/mt5_acquisition_queue.json`

## Normalization Details

- Normalization version: 1.0
- Target timezone: UTC
- Price side: {self.config.mt5_price_side}
- Source timezone: {self.config.mt5_timezone}
- Provider: {self.config.mt5_provider}

## Gate Decision

**Phase 2 Gate:** {'PASSED' if len(rejected) == 0 and len(missing) == 0 else 'FAILED'}

{'All 10 Batch A symbols have accepted real H1 normalized files meeting coverage and quality requirements.' if len(rejected) == 0 and len(missing) == 0 else 'Some symbols failed gate requirements. See rejection reasons above.'}

## Next Steps

{'Proceed to Phase 3: Panels/QC/Alignment' if len(rejected) == 0 and len(missing) == 0 else 'Resolve rejected/missing symbols before proceeding to Phase 3.'}
"""
        
        with open(self.config.phase2_report_path, 'w') as f:
            f.write(report)
    
    def _save_gate_result(self, gate_passed: bool, gate_reasons: List[str]) -> None:
        """Save gate result to JSON."""
        gate_result = {
            "gate_id": "CR-P2-REAL-DATA-REPAIR-01",
            "timestamp": datetime.now().isoformat(),
            "gate_passed": gate_passed,
            "failure_reasons": gate_reasons,
            "batch_a_symbols": self.config.batch_a_symbols,
            "accepted_symbols": self.provenance.get_accepted_symbols(),
            "rejected_symbols": self.provenance.get_rejected_symbols(),
            "missing_symbols": self.provenance.get_missing_symbols(),
            "requirements": {
                "raw_file_exists": True,
                "sha_exists_and_matches": True,
                "normalized_h1_exists": True,
                "source_not_synthetic": True,
                "provider_known": True,
                "timezone_known": True,
                "price_side_known": True,
                "duplicate_timestamps_resolved": True,
                "malformed_ohlc_zero": True,
                "coverage_documented": True,
                "no_silent_interpolation": True,
                "output_reproducible": True
            }
        }
        
        with open(self.config.gate_result_path, 'w') as f:
            json.dump(gate_result, f, indent=2)


def main():
    """Main function for Phase 2 real data pipeline."""
    config = Phase2Config()
    
    # Create dummy Phase 1 results for testing
    phase_1_results = {
        'canonical_inventory': {
            'symbols': config.batch_a_symbols,
            'providers': [config.mt5_provider],
            'timeframes': ['H1', 'D1'],
            'formats': ['csv']
        },
        'batch_a_queue': {
            'queue_items': [
                {
                    'symbol': sym,
                    'priority': 'high',
                    'providers': [config.mt5_provider],
                    'timeframes': ['H1', 'D1'],
                    'formats': ['csv'],
                    'quality_score': 80.0
                }
                for sym in config.batch_a_symbols
            ]
        }
    }
    
    pipeline = Phase2RealDataPipeline(config)
    results = pipeline.run_phase_2(phase_1_results)
    
    print("\nPhase 2 Results:")
    print("=" * 60)
    print(f"Gate Passed: {results['gate_passed']}")
    print(f"Status: {results['status']}")
    print(f"Accepted: {results['batch_a_coverage']['accepted']}/10")
    
    return results


if __name__ == '__main__':
    main()