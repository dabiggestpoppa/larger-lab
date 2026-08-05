"""
Capital Routing Research System

A research and backtesting platform for capital routing analysis.
Discovers how capital exits one currency/region, where it parks first,
where it rotates next, which instruments lead or lag, and which slower
"sleeper" crosses provide the cleanest remaining trade expression.

This is a research platform only - no live trading.
"""

__version__ = "0.1.0"
__author__ = "Quant Lab"
__email__ = "quant@lab.local"

from .cli import main

__all__ = ["main"]