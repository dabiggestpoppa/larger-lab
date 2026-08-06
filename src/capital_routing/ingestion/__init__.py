"""
Ingestion module for Capital Routing Research System.

This module provides data ingestion functionality for the Capital Routing
Research System, including data discovery, schema detection, provider
registry, symbol aliases, and basic checks.
"""

from .discover import DataDiscoverer
from .schema_detection import SchemaDetector
from .provider_registry import ProviderRegistry
from .symbol_aliases import SymbolAliases
from .basic_checks import BasicChecks
from .mt5_adapter import MT5Adapter, MT5ExportConfig, MT5ExportResult, create_batch_a_mt5_queue
from .normalize import OHLCNormalizer, NormalizationConfig, NormalizationResult, create_batch_a_normalization_configs

__all__ = [
    'DataDiscoverer',
    'SchemaDetector',
    'ProviderRegistry',
    'SymbolAliases',
    'BasicChecks',
    'MT5Adapter',
    'MT5ExportConfig',
    'MT5ExportResult',
    'create_batch_a_mt5_queue',
    'OHLCNormalizer',
    'NormalizationConfig',
    'NormalizationResult',
    'create_batch_a_normalization_configs',
]