#!/bin/bash
# agent-setup.sh - Install agent workspace on Kamatera VM
# Run this on the cloud server after provisioning

set -e

echo "============================================="
echo "  Agent Workspace Setup"
echo "============================================="

# ─── 1. System Update ───────────────────────────────────────────────────────
echo "[1/6] Updating system..."
apt update && apt upgrade -y

# ─── 2. Install Node.js 24 ───────────────────────────────────────────────────
echo "[2/6] Installing Node.js 24..."
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt install -y nodejs
node --version
npm --version

# ─── 3. Install Python 3.11+ ───────────────────────────────────────────────
echo "[3/6] Installing Python..."
apt install -y python3 python3-pip python3-venv build-essential
python3 --version

# ─── 4. Install OpenClaw ─────────────────────────────────────────────────────
echo "[4/6] Installing OpenClaw..."
npm install -g openclaw@latest
openclaw --version

# ─── 5. Clone Workspace ─────────────────────────────────────────────────────
echo "[5/6] Cloning workspace..."
WORKSPACE="$HOME/larger-lab"
if [ ! -d "$WORKSPACE" ]; then
    git clone https://github.com/dabiggestpoppa/larger-lab.git "$WORKSPACE"
fi
cd "$WORKSPACE"

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi

# ─── 6. Configure OpenClaw ───────────────────────────────────────────────────
echo "[6/6] Configuring OpenClaw..."
openclaw setup --workspace "$WORKSPACE" --non-interactive

# Configure for OpenRouter
cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "agents": {
    "defaults": {
      "workspace": "$HOME/larger-lab",
      "model": "poolside/laguna-m.1:free"
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
  "plugins": {
    "entries": {
      "openrouter": { "enabled": true },
      "telegram": { "enabled": true }
    }
  }
}
EOF

echo ""
echo "============================================="
echo "  Agent Workspace Setup Complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo "  1. Set OpenRouter API key: openclaw config set OPENROUTER_API_KEY <your-key>"
echo "  2. Start gateway: openclaw gateway run --port 18789"
echo "  3. Connect from local: ssh -L 18789:127.0.0.1:18789 root@SERVER_IP"