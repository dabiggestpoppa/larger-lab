"""
Data discovery module for Capital Routing Research System.

This module implements the data discovery functionality required for Phase 1
of the Capital Routing Research System. It scans configured directories to
identify data files and extract metadata about them.
"""

import os
import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .schema_detection import SchemaDetector
from .provider_registry import ProviderRegistry
from .symbol_aliases import SymbolAliases


class DataDiscoverer:
    """Main data discovery class for the Capital Routing Research System."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data discoverer with configuration.
        
        Args:
            config: Configuration dictionary containing discovery settings
        """
        self.config = config
        self.schema_detector = SchemaDetector()
        self.provider_registry = ProviderRegistry()
        self.symbol_aliases = SymbolAliases()
        
        # Discovery settings
        self.scan_directories = config.get('scan_directories', [])
        self.supported_extensions = config.get('supported_extensions', ['.csv', '.parquet', '.zip'])
        self.max_file_size = config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        
    def discover_files(self) -> List[Dict[str, Any]]:
        """
        Discover all data files in configured directories.
        
        Returns:
            List of dictionaries containing file metadata
        """
        discovered_files = []
        
        for directory in self.scan_directories:
            if not os.path.exists(directory):
                continue
                
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if self._is_supported_file(file):
                        file_path = os.path.join(root, file)
                        file_metadata = self._extract_file_metadata(file_path)
                        if file_metadata:
                            discovered_files.append(file_metadata)
        
        return discovered_files
    
    def _is_supported_file(self, filename: str) -> bool:
        """
        Check if a file has a supported extension.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file extension is supported, False otherwise
        """
        # Check for supported extensions
        for ext in self.supported_extensions:
            if filename.lower().endswith(ext):
                return True
        
        # Check for compressed files
        if filename.lower().endswith('.zip'):
            return True
            
        return False
    
    def _extract_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a data file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata or None if extraction fails
        """
        try:
            # Get basic file information
            stat_info = os.stat(file_path)
            file_size = stat_info.st_size
            
            # Skip files that are too large
            if file_size > self.max_file_size:
                return None
            
            # Determine file type
            file_type = self._detect_file_type(file_path)
            
            # Extract metadata based on file type
            if file_type == 'csv':
                metadata = self._extract_csv_metadata(file_path)
            elif file_type == 'parquet':
                metadata = self._extract_parquet_metadata(file_path)
            elif file_type == 'zip':
                metadata = self._extract_zip_metadata(file_path)
            else:
                return None
            
            # Add basic file information
            metadata['file_path'] = file_path
            metadata['file_size'] = file_size
            metadata['last_modified'] = stat_info.st_mtime
            metadata['file_type'] = file_type
            
            return metadata
            
        except Exception as e:
            # Log error and return None
            print(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect the type of a data file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String indicating file type ('csv', 'parquet', 'zip', or 'unknown')
        """
        filename = os.path.basename(file_path).lower()
        
        if filename.endswith('.csv'):
            return 'csv'
        elif filename.endswith('.parquet') or filename.endswith('.parq'):
            return 'parquet'
        elif filename.endswith('.zip'):
            return 'zip'
        else:
            # Try to detect based on content
            return self._detect_file_type_by_content(file_path)
    
    def _detect_file_type_by_content(self, file_path: str) -> str:
        """
        Detect file type by examining content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String indicating file type
        """
        try:
            # Try to read first few lines to detect CSV
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if ',' in first_line or ';' in first_line:
                    return 'csv'
        except:
            pass
        
        # Default to unknown
        return 'unknown'
    
    def _extract_csv_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary containing CSV metadata
        """
        metadata = {
            'format': 'csv',
            'dialect': 'excel',
            'encoding': 'utf-8',
            'compression': 'none',
            'has_header': False,
            'columns': [],
            'row_count': 0,
            'estimated_size_mb': 0,
        }
        
        try:
            # Try to read CSV to get metadata
            df = pd.read_csv(file_path, nrows=0)
            metadata['columns'] = df.columns.tolist()
            metadata['has_header'] = True
            
            # Get row count
            metadata['row_count'] = len(df)
            
            # Estimate size
            metadata['estimated_size_mb'] = os.path.getsize(file_path) / (1024 * 1024)
            
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
            # Set default values
            metadata['has_header'] = False
            metadata['columns'] = []
            metadata['row_count'] = 0
            metadata['estimated_size_mb'] = os.path.getsize(file_path) / (1024 * 1024)
        
        return metadata
    
    def _extract_parquet_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a Parquet file.
        
        Args:
            file_path: Path to the Parquet file
            
        Returns:
            Dictionary containing Parquet metadata
        """
        metadata = {
            'format': 'parquet',
            'compression': 'unknown',
            'columns': [],
            'row_count': 0,
            'estimated_size_mb': 0,
        }
        
        try:
            # Try to read Parquet to get metadata
            df = pd.read_parquet(file_path)
            metadata['columns'] = df.columns.tolist()
            metadata['row_count'] = len(df)
            
            # Estimate size
            metadata['estimated_size_mb'] = os.path.getsize(file_path) / (1024 * 1024)
            
        except Exception as e:
            print(f"Error reading Parquet {file_path}: {e}")
            # Set default values
            metadata['columns'] = []
            metadata['row_count'] = 0
            metadata['estimated_size_mb'] = os.path.getsize(file_path) / (1024 * 1024)
        
        return metadata
    
    def _extract_zip_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a ZIP file.
        
        Args:
            file_path: part of the ZIP file
            
        Returns:
            Dictionary containing ZIP metadata
        """
        metadata = {
            'format': 'zip',
            'compression': 'unknown',
            'contained_files': [],
            'estimated_size_mb': 0,
        }
        
        try:
            # Get file size
            metadata['estimated_size_mb'] = os.path.getsize(file_path) / (1024 * 1024)
            
            # Try to list contents (simplified)
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zf:
                metadata['contained_files'] = zf.namelist()
                
        except Exception as e:
            print(f"Error reading ZIP {file_path}: {e}")
            # Set default values
            metadata['contained_files'] = []
        
        return metadata
    
    def analyze_symbol_coverage(self, discovered_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze symbol coverage from discovered files.
        
        Args:
            discovered_files: List of discovered file metadata
            
        Returns:
            Dictionary containing symbol coverage analysis
        """
        # Initialize coverage analysis
        coverage_analysis = {
            'total_files': len(discovered_files),
            'symbols_by_provider': {},
            'timeframes': {},
            'formats': {},
            'coverage_gaps': [],
        }
        
        # Analyze each file
        for file_metadata in discovered_files:
            # Get symbol information
            symbol = file_metadata.get('symbol', 'unknown')
            provider = file_metadata.get('provider', 'unknown')
            timeframe = file_metadata.get('timeframe', 'unknown')
            file_format = file_metadata.get('format', 'unknown')
            
            # Update symbol coverage
            if provider not in coverage_analysis['symbols_by_provider']:
                coverage_analysis['symbols_by_provider'][provider] = []
            coverage_analysis['symbols_by_provider'][provider].append(symbol)
            
            # Update timeframe coverage
            if timeframe not in coverage_analysis['timeframes']:
                coverage_analysis['timeframes'][timeframe] = []
            coverage_analysis['timeframes'][timeframe].append(symbol)
            
            # Update format coverage
            if file_format not in coverage_analysis['formats']:
                coverage_analysis['formats'][file_format] = []
            coverage_analysis['formats'][file_format].append(symbol)
        
        # Identify coverage gaps
        coverage_analysis['coverage_gaps'] = self._identify_coverage_gaps(
            coverage_analysis['symbols_by_provider']
        )
        
        return coverage_analysis
    
    def _identify_coverage_gaps(self, symbols_by_provider: Dict[str, List[str]]) -> List[str]:
        """
        Identify gaps in symbol coverage.
        
        Args:
            symbols_by_provider: Dictionary mapping providers to symbols
            
        Returns:
            List of coverage gap descriptions
        """
        gaps = []
        
        # Check for missing Batch A symbols
        batch_a_symbols = {
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 
            'CHFJPY', 'EURCHF', 'GBPCHF'
        }
        
        # Get all symbols from all providers
        all_symbols = []
        for provider_symbols in symbols_by_provider.values():
            all_symbols.extend(provider_symbols)
        
        # Find missing Batch A symbols
        missing_batch_a = batch_a_symbols - set(all_symbols)
        if missing_batch_a:
            gaps.append(f"Missing Batch A symbols: {', '.join(sorted(missing_batch_a))}")
        
        return gaps
    
    def generate_discovery_report(self, discovered_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive discovery report.
        
        Args:
            discovered_files: List of discovered file metadata
            
        Returns:
            Dictionary containing discovery report
        """
        report = {
            'discovery_timestamp': datetime.now().isoformat(),
            'total_files_discovered': len(discovered_files),
            'file_types': {},
            'providers': {},
            'timeframes': {},
            'quality_metrics': {},
            'recommendations': [],
        }
        
        # Analyze file types
        for file_metadata in discovered_files:
            file_type = file_metadata.get('file_type', 'unknown')
            if file_type not in report['file_types']:
                report['file_types'][file_type] = 0
            report['file_types'][file_type] += 1
        
        # Analyze providers
        for file_metadata in discovered_files:
            provider = file_metadata.get('provider', 'unknown')
            symbol = file_metadata.get('symbol', 'unknown')
            if provider not in report['providers']:
                report['providers'][provider] = []
            if symbol not in report['providers'][provider]:
                report['providers'][provider].append(symbol)
        
        # Analyze timeframes
        for file_metadata in discovered_files:
            timeframe = file_metadata.get('timeframe', 'unknown')
            if timeframe not in report['timeframes']:
                report['timeframes'][timeframe] = 0
            report['timeframes'][timeframe] += 1
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on discovery report.
        
        Args:
            report: Discovery report
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for missing Batch A symbols
        batch_a_symbols = {
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 
            'CHFJPY', 'EURCHF', 'GBPCHF'
        }
        
        # Get all symbols from report
        all_symbols = []
        for provider_symbols in report['providers'].items():
            all_symbols.extend(provider_symbols[1])
        
        # Check for missing Batch A symbols
        missing_batch_a = batch_a_symbols - set(all_symbols)
        if missing_batch_a:
            recommendations.append(
                f"Add missing Batch A symbols: {', '.join(sorted(missing_batch_a))}"
            )
        
        # Check for data quality issues
        if report['file_types'].get('unknown', 0) > 0:
            recommendations.append(
                "Investigate files with unknown format for potential data quality issues"
            )
        
        # Check for provider diversity
        if len(report['providers']) < 2:
            recommendations.append(
                "Consider adding data from additional providers for redundancy"
            )
        
        return recommendations