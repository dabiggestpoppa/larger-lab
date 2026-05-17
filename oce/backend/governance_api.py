"""
OCE Governance API — Phase 8.4
================================
REST endpoints for governance, consensus, and coevolution.
"""

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from governance_engine import (
    get_governance_engine,
    GovernanceEngine,
    ProposalStatus,
    ProposalType,
)
from consensus_engine import (
    get_consensus_engine,
    ConsensusEngine,
    VoteValue,
)
from coevolution_protocol import (
    get_coevolution_protocol,
    CoevolutionProtocol,
    TrustLevel,
    PeerStatus,
)


# ─── Request Models ──────────────────────────────────────────────────────────

class ProposeRequest(BaseModel):
    proposal_type: str
    title: str
    description: str
    changes: Dict[str, Any] = {}
    reason: str = ""
    proposer: str = "oce-autonomous"
    required_approvals: int = 1


class ApproveRequest(BaseModel):
    approver: str = "mad"


class RejectRequest(BaseModel):
    rejecter: str = "mad"
    reason: str = ""


class OverrideRequest(BaseModel):
    decision_id: str
    reason: str
    mad_id: str = "mad"


class VoteRequest(BaseModel):
    topic: str
    voter_id: str
    vote: str  # "yes", "no", "abstain"
    weight: float = 1.0


class RegisterPeerRequest(BaseModel):
    agent_id: str
    name: str
    endpoint: Optional[str] = None
    capabilities: List[str] = []
    trust_level: str = "observer"
    metadata: Dict[str, Any] = {}


class TopologyNegotiateRequest(BaseModel):
    peer_agent_id: str
    proposal: Dict[str, Any]


class GoalAlignRequest(BaseModel):
    peer_agent_id: str
    goal_key: str
    local_value: str
    peer_value: str


class ResolveGoalRequest(BaseModel):
    alignment_id: str
    resolved_value: str


class UpdateTrustRequest(BaseModel):
    agent_id: str
    new_trust: str


# ─── Registration Function ───────────────────────────────────────────────────

