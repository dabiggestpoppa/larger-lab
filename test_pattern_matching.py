#!/usr/bin/env python3
"""
Test script for pattern matching.
"""

import re


def test_pattern_matching():
    """Test pattern matching."""
    print("Testing pattern matching...")
    
    # Define symbol patterns
    symbol_patterns = {
        'commodity': r'^(XAU|XAG)[A-Z]{3}$',  # XAUXXX, XAGXXX (e.g., XAUUSD, XAGUSD)
        'currency': r'^[A-Z]{3}USD$',  # XXXUSD (e.g., CADUSD, AUDUSD, NZDUSD)
        'index': r'^[A-Z]{3,6}$',  # XXX to XXXXXX (e.g., SPX, SPX500, DXY)
        'forex': r'^[A-Z]{3}[A-Z]{3}$',  # XXXXXX (e.g., EURUSD, GBPUSD, USDJPY)
    }
    
    # Test symbols
    test_symbols = ['SPX500', 'EURUSD', 'XAUUSD', 'CADUSD', 'DXY']
    
    for symbol in test_symbols:
        print(f"\nTesting symbol: {symbol}")
        
        # Check each pattern
        for symbol_type, pattern in symbol_patterns.items():
            match = re.match(pattern, symbol)
            if match:
                print(f"  Matched pattern: {symbol_type} = {pattern}")
                print(f"  Match: {match.group()}")
                break
        else:
            print(f"  No pattern matched")


if __name__ == '__main__':
    test_pattern_matching()