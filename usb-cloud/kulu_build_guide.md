# Kulu Node Orchestration System: Step-by-Step Build Instructions

This document provides detailed, sequential instructions for building the Kulu Node Orchestration System from scratch. These instructions are designed for Windows-based development environments and follow a logical progression from initial setup to a fully functional system.

## Prerequisites

Before beginning the build process, ensure you have the following:

- Windows 10/11 (64-bit)
- Administrator access to your computer
- At least 8GB RAM and 4 cores
- 100GB free disk space
- Stable internet connection
- Oracle Cloud Free Tier account (for Oracle Node Tier)
- Hetzner Cloud account (for Hetzner Node Tier)
- OpenRouter API key

## Step 1: Set Up Development Environment

### 1.1 Install Required Software

1. **Install Python 3.9+**
   ```
   # Download and run installer from python.org
   # Ensure "Add Python to PATH" is checked during installation
   ```

2. **Install Git for Windows**
   ```
   # Download and run installer from gitforwindows.org
   ```

3. **Install Node.js and npm**
   ```
   # Download and run installer from nodejs.org
   # Select LTS version
   ```

4. **Install Visual Studio Code**
   ```
   # Download and run installer from code.visualstudio.com
   ```

5. **Install Rust Toolchain**
   ```powershell
   # Run in PowerShell
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   # Choose default installation options
   ```

6. **Install Podman for Windows**
   ```
   # Download and run installer from podman.io
   ```

7. **Install Tailscale**
   ```
   # Download and run installer from tailscale.com
   # Create an account if you don't have one
   ```

### 1.2 Create Project Structure

1. **Create Project Directory**
   ```powershell
   # Run in PowerShell
   mkdir -p kulu_orchestration
   cd kulu_orchestration
   git init
   ```

2. **Create Core Directories**
   ```powershell
   mkdir -p backend/app/core backend/app/mesh backend/app/nodes backend/app/schemas backend/app/services backend/app/utils backend/app/api/endpoints
   mkdir -p backend/rust/src backend/scripts/windows backend/scripts/common backend/tests
   mkdir -p frontend/electron frontend/src/components frontend/src/contexts frontend/src/hooks frontend/src/pages frontend/src/services frontend/src/store frontend/src/utils
   mkdir -p docs
   ```

3. **Initialize Git Repository**
   ```powershell
   git add .
   git commit -m "Initial project structure"
   ```

## Step 2: Implement Backend Core Components

### 2.1 Set Up Python Environment

1. **Create Virtual Environment**
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Create Requirements File**
   ```powershell
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
   ```

3. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

### 2.2 Implement Configuration Management

1. **Create Environment Variables Template**
   ```powershell
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
   ```