def register_governance_endpoints(app: FastAPI):
    """Register all governance, consensus, and coevolution endpoints."""

    # ─── Governance Endpoints ─────────────────────────────────────────────

    @app.get("/governance/status")
    async def governance_status():
        """Get governance engine status."""
        try:
            engine = get_governance_engine()
            proposals = engine.list_proposals(limit=5)
            sovereignty = engine.get_sovereignty_report()
            return {
                "status": "active",
                "recent_proposals": proposals,
                "sovereignty": sovereignty,
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            }
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/governance/propose")
    async def governance_propose(request: ProposeRequest):
        """Submit a governance proposal."""
        try:
            engine = get_governance_engine()
            proposal_id = engine.propose_policy_change(
                proposal_type=request.proposal_type,
                title=request.title,
                description=request.description,
                changes=request.changes,
                reason=request.reason,
                proposer=request.proposer,
                required_approvals=request.required_approvals,
            )
            return {"proposal_id": proposal_id, "status": "proposed"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/governance/approve/{proposal_id}")
    async def governance_approve(proposal_id: str, request: ApproveRequest):
        """Approve a governance proposal."""
        try:
            engine = get_governance_engine()
            fully_approved = engine.approve_proposal(proposal_id, request.approver)
            return {"proposal_id": proposal_id, "fully_approved": fully_approved}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/governance/reject/{proposal_id}")
    async def governance_reject(proposal_id: str, request: RejectRequest):
        """Reject a governance proposal."""
        try:
            engine = get_governance_engine()
            engine.reject_proposal(proposal_id, request.rejecter, request.reason)
            return {"proposal_id": proposal_id, "status": "rejected"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/governance/proposals")
    async def governance_list_proposals(
        status: Optional[str] = None,
        limit: int = Query(50, ge=1, le=500),
    ):
        """List governance proposals."""
        try:
            engine = get_governance_engine()
            proposals = engine.list_proposals(status=status, limit=limit)
            return {"proposals": proposals, "count": len(proposals)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/governance/proposals/{proposal_id}")
    async def governance_get_proposal(proposal_id: str):
        """Get a specific proposal."""
        try:
            engine = get_governance_engine()
            proposal = engine.get_proposal_status(proposal_id)
            if not proposal:
                raise HTTPException(status_code=404, detail="Proposal not found")
            return proposal
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/governance/override")
    async def governance_override(request: OverrideRequest):
        """MAD override an autonomous decision."""
        try:
            engine = get_governance_engine()
            engine.override_autonomous_decision(request.decision_id, request.reason, request.mad_id)
            return {"decision_id": request.decision_id, "status": "overridden"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/governance/sovereignty")
    async def governance_sovereignty():
        """Get sovereignty boundary report."""
        try:
            engine = get_governance_engine()
            return engine.get_sovereignty_report()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/governance/log")
    async def governance_log(limit: int = Query(100, ge=1, le=1000)):
        """Get governance audit log."""
        try:
            engine = get_governance_engine()
            return {"log": engine.get_governance_log(limit=limit)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # ─── Consensus Endpoints ──────────────────────────────────────────────

    @app.post("/consensus/vote")
    async def consensus_vote(request: VoteRequest):
        """Submit a vote on a consensus topic."""
        try:
            engine = get_consensus_engine()
            result = engine.submit_vote(request.topic, request.voter_id, request.vote, request.weight)
            return result
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/consensus/status/{topic}")
    async def consensus_status(topic: str):
        """Get consensus status for a topic."""
        try:
            engine = get_consensus_engine()
            status = engine.get_consensus(topic)
            if not status:
                raise HTTPException(status_code=404, detail="Topic not found")
            return status
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/consensus/history")
    async def consensus_history(limit: int = Query(50, ge=1, le=500)):
        """Get voting history."""
        try:
            engine = get_consensus_engine()
            return {"history": engine.get_voting_history(limit=limit)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/consensus/resolve/{topic}")
    async def consensus_resolve(topic: str, request: dict):
        """Resolve a consensus topic with a specific strategy."""
        try:
            engine = get_consensus_engine()
            strategy = request.get("strategy", "majority")
            result = engine.resolve_conflict(topic, strategy)
            return {"topic": topic, "result": result, "strategy": strategy}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    # ─── Coevolution Endpoints ────────────────────────────────────────────

    @app.get("/coevolution/status")
    async def coevolution_status():
        """Get coevolution protocol status."""
        try:
            protocol = get_coevolution_protocol()
            return protocol.get_coevolution_status()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/peers")
    async def coevolution_register_peer(request: RegisterPeerRequest):
        """Register a peer agent."""
        try:
            protocol = get_coevolution_protocol()
            trust = TrustLevel(request.trust_level)
            agent_id = protocol.register_peer_agent(
                agent_id=request.agent_id,
                name=request.name,
                endpoint=request.endpoint,
                capabilities=request.capabilities,
                trust_level=trust,
                metadata=request.metadata,
            )
            return {"agent_id": agent_id, "status": "registered"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/coevolution/peers")
    async def coevolution_list_peers(
        status: Optional[str] = None,
        trust_level: Optional[str] = None,
    ):
        """List peer agents."""
        try:
            protocol = get_coevolution_protocol()
            peers = protocol.list_peers(status=status, trust_level=trust_level)
            return {"peers": peers, "count": len(peers)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/coevolution/peers/{agent_id}")
    async def coevolution_get_peer(agent_id: str):
        """Get a specific peer agent."""
        try:
            protocol = get_coevolution_protocol()
            peer = protocol.get_peer(agent_id)
            if not peer:
                raise HTTPException(status_code=404, detail="Peer not found")
            return peer
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/peers/{agent_id}/trust")
    async def coevolution_update_trust(agent_id: str, request: UpdateTrustRequest):
        """Update trust level for a peer."""
        try:
            protocol = get_coevolution_protocol()
            trust = TrustLevel(request.new_trust)
            success = protocol.update_peer_trust(agent_id, trust)
            if not success:
                raise HTTPException(status_code=404, detail="Peer not found")
            return {"agent_id": agent_id, "trust_level": request.new_trust}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/peers/{agent_id}/heartbeat")
    async def coevolution_peer_heartbeat(agent_id: str):
        """Update peer heartbeat."""
        try:
            protocol = get_coevolution_protocol()
            protocol.update_peer_heartbeat(agent_id)
            return {"agent_id": agent_id, "heartbeat": "updated"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/topology/negotiate")
    async def coevolution_topology_negotiate(request: TopologyNegotiateRequest):
        """Negotiate a topology change with a peer."""
        try:
            protocol = get_coevolution_protocol()
            sync_id = protocol.negotiate_topology_change(request.peer_agent_id, request.proposal)
            return {"sync_id": sync_id, "status": "pending"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/coevolution/topology/syncs")
    async def coevolution_topology_syncs(
        peer_agent_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """List topology syncs."""
        try:
            protocol = get_coevolution_protocol()
            syncs = protocol.get_topology_syncs(peer_agent_id=peer_agent_id, status=status)
            return {"syncs": syncs, "count": len(syncs)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/goals/align")
    async def coevolution_goal_align(request: GoalAlignRequest):
        """Create a goal alignment record."""
        try:
            protocol = get_coevolution_protocol()
            alignment_id = protocol.align_goals(
                request.peer_agent_id, request.goal_key, request.local_value, request.peer_value
            )
            return {"alignment_id": alignment_id}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/goals/resolve")
    async def coevolution_goal_resolve(request: ResolveGoalRequest):
        """Resolve a goal alignment."""
        try:
            protocol = get_coevolution_protocol()
            success = protocol.resolve_goal_alignment(request.alignment_id, request.resolved_value)
            if not success:
                raise HTTPException(status_code=400, detail="Alignment not found or already resolved")
            return {"alignment_id": request.alignment_id, "status": "resolved"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/coevolution/goals")
    async def coevolution_goals(
        peer_agent_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """List goal alignments."""
        try:
            protocol = get_coevolution_protocol()
            alignments = protocol.get_goal_alignments(peer_agent_id=peer_agent_id, status=status)
            return {"alignments": alignments, "count": len(alignments)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.post("/coevolution/peers/{agent_id}/failure")
    async def coevolution_handle_failure(agent_id: str):
        """Handle a peer agent failure."""
        try:
            protocol = get_coevolution_protocol()
            result = protocol.handle_peer_failure(agent_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.get("/coevolution/log")
    async def coevolution_log(limit: int = Query(100, ge=1, le=1000)):
        """Get coevolution audit log."""
        try:
            protocol = get_coevolution_protocol()
            return {"log": protocol.get_coevolution_log(limit=limit)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))
