# Desktop App Meditation — Trading Dashboard Blueprint

> **Date:** 2026-05-30 | **Author:** OC2 Subagent (MAD directive)
> **Purpose:** Complete blueprint for wrapping the Larger-Lab trading system into a desktop dashboard application.
> **Audience:** CC (architecture review), PM (backend/data layers), PM2 (frontend screens), CC (Tauri packaging)

---

## 1. TECH STACK — Framework Comparison

### Contenders

| Criteria | Electron | Tauri | PyQt / PySide | Pure Web (Next.js at :3000) |
|---|---|---|---|---|
| **Dev Speed** | Fast (JS/HTML/CSS) | Fast (JS + Rust bridge) | Slow (Python GUI work) | Already exists — zero new dev |
| **Bundle Size** | ~150–200 MB (ships Chromium) | ~8–15 MB (uses OS webview) | ~40–80 MB (Python + Qt libs) | N/A (browser tab) |
| **Native API Access** | Good (Node.js fs, net) | Excellent (Rust sidecars) | Excellent (full OS access) | None (sandboxed) |
| **Windows Deployment** | electron-builder, MSI | tauri-cli, MSI/MSIX | PyInstaller, Nuitka | N/A |
| **Dark Mode Theming** | CSS (any framework) | CSS (any framework) | QSS (Qt Stylesheets) | Already implemented |
| **Existing Code Reuse** | Full Next.js frontend | Full Next.js frontend | Rewrite everything | 100% (it's already there) |
| **Memory at Runtime** | ~200–400 MB | ~40–80 MB | ~100–200 MB | Whatever Chrome uses |
| **Security Surface** | Large (Node + Chromium) | Small (Rust, no Node) | Medium (Python eval risks) | Sandboxed by browser |
| **Tray / Notifications** | Built-in | Built-in (Rust) | Qt QSystemTray | Web Notifications API (limited) |
| **Auto-Update** | electron-updater | tauri-plugin-updater | Manual / QUpdater | N/A (server-side) |
| **Code Signing** | Standard EV cert | Standard EV cert | Standard EV cert | N/A |
| **Multi-Window** | Easy | Easy (managed via Rust) | QMainWindow x N | Browser tabs |

### Can We Wrap the Existing Next.js App in Tauri?

**Yes — this is the recommended approach.** The standard Tauri pattern:

1. `npm run build` the Next.js app in `oce/frontend/`
2. `npm run export` produces a `out/` directory of static files
3. Tauri config (`tauri.conf.json`) sets `distDir` to `../frontend/out`
4. Tauri spawns a window using the OS webview (Edge WebView2 on Windows)
5. All `fetch('/api/...')` calls hit the FastAPI backend at `http://localhost:8000`

For **dev mode**, run `tauri dev` — it spins up the Next.js dev server and sets the window URL to `http://localhost:3000`. For **production**, `tauri build` bundles the static output with the Rust shim into a single `.exe` + `.msi` installer.

The `@tauri-apps/api` npm package gives the frontend access to native features (file reads, window controls) via `invoke('command_name')` calls into Rust without any Node.js middleman.

### Recommendation: **Tauri + Existing Next.js**

**Why:**

- **Reuse everything** — `oce/frontend/` is already a working Next.js app with shadcn/ui components, Tailwind, and dark mode. No rewrite.
- **Tiny bundle** — ~10 MB final installer vs Electron's ~180 MB. Laptops with 256 GB SSD care about this.
- **Rust bridge for native reads** — If we ever need to read `sniper.db` or `progress/*.md` directly (bypassing FastAPI), Rust can do it safely on the client side.
- **Edge WebView2** — Every Windows 10+ machine already has this. No Chromium to ship.
- **Security** — No Node.js runtime means no `child_process` escape hatches. Rust is memory-safe.
- **MAD's own precedent** — The `startup-kit` repo by duolahypercho (https://github.com/duolahypercho/startup-kit) uses this exact stack: SF Pro font, shadcn/ui, Tailwind, dark palette. We align with that approach.

**Risks:**
- Requires Rust toolchain on build machine (`rustup`, MSVC build tools)
- WebView2 runtime must be present on target machine (it is on Win 10+, but not guaranteed on clean Win Server)
- Some Next.js features (SSR, API routes) don't work in static export — but we don't need them since FastAPI handles all server-side logic

**Alternate fallback:** If Rust toolchain is a blocker, Electron with `electron-builder` is the well-trodden path. Bundle size penalty is acceptable for an internal tool.

---

## 2. ARCHITECTURE

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESKTOP APP (Tauri + WebView2)               │
│                                                                 │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Dashboard │  │ Agent    │  │ Sniper   │  │ Backtest      │  │
│  │ Screen    │  │ Center   │  │ Panel    │  │ Browser       │  │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘  │
│        │              │             │                │           │
│        └──────────────┴─────────────┴────────────────┘           │
│                           │                                     │
│              fetch('/api/...') + WebSocket                      │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (:8000)                        │
│                  oce/backend/main.py                            │
│                                                                 │
│  GET /api/live/positions    ← reads MT5 bridge / log files     │
│  GET /api/live/trades       ← reads MT5 bridge / log files     │
│  GET /api/live/equity       ← computed from positions + pnl    │
│  GET /api/agents/status     ← reads progress/*.md files        │
│  GET /api/sniper/scores     ← reads quant-lab/sniper/sniper.db │
│  GET /api/reports/list      ← reads quant-lab/reports/*.md     │
│  GET /api/reports/{name}    ← reads quant-lab/reports/{name}.md│
│  GET /api/system/cron-status← reads cron tool output           │
│  GET /api/system/health     ← self-check endpoint              │
│  WS  /ws/live               ← pushes live tick/pnl updates     │
└───────┬────────────┬────────────┬──────────────┬────────────────┘
        │            │            │              │
        ▼            ▼            ▼              ▼
   quant-lab/    progress/   quant-lab/    quant-lab/
   mt5/live_logs/  *.md     sniper/        reports/
   (JSON logs)  AGENTS.md  sniper.db      *.md
```

### Data Flow Details

**Live Trading Data Path:**
1. MT5 executors (running on the machine) write JSON log lines to `quant-lab/mt5/live_logs/`
   - Example file: `live_logs/trades_2026-05-30.jsonl` — one trade event per line
   - Example file: `live_logs/positions_snapshot_2026-05-30.json` — periodic full snapshot
2. FastAPI reads these files on request (or maintains a cached in-memory state refreshed every 2s)
3. FastAPI exposes via REST (`GET /api/live/positions`, `GET /api/live/trades`) and WebSocket (`WS /ws/live`)
4. Desktop app polls every 2s or subscribes to WebSocket

**Agent Status Path:**
1. Each agent writes to its own `progress/<tag>-progress.md` file (e.g., `progress/polymorph-progress.md`)
2. AGENTS.md contains the team roster with tags, roles, status columns
3. `shared-conversations/team-chat.md` contains the most recent team messages
4. A new FastAPI endpoint `GET /api/agents/status` parses all of these files and returns a unified JSON array
5. Parser logic: strip markdown formatting, extract last heartbeat timestamp, extract current task line, extract progress percentage if present

**Sniper Data Path:**
1. `quant-lab/sniper/sniper.db` is a SQLite database with tables: `pes_scores`, `firm_data`, `crossover_events`, `deployments`
2. FastAPI opens this as read-only (`mode=ro` URI flag) — no write access from the desktop app
3. `GET /api/sniper/scores` returns latest PES scorecard
4. `GET /api/sniper/firms` returns firm comparison data
5. `GET /api/sniper/crossovers` returns crossover visualization data

**Reports Path:**
1. `quant-lab/reports/*.md` contains generated backtest reports (human-readable markdown)
2. `GET /api/reports/list` returns `[{name, date, size}, ...]`
3. `GET /api/reports/{name}` returns the parsed markdown content (optionally rendered to HTML server-side via `markdown-it` equivalent)
4. Desktop app renders the markdown in a styled viewer component

### Caching Strategy

FastAPI should maintain an in-memory cache:
- Live positions: cache for 2s (refresh from log file on read)
- Agent status: cache for 30s (file I/O is cheap but not free)
- Sniper scores: cache for 60s (data changes slowly)
- Reports list: cache for 60s
- Individual report: cache indefinitely until server restart (files are static once written)

### WebSocket Design

```
WS /ws/live
Server → Client messages:
  {"type": "tick", "symbol": "EURUSD", "bid": 1.08453, "ask": 1.08457}
  {"type": "pnl_update", "daily_pnl": 127.50, "total_equity": 52341.00}
  {"type": "position_update", "positions": [...]}
  {"type": "heartbeat", "ts": "2026-05-30T17:33:00Z"}

Client → Server messages:
  None (unidirectional push for now)
```

---

## 3. UI SCREENS — 5 Main Views

### Design System

```
Palette (GitHub Dark — #0D1117):
  Background:        #0D1117
  Surface (cards):   #161B22
  Border:            #30363D
  Text primary:      #E6EDF3
  Text secondary:    #8B949E
  Accent blue:       #58A6FF
  Accent green:      #3FB950  (positive PnL)
  Accent red:        #F85149  (negative PnL)
  Accent yellow:     #D29922  (warnings)
  Accent purple:     #BC8CFF  (agent status)

Typography:
  Font:     SF Pro Display / -apple-system / Segoe UI (Windows fallback)
  Numbers:  SF Mono / JetBrains Mono / Consolas
  Sizes:    12px (labels), 14px (body), 16px (section headers), 24px (metric big numbers)

Layout:
  Nav:      Left sidebar, 200px fixed, icon + label
  Header:   Top bar, 48px, title + connection indicator + clock
  Content:  Scrollable main area, dense tables, minimal padding
  Tables:   Fixed header, alternating row hover (#1C2128), monospace numbers right-aligned

Rules:
  NO animations (except connection pulse on status dot)
  NO rounded cards — sharp corners (border-radius: 2px)
  NO gradients — flat colors only
  Dense spacing — 8px gaps, 12px cell padding max
  All numbers right-aligned in monospace
  Color coding: green = profit/live, red = loss/down, yellow = warning, blue = informational
```

### Screen 1: Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ DASHBOARD                                    🟢 LIVE  13:33 │
├─────────┬─────────────┬─────────────┬───────────────────────┤
│ EQUITY  │ DAILY PNL   │ OPEN POSITIONS │ TODAY'S TRADES    │
│ $52,341 │ +$127.50    │ 3              │ 12 (7W / 5L)      │
│         │ ↑ +0.24%    │                │ Winrate: 58.3%     │
├─────────┴─────────────┴─────────────┴───────────────────────┤
│ EQUITY CURVE (canvas, 30-day)        │ POSITIONS TABLE       │
│ ┌────────────────────────────────┐   │ SYM  DIR  PNL    AGE  │
│ │    ╭─╮                        │   │ EUR  LONG +$45.2 2h   │
│ │   ╭╯ ╰╮    ╭──╮              │   │ GBP  SHORT -$12.1 45m │
│ │ ──╯    ╰──╯  ╰────          │   │ USD  LONG +$94.4 1h   │
│ └────────────────────────────────┘   │                      │
├───────────────────────────────────────┴──────────────────────┤
│ RECENT TRADES                                               │
│ TIME     SYMBOL  DIR    SIZE  ENTRY    EXIT     PNL  FIRM   │
│ 13:32    EURUSD  LONG   0.1   1.08453  1.08479  +$2.6  ST   │
│ 13:15    GBPUSD  SHORT  0.05  1.27134  1.27108  +$1.3  P90  │
│ 13:00    USDJPY  LONG   0.2   149.852  open     live  ST   │
└──────────────────────────────────────────────────────────────┘
```

**Data sources:**
- Equity, daily PnL: `GET /api/live/equity`
- Positions table: `GET /api/live/positions`
- Recent trades: `GET /api/live/trades?limit=20`
- Equity curve: `GET /api/live/equity?history=30d` (array of `{date, equity}`)

**WebSocket:** Subscribe to `/ws/live` for real-time PnL updates. Green/red flash on PnL changes (only "animation" — 300ms color transition).

---

### Screen 2: Agent Center

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT CENTER                                                │
├──────┬──────────┬────────────────┬───────────────┬──────────┤
│ TAG  │ AGENT    │ CURRENT TASK   │ LAST HEARTBEAT│ PROGRESS │
├──────┼──────────┼────────────────┼───────────────┼──────────┤
│ 🔵CC │Claude Cod│O-7 architecture│ 3 min ago     │ ████░░ 60│
│ 🟠OC2│OWL (OC2) │Orchestrating   │ Online (13:33)│ N/A      │
│ 🟡AS │Assistant │Ctx monitoring  │ 12 min ago    │ ███░░░ 50│
│ 🔴PM │Polymorph │O-7 backend     │ 1 min ago     │ ██████ 90│
│ 🟢RL │Research  │O-7 research    │ 45 min ago    │ ██░░░░ 30│
├──────┴──────────┴────────────────┴───────────────┴──────────┤
│ TEAM CHAT (latest 15 messages)                               │
│ 13:33  🟠OC2: "Phase 1 endpoints written, PM to review"      │
│ 13:28  🔴 PM: "Data layer complete. 8 endpoints green."      │
│ 13:20  🟡 AS: "All agent files parsed correctly. CC aligned."│
│ 13:15  🔵 CC: "Architecture review done. Approved for build."│
│ ...                                                          │
└──────────────────────────────────────────────────────────────┘
```

**Data sources:**
- Agent list: Parse `AGENTS.md` — extract table rows
- Progress: Parse `progress/<tag>-progress.md` — extract task description and progress bar
- Last heartbeat: Read last modification timestamp of each progress file
- Team chat: Parse last 15 lines of `shared-conversations/team-chat.md`

**Visual:**
- Status dot: green (< 5 min since heartbeat), yellow (< 30 min), red (> 30 min), gray (not found)
- Progress bar: rendered as a 6-block visual (each block = ~16%)
- If progress file doesn't exist: show "⚪ INACTIVE"

---

### Screen 3: Sniper Panel

```
┌─────────────────────────────────────────────────────────────┐
│ SNIPER PANEL                                    PES v1.0    │
├───────────────────────────────┬─────────────────────────────┤
│ PES SCORECARD                 │ FIRM COMPARISON             │
│                               │                             │
│ Firm         PES   Status     │ PES                         │
│ ──────────────────────────    │ 100│    ████                │
│ FTMO         87    🟢 LIVE    │  80│    ████  ████          │
│ MyForexFunds 72    🟡 STANDBY │  60│    ████  ████  ████    │
│ The5ers      64    🔴 PAUSED  │  40│    ████  ████  ████    │
│ TopStep      58    ⚪ OFFLINE │  20│    ████  ████  ████    │
│                               │    0└─────────────────────  │
│ Crossover: FTMO > MFF (✓)    │     FTMO  MFF  5ers TopStep │
├───────────────────────────────┴─────────────────────────────┤
│ DEPLOYMENT SIMULATOR                                        │
│ Equity: [$50,000]  Max DD: [10%]  Sim Days: [30]           │
│                                                             │
│ ┌────────────────────────────────────────────────────┐      │
│ │  55K │      ╭──╮                                    │      │
│ │  50K │ ────╯  ╰──── simulated equity curve          │      │
│ │  45K │                                               │      │
│ └────────────────────────────────────────────────────┘      │
│ Result: Would PASS ✅  Final equity: $51,230  Max DD: 6.2%  │
└──────────────────────────────────────────────────────────────┘
```

**Data sources:**
- PES scorecard: `GET /api/sniper/scores` → `[{firm, pes, status, last_updated}]`
- Firm comparison: `GET /api/sniper/firms` → `[{firm, metrics: {...}}]`
- Crossover data: `GET /api/sniper/crossovers` → `[{date, above, below}]`
- Deployment simulator: POST `/api/sniper/simulate` with body `{equity, max_dd, days}` → `{result, final_equity, max_dd_hit, equity_curve: [...]}`

**Visual:**
- Bar charts: rendered with `<div>` bars (no heavy charting library needed)
- PES score coloring: > 80 green, > 60 yellow, < 60 red
- Crossover events: shown as vertical markers on the equity-equivalent chart

---

### Screen 4: Backtest Browser

```
┌────────────────┬────────────────────────────────────────────┐
│ REPORTS        │ REPORT: sniper_ftmo_v3_backtest.md         │
│ ────────────── │                                            │
│ ▶ sniper_ftmo  │ ┌──────────────────────────────────────┐   │
│   v3 (May 30)  │ │      EQUITY CURVE                    │   │
│   45 KB        │ │  55K │         ╭────                   │   │
│                │ │  50K │ ───────╯                       │   │
│ ▶ sniper_p90   │ │  45K │                                │   │
│   v2 (May 29)  │ │      └────────────────────────        │   │
│   38 KB        │ └──────────────────────────────────────┘   │
│                │                                            │
│ ▶ baseline_h1  │ METRICS                                    │
│   (May 28)     │ net_pnl: +$3,420  max_dd: -$1,890         │
│   22 KB        │ winrate: 61.2%  profit_factor: 1.83       │
│                │ sharpe: 1.41  trades: 847                  │
│                │                                            │
│                │ TRADES TABLE                               │
│                │ #   DATE        SYM   DIR  PNL    DUR     │
│                │ 1   2026-04-01  EUR   L    +$12.3  45m   │
│                │ 2   2026-04-01  GBP   S    -$5.1   12m   │
│                │ 3   2026-04-02  JPY   L    +$8.7   2h    │
│                │ ...                                        │
└────────────────┴────────────────────────────────────────────┘
```

**Data sources:**
- Report list: `GET /api/reports/list` → `[{name, filename, date, size}]`
- Report content: `GET /api/reports/sniper_ftmo_v3_backtest` → `{markdown, metrics: {...}, trades: [...], equity_curve: [...]}`
- The server-side parser extracts structured data from the markdown using regex (metrics section, trade list table)

**Layout:**
- Left panel: scrollable file tree, sorted by date desc
- Right panel: tabbed view — "Chart" (equity curve), "Metrics" (key numbers), "Trades" (sortable table), "Raw" (rendered markdown)
- Charts: simple canvas line chart, no external library dependency

---

### Screen 5: System Monitor

```
┌─────────────────────────────────────────────────────────────┐
│ SYSTEM MONITOR                                              │
├──────────────────────────┬──────────────────────────────────┤
│ CRON JOBS               │ EXECUTORS / PROCESSES            │
│                         │                                  │
│ Name          Schedule  │ PID    Name         CPU   MEM    │
│ ─────────────────────── │ ─────────────────────────────── │
│ mt5_heartbeat  every 5m │ 3412   mt5_exec_st  12%   280MB │
│ log_rotate     hourly   │ 3890   mt5_exec_p90 15%   310MB │
│ report_gen     daily    │ 4102   fastapi      3%    45MB  │
│ snapshot_save  30m      │ tauri  desktop_app 2%    85MB   │
│                         │                                  │
│ ✅ All 4 running         │ ⚠️ High memory: mt5_exec_p90    │
├──────────────────────────┴──────────────────────────────────┤
│ ALERT LOG                                                    │
│ TIME     LEVEL    SOURCE          MESSAGE                    │
│ 13:30    ⚠ WARN   mt5_exec_st     Latency spike: 2.3s        │
│ 13:15    ℹ INFO   log_rotate      Rotated 3 log files        │
│ 12:45    ❌ ERROR  mt5_exec_p90    Connection timeout (recov.)│
│ 12:00    ℹ INFO   system          Daily snapshot complete    │
│ 11:30    ⚠ WARN   sniper          P5ers PES dropped to 58    │
├──────────────────────────────────────────────────────────────┤
│ FASTAPI STATUS: 🟈 Server: localhost:8000 | Uptime: 4h 12m  │
│ LAST DATA REFRESH: 1.2s ago | CACHE HIT RATE: 94%          │
└──────────────────────────────────────────────────────────────┘
```

**Data sources:**
- Cron status: `GET /api/system/cron-status` — parses cron config + last run timestamps
- Process list: `GET /api/system/processes` — reads from `ps` output or a PID tracker file that executors write to
- Alert log: `GET /api/system/alerts?limit=50` — reads from `logs/alerts.jsonl`
- FastAPI health: `GET /api/system/health` — returns `{status, uptime, cache_hit_rate, last_refresh}`

**Visual:**
- Status indicators: 🟢 running, 🟡 degraded, 🔴 stopped
- Alert rows color-coded by level (red for ERROR, yellow for WARN, blue for INFO)
- Auto-scroll alert log with "pause" toggle

---

## 4. BUILD PHASES

### Phase 1: Data Layer (PM builds)

**Scope:** New FastAPI endpoints for all data sources.

**Deliverables:**
- [ ] `GET /api/live/positions` — reads from `quant-lab/mt5/live_logs/positions_snapshot_*.json`, returns JSON array
- [ ] `GET /api/live/trades` — reads from `quant-lab/mt5/live_logs/trades_*.jsonl`, returns JSON array, supports `?limit=N&firm=ST|P90|ALL`
- [ ] `GET /api/live/equity` — computes equity curve from positions + PnL, supports `?history=Nd`
- [ ] `GET /api/agents/status` — parses `AGENTS.md` + `progress/*.md` files, returns unified JSON
- [ ] `GET /api/sniper/scores` — read-only query on `quant-lab/sniper/sniper.db`
- [ ] `GET /api/sniper/firms` — firm comparison data from sniper.db
- [ ] `GET /api/sniper/crossovers` — crossover events from sniper.db
- [ ] `POST /api/sniper/simulate` — runs deployment simulation, returns equity curve
- [ ] `GET /api/reports/list` — lists `quant-lab/reports/*.md` with metadata
- [ ] `GET /api/reports/{name}` — parses report markdown into structured JSON
- [ ] `GET /api/system/cron-status` — parses cron tool output
- [ ] `GET /api/system/processes` — reads executor PIDs / process tracker
- [ ] `GET /api/system/alerts` — reads from `logs/alerts.jsonl`
- [ ] `GET /api/system/health` — self-check endpoint
- [ ] `WS /ws/live` — WebSocket push for tick/PnL updates

**Validation:**
- All endpoints tested with `curl` against live data
- Response time < 200ms for all GET endpoints
- Read-only database access verified (attempted write returns error)

**Estimated effort:** 3–4 days

---

### Phase 2: Dashboard Screen (PM2 builds, CC reviews)

**Scope:** Next.js page at route `/dashboard/` — live trading overview.

**Deliverables:**
- [ ] Dashboard page layout (sidebar nav + header + content area)
- [ ] Big metric cards: equity, daily PnL, open positions, today's trade count
- [ ] Equity curve chart (canvas-based, no external lib)
- [ ] Positions table (symbol, direction, PnL, age) with green/red color coding
- [ ] Recent trades table (time, symbol, direction, size, entry, exit, PnL, firm)
- [ ] Polling hook: `useLiveData()` — fetches every 2s, stores in state
- [ ] WebSocket client: connects to `ws://localhost:8000/ws/live` for PnL push updates
- [ ] "OFFLINE" badge when FastAPI is unreachable; shows cached last-known state
- [ ] Dark mode applied (GitHub Dark palette)

**Design review:** CC validates architecture before PM2 begins.

**Estimated effort:** 2–3 days

---

### Phase 3: Agent Center (PM builds)

**Scope:** Next.js page at route `/agents/` — team monitoring.

**Deliverables:**
- [ ] Agent roster table: tag, name, current task, heartbeat, progress bar
- [ ] Status dot with color logic (green < 5m, yellow < 30m, red > 30m, gray offline)
- [ ] Team chat viewer: last 15 messages from `shared-conversations/team-chat.md`
- [ ] Progress bar visualization (6-block indicator)
- [ ] "INACTIVE" state for agents with no progress file
- [ ] Refresh button + auto-refresh toggle (30s interval)

**Estimated effort:** 1–2 days

---

### Phase 4: Sniper Panel (PM2 builds)

**Scope:** Next.js page at route `/sniper/` — PES visualization and simulation.

**Deliverables:**
- [ ] PES scorecard: firm name, score, status badge
- [ ] Firm comparison bar chart (horizontal bars, div-based)
- [ ] Crossover visualization: timeline with crossover event markers
- [ ] Deployment simulator form: equity input, max DD input, day count input
- [ ] Simulation result: PASS/FAIL badge, final equity, max DD hit, equity curve chart
- [ ] Responsive to Sniper Panel data model changes (DB schema is stable)

**Estimated effort:** 2–3 days

---

### Phase 5: Backtest Browser (PM builds)

**Scope:** Next.js page at route `/backtests/` — report viewer.

**Deliverables:**
- [ ] Left sidebar: report file tree, sorted descending by date, showing file size
- [ ] Report viewer with tabs: Chart / Metrics / Trades / Raw
- [ ] Equity curve chart (screen 4 style)
- [ ] Metrics panel: net PnL, max DD, winrate, profit factor, Sharpe, trade count
- [ ] Trades table: sortable columns, monospace numbers
- [ ] Raw markdown renderer (rendered HTML with dark styling)

**Estimated effort:** 2–3 days

---

### Phase 6: System Monitor (PM builds)

**Scope:** Next.js page at route `/system/` — infrastructure monitoring.

**Deliverables:**
- [ ] Cron job status table: name, schedule, last run, next run, status indicator
- [ ] Process list table: PID, name, CPU%, MEM — color-coded for high usage
- [ ] Alert log: time, level, source, message — color-coded rows
- [ ] Alert auto-scroll with pause toggle
- [ ] FastAPI health bar: status, uptime, last refresh, cache hit rate
- [ ] Visual alert for stopped cron jobs or high-memory processes

**Estimated effort:** 2 days

---

### Phase 7: Desktop Wrapper (CC oversees)

**Scope:** Tauri packaging for the full application.

**Deliverables:**
- [ ] Rust toolchain installed on build machine (`rustup` + MSVC Build Tools)
- [ ] `src-tauri/` directory created in the Next.js project
- [ ] `Cargo.toml` configured with tauri dependencies
- [ ] `tauri.config.json`:
  - `distDir`: `../out` (Next.js static export)
  - `appUrl`: `http://localhost:3000` (dev mode) / `index.html` (production)
  - Window: 1400×900 default, min 1024×700, title "Larger-Lab Dashboard"
  - App name: `larger-lab-dashboard`
  - Identifier: `com.largerlab.dashboard`
- [ ] `tauri.conf.json` CSP: allow `fetch` to `http://localhost:8000` only
- [ ] Build script: `npm run build && tauri build` → produces `.msi` installer
- [ ] Code signing: EV cert configured in `tauri.conf.json` (to be provided by MAD)
- [ ] Test: MSI installs on clean Windows 10 VM, app launches, connects to FastAPI
- [ ] Fallback: If Tauri proves difficult, Electron builder config as backup

**CC oversees architecture, does not write Rust** — may delegate to PM for Rust bridge code.

**Estimated effort:** 3–4 days (including testing and packaging)

---

### Phase Summary

| Phase | Builder | Reviewer | Days | Dependencies |
|-------|---------|----------|------|-------------|
| 1: Data Layer | PM | CC | 3–4 | None (starts immediately) |
| 2: Dashboard | PM2 | CC | 2–3 | Phase 1 (endpoints must exist) |
| 3: Agent Center | PM | CC | 1–2 | Phase 1 |
| 4: Sniper Panel | PM2 | CC | 2–3 | Phase 1 |
| 5: Backtest Browser | PM | CC | 2–3 | Phase 1 |
| 6: System Monitor | PM | CC | 2 | Phase 1 |
| 7: Desktop Wrapper | CC + PM | MAD sign-off | 3–4 | Phases 1–6 (all screens done) |

**Total estimated time:** 15–22 days (with 2 concurrent sub-agents working Phases 2–6 in parallel after Phase 1 completes)

---

## 5. INTEGRATION POINTS

### Existing Resources to Leverage

| Resource | Type | How Desktop App Uses It |
|---|---|---|
| `oce/backend/main.py` | FastAPI server | Add all new API routes here. Already running at :8000. Add a new router file `oce/backend/routers/dashboard.py` and include it in `main.py`. |
| `oce/frontend/` | Next.js app | Add new pages: `pages/dashboard.tsx`, `pages/agents.tsx`, `pages/sniper.tsx`, `pages/backtests.tsx`, `pages/system.tsx`. Reuse existing shadcn/ui components and Tailwind config. |
| `quant-lab/mt5/live_logs/` | JSON/JSONL files | FastAPI reads these on each API request. Format: `positions_snapshot_YYYY-MM-DD.json` (array of position objects), `trades_YYYY-MM-DD.jsonl` (newline-delimited trade events). |
| `quant-lab/sniper/sniper.db` | SQLite DB | FastAPI opens with read-only URI: `file:/path/to/sniper.db?mode=ro`. Tables available: `pes_scores`, `firm_data`, `crossover_events`, `deployments`. |
| `progress/*.md` | Markdown files | FastAPI reads all `progress/*.md` files, parses progress bars and timestamps. Simple regex extraction — no full markdown parsing needed. |
| `AGENTS.md` | Markdown file | FastAPI parses the team roster table. Extract columns: tag, agent name, role, status. |
| `shared-conversations/team-chat.md` | Markdown file | FastAPI reads last 15 lines, reverses order (newest first), returns as array of `{timestamp, tag, message}`. |
| `quant-lab/reports/*.md` | Markdown files | FastAPI lists files and parses selected reports. Extract metrics section (key-value pairs), trade table (pipe-delimited), equity curve data (if embedded in report). |
| `logs/alerts.jsonl` | JSONL file | FastAPI tails last 500 lines and returns newest alerts. |

### New Endpoints Specification

#### `GET /api/live/positions`
```json
Response: {
  "positions": [
    {"symbol": "EURUSD", "direction": "LONG", "size": 0.1, "entry": 1.08453, "current": 1.08479, "pnl": 2.60, "age": "2h 15m", "firm": "ST"}
  ],
  "as_of": "2026-05-30T17:33:00Z",
  "source": "live" | "cached"
}
```

#### `GET /api/live/trades`
```json
Query params: ?limit=50&firm=ST|P90|ALL
Response: {
  "trades": [
    {"time": "13:32:15", "symbol": "EURUSD", "dir": "LONG", "size": 0.1, "entry": 1.08453, "exit": 1.08479, "pnl": 2.60, "firm": "ST"},
    ...
  ],
  "total": 847,
  "daily_wins": 7,
  "daily_losses": 5
}
```

#### `GET /api/live/equity`
```json
Query params: ?history=30d
Response: {
  "current_equity": 52341.00,
  "daily_pnl": 127.50,
  "daily_return_pct": 0.24,
  "history": [
    {"date": "2026-04-30", "equity": 49800.00},
    {"date": "2026-05-01", "equity": 50120.00},
    ...
  ]
}
```

#### `GET /api/agents/status`
```json
Response: {
  "agents": [
    {"tag": "CC", "emoji": "🔵", "name": "Claude Code", "role": "Overseer / Architecture", "current_task": "O-7 architecture review", "last_heartbeat": "2026-05-30T17:30:00Z", "heartbeat_age_min": 3, "progress_pct": 60, "status": "active"}
  ],
  "last_updated": "2026-05-30T17:33:00Z"
}
```

#### `GET /api/sniper/scores`
```json
Response: {
  "scores": [
    {"firm": "FTMO", "pes": 87, "status": "LIVE", "last_updated": "2026-05-30T17:00:00Z"},
    ...
  ]
}
```

#### `GET /api/reports/list`
```json
Response: {
  "reports": [
    {"name": "sniper_ftmo_v3_backtest", "filename": "sniper_ftmo_v3_backtest.md", "date": "2026-05-30", "size_kb": 45}
  ]
}
```

#### `GET /api/reports/{name}`
```json
Response: {
  "name": "sniper_ftmo_v3_backtest",
  "markdown": "# Sniper FTMO v3 Backtest\n...",
  "metrics": {"net_pnl": 3420, "max_dd": -1890, "winrate": 61.2, "profit_factor": 1.83, "sharpe": 1.41, "trades": 847},
  "equity_curve": [{"day": 1, "equity": 50000}, ...],
  "trades": [{"date": "2026-04-01", "symbol": "EURUSD", ...}]
}
```

#### `GET /api/system/cron-status`
```json
Response: {
  "jobs": [
    {"name": "mt5_heartbeat", "schedule": "*/5 * * * *", "last_run": "2026-05-30T17:30:00Z", "next_run": "2026-05-30T17:35:00Z", "status": "running"}
  ]
}
```

#### `WS /ws/live`
```json
Server push messages:
{"type": "tick", "symbol": "EURUSD", "bid": 1.08453, "ask": 1.08457, "ts": "17:33:01.234Z"}
{"type": "pnl_update", "daily_pnl": 128.30, "equity": 52341.80}
{"type": "heartbeat", "ts": "17:33:05.000Z"}
```

---

## 6. RISKS

### 🔴 Critical Risks

**1. API Keys / MT5 Credentials Exposure**
- **Risk:** Desktop app bundled with MT5 credentials could leak them.
- **Mitigation:** The desktop app is **read-only visualizer only**. It connects exclusively to FastAPI at `localhost:8000`. FastAPI alone holds MT5 credentials in `oce/backend/` on the server machine. The desktop app never touches MT5 directly.
- **Rule:** No credentials in frontend code. No env variables in Tauri bundle. If the desktop app needs auth, use a session token issued by FastAPI on local connection only.

**2. Desktop App Writing to Critical Data**
- **Risk:** Bug in desktop app overwrites sniper.db or MT5 state.
- **Mitigation:**
  - FastAPI opens `sniper.db` with SQLite read-only URI (`?mode=ro`)
  - All FastAPI DB endpoints are SELECT only
  - Tauri CSP blocks any `fetch` to endpoints other than `localhost:8000`
  - No `POST`/`PUT`/`DELETE` endpoints are exposed to the desktop app

**3. Windows Defender False Positive**
- **Risk:** Packaged Electron/Tauri binary flagged as malware. Common for trading/jailbreak-adjacent tools that read process memory or file watchers.
- **Mitigation:**
  - Code-sign the final `.exe` and `.msi` with an Extended Validation (EV) certificate
  - Submit to Microsoft for malware analysis BEFORE release (https://www.microsoft.com/en-us/wdsi/filesubmission)
  - Avoid `eval()`, dynamic `require()`, or shell execution from the desktop app
  - Tauri is better here than Electron — no Node.js runtime = less detection surface

---

### 🟡 Medium Risks

**4. File Watcher Performance / Tight Loops**
- **Risk:** Reading large log files on every API call causes I/O spikes.
- **Mitigation:**
  - FastAPI reads `live_logs/` with debounced polling (2s), NOT tight loop
  - Log reads use `tail -500` equivalent (last 500 lines only) — never full file read
  - For JSONL files: read from end of file backwards, stop after 500 newlines
  - In-memory cache with TTL prevents repeated disk hits

**5. Large Log Files Overwhelming Memory**
- **Risk:** `trades_*.jsonl` grows to hundreds of MB over days.
- **Mitigation:**
  - Log rotation already handled by cron (`log_rotate` job truncate/rotate older files)
  - FastAPI always tails last 500 lines; discards the rest
  - If log exceeds 100MB, FastAPI returns warning: `{"warning": "log_truncated", "lines_returned": 500}`

**6. FastAPI Down — Desktop App Goes Blank**
- **Risk:** If FastAPI crashes, desktop app shows nothing.
- **Mitigation:**
  - Desktop app caches last-known state in `sessionStorage` (per-tab) or `localStorage` (persistent)
  - If API call fails, show cached data with "⚠ OFFLINE — data from 12:34 (3m ago)" badge
  - Auto-retry every 5s; badge turns green when connection restored
  - FastAPI should have its own watchdog (hermes_watchdog already exists for this purpose)

**7. WebView2 Not Installed**
- **Risk:** Tauri requires Windows Edge WebView2. Not present on clean Windows installs or Server SKUs.
- **Mitigation:**
  - Include WebView2 Evergreen Bootstrapper in the MSI installer prerequisites
  - Detect on app startup: if WebView2 missing, show install prompt with link
  - Fallback: detect and instruct user to install from `https://developer.microsoft.com/en-us/microsoft-edge/webview2/`

