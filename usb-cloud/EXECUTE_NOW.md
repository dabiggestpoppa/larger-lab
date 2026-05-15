# EXECUTE NOW - Kamatera Server Creation

## Run This Command in PowerShell

```powershell
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server create --name larger-lab-agent --datacenter US-NY2 --image "Ubuntu 24.04" --cpu 2B --ram 4096 --disk id=0,size=50 --network id=0,name=wan,ip=auto --password "TempPass123!" --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8 --wait
```

## After Server is Created

### 1. Get Server IP
```powershell
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server info --name larger-lab-agent --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8
```

### 2. SSH into Server (from WSL, Git Bash, or PuTTY)
```bash
ssh root@SERVER_IP
```

### 3. Install Workspace (on server)
```bash
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/usb-cloud/agent-setup.sh | bash
```

### 4. Set Up SSH Tunnel (from local machine)
```bash
ssh -L 18789:127.0.0.1:18789 root@SERVER_IP
```

### 5. Run Backtests
```bash
cd ~/larger-lab
python nautilus/run_backtest.py
```

---

## Files Ready for Use

| File | Location |
|------|----------|
| cloudcli.exe | `usb-cloud/cloudcli.exe` |
| Setup script | `usb-cloud/agent-setup.sh` |
| PowerShell script | `usb-cloud/kamatera-setup.ps1` |
| Documentation | `usb-cloud/README.md` |
| Progress | `usb-cloud/PROGRESS.md` |

---

## Configuration Summary

- **Model**: poolside/laguna-m.1:free (OpenRouter)
- **Gateway Port**: 18789
- **Workspace**: ~/larger-lab
- **Backtest Script**: nautilus/run_backtest.py