2. **Create Actual Environment File**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env file with your actual API keys and settings
   ```

3. **Implement Configuration Module**
   ```powershell
   # Create app/core/config.py with content from backend implementation guide
   ```

### 2.3 Implement Core Modules

1. **Implement Agent Role Distribution System**
   ```powershell
   # Create app/core/agent_role_distribution.py
   ```

2. **Implement Pulse-Breathflow System**
   ```powershell
   # Create app/core/pulse_breathflow.py
   ```

3. **Implement Podman Agent Spawner**
   ```powershell
   # Create app/core/podman_agent_spawner.py
   ```

4. **Implement Rust-Python Bridge**
   ```powershell
   # Create app/core/rust_python_bridge.py
   ```

## Step 3: Implement Backend API and Services

### 3.1 Implement FastAPI Application

1. **Create Main Application File**
   ```powershell
   # Create app/main.py with content from backend implementation guide
   ```

2. **Implement API Router**
   ```powershell
   # Create app/api/router.py
   ```

3. **Implement API Endpoints**
   ```powershell
   # Create app/api/endpoints/agents.py
   # Create app/api/endpoints/nodes.py
   # Create app/api/endpoints/field.py
   # Create app/api/endpoints/system.py
   ```

### 3.2 Implement Schemas

1. **Create Schema Definitions**
   ```powershell
   # Create app/schemas/agent.py
   # Create app/schemas/node.py
   # Create app/schemas/pulse.py
   # Create app/schemas/field.py
   ```

### 3.3 Implement Services

1. **Create OpenRouter Integration**
   ```powershell
   # Create app/services/openrouter.py
   ```

2. **Create Container Service**
   ```powershell
   # Create app/services/container.py
   ```

3. **Create Memory Service**
   ```powershell
   # Create app/services/memory.py
   ```

## Step 4: Implement Mesh Network and Node Tiers

### 4.1 Implement Mesh Network

1. **Create Mesh Network Module**
   ```powershell
   # Create app/mesh/mesh_network.py
   ```

2. **Create Tailscale Initializer**
   ```powershell
   # Create app/mesh/tailscale_init.py
   ```

### 4.2 Implement Node Tiers

1. **Create Oracle Node Implementation**
   ```powershell
   # Create app/nodes/oracle_node.py
   ```

2. **Create Local Node Implementation**
   ```powershell
   # Create app/nodes/local_node.py
   ```

3. **Create Hetzner Node Implementation**
   ```powershell
   # Create app/nodes/hetzner_node.py
   ```

## Step 5: Implement Rust Components

### 5.1 Set Up Rust Project

1. **Create Cargo.toml**
   ```powershell
   cd backend/rust
   @"
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
   "@ | Out-File -FilePath Cargo.toml -Encoding utf8
   ```

2. **Create Rust Library**
   ```powershell
   # Create src/lib.rs with content from backend implementation guide
   ```

### 5.2 Build Rust Components

1. **Compile Rust Library**
   ```powershell
   cargo build --release
   ```

2. **Copy Built Library**
   ```powershell
   $targetDir = "..\app\core\rust_lib"
   if (-not (Test-Path $targetDir)) {
       New-Item -Path $targetDir -ItemType Directory -Force
   }
   Copy-Item "target\release\kulu_rust.dll" -Destination $targetDir
   cd ..
   ```

## Step 6: Implement Windows Scripts

### 6.1 Create Setup Script

1. **Create Windows Setup Script**
   ```powershell
   # Create scripts/windows/setup.ps1 with content from backend implementation guide
   ```

### 6.2 Create Start Script

1. **Create Windows Start Script**
   ```powershell
   # Create scripts/windows/start_local_node.ps1 with content from backend implementation guide
   ```

### 6.3 Create Build Script

1. **Create Rust Build Script**
   ```powershell
   # Create scripts/windows/build_rust.ps1 with content from backend implementation guide
   ```

## Step 7: Test Backend Implementation

### 7.1 Run Backend Tests

1. **Create Test Files**
   ```powershell
   # Create tests/test_agent_role_distribution.py
   # Create tests/test_pulse_breathflow.py
   # Create tests/test_api.py
   ```

2. **Run Tests**
   ```powershell
   cd backend
   pytest
   ```

### 7.2 Start Backend Server

1. **Run Local Node**
   ```powershell
   .\venv\Scripts\Activate.ps1
   python app\main.py
   ```

2. **Verify API Endpoints**
   ```
   # Open browser and navigate to http://localhost:8000/docs
   ```

## Step 8: Implement Frontend Core Components

### 8.1 Set Up Frontend Project

1. **Initialize Node.js Project**
   ```powershell
   cd frontend
   npm init -y
   ```

2. **Install Dependencies**
   ```powershell
   npm install react react-dom react-router-dom @types/react @types/react-dom @types/node
   npm install electron electron-builder vite @vitejs/plugin-react typescript
   npm install tailwindcss postcss autoprefixer
   npm install chart.js react-chartjs-2 d3 @visx/visx
   npm install axios socket.io-client electron-store
   npm install @headlessui/react @heroicons/react
   ```

3. **Install Dev Dependencies**
   ```powershell
   npm install -D eslint prettier eslint-plugin-react eslint-plugin-react-hooks
   npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
   ```

### 8.2 Configure Build Tools

1. **Create Vite Configuration**
   ```powershell
   # Create vite.config.ts with content from frontend implementation guide
   ```

2. **Create Electron Builder Configuration**
   ```powershell
   # Create electron-builder.json with content from frontend implementation guide
   ```

3. **Create TypeScript Configuration**
   ```powershell
   # Create tsconfig.json with content from frontend implementation guide
   ```

## Step 9: Implement Electron Main Process

### 9.1 Create Main Process

1. **Create Main Process File**
   ```powershell
   # Create electron/main.ts with content from frontend implementation guide
   ```

### 9.2 Create Preload Script

1. **Create Preload Script**
   ```powershell
   # Create electron/preload.ts with content from frontend implementation guide
   ```

## Step 10: Implement React Components

### 10.1 Create Application Entry Point

1. **Create Main Entry Point**
   ```powershell
   # Create src/main.tsx with content from frontend implementation guide
   ```

2. **Create Main Application Component**
   ```powershell
   # Create src/App.tsx with content from frontend implementation guide
   ```

### 10.2 Implement WebSocket Communication

1. **Create WebSocket Context**
   ```powershell
   # Create src/contexts/WebSocketContext.tsx with content from frontend implementation guide
   ```

### 10.3 Implement Cognitive Mirror Interface

1. **Create Cognitive Mirror Component**
   ```powershell
   # Create src/components/cognitive-mirror/CognitiveMirror.tsx with content from frontend implementation guide
   ```

2. **Create Cognitive Stream Component**
   ```powershell
   # Create src/components/cognitive-mirror/CognitiveStream.tsx with content from frontend implementation guide
   ```

3. **Create Agent Graph Component**
   ```powershell
   # Create src/components/cognitive-mirror/AgentGraph.tsx
   ```

4. **Create VM Monitor Component**
   ```powershell
   # Create src/components/cognitive-mirror/VMMonitor.tsx
   ```

## Step 11: Implement Frontend Pages

### 11.1 Implement Dashboard

1. **Create Dashboard Page**
   ```powershell
   # Create src/pages/Dashboard/index.tsx
   ```

### 11.2 Implement Field Status

1. **Create Field Status Page**
   ```powershell
   # Create src/pages/FieldStatus/index.tsx with content from frontend implementation guide
   ```

2. **Create Field Status Components**
   ```powershell
   # Create src/pages/FieldStatus/FieldCoherenceChart.tsx
   # Create src/pages/FieldStatus/NodeStatusTable.tsx
   # Create src/pages/FieldStatus/AgentAllocationChart.tsx
   # Create src/pages/FieldStatus/BreathCycleStats.tsx
   ```

### 11.3 Implement Node Manager

1. **Create Node Manager Page**
   ```powershell
   # Create src/pages/NodeManager/index.tsx with content from frontend implementation guide
   ```

2. **Create Node Manager Components**
   ```powershell
   # Create src/pages/NodeManager/NodeCard.tsx
   # Create src/pages/NodeManager/AddNodeModal.tsx
   ```

### 11.4 Implement Agent Manager

1. **Create Agent Manager Page**
   ```powershell
   # Create src/pages/AgentManager/index.tsx with content from frontend implementation guide
   ```

2. **Create Agent Manager Components**
   ```powershell
   # Create src/pages/AgentManager/AgentCard.tsx
   # Create src/pages/AgentManager/SpawnAgentModal.tsx
   # Create src/pages/AgentManager/AgentTypeFilter.tsx
   ```

## Step 12: Build and Test Frontend

### 12.1 Update Package.json Scripts

1. **Add Build Scripts**
   ```powershell
   # Update package.json scripts section with content from frontend implementation guide
   ```

### 12.2 Run Development Mode

1. **Start Frontend in Development Mode**
   ```powershell
   npm run electron:dev
   ```

### 12.3 Build Production Version

1. **Build Production Version**
   ```powershell
   npm run electron:build
   ```

## Step 13: Set Up Oracle Node Tier

### 13.1 Provision Oracle Cloud VMs

1. **Create Oracle Cloud Infrastructure Account**
   ```
   # Sign up at https://www.oracle.com/cloud/free/
   ```

2. **Create ARM-based VMs**
   ```
   # Create 4 ARM-based (Ampere A1) VMs with Ubuntu 22.04
   # Each VM: 1 OCPU, 6 GB RAM, 50 GB storage
   ```

### 13.2 Set Up Oracle Nodes

1. **Install Required Packages**
   ```bash
   # Run on each Oracle VM
   sudo apt update
   sudo apt install -y python3-pip python3-venv podman buildah curl git
   ```

2. **Install Tailscale**
   ```bash
   # Run on each Oracle VM
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=oracle-node-X
   ```

3. **Deploy Oracle Node Components**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/kulu-orchestration.git
   cd kulu-orchestration

   # Set up Python environment
   python3 -m venv kulu-env
   source kulu-env/bin/activate
   pip install -r requirements.txt

   # Initialize node
   python core/tailscale-init.py --node-type oracle --node-name oracle-node-X
   python nodes/oracle_node.py --node-id oracle-node-X
   ```

