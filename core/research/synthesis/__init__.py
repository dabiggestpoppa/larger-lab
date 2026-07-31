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
from .pdf_generator import PDFReportGenerator, generate_pdf_report

__all__ = [
    "SisyphusEngine",
    "PDFReportGenerator",
    "generate_pdf_report",
    "ArgumentStructurer",
    "CitationMapper",
    "ContradictionDetector",
    "ResearchReportGenerator",
]
