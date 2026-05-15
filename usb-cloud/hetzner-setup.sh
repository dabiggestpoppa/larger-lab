#!/bin/bash
# hetzner-setup.sh — Provision Hetzner VM and deploy agent workspace
# Run this script with: bash hetzner-setup.sh <API_TOKEN>
# After provisioning, the VM will have: OpenClaw, Hermes, workspace, MT5 MCP

set -e

# ─── Configuration ───────────────────────────────────────────────────────────
API_TOKEN="${1:?Usage: hetzner-setup.sh <API_TOKEN>}"
SERVER_NAME="larger-lab-cloud"
SERVER_TYPE="cpx31"          # 4 vCPU, 8GB RAM, 160GB NVMe — €8.50/month
SERVER_LOCATION="fsn1"       # Falkenstein, Germany
SERVER_IMAGE="ubuntu-24.04"
SSH_KEY_NAME="larger-lab-key"
WORKSPACE_REPO="https://github.com/dabiggestpoppa/larger-lab.git"

echo "============================================="
echo "  Hetzner Cloud Agent Rig Setup"
echo "============================================="

# ─── 1. Set API Token ────────────────────────────────────────────────────────
echo "[1/8] Setting Hetzner API token..."
hcloud context create larger-lab --token "$API_TOKEN" 2>/dev/null || \
  hcloud context update larger-lab --token "$API_TOKEN" 2>/dev/null || true
hcloud context use larger-lab

# ─── 2. Create SSH Key ───────────────────────────────────────────────────────
echo "[2/8] Setting up SSH key..."
if ! hcloud ssh-key describe "$SSH_KEY_NAME" &>/dev/null; then
    # Generate SSH key locally if not exists
    if [ ! -f ~/.ssh/larger-lab ]; then
        ssh-keygen -t ed25519 -f ~/.ssh/larger-lab -N "" -C "larger-lab-cloud"
    fi
    hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file ~/.ssh/larger-lab.pub
fi

# ─── 3. Create Server ────────────────────────────────────────────────────────
echo "[3/8] Creating Hetzner VM ($SERVER_TYPE, $SERVER_LOCATION)..."
if ! hcloud server describe "$SERVER_NAME" &>/dev/null; then
    hcloud server create \
        --name "$SERVER_NAME" \
        --type "$SERVER_TYPE" \
        --location "$SERVER_LOCATION" \
        --image "$SERVER_IMAGE" \
        --ssh-key "$SSH_KEY_NAME" \
        --label "project=larger-lab" \
        --label "role=agent-rig"
    
    echo "Waiting for server to be ready..."
    sleep 30
fi

SERVER_IP=$(hcloud server ip "$SERVER_NAME")
echo "Server IP: $SERVER_IP"

# ─── 4. Wait for SSH ─────────────────────────────────────────────────────────
echo "[4/8] Waiting for SSH to be available..."
for i in {1..30}; do
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.ssh/larger-lab root@"$SERVER_IP" "echo ready" 2>/dev/null; then
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 10
done

# ─── 5. System Setup ─────────────────────────────────────────────────────────
echo "[5/8] Configuring system..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/larger-lab root@"$SERVER_IP" << 'REMOTESCRIPT'
set -e

# System update
apt update && apt upgrade -y

# Install essential tools
apt install -y curl wget git unzip software-properties-common \
    python3 python3-pip python3-venv build-essential

# Install Node.js 24
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt install -y nodejs

# Install OpenClaw
npm install -g openclaw@latest

# Install rclone
curl https://rclone.org/install.sh | bash

# Create workspace directory
mkdir -p /root/larger-lab

echo "System setup complete."
echo "Node: $(node --version)"
echo "npm: $(npm --version)"
echo "OpenClaw: $(openclaw --version)"
REMOTESCRIPT

# ─── 6. Clone Workspace ──────────────────────────────────────────────────────
echo "[6/8] Cloning workspace..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/larger-lab root@"$SERVER_IP" << REMOTESCRIPT
set -e
cd /root
if [ ! -d "larger-lab" ]; then
    git clone "$WORKSPACE_REPO" larger-lab
fi
cd larger-lab

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt 2>/dev/null || true
fi

echo "Workspace cloned and ready."
REMOTESCRIPT

# ─── 7. Configure OpenClaw on Cloud ──────────────────────────────────────────
echo "[7/8] Configuring OpenClaw on cloud server..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/larger-lab root@"$SERVER_IP" << 'REMOTESCRIPT'
set -e
cd /root/larger-lab

# Initialize OpenClaw
openclaw setup --workspace /root/larger-lab --non-interactive 2>/dev/null || true

# Configure OpenClaw
cat > ~/.openclaw/openclaw.json << 'OPENCLAW_JSON'
{
  "agents": {
    "defaults": {
      "workspace": "/root/larger-lab",
      "model": "anthropic/claude-sonnet-4-20250514"
    }
  },
  "gateway": {
    "mode": "local",
    "auth": { "mode": "token" },
    "port": 18789,
    "bind": "loopback"
  },
  "skills": {
    "load": {
      "extraDirs": [
        "/root/larger-lab/.hermes/skills",
        "/root/larger-lab/mt5-mcp/skills"
      ]
    }
  },
  "mcp": {
    "servers": {}
  }
}
OPENCLAW_JSON

echo "OpenClaw configured."
REMOTESCRIPT

# ─── 8. Start OpenClaw Gateway ───────────────────────────────────────────────
echo "[8/8] Starting OpenClaw gateway..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/larger-lab root@"$SERVER_IP" << 'REMOTESCRIPT'
set -e
cd /root/larger-lab

# Start OpenClaw gateway in background
nohup openclaw gateway run --port 18789 > /tmp/openclaw-gateway.log 2>&1 &
sleep 3

# Check if it's running
if pgrep -f "openclaw" > /dev/null; then
    echo "OpenClaw gateway is running!"
else
    echo "WARNING: OpenClaw gateway may not have started. Check /tmp/openclaw-gateway.log"
fi

# Set up auto-start on reboot
cat > /etc/systemd/system/openclaw-gateway.service << 'SYSTEMD'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/larger-lab
ExecStart=/usr/bin/openclaw gateway run --port 18789
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

systemctl daemon-reload
systemctl enable openclaw-gateway
systemctl start openclaw-gateway

echo "OpenClaw gateway service installed and started."
REMOTESCRIPT

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "============================================="
echo "  Hetzner VM Setup Complete!"
echo "============================================="
echo ""
echo "Server: $SERVER_NAME"
echo "IP: $SERVER_IP"
echo "Type: $SERVER_TYPE (4 vCPU, 8GB RAM, 160GB NVMe)"
echo "Location: $SERVER_LOCATION (Falkenstein, Germany)"
echo "Cost: ~€8.50/month"
echo ""
echo "SSH Access:"
echo "  ssh -i ~/.ssh/larger-lab root@$SERVER_IP"
echo ""
echo "OpenClaw Gateway:"
echo "  http://$SERVER_IP:18789"
echo ""
echo "Workspace:"
echo "  /root/larger-lab"
echo ""
echo "Next steps:"
echo "  1. Set API key: ssh root@$SERVER_IP 'openclaw config set ANTHROPIC_API_KEY <key>'"
echo "  2. Configure Gmail connector (see GMAIL_SETUP.md)"
echo "  3. Set up SSH tunnel from local: ssh -L 18789:127.0.0.1:18789 root@$SERVER_IP"
echo "============================================="