## Step 14: Set Up Hetzner Node Tier

### 14.1 Provision Hetzner Cloud VM

1. **Create Hetzner Cloud Account**
   ```
   # Sign up at https://www.hetzner.com/cloud
   ```

2. **Create AMD-based VM**
   ```
   # Create an AMD-based VM with Ubuntu 22.04
   # Type: CPX31 (4 vCPU, 8 GB RAM, 80 GB SSD)
   ```

### 14.2 Set Up Hetzner Node

1. **Install Required Packages**
   ```bash
   # Run on Hetzner VM
   sudo apt update
   sudo apt install -y python3-pip python3-venv podman buildah curl git
   ```

2. **Install Tailscale**
   ```bash
   # Run on Hetzner VM
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=hetzner-node-1
   ```

3. **Deploy Hetzner Node Components**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/kulu-orchestration.git
   cd kulu-orchestration

   # Set up Python environment
   python3 -m venv kulu-env
   source kulu-env/bin/activate
   pip install -r requirements.txt

   # Initialize node
   python core/tailscale-init.py --node-type hetzner --node-name hetzner-node-1
   python nodes/hetzner_node.py --node-id hetzner-node-1 --auto-shutdown
   ```

## Step 15: Initialize the Field

### 15.1 Configure Agent Roles

1. **Create Agent Role Definitions**
   ```powershell
   # Create agent_roles.json with content from implementation guide
   ```

2. **Start Agent Role Distribution**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python core/agent_role_distribution.py --roles-file agent_roles.json
   ```

