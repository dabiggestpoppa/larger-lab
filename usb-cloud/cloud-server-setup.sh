#!/bin/bash
# cloud-server-setup.sh — Provision a free cloud server and deploy the agent workspace
# Target: Oracle Cloud Free Tier (always free ARM instance) or GCP free tier
#
# Usage: Run on the cloud server after SSH-ing in

set -e

echo "============================================="
echo "  Cloud Agent Server Setup"
echo "============================================="

# ─── 1. System Update ───────────────────────────────────────────────────────
echo "[1/7] Updating system..."
sudo apt update && sudo apt upgrade -y

# ─── 2. Install Node.js 24 ──────────────────────────────────────────────────
echo "[2/7] Installing Node.js 24..."
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version

# ─── 3. Install Python 3.11+ ────────────────────────────────────────────────
echo "[3/7] Installing Python..."
sudo apt install -y python3 python3-pip python3-venv
python3 --version

# ─── 4. Install OpenClaw ────────────────────────────────────────────────────
echo "[4/7] Installing OpenClaw..."
npm install -g openclaw@latest
openclaw --version

# ─── 5. Install rclone ──────────────────────────────────────────────────────
echo "[5/7] Installing rclone..."
curl https://rclone.org/install.sh | sudo bash
rclone --version

# ─── 6. Clone Workspace ─────────────────────────────────────────────────────
echo "[6/7] Cloning workspace..."
WORKSPACE="$HOME/larger-lab"
if [ ! -d "$WORKSPACE" ]; then
    # Replace with your actual repo URL
    git clone https://github.com/dabiggestpoppa/larger-lab.git "$WORKSPACE"
fi
cd "$WORKSPACE"

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
fi

# Install uv if available
if command -v uv &> /dev/null; then
    uv sync
fi

# ─── 7. Configure OpenClaw ──────────────────────────────────────────────────
echo "[7/7] Configuring OpenClaw..."
openclaw setup --workspace "$WORKSPACE" --non-interactive

# Configure MCP server
cat > ~/.openclaw/openclaw.json << 'OPENCLAW_JSON'
{
  "agents": {
    "defaults": {
      "workspace": "$HOME/larger-lab",
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
        "$HOME/larger-lab/.hermes/skills",
        "$HOME/larger-lab/mt5-mcp/skills"
      ]
    }
  },
  "mcp": {
    "servers": {}
  }
}
OPENCLAW_JSON

echo ""
echo "============================================="
echo "  Cloud Server Setup Complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo "  1. Set API key: openclaw config set ANTHROPIC_API_KEY <your-key>"
echo "  2. Start gateway: openclaw gateway run --port 18789"
echo "  3. Connect Hermes/Telegram: openclaw channels login"
echo "  4. Access from local: ssh -L 18789:127.0.0.1:18789 user@cloud-server"
echo ""
echo "Workspace: $WORKSPACE"
echo "OpenClaw: $(openclaw --version)"
