#!/usr/bin/env python3
"""
TB Basket Watcher — durable basket open/close alert monitor.

Polls the TB demo runtime every POLL_S seconds and emits ALERT lines for:

    SIGNAL   - new strategy signal observed (z2.5 entry candidate)
    OPEN     - basket opened (heartbeat open_basket_id transition AND/OR
               ledger BASKET_OPEN_VERIFIED event)
    CLOSE    - basket closed (ledger BASKET_CLOSED_VERIFIED event, or
               open_basket_id cleared) with realized PnL delta

Ground truth is the append-only basket ledger (state/tb_control.db, events
table, tracked by monotonic seq) — durable across polls and restarts. The
runtime heartbeat (state/tb_runtime.db) is a secondary signal for the open
transition and live PnL.

Alerts are written to:
    quant-lab/logs/tb_basket_watch.log        (rotating, human-readable)
    quant-lab/state/tb_basket_watch.json      (machine-readable state +
                                               last alert, atomically updated)

Singleton: PID lock at state/tb_basket_watch.pid (tb_proc.PidLock).
Read-only: never writes to the runtime DBs; never touches MT5; never trades.

    python -u quant-lab/runtime/tb_basket_watcher.py
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

QUANT_LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(QUANT_LAB / "runtime"))

from tb_runtime_config import (  # noqa: E402
    STATE_DIR, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    WATCHER_PID_FILE, WATCHER_LOG,
)
from tb_proc import PidLock  # noqa: E402
from tb_telegram import TelegramNotifier  # noqa: E402

POLL_S = 10.0
WATCH_STATE = STATE_DIR / "tb_basket_watch.json"

RUNTIME_DB = STATE_DIR / "tb_runtime.db"
CONTROL_DB = STATE_DIR / "tb_control.db"

OPEN_EVENTS = {"BASKET_OPEN_VERIFIED"}
CLOSE_EVENTS = {"BASKET_CLOSED_VERIFIED"}
SIGNAL_EVENTS = {"SIGNAL_OBSERVED"}

log = logging.getLogger("tb.basketwatch")


def _setup_logging() -> None:
    h = RotatingFileHandler(WATCHER_LOG, maxBytes=LOG_MAX_BYTES,
                            backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(h)
    c = logging.StreamHandler()
    c.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root.addHandler(c)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _q(db: Path, sql: str, args: tuple = ()) -> list:
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10.0)
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(sql, args)]
        finally:
            con.close()
    except sqlite3.Error as e:
        log.warning("db read failed (%s): %s", db.name, e)
        return []


def latest_heartbeat() -> dict | None:
    rows = _q(RUNTIME_DB,
              "SELECT ts,state,open_basket_id,last_signal_time,"
              "today_pnl,today_pnl_pct,open_pnl,deploy_pnl,deploy_pnl_pct,"
              "account_equity FROM runtime_heartbeat ORDER BY ts DESC LIMIT 1")
    return rows[0] if rows else None


def events_after(seq: int) -> list:
    return _q(CONTROL_DB,
              "SELECT seq,event_type,ts_utc,basket_id,strategy_id,"
              "prior_state,new_state,payload,reason "
              "FROM events WHERE seq > ? ORDER BY seq", (seq,))


def max_event_seq() -> int:
    rows = _q(CONTROL_DB, "SELECT COALESCE(MAX(seq),0) AS m FROM events")
    return int(rows[0]["m"]) if rows else 0


def open_baskets() -> list:
    return _q(CONTROL_DB,
              "SELECT basket_id,state,entry_time_utc,entry_basis,entry_z,"
              "direction FROM basket_current")


def load_state() -> dict:
    try:
        return json.loads(WATCH_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(st: dict) -> None:
    tmp = WATCH_STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, indent=2, default=str),
                   encoding="utf-8")
    os.replace(tmp, WATCH_STATE)


def main() -> int:
    lock = PidLock(WATCHER_PID_FILE, "basket-watcher")
    if not lock.try_acquire().get("ok"):
        log.error("singleton held by live pid — exiting")
        return 2

    st = load_state()
    first_run = "last_seq" not in st
    last_seq = int(st.get("last_seq", 0) or 0)
    prev_open = st.get("open_basket_id") or None
    prev_today = float(st.get("today_pnl", 0.0) or 0.0)
    prev_deploy = float(st.get("deploy_pnl", 0.0) or 0.0)

    tg = TelegramNotifier()

    log.info("watcher start pid=%d (first_run=%s, last_seq=%d, "
             "telegram=%s)",
             os.getpid(), first_run, last_seq,
             "armed" if tg.enabled else "disabled")

    # Reconcile on startup: if a basket is already open, say so once (not an
    # OPEN alert — we didn't witness the transition).
    for b in open_baskets():
        if b["state"] not in ("OPEN", "ENTRY", "ENTERED", "OPEN_VERIFIED"):
            continue
        msg = (f"ALREADY_OPEN basket={b['basket_id']} "
               f"state={b['state']} entry_z={b['entry_z']} "
               f"entry_basis={b['entry_basis']}")
        log.info(msg)
        tg.notify(f"👁 TB watcher reattached — basket already open:\n"
                  f"id={b['basket_id']} state={b['state']} "
                  f"z={b['entry_z']} basis={b['entry_basis']}")
        st["already_open"] = {"ts_utc": utcnow_iso(), "basket": dict(b)}
        st["open_basket_id"] = b["basket_id"]

    try:
        while True:
            hb = latest_heartbeat()
            if hb:
                cur_open = hb["open_basket_id"] or None
                cur_today = float(hb["today_pnl"] or 0.0)
                cur_deploy = float(hb["deploy_pnl"] or 0.0)
            else:
                cur_open = prev_open
                cur_today, cur_deploy = prev_today, prev_deploy

            # 1) ledger events — durable ground truth
            for ev in events_after(last_seq):
                last_seq = ev["seq"]
                t, bid, pay = ev["event_type"], ev["basket_id"], ev["payload"]
                try:
                    payload = json.loads(pay) if pay else {}
                except Exception:
                    payload = {}
                if t in SIGNAL_EVENTS:
                    z = payload.get("z_score", payload.get("z", "?"))
                    basis = payload.get("basis", "?")
                    log.info("ALERT SIGNAL ts=%s z=%s basis=%s reason=%s",
                             ev["ts_utc"], z, basis, ev["reason"] or "")
                    tg.notify(f"📡 TB SIGNAL observed\nz={z} basis={basis}\n"
                              f"ts={ev['ts_utc']} basket={bid}")
                    st["last_alert"] = {"type": "SIGNAL", "ts_utc": ev["ts_utc"],
                                        "basket_id": bid,
                                        "z": z, "basis": basis}
                elif t in OPEN_EVENTS:
                    z = payload.get("z_score", payload.get("z", "?"))
                    basis = payload.get("basis", "?")
                    log.info("ALERT OPEN basket=%s ts=%s z=%s basis=%s",
                             bid, ev["ts_utc"], z, basis)
                    tg.notify(f"🔓 TB BASKET OPEN\nid={bid} z={z} "
                              f"basis={basis}\nts={ev['ts_utc']}")
                    st["open_basket_id"] = bid
                    st["last_alert"] = {"type": "OPEN", "ts_utc": ev["ts_utc"],
                                        "basket_id": bid,
                                        "z": z, "basis": basis}
                elif t in CLOSE_EVENTS:
                    pnl = payload.get("pnl", payload.get("realized_pnl",
                                                          "?"))
                    log.info("ALERT CLOSE basket=%s ts=%s pnl=%s reason=%s",
                             bid, ev["ts_utc"], pnl, ev["reason"] or "")
                    tg.notify(f"🔒 TB BASKET CLOSED\nid={bid} pnl={pnl}\n"
                              f"ts={ev['ts_utc']} reason={ev['reason'] or ''}")
                    st["open_basket_id"] = None
                    st["last_alert"] = {"type": "CLOSE", "ts_utc": ev["ts_utc"],
                                        "basket_id": bid, "pnl": pnl}
                else:
                    log.info("event seq=%d type=%s basket=%s reason=%s",
                             ev["seq"], t, bid, ev["reason"] or "")

            # 2) heartbeat open transition (backstop if ledger lags)
            if hb and cur_open and cur_open != prev_open:
                log.info("ALERT OPEN(heartbeat) basket=%s state=%s",
                         cur_open, hb["state"])
                tg.notify(f"🔓 TB BASKET OPEN (heartbeat)\nid={cur_open} "
                          f"state={hb['state']}")
                st["open_basket_id"] = cur_open
                st["last_alert"] = {"type": "OPEN", "ts_utc": utcnow_iso(),
                                    "basket_id": cur_open, "source": "heartbeat"}
            if hb and prev_open and not cur_open:
                log.info("ALERT CLOSE(heartbeat) basket=%s today_pnl=%.2f "
                         "deploy_pnl=%.2f",
                         prev_open, cur_today, cur_deploy)
                tg.notify(f"🔒 TB BASKET CLOSED (heartbeat)\nid={prev_open}\n"
                          f"today_pnl={cur_today:.2f} "
                          f"deploy_pnl={cur_deploy:.2f}")
                st["open_basket_id"] = None
                st["last_alert"] = {"type": "CLOSE", "ts_utc": utcnow_iso(),
                                    "basket_id": prev_open,
                                    "source": "heartbeat",
                                    "today_pnl": cur_today,
                                    "deploy_pnl": cur_deploy}

            prev_open = cur_open
            prev_today, prev_deploy = cur_today, cur_deploy

            st.update({
                "last_poll_utc": utcnow_iso(),
                "last_seq": last_seq,
                "open_basket_id": cur_open,
                "today_pnl": cur_today,
                "deploy_pnl": cur_deploy,
                "heartbeat_state": hb["state"] if hb else None,
                "pid": os.getpid(),
            })
            save_state(st)
            time.sleep(POLL_S)
    except KeyboardInterrupt:
        log.info("watcher stopped by user")
        return 0
    finally:
        lock.release()


if __name__ == "__main__":
    _setup_logging()
    sys.exit(main())
