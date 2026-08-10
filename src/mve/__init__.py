"""
CEREBUS Morphic Volatility Engine (MVE) - Core Implementation

This package contains the implementation of the CEREBUS Morphic Volatility Engine
research project, investigating whether financial markets exhibit statistically
persistent directional movement after occupying and accepting volatility-normalized
sigma states.

The MVE implements the complete research framework outlined in the project
README, covering all phases from data audit through strategy formulation.
"""

__version__ = "1.0.0"
__author__ = "CEREBUS Research Team"
__license__ = "MIT"

# Core modules
from .volatility import VolatilityEstimators
from .anchors import StructuralAnchors
from .morphic_coordinates import MorphicCoordinates
from .sigma_states import SigmaStates
from .acceptance import AcceptanceCriteria
from .regime import VolatilityRegimeModel
from .rekey import MorphicRekey
from .signals import SignalGenerator
from .backtest import BacktestFramework

__all__ = [
    'VolatilityEstimators',
    'StructuralAnchors',
    'MorphicCoordinates',
    'SigmaStates',
    'AcceptanceCriteria',
    'VolatilityRegimeModel',
    'MorphicRekey',
    'SignalGenerator',
    'BacktestFramework',
]