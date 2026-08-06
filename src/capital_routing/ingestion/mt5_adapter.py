"""
MT5 Historical Data Export Adapter

This module provides an interface to the user's existing MT5 historical
data export workflow. It does NOT execute live trading or broker-order
functions — historical export only.

The adapter documents and supports:
- symbol
- timeframe
- start date
- end date
- output path
- provider/broker
- timezone
- bid/ask/mid price side
- output format
- execution result
- raw file checksum
"""

import os
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class MT5ExportConfig:
    """Configuration for MT5 historical data export."""
    symbol: str
    timeframe: str  # e.g., 'H1', 'D1', 'H4'
    start_date: str  # ISO format: '2022-01-01'
    end_date: str    # ISO format: '2024-12-31'
    output_path: str
    provider: str    # e.g., 'MetaQuotes-Demo', 'ICMarkets-Live'
    timezone: str    # e.g., 'UTC', 'Europe/London', 'America/New_York'
    price_side: str  # 'bid', 'ask', 'mid'
    output_format: str = 'csv'  # 'csv' or 'parquet'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MT5ExportResult:
    """Result of MT5 historical data export."""
    success: bool
    config: MT5ExportConfig
    raw_file_path: Optional[str] = None
    raw_file_sha256: Optional[str] = None
    row_count: int = 0
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    error_message: Optional[str] = None
    export_timestamp: str = ""
    
    def __post_init__(self):
        if not self.export_timestamp:
            self.export_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MT5Adapter:
    """
    Adapter for MT5 historical data export.
    
    This adapter wraps the user's existing MT5 export script. It does not
    execute live trading functions — historical export only.
    
    If the MT5 script cannot be safely executed automatically, this adapter
    generates an exact operator queue with commands/parameters rather than
    fabricating files.
    """
    
    def __init__(self, mt5_script_path: Optional[str] = None):
        """
        Initialize MT5 adapter.
        
        Args:
            mt5_script_path: Path to the user's MT5 export script.
                           If None, will attempt to locate it.
        """
        self.mt5_script_path = mt5_script_path or self._locate_mt5_script()
        self.export_queue: List[MT5ExportConfig] = []
        self.export_results: List[MT5ExportResult] = []
    
    def _locate_mt5_script(self) -> Optional[str]:
        """Attempt to locate the user's MT5 export script."""
        # Common locations to check
        possible_paths = [
            "scripts/mt5_export.py",
            "tools/mt5_export.py",
            "quant-lab/tools/mt5_export.py",
            "mt5_export.py",
            os.path.expanduser("~/mt5_export.py"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def add_export_job(self, config: MT5ExportConfig) -> None:
        """Add an export job to the queue."""
        self.export_queue.append(config)
    
    def add_batch_a_exports(
        self,
        symbols: List[str],
        timeframes: List[str],
        start_date: str,
        end_date: str,
        output_base: str,
        provider: str,
        timezone: str,
        price_side: str
    ) -> None:
        """Add Batch A export jobs for all symbols and timeframes."""
        for symbol in symbols:
            for tf in timeframes:
                output_path = os.path.join(
                    output_base, "raw", provider, symbol, f"{symbol}_{tf}.csv"
                )
                config = MT5ExportConfig(
                    symbol=symbol,
                    timeframe=tf,
                    start_date=start_date,
                    end_date=end_date,
                    output_path=output_path,
                    provider=provider,
                    timezone=timezone,
                    price_side=price_side
                )
                self.add_export_job(config)
    
    def generate_operator_queue(self) -> List[Dict[str, Any]]:
        """
        Generate operator queue with exact commands/parameters.
        
        Returns:
            List of command dictionaries for manual execution.
        """
        queue = []
        for config in self.export_queue:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(config.output_path), exist_ok=True)
            
            # Build command based on script type
            if self.mt5_script_path and self.mt5_script_path.endswith('.py'):
                cmd = [
                    "python", self.mt5_script_path,
                    "--symbol", config.symbol,
                    "--timeframe", config.timeframe,
                    "--start", config.start_date,
                    "--end", config.end_date,
                    "--output", config.output_path,
                    "--provider", config.provider,
                    "--timezone", config.timezone,
                    "--price-side", config.price_side,
                    "--format", config.output_format
                ]
            else:
                # Generic MT5 terminal command template
                cmd = [
                    "mt5_terminal.exe",
                    f"/export:{config.output_path}",
                    f"/symbol:{config.symbol}",
                    f"/timeframe:{config.timeframe}",
                    f"/from:{config.start_date}",
                    f"/to:{config.end_date}"
                ]
            
            queue.append({
                "config": config.to_dict(),
                "command": cmd,
                "command_string": " ".join(cmd),
                "working_directory": os.path.dirname(self.mt5_script_path) if self.mt5_script_path else ".",
                "estimated_duration_seconds": 30,
                "requires_mt5_running": True,
                "notes": "Execute manually if automated export fails"
            })
        
        return queue
    
    def execute_export(self, config: MT5ExportConfig) -> MT5ExportResult:
        """
        Execute a single export job.
        
        Note: This requires MT5 terminal to be running and accessible.
        If automated execution fails, use generate_operator_queue() instead.
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(config.output_path), exist_ok=True)
        
        if not self.mt5_script_path:
            return MT5ExportResult(
                success=False,
                config=config,
                error_message="MT5 export script not found. Use generate_operator_queue() for manual execution."
            )
        
        try:
            # Build command
            cmd = [
                "python", self.mt5_script_path,
                "--symbol", config.symbol,
                "--timeframe", config.timeframe,
                "--start", config.start_date,
                "--end", config.end_date,
                "--output", config.output_path,
                "--provider", config.provider,
                "--timezone", config.timezone,
                "--price-side", config.price_side,
                "--format", config.output_format
            ]
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.path.dirname(self.mt5_script_path)
            )
            
            if result.returncode != 0:
                return MT5ExportResult(
                    success=False,
                    config=config,
                    error_message=f"Export failed: {result.stderr}"
                )
            
            # Verify output file
            if not os.path.exists(config.output_path):
                return MT5ExportResult(
                    success=False,
                    config=config,
                    error_message="Export completed but output file not found"
                )
            
            # Calculate checksum
            sha256 = self._calculate_sha256(config.output_path)
            
            # Get row count and timestamps
            row_count, first_ts, last_ts = self._analyze_export_file(config.output_path)
            
            return MT5ExportResult(
                success=True,
                config=config,
                raw_file_path=config.output_path,
                raw_file_sha256=sha256,
                row_count=row_count,
                first_timestamp=first_ts,
                last_timestamp=last_ts
            )
            
        except subprocess.TimeoutExpired:
            return MT5ExportResult(
                success=False,
                config=config,
                error_message="Export timed out after 5 minutes"
            )
        except Exception as e:
            return MT5ExportResult(
                success=False,
                config=config,
                error_message=f"Export error: {str(e)}"
            )
    
    def _calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _analyze_export_file(self, file_path: str) -> tuple:
        """Analyze exported CSV file for row count and timestamps."""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            row_count = len(df)
            
            # Try to find timestamp column
            timestamp_cols = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()]
            if timestamp_cols:
                ts_col = timestamp_cols[0]
                first_ts = str(df[ts_col].iloc[0]) if row_count > 0 else None
                last_ts = str(df[ts_col].iloc[-1]) if row_count > 0 else None
            else:
                first_ts = None
                last_ts = None
            
            return row_count, first_ts, last_ts
        except Exception:
            return 0, None, None
    
    def run_all_exports(self) -> List[MT5ExportResult]:
        """Run all queued exports."""
        results = []
        for config in self.export_queue:
            result = self.execute_export(config)
            results.append(result)
            self.export_results.append(result)
        return results
    
    def save_queue(self, path: str) -> None:
        """Save export queue to JSON file."""
        queue_data = {
            "generated_at": datetime.now().isoformat(),
            "mt5_script_path": self.mt5_script_path,
            "jobs": [config.to_dict() for config in self.export_queue]
        }
        with open(path, 'w') as f:
            json.dump(queue_data, f, indent=2)
    
    def save_results(self, path: str) -> None:
        """Save export results to JSON file."""
        results_data = {
            "completed_at": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.export_results]
        }
        with open(path, 'w') as f:
            json.dump(results_data, f, indent=2)
    
    def save_operator_queue(self, path: str) -> None:
        """Save operator queue with commands for manual execution."""
        queue = self.generate_operator_queue()
        queue_data = {
            "generated_at": datetime.now().isoformat(),
            "mt5_script_path": self.mt5_script_path,
            "operator_queue": queue
        }
        with open(path, 'w') as f:
            json.dump(queue_data, f, indent=2)


def create_batch_a_mt5_queue(
    output_base: str = "data",
    provider: str = "MetaQuotes-Demo",
    timezone: str = "UTC",
    price_side: str = "bid",
    start_date_h1: str = "2022-01-01",
    start_date_d1: str = "2019-01-01",
    end_date: str = "2024-12-31"
) -> MT5Adapter:
    """
    Create MT5 adapter pre-configured with Batch A export jobs.
    
    Args:
        output_base: Base output directory
        provider: Broker/provider name
        timezone: Source timezone
        price_side: 'bid', 'ask', or 'mid'
        start_date_h1: Start date for H1 data
        start_date_d1: Start date for D1 data
        end_date: End date for all exports
        
    Returns:
        Configured MT5Adapter instance
    """
    adapter = MT5Adapter()
    
    batch_a_symbols = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP',
        'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
    ]
    
    # H1 exports
    adapter.add_batch_a_exports(
        symbols=batch_a_symbols,
        timeframes=['H1'],
        start_date=start_date_h1,
        end_date=end_date,
        output_base=output_base,
        provider=provider,
        timezone=timezone,
        price_side=price_side
    )
    
    # D1 exports
    adapter.add_batch_a_exports(
        symbols=batch_a_symbols,
        timeframes=['D1'],
        start_date=start_date_d1,
        end_date=end_date,
        output_base=output_base,
        provider=provider,
        timezone=timezone,
        price_side=price_side
    )
    
    return adapter


if __name__ == "__main__":
    # Generate operator queue for Batch A
    adapter = create_batch_a_mt5_queue()
    adapter.save_operator_queue("data/manifests/mt5_acquisition_queue.json")
    print("MT5 acquisition queue saved to data/manifests/mt5_acquisition_queue.json")
    print(f"Total jobs: {len(adapter.export_queue)}")