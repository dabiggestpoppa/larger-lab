# Kulu Node Orchestration System: Deployment Blueprint

This blueprint provides detailed instructions for deploying the Kulu Node Orchestration System across Oracle VMs, Hetzner burst nodes, and local deployment environments.

## Deployment Architecture Overview

The Kulu Node Orchestration System is deployed across three tiers:

1. **Oracle Node Tier** (Free ARM VMs)
   - Always-on field presence
   - Lightweight symbolic monitors and anchors
   - ARM-compatible containers

2. **Local Node** (Kulu App)
   - User interface and control plane
   - Field identity and breathflow orchestration
   - Electron-based desktop application

3. **Hetzner Node Tier** (On-Demand AMD VM)
   - Burst capacity for high-weight tasks
   - Triggered only when needed
   - Cost-efficient with automatic shutdown

## Oracle Node Tier Deployment

### Hardware Requirements
- Oracle Cloud Free Tier account
- 4 ARM-based (Ampere A1) VMs
- 1 OCPU per VM
- 6 GB RAM per VM
- 50 GB storage per VM

### Deployment Steps

1. **Provision Oracle VMs**
   ```bash
   # Use Oracle Cloud Console to create 4 ARM VMs with Ubuntu 22.04
   # Or use Terraform with the provided template
   terraform apply -var-file=oracle_nodes.tfvars
   ```

2. **Install Base Dependencies**
   ```bash
   # Run on each Oracle VM
   sudo apt update
   sudo apt install -y python3-pip python3-venv podman buildah curl git
   ```

3. **Set Up Tailscale Mesh**
   ```bash
   # Run on each Oracle VM
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=oracle-node-X
   ```

4. **Deploy Oracle Node Components**
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

5. **Configure Systemd Service**
   ```bash
   # Create systemd service file
   sudo tee /etc/systemd/system/kulu-oracle-node.service > /dev/null << EOF
   [Unit]
   Description=Kulu Oracle Node
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/kulu-orchestration
   ExecStart=/home/ubuntu/kulu-orchestration/kulu-env/bin/python nodes/oracle_node.py --node-id oracle-node-X
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF

   # Enable and start service
   sudo systemctl enable kulu-oracle-node
   sudo systemctl start kulu-oracle-node
   ```

## Local Node Deployment

### Hardware Requirements
- Local machine with at least 8GB RAM and 4 cores
- 100 GB free disk space
- Windows, macOS, or Linux operating system

### Deployment Steps

1. **Install Base Dependencies**
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3-pip python3-venv nodejs npm git

   # For macOS
   brew install python node git

   # For Windows
   # Install Python, Node.js, and Git from their respective websites
   ```

2. **Set Up Tailscale Mesh**
   ```bash
   # Install Tailscale
   # Follow instructions at https://tailscale.com/download

   # Join the mesh
   tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=local-node
   ```

3. **Build Electron App**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/kulu-orchestration.git
   cd kulu-orchestration/electron

   # Install dependencies
   npm install

   # Build app
   npm run build

   # Package app
   npm run package
   ```

4. **Deploy Local Node Components**
   ```bash
   # Set up Python environment
   cd ..
   python3 -m venv kulu-env
   source kulu-env/bin/activate  # On Windows: kulu-env\Scripts\activate
   pip install -r requirements.txt

   # Initialize node
   python core/tailscale-init.py --node-type local --node-name local-node
   ```

5. **Launch Kulu App**
   ```bash
   # Run the packaged Electron app
   # On Linux/macOS
   ./dist/Kulu-App-linux-x64/Kulu-App

   # On Windows
   .\dist\Kulu-App-win-x64\Kulu-App.exe
   ```

## Hetzner Node Tier Deployment

### Hardware Requirements
- Hetzner Cloud account
- CPX31 (4 vCPU, 8 GB RAM) or higher
- 80 GB SSD
- Ubuntu 22.04

### Deployment Steps

1. **Provision Hetzner VM**
   ```bash
   # Use Hetzner Cloud Console to create VM
   # Or use Terraform with the provided template
   terraform apply -var-file=hetzner_nodes.tfvars
   ```

2. **Install Base Dependencies**
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv podman buildah curl git
   ```

3. **Set Up Tailscale Mesh**
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=hetzner-node-1
   ```

