# Telegram Bot Setup

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# Telegram Bot Registration Guide

## Step 1: Create a Bot with BotFather

1. Open Telegram and search for **@BotFather** (the official Telegram bot)
2. Start a chat and send: `/newbot`
3. BotFather will ask for a **name** — enter: `PrimaryObserver` (or whatever you like)
4. BotFather will ask for a **username** — must end in `bot`, e.g.: `primary_observer_bot`
5. BotFather will give you a **token** like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
6. **Save this token** — you'll need it to run the gateway

## Step 2: Configure the Bot (Optional but Recommended)

Send these commands to @BotFather:

```
/setdescription — Set bot description: "Primary Observer — sovereign operational interface for Larger-Lab"
/setabouttext — Set about text: "Operational continuity layer. Not a chatbot."
/setuserpic — Upload a profile picture
/setcommands — Set command menu:
  status — Check all service ports
  spawn — Spawn an agent
  report — Operational summary
  memory — Search vault notes
  graph — Knowledge graph summary
  research — Research a topic
  sync — Sync vault state
  task — Create/list tasks
  trace — Trace execution
  failure — Log structured failure
  help — Show all commands
```

## Step 3: Get Your Chat ID

1. Start a chat with your new bot (tap the username, send any message)
2. Open this URL in a browser (replace `<TOKEN>`):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id":123456789` — that number is your **Chat ID**
4. Save it for access control (optional)

## Step 4: Run the Gateway

```powershell
# In the larger-lab workspace:
$env:TELEGRAM_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
python scripts\start_telegram_gateway.py
```

## Step 5: Test

Send these messages to your bot:
- `/help` — see all commands
- `/status` — check service ports
- `/memory observer` — search vault
- `/spawn research analyze something` — spawn an agent

## Security Notes

- **Never commit the token** to git — use environment variables
- The gateway validates messages come from Telegram's API
- For production: add chat_id whitelist in `telegram_gateway.py`
- BotFather token format: `<numeric_id>:<alphanumeric_string>`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Set TELEGRAM_TOKEN" error | Export the env var before running |
| No response | Check bot token, ensure you messaged the bot first |
| Port conflicts | Gateway doesn't use a port — it polls Telegram's API |
| SSL errors | Update Python/certifi: `pip install --upgrade certifi` |

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Description]]
[[Expo]]
[[Server]]
[[Troubleshooting]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Primary Observer]]
[[Vault]]
[[Telegram Gateway]]
