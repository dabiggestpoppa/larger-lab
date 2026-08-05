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

__all__ = [
    'DataDiscoverer',
    'SchemaDetector',
    'ProviderRegistry',
    'SymbolAliases',
    'BasicChecks',
]