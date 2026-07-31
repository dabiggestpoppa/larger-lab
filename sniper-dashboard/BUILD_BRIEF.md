# SW Dev Team — Dashboard Build Task Brief

> Author: OC2/OWL | Date: 2026-05-31 04:20 EDT
> Authorized by: MAD (stepping-away directive)
> Priority: HIGH | Status: AUTHORIZED

## Objective
Build a nice, simple trading dashboard UI that runs locally. The SW Dev team should use the existing `sniper-dashboard` Next.js skeleton and expand it into a comprehensive CEREBUS trading dashboard.

## Reference Repos (MAD's GitHub List — for design inspiration, NOT copying)
1. https://github.com/ruvnet/RuView.git — Agent visualization
2. https://github.com/colbymchenry/codegraph.git — Code graph visualization
3. https://github.com/mattpocock/skills.git — Skills system
4. https://github.com/dograh-hq/dograh.git — Agent platform
5. https://github.com/teng-lin/notebooklm-py.git — Notebook LM
6. https://github.com/kaktusesquire6rmu/ai-polymarket-agent.git — Polymarket agent

MAD directive: "TRADING INSIGHT TO INTEGRATE STRATEGICALLY WE DONT COPY WE IMPLEMENT THE LOGIC"

## Existing Dashboard Skeleton
- **Location:** `C:\Users\wifik\Desktop\projects\larger-lab\sniper-dashboard\`
- **Stack:** Next.js 14, React, TypeScript, Tailwind CSS, Recharts
- **Existing components:** HealthIndicator, PESChart, FirmMatrix, CrossoverAlert, DeploymentPanel, PromoTracker
- **API server:** `api_server.py` (needs to feed live data)

## Dashboard Requirements

### Core Pages/Views (Priority Order)
1. **Overview (Main Dashboard)**
   - Live P&L (daily, weekly, monthly)
   - Active trades count
   - Win rate (rolling 20/50 trades)
   - Account balance, equity, drawdown %
   - Real-time price tickers for active symbols (EURUSD, USDCHF)

2. **Strategy Performance**
   - Symmetry Trap (EURUSD.PRO) stats: trades, WR, PnL, avg win/loss
   - P90 CASCADE (USDCHF.PRO) stats: trades, WR, PnL, avg win/loss
   - Combined stats
   - Per-asset breakdown (link to existing backtest reports)

3. **Trade History**
   - Table of recent trades (entry, exit, PnL, duration)
   - Filterable by strategy and asset
   - Export to CSV

4. **Backtest Integration**
   - Read existing reports from `quant-lab/reports/`
   - Display per-asset WR/PF/Sharpe in a clean grid
   - Link to full report files

5. **System Health**
   - Executor status (ST alive? P90 alive?)
   - API server status
   - MT5 connection status
   - Last trade timestamp

### Design Principles
- Simple, clean, dark mode (trading aesthetic)
- Mobile-responsive
- Auto-refresh every 30 seconds
- Agent terminal panel (PowerShell-style, can be added later)
- "Good + Good = Great" — take inspiration from existing repos but make it ours

### Data Sources
- MT5 monitor: `quant-lab/mt5/cerebus_monitor.py` (command-line, parse output)
- Backtest reports: `quant-lab/reports/` JSON and markdown files
- Live positions: MT5 via executor status scripts
- Prop firm data: `quant-lab/sniper/` budget data

### Skills Available
- Frontend development: `frontend-design`, `threejs-*`, `canvas`
- Software development: `nodejs-backend-patterns`, `next-best-practices`, `next-cache-components`
- Data visualization: `diagram-maker`, `pandas-pro`
- SW development manager: `software-development`, `subagent-driven-development`
- If additional skills needed, use ClawHub to find them

## Build Process
1. Review existing `sniper-dashboard` skeleton
2. Review 2-3 GitHub repos for design patterns (don't copy, extract ideas)
3. Plan component architecture
4. Build components one at a time
5. Test locally: `cd sniper-dashboard; npm run dev`
6. Verify dashboard loads on http://localhost:3000
7. Write completion report to Obsidian vault

## Output
- Working dashboard at `sniper-dashboard/`
- All components functional
- API server serving live data
- Completion report in Obsidian vault: `execution/DASHBOARD_BUILD_COMPLETE.md`

## Vault Access
```python
from pathlib import Path
VAULT = Path('C:/Users/wifik/Downloads/o2c')
def write_note(category, title, content):
    p = VAULT / category / f"{title}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
```

## Obsidian Categories
agents, architecture, doctrine, execution, failures, graphs, heuristics, journals, memory, ontology, routing, skills
