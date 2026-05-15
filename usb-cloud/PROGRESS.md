# Cloud Agent Rig - Progress Report

## Status: ⏳ In Progress - Server Provisioning

### Completed Tasks
- [x] Downloaded cloudcli v1.2.4
- [x] Initialized cloudcli with API credentials
- [x] Created setup scripts (kamatera-setup.ps1, agent-setup.sh)
- [x] Created documentation (README.md)

### Pending Tasks
- [ ] Create Kamatera VM (larger-lab-agent)
- [ ] SSH into server and run agent-setup.sh
- [ ] Configure OpenClaw with OpenRouter model
- [ ] Set up SSH tunnel for local access
- [ ] Run backtests on cloud server

---

## Server Creation Command

Run this command to create the server:

```powershell
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server create `
  --name larger-lab-agent `
  --datacenter US-NY2 `
  --image "Ubuntu 24.04" `
  --cpu 2B `
  --ram 4096 `
  --disk id=0,size=50 `
  --network id=0,name=wan,ip=auto `
  --password "TempPass123!" `
  --api-clientid 84908b7a4714aacd25c51715e0efe96e `
  --api-secret 9cd519e13f62ef5522736cb103328ba8 `
  --wait
```

Or use the batch file:
```cmd
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\create-server.bat
```

---

## After Server Creation

### 1. Get Server IP
```bash
cloudcli server info --name larger-lab-agent --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8
```

### 2. SSH and Install Workspace
```bash
ssh root@SERVER_IP
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/usb-cloud/agent-setup.sh | bash
```

### 3. Configure SSH Tunnel (Local)
```bash
ssh -L 18789:127.0.0.1:18789 root@SERVER_IP
```

### 4. Run Backtests
```bash
cd ~/larger-lab
python nautilus/run_backtest.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Machine                            │
│  ┌──────────────┐         ┌─────────────────────────────┐   │
│  │   VS Code    │◄────────│  SSH Tunnel (port 18789)  │   │
│  │              │         └─────────────────────────────┘   │
│  └──────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kamatera VM                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  OpenClaw Gateway (port 18789)                      │  │
│  │  - Model: poolside/laguna-m.1:free (OpenRouter)     │  │
│  │  - Telegram plugin enabled                          │  │
│  │                                                     │  │
│  │  larger-lab workspace                                 │  │
│  │  - Nautilus backtesting                             │  │
│  │  - Python 3.11+, Node.js 24                        │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Estimated Costs
- 2B CPU + 4GB RAM + 50GB SSD: ~$0.02-0.04/hr
- Monthly (720 hrs): ~$14-28/month

---

## Notes for Other Agents
- API Key: `84908b7a4714aacd25c51715e0efe96e`
- API Secret: `9cd519e13f62ef5522736cb103328ba8`
- Server name: `larger-lab-agent`
- Password: `TempPass123!` (change after setup)
- Model: `poolside/laguna-m.1:free` via OpenRouter