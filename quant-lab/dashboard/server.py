#!/usr/bin/env python3
"""
DMR Live Trading Dashboard
Simple web UI for monitoring and configuring the DMR live trading script.
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="DMR Live Dashboard")

BASE_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")
CONFIG_FILE = BASE_DIR / "dmr_config.json"
DB_FILE = BASE_DIR / "dmr_live.db"
STATE_FILE = BASE_DIR / "dmr_live_state.json"

# Available symbols (from backtested assets)
AVAILABLE_SYMBOLS = [
    {"id": "EURUSD.PRO", "name": "EUR/USD", "backtest_wr": "94.8%", "backtest_pnl": "+7,903p"},
    {"id": "USDCHF.PRO", "name": "USD/CHF", "backtest_wr": "92.1%", "backtest_pnl": "+8,128p"},
    {"id": "CHFJPY.PRO", "name": "CHF/JPY", "backtest_wr": "95.3%", "backtest_pnl": "+2,154p"},
    {"id": "XAUUSD.PRO", "name": "XAU/USD (Gold)", "backtest_wr": "94.5%", "backtest_pnl": "+4,489p"},
]

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def query_db(query, params=()):
    if not DB_FILE.exists():
        return []
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/api/status")
async def api_status():
    cfg = load_config()
    state = load_state()
    # Don't expose password
    safe_cfg = {k: v for k, v in cfg.items() if k != 'password'}
    return JSONResponse({
        "config": safe_cfg,
        "state": state,
        "available_symbols": AVAILABLE_SYMBOLS,
        "server_time": datetime.now(timezone.utc).isoformat()
    })

@app.get("/api/trades")
async def api_trades(limit=50):
    trades = query_db("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
    return JSONResponse({"trades": trades})

@app.get("/api/p90s")
async def api_p90s(limit=50):
    p90s = query_db("SELECT * FROM p90_events ORDER BY id DESC LIMIT ?", (limit,))
    return JSONResponse({"p90s": p90s})

@app.get("/api/logs")
async def api_logs(limit=50):
    logs = query_db("SELECT * FROM system_log ORDER BY id DESC LIMIT ?", (limit,))
    return JSONResponse({"logs": logs})

@app.get("/api/account")
async def api_account(limit=20):
    snaps = query_db("SELECT * FROM account_snapshots ORDER BY id DESC LIMIT ?", (limit,))
    return JSONResponse({"snapshots": snaps})

@app.post("/api/config")
async def api_update_config(request: Request):
    data = await request.json()
    cfg = load_config()
    # Only allow updating safe fields
    allowed = ['symbols', 'lot_size', 'max_daily_trades_per_symbol', 'hard_exit_hour_est', 'deep_mult', 'kill_mult', 'enabled']
    for k in allowed:
        if k in data:
            cfg[k] = data[k]
    save_config(cfg)
    safe_cfg = {k: v for k, v in cfg.items() if k != 'password'}
    return JSONResponse({"status": "ok", "config": safe_cfg})

@app.post("/api/toggle")
async def api_toggle_trading(request: Request):
    """Toggle trading on/off. Only writes to config — live script reads config each loop."""
    data = await request.json()
    enabled = data.get('enabled', True)
    cfg = load_config()
    cfg['enabled'] = enabled
    save_config(cfg)
    safe_cfg = {k: v for k, v in cfg.items() if k != 'password'}
    return JSONResponse({"status": "ok", "enabled": enabled, "config": safe_cfg})

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DMR Live Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 20px 30px; border-bottom: 1px solid #2a2a4a; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 1.4rem; color: #00d4ff; }
.header .status { font-size: 0.85rem; color: #888; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.card { background: #12121a; border: 1px solid #2a2a3a; border-radius: 10px; padding: 20px; }
.card h2 { font-size: 1rem; color: #00d4ff; margin-bottom: 15px; border-bottom: 1px solid #2a2a3a; padding-bottom: 10px; }
.card h3 { font-size: 0.9rem; color: #aaa; margin: 10px 0 5px; }
.stat-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #1a1a2a; font-size: 0.9rem; }
.stat-row .label { color: #888; }
.stat-row .value { color: #e0e0e0; font-weight: 500; }
.stat-row .value.green { color: #00ff88; }
.stat-row .value.red { color: #ff4444; }
.stat-row .value.yellow { color: #ffaa00; }
table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
th { text-align: left; padding: 8px 6px; background: #1a1a2e; color: #00d4ff; font-weight: 600; position: sticky; top: 0; }
td { padding: 6px; border-bottom: 1px solid #1a1a2a; }
tr:hover { background: #1a1a2e; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge.green { background: #00ff8820; color: #00ff88; }
.badge.red { background: #ff444420; color: #ff4444; }
.badge.yellow { background: #ffaa0020; color: #ffaa00; }
.badge.blue { background: #00d4ff20; color: #00d4ff; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 0.85rem; color: #888; margin-bottom: 4px; }
.form-group input, .form-group select { width: 100%; padding: 8px 12px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 6px; color: #e0e0e0; font-size: 0.9rem; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: #00d4ff; }
.symbol-list { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
.symbol-tag { display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 6px; font-size: 0.85rem; }
.symbol-tag .remove { cursor: pointer; color: #ff4444; font-weight: bold; }
.symbol-tag .remove:hover { color: #ff6666; }
.btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 600; transition: all 0.2s; }
.btn-primary { background: #00d4ff; color: #0a0a0f; }
.btn-primary:hover { background: #00b8e6; }
.btn-danger { background: #ff4444; color: white; }
.btn-danger:hover { background: #cc3333; }
.btn-success { background: #00ff88; color: #0a0a0f; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.toggle { display: flex; align-items: center; gap: 10px; }
.toggle-switch { position: relative; width: 50px; height: 26px; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #2a2a4a; border-radius: 26px; transition: 0.3s; }
.toggle-slider:before { content: ""; position: absolute; height: 20px; width: 20px; left: 3px; bottom: 3px; background: #e0e0e0; border-radius: 50%; transition: 0.3s; }
.toggle-switch input:checked + .toggle-slider { background: #00d4ff; }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(24px); }
.log-viewer { max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 0.75rem; }
.log-entry { padding: 4px 0; border-bottom: 1px solid #1a1a2a; }
.log-entry .time { color: #666; }
.log-entry .level-info { color: #00d4ff; }
.log-entry .level-error { color: #ff4444; }
.log-entry .level-warn { color: #ffaa00; }
.save-status { font-size: 0.8rem; margin-left: 10px; }
.save-status.ok { color: #00ff88; }
.save-status.err { color: #ff4444; }
@media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
    <h1>🦉 DMR Live Dashboard</h1>
    <div class="status" id="serverStatus">Loading...</div>
</div>
<div class="container">

    <!-- Today's Stats -->
    <div class="grid">
        <div class="card">
            <h2>📊 Today's Activity</h2>
            <div id="todayStats">
                <div class="stat-row"><span class="label">Date</span><span class="value" id="todayDate">—</span></div>
                <div class="stat-row"><span class="label">P90s Detected</span><span class="value yellow" id="p90Count">0</span></div>
                <div class="stat-row"><span class="label">Trades Placed</span><span class="value blue" id="tradeCount">0</span></div>
                <div class="stat-row"><span class="label">Wins</span><span class="value green" id="winCount">0</span></div>
                <div class="stat-row"><span class="label">Losses</span><span class="value red" id="lossCount">0</span></div>
                <div class="stat-row"><span class="label">PnL</span><span class="value" id="pnlValue">$0.00</span></div>
            </div>
        </div>

        <div class="card">
            <h2>⚙️ Quick Controls</h2>
            <div class="form-group">
                <div class="toggle">
                    <label class="toggle-switch">
                        <input type="checkbox" id="tradingEnabled" onchange="toggleTrading()">
                        <span class="toggle-slider"></span>
                    </label>
                    <span id="tradingStatusText">Trading Disabled</span>
                </div>
            </div>
            <div class="form-group">
                <label>Lot Size</label>
                <input type="number" id="lotSize" step="0.01" min="0.01" value="0.02" onchange="updateConfig()">
            </div>
            <div class="form-group">
                <label>Hard Exit Hour (EST)</label>
                <input type="number" id="hardExit" step="1" min="12" max="23" value="17" onchange="updateConfig()">
            </div>
            <div class="form-group">
                <label>Max Daily Trades per Symbol</label>
                <input type="number" id="maxTrades" step="1" min="1" max="10" value="1" onchange="updateConfig()">
            </div>
            <button class="btn btn-primary" onclick="saveConfig()">💾 Save Settings</button>
            <span class="save-status" id="saveStatus"></span>
        </div>
    </div>

    <!-- Symbols -->
    <div class="card" style="margin-bottom:20px">
        <h2>📈 Active Symbols</h2>
        <div class="symbol-list" id="activeSymbols"></div>
        <h3>Add Symbol</h3>
        <div class="form-group">
            <select id="addSymbolSelect">
                <option value="">— Select —</option>
            </select>
        </div>
        <button class="btn btn-primary" onclick="addSymbol()">+ Add</button>
    </div>

    <!-- Trade History -->
    <div class="grid">
        <div class="card">
            <h2>📋 Recent Trades</h2>
            <div style="max-height:300px;overflow-y:auto">
            <table>
                <thead><tr><th>Time</th><th>Symbol</th><th>Dir</th><th>Entry</th><th>Result</th><th>PnL</th></tr></thead>
                <tbody id="tradesTable"></tbody>
            </table>
            </div>
        </div>

        <div class="card">
            <h2>🔔 P90 Events</h2>
            <div style="max-height:300px;overflow-y:auto">
            <table>
                <thead><tr><th>Time</th><th>Symbol</th><th>Dir</th><th>Body</th><th>Trade?</th></tr></thead>
                <tbody id="p90Table"></tbody>
            </table>
            </div>
        </div>
    </div>

    <!-- System Logs -->
    <div class="card" style="margin-top:20px">
        <h2>📝 System Logs</h2>
        <div class="log-viewer" id="logViewer"></div>
    </div>
</div>

<script>
let currentConfig = {};
let availableSymbols = [];

async function fetchStatus() {
    try {
        const r = await fetch('/api/status');
        const d = await r.json();
        currentConfig = d.config;
        availableSymbols = d.available_symbols;
        
        document.getElementById('serverStatus').textContent = `Server: ${d.server_time}`;
        const tradingOn = d.config.enabled;
        document.getElementById('tradingEnabled').checked = tradingOn;
        document.getElementById('tradingStatusText').textContent = tradingOn ? 'Trading Enabled' : 'Trading Disabled';
        document.getElementById('tradingStatusText').style.color = tradingOn ? '#00ff88' : '#ff4444';
        document.getElementById('lotSize').value = d.config.lot_size || 0.02;
        document.getElementById('hardExit').value = d.config.hard_exit_hour_est || 17;
        document.getElementById('maxTrades').value = d.config.max_daily_trades_per_symbol || 1;
        
        // Today stats from state
        const state = d.state;
        document.getElementById('todayDate').textContent = state.today || '—';
        let totalP90 = 0, totalTrades = 0, totalWins = 0, totalLosses = 0, totalPnl = 0;
        if (state.symbols) {
            for (const [sym, s] of Object.entries(state.symbols)) {
                totalP90 += s.p90_count || 0;
                totalTrades += s.trade_count || 0;
                totalWins += s.wins || 0;
                totalLosses += s.losses || 0;
                totalPnl += s.pnl || 0;
            }
        }
        document.getElementById('p90Count').textContent = totalP90;
        document.getElementById('tradeCount').textContent = totalTrades;
        document.getElementById('winCount').textContent = totalWins;
        document.getElementById('lossCount').textContent = totalLosses;
        const pnlEl = document.getElementById('pnlValue');
        pnlEl.textContent = '$' + totalPnl.toFixed(2);
        pnlEl.className = 'value ' + (totalPnl >= 0 ? 'green' : 'red');
        
        // Active symbols
        const activeSyms = d.config.symbols || [];
        const symList = document.getElementById('activeSymbols');
        symList.innerHTML = activeSyms.map(s => {
            const info = availableSymbols.find(a => a.id === s) || {name: s};
            return `<div class="symbol-tag">${info.name} <span class="remove" onclick="removeSymbol('${s}')">×</span></div>`;
        }).join('');
        
        // Add symbol dropdown
        const select = document.getElementById('addSymbolSelect');
        const available = availableSymbols.filter(a => !activeSyms.includes(a.id));
        select.innerHTML = '<option value="">— Select —</option>' + 
            available.map(a => `<option value="${a.id}">${a.name} (WR: ${a.backtest_wr})</option>`).join('');
    } catch(e) {
        document.getElementById('serverStatus').textContent = 'Error: ' + e.message;
    }
}

async function fetchTrades() {
    try {
        const r = await fetch('/api/trades?limit=20');
        const d = await r.json();
        const tbody = document.getElementById('tradesTable');
        tbody.innerHTML = d.trades.map(t => `<tr>
            <td>${t.time ? t.time.substr(11,8) : '—'}</td>
            <td>${t.symbol}</td>
            <td><span class="badge ${t.direction === 'LONG' ? 'green' : t.direction === 'SHORT' ? 'red' : 'blue'}">${t.direction}</span></td>
            <td>${t.entry_price || '—'}</td>
            <td><span class="badge ${t.result === 'W' ? 'green' : t.result === 'L' ? 'red' : 'yellow'}">${t.result}</span></td>
            <td class="${t.pnl_usd > 0 ? 'green' : t.pnl_usd < 0 ? 'red' : ''}">$${t.pnl_usd || 0}</td>
        </tr>`).join('');
    } catch(e) {}
}

async function fetchP90s() {
    try {
        const r = await fetch('/api/p90s?limit=20');
        const d = await r.json();
        const tbody = document.getElementById('p90Table');
        tbody.innerHTML = d.p90s.map(p => `<tr>
            <td>${p.time ? p.time.substr(11,8) : '—'}</td>
            <td>${p.symbol}</td>
            <td><span class="badge ${p.direction === 'LONG' ? 'green' : 'red'}">${p.direction}</span></td>
            <td>${p.body_pips.toFixed(1)}p</td>
            <td><span class="badge ${p.trade_triggered ? 'green' : 'yellow'}">${p.trade_triggered ? 'YES' : 'NO'}</span></td>
        </tr>`).join('');
    } catch(e) {}
}

async function fetchLogs() {
    try {
        const r = await fetch('/api/logs?limit=30');
        const d = await r.json();
        const viewer = document.getElementById('logViewer');
        viewer.innerHTML = d.logs.map(l => `<div class="log-entry">
            <span class="time">${l.timestamp ? l.timestamp.substr(11,8) : ''}</span>
            <span class="level-${l.level.toLowerCase()}">[${l.level}]</span>
            <span>${l.category}:</span> ${l.message}
        </div>`).join('');
    } catch(e) {}
}

async function toggleTrading() {
    const enabled = document.getElementById('tradingEnabled').checked;
    document.getElementById('tradingStatusText').textContent = enabled ? 'Trading Enabled' : 'Trading Disabled';
    // Use dedicated toggle endpoint for immediate state update
    try {
        const r = await fetch('/api/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enabled: enabled})
        });
        const d = await r.json();
        if (d.status === 'ok') {
            // Show visual feedback
            const statusText = document.getElementById('tradingStatusText');
            statusText.textContent = enabled ? 'Trading Enabled' : 'Trading Disabled';
            statusText.style.color = enabled ? '#00ff88' : '#ff4444';
            // Also update the server status to show toggle time
            const toggleTime = new Date().toLocaleTimeString();
            document.getElementById('serverStatus').textContent = `Toggle: ${enabled ? 'ON' : 'OFF'} at ${toggleTime}`;
        }
    } catch(e) {
        console.error('Toggle failed:', e);
    }
}

async function updateConfig() {
    // Debounced auto-save
    clearTimeout(window._saveTimeout);
    window._saveTimeout = setTimeout(saveConfig, 1000);
}

async function updateConfigField(key, value) {
    try {
        await fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({[key]: value})
        });
    } catch(e) {}
}

async function saveConfig() {
    const status = document.getElementById('saveStatus');
    status.textContent = 'Saving...';
    status.className = 'save-status';
    try {
        const data = {
            lot_size: parseFloat(document.getElementById('lotSize').value),
            hard_exit_hour_est: parseInt(document.getElementById('hardExit').value),
            max_daily_trades_per_symbol: parseInt(document.getElementById('maxTrades').value),
            enabled: document.getElementById('tradingEnabled').checked,
            symbols: currentConfig.symbols || []
        };
        const r = await fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const d = await r.json();
        if (d.status === 'ok') {
            status.textContent = '✓ Saved';
            status.className = 'save-status ok';
            currentConfig = d.config;
        } else {
            status.textContent = 'Error';
            status.className = 'save-status err';
        }
    } catch(e) {
        status.textContent = 'Error: ' + e.message;
        status.className = 'save-status err';
    }
    setTimeout(() => { status.textContent = ''; }, 3000);
}

async function addSymbol() {
    const select = document.getElementById('addSymbolSelect');
    const sym = select.value;
    if (!sym) return;
    const syms = [...(currentConfig.symbols || []), sym];
    await updateConfigField('symbols', syms);
    fetchStatus();
}

async function removeSymbol(sym) {
    const syms = (currentConfig.symbols || []).filter(s => s !== sym);
    await updateConfigField('symbols', syms);
    fetchStatus();
}

// Initial load
fetchStatus();
fetchTrades();
fetchP90s();
fetchLogs();

// Auto-refresh every 10s
setInterval(fetchStatus, 10000);
setInterval(fetchTrades, 15000);
setInterval(fetchP90s, 15000);
setInterval(fetchLogs, 20000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")