---

### 🟢 Low Risks

**8. SSE vs WebSocket Choice**
- **Risk:** WebSocket may be blocked by corporate proxies. One-way push might suffice.
- **Mitigation:** Start with simple polling (2s interval). If real-time feel is insufficient, add Server-Sent Events (`/api/live/events` with `text/event-stream`). WebSocket is a future optimization.

**9. Next.js Static Export Limitations**
- **Risk:** `next export` doesn't support SSR, API routes, or middleware. Some shadcn/ui components rely on server-side data.
- **Mitigation:** All data comes from FastAPI (`localhost:8000`), not Next.js API routes. Components must use `useEffect` + `fetch`, not `getServerSideProps`. This is already the pattern in our codebase.

**10. Rust Toolchain Build Machine Setup**
- **Risk:** Tauri requires Rust + MSVC Build Tools. Large download (~2 GB), long compile times.
- **Mitigation:**
  - Document the setup steps in a `BUILD.md` file
  - Cache the Cargo build directory between builds
  - Phase 7 is the LAST phase — time to set up the build machine
  - Electron fallback is always available if Rust proves problematic

---

## Appendix: File Structure

```
meditation-room/
└── desktop-app-meditation.md          ← This file

oce/backend/
├── main.py                            ← Existing — add routers below
├── routers/
│   ├── __init__.py
│   ├── dashboard.py                   ← NEW: /api/live/* endpoints
│   ├── agents.py                      ← NEW: /api/agents/* endpoints
│   ├── sniper.py                      ← NEW: /api/sniper/* endpoints
│   ├── reports.py                     ← NEW: /api/reports/* endpoints
│   └── system.py                      ← NEW: /api/system/* endpoints
├── services/
│   ├── log_reader.py                  ← NEW: reads live_logs/ files
│   ├── agent_parser.py                ← NEW: parses progress/*.md
│   ├── sniper_db.py                   ← NEW: read-only SQLite access
│   ├── report_parser.py               ← NEW: parses report markdown
│   └── alert_reader.py                ← NEW: reads alerts.jsonl
└── websocket.py                       ← NEW: /ws/live handler

oce/frontend/
├── pages/
│   ├── index.tsx                      ← Existing — add nav links
│   ├── dashboard.tsx                  ← NEW: Screen 1
│   ├── agents.tsx                     ← NEW: Screen 2
│   ├── sniper.tsx                     ← NEW: Screen 3
│   ├── backtests.tsx                  ← NEW: Screen 4
│   └── system.tsx                     ← NEW: Screen 5
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx                ← NEW: left nav
│   │   ├── Header.tsx                 ← NEW: top bar w/ status
│   │   └── OfflineBanner.tsx          ← NEW: connection warning
│   ├── charts/
│   │   ├── EquityCurve.tsx            ← NEW: canvas line chart
│   │   └── BarChart.tsx               ← NEW: div-based bars
│   └── ui/                            ← Existing shadcn/ui
│       ├── OfflineBadge.tsx           ← NEW
│       ├── StatusDot.tsx              ← NEW
│       ├── ProgressBlocks.tsx         ← NEW
│       └── MetricCard.tsx             ← NEW
├── hooks/
│   ├── useLiveData.ts                 ← NEW: polling + WS
│   ├── useOfflineCache.ts             ← NEW: localStorage fallback
│   └── useAgentStatus.ts              ← NEW: agent data hook
└── styles/
    └── dashboard.css                  ← NEW: dark palette overrides

src-tauri/                             ← NEW: Tauri project root
├── Cargo.toml
├── tauri.conf.json
├── icons/
│   ├── app-icon.png
│   └── tray-icon.png
└── src/
    └── main.rs                        ← T minimal Rust main

quant-lab/                             ← NO CHANGES — read only
├── mt5/live_logs/                     ← FastAPI reads these
├── sniper/sniper.db                   ← FastAPI reads (mode=ro)
└── reports/*.md                       ← FastAPI reads these

progress/                              ← NO CHANGES — read only
├── claude-code-progress.md            ← FastAPI reads these
├── openclaw-2-progress.md
├── assistant-progress.md
├── polymorph-progress.md
└── researcher-progress.md
```

---

*Blueprint complete. Ready for MAD review and CC architecture sign-off. Phase 1 can begin immediately — no blockers.*
