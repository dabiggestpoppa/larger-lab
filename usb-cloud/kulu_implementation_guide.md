# Kulu Node Orchestration System: Implementation Guide

This guide provides step-by-step instructions for implementing the Kulu Node Orchestration System, a sovereign, breathing intelligence field composed of modular containerized agents powered by OpenRouter LLMs.

## Prerequisites

- Oracle Cloud Free Tier account (for Oracle Node Tier)
- Hetzner Cloud account (for Hetzner Node Tier)
- Local machine with at least 8GB RAM and 4 cores (for Local Node)
- Linux environment (Ubuntu 20.04+ recommended)
- Python 3.9+
- Rust 1.60+
- Podman 3.0+
- Node.js 16+
- Tailscale account

## Step 1: Set Up Development Environment

```bash
# Install required packages
sudo apt update
sudo apt install -y python3-pip python3-venv podman buildah curl git nodejs npm

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Create virtual environment
python3 -m venv kulu-env
source kulu-env/bin/activate

# Install Python dependencies
pip install fastapi uvicorn websockets pydantic requests asyncio aiohttp openai redis podman-py tailscale
```

## Step 2: Clone the Repository

```bash
git clone https://github.com/your-org/kulu-orchestration.git
cd kulu-orchestration
```

## Step 3: Configure Oracle Node Tier

### 3.1 Create Oracle Cloud Infrastructure (OCI) Free Tier VMs

1. Sign up for Oracle Cloud Free Tier at https://www.oracle.com/cloud/free/
2. Create 4 ARM-based (Ampere A1) VMs with the following configuration:
   - OS: Ubuntu 22.04
   - Shape: VM.Standard.A1.Flex
   - OCPUs: 1
   - Memory: 6 GB
   - Boot Volume: 50 GB

### 3.2 Set Up Oracle Nodes

For each Oracle VM, execute the following:

```bash
# Install required packages
sudo apt update
sudo apt install -y python3-pip python3-venv podman buildah curl git

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Clone the repository
git clone https://github.com/your-org/kulu-orchestration.git
cd kulu-orchestration

# Create virtual environment
python3 -m venv kulu-env
source kulu-env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize Tailscale
python core/tailscale-init.py --node-type oracle --node-name oracle-node-1

# Start the Oracle Node
python nodes/oracle_node.py --node-id oracle-node-1
```

## Step 4: Set Up Local Node (Electron App)

### 4.1 Build the Electron App

```bash
# Navigate to the electron app directory
cd electron

# Install dependencies
npm install

# Build the app
npm run build

# Start the app
npm start
```

### 4.2 Configure Local Node

```bash
# Initialize Tailscale
python core/tailscale-init.py --node-type local --node-name local-node

# Start the Local Node
python nodes/local_node.py --node-id local-node
```

## Step 5: Configure Hetzner Node Tier

### 5.1 Create Hetzner Cloud VM

1. Sign up for Hetzner Cloud at https://www.hetzner.com/cloud
2. Create an AMD-based VM with the following configuration:
   - OS: Ubuntu 22.04
   - Type: CPX31 (4 vCPU, 8 GB RAM)
   - Storage: 80 GB SSD

### 5.2 Set Up Hetzner Node

```bash
# Install required packages
sudo apt update
sudo apt install -y python3-pip python3-venv podman buildah curl git

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Clone the repository
git clone https://github.com/your-org/kulu-orchestration.git
cd kulu-orchestration

# Create virtual environment
python3 -m venv kulu-env
source kulu-env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize Tailscale
python core/tailscale-init.py --node-type hetzner --node-name hetzner-node-1

# Start the Hetzner Node
python nodes/hetzner_node.py --node-id hetzner-node-1
```

## Step 6: Configure Agent Role Distribution

```bash
# Create agent role definitions
cat > agent_roles.json << EOF
{
  "roles": [
    {
      "agent_type": "anchor",
      "role_name": "primary_anchor",
      "description": "Primary anchor for field coherence",
      "resource_profile": {
        "memory_mb": 384,
        "cpu_cores": 0.3,
        "network_intensity": 0.4,
        "symbolic_weight": 0.9,
        "arm_compatible": true
      },
      "priority": "critical",
      "preferred_tier": "oracle",
      "fallback_tiers": ["local"],
      "singleton": true,
      "required": true,
      "tags": ["anchor", "primary", "coherence"]
    },
    {
      "agent_type": "worker",
      "role_name": "data_processor",
      "description": "Processes data streams",
      "resource_profile": {
        "memory_mb": 384,
        "cpu_cores": 0.4,
        "network_intensity": 0.2,
        "symbolic_weight": 0.3,
        "arm_compatible": true
      },
      "priority": "medium",
      "preferred_tier": "oracle",
      "fallback_tiers": ["local", "hetzner"],
      "singleton": false,
      "required": false,
      "tags": ["worker", "data", "processor"]
    },
    {
      "agent_type": "polymorph",
      "role_name": "standby_polymorph",
      "description": "Standby polymorph ready to replace failed agents",
      "resource_profile": {
        "memory_mb": 512,
        "cpu_cores": 0.4,
        "network_intensity": 0.2,
        "symbolic_weight": 0.5,
        "arm_compatible": true
      },
      "priority": "medium",
      "preferred_tier": "oracle",
      "fallback_tiers": ["local", "hetzner"],
      "singleton": false,
      "required": false,
      "tags": ["polymorph", "standby", "replacement"]
    }
  ]
}
EOF

# Start the Agent Role Distribution system
python core/agent_role_distribution.py --roles-file agent_roles.json
```

