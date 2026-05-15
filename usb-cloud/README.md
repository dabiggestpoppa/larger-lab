# Kamatera Cloud Agent Rig

Provision and configure a Kamatera VM for running the agent workspace with OpenClaw gateway.

## Prerequisites

- Kamatera API Key and Secret (from https://cloud.kamatera.com)
- cloudcli downloaded (or use the setup script)
- SSH key pair for server access

## Quick Start

### 1. Provision Server

```powershell
# PowerShell - run from usb-cloud directory
.\kamatera-setup.ps1 -ApiKey "YOUR_API_KEY" -ApiSecret "YOUR_API_SECRET"
```

Or manually with cloudcli:

```bash
cloudcli server create \
  --name larger-lab-agent \
  --datacenter US-NY2 \
  --image "Ubuntu 24.04" \
  --cpu 2B \
  --ram 4096 \
  --disk id=0,size=50 \
  --network id=0,name=wan,ip=auto \
  --password "TempPass123!" \
  --api-clientid YOUR_API_KEY \
  --api-secret YOUR_API_SECRET \
  --wait
```

### 2. Get Server IP

```bash
cloudcli server info --name larger-lab-agent --api-clientid YOUR_API_KEY --api-secret YOUR_API_SECRET
```

### 3. Install Workspace (on server)

```bash
# SSH into server
ssh root@SERVER_IP

# Run setup script
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/usb-cloud/agent-setup.sh | bash
```

### 4. Configure SSH Tunnel (from local machine)

```bash
# Forward gateway port to local machine
ssh -L 18789:127.0.0.1:18789 root@SERVER_IP
```

Now you can access the gateway at `http://localhost:18789` from your local machine.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Machine                            │
│  ┌──────────────┐         ┌─────────────────────────────┐   │
│  │   VS Code    │◄────────│  SSH Tunnel (port 18789)  │   │
│  │              │         └─────────────────────────────┘   │
│  │ OpenClaw     │                                         │
│  │ Extension    │                                         │
│  └──────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kamatera VM                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  OpenClaw Gateway (port 18789)                      │  │
│  │  - OpenRouter model: poolside/laguna-m.1:free       │  │
│  │  - Telegram plugin enabled                          │  │
│  │                                                     │  │
│  │  larger-lab workspace                                 │  │
│  │  - Nautilus backtesting                             │  │
│  │  - Python 3.11+                                     │  │
│  │  - Node.js 24                                       │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Server Specs

| Component | Value |
|-----------|-------|
| OS | Ubuntu 24.04 |
| CPU | 2B (2 shared cores) |
| RAM | 4GB |
| Disk | 50GB SSD |
| Datacenter | US-NY2 |
| Estimated Cost | ~$0.02/hr |

## Files

- `kamatera-setup.ps1` - PowerShell script to provision VM
- `agent-setup.sh` - Setup script for workspace installation
- `cloud-server-setup.sh` - Original reference script

## Troubleshooting

### Gateway not accessible

1. Check server is running: `cloudcli server info --name larger-lab-agent`
2. Verify SSH tunnel: `ssh -L 18789:127.0.0.1:18789 root@SERVER_IP`
3. Check gateway logs on server: `journalctl -u openclaw-gateway`

### Model not responding

1. Verify OpenRouter API key is set: `openclaw config get OPENROUTER_API_KEY`
2. Test model directly: `curl https://openrouter.ai/api/v1/models`

### SSH connection issues

1. Ensure password meets requirements (10-20 chars, upper/lower/digit)
2. Use SSH key instead: `--ssh-key ~/.ssh/id_rsa.pub`