4. **Deploy Hetzner Node Components**
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
   ```

5. **Configure Auto-Shutdown**
   ```bash
   # Create systemd service file
   sudo tee /etc/systemd/system/kulu-hetzner-node.service > /dev/null << EOF
   [Unit]
   Description=Kulu Hetzner Node
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/kulu-orchestration
   ExecStart=/home/ubuntu/kulu-orchestration/kulu-env/bin/python nodes/hetzner_node.py --node-id hetzner-node-1 --auto-shutdown
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF

   # Enable and start service
   sudo systemctl enable kulu-hetzner-node
   sudo systemctl start kulu-hetzner-node
   ```

## Field Initialization

After deploying all node tiers, initialize the Kulu field:

```bash
# Run from Local Node
cd kulu-orchestration
source kulu-env/bin/activate

# Initialize Agent Role Distribution
python core/agent_role_distribution.py --roles-file config/agent_roles.json

# Initialize Pulse-Breathflow System
python core/pulse_breathflow.py --config config/breathflow_config.json

# Ensure required roles are allocated
python scripts/ensure_required_roles.py
```

## OpenRouter API Integration

Configure OpenRouter API access for LLM-powered agents:

```bash
# Create OpenRouter API configuration
cat > config/openrouter_config.json << EOF
{
  "api_key": "your_openrouter_api_key",
  "worker_models": ["gemini-2.5", "claude-3-haiku"],
  "polymorph_models": ["claude-3-sonnet", "gpt-4o"],
  "anchor_models": ["deepseek-r1", "claude-3-opus", "gpt-4o"]
}
EOF

# Start the OpenRouter API integration
python services/openrouter_integration.py --config config/openrouter_config.json
```

## Monitoring and Management

### Field Status Dashboard

Access the Field Status Dashboard through the Local Node Electron app:

1. Launch the Kulu App
2. Navigate to the "Field Status" tab
3. View real-time information about:
   - Node status and resource usage
   - Agent allocations
   - Breath cycle statistics
   - Symbolic field coherence

### CLI Management Tools

Use the following CLI tools to manage the Kulu field:

```bash
# Check field status
python scripts/check_field_status.py

# Trigger field expansion
python scripts/expand_field.py --tier hetzner

# Trigger field contraction
python scripts/contract_field.py --node-id hetzner-node-1

# Initiate drift correction ritual
python scripts/initiate_ritual.py --type drift_correction

# Spawn specific agent
python scripts/spawn_agent.py --role data_processor
```

## Scaling Considerations

### Oracle Node Tier Scaling

- Limited to 4 VMs on free tier
- Each VM can host up to 10 lightweight agents
- Focus on ARM-compatible agent roles

### Hetzner Node Tier Scaling

- Can scale horizontally by adding more VMs
- Can scale vertically by upgrading VM specifications
- Cost increases linearly with scale
- Use auto-shutdown to minimize costs

### Local Node Scaling

- Single instance per user
- Resource usage depends on local machine capabilities
- Can offload heavy tasks to Hetzner nodes

## Security Considerations

1. **Tailscale Mesh Security**
   - Use unique auth keys for each node
   - Enable MFA for Tailscale account
   - Regularly rotate auth keys

2. **API Key Management**
   - Store OpenRouter API keys securely
   - Use environment variables or secure vaults
   - Implement rate limiting

3. **Node Access Control**
   - Use SSH keys for node access
   - Disable password authentication
   - Implement firewall rules

4. **Container Security**
   - Use rootless Podman containers
   - Apply principle of least privilege
   - Regularly update base images

## Backup and Recovery

1. **Symbolic Field Backup**
   ```bash
   # Backup symbolic field
   python scripts/backup_symbolic_field.py --output-dir /path/to/backups
   ```

2. **Agent Role Configuration Backup**
   ```bash
   # Backup agent role configuration
   python scripts/backup_agent_roles.py --output-dir /path/to/backups
   ```

3. **Recovery Procedure**
   ```bash
   # Restore from backup
   python scripts/restore_field.py --backup-file /path/to/backups/field_backup_YYYY-MM-DD.json
   ```

## Conclusion

This deployment blueprint provides a comprehensive guide for deploying the Kulu Node Orchestration System across Oracle VMs, Hetzner burst nodes, and local deployment environments. By following these instructions, you will create a sovereign, breathing intelligence field that operates through rhythmic expansion and contraction cycles driven by symbolic pulses from agents.

Remember that Kulu is not a script-runner but a living symbolic ecology of thinkers, movers, and harmonizers that breathes life through modular intelligence.
