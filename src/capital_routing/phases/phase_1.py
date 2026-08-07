"""
Phase 1: Data Discovery Pipeline for Capital Routing Research System.

This module implements the complete Phase 1 data discovery pipeline,
including canonical inventory generation and Batch A queue creation.
"""

import os
import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path

from ..ingestion import (
    DataDiscoverer,
    SchemaDetector,
    ProviderRegistry,
    SymbolAliases,
    BasicChecks,
)


class Phase1DataDiscovery:
    """Phase 1 data discovery pipeline for Capital Routing Research System."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Phase 1 data discovery pipeline.
        
        Args:
            config: Configuration dictionary containing pipeline settings
        """
        self.config = config
        self.provider_registry = ProviderRegistry()
        self.symbol_aliases = SymbolAliases()
        self.schema_detector = SchemaDetector()
        self.basic_checks = BasicChecks()
        
        # Phase 1 specific settings
        self.canonical_inventory_path = config.get(
            'canonical_inventory_path',
            'canonical_inventory.json'
        )
        self.batch_a_queue_path = config.get(
            'batch_a_queue_path',
            'batch_a_queue.json'
        )
        self.discovery_report_path = config.get(
            'discovery_report_path',
            'discovery_report.json'
        )
        
        # Initialize data discoverer
        self.data_discoverer = DataDiscoverer(config)
    
    def run_phase_1(self) -> Dict[str, Any]:
        """
        Run the complete Phase 1 data discovery pipeline.
        
        Returns:
            Dictionary containing Phase 1 results
        """
        print("Starting Phase 1: Data Discovery Pipeline")
        print("=" * 50)
        
        # Step 1: Discover data files
        print("Step 1: Discovering data files...")
        discovered_files = self._discover_data_files()
        
        # Step 2: Analyze symbol coverage
        print("Step 2: Analyzing symbol coverage...")
        symbol_coverage = self._analyze_symbol_coverage(discovered_files)
        
        # Step 3: Generate canonical inventory
        print("Step 3: Generating canonical inventory...")
        canonical_inventory = self._generate_canonical_inventory(
            discovered_files, symbol_coverage
        )
        
        # Step 4: Create Batch A queue
        print("Step 4: Creating Batch A queue...")
        batch_a_queue = self._create_batch_a_queue(canonical_inventory)
        
        # Step 5: Generate discovery report
        print("Step 5: Generating discovery report...")
        discovery_report = self._generate_discovery_report(
            discovered_files, symbol_coverage, canonical_inventory, batch_a_queue
        )
        
        # Step 6: Save results
        print("Step 6: Saving results...")
        self._save_phase_1_results(
            canonical_inventory, batch_a_queue, discovery_report
        )
        
        # Compile Phase 1 results
        phase_1_results = {
            'phase': '1',
            'phase_name': 'Data Discovery',
            'timestamp': datetime.now().isoformat(),
            'discovered_files_count': len(discovered_files),
            'canonical_inventory': canonical_inventory,
            'batch_a_queue': batch_a_queue,
            'discovery_report': discovery_report,
            'status': 'completed',
        }
        
        print("=" * 50)
        print("Phase 1 completed successfully!")
        print(f"Discovered {len(discovered_files)} data files")
        print(f"Generated canonical inventory with {len(canonical_inventory.get('symbols', []))} symbols")
        print(f"Created Batch A queue with {len(batch_a_queue.get('queue', []))} items")
        
        return phase_1_results
    
    def _discover_data_files(self) -> List[Dict[str, Any]]:
        """
        Discover data files using the data discoverer.
        
        Returns:
            List of discovered file metadata
        """
        # Discover files
        discovered_files = self.data_discoverer.discover_files()
        
        # Enhance file metadata with additional information
        enhanced_files = []
        for file_metadata in discovered_files:
            enhanced_metadata = self._enhance_file_metadata(file_metadata)
            enhanced_files.append(enhanced_metadata)
        
        return enhanced_files
    
    def _enhance_file_metadata(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance file metadata with additional information.
        
        Args:
            file_metadata: Original file metadata
            
        Returns:
            Enhanced file metadata
        """
        # Create enhanced metadata
        enhanced_metadata = file_metadata.copy()
        
        # Add provider information
        enhanced_metadata['provider'] = self._determine_provider(file_metadata)
        
        # Add symbol information
        enhanced_metadata['symbol'] = self._extract_symbol(file_metadata)
        
        # Add timeframe information
        enhanced_metadata['timeframe'] = self._extract_timeframe(file_metadata)
        
        # Add quality score
        enhanced_metadata['quality_score'] = self._calculate_file_quality_score(file_metadata)
        
        # Add discovery timestamp
        enhanced_metadata['discovered_at'] = datetime.now().isoformat()
        
        return enhanced_metadata
    
    def _determine_provider(self, file_metadata: Dict[str, Any]) -> str:
        """
        Determine provider for a file.
        
        Args:
            file_metadata: File metadata
            
        Returns:
            Provider name
        """
        file_path = file_metadata.get('file_path', '')
        file_name = os.path.basename(file_path).lower()
        dir_path = os.path.dirname(file_path).lower()
        
        # Determine provider based on file name or path
        if 'nautilus' in file_name or 'nautilus' in dir_path:
            return 'nautilus'
        elif 'rekey' in file_name or 'rekey' in dir_path:
            return 'rekey'
        elif 'cerebus' in file_name or 'cerebus' in dir_path:
            return 'cerebus'
        elif 'oanda' in file_name or 'oanda' in dir_path:
            return 'oanda'
        elif 'dukascopy' in file_name or 'dukascopy' in dir_path:
            return 'dukascopy'
        elif 'mt5_pro' in dir_path or 'pro' in file_name or '_pro_' in file_name:
            return 'mt5_pro'
        elif 'mt5_fetched' in dir_path or 'fetched' in file_name:
            return 'mt5_fetched'
        else:
            return 'unknown'
    
    def _extract_symbol(self, file_metadata: Dict[str, Any]) -> str:
        """
        Extract symbol from file metadata.
        
        Args:
            file_metadata: File metadata
            
        Returns:
            Symbol
        """
        file_path = file_metadata.get('file_path', '')
        file_name = os.path.basename(file_path)
        
        # Extract symbol from file name
        # Common patterns: SYMBOL_TIMEFRAME.csv, SYMBOL_DATA.csv, etc.
        symbol_patterns = [
            r'^([A-Z]{6})_.*$',  # EURUSD_20230101.csv
            r'^([A-Z]{3}[A-Z]{3})_.*$',  # EURUSD_20230101.csv
            r'^([A-Z]{3}USD)_.*$',  # XAUUSD_20230101.csv
            r'^([A-Z]{3,4})$',  # SPX, DXY, etc.
        ]
        
        for pattern in symbol_patterns:
            match = re.match(pattern, file_name)
            if match:
                return match.group(1)
        
        # Default to unknown
        return 'unknown'
    
    def _extract_timeframe(self, file_metadata: Dict[str, Any]) -> str:
        """
        Extract timeframe from file metadata.
        
        Args:
            file_metadata: File metadata
            
        Returns:
            Timeframe
        """
        file_path = file_metadata.get('file_path', '')
        file_name = os.path.basename(file_path)
        
        # Extract timeframe from file name
        # Common patterns: SYMBOL_TIMEFRAME.csv, SYMBOL_DATA.csv, etc.
        timeframe_patterns = [
            r'.*_(\d+)m\.csv$',  # SYMBOL_5m.csv
            r'.*_(\d+)h\.csv$',  # SYMBOL_1h.csv
            r'.*_(\d+)d\.csv$',  # SYMBOL_1d.csv
            r'.*_(\d+)w\.csv$',  # SYMBOL_1w.csv
            r'.*_(\d+)M\.csv$',  # SYMBOL_1M.csv
            r'.*_H(\d+)\.csv$',  # SYMBOL_H1.csv
            r'.*_(\d+)min\.csv$',  # SYMBOL_5min.csv
            r'.*_(\d+)hour\.csv$',  # SYMBOL_1hour.csv
            r'.*_(\d+)day\.csv$',  # SYMBOL_1day.csv
            r'.*_PRO_(\w+)\.csv$',  # SYMBOL_PRO_D1.csv, SYMBOL_PRO_M5.csv, etc.
            r'.*_M(\d+)\.csv$',  # SYMBOL_M5.csv
            r'.*_(M5|M15|M30|H1|H4|D1|W1|MN1)\.csv$',  # SYMBOL_M5.csv, SYMBOL_D1.csv, etc.
        ]
        
        for pattern in timeframe_patterns:
            match = re.match(pattern, file_name)
            if match:
                timeframe = match.group(1)
                if pattern.endswith('m\.csv$') or pattern.endswith('min\.csv$'):
                    return f'{timeframe}m'
                elif pattern.endswith('h\.csv$') or pattern.endswith('hour\.csv$') or pattern.endswith('H(\d+)\.csv$'):
                    return f'{timeframe}h'
                elif pattern.endswith('d\.csv$') or pattern.endswith('day\.csv$'):
                    return f'{timeframe}d'
                elif pattern.endswith('w\.csv$'):
                    return f'{timeframe}w'
                elif pattern.endswith('M\.csv$'):
                    return f'{timeframe}M'
                elif pattern.endswith('PRO_(\w+)\.csv$'):
                    # Handle PRO_D1, PRO_M5, PRO_MN1, PRO_W1
                    tf = timeframe.upper()
                    if tf == 'D1':
                        return 'D1'
                    elif tf == 'W1':
                        return 'W1'
                    elif tf == 'MN1':
                        return 'MN1'
                    elif tf.startswith('M'):
                        return tf
                    return tf
                elif pattern.endswith('(M5|M15|M30|H1|H4|D1|W1|MN1)\.csv$'):
                    return timeframe.upper()
        
        # Default to unknown
        return 'unknown'
    
    def _calculate_file_quality_score(self, file_metadata: Dict[str, Any]) -> float:
        """
        Calculate quality score for a file.
        
        Args:
            file_metadata: File metadata
            
        Returns:
            Quality score (0-100)
        """
        score = 0.0
        max_score = 100.0
        
        # Check file size
        file_size = file_metadata.get('file_size', 0)
        if file_size > 0:
            # Penalize very large files
            if file_size > 100 * 1024 * 1024:  # 100MB
                score -= 10
            elif file_size > 10 * 1024 * 1024:  # 10MB
                score -= 5
        
        # Check file type
        file_type = file_metadata.get('file_type', 'unknown')
        if file_type == 'csv':
            score += 20
        elif file_type == 'parquet':
            score += 30
        elif file_type == 'zip':
            score += 10
        
        # Check for required metadata
        if 'columns' in file_metadata:
            score += 20
        
        if 'row_count' in file_metadata:
            score += 20
        
        # Ensure score is within bounds
        score = max(0.0, min(score, max_score))
        
        return score
    
    def _analyze_symbol_coverage(self, discovered_files: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            'quality_metrics': {},
        }
        
        # Analyze each file
        for file_metadata in discovered_files:
            # Get symbol information
            symbol = file_metadata.get('symbol', 'unknown')
            provider = file_metadata.get('provider', 'unknown')
            timeframe = file_metadata.get('timeframe', 'unknown')
            file_format = file_metadata.get('file_type', 'unknown')
            quality_score = file_metadata.get('quality_score', 0.0)
            
            # Update symbol coverage
            if provider not in coverage_analysis['symbols_by_provider']:
                coverage_analysis['symbols_by_provider'][provider] = []
            if symbol not in coverage_analysis['symbols_by_provider'][provider]:
                coverage_analysis['symbols_by_provider'][provider].append(symbol)
            
            # Update timeframe coverage
            if timeframe not in coverage_analysis['timeframes']:
                coverage_analysis['timeframes'][timeframe] = []
            if symbol not in coverage_analysis['timeframes'][timeframe]:
                coverage_analysis['timeframes'][timeframe].append(symbol)
                coverage_analysis['timeframes'][timeframe].append(symbol)
            
            # Update format coverage
            if file_format not in coverage_analysis['formats']:
                coverage_analysis['formats'][file_format] = []
            if symbol not in coverage_analysis['formats'][file_format]:
                coverage_analysis['formats'][file_format].append(symbol)
            
            # Update quality metrics
            if quality_score > 0:
                if 'quality_scores' not in coverage_analysis['quality_metrics']:
                    coverage_analysis['quality_metrics']['quality_scores'] = []
                coverage_analysis['quality_metrics']['quality_scores'].append(quality_score)
        
        # Calculate average quality score
        if 'quality_scores' in coverage_analysis['quality_metrics']:
            quality_scores = coverage_analysis['quality_metrics']['quality_scores']
            coverage_analysis['quality_metrics']['average_quality_score'] = (
                sum(quality_scores) / len(quality_scores)
            )
        
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
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
            'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
        }
        
        # Get all symbols from all providers
        all_symbols = []
        for provider_symbols in symbols_by_provider.values():
            all_symbols.extend(provider_symbols)
        
        # Find missing Batch A symbols
        missing_batch_a = batch_a_symbols - set(all_symbols)
        if missing_batch_a:
            gaps.append(
                f"Missing Batch A symbols: {', '.join(sorted(missing_batch_a))}"
            )
        
        return gaps
    
    def _generate_canonical_inventory(self, 
                                     discovered_files: List[Dict[str, Any]], 
                                     symbol_coverage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate canonical inventory from discovered files.
        
        Args:
            discovered_files: List of discovered file metadata
            symbol_coverage: Symbol coverage analysis
            
        Returns:
            Dictionary containing canonical inventory
        """
        # Initialize canonical inventory
        canonical_inventory = {
            'inventory_timestamp': datetime.now().isoformat(),
            'total_files': len(discovered_files),
            'providers': list(symbol_coverage['symbols_by_provider'].keys()),
            'symbols': [],
            'timeframes': list(symbol_coverage['timeframes'].keys()),
            'formats': list(symbol_coverage['formats'].keys()),
            'quality_metrics': symbol_coverage.get('quality_metrics', {}),
            'coverage_gaps': symbol_coverage.get('coverage_gaps', []),
        }
        
        # Get all unique symbols
        all_symbols = set()
        for provider_symbols in symbol_coverage['symbols_by_provider'].values():
            all_symbols.update(provider_symbols)
        
        # Add symbols to canonical inventory
        canonical_inventory['symbols'] = sorted(list(all_symbols))
        
        # Add symbol details
        canonical_inventory['symbol_details'] = {}
        for symbol in canonical_inventory['symbols']:
            canonical_inventory['symbol_details'][symbol] = {
                'providers': [
                    provider for provider, symbols in symbol_coverage['symbols_by_provider'].items()
                    if symbol in symbols
                ],
                'timeframes': [
                    timeframe for timeframe, symbols in symbol_coverage['timeframes'].items()
                    if symbol in symbols
                ],
                'formats': [
                    format for format, symbols in symbol_coverage['formats'].items()
                    if symbol in symbols
                ],
                'quality_score': self._calculate_symbol_quality_score(
                    symbol, symbol_coverage
                ),
            }
        
        return canonical_inventory
    
    def _calculate_symbol_quality_score(self, 
                                      symbol: str, 
                                      symbol_coverage: Dict[str, Any]) -> float:
        """
        Calculate quality score for a symbol.
        
        Args:
            symbol: Symbol to calculate score for
            symbol_coverage: Symbol coverage analysis
            
        Returns:
            Quality score (0-100)
        """
        score = 0.0
        max_score = 100.0
        
        # Check if symbol is in Batch A
        batch_a_symbols = {
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
            'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
        }
        
        if symbol in batch_a_symbols:
            score += 30
        
        # Check provider diversity
        providers = [
            provider for provider, symbols in symbol_coverage['symbols_by_provider'].items()
            if symbol in symbols
        ]
        
        if len(providers) > 1:
            score += 20
        elif len(providers) == 1:
            score += 10
        
        # Check timeframe diversity
        timeframes = [
            timeframe for timeframe, symbols in symbol_coverage['timeframes'].items()
            if symbol in symbols
        ]
        
        if len(timeframes) > 2:
            score += 20
        elif len(timeframes) == 2:
            score += 15
        elif len(timeframes) == 1:
            score += 10
        
        # Check format diversity
        formats = [
            format for format, symbols in symbol_coverage['formats'].items()
            if symbol in symbols
        ]
        
        if len(formats) > 1:
            score += 20
        elif len(formats) == 1:
            score += 10
        
        # Ensure score is within bounds
        score = max(0.0, min(score, max_score))
        
        return score
    
    def _create_batch_a_queue(self, canonical_inventory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Batch A queue from canonical inventory.
        
        Args:
            canonical_inventory: Canonical inventory
            
        Returns:
            Dictionary containing Batch A queue
        """
        # Initialize Batch A queue
        batch_a_queue = {
            'queue_timestamp': datetime.now().isoformat(),
            'queue_id': f"batch_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'priority': 'high',
            'estimated_processing_time': '2-4 hours',
            'queue_items': [],
            'processing_status': 'pending',
        }
        
        # Get Batch A symbols
        batch_a_symbols = {
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
            'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
        }
        
        # Create queue items for Batch A symbols
        for symbol in canonical_inventory['symbols']:
            if symbol in batch_a_symbols:
                queue_item = {
                    'symbol': symbol,
                    'priority': 'high',
                    'estimated_processing_time': '30-60 minutes',
                    'status': 'pending',
                    'providers': canonical_inventory['symbol_details'][symbol]['providers'],
                    'timeframes': canonical_inventory['symbol_details'][symbol]['timeframes'],
                    'formats': canonical_inventory['symbol_details'][symbol]['formats'],
                    'quality_score': canonical_inventory['symbol_details'][symbol]['quality_score'],
                }
                
                batch_a_queue['queue_items'].append(queue_item)
        
        # Sort queue items by priority and quality score
        batch_a_queue['queue_items'].sort(
            key=lambda x: (x['priority'] == 'low', x['quality_score']),
            reverse=True
        )
        
        return batch_a_queue
    
    def _generate_discovery_report(self, 
                                 discovered_files: List[Dict[str, Any]], 
                                 symbol_coverage: Dict[str, Any], 
                                 canonical_inventory: Dict[str, Any], 
                                 batch_a_queue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate discovery report.
n        
        Args:
            discovered_files: List of discovered file metadata
            symbol_coverage: Symbol coverage analysis
            canonical_inventory: Canonical inventory
            batch_a_queue: Batch A queue
            
        Returns:
            Dictionary containing discovery report
        """
        # Initialize discovery report
        discovery_report = {
            'report_timestamp': datetime.now().isoformat(),
            'report_id': f"discovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'total_files_discovered': len(discovered_files),
            'total_symbols': len(canonical_inventory['symbols']),
            'total_providers': len(canonical_inventory['providers']),
            'total_timeframes': len(canonical_inventory['timeframes']),
            'total_formats': len(canonical_inventory['formats']),
            'average_quality_score': canonical_inventory['quality_metrics'].get(
                'average_quality_score', 0.0
            ),
            'coverage_gaps': canonical_inventory['coverage_gaps'],
            'batch_a_queue_size': len(batch_a_queue['queue_items']),
            'recommendations': self._generate_recommendations(
                discovered_files, symbol_coverage, canonical_inventory, batch_a_queue
            ),
        }
        
        return discovery_report
    
    def _generate_recommendations(self, 
                                 discovered_files: List[Dict[str, Any]], 
                                 symbol_coverage: Dict[str, Any], 
                                 canonical_inventory: Dict[str, Any], 
                                 batch_a_queue: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on discovery results.
        
        Args:
            discovered_files: List of discovered file metadata
            symbol_coverage: Symbol coverage analysis
            canonical_inventory: Canonical inventory
            batch_a_queue: Batch A queue
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check for missing Batch A symbols
        batch_a_symbols = {
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
            'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
        }
        
        # Get all symbols from canonical inventory
        all_symbols = set(canonical_inventory['symbols'])
        
        # Find missing Batch A symbols
        missing_batch_a = batch_a_symbols - all_symbols
        if missing_batch_a:
            recommendations.append(
                f"Add missing Batch A symbols: {', '.join(sorted(missing_batch_a))}"
            )
        
        # Check for data quality issues
        if canonical_inventory['quality_metrics'].get('average_quality_score', 0.0) < 50.0:
            recommendations.append(
                "Investigate data quality issues - average quality score is below threshold"
            )
        
        # Check for provider diversity
        if len(canonical_inventory['providers']) < 2:
            recommendations.append(
                "Consider adding data from additional providers for redundancy"
            )
        
        # Check for timeframe diversity
        if len(canonical_inventory['timeframes']) < 2:
            recommendations.append(
                "Consider adding data from additional timeframes for comprehensive analysis"
            )
        
        # Check for format diversity
        if len(canonical_inventory['formats']) < 2:
            recommendations.append(
                "Consider adding data from additional formats for flexibility"
            )
        
        # Check for coverage gaps
        if canonical_inventory['coverage_gaps']:
            recommendations.extend(canonical_inventory['coverage_gaps'])
        
        return recommendations
    
    def _save_phase_1_results(self, 
                             canonical_inventory: Dict[str, Any], 
                             batch_a_queue: Dict[str, Any], 
                             discovery_report: Dict[str, Any]):
        """
        Save Phase 1 results to files.
        
        Args:
            canonical_inventory: Canonical inventory
            batch_a_queue: Batch A queue
            discovery_report: Discovery report
        """
        # Save canonical inventory
        canon_dir = os.path.dirname(self.canonical_inventory_path)
        if canon_dir:
            os.makedirs(canon_dir, exist_ok=True)
        with open(self.canonical_inventory_path, 'w') as f:
            json.dump(canonical_inventory, f, indent=2, default=str)
        
        # Save Batch A queue
        batch_dir = os.path.dirname(self.batch_a_queue_path)
        if batch_dir:
            os.makedirs(batch_dir, exist_ok=True)
        with open(self.batch_a_queue_path, 'w') as f:
            json.dump(batch_a_queue, f, indent=2, default=str)
        
        # Save discovery report
        disc_dir = os.path.dirname(self.discovery_report_path)
        if disc_dir:
            os.makedirs(disc_dir, exist_ok=True)
        with open(self.discovery_report_path, 'w') as f:
            json.dump(discovery_report, f, indent=2, default=str)


def main():
    """Main function for Phase 1 data discovery."""
    # Create default configuration
    config = {
        'scan_directories': [
            'data',
            'input',
            'raw_data',
            'sources',
        ],
        'supported_extensions': ['.csv', '.parquet', '.zip'],
        'max_file_size': 100 * 1024 * 1024,  # 100MB
        'canonical_inventory_path': 'canonical_inventory.json',
        'batch_a_queue_path': 'batch_a_queue.json',
        'discovery_report_path': 'discovery_report.json',
    }
    
    # Create Phase 1 data discovery pipeline
    phase_1 = Phase1DataDiscovery(config)
    
    # Run Phase 1
    results = phase_1.run_phase_1()
    
    # Print results
    print("\nPhase 1 Results:")
    print("=" * 50)
    print(f"Phase: {results['phase']}")
    print(f"Phase Name: {results['phase_name']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Status: {results['status']}")
    print(f"Discovered Files: {results['discovered_files_count']}")
    print(f"Canonical Inventory Symbols: {len(results['canonical_inventory']['symbols'])}")
    print(f"Batch A Queue Items: {len(results['batch_a_queue']['queue_items'])}")
    
    return results


if __name__ == '__main__':
    main()