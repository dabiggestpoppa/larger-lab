"""
Provider registry module for Capital Routing Research System.

This module manages data providers and their configurations for the
Capital Routing Research System.
"""

import json
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import yaml


class ProviderRegistry:
    """Provider registry class for the Capital Routing Research System."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the provider registry.
        
        Args:
            config_path: Path to provider configuration file
        """
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.provider_configs: Dict[str, Dict[str, Any]] = {}
        self.symbol_mappings: Dict[str, Dict[str, Any]] = {}
        
        # Load default providers
        self._load_default_providers()
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
    
    def _load_default_providers(self):
        """Load default providers."""
        # Define default providers
        default_providers = {
            'nautilus': {
                'name': 'Nautilus',
                'type': 'broker',
                'description': 'Nautilus trading platform',
                'version': '1.0.0',
                'capabilities': ['trading', 'data', 'analytics'],
                'status': 'active',
                'priority': 1,
                'batch_a_symbols': [
                    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
                    'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
                ],
                'batch_b_symbols': [
                    'AUDUSD', 'NZDUSD', 'AUDJPY', 'NZDJPY', 'AUDCHF', 'NZDCHF',
                    'EURAUD', 'EURNZD', 'GBPAUD', 'GBPNZD', 'AUDGBP', 'CHFAUD',
                    'CADUSD', 'EURCAD', 'GBPCAD', 'AUDCAD', 'NzdCad', 'USDCAD'
                ],
                'batch_c_symbols': [
                    'XAUUSD', 'XAGUSD', 'XAUJPY', 'XAGJPY', 'XAUCAD', 'XAUCHF',
                    'XAGCAD', 'XAGCHF', 'XAUUSD', 'XAGUSD'
                ],
                'batch_d_symbols': [
                    'SPX500', 'NDX100', 'DXY', 'VIX', 'GOLD', 'SILVER', 'OIL'
                ],
                'config': {
                    'host': 'localhost',
                    'port': 8080,
                    'protocol': 'https',
                    'timeout': 30,
                    'retry_count': 3,
                }
            },
            'rekey': {
                'name': 'Rekey',
                'type': 'data_provider',
                'description': 'Rekey data provider',
                'version': '1.0.0',
                'capabilities': ['data', 'analytics', 'research'],
                'status': 'active',
                'priority': 2,
                'batch_a_symbols': [
                    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
                    'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
                ],
                'config': {
                    'host': 'localhost',
                    'port': 8081,
                    'protocol': 'https',
                    'timeout': 30,
                    'retry_count': 3,
                }
            },
            'cerebus': {
                'name': 'Cerebus',
                'type': 'scanner',
                'description': 'Cerebus neuro-symbolic scanner',
                'version': '1.0.0',
                'capabilities': ['scanning', 'analysis', 'detection'],
                'status': 'active',
                'priority': 3,
                'batch_a_symbols': [
                    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
                    'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
                ],
                'config': {
                    'host': 'localhost',
                    'port': 8082,
                    'protocol': 'https',
                    'timeout': 30,
                    'retry_count': 3,
                }
            },
            'oanda': {
                'name': 'OANDA',
                'type': 'data_provider',
                'description': 'OANDA forex data provider',
                'version': '1.0.0',
                'capabilities': ['data', 'prices', 'quotes'],
                'status': 'active',
                'priority': 4,
                'batch_a_symbols': [
                    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
                    'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
                ],
                'config': {
                    'host': 'api.oanda.com',
                    'port': 443,
                    'protocol': 'https',
                    'timeout': 30,
                    'retry_count': 3,
                }
            },
            'dukascopy': {
                'name': 'Dukascopy',
                'type': 'data_provider',
                'description': 'Dukascopy forex data provider',
                'version': '1.0.0',
                'capabilities': ['data', 'historical', 'tick_data'],
                'status': 'active',
                'priority': 5,
                'batch_a_symbols': [
                    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'EURJPY', 
                    'GBPJPY', 'CHFJPY', 'EURCHF', 'GBPCHF'
                ],
                'config': {
                    'host': 'data.dukascopy.com',
                    'port': 443,
                    'protocol': 'https',
                    'timeout': 30,
                    'retry_count': 3,
                }
            },
        }
        
        # Register default providers
        for provider_id, provider_info in default_providers.items():
            self.providers[provider_id] = provider_info
    
    def load_config(self, config_path: str):
        """
        Load provider configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        if not os.path.exists(config_path):
            return
        
        # Load configuration based on file extension
        if config_path.endswith('.json'):
            with open(config_path, 'r') as f:
                config = json.load(f)
        elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {config_path}")
        
        # Update providers with configuration
        if 'providers' in config:
            for provider_id, provider_info in config['providers'].items():
                if provider_id in self.providers:
                    self.providers[provider_id].update(provider_info)
        
        # Load symbol mappings
        if 'symbol_mappings' in config:
            self.symbol_mappings.update(config['symbol_mappings'])
    
    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Get provider information by ID.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider information or None if not found
        """
        return self.providers.get(provider_id)
    
    def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all providers.
        
        Returns:
            Dictionary of all providers
        """
        return self.providers.copy()
    
    def get_providers_by_type(self, provider_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get providers by type.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Dictionary of providers by type
        """
        return {
            provider_id: provider_info
            for provider_id, provider_info in self.providers.items()
            if provider_info.get('type') == provider_type
        }
    
    def get_providers_by_capability(self, capability: str) -> Dict[str, Dict[str, Any]]:
        """
        Get providers by capability.
        
        Args:
            capability: Provider capability
            
        Returns:
            Dictionary of providers by capability
        """
        return {
            provider_id: provider_info
            for provider_id, provider_info in self.providers.items()
            if capability in provider_info.get('capabilities', [])
        }
    
    def get_active_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get active providers.
        
        Returns:
            Dictionary of active providers
        """
        return {
            provider_id: provider_info
            for provider_id, provider_info in self.providers.items()
            if provider_info.get('status') == 'active'
        }
    
    def get_provider_symbols(self, provider_id: str) -> List[str]:
        """
        Get symbols for a provider.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List of symbols for the provider
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return []
        
        # Get symbols based on provider type
        if 'batch_a_symbols' in provider:
            return provider['batch_a_symbols']
        elif 'batch_b_symbols' in provider:
            return provider['batch_b_symbols']
        elif 'batch_c_symbols' in provider:
            return provider['batch_c_symbols']
        elif 'batch_d_symbols' in provider:
            return provider['batch_d_symbols']
        else:
            return []
    
    def get_all_symbols(self) -> Set[str]:
        """
        Get all symbols from all providers.
        
        Returns:
            Set of all symbols
        """
        all_symbols = set()
        
        for provider_id, provider_info in self.providers.items():
            symbols = self.get_provider_symbols(provider_id)
            all_symbols.update(symbols)
        
        return all_symbols
    
    def get_batch_a_symbols(self) -> Set[str]:
        """
        Get Batch A symbols.
        
        Returns:
            Set of Batch A symbols
        """
        batch_a_symbols = set()
        
        for provider_info in self.providers.values():
            if 'batch_a_symbols' in provider_info:
                batch_a_symbols.update(provider_info['batch_a_symbols'])
        
        return batch_a_symbols
    
    def get_batch_b_symbols(self) -> Set[str]:
        """
        Get Batch B symbols.
        
        Returns:
            Set of Batch B symbols
        """
        batch_b_symbols = set()
        
        for provider_info in self.providers.values():
            if 'batch_b_symbols' in provider_info:
                batch_b_symbols.update(provider_info['batch_b_symbols'])
        
        return batch_b_symbols
    
    def get_batch_c_symbols(self) -> Set[str]:
        """
        Get Batch C symbols.
        
        Returns:
            Set of Batch C symbols
        """
        batch_c_symbols = set()
        
        for provider_info in self.providers.values():
            if 'batch_c_symbols' in provider_info:
                batch_c_symbols.update(provider_info['batch_c_symbols'])
        
        return batch_c_symbols
    
    def get_batch_d_symbols(self) -> Set[str]:
        """
        Get Batch D symbols.
        
        Returns:
            Set of Batch D symbols
        """
        batch_d_symbols = set()
        
        for provider_info in self.providers.values():
            if 'batch_d_symbols' in provider_info:
                batch_d_symbols.update(provider_info['batch_d_symbols'])
        
        return batch_d_symbols
    
    def map_symbol(self, symbol: str, provider_id: str) -> Optional[str]:
        """
        Map a symbol to a provider.
        
        Args:
            symbol: Symbol to map
            provider_id: Provider ID
            
        Returns:
            Mapped symbol or None if not found
        """
        # Check symbol mappings
        if symbol in self.symbol_mappings:
            mapping = self.symbol_mappings[symbol]
            if provider_id in mapping:
                return mapping[provider_id]
        
        # Check if symbol is in provider's symbols
        provider_symbols = self.get_provider_symbols(provider_id)
        if symbol in provider_symbols:
            return symbol
        
        return None
    
    def get_provider_for_symbol(self, symbol: str) -> Optional[str]:
        """
        Get provider for a symbol.
        
        Args:
            symbol: Symbol to find provider for
            
        Returns:
            Provider ID or None if not found
        """
        # Check symbol mappings
        if symbol in self.symbol_mappings:
            mapping = self.symbol_mappings[symbol]
            if mapping:
                return list(mapping.keys())[0]
        
        # Check each provider
        for provider_id, provider_info in self.providers.items():
            if symbol in self.get_provider_symbols(provider_id):
                return provider_id
        
        return None
    
    def add_provider(self, provider_id: str, provider_info: Dict[str, Any]):
        """
        Add a provider.
        
        Args:
            provider_id: Provider ID
            provider_info: Provider information
        """
        self.providers[provider_id] = provider_info
    
    def remove_provider(self, provider_id: str):
        """
        Remove a provider.
        
        Args:
            provider_id: Provider ID
        """
        if provider_id in self.providers:
            del self.providers[provider_id]
    
    def update_provider(self, provider_id: str, provider_info: Dict[str, Any]):
        """
        Update a provider.
        
        Args:
            provider_id: Provider ID
            provider_info: Provider information
        """
        if provider_id in self.providers:
            self.providers[provider_id].update(provider_info)
    
    def get_provider_status(self, provider_id: str) -> str:
        """
        Get provider status.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider status
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return 'unknown'
        
        return provider.get('status', 'unknown')
    
    def set_provider_status(self, provider_id: str, status: str):
        """
        Set provider status.
        
        Args:
            provider_id: Provider ID
            status: Provider status
        """
        provider = self.get_provider(provider_id)
        if provider:
            provider['status'] = status
    
    def get_provider_priority(self, provider_id: str) -> int:
        """
        Get provider priority.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider priority
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return 0
        
        return provider.get('priority', 0)
    
    def get_providers_by_priority(self) -> List[str]:
        """
        Get providers by priority.
        
        Returns:
            List of provider IDs sorted by priority
        """
        return sorted(
            self.providers.keys(),
            key=lambda x: self.get_provider_priority(x),
            reverse=True
        )
    
    def get_provider_capabilities(self, provider_id: str) -> List[str]:
        """
        Get provider capabilities.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            List of provider capabilities
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return []
        
        return provider.get('capabilities', [])
    
    def has_capability(self, provider_id: str, capability: str) -> bool:
        """
        Check if provider has a capability.
        
        Args:
            provider_id: Provider ID
            capability: Capability to check
            
        Returns:
            True if provider has capability, False otherwise
        """
        capabilities = self.get_provider_capabilities(provider_id)
        return capability in capabilities
    
    def get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        """
        Get provider configuration.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider configuration
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return {}
        
        return provider.get('config', {})
    
    def update_provider_config(self, provider_id: str, config: Dict[str, Any]):
        """
        Update provider configuration.
        
        Args:
            provider_id: Provider ID
            config: Provider configuration
        """
        provider = self.get_provider(provider_id)
        if provider:
            provider['config'].update(config)