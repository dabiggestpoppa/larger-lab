"""
V3 Phase 3 — Topology API Endpoints
FastAPI routes for the Resonant Topology & BSP Emergence Layer.

Provides endpoints for:
- Collar field management (connect, disconnect, query)
- BSP trajectory projections
- Resonance routing
- Glyph encoding/decoding
- Topology health stats
"""

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

from .resonance import SignalPacket, ResonanceEngine, CoherenceEngine
from .reconstruction import AttractorMemory
from .topology.collar_field import CollarFieldEngine
from .topology.bsp_projection import BSPProjectionEngine
from .topology.resonance_router import ResonanceRouter
from .topology.glyph_engine import GlyphEngine

logger = logging.getLogger("oce.topology")

# ─── Global Instances ────────────────────────────────────────────────────────

_collar_engine = CollarFieldEngine()
_bsp_engine = BSPProjectionEngine()
_resonance_router = ResonanceRouter()
_glyph_engine = GlyphEngine()
_resonance_engine = ResonanceEngine()
_attractor_memory = AttractorMemory()


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class CollarConnectRequest(BaseModel):
    observer_a: str
    observer_b: str
    initial_resonance: float = 0.5


class CollarDisconnectRequest(BaseModel):
    observer_a: str
    observer_b: str


class ProjectRequest(BaseModel):
    observer_states: dict[str, tuple[float, float]] = {}


class RouteRequest(BaseModel):
    signal_source: str = "api"
    amplitude: float = 0.5
    coherence: float = 0.5
    phase: float = 0.0
    entropy_delta: float = 0.0
    target_observers: list[str] = []


class GlyphEncodeRequest(BaseModel):
    text: str


class GlyphDecodeRequest(BaseModel):
    glyphs: list[str]


# ─── Registration Function ───────────────────────────────────────────────────

