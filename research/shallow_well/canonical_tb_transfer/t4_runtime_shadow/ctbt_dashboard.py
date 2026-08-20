#!/usr/bin/env python3
"""
CTBT T4.1 — TRANSFER FAMILY READ-ONLY DASHBOARD
================================================

Serves http://127.0.0.1:8766 (localhost ONLY). Reads ONLY the CTBT forward
state: activation seal, forward clock, operator status, and the per-candidate
shadow ledgers + completeness audits. It NEVER scrapes logs, NEVER touches
MT5, and NEVER reads canonical TB data.

STRICTLY READ-ONLY: no controls, no config mutation, no orders, no capital.

Architecture cloned from the canonical TB dashboard (tb_dashboard.py):
same stdlib HTTP server pattern, same dark monospace theme, same status
card / table / health-indicator conventions, same 5s auto-refresh.

    python ctbt_dashboard.py [--port 8766]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

T4_DIR = Path(__file__).resolve().parent
STATE = T4_DIR / "state"

CANONICAL_DASHBOARD_URL = "http://127.0.0.1:8765"

# Frozen historical reference bands (T1.1 dev / T2 2025 confirmation).
# Reference display ONLY — never pooled with forward evidence.
REFERENCE = {
    "EUR_GBP_USD": {
        "dev": {"label": "DEVELOPMENT", "ev": 15.7393, "pf": 5.4152, "wr": 78.16},
        "conf": {"label": "2025 CONFIRMATION", "ev": 17.7550, "pf": 5.5231, "wr": 77.40},
    },
    "GBP_NZD_USD": {
        "dev": {"label": "DEVELOPMENT", "ev": 22.8374, "pf": 8.0184, "wr": 84.29},
        "conf": {"label": "2025 CONFIRMATION", "ev": 11.8681, "pf": 5.8179, "wr": 74.07},
    },
}

STRATEGIES = ["EUR_GBP_USD", "GBP_NZD_USD"]
VERSIONS = {"EUR_GBP_USD": "CTBT-EUR-GBP-USD-v1", "GBP_NZD_USD": "CTBT-GBP-NZD-USD-v1"}
HASHES = {
    "EUR_GBP_USD": "aad0a8e64c6964952eb9129ac2cdebd34d308e6df87ebf45e4584c351044b1a7",
    "GBP_NZD_USD": "5538d63a8acb29883b117fc23c76b1fe389db47ed89009ab3cd258b864f62485",
}
# Observed baseline spreads (points) at activation probe + modeled cost (bps)
OBSERVED_SPREAD_PTS = {"EURGBP.PRO": 2, "EURUSD.PRO": 1, "GBPUSD.PRO": 2,
                       "GBPNZD.PRO": 11, "NZDUSD.PRO": 1}
MODELED_COST_BPS = {"EUR_GBP_USD": 8.056, "GBP_NZD_USD": 8.893}  # frozen conservative contract (2025 basis)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _days_between(a: str, b: str) -> float:
    try:
        ta = datetime.fromisoformat(a.replace("Z", "+00:00"))
        tb = datetime.fromisoformat(b.replace("Z", "+00:00"))
        return max((tb - ta).total_seconds() / 86400.0, 0.0)
    except Exception:
        return 0.0


def load_ledger(tri: str) -> list[dict]:
    p = STATE / f"ledger_{tri}.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_audit(tri: str) -> list[dict]:
    p = STATE / f"ledger_{tri}.audit.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def completeness(tri: str) -> dict:
    counts = {}
    for r in load_audit(tri):
        cls = r.get("classification", "NO_SIGNAL")
        counts[cls] = counts.get(cls, 0) + 1
    total_classified = sum(v for k, v in counts.items()
                           if k != "NO_SIGNAL")
    matched = counts.get("MATCHED_SHADOW", 0) + counts.get("VALID_RUNTIME_BLOCK", 0)
    recognition = (100.0 * matched / total_classified) if total_classified else 100.0
    return {"counts": counts, "total_classified": total_classified,
            "recognition_rate": recognition,
            "warning": counts.get("MISSED_SIGNAL", 0) > 0
                       or counts.get("RUNTIME_ONLY_SIGNAL", 0) > 0}


def performance(tri: str) -> dict:
    """Forward performance. Metrics only when N >= 10 (else INSUFFICIENT)."""
    evs = load_ledger(tri)
    n = len(evs)
    out = {"N": n, "events_per_week": None, "state": "INSUFFICIENT_EVENTS"}
    if n == 0:
        out["state"] = "INSUFFICIENT_EVENTS"
        return out
    # events/week from first to last (or since activation)
    first = evs[0].get("decision_bar_timestamp", "")
    last = evs[-1].get("decision_bar_timestamp", "")
    weeks = max(_days_between(first, last) / 7.0, 1e-9) if first and last else None
    out["events_per_week"] = round(n / weeks, 3) if weeks else None
    if n < 10:
        out["state"] = "INSUFFICIENT_EVENTS"
        return out
    nets = [e.get("net_modeled_bps") or 0.0 for e in evs]
    gross = [e.get("gross_bps") or 0.0 for e in evs]
    import statistics
    wins = [x for x in nets if x > 0]
    losses = [abs(x) for x in nets if x < 0]
    pf = (sum(wins) / sum(losses)) if losses else (float("inf") if wins else 0.0)
    wr = 100.0 * len(wins) / n
    cum = 0.0
    peak = 0.0
    maxdd = 0.0
    streak = best_streak = 0
    for x in nets:
        cum += x
        peak = max(peak, cum)
        maxdd = max(maxdd, peak - cum)
        streak = streak + 1 if x < 0 else 0
        best_streak = max(best_streak, streak)
    out.update({
        "state": "MECHANISM_ALIGNED" if sum(nets) > 0 else "MECHANISM_WEAKENED",
        "gross_ev": round(statistics.mean(gross), 4),
        "net_modeled_ev": round(statistics.mean(nets), 4),
        "wr": round(wr, 2),
        "median_ev": round(statistics.median(nets), 4),
        "pf": round(pf, 3),
        "max_dd": round(maxdd, 2),
        "p5": round(sorted(nets)[max(0, int(0.05 * n) - 1)], 3),
        "worst": round(min(nets), 3),
        "worst_streak": best_streak,
        "avg_hold": round(statistics.mean([e.get("hold_minutes") or 0 for e in evs]), 1),
        "z6_rate": round(100.0 * sum(1 for e in evs if e.get("exit_reason") == "SL_HIT") / n, 2),
        "hard_exit_rate": round(100.0 * sum(1 for e in evs if e.get("exit_reason") == "TIMEOUT") / n, 2),
    })
    return out


def cost_health(tri: str) -> dict:
    evs = load_ledger(tri)
    observed = [e.get("observed_quote_crossing_cost_bps") for e in evs
                if e.get("observed_quote_crossing_cost_bps")]
    dist = {}
    if observed:
        import statistics
        s = sorted(observed)
        def q(p):
            return s[min(len(s) - 1, int(p * len(s)))]
        dist = {"median": round(statistics.median(s), 3),
                "p75": round(q(0.75), 3), "p90": round(q(0.90), 3), "p95": round(q(0.95), 3)}
    mult = None
    if observed and MODELED_COST_BPS.get(tri):
        mult = round(statistics.median(observed) / MODELED_COST_BPS[tri], 3)
    state = "COST_MARGIN_HEALTHY"
    return {"modeled_cost_bps": MODELED_COST_BPS.get(tri),
            "observed_n": len(observed), "distribution": dist,
            "observed_model_multiple": mult, "state": state}


def strategy_status(tri: str, seal: dict, clock: dict, op: dict) -> dict:
    n = len(load_ledger(tri))
    comp = completeness(tri)
    perf = performance(tri)
    cost = cost_health(tri)
    canary = {
        "event_condition": n >= 10,
        "time_condition": (clock.get("elapsed_days") or 0) >= 28,
        "eligible": n >= 10 and (clock.get("elapsed_days") or 0) >= 28,
    }
    return {
        "strategy": tri,
        "version": VERSIONS[tri],
        "hash": HASHES[tri],
        "forward_state": "FORWARD_SHADOW_ONLY",
        "events": n,
        "events_per_week": perf["events_per_week"],
        "performance_state": perf["state"],
        "performance": perf,
        "completeness": comp,
        "cost": cost,
        "canary": canary,
        "horizons": {"early_diagnostic": 15, "minimum_useful": 30, "preferred": 50},
        "reference": REFERENCE[tri],
        "recent_events": sorted(load_ledger(tri),
                                key=lambda e: e.get("decision_bar_timestamp", ""),
                                reverse=True)[:25],
    }


def build_status() -> dict:
    seal = _read_json(T4_DIR / "CTBT_T4_ACTIVATION_SEAL.json", {})
    clock = _read_json(T4_DIR / "CTBT_T4_FORWARD_CLOCK.json", {})
    op = _read_json(T4_DIR / "CTBT_T4_OPERATOR_STATUS.json", {})
    active = seal.get("status") == "ACTIVE"
    return {
        "header": {
            "forward_state": "FORWARD SHADOW ACTIVE" if active else "PENDING",
            "provider": "Ox Securities MT5 Demo",
            "mode": "READ ONLY",
            "execution": "DISABLED",
            "capital": "DISABLED",
        },
        "clock": {
            "activation_timestamp": seal.get("activation_timestamp_utc"),
            "days_elapsed": clock.get("elapsed_days", 0),
            "first_eligible_bar": seal.get("first_eligible_m5_bar"),
            "authoritative": clock.get("authoritative", False),
        },
        "operator": op,
        "system_health": {
            "collector_running": bool(op.get("collector_running")),
            "collector_pid": op.get("collector_pid"),
            "provider_connected": bool(op.get("provider_connected")),
            "last_bar": (op.get("last_bar_timestamp") or {}),
            "last_heartbeat": op.get("last_heartbeat_utc"),
            "recognition_rate": op.get("signal_recognition_rate"),
            "order_prevention_pass": bool(op.get("order_prevention_pass")),
            "data_freshness": op.get("dashboard_data_freshness"),
        },
        "strategies": {tri: strategy_status(tri, seal, clock, op) for tri in STRATEGIES},
        "canonical_dashboard": CANONICAL_DASHBOARD_URL,
        "server_utc": _now(),
        "read_only": True,
        "zero_events_note": "0 EVENT / WAITING FOR NATURAL SIGNAL",
    }


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>QUANT BOX / TB — Transfer Family</title>
<style>
body{font-family:monospace;background:#101418;color:#d7e0e8;margin:24px}
h1{font-size:18px}h2{font-size:15px;margin:16px 0 6px}
.card{background:#171d24;border:1px solid #2a3441;border-radius:6px;
padding:14px 18px;margin:10px 0;max-width:760px}
.k{color:#7f96a8}.v{color:#e8f1f8;font-weight:bold}
.ok{color:#4ade80}.warn{color:#fbbf24}.bad{color:#f87171}
table{border-collapse:collapse;width:100%}td,th{padding:3px 12px 3px 0;text-align:left}
th{color:#7f96a8;font-weight:normal;border-bottom:1px solid #2a3441}
.nav a{color:#7f96a8;margin-right:18px;text-decoration:none}
.nav a.sel{color:#4ade80;font-weight:bold}
.banner{background:#1a2330;border:1px solid #2a5a3a;border-radius:6px;
padding:10px 18px;margin:10px 0;max-width:760px}
.tag{display:inline-block;padding:2px 8px;border-radius:4px;margin-right:8px}
.tag.green{background:#14332a;color:#4ade80}.tag.red{background:#3a1414;color:#f87171}
.tag.yellow{background:#3a2f14;color:#fbbf24}
</style></head><body>
<h1>QUANT BOX / TB — TRANSFER FAMILY <span id="st"></span></h1>
<div class="nav">
<a href="#" data-tab="overview" class="sel">FAMILY OVERVIEW</a>
<a href="#" data-tab="EUR_GBP_USD">EUR / GBP / USD</a>
<a href="#" data-tab="GBP_NZD_USD">GBP / NZD / USD</a>
<a href="#" data-tab="canonical">CANONICAL TB</a>
</div>
<div id="c"><i>loading…</i></div>
<script>
let D=null;
const nav=document.querySelectorAll('.nav a');
function setTab(tab){location.hash='tab='+tab;
 nav.forEach(x=>x.classList.toggle('sel',x.dataset.tab===tab));render(tab);}
nav.forEach(a=>a.addEventListener('click',e=>{e.preventDefault();setTab(a.dataset.tab);}));
async function load(){try{const r=await fetch('/api/status');D=await r.json();
 const st=document.getElementById('st');
 st.textContent='['+D.header.forward_state+']';
 st.className=D.header.forward_state==='FORWARD SHADOW ACTIVE'?'ok':'warn';
 const want=(location.hash.match(/tab=(\w+)/)||[])[1]||'overview';
 const tab=[...nav].some(a=>a.dataset.tab===want)?want:'overview';
 nav.forEach(x=>x.classList.toggle('sel',x.dataset.tab===tab));render(tab);
}catch(e){document.getElementById('c').innerHTML='<span class="bad">dashboard read error</span>';}}
function bar(x,total){const p=Math.min(100,100*x/total);return '<div style="background:#101418;border:1px solid #2a3441;border-radius:3px;width:100%;height:10px"><div style="background:#4ade80;width:'+p+'%;height:10px;border-radius:3px"></div></div>';}
function hdr(){const h=D.header;return '<div class="banner"><span class="tag green">'+h.forward_state+'</span>'+
 'PROVIDER <span class="v">'+h.provider+'</span> | MODE <span class="v">'+h.mode+'</span> | '+
 'EXECUTION <span class="tag red">'+h.execution+'</span> CAPITAL <span class="tag red">'+h.capital+'</span></div>';}
function clockPanel(c){return '<div class="card"><h2>FORWARD CLOCK</h2><table>'+
 '<tr><td class="k">ACTIVATION</td><td class="v">'+(c.activation_timestamp||'n/a')+'</td></tr>'+
 '<tr><td class="k">DAYS ELAPSED</td><td class="v">'+c.days_elapsed.toFixed(4)+'</td></tr>'+
 '<tr><td class="k">FIRST ELIGIBLE M5 BAR</td><td class="v">'+(c.first_eligible_bar||'n/a')+'</td></tr>'+
 '<tr><td class="k">AUTHORITATIVE</td><td class="v">'+(c.authoritative?'YES':'NO')+'</td></tr></table></div>';}
function healthPanel(h){return '<div class="card"><h2>SYSTEM HEALTH</h2><table>'+
 '<tr><td class="k">COLLECTOR</td><td class="v '+(h.collector_running?'ok':'bad')+'">'+(h.collector_running?'RUNNING (pid '+h.collector_pid+')':'STOPPED')+'</td></tr>'+
 '<tr><td class="k">PROVIDER</td><td class="v '+(h.provider_connected?'ok':'bad')+'">'+(h.provider_connected?'CONNECTED':'OFFLINE')+'</td></tr>'+
 '<tr><td class="k">LAST M5 BAR</td><td class="v">'+((h.last_bar&&h.last_bar.EUR_GBP_USD)||'n/a')+'</td></tr>'+
 '<tr><td class="k">LAST HEARTBEAT</td><td class="v">'+(h.last_heartbeat||'n/a')+'</td></tr>'+
 '<tr><td class="k">RECOGNITION RATE</td><td class="v '+(h.recognition_rate>=100?'ok':'warn')+'">'+(h.recognition_rate||0)+'%</td></tr>'+
 '<tr><td class="k">ORDER PREVENTION</td><td class="v '+(h.order_prevention_pass?'ok':'bad')+'">'+(h.order_prevention_pass?'PASS':'FAIL')+'</td></tr></table></div>';}
function completenessPanel(c){const cs=c.counts||{};const warn=c.warning;
 return '<div class="card"><h2>SIGNAL COMPLETENESS</h2><table>'+
 '<tr><td class="k">MATCHED_SHADOW</td><td class="v ok">'+(cs.MATCHED_SHADOW||0)+'</td></tr>'+
 '<tr><td class="k">VALID_RUNTIME_BLOCK</td><td class="v">'+(cs.VALID_RUNTIME_BLOCK||0)+'</td></tr>'+
 '<tr><td class="k">MISSED_SIGNAL</td><td class="v '+(cs.MISSED_SIGNAL?'bad':'')+'">'+(cs.MISSED_SIGNAL||0)+'</td></tr>'+
 '<tr><td class="k">RUNTIME_ONLY_SIGNAL</td><td class="v '+(cs.RUNTIME_ONLY_SIGNAL?'bad':'')+'">'+(cs.RUNTIME_ONLY_SIGNAL||0)+'</td></tr>'+
 '<tr><td class="k">DATA_DIVERGENCE</td><td class="v '+(cs.DATA_DIVERGENCE?'warn':'')+'">'+(cs.DATA_DIVERGENCE||0)+'</td></tr>'+
 '<tr><td class="k">NO_SIGNAL</td><td class="v">'+(cs.NO_SIGNAL||0)+'</td></tr>'+
 '<tr><td class="k">RECOGNITION RATE</td><td class="v '+(c.recognition_rate>=100?'ok':'warn')+'">'+c.recognition_rate+'% (TARGET 100%)</td></tr></table>'+
 (warn?'<p class="bad">ENGINEERING WARNING: MISSED_SIGNAL or RUNTIME_ONLY_SIGNAL present — investigate.</p>':'')+'</div>';}
function costPanel(c){const d=c.distribution||{};
 return '<div class="card"><h2>BROKER REALITY</h2><table>'+
 '<tr><td class="k">HISTORICAL MODELED BASKET COST</td><td class="v">'+(c.modeled_cost_bps!=null?c.modeled_cost_bps+' bps':'n/a')+'</td></tr>'+
 '<tr><td class="k">OBSERVED SIGNAL-TIME CROSSING</td><td class="v">'+(c.observed_n>0?'n='+c.observed_n:'NOT_AVAILABLE (0 signals)')+'</td></tr>'+
 '<tr><td class="k">COST DISTRIBUTION</td><td class="v">'+(d.median?'med '+d.median+' / p75 '+d.p75+' / p90 '+d.p90+' / p95 '+d.p95+' bps':'—')+'</td></tr>'+
 '<tr><td class="k">OBSERVED/MODELED MULTIPLE</td><td class="v">'+(c.observed_model_multiple!=null?c.observed_model_multiple:'—')+'</td></tr>'+
 '<tr><td class="k">COST HEALTH</td><td class="v ok">'+c.state+'</td></tr></table></div>';}
function canaryPanel(k,events){const ev=k.event_condition?'ok':'warn';const tm=k.time_condition?'ok':'warn';
 return '<div class="card"><h2>DEMO-CANARY REVIEW PROGRESS</h2><table>'+
 '<tr><td class="k">EVENT CONDITION</td><td class="v '+ev+'">'+events+' / 10 clean forward events</td></tr>'+
 '<tr><td class="k">TIME CONDITION</td><td class="v '+tm+'">'+Math.floor(D.clock.days_elapsed)+' / 28 days</td></tr>'+
 '<tr><td class="k">ELIGIBILITY</td><td class="v '+(k.eligible?'ok':'warn')+'">'+(k.eligible?'DEMO_CANARY_REVIEW_ELIGIBLE':'NOT ELIGIBLE')+'</td></tr>'+
 '<tr><td class="k">NOTE</td><td class="k">eligibility ≠ FORWARD VALIDATED / LIVE READY / PRODUCTION READY; demo orders require SW-CTBT-T5 + human authorization</td></tr></table></div>';}
function perfPanel(p){if(p.state==='INSUFFICIENT_EVENTS'){
 return '<div class="card"><h2>FORWARD PERFORMANCE</h2><p class="warn">INSUFFICIENT EVENTS (N='+p.N+') — metrics withheld until N>=10.</p>'+
 (p.events_per_week?'<p class="k">EVENT RATE: '+p.events_per_week+'/week</p>':'')+'</div>';}
 return '<div class="card"><h2>FORWARD PERFORMANCE (N='+p.N+')</h2><table>'+
 '<tr><td class="k">GROSS EV</td><td class="v">'+p.gross_ev+' bps</td></tr>'+
 '<tr><td class="k">NET MODELED EV</td><td class="v '+(p.net_modeled_ev>0?'ok':'bad')+'">'+p.net_modeled_ev+' bps</td></tr>'+
 '<tr><td class="k">WIN RATE</td><td class="v">'+p.wr+'%</td></tr>'+
 '<tr><td class="k">MEDIAN EV</td><td class="v">'+p.median_ev+' bps</td></tr>'+
 '<tr><td class="k">PF</td><td class="v">'+(p.pf===Infinity?'inf':p.pf)+'</td></tr>'+
 '<tr><td class="k">MAX DD</td><td class="v">'+p.max_dd+' bps</td></tr>'+
 '<tr><td class="k">p5 / WORST</td><td class="v">'+p.p5+' / '+p.worst+' bps</td></tr>'+
 '<tr><td class="k">LOSING STREAK</td><td class="v">'+p.worst_streak+'</td></tr>'+
 '<tr><td class="k">AVG HOLD</td><td class="v">'+p.avg_hold+' min</td></tr>'+
 '<tr><td class="k">z6 / HARD-EXIT RATE</td><td class="v">'+p.z6_rate+'% / '+p.hard_exit_rate+'%</td></tr></table>'+
 '<p class="k">MECHANISM STATE: <span class="'+(p.state==='MECHANISM_ALIGNED'?'ok':'warn')+'">'+p.state+'</span> (evidence display only)</p></div>';}
function refPanel(r){return '<div class="card"><h2>HISTORICAL REFERENCE (NOT pooled)</h2><table>'+
 '<tr><th></th><th>'+r.dev.label+'</th><th>'+r.conf.label+'</th><th>FORWARD</th></tr>'+
 '<tr><td class="k">EV (bps)</td><td class="v">'+r.dev.ev+'</td><td class="v">'+r.conf.ev+'</td><td class="v">prospective</td></tr>'+
 '<tr><td class="k">PF</td><td class="v">'+r.dev.pf+'</td><td class="v">'+r.conf.pf+'</td><td class="v">prospective</td></tr>'+
 '<tr><td class="k">WR %</td><td class="v">'+r.dev.wr+'</td><td class="v">'+r.conf.wr+'</td><td class="v">prospective</td></tr></table></div>';}
function horizonPanel(s){const h=s.horizons;return '<div class="card"><h2>FORWARD EVIDENCE HORIZONS</h2><table>'+
 '<tr><td class="k">10 — DEMO-CANARY REVIEW</td><td>'+bar(Math.min(s.events,10),10)+'</td><td class="v">'+s.events+'/10</td></tr>'+
 '<tr><td class="k">15 — EARLY DIAGNOSTIC</td><td>'+bar(Math.min(s.events,15),15)+'</td><td class="v">'+s.events+'/15</td></tr>'+
 '<tr><td class="k">30 — MINIMUM USEFUL</td><td>'+bar(Math.min(s.events,30),30)+'</td><td class="v">'+s.events+'/30</td></tr>'+
 '<tr><td class="k">50 — PREFERRED</td><td>'+bar(Math.min(s.events,50),50)+'</td><td class="v">'+s.events+'/50</td></tr></table></div>';}
function eventsTable(evs){if(!evs.length){return '<div class="card"><h2>RECENT EVENTS</h2><p class="k">'+D.zero_events_note+'</p></div>';}
 let h='<div class="card"><h2>RECENT EVENTS</h2><table><tr><th>ENTRY</th><th>EXIT</th><th>DIR</th><th>Z IN</th><th>Z OUT</th><th>REASON</th><th>GROSS</th><th>NET</th><th>HOLD</th><th>COMPLETENESS</th></tr>';
 for(const e of evs){h+='<tr><td>'+e.decision_bar_timestamp+'</td><td>'+e.exit_timestamp+'</td><td>'+e.direction+'</td><td>'+e.entry_z+'</td><td>'+e.exit_z+'</td><td>'+e.exit_reason+'</td><td>'+(e.gross_bps!=null?e.gross_bps.toFixed(1):'')+'</td><td>'+(e.net_modeled_bps!=null?e.net_modeled_bps.toFixed(1):'')+'</td><td>'+(e.hold_minutes!=null?e.hold_minutes+'m':'')+'</td><td>'+(e.completeness_classification||'PENDING_AUDIT')+'</td></tr>';}
 return h+'</table></div>';}
function strategyPage(tri){const s=D.strategies[tri];const c=D.clock;
 return hdr()+clockPanel(c)+
 '<div class="card"><h2>'+tri+' — '+s.version+'</h2><table>'+
 '<tr><td class="k">STRATEGY HASH</td><td class="v">'+s.hash.slice(0,20)+'…</td></tr>'+
 '<tr><td class="k">FORWARD STATE</td><td class="v ok">'+s.forward_state+'</td></tr>'+
 '<tr><td class="k">EVENTS</td><td class="v">'+s.events+' (0 EVENT / WAITING FOR NATURAL SIGNAL if zero)</td></tr></table></div>'+
 canaryPanel(s.canary,s.events)+horizonPanel(s)+perfPanel(s.performance)+refPanel(s.reference)+
 costPanel(s.cost)+completenessPanel(s.completeness)+eventsTable(s.recent_events);}
function overview(){let h=hdr()+clockPanel(D.clock)+healthPanel(D.system_health);
 for(const tri of Object.keys(D.strategies)){const s=D.strategies[tri];
 h+='<div class="card"><h2>'+tri+' <span class="k">('+s.version+')</span></h2><table>'+
 '<tr><td class="k">STATE</td><td class="v ok">'+s.forward_state+'</td></tr>'+
 '<tr><td class="k">EVENTS</td><td class="v">'+s.events+'</td></tr>'+
 '<tr><td class="k">DEMO-CANARY</td><td class="v '+(s.canary.eligible?'ok':'warn')+'">'+(s.canary.eligible?'DEMO_CANARY_REVIEW_ELIGIBLE':'NOT ELIGIBLE')+'</td></tr>'+
 '<tr><td class="k">RECOGNITION</td><td class="v">'+s.completeness.recognition_rate+'%</td></tr></table></div>';}
 return h+'<p class="k">Evidence isolated per strategy. No combined PnL / PF / EV. No portfolio inference.</p>';}
function render(tab){const c=document.getElementById('c');
 if(tab==='canonical'){c.innerHTML='<div class="card"><h2>CANONICAL TB</h2><p class="k">Canonical AUD_GBP_NZD evidence and runtime are separate and unchanged.</p>'+
 '<p>Open the existing canonical dashboard: <a href="'+D.canonical_dashboard+'" style="color:#4ade80">'+D.canonical_dashboard+'</a></p></div>';return;}
 if(tab==='overview'){c.innerHTML=overview();return;}
 c.innerHTML=strategyPage(tab);}
load();setInterval(load,5000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):  # noqa: N802
        try:
            if self.path.split("?")[0] in ("/api/status", "/api/health"):
                body = json.dumps(build_status(), default=str).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                body = HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:  # pragma: no cover
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            except Exception:
                pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"CTBT TRANSFER DASHBOARD http://127.0.0.1:{args.port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
