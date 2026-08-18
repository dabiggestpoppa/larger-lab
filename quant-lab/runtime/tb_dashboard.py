#!/usr/bin/env python3
"""
TB-R6.1 — READ-ONLY LOCAL MONITOR DASHBOARD
===========================================

Serves http://127.0.0.1:8765 (localhost ONLY). Reads the durable runtime DB
(existing SQLite, WAL) — it NEVER scrapes logs and NEVER touches MT5.

STRICTLY READ-ONLY: no buy/sell/close/force controls, no config mutation.
Operational control stays with tbctl / the OS service.

    python -u quant-lab/runtime/tb_dashboard.py [--port 8765]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from pathlib import Path

QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB / "runtime"))

from tb_runtime_config import (  # noqa: E402
    DASHBOARD_HOST, DASHBOARD_PORT, HEARTBEAT_GREEN_MAX_S,
    HEARTBEAT_YELLOW_MAX_S, DASHBOARD_LOG, DASHBOARD_PID_FILE,
    LOG_MAX_BYTES, LOG_BACKUP_COUNT, RUNNING, STOPPED_BY_USER,
)
from tb_runtime_db import RuntimeDB  # noqa: E402
from tb_proc import PidLock, pid_alive  # noqa: E402

log = logging.getLogger("tb.dashboard")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fmt_age(seconds) -> str:
    if seconds is None:
        return "n/a"
    if seconds < 60:
        return f"{seconds:.0f}s ago"
    if seconds < 3600:
        return f"{seconds/60:.1f}m ago"
    return f"{seconds/3600:.1f}h ago"


def _fmt_pnl(v: float) -> str:
    return f"${v:,.2f}"


def build_status(rdb: RuntimeDB) -> dict:
    hb = rdb.latest_heartbeat()
    desired = rdb.desired_state()
    age = rdb.heartbeat_age_s()

    # ENGINE STATUS: ONLINE / DEGRADED / OFFLINE / STOPPED
    if desired == STOPPED_BY_USER:
        engine = "STOPPED"
    elif hb is None:
        engine = "OFFLINE"
    elif age is None or age > HEARTBEAT_YELLOW_MAX_S:
        engine = "OFFLINE"
    elif age > HEARTBEAT_GREEN_MAX_S:
        engine = "DEGRADED"
    else:
        engine = "ONLINE"

    worker_state = hb["state"] if hb else ""

    # STRATEGY STATE: WAITING / FLAT / OPEN / EXIT_PENDING /
    #                 RECOVERY_REQUIRED / BLOCKED
    if worker_state.startswith("BLOCKED"):
        strat = "BLOCKED"
    elif worker_state in ("RECONCILIATION_REQUIRED", "OPEN_VERIFIED"):
        strat = "RECOVERY_REQUIRED" if "RECONCILIATION" in worker_state else "OPEN"
    elif hb and hb["open_basket_id"]:
        strat = "OPEN"
    elif worker_state in ("FLAT",):
        strat = "FLAT"
    elif worker_state in ("ONLINE_MARKET_CLOSED", "WAITING_FOR_MT5",
                          "DEGRADED_DISK", "DEGRADED", "DEGRADED_ERROR"):
        strat = "WAITING"
    else:
        strat = "WAITING"

    mt5 = bool(hb and hb["mt5_connected"])
    gate = bool(hb and hb["account_gate"])
    market_open = bool(hb and hb["market_open"])

    # uptime from worker start / deployment
    dep_ts = rdb.get_status("deployment_start_timestamp", "")
    up_secs = None
    try:
        if dep_ts:
            d = datetime.fromisoformat(dep_ts)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            up_secs = (datetime.now(timezone.utc) - d).total_seconds()
    except Exception:
        pass

    errs = rdb.recent_errors(1)
    return {
        "engine_status": engine,
        "uptime_s": up_secs,
        "uptime": _fmt_age(up_secs) if up_secs is not None else "n/a",
        "last_heartbeat": hb["ts"] if hb else "",
        "heartbeat_age_s": age,
        "heartbeat_age": _fmt_age(age) if age is not None else "n/a",
        "worker_pid": hb["pid"] if hb else None,
        "worker_state": worker_state,
        "desired_state": desired,
        "mt5_status": "CONNECTED" if mt5 else ("DEGRADED" if hb else "OFFLINE"),
        "account_gate": "PASS" if gate else "FAIL",
        "strategy_state": strat,
        "market_open": market_open,
        "last_closed_bar": hb["last_closed_bar"] if hb else "",
        "last_signal_time": hb["last_signal_time"] if hb else "",
        "open_basket": (hb["open_basket_id"] if hb and hb["open_basket_id"]
                        else "NO"),
        "open_basket_pnl": (hb["open_pnl"] if hb else 0.0),
        "today_tb_pnl": (hb["today_pnl"] if hb else 0.0),
        "today_tb_pnl_pct": (hb["today_pnl_pct"] if hb else 0.0),
        "deploy_tb_pnl": (hb["deploy_pnl"] if hb else 0.0),
        "deploy_tb_pnl_pct": (hb["deploy_pnl_pct"] if hb else 0.0),
        "account_equity": (hb["account_equity"] if hb else 0.0),
        "disk_free_gb": (hb["disk_free_gb"] if hb else 0.0),
        "last_error": (errs[0]["message"] if errs else "none"),
        "last_error_ts": (errs[0]["ts"] if errs else ""),
        "read_only": True,
        "server_utc": _now(),
    }


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>TB Demo Runtime</title>
<meta http-equiv="refresh" content="5">
<style>
body{font-family:monospace;background:#101418;color:#d7e0e8;margin:24px}
h1{font-size:18px}.card{background:#171d24;border:1px solid #2a3441;border-radius:6px;
padding:14px 18px;margin:10px 0;max-width:640px}
.k{color:#7f96a8}.v{color:#e8f1f8;font-weight:bold}
.ok{color:#4ade80}.warn{color:#fbbf24}.bad{color:#f87171}
table{border-collapse:collapse}td{padding:3px 12px 3px 0}
</style></head><body>
<h1>TB Triangular Basis — Demo Runtime <span id="st"></span></h1>
<div class="card" id="c"><i>loading…</i></div>
<script>
const E=['engine_status','uptime','last_heartbeat','heartbeat_age','worker_pid',
'worker_state','desired_state','mt5_status','account_gate','strategy_state',
'market_open','last_closed_bar','last_signal_time','open_basket',
'today_tb_pnl','today_tb_pnl_pct','open_basket_pnl',
'deploy_tb_pnl','deploy_tb_pnl_pct','account_equity',
'disk_free_gb','last_error'];
const LBL={engine_status:'ENGINE',uptime:'UPTIME',last_heartbeat:'LAST HEARTBEAT',
heartbeat_age:'HEARTBEAT',worker_pid:'WORKER PID',worker_state:'WORKER STATE',
desired_state:'DESIRED',mt5_status:'MT5',account_gate:'ACCOUNT GATE',
strategy_state:'STRATEGY',market_open:'MARKET',last_closed_bar:'LAST M5 BAR',
last_signal_time:'LAST SIGNAL',open_basket:'OPEN BASKET',
today_tb_pnl:'TODAY TB PNL $',today_tb_pnl_pct:'TODAY TB RETURN %',
open_basket_pnl:'OPEN BASKET PNL $',deploy_tb_pnl:'TB SINCE DEPLOY $',
deploy_tb_pnl_pct:'TB SINCE DEPLOY %',account_equity:'ACCOUNT EQUITY',
disk_free_gb:'FREE DISK GB',last_error:'LAST ERROR'};
const FMT={today_tb_pnl:v=>'$'+v.toFixed(2),today_tb_pnl_pct:v=>v.toFixed(3)+'%',
open_basket_pnl:v=>'$'+v.toFixed(2),deploy_tb_pnl:v=>'$'+v.toFixed(2),
deploy_tb_pnl_pct:v=>v.toFixed(3)+'%',account_equity:v=>'$'+v.toFixed(2),
disk_free_gb:v=>v.toFixed(2)};
async function load(){try{
 const r=await fetch('/api/status');const d=await r.json();
 const st=document.getElementById('st');
 st.textContent='['+d.engine_status+']';
 st.className=d.engine_status==='ONLINE'?'ok':(d.engine_status==='DEGRADED'?'warn':'bad');
 let h='<table>';
 for(const k of E){const v=d[k];const disp=(FMT[k]?FMT[k](v):v);
  let cls='';if(k==='engine_status')cls=d.engine_status==='ONLINE'?'ok':(d.engine_status==='DEGRADED'?'warn':'bad');
  if(k==='account_gate')cls=v==='PASS'?'ok':'bad';
  if(k==='mt5_status')cls=v==='CONNECTED'?'ok':'warn';
  h+='<tr><td class="k">'+LBL[k]+'</td><td class="v '+cls+'">'+disp+'</td></tr>';}
 h+='</table><p class="k">READ-ONLY — operational control via tbctl only.</p>';
 document.getElementById('c').innerHTML=h;
}catch(e){document.getElementById('c').innerHTML='<span class="bad">dashboard read error</span>';}}
load();setInterval(load,5000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):  # noqa: N802
        try:
            rdb = RuntimeDB()
            try:
                if self.path.split("?")[0] in ("/api/status", "/api/health"):
                    body = json.dumps(build_status(rdb)).encode()
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
            finally:
                rdb.close()
        except Exception as e:  # pragma: no cover
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            except Exception:
                pass


def main() -> int:
    lock = PidLock(DASHBOARD_PID_FILE, "dashboard")
    got = lock.try_acquire()
    if not got["ok"]:
        print(f"SINGLETON_BLOCKED: {got['reason']}", flush=True)
        return 2
    try:
        ap = argparse.ArgumentParser()
        ap.add_argument("--port", type=int, default=DASHBOARD_PORT)
        args = ap.parse_args()
        h = RotatingFileHandler(DASHBOARD_LOG, maxBytes=LOG_MAX_BYTES,
                                backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(h)
        logging.getLogger().setLevel(logging.INFO)
        srv = ThreadingHTTPServer((DASHBOARD_HOST, args.port), Handler)
        log.info("dashboard on http://%s:%d", DASHBOARD_HOST, args.port)
        print(f"DASHBOARD http://{DASHBOARD_HOST}:{args.port}", flush=True)
        srv.serve_forever()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