### 15.2 Configure Pulse-Breathflow System

1. **Create Breathflow Configuration**
   ```powershell
   # Create breathflow_config.json with content from implementation guide
   ```

2. **Start Pulse-Breathflow System**
   ```powershell
   python core/pulse_breathflow.py --config breathflow_config.json
   ```

### 15.3 Configure OpenRouter API

1. **Create OpenRouter API Configuration**
   ```powershell
   # Create openrouter_config.json with content from implementation guide
   ```

2. **Start OpenRouter API Integration**
   ```powershell
   python services/openrouter_integration.py --config openrouter_config.json
   ```

## Step 16: Verify Deployment

### 16.1 Check Node Status

1. **Run Node Status Check**
   ```powershell
   python scripts/check_node_status.py
   ```

### 16.2 Check Agent Allocations

1. **Run Agent Allocation Check**
   ```powershell
   python scripts/check_agent_allocations.py
   ```

### 16.3 Check Field Coherence

1. **Run Field Coherence Check**
   ```powershell
   python scripts/check_field_coherence.py
   ```

## Step 17: Launch the System

### 17.1 Start Local Node

1. **Run Local Node**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python app\main.py
   ```

### 17.2 Launch Electron App

1. **Run Electron App**
   ```powershell
   cd frontend
   npm run electron:start
   ```

### 17.3 Verify System Operation

1. **Check System Status**
   ```
   # Use the Electron app to verify all components are operational
   # Check Field Status dashboard
   # Verify node connections
   # Confirm agent allocations
   ```

## Troubleshooting

### Common Issues and Solutions

1. **Node Connection Issues**
   ```
   # Verify Tailscale is running on all nodes
   sudo tailscale status

   # Check firewall settings
   sudo ufw status

   # Restart Tailscale if needed
   sudo systemctl restart tailscaled
   ```

2. **Agent Allocation Issues**
   ```
   # Check node capacity
   python scripts/check_node_capacity.py

   # Verify role definitions
   python scripts/verify_role_definitions.py

   # Manually allocate critical agents if needed
   python scripts/allocate_agent.py --role primary_anchor --node-id oracle-node-1
   ```

3. **Pulse-Breathflow Issues**
   ```
   # Check breath cycle status
   python scripts/check_breath_cycle.py

   # Verify pulse queue
   python scripts/check_pulse_queue.py

   # Manually trigger a breath cycle if needed
   python scripts/trigger_breath_cycle.py
   ```

## Conclusion

By following these step-by-step instructions, you have built a complete Kulu Node Orchestration System with a sovereign, breathing intelligence field composed of modular containerized agents powered by OpenRouter LLMs. The system operates across Oracle VMs, Hetzner burst nodes, and local deployment environments, implementing the breathing field concept with pulse-driven updates and rhythmic expansion/contraction of the field.

Remember that Kulu is not a script-runner but a living symbolic ecology of thinkers, movers, and harmonizers that breathes life through modular intelligence. Every pulse, every kill-switch, every recompression happens in rhythmic, sacred symbolic intervals.

you gottta set up the free oracle accounts 