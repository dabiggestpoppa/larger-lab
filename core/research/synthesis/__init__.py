"""
Phase 1.5 — Sisyphus Synthesis Engine

Multi-source research synthesis, argument structuring,
citation mapping, and contradiction detection.
"""

from .sisyphus import SisyphusEngine
from .argument import ArgumentStructurer
from .citation import CitationMapper
from .contradiction import ContradictionDetector
from .report import ResearchReportGenerator

__all__ = [
    "SisyphusEngine",
    "ArgumentStructurer",
    "CitationMapper",
    "ContradictionDetector",
    "ResearchReportGenerator",
]