def register_topology_endpoints(app: FastAPI) -> None:
    """Register all topology API endpoints on the given FastAPI app."""

    # ── Collar Field Endpoints ─────────────────────────────────────────────

    @app.post("/topology/collar/connect")
    async def collar_connect(request: CollarConnectRequest):
        """Create or strengthen a collar connection between two observers."""
        try:
            _collar_engine.connect(
                request.observer_a, request.observer_b, request.initial_resonance
            )
            return {
                "status": "connected",
                "observer_a": request.observer_a,
                "observer_b": request.observer_b,
                "resonance": request.initial_resonance,
            }
        except Exception as e:
            logger.error(f"Collar connect error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/topology/collar/disconnect")
    async def collar_disconnect(request: CollarDisconnectRequest):
        """Weaken a collar connection between two observers."""
        try:
            _collar_engine.disconnect(request.observer_a, request.observer_b)
            return {
                "status": "disconnected",
                "observer_a": request.observer_a,
                "observer_b": request.observer_b,
            }
        except Exception as e:
            logger.error(f"Collar disconnect error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/topology/collars")
    async def get_collars(
        strong_only: bool = Query(False),
        observer_id: Optional[str] = None,
    ):
        """Get collar field status."""
        try:
            if observer_id:
                collar = _collar_engine.collars.get(observer_id)
                if not collar:
                    return {"collar": None, "message": f"No collar for {observer_id}"}
                return {"collar": collar.__dict__}

            if strong_only:
                collars = [c for c in _collar_engine.collars.values() if c.is_strong]
            else:
                collars = list(_collar_engine.collars.values())

            return {
                "collars": [
                    {
                        "observer_id": c.observer_id,
                        "connection_count": c.connection_count,
                        "avg_resonance": round(c.avg_resonance, 4),
                        "is_strong": c.is_strong,
                        "is_weakening": c.is_weakening,
                        "entropy_cost": c.entropy_cost,
                        "glyph_affinity": c.glyph_affinity,
                    }
                    for c in collars
                ],
                "count": len(collars),
            }
        except Exception as e:
            logger.error(f"Collars query error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/topology/resonance-matrix")
    async def get_resonance_matrix():
        """Get the full resonance matrix between all observers."""
        try:
            matrix = _collar_engine.get_resonance_matrix()
            return {"matrix": matrix, "observer_count": len(matrix)}
        except Exception as e:
            logger.error(f"Resonance matrix error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/topology/collar/{observer_id}/strongest")
    async def get_strongest_connections(
        observer_id: str,
        top_n: int = Query(5, ge=1, le=20),
    ):
        """Get strongest connections for an observer."""
        try:
            connections = _collar_engine.get_strongest_connections(observer_id, top_n)
            return {
                "observer_id": observer_id,
                "connections": [
                    {"observer_id": obs_id, "resonance": round(score, 4)}
                    for obs_id, score in connections
                ],
            }
        except Exception as e:
            logger.error(f"Strongest connections error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── BSP Projection Endpoints ───────────────────────────────────────────

    @app.post("/topology/project")
    async def project_trajectory(request: ProjectRequest):
        """Generate a BSP trajectory projection from current field state."""
        try:
            projection = _bsp_engine.project(
                resonance_engine=_resonance_engine,
                attractor_memory=_attractor_memory,
                observer_states=request.observer_states,
            )
            return {"projection": projection.to_dict()}
        except Exception as e:
            logger.error(f"Projection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/topology/projections/recent")
    async def get_recent_projections(
        limit: int = Query(10, ge=1, le=100),
    ):
        """Get recent trajectory projections."""
        try:
            projections = _bsp_engine.get_recent_projections(limit)
            return {
                "projections": [p.to_dict() for p in projections],
                "count": len(projections),
            }
        except Exception as e:
            logger.error(f"Recent projections error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── Resonance Router Endpoints ─────────────────────────────────────────

    @app.post("/topology/route")
    async def route_signal(request: RouteRequest):
        """Route a signal by resonance compatibility."""
        try:
            signal = SignalPacket(
                source=request.signal_source,
                amplitude=request.amplitude,
                coherence=request.coherence,
                phase=request.phase,
                entropy_delta=request.entropy_delta,
            )
            routes = _resonance_router.route(
                signal=signal,
                collar_engine=_collar_engine,
                target_observers=request.target_observers,
            )
            return {
                "routes": [r.to_dict() for r in routes],
                "count": len(routes),
            }
        except Exception as e:
            logger.error(f"Routing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/topology/routes/active")
    async def get_active_routes(
        min_score: float = Query(0.3, ge=0.0, le=1.0),
    ):
        """Get currently active routes above a score threshold."""
        try:
            routes = _resonance_router.get_active_routes(min_score)
            return {
                "routes": [r.to_dict() for r in routes],
                "count": len(routes),
            }
        except Exception as e:
            logger.error(f"Active routes error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── Glyph Engine Endpoints ─────────────────────────────────────────────

    @app.post("/topology/glyph/encode")
    async def glyph_encode(request: GlyphEncodeRequest):
        """Encode text to glyph-compressed form."""
        try:
            result = _glyph_engine.encode(request.text)
            return {"encoded": result}
        except Exception as e:
            logger.error(f"Glyph encode error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/topology/glyph/decode")
    async def glyph_decode(request: GlyphDecodeRequest):
        """Decode glyphs back to text."""
        try:
            result = _glyph_engine.decode(request.glyphs)
            return {"decoded": result}
        except Exception as e:
            logger.error(f"Glyph decode error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/topology/glyph/map")
    async def get_glyph_map():
        """Get the current glyph dictionary."""
        try:
            return {"glyphs": _glyph_engine.get_glyph_map(), "count": len(_glyph_engine.get_glyph_map())}
        except Exception as e:
            logger.error(f"Glyph map error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ── Topology Stats ─────────────────────────────────────────────────────

    @app.get("/topology/stats")
    async def get_topology_stats():
        """Get comprehensive topology health stats."""
        try:
            collar_count = len(_collar_engine.collars)
            strong_collars = sum(1 for c in _collar_engine.collars.values() if c.is_strong)
            weakening_collars = sum(1 for c in _collar_engine.collars.values() if c.is_weakening)
            active_routes = len(_resonance_router.get_active_routes(0.0))

            return {
                "collars": {
                    "total": collar_count,
                    "strong": strong_collars,
                    "weakening": weakening_collars,
                },
                "routes": {
                    "active": active_routes,
                },
                "projections": {
                    "total": _bsp_engine._projection_counter,
                },
                "glyphs": {
                    "dictionary_size": len(_glyph_engine.get_glyph_map()),
                },
            }
        except Exception as e:
            logger.error(f"Topology stats error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("Topology API endpoints registered (12 endpoints)")
