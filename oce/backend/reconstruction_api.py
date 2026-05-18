"""
V3 Phase 2 — Reconstruction API Endpoints
FastAPI routes for the Reconstructive Continuity Manifold (RCM).

Provides endpoints for:
- Causal geometry (edges, lineages, influence scoring)
- Attractor memory (store, recall, find nearest)
- Continuity reconstruction (from partial state)
- Overlap manifold (zones, shared state synthesis)
- Continuity repair (detect fractures, auto-repair)
"""

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

from reconstruction import (
    CausalGeometryEngine, CausalEdge, ContinuityLineage,
    AttractorMemory, Attractor,
    ReconstructionEngine, ReconstructionResult,
    OverlapManifold, OverlapZone,
    ContinuityRepairLoop, RepairResult,
)

logger = logging.getLogger("oce.reconstruction")

# Global instances
_causal_engine: Optional[CausalGeometryEngine] = None
_attractor_memory: Optional[AttractorMemory] = None
_reconstruction_engine: Optional[ReconstructionEngine] = None
_overlap_manifold: Optional[OverlapManifold] = None
_repair_loop: Optional[ContinuityRepairLoop] = None


def _get_causal_engine() -> CausalGeometryEngine:
    global _causal_engine
    if _causal_engine is None:
        _causal_engine = CausalGeometryEngine()
    return _causal_engine


def _get_attractor_memory() -> AttractorMemory:
    global _attractor_memory
    if _attractor_memory is None:
        _attractor_memory = AttractorMemory()
    return _attractor_memory


def _get_reconstruction_engine() -> ReconstructionEngine:
    global _reconstruction_engine
    if _reconstruction_engine is None:
        _reconstruction_engine = ReconstructionEngine()
    return _reconstruction_engine


def _get_overlap_manifold() -> OverlapManifold:
    global _overlap_manifold
    if _overlap_manifold is None:
        _overlap_manifold = OverlapManifold()
    return _overlap_manifold


def _get_repair_loop() -> ContinuityRepairLoop:
    global _repair_loop
    if _repair_loop is None:
        _repair_loop = ContinuityRepairLoop()
    return _repair_loop


# Pydantic models for request bodies

class CreateEdgeRequest(BaseModel):
    source_state: str
    target_state: str
    influence_weight: float = 0.5
    continuity_strength: float = 0.5
    entropy_delta: float = 0.0
    tags: list[str] = []


class CreateAttractorRequest(BaseModel):
    state_id: str
    observer_cluster: list[str] = []
    coherence: float = 0.5
    resonance_signature: list[str] = []


class ReconstructRequest(BaseModel):
    target_state: str
    known_observers: list[str] = []
    known_coherence: float = 0.5
    partial_context: dict = {}


class CreateZoneRequest(BaseModel):
    observer_ids: list[str] = []
    shared_attractors: list[str] = []


class RepairRequest(BaseModel):
    target_state: str
    known_observers: list[str] = []
    known_coherence: float = 0.5


