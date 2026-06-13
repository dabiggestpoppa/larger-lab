"""
RCE API — Research Cognition Engine endpoints.

Exposes the full RCE pipeline via FastAPI:
- POST /api/v1/rce/decompose — Decompose papers into knowledge objects
- POST /api/v1/rce/relationships — Build semantic relationship graph
- POST /api/v1/rce/reason — Cross-document reasoning
- POST /api/v1/rce/synthesize — Theory synthesis + research report
- POST /api/v1/rce/validate — Full validation suite
- POST /api/v1/rce/pipeline — Run full RCE pipeline (all 5 phases)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.research.cognition.decomposition import KnowledgeDecomposer
from core.research.cognition.relationships import RelationshipBuilder
from core.research.cognition.reasoning import CrossDocumentReasoner
from core.research.cognition.schema import KnowledgeObject
from core.research.cognition.synthesis import TheorySynthesizer
from core.research.cognition.validation import RCEValidator

logger = logging.getLogger("oce.rce.api")

router = APIRouter(prefix="/api/v1/rce", tags=["rce"])


# ─── Request/Response Models ───


class PaperInput(BaseModel):
    """Single paper input for decomposition."""
    text: str = Field(..., description="Full paper text (abstract + body)")
    title: str = Field(default="", description="Paper title")
    authors: List[str] = Field(default_factory=list, description="Author names")
    year: str = Field(default="", description="Publication year")
    doi: str = Field(default="", description="DOI if available")
    source_url: str = Field(default="", description="URL to source")


class DecomposeRequest(BaseModel):
    """Request for paper decomposition."""
    papers: List[PaperInput] = Field(..., description="List of papers to decompose")


class RCEPipelineRequest(BaseModel):
    """Request for full RCE pipeline."""
    papers: List[PaperInput] = Field(..., description="List of papers to analyze")
    skip_validation: bool = Field(default=False, description="Skip validation phase")


class RCEResponse(BaseModel):
    """Standard RCE response."""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


# ─── Initialize Components ───

_decomposer = KnowledgeDecomposer()
_relationship_builder = RelationshipBuilder()
_reasoner = CrossDocumentReasoner()
_synthesizer = TheorySynthesizer()
_validator = RCEValidator()


def _paper_input_to_dict(paper: PaperInput) -> Dict[str, Any]:
    """Convert PaperInput to dict for processing."""
    return {
        "text": paper.text,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "doi": paper.doi,
        "source_url": paper.source_url,
    }


def _knowledge_object_to_dict(obj: KnowledgeObject) -> Dict[str, Any]:
    """Convert KnowledgeObject to serializable dict."""
    return obj.to_dict()


# ─── Endpoints ───


@router.post("/decompose", response_model=RCEResponse)
async def decompose_papers(request: DecomposeRequest):
    """
    R1 — Decompose papers into structured knowledge objects.
    
    Extracts claims, mechanisms, assumptions, equations,
    limitations, and novelty from each paper.
    """
    try:
        papers = [_paper_input_to_dict(p) for p in request.papers]
        knowledge_objects = _decomposer.decompose_batch(papers)
        
        return RCEResponse(
            success=True,
            data={
                "knowledge_objects": [
                    _knowledge_object_to_dict(obj) for obj in knowledge_objects
                ],
                "count": len(knowledge_objects),
                "avg_completeness": sum(
                    obj.extraction_completeness for obj in knowledge_objects
                ) / max(len(knowledge_objects), 1),
            },
        )
    except Exception as e:
        logger.error(f"Decomposition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships", response_model=RCEResponse)
async def build_relationships(request: DecomposeRequest):
    """
    R2 — Build semantic relationship graph from papers.
    
    Extracts concepts, detects relationships, builds causal chains,
    and clusters similar concepts.
    """
    try:
        papers = [_paper_input_to_dict(p) for p in request.papers]
        knowledge_objects = _decomposer.decompose_batch(papers)
        
        if len(knowledge_objects) < 2:
            return RCEResponse(
                success=True,
                data={
                    "message": "Need at least 2 papers for relationship analysis",
                    "knowledge_objects": [
                        _knowledge_object_to_dict(obj) for obj in knowledge_objects
                    ],
                },
            )
        
        graph = _relationship_builder.build_graph(knowledge_objects)
        
        return RCEResponse(
            success=True,
            data=graph,
        )
    except Exception as e:
        logger.error(f"Relationship building failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reason", response_model=RCEResponse)
async def cross_document_reasoning(request: DecomposeRequest):
    """
    R3 — Cross-document reasoning.
    
    Compares papers, detects contradictions, finds consensus,
    evaluates explanatory strength, and builds reasoning chains.
    """
    try:
        papers = [_paper_input_to_dict(p) for p in request.papers]
        knowledge_objects = _decomposer.decompose_batch(papers)
        
        if len(knowledge_objects) < 2:
            return RCEResponse(
                success=True,
                data={
                    "message": "Need at least 2 papers for cross-document reasoning",
                    "knowledge_objects": [
                        _knowledge_object_to_dict(obj) for obj in knowledge_objects
                    ],
                },
            )
        
        reasoning_results = _reasoner.reason(knowledge_objects)
        
        return RCEResponse(
            success=True,
            data=reasoning_results,
        )
    except Exception as e:
        logger.error(f"Cross-document reasoning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize", response_model=RCEResponse)
async def synthesize_theory(request: DecomposeRequest):
    """
    R4 — Theory synthesis + research report generation.
    
    Constructs unified theories from decomposed knowledge
    and generates structured research reports.
    """
    try:
        papers = [_paper_input_to_dict(p) for p in request.papers]
        knowledge_objects = _decomposer.decompose_batch(papers)
        
        if len(knowledge_objects) < 1:
            return RCEResponse(
                success=False,
                error="Need at least 1 paper for synthesis",
            )
        
        # First run reasoning
        reasoning_results = _reasoner.reason(knowledge_objects)
        
        # Then synthesize
        synthesis_results = _synthesizer.synthesize(knowledge_objects, reasoning_results)
        
        return RCEResponse(
            success=True,
            data=synthesis_results,
        )
    except Exception as e:
        logger.error(f"Theory synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=RCEResponse)
async def validate_rce(request: DecomposeRequest):
    """
    R5 — Full validation + stress testing.
    
    Runs 5 domain benchmarks and calculates quality metrics.
    """
    try:
        papers = [_paper_input_to_dict(p) for p in request.papers]
        knowledge_objects = _decomposer.decompose_batch(papers)
        
        validation_results = _validator.validate(knowledge_objects)
        
        return RCEResponse(
            success=True,
            data=validation_results,
        )
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline", response_model=RCEResponse)
async def full_pipeline(request: RCEPipelineRequest):
    """
    Full RCE pipeline — runs all 5 phases in sequence.
    
    R1 → R2 → R3 → R4 → R5
    
    Returns complete analysis including:
    - Decomposed knowledge objects
    - Relationship graph
    - Cross-document reasoning results
    - Unified theory + research report
    - Validation metrics
    """
    try:
        papers = [_paper_input_to_dict(p) for p in request.papers]
        
        # R1 — Decompose
        knowledge_objects = _decomposer.decompose_batch(papers)
        
        if not knowledge_objects:
            return RCEResponse(
                success=False,
                error="Failed to decompose any papers",
            )
        
        # R2 — Relationships
        graph = _relationship_builder.build_graph(knowledge_objects)
        
        # R3 — Reasoning
        reasoning_results = _reasoner.reason(knowledge_objects)
        
        # R4 — Synthesis
        synthesis_results = _synthesizer.synthesize(knowledge_objects, reasoning_results)
        
        # R5 — Validation (optional)
        validation_results = None
        if not request.skip_validation:
            validation_results = _validator.validate(knowledge_objects)
        
        return RCEResponse(
            success=True,
            data={
                "knowledge_objects": [
                    _knowledge_object_to_dict(obj) for obj in knowledge_objects
                ],
                "relationship_graph": graph,
                "reasoning": reasoning_results,
                "synthesis": synthesis_results,
                "validation": validation_results,
                "pipeline_summary": {
                    "num_papers": len(knowledge_objects),
                    "num_concepts": graph["stats"]["num_concepts"],
                    "num_contradictions": reasoning_results["stats"]["num_contradictions"],
                    "num_consensus": reasoning_results["stats"]["num_consensus"],
                    "synthesis_confidence": synthesis_results["confidence"],
                    "validation_passed": validation_results["passed"] if validation_results else None,
                },
            },
        )
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rce_health():
    """RCE health check."""
    return {
        "status": "healthy",
        "components": {
            "decomposer": "ready",
            "relationship_builder": "ready",
            "reasoner": "ready",
            "synthesizer": "ready",
            "validator": "ready",
        },
        "version": "1.0.0",
    }
