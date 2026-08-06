"""
Quality module for Capital Routing Research System.

This module provides data quality validation, gap analysis, and provenance
tracking for the Capital Routing Research System.
"""

from .ohlc_validation import OHLCValidator, OHLCValidationResult, validate_normalized_file
from .gap_analysis import GapAnalyzer, GapAnalysisResult, GapInfo, analyze_normalized_file
from .provenance import ProvenanceTracker, RawFileManifestEntry, NormalizedFileManifestEntry, BatchACoverageEntry, create_provenance_tracker

__all__ = [
    'OHLCValidator',
    'OHLCValidationResult',
    'validate_normalized_file',
    'GapAnalyzer',
    'GapAnalysisResult',
    'GapInfo',
    'analyze_normalized_file',
    'ProvenanceTracker',
    'RawFileManifestEntry',
    'NormalizedFileManifestEntry',
    'BatchACoverageEntry',
    'create_provenance_tracker',
]