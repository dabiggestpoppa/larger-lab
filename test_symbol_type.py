#!/usr/bin/env python3
"""
Test script for symbol type detection.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from capital_routing.ingestion import SymbolAliases


def test_symbol_type():
    """Test symbol type detection."""
    print("Testing symbol type detection...")
    
    symbol_aliases = SymbolAliases()
    
    # Test various symbols
    test_cases = [
        ('EURUSD', 'forex'),
        ('GBPUSD', 'forex'),
        ('USDJPY', 'forex'),
        ('XAUUSD', 'commodity'),
        ('XAGUSD', 'commodity'),
        ('SPX', 'index'),
        ('NDX', 'index'),
        ('DXY', 'index'),
        ('VIX', 'index'),
        ('CADUSD', 'currency'),
        ('AUDUSD', 'currency'),
    ]
    
    for symbol, expected_type in test_cases:
        actual_type = symbol_aliases.get_symbol_type(symbol)
        print(f"Symbol: {symbol}, Expected: {expected_type}, Actual: {actual_type}")
        
        if actual_type != expected_type:
            print(f"❌ FAILED: {symbol} expected {expected_type} but got {actual_type}")
            return False
        else:
            print(f"✓ PASSED: {symbol} correctly identified as {actual_type}")
    
    print("\nAll symbol type tests passed!")
    return True


if __name__ == '__main__':
    success = test_symbol_type()
    sys.exit(0 if success else 1)