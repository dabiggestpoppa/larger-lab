#!/usr/bin/env python3
"""
Test script for Capital Routing Research System ingestion module.

This script tests the ingestion functionality of the Capital Routing
Research System, including data discovery, schema detection, provider
registry, symbol aliases, and basic checks.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from capital_routing.ingestion import (
    DataDiscoverer,
    SchemaDetector,
    ProviderRegistry,
    SymbolAliases,
    BasicChecks,
)


def test_symbol_aliases():
    """Test symbol aliases functionality."""
    print("Testing SymbolAliases...")
    
    symbol_aliases = SymbolAliases()
    
    # Test symbol normalization
    assert symbol_aliases.normalize_symbol('EURUSD') == 'EURUSD'
    assert symbol_aliases.normalize_symbol('eurusd') == 'EURUSD'
    assert symbol_aliases.normalize_symbol('EUR/USD') == 'EURUSD'
    assert symbol_aliases.normalize_symbol('EUR USD') == 'EURUSD'
    
    # Test symbol resolution
    assert symbol_aliases.resolve_symbol('EURUSD') == 'EURUSD'
    assert symbol_aliases.resolve_symbol('eurusd') == 'EURUSD'
    assert symbol_aliases.resolve_symbol('EUR/USD') == 'EURUSD'
    
    # Test alias retrieval
    aliases = symbol_aliases.get_aliases('EURUSD')
    assert 'EUR/USD' in aliases
    assert 'EURO/USD' in aliases
    
    # Test symbol validation
    assert symbol_aliases.is_valid_symbol('EURUSD') == True
    assert symbol_aliases.is_valid_symbol('INVALID') == False
    
    # Test symbol type
    assert symbol_aliases.get_symbol_type('EURUSD') == 'forex'
    assert symbol_aliases.get_symbol_type('XAUUSD') == 'commodity'
    assert symbol_aliases.get_symbol_type('SPX500') == 'index'
    
    print("✓ SymbolAliases tests passed")


def test_provider_registry():
    """Test provider registry functionality."""
    print("Testing ProviderRegistry...")
    
    provider_registry = ProviderRegistry()
    
    # Test provider retrieval
    nautilus_provider = provider_registry.get_provider('nautilus')
    assert nautilus_provider is not None
    assert nautilus_provider['name'] == 'Nautilus'
    
    # Test all providers
    all_providers = provider_registry.get_all_providers()
    assert len(all_providers) > 0
    
    # Test providers by type
    broker_providers = provider_registry.get_providers_by_type('broker')
    assert len(broker_providers) > 0
    
    # Test providers by capability
    data_providers = provider_registry.get_providers_by_capability('data')
    assert len(data_providers) > 0
    
    # Test active providers
    active_providers = provider_registry.get_active_providers()
    assert len(active_providers) > 0
    
    # Test provider symbols
    nautilus_symbols = provider_registry.get_provider_symbols('nautilus')
    assert len(nautilus_symbols) > 0
    
    # Test all symbols
    all_symbols = provider_registry.get_all_symbols()
    assert len(all_symbols) > 0
    
    # Test batch A symbols
    batch_a_symbols = provider_registry.get_batch_a_symbols()
    assert len(batch_a_symbols) > 0
    
    # Test symbol mapping
    mapped_symbol = provider_registry.map_symbol('EURUSD', 'nautilus')
    assert mapped_symbol == 'EURUSD'
    
    # Test provider for symbol
    provider_for_symbol = provider_registry.get_provider_for_symbol('EURUSD')
    assert provider_for_symbol is not None
    
    print("✓ ProviderRegistry tests passed")


def test_schema_detection():
    """Test schema detection functionality."""
    print("Testing SchemaDetector...")
    
    schema_detector = SchemaDetector()
    
    # Create test data
    import pandas as pd
    test_data = pd.DataFrame({
        'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'],
        'price': [1.1234, 1.2345, 110.123],
        'volume': [1000, 2000, 3000],
        'timestamp': pd.date_range('2023-01-01', periods=3),
    })
    
    # Save test data to CSV
    test_csv_path = 'test_data.csv'
    test_data.to_csv(test_csv_path, index=False)
    
    try:
        # Test CSV schema detection
        csv_schema = schema_detector.detect_schema(test_csv_path, 'csv')
        assert csv_schema['file_format'] == 'csv'
        assert len(csv_schema['columns']) == 4
        assert 'symbol' in csv_schema['data_types']
        assert 'price' in csv_schema['data_types']
        assert 'volume' in csv_schema['data_types']
        assert 'timestamp' in csv_schema['data_types']
        
        # Test schema statistics
        assert csv_schema['statistics']['total_columns'] == 4
        assert csv_schema['statistics']['numeric_columns'] == 3
        assert csv_schema['statistics']['datetime_columns'] == 1
        
        # Test schema quality metrics
        assert 'quality_metrics' in csv_schema
        assert 'overall_score' in csv_schema['quality_metrics']
        
    finally:
        # Clean up test file
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
    
    print("✓ SchemaDetector tests passed")


def test_basic_checks():
    """Test basic checks functionality."""
    print("Testing BasicChecks...")
    
    basic_checks = BasicChecks()
    
    # Create test data with actual duplicate rows for uniqueness testing
    import pandas as pd
    test_data = pd.DataFrame({
        'symbol': ['EURUSD', 'GBPUSD', 'USDJPY', 'EURUSD'],  # First and last rows identical
        'price': [1.1234, 1.2345, 110.123, 1.1234],
        'volume': [1000, 2000, 3000, 1000],
        'timestamp': pd.date_range('2023-01-01', periods=4),  # Different timestamps to make rows unique except...
    })
    
    # Make first and last rows truly identical by setting same timestamp
    test_data.loc[3, 'timestamp'] = test_data.loc[0, 'timestamp']
    
    # Run all checks
    check_results = basic_checks.run_all_checks(test_data)
    
    # Check results structure
    assert 'checks' in check_results
    assert 'completeness' in check_results['checks']
    assert 'uniqueness' in check_results['checks']
    assert 'validity' in check_results['checks']
    assert 'consistency' in check_results['checks']
    assert 'timeliness' in check_results['checks']
    
    # Check completeness
    completeness = check_results['checks']['completeness']
    assert 'completeness_score' in completeness
    assert completeness['completeness_score'] > 0
    
    # Check uniqueness
    uniqueness = check_results['checks']['uniqueness']
    assert 'duplicate_percentage' in uniqueness
    assert uniqueness['duplicate_percentage'] > 0
    
    # Check validity
    validity = check_results['checks']['validity']
    assert 'validity_score' in validity
    
    # Check consistency
    consistency = check_results['checks']['consistency']
    assert 'consistency_score' in consistency
    
    # Check timeliness
    timeliness = check_results['checks']['timeliness']
    assert 'timeliness_score' in timeliness
    
    # Check overall score
    assert 'overall_score' in check_results
    assert check_results['overall_score'] > 0
    
    print("✓ BasicChecks tests passed")


def test_data_discoverer():
    """Test data discoverer functionality."""
    print("Testing DataDiscoverer...")
    
    # Create test configuration
    config = {
        'scan_directories': ['.'],
        'supported_extensions': ['.csv', '.parquet', '.zip'],
        'max_file_size': 100 * 1024 * 1024,  # 100MB
    }
    
    # Create test data
    import pandas as pd
    test_data = pd.DataFrame({
        'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'],
        'price': [1.1234, 1.2345, 110.123],
        'volume': [1000, 2000, 3000],
        'timestamp': pd.date_range('2023-01-01', periods=3),
    })
    
    # Save test data to CSV
    test_csv_path = 'test_data.csv'
    test_data.to_csv(test_csv_path, index=False)
    
    try:
        # Create data discoverer
        discoverer = DataDiscoverer(config)
        
        # Discover files
        discovered_files = discoverer.discover_files()
        
        # Check results
        assert len(discovered_files) > 0
        
        # Test symbol coverage analysis
        coverage_analysis = discoverer.analyze_symbol_coverage(discovered_files)
        assert 'total_files' in coverage_analysis
        assert 'symbols_by_provider' in coverage_analysis
        assert 'coverage_gaps' in coverage_analysis
        
        # Test discovery report
        discovery_report = discoverer.generate_discovery_report(discovered_files)
        assert 'discovery_timestamp' in discovery_report
        assert 'total_files_discovered' in discovery_report
        assert 'file_types' in discovery_report
        assert 'providers' in discovery_report
        assert 'recommendations' in discovery_report
        
    finally:
        # Clean up test file
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
    
    print("✓ DataDiscoverer tests passed")


def main():
    """Run all tests."""
    print("Running Capital Routing Research System ingestion module tests...")
    print("=" * 60)
    
    try:
        test_symbol_aliases()
        test_provider_registry()
        test_schema_detection()
        test_basic_checks()
        test_data_discoverer()
        
        print("=" * 60)
        print("All tests passed! ✓")
        return 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())