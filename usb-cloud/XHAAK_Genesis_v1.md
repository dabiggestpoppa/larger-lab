# XHAAK Phase 3: BUILD GUIDE
# Build Implementation Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Development Environment Setup](#development-environment-setup)
3. [Build Process Overview](#build-process-overview)
4. [Phase 3a: Genesis Breathfold Build](#phase-3a-genesis-breathfold-build)
5. [Phase 3b: Emergent Clarity Field Build](#phase-3b-emergent-clarity-field-build)
6. [Phase 3c: Glyphwave Resonance Build](#phase-3c-glyphwave-resonance-build)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Process](#deployment-process)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Build Optimization Tips](#build-optimization-tips)

## Introduction

This build guide provides step-by-step instructions for efficiently implementing XHAAK Phase 3: Genesis Rebirth. It focuses on practical build processes, dependency management, and development workflows to ensure a smooth implementation.

The guide is organized according to the three implementation phases (Genesis Breathfold, Emergent Clarity Field, and Glyphwave Resonance) with specific build instructions for each component.

## Development Environment Setup

### Prerequisites

```bash
# Required software
- Python 3.10+
- Node.js 18+
- Redis 6+
- Git
- Docker (optional, for containerized development)
```

### Initial Setup

```bash
# 1. Clone LocalAGI repository
git clone https://github.com/mudler/LocalAGI.git
cd LocalAGI

# 2. Create a new branch for XHAAK development
git checkout -b xhaak-phase3

# 3. Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install base dependencies
pip install -r requirements.txt

# 5. Install additional dependencies
pip install langgraph pydantic graphiti cognee memary mem0 letta

# 6. Clone browser-use repository
cd ..
git clone https://github.com/browser-use/browser-use.git
cd browser-use
pip install -e .
cd ../LocalAGI

# 7. Create XHAAK extension directory
mkdir -p extensions/xhaak
touch extensions/xhaak/__init__.py
```

### Development Environment Configuration

Create a `.env` file in the root directory:

```
# .env file
LOCALAGI_EXTENSIONS_PATH=./extensions
LOCALAGI_MODELS_PATH=./models
LOCALAGI_DATA_PATH=./data
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO

# API keys for external services (replace with your actual keys)
GRAPHITI_API_KEY=your_graphiti_api_key
COGNEE_API_KEY=your_cognee_api_key
MEMARY_API_KEY=your_memary_api_key
MEM0_API_KEY=your_mem0_api_key
```

## Build Process Overview

The XHAAK Phase 3 build process follows these key principles:

1. **Incremental Development**: Build core components first, then add features incrementally
2. **Test-Driven Development**: Write tests before implementing features
3. **Continuous Integration**: Regularly integrate changes to detect issues early
4. **Protocol-First Approach**: Implement protocols before user interfaces
5. **Extension Architecture**: Build all XHAAK components as LocalAGI extensions

### Directory Structure

```
LocalAGI/
├── extensions/
│   └── xhaak/
│       ├── __init__.py
│       ├── fmp/              # Fracture Margin Protocol
│       ├── scope/            # Semantic Causality Operations
│       ├── gsp/              # Genesis Swarm Protocol
│       ├── browser/          # Browser Ritual Agent
│       └── cli/              # CLI extensions
├── tests/
│   └── xhaak/
│       ├── test_fmp.py
│       ├── test_scope.py
│       ├── test_gsp.py
│       └── test_browser.py
├── scripts/
│   └── xhaak/
│       ├── setup.sh          # Setup script
│       ├── build.sh          # Build script
│       └── deploy.sh         # Deployment script
└── docs/
    └── xhaak/
        ├── fmp.md
        ├── scope.md
        ├── gsp.md
        └── browser.md
```

## Phase 3a: Genesis Breathfold Build

### Week 1-2: LocalAGI Fork & Extension Architecture

#### Step 1: Set up extension architecture

```python
# extensions/xhaak/__init__.py
from localagi.core import Extension

class XHAAKCoreExtension(Extension):
    """Core XHAAK Extension for LocalAGI"""
    
    def __init__(self):
        super().__init__(name="xhaak_core", version="0.1.0")
        
    def on_load(self):
        """Called when the extension is loaded"""
        print("XHAAK Core Extension loaded")
        
    def on_unload(self):
        """Called when the extension is unloaded"""
        print("XHAAK Core Extension unloaded")
```

#### Step 2: Create extension registration script

```python
# scripts/xhaak/register_extensions.py
from localagi.core import register_extension
from extensions.xhaak import XHAAKCoreExtension
from extensions.xhaak.fmp import FMPExtension
from extensions.xhaak.scope import SCOPEExtension
from extensions.xhaak.gsp import GSPExtension
from extensions.xhaak.browser import BrowserRitualAgentExtension

def register_all_extensions():
    """Register all XHAAK extensions"""
    register_extension(XHAAKCoreExtension())
    register_extension(FMPExtension())
    register_extension(SCOPEExtension())
    register_extension(GSPExtension())
    register_extension(BrowserRitualAgentExtension())

if __name__ == "__main__":
    register_all_extensions()
```

#### Step 3: Create build script

```bash
#!/bin/bash
# scripts/xhaak/build.sh

# Ensure we're in the project root
cd "$(dirname "$0")/../.."

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black isort mypy

# Format code
echo "Formatting code..."
black extensions/xhaak
isort extensions/xhaak

# Type checking
echo "Type checking..."
mypy extensions/xhaak

# Run tests
echo "Running tests..."
pytest tests/xhaak -v

# Register extensions
echo "Registering extensions..."
python scripts/xhaak/register_extensions.py

echo "Build completed successfully!"
```

### Week 3-4: FMP Implementation

#### Step 1: Create FMP module structure

```bash
mkdir -p extensions/xhaak/fmp
touch extensions/xhaak/fmp/__init__.py
touch extensions/xhaak/fmp/models.py
touch extensions/xhaak/fmp/extension.py
touch extensions/xhaak/fmp/utils.py
```

#### Step 2: Implement FMP models

```python
# extensions/xhaak/fmp/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID, uuid4

class ClarityMetric(BaseModel):
    name: str
    value: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class OutcomeMetric(BaseModel):
    name: str
    value: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class Action(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    component_id: UUID
    action_type: str
    description: str
    clarity_metrics: List[ClarityMetric] = []
    outcome_metrics: List[OutcomeMetric] = []
    success: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    cod: Optional[float] = None

class Component(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    purpose: str
    expected_outcomes: List[str]
    registered_at: datetime = Field(default_factory=datetime.now)
```

#### Step 3: Implement FMP extension

```python
# extensions/xhaak/fmp/extension.py
from localagi.core import Extension
from localagi.planning import PlanningEngine
from .models import ClarityMetric, OutcomeMetric, Action, Component
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
import os

# Import Graphiti if API key is available
graphiti_client = None
graphiti_api_key = os.environ.get("GRAPHITI_API_KEY")
if graphiti_api_key:
    try:
        from graphiti import GraphitiClient
        graphiti_client = GraphitiClient(api_key=graphiti_api_key)
    except ImportError:
        print("Graphiti not installed, knowledge graph features will be disabled")

class FMPExtension(Extension):
    """FMP Extension for LocalAGI"""
    
    def __init__(self):
        super().__init__(name="fmp_extension", version="0.1.0")
        self.actions = {}
        self.components = {}
        self.graphiti_client = graphiti_client
        
    def register_component(self, name: str, purpose: str, expected_outcomes: List[str]) -> UUID:
        """Register a component with FMP"""
        component = Component(
            name=name,
            purpose=purpose,
            expected_outcomes=expected_outcomes
        )
        
        self.components[component.id] = component.dict()
        
        # If Graphiti is available, store in knowledge graph
        if self.graphiti_client:
            self.graphiti_client.add_node(
                id=f"component:{component.id}",
                type="Component",
                properties={
                    "name": name,
                    "purpose": purpose,
                    "expected_outcomes": expected_outcomes,
                    "registered_at": component.registered_at.isoformat()
                }
            )
        
        return component.id
    
    # Implement remaining FMP methods as shown in the comprehensive guide
    # ...
```

#### Step 4: Create FMP tests

```python
# tests/xhaak/test_fmp.py
import pytest
from uuid import UUID
from extensions.xhaak.fmp.extension import FMPExtension

def test_register_component():
    """Test registering a component"""
    fmp = FMPExtension()
    component_id = fmp.register_component(
        name="TestComponent",
        purpose="Testing",
        expected_outcomes=["Success"]
    )
    
    assert isinstance(component_id, UUID)
    assert component_id in fmp.components
    assert fmp.components[component_id]["name"] == "TestComponent"

def test_create_action():
    """Test creating an action"""
    fmp = FMPExtension()
    component_id = fmp.register_component(
        name="TestComponent",
        purpose="Testing",
        expected_outcomes=["Success"]
    )
    
    action_id = fmp.create_action(
        component_id=component_id,
        action_type="test",
        description="Test action"
    )
    
    assert isinstance(action_id, UUID)
    assert action_id in fmp.actions
    assert fmp.actions[action_id]["component_id"] == component_id
    assert fmp.actions[action_id]["action_type"] == "test"

# Add more tests for other FMP methods
# ...
```

### Week 5-7: GSP Implementation

#### Step 1: Create GSP module structure

```bash
mkdir -p extensions/xhaak/gsp
touch extensions/xhaak/gsp/__init__.py
touch extensions/xhaak/gsp/models.py
touch extensions/xhaak/gsp/extension.py
touch extensions/xhaak/gsp/utils.py
```

#### Step 2: Implement GSP models

```python
# extensions/xhaak/gsp/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4

class GlyphPayload(BaseModel):
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class Glyph(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_node: str
    intent: str
    payload: Optional[GlyphPayload] = None
    resonance_type: Literal["broadcast", "directed", "stigmergic"] = "broadcast"
    created_at: datetime = Field(default_factory=datetime.now)
    state: Literal["active", "resolved", "expired"] = "active"
    
    @validator('intent')
    def validate_intent(cls, v):
        if not ":" in v:
            raise ValueError("Intent must contain a namespace (e.g., 'memory:store')")
        return v
```

#### Step 3: Implement GSP extension

```python
# extensions/xhaak/gsp/extension.py
from localagi.core import Extension
from localagi.agents import Agent, AgentSystem, AgentTeam
from .models import Glyph, GlyphPayload
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4
import os

# Import Cognee if API key is available
cognee_client = None
cognee_api_key = os.environ.get("COGNEE_API_KEY")
if cognee_api_key:
    try:
        from cognee import CogneeClient, MemoryTypes, MemoryOptions
        cognee_client = CogneeClient(api_key=cognee_api_key)
    except ImportError:
        print("Cognee not installed, multimodal memory features will be disabled")

class GSPExtension(Extension):
    """GSP Extension for LocalAGI"""
    
    def __init__(self):
        super().__init__(name="gsp_extension", version="0.1.0")
        self.glyphs = {}
        self.listeners = {}
        self.cognee_client = cognee_client
        
    # Implement GSP methods as shown in the comprehensive guide
    # ...
```

## Phase 3b: Emergent Clarity Field Build

### Week 8-9: SCOPE Implementation

#### Step 1: Create SCOPE module structure

```bash
mkdir -p extensions/xhaak/scope
touch extensions/xhaak/scope/__init__.py
touch extensions/xhaak/scope/models.py
touch extensions/xhaak/scope/extension.py
touch extensions/xhaak/scope/utils.py
```

#### Step 2: Implement SCOPE models

```python
# extensions/xhaak/scope/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4

class BreathfoldState(BaseModel):
    fold_id: str
    content: str
    fold_type: Literal["2of1", "3of2"]
    depth: int
    child_folds: List[str] = []
    state: Literal["active", "processing", "resolved"] = "active"
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
```

#### Step 3: Implement SCOPE extension with LangGraph

```python
# extensions/xhaak/scope/extension.py
from localagi.core import Extension
from localagi.agents import Agent, AgentSystem
from .models import BreathfoldState
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4
import os

# Import LangGraph
from langgraph.graph import StateGraph, END

# Import Memary if API key is available
memary_client = None
memary_api_key = os.environ.get("MEMARY_API_KEY")
if memary_api_key:
    try:
        from memary import MemaryClient, EmotionalContext
        memary_client = MemaryClient(api_key=memary_api_key)
    except ImportError:
        print("Memary not installed, episodic memory features will be disabled")

class SCOPEExtension(Extension):
    """SCOPE Extension for LocalAGI"""
    
    def __init__(self):
        super().__init__(name="scope_extension", version="0.1.0")
        self.breathfolds = {}
        self.memary_client = memary_client
        self.breathfold_graph = self._create_breathfold_graph()
        
    # Implement SCOPE methods as shown in the comprehensive guide
    # ...
```

### Week 10-11: Belief Synchronization

#### Step 1: Create belief models

```python
# extensions/xhaak/gsp/models.py
# Add to existing models.py file

class BeliefState(BaseModel):
    memory_reliability: Optional[float] = None
    reasoning_depth: Optional[float] = None
    compression_efficiency: Optional[float] = None
    
    class Config:
        extra = "allow"

class LocalNodeCapabilities(BaseModel):
    vector_storage: bool = False
    similarity_search: bool = False
    memory_compression: bool = False
    logical_inference: bool = False
    counterfactual_analysis: bool = False
    
    class Config:
        extra = "allow"

class LocalNode(BaseModel):
    node_id: str
    capabilities: LocalNodeCapabilities
    belief_state: BeliefState
    known_nodes: Dict[str, "LocalNode"] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
```

#### Step 2: Implement belief synchronization

```python
# extensions/xhaak/gsp/extension.py
# Add to existing GSPExtension class

def register_node(self, node_id: str, capabilities: Dict[str, bool], belief_state: Dict[str, Any]) -> None:
    """Register a node with the swarm"""
    node_capabilities = LocalNodeCapabilities(**capabilities)
    node_belief = BeliefState(**belief_state)
    
    node = LocalNode(
        node_id=node_id,
        capabilities=node_capabilities,
        belief_state=node_belief
    )
    
    self.nodes[node_id] = node.dict()
    
    # Create registration glyph
    self.create_glyph(
        source_node=node_id,
        intent="swarm:registration",
        payload={
            "content": {
                "capabilities": capabilities,
                "belief_state": belief_state
            }
        }
    )

def detect_belief_contradictions(self, node_id: str) -> List[Dict[str, Any]]:
    """Detect contradictions between a node's beliefs and other nodes"""
    if node_id not in self.nodes:
        return []
        
    node = self.nodes[node_id]
    contradictions = []
    
    for other_id, other_node in self.nodes.items():
        if other_id == node_id:
            continue
            
        # Compare belief states
        node_beliefs = node["belief_state"]
        other_beliefs = other_node["belief_state"]
        
        for key in node_beliefs:
            if key in other_beliefs and node_beliefs[key] != other_beliefs[key]:
                contradictions.append({
                    "belief": key,
                    "node_value": node_beliefs[key],
                    "other_node": other_id,
                    "other_value": other_beliefs[key],
                    "severity": abs(float(node_beliefs[key]) - float(other_beliefs[key])) if isinstance(node_beliefs[key], (int, float)) and isinstance(other_beliefs[key], (int, float)) else 1.0
                })
    
    return contradictions
```

### Week 12-13: Memory Dynamics

#### Step 1: Create memory integration module

```bash
mkdir -p extensions/xhaak/memory
touch extensions/xhaak/memory/__init__.py
touch extensions/xhaak/memory/integration.py
```

#### Step 2: Implement memory integration

```python
# extensions/xhaak/memory/integration.py
from typing import Dict, Any, List, Optional
import os

# Import memory systems if API keys are available
cognee_client = None
cognee_api_key = os.environ.get("COGNEE_API_KEY")
if cognee_api_key:
    try:
        from cognee import CogneeClient, MemoryTypes, MemoryOptions
        cognee_client = CogneeClient(api_key=cognee_api_key)
    except ImportError:
        print("Cognee not installed, multimodal memory features will be disabled")

mem0_client = None
mem0_api_key = os.environ.get("MEM0_API_KEY")
if mem0_api_key:
    try:
        from mem0 import Mem0Client, MemoryLevel, MemoryOptions
        mem0_client = Mem0Client(api_key=mem0_api_key)
    except ImportError:
        print("Mem0 not installed, multi-level memory features will be disabled")

class MemoryIntegration:
    """Integration with multiple memory systems"""
    
    def __init__(self):
        self.cognee_client = cognee_client
        self.mem0_client = mem0_client
        
    async def store_memory(self, content: Dict[str, Any], metadata: Dict[str, Any], 
                          memory_type: str = "text", level: str = "working") -> Dict[str, Any]:
        """Store memory in available memory systems"""
        results = {}
        
        # Store in Cognee if available
        if self.cognee_client:
            cognee_memory_type = MemoryTypes.TEXT
            if memory_type == "image":
                cognee_memory_type = MemoryTypes.IMAGE
            elif memory_type == "audio":
                cognee_memory_type = MemoryTypes.AUDIO
            elif memory_type == "video":
                cognee_memory_type = MemoryTypes.VIDEO
                
            cognee_options = MemoryOptions(
                metadata=metadata,
                tags=metadata.get("tags", [])
            )
            
            cognee_id = await self.cognee_client.store(
                content=content,
                memory_type=cognee_memory_type,
                options=cognee_options
            )
            
            results["cognee_id"] = cognee_id
        
        # Store in Mem0 if available
        if self.mem0_client:
            mem0_level = MemoryLevel.WORKING
            if level == "short_term":
                mem0_level = MemoryLevel.SHORT_TERM
            elif level == "long_term":
                mem0_level = MemoryLevel.LONG_TERM
                
            mem0_options = MemoryOptions(
                metadata=metadata,
                tags=metadata.get("tags", [])
            )
            
            mem0_id = await self.mem0_client.store(
                content=str(content),
                level=mem0_level,
                options=mem0_options
            )
            
            results["mem0_id"] = mem0_id
        
        return results
    
    async def retrieve_memory(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                             level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve memory from available memory systems"""
        results = []
        
        # Retrieve from Cognee if available
        if self.cognee_client:
            cognee_results = await self.cognee_client.search(
                query=query,
                filters=filters,
                limit=10
            )
            
            for result in cognee_results:
                result["source"] = "cognee"
                results.append(result)
        
        # Retrieve from Mem0 if available
        if self.mem0_client:
            mem0_level = None
            if level == "working":
                mem0_level = MemoryLevel.WORKING
            elif level == "short_term":
                mem0_level = MemoryLevel.SHORT_TERM
            elif level == "long_term":
                mem0_level = MemoryLevel.LONG_TERM
                
            mem0_results = await self.mem0_client.search(
                query=query,
                level=mem0_level,
                filters=filters,
                limit=10
            )
            
            for result in mem0_results:
                result["source"] = "mem0"
                results.append(result)
        
        return results
```

### Week 14-15: Stigmergy Activation

#### Step 1: Create stigmergy module

```bash
mkdir -p extensions/xhaak/stigmergy
touch extensions/xhaak/stigmergy/__init__.py
touch extensions/xhaak/stigmergy/environment.py
```

#### Step 2: Implement stigmergy environment

```python
# extensions/xhaak/stigmergy/environment.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

class StigmergyEnvironment:
    """Environment for stigmergic coordination"""
    
    def __init__(self):
        self.signals = {}
        self.signal_strength_decay = 0.1  # Signal strength decays by 10% per time unit
        
    def place_signal(self, location: str, signal_type: str, strength: float, 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Place a signal in the environment"""
        signal_id = str(uuid4())
        
        self.signals[signal_id] = {
            "location": location,
            "signal_type": signal_type,
            "strength": strength,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        return signal_id
    
    def detect_signals(self, location: str, signal_type: Optional[str] = None, 
                      min_strength: float = 0.1) -> List[Dict[str, Any]]:
        """Detect signals at a location"""
        detected = []
        
        for signal_id, signal in self.signals.items():
            if signal["location"] == location and signal["strength"] >= min_strength:
                if signal_type is None or signal["signal_type"] == signal_type:
                    detected.append({
                        "signal_id": signal_id,
                        **signal
                    })
        
        return detected
    
    def update_signal_strength(self, signal_id: str, strength_delta: float) -> bool:
        """Update the strength of a signal"""
        if signal_id not in self.signals:
            return False
            
        self.signals[signal_id]["strength"] += strength_delta
        
        # Ensure strength is between 0 and 1
        self.signals[signal_id]["strength"] = max(0.0, min(1.0, self.signals[signal_id]["strength"]))
        
        return True
    
    def decay_signals(self) -> None:
        """Decay all signal strengths"""
        for signal_id in list(self.signals.keys()):
            self.signals[signal_id]["strength"] -= self.signal_strength_decay
            
            # Remove signals that have decayed below threshold
            if self.signals[signal_id]["strength"] <= 0:
                del self.signals[signal_id]
```

## Phase 3c: Glyphwave Resonance Build

### Week 16-17: Multi-node Collaboration

#### Step 1: Create collaboration module

```bash
mkdir -p extensions/xhaak/collaboration
touch extensions/xhaak/collaboration/__init__.py
touch extensions/xhaak/collaboration/task_distribution.py
```

#### Step 2: Implement task distribution

```python
# extensions/xhaak/collaboration/task_distribution.py
from typing import Dict, Any, List, Optional
from uuid import uuid4

class TaskDistributor:
    """Distributes tasks among nodes"""
    
    def __init__(self, gsp_extension):
        self.gsp = gsp_extension
        self.tasks = {}
        
    def create_task(self, name: str, description: str, requirements: Dict[str, Any]) -> str:
        """Create a new task"""
        task_id = str(uuid4())
        
        self.tasks[task_id] = {
            "name": name,
            "description": description,
            "requirements": requirements,
            "status": "created",
            "assigned_to": None,
            "result": None
        }
        
        return task_id
    
    def find_suitable_nodes(self, task_id: str) -> List[str]:
        """Find nodes suitable for a task"""
        if task_id not in self.tasks:
            return []
            
        task = self.tasks[task_id]
        requirements = task["requirements"]
        
        suitable_nodes = []
        
        for node_id, node in self.gsp.nodes.items():
            # Check if node has required capabilities
            if "capabilities" in requirements:
                node_capabilities = node["capabilities"]
                meets_requirements = True
                
                for capability, required in requirements["capabilities"].items():
                    if required and (capability not in node_capabilities or not node_capabilities[capability]):
                        meets_requirements = False
                        break
                
                if not meets_requirements:
                    continue
            
            suitable_nodes.append(node_id)
        
        return suitable_nodes
    
    def assign_task(self, task_id: str, node_id: str) -> bool:
        """Assign a task to a node"""
        if task_id not in self.tasks or node_id not in self.gsp.nodes:
            return False
            
        self.tasks[task_id]["status"] = "assigned"
        self.tasks[task_id]["assigned_to"] = node_id
        
        # Create task assignment glyph
        self.gsp.create_glyph(
            source_node="task_distributor",
            intent="task:assign",
            payload={
                "content": {
                    "task_id": task_id,
                    "task": self.tasks[task_id]
                }
            },
            resonance_type="directed"
        )
        
        return True
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed"""
        if task_id not in self.tasks:
            return False
            
        self.tasks[task_id]["status"] = "completed"
        self.tasks[task_id]["result"] = result
        
        return True
```

#### Step 3: Implement collaborative reasoning

```python
# extensions/xhaak/collaboration/collaborative_reasoning.py
from typing import Dict, Any, List, Optional
from uuid import uuid4

class CollaborativeReasoning:
    """Enables collaborative reasoning among nodes"""
    
    def __init__(self, scope_extension, gsp_extension):
        self.scope = scope_extension
        self.gsp = gsp_extension
        self.reasoning_sessions = {}
        
    def create_session(self, topic: str, initial_question: str) -> str:
        """Create a new collaborative reasoning session"""
        session_id = str(uuid4())
        
        # Create initial breathfold
        fold_id = self.scope.create_fold(initial_question)
        
        self.reasoning_sessions[session_id] = {
            "topic": topic,
            "initial_question": initial_question,
            "root_fold_id": fold_id,
            "participant_nodes": [],
            "status": "active"
        }
        
        # Create session announcement glyph
        self.gsp.create_glyph(
            source_node="collaborative_reasoning",
            intent="reasoning:session:created",
            payload={
                "content": {
                    "session_id": session_id,
                    "topic": topic,
                    "initial_question": initial_question
                }
            },
            resonance_type="broadcast"
        )
        
        return session_id
    
    def join_session(self, session_id: str, node_id: str) -> bool:
        """Join a collaborative reasoning session"""
        if session_id not in self.reasoning_sessions:
            return False
            
        if node_id not in self.reasoning_sessions[session_id]["participant_nodes"]:
            self.reasoning_sessions[session_id]["participant_nodes"].append(node_id)
            
            # Create join announcement glyph
            self.gsp.create_glyph(
                source_node=node_id,
                intent="reasoning:session:joined",
                payload={
                    "content": {
                        "session_id": session_id
                    }
                },
                resonance_type="broadcast"
            )
        
        return True
    
    def contribute_insight(self, session_id: str, node_id: str, insight: str) -> Optional[str]:
        """Contribute an insight to a reasoning session"""
        if session_id not in self.reasoning_sessions or self.reasoning_sessions[session_id]["status"] != "active":
            return None
            
        if node_id not in self.reasoning_sessions[session_id]["participant_nodes"]:
            return None
            
        # Create a child fold for the insight
        parent_fold_id = self.reasoning_sessions[session_id]["root_fold_id"]
        fold_id = self.scope.create_fold(insight, fold_type="3of2")
        
        # Create insight contribution glyph
        self.gsp.create_glyph(
            source_node=node_id,
            intent="reasoning:insight:contributed",
            payload={
                "content": {
                    "session_id": session_id,
                    "fold_id": fold_id,
                    "insight": insight
                }
            },
            resonance_type="broadcast"
        )
        
        return fold_id
    
    def synthesize_insights(self, session_id: str) -> Optional[str]:
        """Synthesize insights from a reasoning session"""
        if session_id not in self.reasoning_sessions:
            return None
            
        root_fold_id = self.reasoning_sessions[session_id]["root_fold_id"]
        resolution = self.scope.get_fold_resolution(root_fold_id)
        
        if resolution:
            self.reasoning_sessions[session_id]["status"] = "completed"
            
            # Create synthesis glyph
            self.gsp.create_glyph(
                source_node="collaborative_reasoning",
                intent="reasoning:session:synthesized",
                payload={
                    "content": {
                        "session_id": session_id,
                        "resolution": resolution
                    }
                },
                resonance_type="broadcast"
            )
        
        return resolution
```

### Week 18-20: System Integration

#### Step 1: Create CLI module

```bash
mkdir -p extensions/xhaak/cli
touch extensions/xhaak/cli/__init__.py
touch extensions/xhaak/cli/commands.py
```

#### Step 2: Implement CLI commands

```python
# extensions/xhaak/cli/commands.py
import click
import json
import sys
from localagi.cli import cli as localagi_cli

@localagi_cli.group()
def xhaak():
    """XHAAK commands for LocalAGI"""
    pass

@xhaak.command("list-agents")
def list_agents():
    """List all agents in the swarm"""
    from localagi.client import LocalAGIClient
    
    client = LocalAGIClient()
    agents = client.get_agents()
    
    click.echo(f"Found {len(agents)} agents in the swarm:")
    for agent in agents:
        click.echo(f"  - {agent['id']}: {agent['name']} ({agent['type']})")
        if "capabilities" in agent:
            click.echo(f"    Capabilities: {', '.join(agent['capabilities'])}")

@xhaak.command("glyphcast")
@click.argument("intent")
@click.option("--payload", help="JSON payload for the glyph")
def glyphcast(intent, payload=None):
    """Broadcast a glyph with specific intent"""
    from localagi.client import LocalAGIClient
    
    client = LocalAGIClient()
    
    payload_dict = None
    if payload:
        try:
            payload_dict = json.loads(payload)
        except json.JSONDecodeError:
            click.echo("Error: Payload must be valid JSON")
            sys.exit(1)
    
    result = client.call_extension("gsp_extension", "create_and_broadcast_glyph", {
        "source_node": "cli",
        "intent": intent,
        "payload": payload_dict,
        "resonance_type": "broadcast"
    })
    
    if result.get("success"):
        click.echo(f"Glyph broadcast successful. Glyph ID: {result.get('glyph_id')}")
        click.echo(f"Received by {len(result.get('received_by', []))} agents")
    else:
        click.echo(f"Error broadcasting glyph: {result.get('error')}")

# Implement remaining CLI commands as shown in the comprehensive guide
# ...
```

#### Step 3: Create browser commands

```python
# extensions/xhaak/cli/browser_commands.py
import click
import json
import sys
from localagi.cli import cli as localagi_cli
from .commands import xhaak

@xhaak.group("browser")
def browser():
    """Browser commands for XHAAK"""
    pass

@browser.command("ritual-create")
@click.argument("ritual_file", type=click.Path(exists=True))
def ritual_create(ritual_file):
    """Create a browser ritual from a JSON file"""
    from localagi.client import LocalAGIClient
    
    client = LocalAGIClient()
    
    # Load ritual from file
    with open(ritual_file, 'r') as f:
        ritual = json.load(f)
    
    # Call Browser Ritual Agent extension
    result = client.call_extension("browser_ritual_agent", "create_ritual", {
        "site_url": ritual.get("site_url", ""),
        "navigation_flow": ritual.get("navigation_flow", []),
        "target_actions": ritual.get("target_actions", []),
        "completion_conditions": ritual.get("completion_conditions", {}),
        "fallback_rituals": ritual.get("fallback_rituals")
    })
    
    if "ritual_id" in result:
        click.echo(f"Browser ritual created with ID: {result['ritual_id']}")
    else:
        click.echo(f"Error creating browser ritual: {result.get('error', 'Unknown error')}")

# Implement remaining browser commands as shown in the comprehensive guide
# ...
```

#### Step 4: Create integration tests

```python
# tests/xhaak/test_integration.py
import pytest
from extensions.xhaak.fmp.extension import FMPExtension
from extensions.xhaak.scope.extension import SCOPEExtension
from extensions.xhaak.gsp.extension import GSPExtension
from extensions.xhaak.browser.extension import BrowserRitualAgentExtension

def test_fmp_scope_integration():
    """Test integration between FMP and SCOPE"""
    fmp = FMPExtension()
    scope = SCOPEExtension()
    
    # Register a component
    component_id = fmp.register_component(
        name="BreathfoldProcessor",
        purpose="Process breathfolds",
        expected_outcomes=["Successful breathfold resolution"]
    )
    
    # Create an action
    action_id = fmp.create_action(
        component_id=component_id,
        action_type="breathfold_creation",
        description="Create a breathfold"
    )
    
    # Record clarity metrics
    fmp.record_clarity(
        action_id=action_id,
        metrics=[
            {
                "name": "content_clarity",
                "value": 0.8,
                "description": "Clarity of the breathfold content"
            }
        ]
    )
    
    # Create a breathfold
    fold_id = scope.create_fold("Test breathfold content")
    
    # Get the resolution
    resolution = scope.get_fold_resolution(fold_id)
    
    # Record outcome metrics
    fmp.record_outcome(
        action_id=action_id,
        metrics=[
            {
                "name": "resolution_quality",
                "value": 0.7,
                "description": "Quality of the breathfold resolution"
            }
        ],
        success=True
    )
    
    # Calculate CØD
    cod = fmp.calculate_cod(action_id)
    
    assert cod is not None
    assert 0.0 <= cod <= 1.0

# Add more integration tests for other component combinations
# ...
```

## Testing Strategy

### Unit Tests

Create unit tests for each component:

```bash
# Run unit tests for FMP
pytest tests/xhaak/test_fmp.py -v

# Run unit tests for SCOPE
pytest tests/xhaak/test_scope.py -v

# Run unit tests for GSP
pytest tests/xhaak/test_gsp.py -v

# Run unit tests for Browser Ritual Agent
pytest tests/xhaak/test_browser.py -v
```

### Integration Tests

Create integration tests for component interactions:

```bash
# Run integration tests
pytest tests/xhaak/test_integration.py -v
```

### System Tests

Create system tests for end-to-end functionality:

```bash
# Run system tests
pytest tests/xhaak/test_system.py -v
```

### Test Coverage

Monitor test coverage to ensure comprehensive testing:

```bash
# Generate test coverage report
pytest tests/xhaak --cov=extensions.xhaak --cov-report=html
```

## Deployment Process

### Local Deployment

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Register extensions
python scripts/xhaak/register_extensions.py

# 3. Start Redis
redis-server

# 4. Start LocalAGI with XHAAK extensions
python -m localagi.server --extensions-path=./extensions
```

### Docker Deployment

Create a Dockerfile:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Register extensions
RUN python scripts/xhaak/register_extensions.py

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "-m", "localagi.server", "--extensions-path=./extensions"]
```

Build and run the Docker container:

```bash
# Build Docker image
docker build -t xhaak-phase3 .

# Run Docker container
docker run -p 8000:8000 -d xhaak-phase3
```

### Production Deployment

For production deployment, use Docker Compose:

```yaml
# docker-compose.yml
version: '3'

services:
  redis:
    image: redis:6
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  xhaak:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - GRAPHITI_API_KEY=${GRAPHITI_API_KEY}
      - COGNEE_API_KEY=${COGNEE_API_KEY}
      - MEMARY_API_KEY=${MEMARY_API_KEY}
      - MEM0_API_KEY=${MEM0_API_KEY}
    depends_on:
      - redis

volumes:
  redis-data:
```

Deploy with Docker Compose:

```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Extension Loading Issues

**Issue**: Extensions not loading properly.

**Solution**:
```bash
# Check extension registration
python -c "from localagi.core import list_extensions; print(list_extensions())"

# Ensure extension path is correct
python -m localagi.server --extensions-path=./extensions --log-level=DEBUG
```

#### Redis Connection Issues

**Issue**: Cannot connect to Redis.

**Solution**:
```bash
# Check Redis status
redis-cli ping

# Ensure Redis URL is correct
export REDIS_URL=redis://localhost:6379/0
```

#### API Key Issues

**Issue**: External services not working due to API key issues.

**Solution**:
```bash
# Check if API keys are set
echo $GRAPHITI_API_KEY
echo $COGNEE_API_KEY
echo $MEMARY_API_KEY
echo $MEM0_API_KEY

# Set API keys if missing
export GRAPHITI_API_KEY=your_graphiti_api_key
export COGNEE_API_KEY=your_cognee_api_key
export MEMARY_API_KEY=your_memary_api_key
export MEM0_API_KEY=your_mem0_api_key
```

#### Browser Ritual Issues

**Issue**: Browser rituals failing.

**Solution**:
```bash
# Check browser-use installation
pip show browser-use

# Reinstall if needed
pip uninstall -y browser-use
pip install -e /path/to/browser-use

# Check browser ritual status
xhaakctl browser:ritual-status <ritual_id>
```

## Build Optimization Tips

### Performance Optimization

1. **Lazy Loading**: Implement lazy loading for external services to reduce startup time.

```python
class LazyServiceLoader:
    """Lazy loader for external services"""
    
    def __init__(self, service_name, api_key_env, service_class):
        self.service_name = service_name
        self.api_key_env = api_key_env
        self.service_class = service_class
        self._instance = None
    
    def get_instance(self):
        """Get service instance, initializing if necessary"""
        if self._instance is None:
            import os
            api_key = os.environ.get(self.api_key_env)
            if api_key:
                try:
                    self._instance = self.service_class(api_key=api_key)
                except ImportError:
                    print(f"{self.service_name} not installed, features will be disabled")
        
        return self._instance
```

2. **Caching**: Implement caching for frequently accessed data.

```python
class SimpleCache:
    """Simple in-memory cache"""
    
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, key, default=None):
        """Get value from cache"""
        return self.cache.get(key, default)
    
    def set(self, key, value):
        """Set value in cache"""
        # Evict oldest item if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = value
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
```

3. **Asynchronous Processing**: Use asynchronous processing for non-blocking operations.

```python
import asyncio

async def process_glyphs_async(glyphs, processor_func):
    """Process glyphs asynchronously"""
    tasks = []
    for glyph in glyphs:
        task = asyncio.create_task(processor_func(glyph))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### Memory Optimization

1. **Object Pooling**: Implement object pooling for frequently created objects.

```python
class GlyphPool:
    """Pool for glyph objects"""
    
    def __init__(self, max_size=100):
        self.pool = []
        self.max_size = max_size
    
    def get_glyph(self):
        """Get a glyph from the pool or create a new one"""
        if self.pool:
            return self.pool.pop()
        else:
            return {}
    
    def return_glyph(self, glyph):
        """Return a glyph to the pool"""
        if len(self.pool) < self.max_size:
            # Clear glyph data
            glyph.clear()
            self.pool.append(glyph)
```

2. **Memory Monitoring**: Implement memory monitoring to detect leaks.

```python
import psutil
import os

def monitor_memory_usage():
    """Monitor memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss": memory_info.rss / (1024 * 1024),  # RSS in MB
        "vms": memory_info.vms / (1024 * 1024)   # VMS in MB
    }
```

### Build Automation

1. **Continuous Integration**: Set up CI/CD pipeline for automated testing and deployment.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, xhaak-phase3 ]
  pull_request:
    branches: [ main, xhaak-phase3 ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/xhaak --cov=extensions.xhaak
```

2. **Build Script**: Create a comprehensive build script.

```bash
#!/bin/bash
# scripts/xhaak/build_all.sh

# Ensure we're in the project root
cd "$(dirname "$0")/../.."

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black isort mypy

# Format code
echo "Formatting code..."
black extensions/xhaak
isort extensions/xhaak

# Type checking
echo "Type checking..."
mypy extensions/xhaak

# Run tests
echo "Running tests..."
pytest tests/xhaak -v --cov=extensions.xhaak --cov-report=html

# Register extensions
echo "Registering extensions..."
python scripts/xhaak/register_extensions.py

# Build documentation
echo "Building documentation..."
mkdir -p docs/build
sphinx-build docs/source docs/build

echo "Build completed successfully!"
```

By following this build implementation guide, you'll be able to efficiently implement XHAAK Phase 3: Genesis Rebirth with a clear, step-by-step approach that ensures high-quality code, comprehensive testing, and smooth deployment.