def register_reconstruction_endpoints(app: FastAPI) -> None:
    """Register all V3 Phase 2 reconstruction endpoints."""

    # ── Causal Geometry ──

    @app.get("/reconstruction/geometry/stats")
    def get_geometry_stats():
        return _get_causal_engine().stats

    @app.post("/reconstruction/geometry/edge")
    def create_edge(req: CreateEdgeRequest):
        edge = _get_causal_engine().create_edge(
            source_state=req.source_state,
            target_state=req.target_state,
            influence_weight=req.influence_weight,
            continuity_strength=req.continuity_strength,
            entropy_delta=req.entropy_delta,
            tags=req.tags,
        )
        return edge.to_dict()

    @app.get("/reconstruction/geometry/lineage/{state_id}")
    def get_lineage(state_id: str):
        lineage = _get_causal_engine().get_lineage(state_id)
        if not lineage:
            raise HTTPException(status_code=404, detail="Lineage not found")
        return lineage.to_dict()

    @app.get("/reconstruction/geometry/influence/{state_id}")
    def get_influence(state_id: str):
        return {"state_id": state_id, "influence_score": _get_causal_engine().get_influence_score(state_id)}

    @app.get("/reconstruction/geometry/ancestors/{state_id}")
    def get_ancestors(state_id: str, max_depth: int = 10):
        chain = _get_causal_engine().get_ancestor_chain(state_id, max_depth=max_depth)
        return {"state_id": state_id, "ancestor_chain": chain}

    # ── Attractor Memory ──

    @app.get("/reconstruction/attractors/stats")
    def get_attractor_stats():
        return _get_attractor_memory().stats

    @app.post("/reconstruction/attractors")
    def create_attractor(req: CreateAttractorRequest):
        attractor = _get_attractor_memory().create_attractor(
            state_id=req.state_id,
            observer_cluster=req.observer_cluster,
            coherence=req.coherence,
            resonance_signature=req.resonance_signature,
        )
        return attractor.to_dict()

    @app.get("/reconstruction/attractors/{attractor_id}")
    def get_attractor(attractor_id: str):
        attractor = _get_attractor_memory().recall(attractor_id)
        if not attractor:
            raise HTTPException(status_code=404, detail="Attractor not found")
        return attractor.to_dict()

    @app.get("/reconstruction/attractors/nearest")
    def find_nearest_attractor(coherence: float = 0.5, observers: str = ""):
        obs_list = [o.strip() for o in observers.split(",") if o.strip()]
        nearest = _get_attractor_memory().find_nearest(coherence=coherence, observers=obs_list or None)
        if not nearest:
            raise HTTPException(status_code=404, detail="No attractor found")
        return nearest.to_dict()

    @app.get("/reconstruction/attractors/stable")
    def get_stable_attractors():
        return [a.to_dict() for a in _get_attractor_memory().get_stable_attractors()]

    # ── Reconstruction Engine ──

    @app.get("/reconstruction/engine/stats")
    def get_reconstruction_stats():
        return _get_reconstruction_engine().stats

    @app.post("/reconstruction/reconstruct")
    def reconstruct(req: ReconstructRequest):
        result = _get_reconstruction_engine().reconstruct(
            target_state=req.target_state,
            known_observers=req.known_observers,
            known_coherence=req.known_coherence,
            partial_context=req.partial_context,
        )
        return result.to_dict()

    @app.post("/reconstruction/transition")
    def record_transition(req: CreateEdgeRequest):
        edge = _get_reconstruction_engine().record_state_transition(
            source_state=req.source_state,
            target_state=req.target_state,
            influence_weight=req.influence_weight,
            continuity_strength=req.continuity_strength,
            entropy_delta=req.entropy_delta,
            tags=req.tags,
        )
        return edge.to_dict()

    # ── Overlap Manifold ──

    @app.get("/reconstruction/overlap/stats")
    def get_overlap_stats():
        return _get_overlap_manifold().stats

    @app.post("/reconstruction/overlap/zone")
    def create_zone(req: CreateZoneRequest):
        zone = _get_overlap_manifold().create_zone(
            observer_ids=req.observer_ids,
            shared_attractors=req.shared_attractors,
        )
        return zone.to_dict()

    @app.get("/reconstruction/overlap/shared-state")
    def synthesize_shared_state(observers: str = ""):
        obs_list = [o.strip() for o in observers.split(",") if o.strip()]
        if len(obs_list) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 observers")
        result = _get_overlap_manifold().synthesize_shared_state(
            observer_ids=obs_list,
            attractor_memory=_get_attractor_memory(),
        )
        return result

    @app.get("/reconstruction/overlap/strength")
    def get_overlap_strength(observer_a: str, observer_b: str):
        strength = _get_overlap_manifold().calculate_overlap_strength(observer_a, observer_b)
        return {"observer_a": observer_a, "observer_b": observer_b, "overlap_strength": strength}

    # ── Continuity Repair ──

    @app.get("/reconstruction/repair/stats")
    def get_repair_stats():
        return _get_repair_loop().stats

    @app.get("/reconstruction/repair/fractures")
    def detect_fractures():
        return _get_repair_loop().detect_fractures()

    @app.post("/reconstruction/repair")
    def repair(req: RepairRequest):
        result = _get_repair_loop().repair(
            target_state=req.target_state,
            known_observers=req.known_observers,
            known_coherence=req.known_coherence,
        )
        return result.to_dict()

    @app.post("/reconstruction/repair/auto")
    def auto_repair(observers: str = ""):
        obs_list = [o.strip() for o in observers.split(",") if o.strip()]
        results = _get_repair_loop().auto_repair(observer_ids=obs_list or None)
        return [r.to_dict() for r in results]

    # ── Combined Stats ──

    @app.get("/reconstruction/stats")
    def get_all_reconstruction_stats():
        return {
            "geometry": _get_causal_engine().stats,
            "attractors": _get_attractor_memory().stats,
            "reconstruction": _get_reconstruction_engine().stats,
            "overlap": _get_overlap_manifold().stats,
            "repair": _get_repair_loop().stats,
        }

    logger.info("V3 Phase 2 reconstruction endpoints registered")
