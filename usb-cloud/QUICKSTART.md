# Quick Start - Kamatera Agent Rig

## One-Command Setup

Open PowerShell as Administrator and run:

```powershell
# 1. Create the server
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server create --name larger-lab-agent --datacenter US-NY2 --image "Ubuntu 24.04" --cpu 2B --ram 4096 --disk id=0,size=50 --network id=0,name=wan,ip=auto --password "TempPass123!" --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8 --wait

# 2. Get server IP (after creation)
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server info --name larger-lab-agent --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8
```

## After Server is Created

### SSH into the server:
```bash
ssh root@SERVER_IP
```

### Install the workspace (run on server):
```bash
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/usb-cloud/agent-setup.sh | bash
```

### Set up SSH tunnel (from local machine):
```bash
ssh -L 18789:127.0.0.1:18789 root@SERVER_IP
```

### Run backtests:
```bash
cd ~/larger-lab
python nautilus/run_backtest.py
```

---

## Files Created

| File | Purpose |
|------|---------|
| `kamatera-setup.ps1` | PowerShell provisioning script |
| `agent-setup.sh` | Server setup script |
| `create-server.bat` | Batch file for server creation |
| `PROGRESS.md` | Detailed progress report |
| `README.md` | Full documentation |

---

## Current Status

- ✅ cloudcli downloaded and initialized
- ✅ API credentials configured
- ⏳ Server creation pending (run command above)
- ⏳ Workspace deployment pending
- ⏳ SSH tunnel setup pending