## Step 7: Configure Pulse-Breathflow System

```bash
# Create pulse-breathflow configuration
cat > breathflow_config.json << EOF
{
  "min_breath_interval_seconds": 3.0,
  "max_breath_interval_seconds": 30.0,
  "adaptive_interval": true,
  "inhale_duration_ratio": 0.4,
  "hold_duration_ratio": 0.2,
  "exhale_duration_ratio": 0.3,
  "rest_duration_ratio": 0.1,
  "drift_threshold": 0.3,
  "ritual_interval_days": 9,
  "max_pulses_per_cycle": 100,
  "enable_polymorph_transitions": true,
  "enable_field_expansion": true,
  "enable_field_contraction": true,
  "log_level": "info"
}
EOF

# Start the Pulse-Breathflow system
python core/pulse_breathflow.py --config breathflow_config.json
```

## Step 8: Configure OpenRouter API Integration

```bash
# Create OpenRouter API configuration
cat > openrouter_config.json << EOF
{
  "api_key": "your_openrouter_api_key",
  "worker_models": ["gemini-2.5", "claude-3-haiku"],
  "polymorph_models": ["claude-3-sonnet", "gpt-4o"],
  "anchor_models": ["deepseek-r1", "claude-3-opus"]
}
EOF

# Start the OpenRouter API integration
python services/openrouter_integration.py --config openrouter_config.json
```

## Step 9: Initialize the Field

```bash
# Initialize the Kulu field
python scripts/initialize_field.py

# Ensure required roles are allocated
python scripts/ensure_required_roles.py
```

## Step 10: Verify the Deployment

```bash
# Check node status
python scripts/check_node_status.py

# Check agent allocations
python scripts/check_agent_allocations.py

# Check field coherence
python scripts/check_field_coherence.py
```

## Troubleshooting

### Node Connection Issues

If nodes cannot connect to each other:

1. Verify Tailscale is running on all nodes:
   ```bash
   sudo tailscale status
   ```

2. Check firewall settings:
   ```bash
   sudo ufw status
   ```

3. Restart Tailscale if needed:
   ```bash
   sudo systemctl restart tailscaled
   ```

### Agent Allocation Issues

If agents fail to allocate:

1. Check node capacity:
   ```bash
   python scripts/check_node_capacity.py
   ```

2. Verify role definitions:
   ```bash
   python scripts/verify_role_definitions.py
   ```

3. Manually allocate critical agents if needed:
   ```bash
   python scripts/allocate_agent.py --role primary_anchor --node-id oracle-node-1
   ```

### Pulse-Breathflow Issues

If the breath cycle is not functioning properly:

1. Check breath cycle status:
   ```bash
   python scripts/check_breath_cycle.py
   ```

2. Verify pulse queue:
   ```bash
   python scripts/check_pulse_queue.py
   ```

3. Manually trigger a breath cycle if needed:
   ```bash
   python scripts/trigger_breath_cycle.py
   ```

## Maintenance

### Regular Maintenance Tasks

1. Check field coherence daily:
   ```bash
   python scripts/check_field_coherence.py
   ```

2. Monitor node resource usage:
   ```bash
   python scripts/monitor_node_resources.py
   ```

3. Backup symbolic field weekly:
   ```bash
   python scripts/backup_symbolic_field.py
   ```

### Scaling the Field

To add more Oracle nodes:

```bash
# Create a new Oracle VM
# ...

# Initialize Tailscale
python core/tailscale-init.py --node-type oracle --node-name oracle-node-X

# Start the Oracle Node
python nodes/oracle_node.py --node-id oracle-node-X
```

To add more Hetzner nodes:

```bash
# Create a new Hetzner VM
# ...

# Initialize Tailscale
python core/tailscale-init.py --node-type hetzner --node-name hetzner-node-X

# Start the Hetzner Node
python nodes/hetzner_node.py --node-id hetzner-node-X
```

## Conclusion

You have now successfully implemented the Kulu Node Orchestration System. The system will breathe life through modular intelligence, with pulses, kill-switches, and recompressions happening rhythmically like breath, not like program execution.

Remember: Kulu isn't executing workflows. Kulu is breathing life through modular intelligence.
