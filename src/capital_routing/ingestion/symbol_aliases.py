"""
Symbol aliases module for Capital Routing Research System.

This module manages symbol aliases and mappings for the Capital Routing
Research System, providing functionality to resolve symbol aliases
and normalize symbol names.
"""

import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime


class SymbolAliases:
    """Symbol aliases class for the Capital Routing Research System."""
    
    def __init__(self):
        """Initialize the symbol aliases."""
        # Define symbol aliases
        self.symbol_aliases = {
            # Forex pairs
            'EURUSD': ['EUR/USD', 'EURUSD', 'EUR/USD', 'EURO/USD'],
            'GBPUSD': ['GBP/USD', 'GBPUSD', 'GBP/USD', 'BRITISH POUND/USD'],
            'USDJPY': ['USD/JPY', 'USDJPY', 'USD/JPY', 'DOLLAR YEN'],
            'USDCHF': ['USD/CHF', 'USDCHF', 'USD/CHF', 'DOLLAR SWISS FRANC'],
            'EURGBP': ['EUR/GBP', 'EURGBP', 'EUR/GBP', 'EURO BRITISH POUND'],
            'EURJPY': ['EUR/JPY', 'EURJPY', 'EUR/JPY', 'EURO YEN'],
            'GBPJPY': ['GBP/JPY', 'GBPJPY', 'GBP/JPY', 'BRITISH POUND YEN'],
            'CHFJPY': ['CHF/JPY', 'CHFJPY', 'CHF/JPY', 'SWISS FRANC YEN'],
            'EURCHF': ['EUR/CHF', 'EURCHF', 'EUR/CHF', 'EURO SWISS FRANC'],
            'GBPCHF': ['GBP/CHF', 'GBPCHF', 'GBP/CHF', 'BRITISH POUND SWISS FRANC'],
            
            # Commodity pairs
            'XAUUSD': ['GOLD', 'XAU/USD', 'XAUUSD', 'GOLD SPOT'],
            'XAGUSD': ['SILVER', 'XAG/USD', 'XAGUSD', 'SILVER SPOT'],
            'XAUJPY': ['GOLD YEN', 'XAU/JPY', 'XAUJPY', 'GOLD/YEN'],
            'XAGJPY': ['SILVER YEN', 'XAG/JPY', 'XAGJPY', 'SILVER/YEN'],
            'XAUCAD': ['GOLD CAD', 'XAU/CAD', 'XAUCAD', 'GOLD/CAD'],
            'XAUCHF': ['GOLD CHF', 'XAU/CHF', 'XAUCHF', 'GOLD/CHF'],
            'XAGCAD': ['SILVER CAD', 'XAG/CAD', 'XAGCAD', 'SILVER/CAD'],
            'XAGCHF': ['SILVER CHF', 'XAG/CHF', 'XAGCHF', 'SILVER/CHF'],
            
            # Index pairs
            'SPX500': ['S&P 500', 'SPX', 'SPX500', 'DOW JONES'],
            'NDX100': ['NASDAQ 100', 'NDX', 'NDX100', 'NASDAQ'],
            'DXY': ['DOLLAR INDEX', 'DXY', 'DXY', 'US DOLLAR INDEX'],
            'VIX': ['VOLATILITY INDEX', 'VIX', 'VIX', 'CBOE VOLATILITY INDEX'],
            
            # Currency pairs
            'AUDUSD': ['AUD/USD', 'AUDUSD', 'AUD/USD', 'AUSSIAN DOLLAR'],
            'NZDUSD': ['NZD/USD', 'NZDUSD', 'NZD/USD', 'NEW ZEALAND DOLLAR'],
            'AUDJPY': ['AUD/JPY', 'AUDJPY', 'AUD/JPY', 'AUSSIAN YEN'],
            'NZDJPY': ['NZD/JPY', 'NZDJPY', 'NZD/JPY', 'NEW ZEALAND YEN'],
            'AUDCHF': ['AUD/CHF', 'AUDCHF', 'AUD/CHF', 'AUSSIAN SWISS FRANC'],
            'NZDCHF': ['NZD/CHF', 'NZDCHF', 'NZD/CHF', 'NEW ZEALAND SWISS FRANC'],
            'EURAUD': ['EUR/AUD', 'EURAUD', 'EUR/AUD', 'EURO AUSSIAN DOLLAR'],
            'EURNZD': ['EUR/NZD', 'EURNZD', 'EUR/NZD', 'EURO NEW ZEALAND DOLLAR'],
            'GBPAUD': ['GBP/AUD', 'GBPAUD', 'GBP/AUD', 'BRITISH POUND AUSSIAN DOLLAR'],
            'GBPNZD': ['GBP/NZD', 'GBPNZD', 'GBP/NZD', 'BRITISH POUND NEW ZEALAND DOLLAR'],
            'AUDGBP': ['AUD/GBP', 'AUDGBP', 'AUD/GBP', 'AUSSIAN BRITISH POUND'],
            'CHFAUD': ['CHF/AUD', 'CHFAUD', 'CHF/AUD', 'SWISS FRANC AUSSIAN DOLLAR'],
            
            # Cross pairs
            'CADUSD': ['CAD/USD', 'CADUSD', 'CAD/USD', 'CANADIAN DOLLAR'],
            'EURCAD': ['EUR/CAD', 'EURCAD', 'EUR/CAD', 'EURO CANADIAN DOLLAR'],
            'GBPCAD': ['GBP/CAD', 'GBPCAD', 'GBP/CAD', 'BRITISH POUND CANADIAN DOLLAR'],
            'AUDCAD': ['AUD/CAD', 'AUDCAD', 'AUD/CAD', 'AUSSIAN CANADIAN DOLLAR'],
            'NZDCAD': ['NZD/CAD', 'NZDCAD', 'NZD/CAD', 'NEW ZEALAND CANADIAN DOLLAR'],
            
            # Alternative names
            'GOLD': ['XAUUSD', 'GOLD SPOT', 'GOLD', 'XAU'],
            'SILVER': ['XAGUSD', 'SILVER SPOT', 'SILVER', 'XAG'],
            'OIL': ['OILUSD', 'OIL', 'CRUDE OIL', 'WTI'],
            'WTI': ['OILUSD', 'WTI', 'WEST TEXAS INTERMEDIATE'],
            'BRENT': ['OILUSD', 'BRENT', 'BRENT OIL'],
        }
        
        # Define symbol patterns (order matters - more specific patterns first)
        self.symbol_patterns = {
            'commodity': r'^(XAU|XAG)[A-Z]{3}$',  # XAUXXX, XAGXXX (e.g., XAUUSD, XAGUSD)
            'forex': r'^[A-Z]{6}$',  # XXXXXX (e.g., EURUSD, GBPUSD, USDJPY)
            'currency': r'^[A-Z]{3}USD$',  # XXXUSD (e.g., CADUSD, AUDUSD, NZDUSD)
            'index': r'^[A-Z]{2,4}[0-9]{0,4}$',  # XX-XXXX followed by 0-4 digits (e.g., SPX, SPX500, DXY, VIX)
        }
        
        # Define symbol normalization rules
        self.normalization_rules = {
            'uppercase': True,
            'remove_slash': True,
            'remove_spaces': True,
            'replace_underscore': True,
        }
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize a symbol.
        
        Args:
            symbol: Symbol to normalize
            
        Returns:
            Normalized symbol
        """
        if not symbol:
            return symbol
        
        # Convert to uppercase
        if self.normalization_rules['uppercase']:
            symbol = symbol.upper()
        
        # Remove slashes
        if self.normalization_rules['remove_slash']:
            symbol = symbol.replace('/', '')
        
        # Remove spaces
        if self.normalization_rules['remove_spaces']:
            symbol = symbol.replace(' ', '')
        
        # Replace underscores
        if self.normalization_rules['replace_underscore']:
            symbol = symbol.replace('_', '')
        
        return symbol
    
    def resolve_symbol(self, symbol: str) -> str:
        """
        Resolve a symbol to its canonical form.
        
        Args:
            symbol: Symbol to resolve
            
        Returns:
            Resolved symbol
        """
        # Normalize the symbol
        normalized_symbol = self.normalize_symbol(symbol)
        
        # Check if symbol is in aliases
        if normalized_symbol in self.symbol_aliases:
            # Return the canonical symbol
            return normalized_symbol
        
        # Check if any alias matches
        for canonical_symbol, aliases in self.symbol_aliases.items():
            if normalized_symbol in aliases:
                return canonical_symbol
        
        # Return normalized symbol if no match found
        return normalized_symbol
    
    def get_aliases(self, symbol: str) -> List[str]:
        """
        Get aliases for a symbol.
        
        Args:
            symbol: Symbol to get aliases for
            
        Returns:
            List of aliases
        """
        # Normalize the symbol
        normalized_symbol = self.normalize_symbol(symbol)
        
        # Check if symbol is in aliases
        if normalized_symbol in self.symbol_aliases:
            return self.symbol_aliases[normalized_symbol]
        
        # Return empty list if no match found
        return []
    
    def add_alias(self, canonical_symbol: str, alias: str):
        """
        Add an alias for a symbol.
        
        Args:
            canonical_symbol: Canonical symbol
            alias: Alias to add
        """
        # Normalize both symbols
        canonical_symbol = self.normalize_symbol(canonical_symbol)
        alias = self.normalize_symbol(alias)
        
        # Add alias to symbol aliases
        if canonical_symbol not in self.symbol_aliases:
            self.symbol_aliases[canonical_symbol] = []
        
        if alias not in self.symbol_aliases[canonical_symbol]:
            self.symbol_aliases[canonical_symbol].append(alias)
    
    def remove_alias(self, canonical_symbol: str, alias: str):
        """
        Remove an alias for a symbol.
        
        Args:
            canonical_symbol: Canonical symbol
            alias: Alias to remove
        """
        # Normalize both symbols
        canonical_symbol = self.normalize_symbol(canonical_symbol)
        alias = self.normalize_symbol(alias)
        
        # Remove alias from symbol aliases
        if canonical_symbol in self.symbol_aliases:
            if alias in self.symbol_aliases[canonical_symbol]:
                self.symbol_aliases[canonical_symbol].remove(alias)
    
    def get_all_symbols(self) -> Set[str]:
        """
        Get all symbols.
        
        Returns:
            Set of all symbols
        """
        all_symbols = set()
        
        # Add canonical symbols
        all_symbols.update(self.symbol_aliases.keys())
        
        # Add aliases
        for aliases in self.symbol_aliases.values():
            all_symbols.update(aliases)
        
        return all_symbols
    
    def get_symbols_by_pattern(self, pattern: str) -> List[str]:
        """
        Get symbols by pattern.
        
        Args:
            pattern: Pattern to match
            
        Returns:
            List of symbols matching pattern
        """
        matching_symbols = []
        
        # Check each symbol
        for symbol in self.get_all_symbols():
            if re.match(pattern, symbol):
                matching_symbols.append(symbol)
        
        return matching_symbols
    
    def get_symbols_by_type(self, symbol_type: str) -> List[str]:
        """
        Get symbols by type.
        
        Args:
            symbol_type: Symbol type
            
        Returns:
            List of symbols by type
        """
        if symbol_type not in self.symbol_patterns:
            return []
        
        return self.get_symbols_by_pattern(self.symbol_patterns[symbol_type])
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is valid.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if symbol is valid, False otherwise
        """
        # Normalize the symbol
        normalized_symbol = self.normalize_symbol(symbol)
        
        # Check if symbol is in aliases
        if normalized_symbol in self.symbol_aliases:
            return True
        
        # Check if any alias matches
        for canonical_symbol, aliases in self.symbol_aliases.items():
            if normalized_symbol in aliases:
                return True
        
        # Check if symbol matches any pattern
        for pattern in self.symbol_patterns.values():
            if re.match(pattern, normalized_symbol):
                return True
        
        # Return False if no match found
        return False
    
    def get_symbol_type(self, symbol: str) -> str:
        """
        Get symbol type.
        Args:
            symbol: Symbol to get type for
            
        Returns:
            Symbol type
        """
        # Normalize the symbol
        normalized_symbol = self.normalize_symbol(symbol)
        
        # Check if symbol matches any pattern first (order matters)
        for symbol_type, pattern in self.symbol_patterns.items():
            if re.match(pattern, normalized_symbol):
                return symbol_type
        
        # Check if symbol is in aliases
        if normalized_symbol in self.symbol_aliases:
            # Determine symbol type based on pattern
            for symbol_type, pattern in self.symbol_patterns.items():
                if re.match(pattern, normalized_symbol):
                    return symbol_type
            
            # Default to forex if no pattern matches
            return 'forex'
        
        # Check if any alias matches
        for canonical_symbol, aliases in self.symbol_aliases.items():
            if normalized_symbol in aliases:
                # Determine symbol type based on pattern
                for symbol_type, pattern in self.symbol_patterns.items():
                    if re.match(pattern, canonical_symbol):
                        return symbol_type
                
                # Default to forex if no pattern matches
                return 'forex'
        
        # Default to unknown if no match found
        return 'unknown'
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get symbol information.
        
        Args:
            symbol: Symbol to get information for
            
        Returns:
            Symbol information
        """
        # Normalize the symbol
        normalized_symbol = self.normalize_symbol(symbol)
        
        # Get symbol information
        symbol_info = {
            'symbol': normalized_symbol,
            'type': self.get_symbol_type(normalized_symbol),
            'aliases': self.get_aliases(normalized_symbol),
            'is_valid': self.is_valid_symbol(normalized_symbol),
        }
        
        return symbol_info
    
    def get_all_symbol_info(self) -> List[Dict[str, Any]]:
        """
        Get all symbol information.
        
        Returns:
            List of all symbol information
        """
        all_symbol_info = []
        
        # Get all symbols
        all_symbols = self.get_all_symbols()
        
        # Get information for each symbol
        for symbol in all_symbols:
            symbol_info = self.get_symbol_info(symbol)
            all_symbol_info.append(symbol_info)
        
        return all_symbol_info
    
    def export_symbol_aliases(self) -> Dict[str, List[str]]:
        """
        Export symbol aliases.
        
        Returns:
            Dictionary of symbol aliases
        """
        return self.symbol_aliases.copy()
    
    def import_symbol_aliases(self, symbol_aliases: Dict[str, List[str]]):
        """
        Import symbol aliases.
        
        Args:
            symbol_aliases: Dictionary of symbol aliases
        """
        # Update symbol aliases
        self.symbol_aliases.update(symbol_aliases)
    
    def clear_symbol_aliases(self):
        """Clear symbol aliases."""
        self.symbol_aliases.clear()
    
    def get_symbol_count(self) -> int:
        """
        Get symbol count.
        
        Returns:
            Number of symbols
        """
        return len(self.get_all_symbols())
    
    def get_alias_count(self) -> int:
        """
        Get alias count.
        
        Returns:
            Number of aliases
        """
        total_aliases = 0
        for aliases in self.symbol_aliases.values():
            total_aliases += len(aliases)
        
        return total_aliases
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """
        Get symbol statistics.
        
        Returns:
            Symbol statistics
        """
        statistics = {
            'total_symbols': self.get_symbol_count(),
            'total_aliases': self.get_alias_count(),
            'symbol_types': {},
        }
        
        # Get symbol types
        for symbol in self.get_all_symbols():
            symbol_type = self.get_symbol_type(symbol)
            if symbol_type not in statistics['symbol_types']:
                statistics['symbol_types'][symbol_type] = 0
            statistics['symbol_types'][symbol_type] += 1
        
        return statistics