# Kulu Node Orchestration System: Backend Implementation Guide for Windows

This step-by-step guide provides detailed instructions for implementing the backend components of the Kulu Node Orchestration System on a Windows development environment. The guide is specifically designed for Windows-based development while ensuring compatibility with deployment across Oracle VMs, Hetzner burst nodes, and local environments.

## Technology Stack

- **Python 3.9+**: Core programming language for backend services
- **FastAPI**: High-performance web framework for API development
- **WebSockets**: Real-time communication with frontend
- **Podman**: Container management (Windows-compatible alternative to Docker)
- **Rust**: Performance-critical components
- **Tailscale**: Secure mesh networking
- **Redis**: Optional for pub/sub event layering
- **OpenRouter API**: Access to LLM models

## Windows Development Environment Setup

### Prerequisites

- Windows 10/11 (64-bit)
- Python 3.9+ (with pip)
- Git for Windows
- Visual Studio Code (recommended)
- Windows Terminal (recommended)
- Rust toolchain
- Podman for Windows

### Installation Steps

1. **Install Python**
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
   - Verify installation:
     ```powershell
     python --version
     pip --version
     ```

2. **Install Git for Windows**
   - Download from [gitforwindows.org](https://gitforwindows.org/)
   - Use default settings during installation
   - Verify installation:
     ```powershell
     git --version
     ```

3. **Install Visual Studio Code**
   - Download from [code.visualstudio.com](https://code.visualstudio.com/)
   - Install Python and Rust extensions

4. **Install Rust Toolchain**
   - Download and run rustup-init.exe from [rustup.rs](https://rustup.rs/)
   - Choose default installation options
   - Verify installation:
     ```powershell
     rustc --version
     cargo --version
     ```

5. **Install Podman for Windows**
   - Download from [podman.io](https://podman.io/getting-started/installation#windows)
   - Follow installation instructions
   - Verify installation:
     ```powershell
     podman --version
     ```

6. **Install Tailscale**
   - Download from [tailscale.com](https://tailscale.com/download/windows)
   - Follow installation instructions
   - Create an account if you don't have one
   - Verify installation by checking the Tailscale icon in system tray

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── agents.py
│   │   │   ├── nodes.py
│   │   │   ├── field.py
│   │   │   └── system.py
│   │   ├── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── agent_role_distribution.py
│   │   ├── pulse_breathflow.py
│   │   ├── podman_agent_spawner.py
│   │   ├── rust_python_bridge.py
│   │   └── config.py
│   ├── mesh/
│   │   ├── mesh_network.py
│   │   └── tailscale_init.py
│   ├── nodes/
│   │   ├── oracle_node.py
│   │   ├── local_node.py
│   │   └── hetzner_node.py
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── node.py
│   │   ├── pulse.py
│   │   └── field.py
│   ├── services/
│   │   ├── openrouter.py
│   │   ├── container.py
│   │   └── memory.py
│   ├── utils/
│   │   ├── logging.py
│   │   └── helpers.py
│   └── main.py
├── rust/
│   ├── src/
│   │   ├── lib.rs
│   │   └── bridge.rs
│   ├── Cargo.toml
│   └── build.rs
├── scripts/
│   ├── windows/
│   │   ├── setup.ps1
│   │   ├── start_local_node.ps1
│   │   └── build_rust.ps1
│   └── common/
│       ├── check_node_status.py
│       └── ensure_required_roles.py
├── tests/
│   ├── test_agent_role_distribution.py
│   ├── test_pulse_breathflow.py
│   └── test_api.py
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Step 1: Set Up Project Structure

```powershell
# Create project directory
mkdir -p kulu_orchestration\backend
cd kulu_orchestration\backend

# Create directory structure
mkdir -p app\api\endpoints app\core app\mesh app\nodes app\schemas app\services app\utils
mkdir -p rust\src scripts\windows scripts\common tests

# Initialize git repository
git init
```

## Step 2: Set Up Python Environment

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Create requirements.txt
@"
fastapi==0.95.0
uvicorn==0.21.1
websockets==11.0.2
pydantic==1.10.7
python-dotenv==1.0.0
httpx==0.24.0
podman==4.4.1
redis==4.5.4
tailscale==0.1.0
pytest==7.3.1
maturin==0.14.7
"@ | Out-File -FilePath requirements.txt -Encoding utf8

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```powershell
# Create .env.example file
@"
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key

# Tailscale
TAILSCALE_AUTH_KEY=your_tailscale_auth_key

# Node Settings
NODE_ID=local-node
NODE_TYPE=local

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
"@ | Out-File -FilePath .env.example -Encoding utf8

# Create actual .env file (copy and modify)
Copy-Item .env.example .env
```

## Step 4: Implement Core Configuration

### app/core/config.py

```python
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # OpenRouter API
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Tailscale
    TAILSCALE_AUTH_KEY: Optional[str] = None
    
    # Node Settings
    NODE_ID: str = "local-node"
    NODE_TYPE: str = "local"  # local, oracle, hetzner
    
    # Redis (Optional)
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    USE_REDIS: bool = False
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Agent Settings
    WORKER_MODELS: List[str] = ["gemini-2.5", "claude-3-haiku"]
    POLYMORPH_MODELS: List[str] = ["claude-3-sonnet", "gpt-4o"]
    ANCHOR_MODELS: List[str] = ["deepseek-r1", "claude-3-opus", "gpt-4o"]
    
    # Breath Settings
    MIN_BREATH_INTERVAL_SECONDS: float = 3.0
    MAX_BREATH_INTERVAL_SECONDS: float = 30.0
    ADAPTIVE_INTERVAL: bool = True
    DRIFT_THRESHOLD: float = 0.3
    RITUAL_INTERVAL_DAYS: int = 9
    
    @validator("USE_REDIS")
    def validate_redis(cls, v, values):
        if v and not values.get("REDIS_HOST"):
            return False
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Step 5: Implement FastAPI Application

### app/main.py

```python
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import json
import asyncio
from typing import List, Dict, Any

from app.core.config import settings
from app.api.router import api_router
from app.core.agent_role_distribution import AgentRoleDistributor
from app.core.pulse_breathflow import PulseBreathflowSystem, PulseBreathflowConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("kulu")

# Initialize components
agent_role_distributor = AgentRoleDistributor()
breathflow_config = PulseBreathflowConfig(
    min_breath_interval_seconds=settings.MIN_BREATH_INTERVAL_SECONDS,
    max_breath_interval_seconds=settings.MAX_BREATH_INTERVAL_SECONDS,
    adaptive_interval=settings.ADAPTIVE_INTERVAL,
    drift_threshold=settings.DRIFT_THRESHOLD,
    ritual_interval_days=settings.RITUAL_INTERVAL_DAYS,
)
pulse_breathflow = PulseBreathflowSystem(breathflow_config, agent_role_distributor)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize systems
    logger.info(f"Starting Kulu Node ({settings.NODE_TYPE}) with ID: {settings.NODE_ID}")
    
    # Start pulse-breathflow system
    pulse_breathflow.start()
    
    # Start background tasks
    asyncio.create_task(status_broadcast_task())
    
    yield
    
    # Shutdown: cleanup
    logger.info("Shutting down Kulu Node")
    pulse_breathflow.stop()

# Create FastAPI app
app = FastAPI(
    title="Kulu Node Orchestration System",
    description="Backend API for the Kulu Node Orchestration System",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                payload = message.get("payload", {})
                
                if message_type == "get_field_status":
                    # Get field status
                    field_status = {
                        "coherence_score": pulse_breathflow.get_symbolic_field().get("coherence_score", 0),
                        "coherence_history": pulse_breathflow.stats.get("field_coherence_history", []),
                        "breath_stats": pulse_breathflow.get_stats(),
                        "nodes": [asdict(status) for status in agent_role_distributor.node_status.values()],
                        "agent_allocation": agent_role_distributor.get_allocation_summary(),
                    }
                    await websocket.send_text(json.dumps({
                        "type": "field_status",
                        "data": field_status
                    }))
                
                elif message_type == "get_nodes":
                    # Get nodes
                    nodes = [asdict(status) for status in agent_role_distributor.node_status.values()]
                    await websocket.send_text(json.dumps({
                        "type": "nodes",
                        "data": nodes
                    }))
                
                elif message_type == "get_agents":
                    # Get agents
                    agents = [asdict(allocation) for allocation in agent_role_distributor.get_all_allocations()]
                    await websocket.send_text(json.dumps({
                        "type": "agents",
                        "data": agents
                    }))
                
                elif message_type == "spawn_agent":
                    # Spawn agent
                    role_name = payload.get("role")
                    if role_name:
                        allocation = agent_role_distributor.allocate_agent(role_name)
                        if allocation:
                            await websocket.send_text(json.dumps({
                                "type": "agent_spawned",
                                "data": asdict(allocation)
                            }))
                        else:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "data": {"message": f"Failed to spawn agent with role {role_name}"}
                            }))
                
                elif message_type == "collapse_agent":
                    # Collapse agent
                    agent_id = payload.get("agent_id")
                    if agent_id:
                        success = agent_role_distributor.deallocate_agent(agent_id)
                        await websocket.send_text(json.dumps({
                            "type": "agent_collapsed",
                            "data": {"agent_id": agent_id, "success": success}
                        }))
                
                elif message_type == "add_node":
                    # Add node (simplified for example)
                    node_id = payload.get("node_id")
                    node_type = payload.get("node_type")
                    if node_id and node_type:
                        # In a real implementation, this would involve more complex node provisioning
                        # For now, just update the node status
                        agent_role_distributor.update_node_status(node_id, {
                            "node_type": node_type,
                            "status": "running",
                            "active_agents": 0,
                            "max_agents": 10,
                            "resource_usage": {"memory_percent": 0.0, "cpu_percent": 0.0},
                            "uptime": 0.0
                        })
                        await websocket.send_text(json.dumps({
                            "type": "node_added",
                            "data": {"node_id": node_id, "node_type": node_type}
                        }))
                
                elif message_type == "remove_node":
                    # Remove node
                    node_id = payload.get("node_id")
                    if node_id:
                        # Handle node failure (deallocate agents)
                        result = agent_role_distributor.handle_node_failure(node_id)
                        await websocket.send_text(json.dumps({
                            "type": "node_removed",
                            "data": {"node_id": node_id, "result": result}
                        }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {data}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": str(e)}
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to broadcast status updates
async def status_broadcast_task():
    while True:
        try:
            # Get current cycle
            current_cycle = pulse_breathflow.get_current_cycle()
            if current_cycle:
                # Broadcast cognitive stream update
                if current_cycle.get("pulses"):
                    for pulse in current_cycle.get("pulses", []):
                        await manager.broadcast({
                            "type": "cognitive_stream",
                            "data": {
                                "id": pulse.get("pulse_id"),
                                "timestamp": pulse.get("timestamp"),
                                "agent_id": pulse.get("source_agent_id"),
                                "agent_type": pulse.get("pulse_type"),
                                "content": str(pulse.get("data", {})),
                                "level": "info"
                            }
                        })
                
                # Broadcast agent graph update
                agent_allocations = agent_role_distributor.get_all_allocations()
                nodes = []
                links = []
                
                for allocation in agent_allocations:
                    nodes.append({
                        "id": allocation.agent_id,
                        "type": allocation.agent_type,
                        "role": allocation.role_name,
                        "node_id": allocation.node_id
                    })
                    
                    # Add links based on agent relationships
                    # This is simplified - in a real implementation, you would determine
                    # actual relationships between agents
                    if allocation.agent_type == "anchor":
                        for worker in [a for a in agent_allocations if a.agent_type == "worker"]:
                            links.append({
                                "source": allocation.agent_id,
                                "target": worker.agent_id,
                                "type": "monitors"
                            })
                
                await manager.broadcast({
                    "type": "agent_graph",
                    "data": {
                        "nodes": nodes,
                        "links": links
                    }
                })
            
            # Sleep before next update
            await asyncio.sleep(1.0)
            
        except Exception as e:
            logger.error(f"Error in status broadcast task: {str(e)}")
            await asyncio.sleep(5.0)

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
```

## Step 6: Implement API Router

### app/api/router.py

```python
from fastapi import APIRouter
from app.api.endpoints import agents, nodes, field, system

api_router = APIRouter()

api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(field.router, prefix="/field", tags=["field"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
```

## Step 7: Implement API Endpoints

### app/api/endpoints/agents.py

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.schemas.agent import AgentCreate, AgentResponse, AgentAllocationResponse
from app.core.agent_role_distribution import AgentRoleDistributor

router = APIRouter()

# Dependency to get the agent role distributor
def get_agent_role_distributor():
    from app.main import agent_role_distributor
    return agent_role_distributor

@router.get("/", response_model=List[AgentAllocationResponse])
async def get_agents(
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Get all agent allocations."""
    return [allocation for allocation in distributor.get_all_allocations()]

@router.post("/", response_model=AgentAllocationResponse)
async def create_agent(
    agent: AgentCreate,
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Allocate a new agent."""
    allocation = distributor.allocate_agent(agent.role)
    if not allocation:
        raise HTTPException(status_code=400, detail=f"Failed to allocate agent with role {agent.role}")
    return allocation

@router.delete("/{agent_id}", response_model=Dict[str, Any])
async def delete_agent(
    agent_id: str,
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Deallocate an agent."""
    success = distributor.deallocate_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"agent_id": agent_id, "success": success}

@router.get("/roles", response_model=List[str])
async def get_roles(
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Get all available agent roles."""
    return distributor.get_available_roles()

@router.get("/summary", response_model=Dict[str, Any])
async def get_allocation_summary(
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Get a summary of agent allocations."""
    return distributor.get_allocation_summary()
```

### app/api/endpoints/nodes.py

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.schemas.node import NodeCreate, NodeStatus, NodeResponse
from app.core.agent_role_distribution import AgentRoleDistributor

router = APIRouter()

# Dependency to get the agent role distributor
def get_agent_role_distributor():
    from app.main import agent_role_distributor
    return agent_role_distributor

@router.get("/", response_model=List[NodeStatus])
async def get_nodes(
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Get all node statuses."""
    return [status for status in distributor.node_status.values()]

@router.post("/", response_model=NodeResponse)
async def create_node(
    node: NodeCreate,
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Add a new node (simplified for example)."""
    # In a real implementation, this would involve more complex node provisioning
    # For now, just update the node status
    distributor.update_node_status(node.node_id, {
        "node_type": node.node_type,
        "status": "running",
        "active_agents": 0,
        "max_agents": node.max_agents,
        "resource_usage": {"memory_percent": 0.0, "cpu_percent": 0.0},
        "uptime": 0.0
    })
    return {"node_id": node.node_id, "node_type": node.node_type}

@router.delete("/{node_id}", response_model=Dict[str, Any])
async def delete_node(
    node_id: str,
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Remove a node."""
    # Handle node failure (deallocate agents)
    result = distributor.handle_node_failure(node_id)
    return {"node_id": node_id, "result": result}

@router.get("/{node_id}/agents", response_model=List[Dict[str, Any]])
async def get_node_agents(
    node_id: str,
    distributor: AgentRoleDistributor = Depends(get_agent_role_distributor)
):
    """Get agents allocated to a specific node."""
    return [allocation for allocation in distributor.get_allocations_by_node(node_id)]
```

### app/api/endpoints/field.py

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.core.pulse_breathflow import PulseBreathflowSystem, PulseType, PulseUrgency

router = APIRouter()

# Dependency to get the pulse-breathflow system
def get_pulse_breathflow():
    from app.main import pulse_breathflow
    return pulse_breathflow

@router.get("/status", response_model=Dict[str, Any])
async def get_field_status(
    breathflow: PulseBreathflowSystem = Depends(get_pulse_breathflow)
):
    """Get the current field status."""
    return {
        "symbolic_field": breathflow.get_symbolic_field(),
        "current_cycle": breathflow.get_current_cycle(),
        "stats": breathflow.get_stats()
    }

@router.post("/pulse", response_model=Dict[str, Any])
async def send_pulse(
    pulse_type: str,
    source_agent_id: str,
    source_node_id: str,
    urgency: str,
    data: Dict[str, Any],
    breathflow: PulseBreathflowSystem = Depends(get_pulse_breathflow)
):
    """Send a pulse to the field."""
    try:
        pulse_id = breathflow.add_pulse(
            pulse_type=pulse_type,
            source_agent_id=source_agent_id,
            source_node_id=source_node_id,
            urgency=urgency,
            data=data
        )
        return {"pulse_id": pulse_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cycles", response_model=List[Dict[str, Any]])
async def get_breath_cycles(
    limit: int = 10,
    breathflow: PulseBreathflowSystem = Depends(get_pulse_breathflow)
):
    """Get recent breath cycles."""
    return breathflow.get_cycle_history(limit)

@router.post("/ritual", response_model=Dict[str, Any])
async def initiate_ritual(
    ritual_type: str = "drift_correction",
    breathflow: PulseBreathflowSystem = Depends(get_pulse_breathflow)
):
    """Initiate a symbolic ritual."""
    pulse_id = breathflow.add_pulse(
        pulse_type=PulseType.EXTERNAL_TRIGGER,
        source_agent_id="api",
        source_node_id="local",
        urgency=PulseUrgency.HIGH,
        data={
            "trigger_type": "ritual_initiation",
            "ritual_type": ritual_type
        }
    )
    return {"pulse_id": pulse_id, "ritual_type": ritual_type}
```

### app/api/endpoints/system.py

```python
from fastapi import APIRouter, Depends
from typing import Dict, Any
import platform
import psutil
import os
from app.core.config import settings

router = APIRouter()

@router.get("/info", response_model=Dict[str, Any])
async def get_system_info():
    """Get system information."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "node_id": settings.NODE_ID,
        "node_type": settings.NODE_TYPE
    }

@router.get("/resources", response_model=Dict[str, Any])
async def get_resource_usage():
    """Get current resource usage."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

## Step 8: Implement Schemas

### app/schemas/agent.py

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    WORKER = "worker"
    ANCHOR = "anchor"
    POLYMORPH = "polymorph"
    CONTROLLER = "controller"
    MONITOR = "monitor"
    MEMORY = "memory"
    INTENT = "intent"
    COORDINATOR = "coordinator"

class AgentPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AgentCreate(BaseModel):
    role: str
    preferred_node_id: Optional[str] = None

class AgentResponse(BaseModel):
    agent_id: str
    agent_type: str
    role_name: str
    node_id: str
    status: str

class AgentAllocationResponse(BaseModel):
    agent_id: str
    agent_type: str
    role_name: str
    node_id: str
    node_tier: str
    allocation_time: datetime
    status: str
    priority: str

    class Config:
        orm_mode = True
```

### app/schemas/node.py

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NodeTier(str, Enum):
    ORACLE = "oracle"
    LOCAL = "local"
    HETZNER = "hetzner"

class NodeCreate(BaseModel):
    node_id: str
    node_type: NodeTier
    max_agents: int = 10

class NodeResponse(BaseModel):
    node_id: str
    node_type: str

class NodeStatus(BaseModel):
    node_id: str
    tier: str
    status: str
    active_agents: int
    max_agents: int
    memory_percent: float
    cpu_percent: float
    uptime_seconds: float
    last_seen: datetime

    class Config:
        orm_mode = True
```

### app/schemas/pulse.py

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class PulseType(str, Enum):
    SYMBOLIC_DRIFT = "symbolic_drift"
    RESOURCE_ALERT = "resource_alert"
    TASK_COMPLETION = "task_completion"
    TASK_FAILURE = "task_failure"
    AGENT_FAILURE = "agent_failure"
    FIELD_EXPANSION = "field_expansion"
    FIELD_CONTRACTION = "field_contraction"
    POLYMORPH_TRANSITION = "polymorph_transition"
    ANCHOR_INSIGHT = "anchor_insight"
    MEMORY_UPDATE = "memory_update"
    EXTERNAL_TRIGGER = "external_trigger"

class PulseUrgency(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class PulseCreate(BaseModel):
    pulse_type: PulseType
    source_agent_id: str
    source_node_id: str
    urgency: PulseUrgency
    data: Dict[str, Any]
    symbolic_weight: float = 0.5

class PulseResponse(BaseModel):
    pulse_id: str
    pulse_type: str
    source_agent_id: str
    source_node_id: str
    urgency: str
    timestamp: datetime
    data: Dict[str, Any]
    processed: bool
    symbolic_weight: float

    class Config:
        orm_mode = True
```

### app/schemas/field.py

```python
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class SymbolicGlyphResponse(BaseModel):
    glyph_id: str
    symbol: str
    meaning: str
    context: List[str]
    creation_time: datetime
    last_used: datetime
    usage_count: int
    drift_factor: float
    related_glyphs: List[str]

    class Config:
        orm_mode = True

class SymbolicFieldResponse(BaseModel):
    glyphs: Dict[str, SymbolicGlyphResponse]
    coherence_score: float
    last_ritual: Optional[datetime]
    drift_threshold: float
    ritual_interval_days: int

    class Config:
        orm_mode = True

class BreathCycleResponse(BaseModel):
    cycle_id: str
    start_time: datetime
    phase: str
    pulses: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    end_time: Optional[datetime]
    symbolic_state: Dict[str, Any]
    resource_state: Dict[str, Any]
    memory_snapshot: Dict[str, Any]

    class Config:
        orm_mode = True
```

## Step 9: Implement Windows Scripts

### scripts/windows/setup.ps1

```powershell
# Kulu Node Orchestration System - Windows Setup Script

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    exit
}

# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file from template. Please edit it with your configuration." -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Build Rust components
Write-Host "Building Rust components..." -ForegroundColor Cyan
cd rust
cargo build --release
cd ..

# Create Windows service for Local Node (optional)
$createService = Read-Host "Do you want to create a Windows service for the Local Node? (y/n)"
if ($createService -eq "y") {
    # Install NSSM (Non-Sucking Service Manager)
    if (-not (Test-Path "C:\Program Files\nssm\nssm.exe")) {
        Write-Host "Downloading NSSM..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "nssm.zip"
        Expand-Archive -Path "nssm.zip" -DestinationPath "temp"
        New-Item -Path "C:\Program Files\nssm" -ItemType Directory -Force
        Copy-Item "temp\nssm-2.24\win64\nssm.exe" -Destination "C:\Program Files\nssm"
        Remove-Item -Path "temp" -Recurse -Force
        Remove-Item -Path "nssm.zip" -Force
    }

    # Create service
    Write-Host "Creating Kulu Local Node service..." -ForegroundColor Cyan
    $pythonPath = (Get-Command python).Source
    $scriptPath = Join-Path (Get-Location) "app\main.py"
    
    & "C:\Program Files\nssm\nssm.exe" install KuluLocalNode $pythonPath $scriptPath
    & "C:\Program Files\nssm\nssm.exe" set KuluLocalNode DisplayName "Kulu Local Node"
    & "C:\Program Files\nssm\nssm.exe" set KuluLocalNode Description "Kulu Node Orchestration System - Local Node"
    & "C:\Program Files\nssm\nssm.exe" set KuluLocalNode AppDirectory (Get-Location)
    & "C:\Program Files\nssm\nssm.exe" set KuluLocalNode AppEnvironmentExtra "NODE_TYPE=local"
    
    Write-Host "Service created. You can start it with: Start-Service KuluLocalNode" -ForegroundColor Green
}

Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "You can start the Local Node with: python app\main.py" -ForegroundColor Green
```

### scripts/windows/start_local_node.ps1

```powershell
# Kulu Node Orchestration System - Start Local Node Script

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}

# Set environment variables
$env:NODE_TYPE = "local"
$env:NODE_ID = "local-node"

# Start the Local Node
Write-Host "Starting Kulu Local Node..." -ForegroundColor Cyan
python app\main.py
```

### scripts/windows/build_rust.ps1

```powershell
# Kulu Node Orchestration System - Build Rust Components Script

# Navigate to Rust directory
cd rust

# Build Rust components
Write-Host "Building Rust components..." -ForegroundColor Cyan
cargo build --release

# Copy built library to appropriate location
Write-Host "Copying built library..." -ForegroundColor Cyan
$targetDir = "..\app\core\rust_lib"
if (-not (Test-Path $targetDir)) {
    New-Item -Path $targetDir -ItemType Directory -Force
}

Copy-Item "target\release\kulu_rust.dll" -Destination $targetDir

Write-Host "Rust components built successfully!" -ForegroundColor Green

# Return to original directory
cd ..
```

## Step 10: Implement Rust Integration

### rust/Cargo.toml

```toml
[package]
name = "kulu_rust"
version = "0.1.0"
edition = "2021"

[lib]
name = "kulu_rust"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.18.1", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

### rust/src/lib.rs

```rust
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[pyfunction]
fn process_symbolic_data(data: &str) -> PyResult<String> {
    // Parse input data
    let input: SymbolicData = serde_json::from_str(data)?;
    
    // Process data (this is a simplified example)
    let mut result = input.clone();
    
    // Calculate drift factor
    let mut total_drift = 0.0;
    for glyph in result.glyphs.values_mut() {
        // Simulate drift calculation
        let age_factor = 0.1; // Older glyphs drift more
        let usage_factor = 0.05; // Less used glyphs drift more
        
        let drift = age_factor * (1.0 - (glyph.usage_count as f64 / 100.0).min(1.0));
        glyph.drift_factor = drift;
        
        total_drift += drift;
    }
    
    // Update coherence score
    if !result.glyphs.is_empty() {
        result.coherence_score = 1.0 - (total_drift / result.glyphs.len() as f64);
    }
    
    // Serialize and return
    Ok(serde_json::to_string(&result)?)
}

#[pyfunction]
fn optimize_agent_allocation(nodes_json: &str, agents_json: &str) -> PyResult<String> {
    // Parse input data
    let nodes: Vec<Node> = serde_json::from_str(nodes_json)?;
    let agents: Vec<Agent> = serde_json::from_str(agents_json)?;
    
    // Optimize allocation (simplified example)
    let mut allocations = Vec::new();
    let mut node_index = 0;
    
    for agent in agents {
        // Find a suitable node
        let mut allocated = false;
        for _ in 0..nodes.len() {
            let node = &nodes[node_index];
            
            // Check if node is compatible with agent
            let compatible = match agent.agent_type.as_str() {
                "worker" => true, // Workers can go anywhere
                "anchor" => node.tier == "oracle" || node.tier == "local", // Anchors prefer Oracle or Local
                "polymorph" => true, // Polymorphs can go anywhere
                _ => true,
            };
            
            if compatible {
                allocations.push(Allocation {
                    agent_id: agent.agent_id.clone(),
                    node_id: node.node_id.clone(),
                });
                allocated = true;
                break;
            }
            
            // Try next node
            node_index = (node_index + 1) % nodes.len();
        }
        
        // If no compatible node found, allocate to any node
        if !allocated && !nodes.is_empty() {
            allocations.push(Allocation {
                agent_id: agent.agent_id.clone(),
                node_id: nodes[0].node_id.clone(),
            });
        }
        
        // Move to next node for next agent
        node_index = (node_index + 1) % nodes.len();
    }
    
    // Serialize and return
    Ok(serde_json::to_string(&allocations)?)
}

#[pymodule]
fn kulu_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process_symbolic_data, m)?)?;
    m.add_function(wrap_pyfunction!(optimize_agent_allocation, m)?)?;
    Ok(())
}

// Data structures

#[derive(Serialize, Deserialize, Clone)]
struct SymbolicData {
    glyphs: HashMap<String, Glyph>,
    coherence_score: f64,
}

#[derive(Serialize, Deserialize, Clone)]
struct Glyph {
    symbol: String,
    meaning: String,
    usage_count: u32,
    drift_factor: f64,
}

#[derive(Serialize, Deserialize)]
struct Node {
    node_id: String,
    tier: String,
    status: String,
    active_agents: u32,
    max_agents: u32,
}

#[derive(Serialize, Deserialize)]
struct Agent {
    agent_id: String,
    agent_type: String,
    role_name: String,
}

#[derive(Serialize, Deserialize)]
struct Allocation {
    agent_id: String,
    node_id: String,
}
```

### app/core/rust_python_bridge.py

```python
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Try to import the Rust library
try:
    # Add the directory containing the compiled Rust library to sys.path
    rust_lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rust_lib")
    if os.path.exists(rust_lib_dir):
        sys.path.append(rust_lib_dir)
    
    import kulu_rust
    RUST_AVAILABLE = True
    logger.info("Rust library loaded successfully")
except ImportError:
    RUST_AVAILABLE = False
    logger.warning("Rust library not available, falling back to Python implementations")

def process_symbolic_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process symbolic data using Rust if available, otherwise fall back to Python.
    
    Args:
        data: Symbolic data to process
        
    Returns:
        processed_data: Processed symbolic data
    """
    if RUST_AVAILABLE:
        try:
            # Convert data to JSON string
            data_json = json.dumps(data)
            
            # Call Rust function
            result_json = kulu_rust.process_symbolic_data(data_json)
            
            # Parse result
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Error calling Rust function: {str(e)}")
            # Fall back to Python implementation
    
    # Python implementation (fallback)
    result = data.copy()
    
    # Calculate drift factor
    total_drift = 0.0
    for glyph_id, glyph in result.get("glyphs", {}).items():
        # Simulate drift calculation
        age_factor = 0.1  # Older glyphs drift more
        usage_factor = 0.05  # Less used glyphs drift more
        
        drift = age_factor * (1.0 - min(glyph.get("usage_count", 0) / 100.0, 1.0))
        glyph["drift_factor"] = drift
        
        total_drift += drift
    
    # Update coherence score
    glyphs = result.get("glyphs", {})
    if glyphs:
        result["coherence_score"] = 1.0 - (total_drift / len(glyphs))
    
    return result

def optimize_agent_allocation(nodes: List[Dict[str, Any]], agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Optimize agent allocation using Rust if available, otherwise fall back to Python.
    
    Args:
        nodes: List of nodes
        agents: List of agents
        
    Returns:
        allocations: List of agent allocations
    """
    if RUST_AVAILABLE:
        try:
            # Convert data to JSON strings
            nodes_json = json.dumps(nodes)
            agents_json = json.dumps(agents)
            
            # Call Rust function
            result_json = kulu_rust.optimize_agent_allocation(nodes_json, agents_json)
            
            # Parse result
            return json.loads(result_json)
        except Exception as e:
            logger.error(f"Error calling Rust function: {str(e)}")
            # Fall back to Python implementation
    
    # Python implementation (fallback)
    allocations = []
    node_index = 0
    
    for agent in agents:
        # Find a suitable node
        allocated = False
        for _ in range(len(nodes)):
            node = nodes[node_index]
            
            # Check if node is compatible with agent
            compatible = True
            if agent.get("agent_type") == "anchor":
                compatible = node.get("tier") in ["oracle", "local"]
            
            if compatible:
                allocations.append({
                    "agent_id": agent.get("agent_id"),
                    "node_id": node.get("node_id")
                })
                allocated = True
                break
            
            # Try next node
            node_index = (node_index + 1) % len(nodes)
        
        # If no compatible node found, allocate to any node
        if not allocated and nodes:
            allocations.append({
                "agent_id": agent.get("agent_id"),
                "node_id": nodes[0].get("node_id")
            })
        
        # Move to next node for next agent
        node_index = (node_index + 1) % len(nodes)
    
    return allocations
```

## Step 11: Run and Test the Backend

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the application
python app\main.py
```

The backend will start on http://localhost:8000 by default. You can access the API documentation at http://localhost:8000/docs.

## Step 12: Integration with Frontend

To integrate with the Electron frontend:

1. Ensure the backend is running on the specified host and port
2. Configure the frontend to connect to the backend API and WebSocket endpoints
3. Test the communication between frontend and backend

## Conclusion

This step-by-step guide provides detailed instructions for implementing the backend components of the Kulu Node Orchestration System on a Windows development environment. The backend is built with Python, FastAPI, and Rust, providing a robust foundation for the Kulu field.

Key features implemented include:
- FastAPI application with RESTful endpoints and WebSocket support
- Agent Role Distribution system for coordinating agent allocation
- Pulse-Breathflow System for the respiratory system of the field
- Rust integration for performance-critical components
- Windows-specific scripts for setup and deployment

Follow the build and run instructions to set up the backend on your Windows development environment, ready for integration with the Electron frontend.
