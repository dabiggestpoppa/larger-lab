#!/usr/bin/env python3
"""
Debug script for symbol type detection.
"""

import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from capital_routing.ingestion import SymbolAliases


def debug_symbol_type():
    """Debug symbol type detection."""
    print("Debugging symbol type detection...")
    
    symbol_aliases = SymbolAliases()
    
    # Test SPX500
    symbol = 'SPX500'
    normalized_symbol = symbol_aliases.normalize_symbol(symbol)
    print(f"Symbol: {symbol}, Normalized: {normalized_symbol}")
    
    # Check if symbol is in aliases
    if normalized_symbol in symbol_aliases.symbol_aliases:
        print(f"Symbol found in aliases")
        # Determine symbol type based on pattern
        for symbol_type, pattern in symbol_aliases.symbol_patterns.items():
            if re.match(pattern, normalized_symbol):
                print(f"Matched pattern: {symbol_type} = {pattern}")
                return symbol_type
        
        # Default to forex if no pattern matches
        print(f"Defaulting to forex")
        return 'forex'
    
    # Check if any alias matches
    for canonical_symbol, aliases in symbol_aliases.symbol_aliases.items():
        if normalized_symbol in aliases:
            print(f"Symbol found in aliases as alias of {canonical_symbol}")
            # Determine symbol type based on pattern
            for symbol_type, pattern in symbol_aliases.symbol_patterns.items():
                if re.match(pattern, canonical_symbol):
                    print(f"Matched pattern: {symbol_type} = {pattern}")
                    return symbol_type
            
            # Default to forex if no pattern matches
            print(f"Defaulting to forex")
            return 'forex'
    
    # Check if symbol matches any pattern
    for symbol_type, pattern in symbol_aliases.symbol_patterns.items():
        if re.match(pattern, normalized_symbol):
            print(f"Matched pattern: {symbol_type} = {pattern}")
            return symbol_type
    
    # Default to unknown if no match found
    print(f"Defaulting to unknown")
    return 'unknown'


if __name__ == '__main__':
    result = debug_symbol_type()
    print(f"\nResult: {result}")