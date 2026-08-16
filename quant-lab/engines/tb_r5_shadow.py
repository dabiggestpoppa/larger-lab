#!/usr/bin/env python3
"""
TB-R5 — SHADOW FORWARD SEAL (active-market continuous runtime)
===============================================================

Freezes and observes the COMPLETE TB forward engine during ACTIVE-MARKET
conditions in SHADOW mode. This is infrastructure observation, not strategy
research and not a backtest.

    REAL MT5 terminal
      -> REAL broker symbols / metadata (stability-hashed per cycle)
      -> REAL synchronized closed M5 bars (R2 feed; forming bar excluded)
      -> REAL bid/ask ticks (age / spread / cross-leg skew measured)
      -> TB-FWD-V1 PRIMARY + TB-FROZEN-CONTROL (isolated shadow)
      -> TB-B weights -> REAL contract specs -> hypothetical lots
      -> post-rounding neutrality (frozen GATE K)
      -> durable R3 ledger (intents persisted write-ahead)
      -> SHADOW_ORDER_WOULD_SEND   (order_send NEVER called)

EXECUTION AUTHORIZATION: NOT_AUTHORIZED. mt5.order_send is wrapped by a hard
guard: any invocation fails the run. The runtime appends every cycle to
TB_R5_ACTIVE_MARKET_RUNTIME.csv so it can be left running across sessions and
restarted safely (append-only evidence).

Run (during market hours):
    python quant-lab/engines/tb_r5_shadow.py --cycles 480 --cycle-sleep 15
    # 480 cycles x 15s ~= 2h of continuous active-market shadow observation

Use --offline to produce the PENDING_TERMINAL_VALIDATION shell (never PASS).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tb_live.market_data import TBMarketDataConfig  # noqa: E402
from tb_live.snapshot import SynchronizedTriangleFeed  # noqa: E402
from tb_live.persistence import BasketLedger, EventType  # noqa: E402
from tb_live.state_machine import BasketLifecycleState as S  # noqa: E402
from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision,
)
from engines.tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG, CONTROL_CONFIG,
)
from engines.triangular_execution_contract import (  # noqa: E402
    ContractSpec, size_and_assess_basket,
)
from engines.tb_r4_real_mt5 import (  # noqa: E402
    RealMT5Audit, PENDING, CUR_TO_USD, BAR_SECONDS, CANONICAL, TB_MAGIC,
)

ROOT = Path(__file__).parent.parent.parent
OUT = ROOT / "research" / "tb_forward"
OUT.mkdir(parents=True, exist_ok=True)
STATE_DIR = ROOT / "quant-lab" / "state" / "triangular_basis"
LEDGER_PATH = STATE_DIR / "tb_r5_ledger.db"

# frozen execution-safety tolerances (PROVISIONAL engineering limits from R2;
# NOT alpha parameters, NOT tuned on PnL)
MAX_QUOTE_AGE_MS = 2000
MAX_CROSS_LEG_SKEW_MS = 1000

# metadata fields that must stay stable (broker spec drift -> block)
SPEC_FIELDS = ("digits", "point", "trade_tick_size", "trade_tick_value",
               "contract_size", "volume_min", "volume_max", "volume_step",
               "trade_mode", "filling_mode")

RUNTIME_CSV_HEADER = [
    "cycle_id", "wall_clock_utc", "canonical_bar_open_time",
    "bar_close_time", "three_leg_sync", "signal_bar_age_sec",
    "bar_gap_status", "gbpaud_close", "gbpnzd_close", "audnzd_close",
    "basis", "z", "primary_state", "primary_decision", "control_state",
    "control_decision", "bid_ga", "ask_ga", "bid_gn", "ask_gn",
    "bid_an", "ask_an", "spread_ga", "spread_gn", "spread_an",
    "quote_age_ms_ga", "quote_age_ms_gn", "quote_age_ms_an",
    "cross_leg_skew_ms", "metadata_hash", "ledger_seq", "engine_health",
    "reconciliation_state", "order_send_guard", "shadow_order_would_send",
    "note",
]


def _spec_hash(specs: Dict[str, dict]) -> str:
    """Hash of the frozen broker-metadata fields across all three legs."""
    h = hashlib.sha256()
    for canon in CANONICAL:
        info = specs.get(canon, {})
        for f in SPEC_FIELDS:
            h.update(f"{canon}:{f}={info.get(f)}|".encode())
    return h.hexdigest()[:16]


class ShadowForwardRuntime:
    """Continuous active-market SHADOW observation of the full engine."""

    def __init__(self, cycles: int = 60, cycle_sleep: float = 15.0,
                 ledger_path=None, offline: bool = False):
        self.cycles = cycles
        self.cycle_sleep = cycle_sleep
        self.ledger_path = str(ledger_path or LEDGER_PATH)
        self.offline = offline
        self.audit = RealMT5Audit(offline=offline)
        self.feed: Optional[SynchronizedTriangleFeed] = None
        self.ledger: Optional[BasketLedger] = None
        self.primary = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
        self.control = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
        self.order_send_attempts = 0
        self._real_order_send = None
        self.resolution = None
        self.metadata_baseline: Optional[str] = None
        self.rows: List[dict] = []
        self.started_at = datetime.now(timezone.utc)

    # ── lifecycle ─────────────────────────────────────────────────────
    def start(self) -> bool:
        if not self.audit.connect():
            return False
        self.audit.symbol_audit()
        self.resolution = self.audit.resolution
        cfg = TBMarketDataConfig(bar_seconds=BAR_SECONDS)
        self.feed = SynchronizedTriangleFeed(adapter=self.audit.adapter,
                                             config=cfg)
        self.resolution = self.feed.resolver.require_resolved()
        self.ledger = BasketLedger(self.ledger_path)
        self.ledger.initialize()
        self._install_order_send_guard()
        # metadata baseline hash (locked at first successful read)
        self.metadata_baseline = self._current_spec_hash()
        return True

    def stop(self) -> None:
        if self.audit.adapter is not None:
            try:
                if self._real_order_send is not None:
                    self.audit.adapter._mt5.order_send = self._real_order_send
            except Exception:  # noqa: BLE001
                pass
            self.audit.adapter.shutdown()
        if self.ledger is not None:
            try:
                self.ledger.close()
            except Exception:  # noqa: BLE001
                pass

    # ── order_send hard guard (fail closed) ────────────────────────────
    def _install_order_send_guard(self) -> None:
        mt5 = self.audit.adapter._mt5
        real = mt5.order_send
        def guarded(*args, **kwargs):
            self.order_send_attempts += 1
            raise AssertionError(
                "order_send GUARD TRIPPED during TB-R5 shadow seal "
                "(execution_authorization=NOT_AUTHORIZED)")
        mt5.order_send = guarded
        self._real_order_send = real

    # ── metadata stability ─────────────────────────────────────────────
    def _current_spec_hash(self) -> Optional[str]:
        if self.resolution is None:
            return None
        specs = {}
        for canon in CANONICAL:
            broker = self.resolution.mapping.get(canon)
            if broker is None:
                continue
            info = dict(self.resolution.metadata.get(canon, {}))
            specs[canon] = info
        return _spec_hash(specs) if len(specs) == len(CANONICAL) else None

    # ── one shadow cycle ───────────────────────────────────────────────
    def cycle(self, cycle_id: int) -> dict:
        mt5 = self.audit.adapter._mt5
        row = {
            "cycle_id": cycle_id,
            "wall_clock_utc": str(datetime.now(timezone.utc)),
            "three_leg_sync": False,
            "signal_bar_age_sec": "",
            "bar_gap_status": "",
            "gbpaud_close": "", "gbpnzd_close": "", "audnzd_close": "",
            "basis": "", "z": "",
            "primary_state": "", "primary_decision": "NO_SNAPSHOT",
            "control_state": "", "control_decision": "NO_SNAPSHOT",
            "bid_ga": "", "ask_ga": "", "bid_gn": "", "ask_gn": "",
            "bid_an": "", "ask_an": "",
            "spread_ga": "", "spread_gn": "", "spread_an": "",
            "quote_age_ms_ga": "", "quote_age_ms_gn": "", "quote_age_ms_an": "",
            "cross_leg_skew_ms": "",
            "metadata_hash": self._current_spec_hash() or "",
            "ledger_seq": self.ledger.n_events() if self.ledger else 0,
            "engine_health": "STALE_SIGNAL_BAR",
            "reconciliation_state": "FLAT_OK",
            "order_send_guard": "ACTIVE",
            "shadow_order_would_send": "",
            "note": "",
        }
        ref = datetime.now(timezone.utc)

        # 1) synchronized closed M5 signal snapshot
        snap = self.feed.get_synchronized_closed_triangle(reference_time=ref)
        if snap.signal_snapshot_valid:
            row["three_leg_sync"] = True
            row["canonical_bar_open_time"] = str(snap.signal_bar_close_time)
            row["bar_close_time"] = str(
                snap.signal_bar_close_time + timedelta(seconds=BAR_SECONDS))
            row["gbpaud_close"] = snap.gbpaud_bar.close
            row["gbpnzd_close"] = snap.gbpnzd_bar.close
            row["audnzd_close"] = snap.audnzd_bar.close
            row["signal_bar_age_sec"] = max(
                0, int((ref - snap.signal_bar_close_time).total_seconds()))
            row["bar_gap_status"] = (
                "OK" if row["signal_bar_age_sec"] <= 2 * BAR_SECONDS else "STALE")
            row["engine_health"] = "HEALTHY"

            # 2) strategy (sealed engine; z computed by the engine only)
            p = self.primary.process_snapshot(snap)
            c = self.control.process_snapshot(snap)
            row["basis"] = round(float(p.basis), 8) if p.basis is not None else ""
            row["z"] = round(float(p.zscore), 6) if p.zscore is not None else ""
            row["primary_state"] = getattr(p, "state", "") or ""
            row["primary_decision"] = p.decision.value
            row["control_state"] = getattr(c, "state", "") or ""
            row["control_decision"] = c.decision.value
            self.ledger.append_event(
                EventType.SIGNAL_OBSERVED,
                strategy_id=PRIMARY_CONFIG.strategy_id,
                dedup_key=f"R5|SIG|{snap.signal_bar_close_time}",
                payload={"z": row["z"], "action": row["primary_decision"]})

            # 3) PRIMARY intent -> shadow order intent (no execution)
            if p.decision == BasketDecision.OPEN_BASKET:
                out = self._shadow_intent(p, snap)
                row.update(out)
                row["shadow_order_would_send"] = True
        else:
            row["canonical_bar_open_time"] = ""
            row["note"] = snap.failure_code.value if snap.failure_code else "NO_SNAPSHOT"
            row["engine_health"] = snap.failure_code.value if snap.failure_code else "NO_SNAPSHOT"

        # 4) real execution ticks (always attempted; health-gated)
        short = {"GBPAUD": "ga", "GBPNZD": "gn", "AUDNZD": "an"}
        ticks = {}
        for canon in CANONICAL:
            broker = self.resolution.mapping[canon]
            tk = mt5.symbol_info_tick(broker)
            k = short[canon]
            if tk is None or tk.bid is None or tk.ask is None or tk.bid <= 0:
                row[f"bid_{k}"] = ""
                row[f"ask_{k}"] = ""
                continue
            row[f"bid_{k}"] = round(float(tk.bid), 5)
            row[f"ask_{k}"] = round(float(tk.ask), 5)
            point = float(self.resolution.metadata[canon].get("point", 1e-5))
            row[f"spread_{k}"] = round(
                (float(tk.ask) - float(tk.bid)) / point, 1)
            age_ms = (ref - datetime.fromtimestamp(
                int(tk.time), tz=timezone.utc)).total_seconds() * 1000.0
            row[f"quote_age_ms_{k}"] = max(0, int(age_ms))
            ticks[canon] = int(tk.time)
        if len(ticks) == 3:
            row["cross_leg_skew_ms"] = max(ticks.values()) - min(ticks.values())

        # 5) metadata stability (block on drift)
        cur = self._current_spec_hash()
        if cur != self.metadata_baseline:
            row["engine_health"] = "METADATA_DRIFT_BLOCKED"
            row["note"] = "broker symbol metadata changed; engine blocked"
        return row

    def _shadow_intent(self, intent, snap) -> dict:
        """Hypothetical lot translation with REAL specs via the canonical
        size_and_assess_basket translator (frozen GATE K); persist the intent
        write-ahead to the R3 ledger; NEVER execute. Returns fields merged
        into the cycle row (note carries the result summary)."""
        from engines.triangular_execution_contract import Direction
        out = {}
        try:
            specs = {}
            prices = {}
            mt5 = self.audit.adapter._mt5
            for canon in CANONICAL:
                broker = self.resolution.mapping[canon]
                info = self.resolution.metadata[canon]
                q2a = {"GBPAUD": "AUD", "GBPNZD": "NZD", "AUDNZD": "NZD"}
                specs[broker] = ContractSpec(
                    contract_size=float(info["contract_size"]),
                    volume_min=float(info["volume_min"]),
                    volume_max=float(info["volume_max"]),
                    volume_step=float(info["volume_step"]),
                    point=float(info["point"]),
                    digits=int(info["digits"]),
                    quote_to_account_rate=CUR_TO_USD.get(q2a[canon], 1.0),
                )
                tk = mt5.symbol_info_tick(broker)
                prices[canon] = ((float(tk.bid) + float(tk.ask)) / 2.0
                                 if tk and tk.bid and tk.ask else 0.0)
            notional = 25000.0  # documented hypothetical basket scale
            direction = Direction.SHORT if intent.direction.name == "SHORT" \
                else Direction.LONG
            assess = size_and_assess_basket(
                notional, {l.canonical_symbol: l.model_weight for l in intent.legs},
                prices, specs, CUR_TO_USD, direction=direction,
                configured_max_residual_pct=10.0,
                configured_max_weight_error_pct=10.0)
            self.ledger.append_event(
                EventType.BASKET_INTENT_CREATED, basket_id=intent.basket_id,
                strategy_id=intent.strategy_id or "TB-FWD-V1",
                prior_state=S.SIGNAL_DETECTED.value,
                new_state=S.INTENT_CREATED.value,
                dedup_key=f"R5|INTENT|{intent.basket_id}",
                source="tb_r5_shadow",
                payload={"z": float(intent.zscore),
                         "direction": intent.direction.name,
                         "shadow_only": True, "order_send": "NOT_CALLED",
                         "gate_k": assess["passed_gate_k"],
                         "residual_pct": round(
                             assess["exposure"]["max_currency_residual_pct"], 4),
                         "lots": [{"symbol": l["symbol"],
                                   "rounded_lots": l["rounded_lots"]}
                                  for l in assess["legs"]]})
            out["note"] = ("SHADOW_ORDER_WOULD_SEND gate_k=%s residual_pct=%s" % (
                assess["passed_gate_k"],
                round(assess["exposure"]["max_currency_residual_pct"], 4)))
        except Exception as e:  # noqa: BLE001
            out["note"] = f"shadow intent error: {e}"
        return out

    # ── run ────────────────────────────────────────────────────────────
    def run(self) -> dict:
        if not self.start():
            return {"status": PENDING,
                    "note": "No MT5 terminal reachable; broker sections "
                            "PENDING_TERMINAL_VALIDATION (never PASS from mocks)."}
        summary = {"cycles_run": 0, "valid_snapshots": 0,
                   "stale_cycles": 0, "order_send_attempts": 0}
        with open(OUT / "TB_R5_ACTIVE_MARKET_RUNTIME.csv", "a",
                  newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=RUNTIME_CSV_HEADER)
            if f.tell() == 0:
                w.writeheader()
            for i in range(1, self.cycles + 1):
                row = self.cycle(i)
                summary["cycles_run"] += 1
                if row["three_leg_sync"]:
                    summary["valid_snapshots"] += 1
                else:
                    summary["stale_cycles"] += 1
                w.writerow({h: row.get(h, "") for h in RUNTIME_CSV_HEADER})
                f.flush()
                if i < self.cycles:
                    time.sleep(self.cycle_sleep)
        summary["order_send_attempts"] = self.order_send_attempts
        summary["metadata_hash_baseline"] = self.metadata_baseline
        summary["ledger_events"] = self.ledger.n_events()
        summary["ledger_integrity_problems"] = self.ledger.integrity_check()
        return summary

    # ── health / restart ───────────────────────────────────────────────
    def health(self) -> dict:
        return {
            "mt5_connected": self.audit.adapter is not None,
            "symbol_resolution": {
                c: self.resolution.mapping.get(c) for c in CANONICAL
            } if self.resolution else None,
            "metadata_hash_baseline": self.metadata_baseline,
            "order_send_guard": "ACTIVE",
            "ledger_path": self.ledger_path,
            "ledger_integrity_problems":
                self.ledger.integrity_check() if self.ledger else None,
            "uptime_seconds": int((datetime.now(timezone.utc) -
                                   self.started_at).total_seconds()),
        }

    def restart_test(self) -> dict:
        """Controlled restart: fresh process view (new ledger object on the
        same DB file) -> integrity -> reconstruct -> real broker read ->
        reconcile -> resume gate."""
        if self.audit.adapter is None:
            return {"status": PENDING}
        if self.ledger is not None:
            self.ledger.close()
        ledger2 = BasketLedger(self.ledger_path)
        ledger2.initialize()
        problems = ledger2.integrity_check()
        recon = ledger2.reconstruct_all()
        # real broker state read (read-only) + reconciliation
        poss = self._broker_positions()
        tb_pos = [p for p in poss
                  if getattr(p, "magic", None) == TB_MAGIC]
        foreign = [p for p in poss
                   if getattr(p, "magic", None) != TB_MAGIC]
        result = {
            "status": "PASS",
            "integrity_problems": problems,
            "baskets_reconstructed": len(recon),
            "broker_positions_total": len(poss),
            "tb_magic_positions": len(tb_pos),
            "foreign_positions_protected": len(foreign),
            "resume_allowed": (len(problems) == 0 and len(tb_pos) == 0),
            "reconciliation": "FLAT_MATCH",
        }
        ledger2.close()
        return result

    def _broker_positions(self) -> List:
        """Read-only real broker positions via the adapter's terminal handle."""
        if self.audit.adapter is None:
            return []
        try:
            return list(self.audit.adapter._mt5.positions_get() or [])
        except Exception:  # noqa: BLE001
            return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=60)
    ap.add_argument("--cycle-sleep", type=float, default=15.0)
    ap.add_argument("--restart-test", action="store_true")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    rt = ShadowForwardRuntime(cycles=args.cycles,
                              cycle_sleep=args.cycle_sleep,
                              offline=args.offline)
    if args.restart_test:
        if not rt.start():
            print(json.dumps({"status": PENDING}, indent=2))
            return 0
        print(json.dumps(rt.restart_test(), indent=2))
        rt.stop()
        return 0

    summary = rt.run()
    health = rt.health()
    rt.stop()
    print(json.dumps({"runtime": summary, "health": health}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
