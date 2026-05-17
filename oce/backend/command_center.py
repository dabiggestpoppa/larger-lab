"""
Command Center — Agent Room Management & Direct Messaging

Provides:
- Room creation / listing / deletion
- Direct messaging MAD → any agent
- Agent-to-agent messaging within rooms
- Room persistence (survives page refresh)
- Background room execution (rooms keep running when MAD navigates away)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import uuid
import json
import os

router = APIRouter(prefix="/command-center", tags=["Command Center"])

# ── Persistence ──────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ROOMS_FILE = os.path.join(DATA_DIR, "command-center-rooms.json")
AGENTS_FILE = os.path.join(DATA_DIR, "command-center-agents.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Models ────────────────────────────────────────────────────────────────────
class CreateRoomRequest(BaseModel):
    name: str = Field(..., description="Room name")
    description: str = Field(default="", description="Room purpose")
    agent_ids: List[str] = Field(default_factory=list, description="Agent session keys to include")
    persistent: bool = Field(default=True, description="Keep running in background")


class SendMessageRequest(BaseModel):
    room_id: str
    sender: str = Field(..., description="Sender ID: 'mad' or agent session key")
    content: str
    message_type: str = Field(default="text", description="text | command | result | system")


class RegisterAgentRequest(BaseModel):
    session_key: str
    label: str
    role: str = Field(default="", description="Agent role description")
    capabilities: List[str] = Field(default_factory=list)


# ── Agent Registry ───────────────────────────────────────────────────────────
@router.get("/agents")
async def list_agents():
    """List all registered agents with their status."""
    agents = load_json(AGENTS_FILE, {})
    return {"agents": agents, "count": len(agents)}


@router.post("/agents/register")
async def register_agent(req: RegisterAgentRequest):
    """Register an agent so MAD can see and message it."""
    agents = load_json(AGENTS_FILE, {})
    agents[req.session_key] = {
        "session_key": req.session_key,
        "label": req.label,
        "role": req.role,
        "capabilities": req.capabilities,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "status": "online",
    }
    save_json(AGENTS_FILE, agents)
    return {"status": "registered", "agent": agents[req.session_key]}


@router.post("/agents/{session_key}/heartbeat")
async def agent_heartbeat(session_key: str):
    """Update agent's last_seen timestamp."""
    agents = load_json(AGENTS_FILE, {})
    if session_key in agents:
        agents[session_key]["last_seen"] = datetime.now(timezone.utc).isoformat()
        agents[session_key]["status"] = "online"
        save_json(AGENTS_FILE, agents)
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Agent not registered")


@router.get("/agents/{session_key}")
async def get_agent(session_key: str):
    """Get a specific agent's info."""
    agents = load_json(AGENTS_FILE, {})
    if session_key not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents[session_key]


# ── Room Management ──────────────────────────────────────────────────────────
@router.get("/rooms")
async def list_rooms():
    """List all rooms."""
    rooms = load_json(ROOMS_FILE, {})
    return {"rooms": rooms, "count": len(rooms)}


@router.post("/rooms")
async def create_room(req: CreateRoomRequest):
    """Create a new room. Agents in the room can exchange messages."""
    rooms = load_json(ROOMS_FILE, {})
    room_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    room = {
        "id": room_id,
        "name": req.name,
        "description": req.description,
        "agent_ids": req.agent_ids,
        "persistent": req.persistent,
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "status": "active",
    }

    # System message announcing room creation
    room["messages"].append({
        "id": str(uuid.uuid4())[:8],
        "sender": "system",
        "content": f"Room '{req.name}' created. Agents: {', '.join(req.agent_ids) if req.agent_ids else 'none yet'}",
        "message_type": "system",
        "timestamp": now,
    })

    rooms[room_id] = room
    save_json(ROOMS_FILE, rooms)
    return {"status": "created", "room": room}


@router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details and message history."""
    rooms = load_json(ROOMS_FILE, {})
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    return rooms[room_id]


@router.post("/rooms/{room_id}/message")
async def send_message(room_id: str, req: SendMessageRequest):
    """Send a message to a room. MAD can message any agent; agents can message each other."""
    rooms = load_json(ROOMS_FILE, {})
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    msg = {
        "id": str(uuid.uuid4())[:8],
        "sender": req.sender,
        "content": req.content,
        "message_type": req.message_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    rooms[room_id]["messages"].append(msg)
    rooms[room_id]["updated_at"] = msg["timestamp"]
    save_json(ROOMS_FILE, rooms)

    return {"status": "sent", "message": msg}


@router.post("/rooms/{room_id}/agents")
async def add_agent_to_room(room_id: str, session_key: str):
    """Add an agent to an existing room."""
    rooms = load_json(ROOMS_FILE, {})
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    if session_key not in rooms[room_id]["agent_ids"]:
        rooms[room_id]["agent_ids"].append(session_key)
        rooms[room_id]["messages"].append({
            "id": str(uuid.uuid4())[:8],
            "sender": "system",
            "content": f"Agent {session_key} joined the room",
            "message_type": "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        save_json(ROOMS_FILE, rooms)

    return {"status": "added", "room": rooms[room_id]}


@router.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    """Delete a room."""
    rooms = load_json(ROOMS_FILE, {})
    if room_id in rooms:
        del rooms[room_id]
        save_json(ROOMS_FILE, rooms)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Room not found")


# ── Direct Messaging ────────────────────────────────────────────────────────
@router.get("/dm/{agent_session_key}")
async def get_dm_history(agent_session_key: str):
    """Get DM history between MAD and a specific agent."""
    # DMs are stored as rooms with exactly 2 participants
    rooms = load_json(ROOMS_FILE, {})
    dm_rooms = [
        r for r in rooms.values()
        if r.get("name", "").startswith("DM:") and agent_session_key in r.get("agent_ids", [])
    ]
    if dm_rooms:
        return {"messages": dm_rooms[0]["messages"], "room_id": dm_rooms[0]["id"]}
    return {"messages": [], "room_id": None}


@router.post("/dm/{agent_session_key}")
async def send_dm(agent_session_key: str, req: SendMessageRequest):
    """Send a direct message to an agent. Creates DM room if needed."""
    rooms = load_json(ROOMS_FILE, {})

    # Find existing DM room
    dm_room = None
    for rid, r in rooms.items():
        if r.get("name", "").startswith("DM:") and agent_session_key in r.get("agent_ids", []):
            dm_room = r
            break

    if not dm_room:
        # Create DM room
        room_id = str(uuid.uuid4())[:8]
        dm_room = {
            "id": room_id,
            "name": f"DM: MAD ↔ {agent_session_key.split(':')[-1][:20]}",
            "description": "Direct message",
            "agent_ids": [agent_session_key],
            "persistent": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "status": "active",
        }
        rooms[room_id] = dm_room

    msg = {
        "id": str(uuid.uuid4())[:8],
        "sender": req.sender,
        "content": req.content,
        "message_type": req.message_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    dm_room["messages"].append(msg)
    dm_room["updated_at"] = msg["timestamp"]
    save_json(ROOMS_FILE, rooms)

    return {"status": "sent", "message": msg, "room_id": dm_room["id"]}
