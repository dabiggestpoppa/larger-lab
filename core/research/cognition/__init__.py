"""
Research Cognition Engine (RCE) — Full scientific reasoning pipeline.

RD Revision 3-Phase Cognition Rebuild:
- REV-1: Structural Decomposition Hardening (6 engines)
- REV-2: Adversarial Scientific Reasoning (6 engines)  
- REV-3: Theory Competition + Scientific Judgment (7 engines)

Multi-source ingestion: OpenAlex + arXiv + S2 (all 3 sources by default)

This package transforms OCE from a retrieval system into a machine scientist.
"""

from .decomposition import KnowledgeDecomposer
from .multi_source import MultiSourceFetcher
from .relationships import RelationshipBuilder
from .reasoning import CrossDocumentReasoner
from .synthesis import TheorySynthesizer
from .validation import RCEValidator

# REV-1: Structural Decomposition Hardening
from .rev1_decomposition import (
    extract_claims,
    extract_explicit_assumptions,
    infer_implicit_assumptions,
)
from .rev1_mechanisms import (
    decompose_mechanisms,
    extract_limitations_and_weaknesses,
    decompose_paper,
    decompose_papers,
    ScientificKnowledgeObject,
)

# REV-2: Adversarial Scientific Reasoning
from .rev2_adversarial import (
    detect_contradictions,
    pressure_test_contradiction,
    generate_alternative_explanations,
    scientific_attack,
    detect_boundary_conditions,
    ConflictMemory,
    run_adversarial_reasoning,
)

# REV-3: Theory Competition + Scientific Judgment
from .rev3_theory import (
    extract_theories,
    compete_theories,
    score_assumption_cost,
    analyze_generalization,
    rank_theories,
    synthesize_theory,
    JudgmentMemory,
    run_theory_competition,
)

__all__ = [
    # Original components
    "KnowledgeDecomposer",
    "MultiSourceFetcher",
    "RelationshipBuilder",
    "CrossDocumentReasoner",
    "TheorySynthesizer",
    "RCEValidator",
    # REV-1
    "extract_claims", "extract_explicit_assumptions", "infer_implicit_assumptions",
    "decompose_mechanisms", "extract_limitations_and_weaknesses",
    "decompose_paper", "decompose_papers", "ScientificKnowledgeObject",
    # REV-2
    "detect_contradictions", "pressure_test_contradiction",
    "generate_alternative_explanations", "scientific_attack",
    "detect_boundary_conditions", "ConflictMemory", "run_adversarial_reasoning",
    # REV-3
    "extract_theories", "compete_theories", "score_assumption_cost",
    "analyze_generalization", "rank_theories", "synthesize_theory",
    "JudgmentMemory", "run_theory_competition",
]
