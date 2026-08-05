"""
Phase 2: Data Processing Pipeline for Capital Routing Research System.

This module implements the complete Phase 2 data processing pipeline,
including data validation, transformation, and enrichment.
"""

import os
import json
import pandas as pd
import numpy as np
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


class Phase2DataProcessing:
    """Phase 2 data processing pipeline for Capital Routing Research System."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Phase 2 data processing pipeline.
        
        Args:
            config: Configuration dictionary containing pipeline settings
        """
        self.config = config
        self.provider_registry = ProviderRegistry()
        self.symbol_aliases = SymbolAliases()
        self.schema_detector = SchemaDetector()
        self.basic_checks = BasicChecks()
        
        # Phase 2 specific settings
        self.processed_data_path = config.get(
            'processed_data_path',
            'processed_data.json'
        )
        self.validation_report_path = config.get(
            'validation_report_path',
            'validation_report.json'
        )
        self.transformation_report_path = config.get(
            'transformation_report_path',
            'transformation_report.json'
        )
        
        # Initialize data discoverer
        self.data_discoverer = DataDiscoverer(config)
    
    def run_phase_2(self, phase_1_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete Phase 2 data processing pipeline.
        
        Args:
            phase_1_results: Results from Phase 1
            
        Returns:
            Dictionary containing Phase 2 results
        """
        print("Starting Phase 2: Data Processing Pipeline")
        print("=" * 50)
        
        # Step 1: Load canonical inventory
        print("Step 1: Loading canonical inventory...")
        canonical_inventory = phase_1_results.get('canonical_inventory', {})
        
        # Step 2: Load Batch A queue
        print("Step 2: Loading Batch A queue...")
        batch_a_queue = phase_1_results.get('batch_a_queue', {})
        
        # Step 3: Process data files
        print("Step 3: Processing data files...")
        processed_data = self._process_data_files(canonical_inventory, batch_a_queue)
        
        # Step 4: Validate processed data
        print("Step 4: Validating processed data...")
        validation_report = self._validate_processed_data(processed_data)
        
        # Step 5: Transform processed data
        print("Step 5: Transforming processed data...")
        transformation_report = self._transform_processed_data(processed_data)
        
        # Step 6: Save results
        print("Step 6: Saving results...")
        self._save_phase_2_results(
            processed_data, validation_report, transformation_report
        )
        
        # Compile Phase 2 results
        phase_2_results = {
            'phase': '2',
            'phase_name': 'Data Processing',
            'timestamp': datetime.now().isoformat(),
            'processed_data_count': len(processed_data.get('processed_files', [])),
            'processed_data': processed_data,
            'validation_report': validation_report,
            'transformation_report': transformation_report,
            'status': 'completed',
        }
        
        print("=" * 50)
        print("Phase 2 completed successfully!")
        print(f"Processed {len(processed_data.get('processed_files', []))} data files")
        print(f"Validation score: {validation_report.get('overall_score', 0.0):.1f}%")
        print(f"Transformation score: {transformation_report.get('overall_score', 0.0):.1f}%")
        
        return phase_2_results
    
    def _process_data_files(self, 
                          canonical_inventory: Dict[str, Any], 
                          batch_a_queue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data files from canonical inventory and Batch A queue.
        
        Args:
            canonical_inventory: Canonical inventory
            batch_a_queue: Batch A queue
            
        Returns:
            Dictionary containing processed data
        """
        # Initialize processed data
        processed_data = {
            'processing_timestamp': datetime.now().isoformat(),
            'total_files': len(canonical_inventory.get('symbols', [])),
            'processed_files': [],
            'processing_status': 'pending',
        }
        
        # Process each symbol in Batch A queue
        for queue_item in batch_a_queue.get('queue_items', []):
            symbol = queue_item.get('symbol', 'unknown')
            
            # Process symbol data
            symbol_data = self._process_symbol_data(symbol, queue_item)
            processed_data['processed_files'].append(symbol_data)
        
        return processed_data
    
    def _process_symbol_data(self, symbol: str, queue_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data for a specific symbol.
        
        Args:
            symbol: Symbol to process
            queue_item: Queue item containing symbol information
            
        Returns:
            Dictionary containing processed symbol data
        """
        # Initialize symbol data
        symbol_data = {
            'symbol': symbol,
            'processing_timestamp': datetime.now().isoformat(),
            'providers': queue_item.get('providers', []),
            'timeframes': queue_item.get('timeframes', []),
            'formats': queue_item.get('formats', []),
            'quality_score': queue_item.get('quality_score', 0.0),
            'processed_data': {},
            'processing_status': 'pending',
        }
        
        # Process data for each provider
        for provider in symbol_data['providers']:
            # Get provider configuration
            provider_config = self.provider_registry.get_provider_config(provider)
            
            # Process data for provider
            provider_data = self._process_provider_data(symbol, provider, provider_config)
            symbol_data['processed_data'][provider] = provider_data
        
        return symbol_data
    
    def _process_provider_data(self, 
                              symbol: str, 
                              provider: str, 
                              provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data for a specific provider.
        
        Args:
            symbol: Symbol to process
            provider: Provider to process data for
            provider_config: Provider configuration
            
        Returns:
            Dictionary containing processed provider data
        """
        # Initialize provider data
        provider_data = {
            'provider': provider,
            'processing_timestamp': datetime.now().isoformat(),
            'data_points': [],
            'statistics': {},
            'quality_metrics': {},
            'processing_status': 'pending',
        }
        
        # Simulate data processing
        # In a real implementation, this would load actual data from the provider
        # and perform various processing steps
        
        # Generate sample data points
        for timeframe in ['1m', '5m', '15m', '1h', '4h', '1d']:
            # Generate sample data for this timeframe
            data_points = self._generate_sample_data_points(symbol, timeframe, provider_config)
            provider_data['data_points'].append({
                'timeframe': timeframe,
                'data_points': data_points,
                'count': len(data_points),
            })
        
        # Calculate statistics
        provider_data['statistics'] = self._calculate_provider_statistics(provider_data)
        
        # Calculate quality metrics
        provider_data['quality_metrics'] = self._calculate_provider_quality_metrics(provider_data)
        
        return provider_data
    
    def _generate_sample_data_points(self, 
                                   symbol: str, 
                                   timeframe: str, 
                                   provider_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample data points for a symbol and timeframe.
        
        Args:
            symbol: Symbol to generate data for
            timeframe: Timeframe to generate data for
            provider_config: Provider configuration
            
        Returns:
            List of sample data points
        """
        # Generate sample data points
        data_points = []
        
        # Generate data for the last 100 periods
        for i in range(100):
            # Calculate timestamp
            timestamp = datetime.now()
            if timeframe.endswith('m'):
                timestamp = timestamp.replace(minute=timestamp.minute - i)
            elif timeframe.endswith('h'):
                timestamp = timestamp.replace(hour=timestamp.hour - i)
            elif timeframe.endswith('d'):
                timestamp = timestamp.replace(day=timestamp.day - i)
            
            # Generate sample price data
            base_price = 1.0 if symbol == 'EURUSD' else 1.2 if symbol == 'GBPUSD' else 110.0
            price_change = np.random.normal(0, 0.001)
            price = base_price * (1 + price_change)
            
            # Generate sample volume
            volume = np.random.randint(1000, 10000)
            
            # Create data point
            data_point = {
                'timestamp': timestamp.isoformat(),
                'price': round(price, 5),
                'volume': volume,
                'high': round(price * (1 + np.random.uniform(0, 0.01)), 5),
                'low': round(price * (1 - np.random.uniform(0, 0.01)), 5),
                'open': round(price * (1 + np.random.uniform(-0.005, 0.005)), 5),
                'close': round(price, 5),
            }
            
            data_points.append(data_point)
        
        return data_points
    
    def _calculate_provider_statistics(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate statistics for provider data.
        
        Args:
            provider_data: Provider data
            
        Returns:
            Dictionary containing provider statistics
        """
        # Initialize statistics
        statistics = {
            'total_data_points': 0,
            'average_price': 0.0,
            'min_price': 0.0,
            'max_price': 0.0,
            'average_volume': 0.0,
            'min_volume': 0,
            'max_volume': 0,
            'price_volatility': 0.0,
            'volume_volatility': 0.0,
        }
        
        # Calculate statistics
        all_prices = []
        all_volumes = []
        
        for timeframe_data in provider_data['data_points']:
            for data_point in timeframe_data['data_points']:
                all_prices.append(data_point['price'])
                all_volumes.append(data_point['volume'])
        
        if all_prices:
            statistics['total_data_points'] = len(all_prices)
            statistics['average_price'] = sum(all_prices) / len(all_prices)
            statistics['min_price'] = min(all_prices)
            statistics['max_price'] = max(all_prices)
            statistics['average_volume'] = sum(all_volumes) / len(all_volumes)
            statistics['min_volume'] = min(all_volumes)
            statistics['max_volume'] = max(all_volumes)
            
            # Calculate volatility
            if len(all_prices) > 1:
                price_returns = np.diff(all_prices) / all_prices[:-1]
                statistics['price_volatility'] = np.std(price_returns) * 100
            
            if len(all_volumes) > 1:
                volume_returns = np.diff(all_volumes) / all_volumes[:-1]
                statistics['volume_volatility'] = np.std(volume_returns) * 100
        
        return statistics
    
    def _calculate_provider_quality_metrics(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality metrics for provider data.
        
        Args:
            provider_data: Provider data
            
        Returns:
            Dictionary containing provider quality metrics
        """
        # Initialize quality metrics
        quality_metrics = {
            'completeness': 0.0,
            'uniqueness': 0.0,
            'validity': 0.0,
            'consistency': 0.0,
            'overall_score': 0.0,
        }
        
        # Calculate completeness
        total_data_points = 0
        complete_data_points = 0
        
        for timeframe_data in provider_data['data_points']:
            for data_point in timeframe_data['data_points']:
                total_data_points += 1
                
                # Check if data point is complete
                if all(key in data_point for key in ['timestamp', 'price', 'volume', 'high', 'low', 'open', 'close']):
                    complete_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['completeness'] = (complete_data_points / total_data_points) * 100
        
        # Calculate uniqueness
        unique_timestamps = set()
        for timeframe_data in provider_data['data_points']:
            for data_point in timeframe_data['data_points']:
                unique_timestamps.add(data_point['timestamp'])
        
        if total_data_points > 0:
            quality_metrics['uniqueness'] = (len(unique_timestamps) / total_data_points) * 100
        
        # Calculate validity
        valid_data_points = 0
        for timeframe_data in provider_data['data_points']:
            for data_point in timeframe_data['data_points']:
                # Check if data point is valid
                if (
                    data_point['price'] > 0 and
                    data_point['volume'] > 0 and
                    data_point['high'] > data_point['low'] and
                    data_point['close'] >= data_point['low'] and
                    data_point['close'] <= data_point['high']
                ):
                    valid_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['validity'] = (valid_data_points / total_data_points) * 100
        
        # Calculate consistency
        consistent_data_points = 0
        for timeframe_data in provider_data['data_points']:
            for data_point in timeframe_data['data_points']:
                # Check if data point is consistent
                price_change = abs(data_point['close'] - data_point['open']) / data_point['open']
                if price_change < 0.1:  # Less than 10% price change
                    consistent_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['consistency'] = (consistent_data_points / total_data_points) * 100
        
        # Calculate overall score
        scores = [
            quality_metrics['completeness'],
            quality_metrics['uniqueness'],
            quality_metrics['validity'],
            quality_metrics['consistency'],
        ]
        
        if scores:
            quality_metrics['overall_score'] = sum(scores) / len(scores)
        
        return quality_metrics
    
    def _validate_processed_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate processed data.
        
        Args:
            processed_data: Processed data
            
        Returns:
            Dictionary containing validation report
        """
        # Initialize validation report
        validation_report = {
            'validation_timestamp': datetime.now().isoformat(),
            'total_files': len(processed_data.get('processed_files', [])),
            'validation_status': 'pending',
            'validation_results': {},
            'overall_score': 0.0,
            'issues': [],
        }
        
        # Validate each processed file
        for symbol_data in processed_data.get('processed_files', []):
            symbol = symbol_data.get('symbol', 'unknown')
            
            # Validate symbol data
            validation_result = self._validate_symbol_data(symbol_data)
            validation_report['validation_results'][symbol] = validation_result
            
            # Add issues to validation report
            if 'issues' in validation_result:
                validation_report['issues'].extend(validation_result['issues'])
        
        # Calculate overall score
        if validation_report['validation_results']:
            scores = [
                validation_result.get('overall_score', 0.0)
                for validation_result in validation_report['validation_results'].values()
            ]
            validation_report['overall_score'] = sum(scores) / len(scores)
        
        return validation_report
    
    def _validate_symbol_data(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate symbol data.
        
        Args:
            symbol_data: Symbol data to validate
            
        Returns:
            Dictionary containing validation result
        """
        # Initialize validation result
        validation_result = {
            'symbol': symbol_data.get('symbol', 'unknown'),
            'validation_timestamp': datetime.now().isoformat(),
            'validation_status': 'pending',
            'quality_score': symbol_data.get('quality_score', 0.0),
            'issues': [],
            'overall_score': 0.0,
        }
        
        # Validate quality score
        if symbol_data.get('quality_score', 0.0) < 50.0:
            validation_result['issues'].append(
                f"Quality score is below threshold ({symbol_data.get('quality_score', 0.0):.1f}% < 50.0%)"
            )
        
        # Validate providers
        providers = symbol_data.get('providers', [])
        if not providers:
            validation_result['issues'].append('No providers specified')
        
        # Validate timeframes
        timeframes = symbol_data.get('timeframes', [])
        if not timeframes:
            validation_result['issues'].append('No timeframes specified')
        
        # Validate formats
        formats = symbol_data.get('formats', [])
        if not formats:
            validation_result['issues'].append('No formats specified')
        
        # Calculate overall score
        scores = []
        
        # Add quality score
        scores.append(symbol_data.get('quality_score', 0.0))
        
        # Add validation scores
        if not validation_result['issues']:
            scores.append(100.0)
        
        if scores:
            validation_result['overall_score'] = sum(scores) / len(scores)
        
        return validation_result
    
    def _transform_processed_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform processed data.
        
        Args:
            processed_data: Processed data
            
        Returns:
            Dictionary containing transformation report
        """
        # Initialize transformation report
        transformation_report = {
            'transformation_timestamp': datetime.now().isoformat(),
            'total_files': len(processed_data.get('processed_files', [])),
            'transformation_status': 'pending',
            'transformation_results': {},
            'overall_score': 0.0,
            'issues': [],
        }
        
        # Transform each processed file
        for symbol_data in processed_data.get('processed_files', []):
            symbol = symbol_data.get('symbol', 'unknown')
            
            # Transform symbol data
            transformation_result = self._transform_symbol_data(symbol_data)
            transformation_report['transformation_results'][symbol] = transformation_result
            
            # Add issues to transformation report
            if 'issues' in transformation_result:
                transformation_report['issues'].extend(transformation_result['issues'])
        
        # Calculate overall score
        if transformation_report['transformation_results']:
            scores = [
                transformation_result.get('overall_score', 0.0)
                for transformation_result in transformation_report['transformation_results'].values()
            ]
            transformation_report['overall_score'] = sum(scores) / len(scores)
        
        return transformation_report
    
    def _transform_symbol_data(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform symbol data.
        
        Args:
            symbol_data: Symbol data to transform
            
        Returns:
            Dictionary containing transformation result
        """
        # Initialize transformation result
        transformation_result = {
            'symbol': symbol_data.get('symbol', 'unknown'),
            'transformation_timestamp': datetime.now().isoformat(),
            'transformation_status': 'pending',
            'quality_score': symbol_data.get('quality_score', 0.0),
            'issues': [],
            'overall_score': 0.0,
        }
        
        # Transform data for each provider
        for provider, provider_data in symbol_data.get('processed_data', {}).items():
            # Transform provider data
            transformed_data = self._transform_provider_data(provider_data)
            
            # Add transformed data to symbol data
            if 'transformed_data' not in symbol_data:
                symbol_data['transformed_data'] = {}
            symbol_data['transformed_data'][provider] = transformed_data
        
        # Calculate overall score
        scores = []
        
        # Add quality score
        scores.append(symbol_data.get('quality_score', 0.0))
        
        # Add transformation scores
        if 'transformed_data' in symbol_data:
            for provider_data in symbol_data['transformed_data'].values():
                if 'quality_metrics' in provider_data:
                    scores.append(provider_data['quality_metrics'].get('overall_score', 0.0))
        
        if scores:
            transformation_result['overall_score'] = sum(scores) / len(scores)
        
        return transformation_result
    
    def _transform_provider_data(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform provider data.
        
        Args:
            provider_data: Provider data to transform
            
        Returns:
            Dictionary containing transformed provider data
        """
        # Initialize transformed provider data
        transformed_data = {
            'provider': provider_data.get('provider', 'unknown'),
            'transformation_timestamp': datetime.now().isoformat(),
            'data_points': [],
            'statistics': {},
            'quality_metrics': {},
            'transformation_status': 'pending',
        }
        
        # Transform data points
        for timeframe_data in provider_data['data_points']:
            # Transform timeframe data
            transformed_timeframe_data = self._transform_timeframe_data(timeframe_data)
            transformed_data['data_points'].append(transformed_timeframe_data)
        
        # Calculate statistics
        transformed_data['statistics'] = self._calculate_transformed_statistics(transformed_data)
        
        # Calculate quality metrics
        transformed_data['quality_metrics'] = self._calculate_transformed_quality_metrics(transformed_data)
        
        return transformed_data
    
    def _transform_timeframe_data(self, timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform timeframe data.
        
        Args:
            timeframe_data: Timeframe data to transform
            
        Returns:
            Dictionary containing transformed timeframe data
        """
        # Initialize transformed timeframe data
        transformed_timeframe_data = {
            'timeframe': timeframe_data.get('timeframe', 'unknown'),
            'data_points': [],
            'statistics': {},
            'quality_metrics': {},
            'transformation_status': 'pending',
        }
        
        # Transform data points
        for data_point in timeframe_data['data_points']:
            # Transform data point
            transformed_data_point = self._transform_data_point(data_point)
            transformed_timeframe_data['data_points'].append(transformed_data_point)
        
        # Calculate statistics
        transformed_timeframe_data['statistics'] = self._calculate_transformed_timeframe_statistics(transformed_timeframe_data)
        
        # Calculate quality metrics
        transformed_timeframe_data['quality_metrics'] = self._calculate_transformed_timeframe_quality_metrics(transformed_timeframe_data)
        
        return transformed_timeframe_data
    
    def _transform_data_point(self, data_point: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform data point.
        
        Args:
            data_point: Data point to transform
            
        Returns:
            Dictionary containing transformed data point
        """
        # Initialize transformed data point
        transformed_data_point = {
            'timestamp': data_point.get('timestamp', ''),
            'price': data_point.get('price', 0.0),
            'volume': data_point.get('volume', 0),
            'high': data_point.get('high', 0.0),
            'low': data_point.get('low', 0.0),
            'open': data_point.get('open', 0.0),
            'close': data_point.get('close', 0.0),
            'transformed_timestamp': datetime.now().isoformat(),
            'price_change': 0.0,
            'price_change_percent': 0.0,
            'volume_change': 0.0,
            'high_low_spread': 0.0,
            'open_close_spread': 0.0,
        }
        
        # Calculate price change
        if transformed_data_point['open'] > 0:
            transformed_data_point['price_change'] = transformed_data_point['close'] - transformed_data_point['open']
            transformed_data_point['price_change_percent'] = (transformed_data_point['price_change'] / transformed_data_point['open']) * 100
        
        # Calculate volume change
        transformed_data_point['volume_change'] = transformed_data_point['volume'] - 1000  # Placeholder
        
        # Calculate spreads
        transformed_data_point['high_low_spread'] = transformed_data_point['high'] - transformed_data_point['low']
        transformed_data_point['open_close_spread'] = abs(transformed_data_point['close'] - transformed_data_point['open'])
        
        return transformed_data_point
    
    def _calculate_transformed_statistics(self, transformed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate statistics for transformed data.
        
        Args:
            transformed_data: Transformed data
            
        Returns:
            Dictionary containing transformed statistics
        """
        # Initialize statistics
        statistics = {
            'total_data_points': 0,
            'average_price': 0.0,
            'min_price': 0.0,
            'max_price': 0.0,
            'average_volume': 0.0,
            'min_volume': 0,
            'max_volume': 0,
            'average_price_change': 0.0,
            'average_price_change_percent': 0.0,
            'average_volume_change': 0.0,
            'average_high_low_spread': 0.0,
            'average_open_close_spread': 0.0,
        }
        
        # Calculate statistics
        all_prices = []
        all_volumes = []
        all_price_changes = []
        all_price_change_percents = []
        all_volume_changes = []
        all_high_low_spreads = []
        all_open_close_spreads = []
        
        for timeframe_data in transformed_data['data_points']:
            for data_point in timeframe_data['data_points']:
                all_prices.append(data_point['price'])
                all_volumes.append(data_point['volume'])
                all_price_changes.append(data_point['price_change'])
                all_price_change_percents.append(data_point['price_change_percent'])
                all_volume_changes.append(data_point['volume_change'])
                all_high_low_spreads.append(data_point['high_low_spread'])
                all_open_close_spreads.append(data_point['open_close_spread'])
        
        if all_prices:
            statistics['total_data_points'] = len(all_prices)
            statistics['average_price'] = sum(all_prices) / len(all_prices)
            statistics['min_price'] = min(all_prices)
            statistics['max_price'] = max(all_prices)
            statistics['average_volume'] = sum(all_volumes) / len(all_volumes)
            statistics['min_volume'] = min(all_volumes)
            statistics['max_volume'] = max(all_volumes)
            
            if all_price_changes:
                statistics['average_price_change'] = sum(all_price_changes) / len(all_price_changes)
                statistics['average_price_change_percent'] = sum(all_price_change_percents) / len(all_price_change_percents)
            
            if all_volume_changes:
                statistics['average_volume_change'] = sum(all_volume_changes) / len(all_volume_changes)
            
            if all_high_low_spreads:
                statistics['average_high_low_spread'] = sum(all_high_low_spreads) / len(all_high_low_spreads)
            
            if all_open_close_spreads:
                statistics['average_open_close_spread'] = sum(all_open_close_spreads) / len(all_open_close_spreads)
        
        return statistics
    
    def _calculate_transformed_quality_metrics(self, transformed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality metrics for transformed data.
        
        Args:
            transformed_data: Transformed data
            
        Returns:
            Dictionary containing transformed quality metrics
        """
        # Initialize quality metrics
        quality_metrics = {
            'completeness': 0.0,
            'uniqueness': 0.0,
            'validity': 0.0,
            'consistency': 0.0,
            'overall_score': 0.0,
        }
        
        # Calculate completeness
        total_data_points = 0
        complete_data_points = 0
        
        for timeframe_data in transformed_data['data_points']:
            for data_point in timeframe_data['data_points']:
                total_data_points += 1
                
                # Check if data point is complete
                if all(key in data_point for key in ['timestamp', 'price', 'volume', 'high', 'low', 'open', 'close']):
                    complete_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['completeness'] = (complete_data_points / total_data_points) * 100
        
        # Calculate uniqueness
        unique_timestamps = set()
        for timeframe_data in transformed_data['data_points']:
            for data_point in timeframe_data['data_points']:
                unique_timestamps.add(data_point['timestamp'])
        
        if total_data_points > 0:
            quality_metrics['uniqueness'] = (len(unique_timestamps) / total_data_points) * 100
        
        # Calculate validity
        valid_data_points = 0
        for timeframe_data in transformed_data['data_points']:
            for data_point in timeframe_data['data_points']:
                # Check if data point is valid
                if (
                    data_point['price'] > 0 and
                    data_point['volume'] > 0 and
                    data_point['high'] > data_point['low'] and
                    data_point['close'] >= data_point['low'] and
                    data_point['close'] <= data_point['high']
                ):
                    valid_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['validity'] = (valid_data_points / total_data_points) * 100
        
        # Calculate consistency
        consistent_data_points = 0
        for timeframe_data in transformed_data['data_points']:
            for data_point in timeframe_data['data_points']:
                # Check if data point is consistent
                price_change = abs(data_point['close'] - data_point['open']) / data_point['open']
                if price_change < 0.1:  # Less than 10% price change
                    consistent_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['consistency'] = (consistent_data_points / total_data_points) * 100
        
        # Calculate overall score
        scores = [
            quality_metrics['completeness'],
            quality_metrics['uniqueness'],
            quality_metrics['validity'],
            quality_metrics['consistency'],
        ]
        
        if scores:
            quality_metrics['overall_score'] = sum(scores) / len(scores)
        
        return quality_metrics
    
    def _calculate_transformed_timeframe_statistics(self, transformed_timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate statistics for transformed timeframe data.
        
        Args:
            transformed_timeframe_data: Transformed timeframe data
            
        Returns:
            Dictionary containing transformed timeframe statistics
        """
        # Initialize statistics
        statistics = {
            'total_data_points': 0,
            'average_price': 0.0,
            'min_price': 0.0,
            'max_price': 0.0,
            'average_volume': 0.0,
            'min_volume': 0,
            'max_volume': 0,
            'average_price_change': 0.0,
            'average_price_change_percent': 0.0,
            'average_volume_change': 0.0,
            'average_high_low_spread': 0.0,
            'average_open_close_spread': 0.0,
        }
        
        # Calculate statistics
        all_prices = []
        all_volumes = []
        all_price_changes = []
        all_price_change_percents = []
        all_volume_changes = []
        all_high_low_spreads = []
        all_open_close_spreads = []
        
        for data_point in transformed_timeframe_data['data_points']:
            all_prices.append(data_point['price'])
            all_volumes.append(data_point['volume'])
            all_price_changes.append(data_point['price_change'])
            all_price_change_percents.append(data_point['price_change_percent'])
            all_volume_changes.append(data_point['volume_change'])
            all_high_low_spreads.append(data_point['high_low_spread'])
            all_open_close_spreads.append(data_point['open_close_spread'])
        
        if all_prices:
            statistics['total_data_points'] = len(all_prices)
            statistics['average_price'] = sum(all_prices) / len(all_prices)
            statistics['min_price'] = min(all_prices)
            statistics['max_price'] = max(all_prices)
            statistics['average_volume'] = sum(all_volumes) / len(all_volumes)
            statistics['min_volume'] = min(all_volumes)
            statistics['max_volume'] = max(all_volumes)
            
            if all_price_changes:
                statistics['average_price_change'] = sum(all_price_changes) / len(all_price_changes)
                statistics['average_price_change_percent'] = sum(all_price_change_percents) / len(all_price_change_percents)
            
            if all_volume_changes:
                statistics['average_volume_change'] = sum(all_volume_changes) / len(all_volume_changes)
            
            if all_high_low_spreads:
                statistics['average_high_low_spread'] = sum(all_high_low_spreads) / len(all_high_low_spreads)
            
            if all_open_close_spreads:
                statistics['average_open_close_spread'] = sum(all_open_close_spreads) / len(all_open_close_spreads)
        
        return statistics
    
    def _calculate_transformed_timeframe_quality_metrics(self, transformed_timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality metrics for transformed timeframe data.
        
        Args:
            transformed_timeframe_data: Transformed timeframe data
            
        Returns:
            Dictionary containing transformed timeframe quality metrics
        """
        # Initialize quality metrics
        quality_metrics = {
            'completeness': 0.0,
            'uniqueness': 0.0,
            'validity': 0.0,
            'consistency': 0.0,
            'overall_score': 0.0,
        }
        
        # Calculate completeness
        total_data_points = len(transformed_timeframe_data['data_points'])
        complete_data_points = 0
        
        for data_point in transformed_timeframe_data['data_points']:
            # Check if data point is complete
            if all(key in data_point for key in ['timestamp', 'price', 'volume', 'high', 'low', 'open', 'close']):
                complete_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['completeness'] = (complete_data_points / total_data_points) * 100
        
        # Calculate uniqueness
        unique_timestamps = set()
        for data_point in transformed_timeframe_data['data_points']:
            unique_timestamps.add(data_point['timestamp'])
        
        if total_data_points > 0:
            quality_metrics['uniqueness'] = (len(unique_timestamps) / total_data_points) * 100
        
        # Calculate validity
        valid_data_points = 0
        for data_point in transformed_timeframe_data['data_points']:
            # Check if data point is valid
            if (
                data_point['price'] > 0 and
                data_point['volume'] > 0 and
                data_point['high'] > data_point['low'] and
                data_point['close'] >= data_point['low'] and
                data_point['close'] <= data_point['high']
            ):
                valid_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['validity'] = (valid_data_points / total_data_points) * 100
        
        # Calculate consistency
        consistent_data_points = 0
        for data_point in transformed_timeframe_data['data_points']:
            # Check if data point is consistent
            price_change = abs(data_point['close'] - data_point['open']) / data_point['open']
            if price_change < 0.1:  # Less than 10% price change
                consistent_data_points += 1
        
        if total_data_points > 0:
            quality_metrics['consistency'] = (consistent_data_points / total_data_points) * 100
        
        # Calculate overall score
        scores = [
            quality_metrics['completeness'],
            quality_metrics['uniqueness'],
            quality_metrics['validity'],
            quality_metrics['consistency'],
        ]
        
        if scores:
            quality_metrics['overall_score'] = sum(scores) / len(scores)
        
        return quality_metrics
    
    def _save_phase_2_results(self, 
                            processed_data: Dict[str, Any], 
                            validation_report: Dict[str, Any], 
                            transformation_report: Dict[str, Any]):
        """
        Save Phase 2 results to files.
        
        Args:
            processed_data: Processed data
            validation_report: Validation report
            transformation_report: Transformation report
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.processed_data_path), exist_ok=True)
        
        # Save processed data
        with open(self.processed_data_path, 'w') as f:
            json.dump(processed_data, f, indent=2, default=str)
        
        # Save validation report
        with open(self.validation_report_path, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)
        
        # Save transformation report
        with open(self.transformation_report_path, 'w') as f:
            json.dump(transformation_report, f, indent=2, default=str)


def main():
    """Main function for Phase 2 data processing."""
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
        'processed_data_path': 'processed_data.json',
        'validation_report_path': 'validation_report.json',
        'transformation_report_path': 'transformation_report.json',
    }
    
    # Create Phase 2 data processing pipeline
    phase_2 = Phase2DataProcessing(config)
    
    # Create dummy Phase 1 results
    phase_1_results = {
        'phase': '1',
        'phase_name': 'Data Discovery',
        'timestamp': datetime.now().isoformat(),
        'discovered_files_count': 10,
        'canonical_inventory': {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'],
            'providers': ['nautilus', 'rekey', 'cerebus'],
            'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
            'formats': ['csv', 'parquet'],
        },
        'batch_a_queue': {
            'queue_items': [
                {
                    'symbol': 'EURUSD',
                    'priority': 'high',
                    'estimated_processing_time': '30-60 minutes',
                    'status': 'pending',
                    'providers': ['nautilus', 'rekey'],
                    'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
                    'formats': ['csv', 'parquet'],
                    'quality_score': 85.0,
                },
                {
                    'symbol': 'GBPUSD',
                    'priority': 'high',
                    'estimated_processing_time': '30-60 minutes',
                    'status': 'pending',
                    'providers': ['nautilus', 'rekey'],
                    'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
                    'formats': ['csv', 'parquet'],
                    'quality_score': 80.0,
                },
            ],
        },
    }
    
    # Run Phase 2
    results = phase_2.run_phase_2(phase_1_results)
    
    # Print results
    print("\nPhase 2 Results:")
    print("=" * 50)
    print(f"Phase: {results['phase']}")
    print(f"Phase Name: {results['phase_name']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Status: {results['status']}")
    print(f"Processed Data Files: {results['processed_data_count']}")
    print(f"Validation Score: {results['validation_report'].get('overall_score', 0.0):.1f}%")
    print(f"Transformation Score: {results['transformation_report'].get('overall_score', 0.0):.1f}%")
    
    return results


if __name__ == '__main__':
    main()