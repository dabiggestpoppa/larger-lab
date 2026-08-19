"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · LIVE / MATCH / PARITY
===================================================================

READ-ONLY side of the audit:

  * LiveLedgerReader   — opens the runtime event ledger (tb_control.db) in
                         SQLite read-only mode; never writes, never locks
                         for write.
  * LiveRuntimeReader  — read-only peek at tb_runtime.db (desired state,
                         heartbeat market-open, errors) for report context.
  * EventMatcher       — matches replay expectations to runtime artifacts by
                         strategy variant + canonical bar key + direction +
                         decision type; assigns exactly one OutcomeClass per
                         event; never matches loosely by wall-clock time.
  * Parity providers   — frozen numeric tolerance comparison of audit bars
                         vs live-observed bars. UNKNOWN/FAIL around a
                         disputed signal => DATA_DIVERGENCE (fail closed,
                         never accuse the runtime without parity proof).

NO broker calls exist here. NO runtime DB writes exist here.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tb_audit_core import (
    CONTROL_STRATEGY_ID,
    PRIMARY_STRATEGY_ID,
    AuditSummary,
    DecisionType,
    ExpectedEvent,
    LiveEvent,
    MatchRecord,
    OutcomeClass,
    PARITY_ABS_TOL,
    PARITY_REL_TOL,
    ParityStatus,
    bar_key_minute,
    direction_from_z,
)

SIGNAL_OBSERVED = "SIGNAL_OBSERVED"
EXIT_SIGNAL_OBSERVED = "EXIT_SIGNAL_OBSERVED"
BASKET_OPEN_VERIFIED = "BASKET_OPEN_VERIFIED"
BASKET_CLOSED_VERIFIED = "BASKET_CLOSED_VERIFIED"
ENGINE_BLOCKED = "ENGINE_BLOCKED"
SIGNAL_REJECTED = "SIGNAL_REJECTED"

STRATEGY_IDS = (PRIMARY_STRATEGY_ID, CONTROL_STRATEGY_ID)


# ─── Read-only ledger reader ─────────────────────────────────────────────
class LiveLedgerReader:
    """Reads the append-only runtime event ledger READ-ONLY."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def read_events(self, since_ts: Optional[str] = None,
                    strategies=STRATEGY_IDS) -> List[LiveEvent]:
        if not self.db_path.exists():
            return []
        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            q = ("SELECT seq, event_type, ts_utc, basket_id, strategy_id, "
                 "dedup_key, payload, reason FROM events "
                 "WHERE strategy_id IN (%s)" %
                 ",".join("?" * len(strategies)))
            args: list = list(strategies)
            if since_ts:
                q += " AND ts_utc >= ?"
                args.append(since_ts)
            q += " ORDER BY seq"
            rows = con.execute(q, args).fetchall()
        finally:
            con.close()
        out: List[LiveEvent] = []
        for r in rows:
            try:
                payload = json.loads(r["payload"] or "{}")
            except Exception:
                payload = {}
            ev = LiveEvent(
                seq=int(r["seq"]), event_type=str(r["event_type"]),
                ts_utc=str(r["ts_utc"]), strategy_id=str(r["strategy_id"]),
                basket_id=str(r["basket_id"] or ""),
                dedup_key=str(r["dedup_key"] or ""),
                payload=payload, reason=str(r["reason"] or ""),
            )
            self._decorate(ev)
            out.append(ev)
        return out

    @staticmethod
    def _decorate(ev: LiveEvent) -> None:
        if "|" in ev.dedup_key:
            tail = ev.dedup_key.rsplit("|", 1)[-1].strip()
            bkm = bar_key_minute(tail)
            if bkm:
                ev.bar_key = bkm
        z = ev.payload.get("z")
        if isinstance(z, (int, float)):
            ev.z = float(z)
            ev.direction = direction_from_z(float(z))


# ─── Read-only runtime reader (context only) ─────────────────────────────
class LiveRuntimeReader:
    """Read-only peek at the runtime DB for report context."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def context(self) -> dict:
        ctx = {"db_present": self.db_path.exists(),
               "desired_state": "", "market_open": None,
               "last_bar_key": "", "last_error": ""}
        if not ctx["db_present"]:
            return ctx
        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        try:
            try:
                r = con.execute("SELECT value FROM schema_meta "
                                "WHERE key='desired_state'").fetchone()
                if r:
                    ctx["desired_state"] = r["value"]
            except Exception:
                pass
            try:
                r = con.execute(
                    "SELECT market_open, last_bar_key, ts_utc "
                    "FROM runtime_heartbeat ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                if r:
                    ctx["market_open"] = bool(r["market_open"])
                    ctx["last_bar_key"] = r["last_bar_key"] or ""
            except Exception:
                pass
            try:
                r = con.execute(
                    "SELECT message, ts_utc FROM runtime_errors "
                    "ORDER BY seq DESC LIMIT 1").fetchone()
                if r:
                    ctx["last_error"] = r["message"] or ""
            except Exception:
                pass
        finally:
            con.close()
        return ctx


# ─── Parity ──────────────────────────────────────────────────────────────
class ParityProvider:
    def status_for(self, bar_key: str) -> ParityStatus:
        raise NotImplementedError

    def detail(self) -> dict:
        return {"provider": type(self).__name__}


class NullParityProvider(ParityProvider):
    """No live-observed data -> UNKNOWN (fails closed on disputes)."""

    def status_for(self, bar_key: str) -> ParityStatus:
        return ParityStatus.UNKNOWN

    def detail(self) -> dict:
        return {"provider": "null",
                "note": "no live-observed market data; disputed signals "
                        "fail closed as DATA_DIVERGENCE"}


class StaticParityProvider(ParityProvider):
    """Test seam: inject PASS/FAIL per bar key (or globally)."""

    def __init__(self, status: ParityStatus, keys: Optional[set] = None):
        self._status = status
        self._keys = keys or set()

    def status_for(self, bar_key: str) -> ParityStatus:
        if self._keys and bar_key not in self._keys:
            return ParityStatus.PASS
        return self._status

    def detail(self) -> dict:
        return {"provider": "static", "status": self._status.value}


class BarsParityProvider(ParityProvider):
    """Audit raw bars vs live-observed bars with frozen tolerance.

    Material divergence on ANY leg at a disputed bar key => FAIL; missing
    live-observed bar at a disputed key => FAIL (cannot prove parity).
    Frozen tolerance: abs diff > max(PARITY_ABS_TOL, PARITY_REL_TOL * price).
    """

    def __init__(self, audit_bars: Dict[str, dict],
                 live_bars: Dict[str, dict], checked_keys: set):
        self.audit = audit_bars
        self.live = live_bars
        self.checked = checked_keys
        self._cache: Dict[str, ParityStatus] = {}
        self.divergences: List[dict] = []

    @staticmethod
    def _material(a: float, b: float) -> bool:
        return abs(a - b) > max(PARITY_ABS_TOL, PARITY_REL_TOL * abs(a))

    def status_for(self, bar_key: str) -> ParityStatus:
        if bar_key not in self.checked:
            return ParityStatus.PASS
        if bar_key in self._cache:
            return self._cache[bar_key]
        st = ParityStatus.PASS
        for sym in ("GBPAUD", "GBPNZD", "AUDNZD"):
            a = self.audit.get(sym, {}).get(bar_key)
            b = self.live.get(sym, {}).get(bar_key)
            if a is None or b is None:
                self.divergences.append({"bar_key": bar_key, "symbol": sym,
                                         "audit_close": a, "live_close": b,
                                         "material": True,
                                         "reason": "missing live-observed bar"})
                st = ParityStatus.FAIL
                continue
            if self._material(float(a), float(b)):
                self.divergences.append({"bar_key": bar_key, "symbol": sym,
                                         "audit_close": float(a),
                                         "live_close": float(b),
                                         "material": True,
                                         "reason": "close divergence"})
                st = ParityStatus.FAIL
        self._cache[bar_key] = st
        return st

    def detail(self) -> dict:
        return {"provider": "bars", "checked_keys": len(self.checked),
                "divergence_count": len(self.divergences),
                "divergences": self.divergences[:50]}


class Mt5ParityProvider(ParityProvider):
    """Read-only MT5 pull of the disputed week compared to audit bars.

    Used ONLY when explicitly enabled (--mt5) and the terminal is up.
    copy_rates_range is a read; it can never send orders.
    """

    def __init__(self, audit_bars: Dict[str, dict], checked_keys: set,
                 week_start: datetime,
                 broker_map: Optional[Dict[str, str]] = None):
        self.audit = audit_bars
        self.checked = checked_keys
        self.week_start = week_start
        self.broker_map = broker_map or {
            "GBPAUD": "GBPAUD.PRO", "GBPNZD": "GBPNZD.PRO",
            "AUDNZD": "AUDNZD.PRO"}
        self._live: Dict[str, Dict[str, float]] = {}
        self._ok = False
        self._pull()

    def _pull(self) -> None:
        try:
            import MetaTrader5 as mt5  # noqa: PLC0415 - optional
        except Exception:
            return
        if not mt5.initialize():
            return
        try:
            for sym, broker in self.broker_map.items():
                rates = mt5.copy_rates_range(
                    broker, mt5.TIMEFRAME_M5, self.week_start,
                    self.week_start + timedelta(days=7))
                if rates is None:
                    continue
                self._live[sym] = {
                    datetime.fromtimestamp(int(r["time"]), tz=timezone.utc)
                    .strftime("%Y-%m-%d %H:%M"): float(r["close"])
                    for r in rates}
            self._ok = True
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass

    def status_for(self, bar_key: str) -> ParityStatus:
        if not self._ok or bar_key not in self.checked:
            return ParityStatus.PASS if self._ok else ParityStatus.UNKNOWN
        for sym in ("GBPAUD", "GBPNZD", "AUDNZD"):
            a = self.audit.get(sym, {}).get(bar_key)
            b = self._live.get(sym, {}).get(bar_key)
            if a is None or b is None:
                return ParityStatus.FAIL
            if abs(a - b) > max(PARITY_ABS_TOL, PARITY_REL_TOL * abs(a)):
                return ParityStatus.FAIL
        return ParityStatus.PASS

    def detail(self) -> dict:
        return {"provider": "mt5", "connected": self._ok,
                "live_symbols": sorted(self._live.keys())}


def build_parity_map(data_window) -> Dict[str, dict]:
    """{symbol: {bar_key: close}} from the audit window (audit side)."""
    out: Dict[str, dict] = {}
    for sym in ("GBPAUD", "GBPNZD", "AUDNZD"):
        out[sym] = {b.ts.strftime("%Y-%m-%d %H:%M"): b.close
                    for b in data_window.per_symbol[sym]}
    return out


# ─── Matching ────────────────────────────────────────────────────────────
def _parse_ts(s: str) -> datetime:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return datetime(1970, 1, 1)


class EventMatcher:
    """Classify every expected + live event into exactly one outcome."""

    def __init__(self, parity: ParityProvider):
        self.parity = parity

    def match(self, expected: List[ExpectedEvent], live: List[LiveEvent]):
        """Returns (records, summaries_by_strategy, unmatched_live_signals)."""
        records: List[MatchRecord] = []
        summaries = {s: AuditSummary(strategy_id=s) for s in STRATEGY_IDS}
        unmatched_live: List[LiveEvent] = []

        live_entries: Dict[Tuple, List[LiveEvent]] = {}
        for ev in live:
            if ev.event_type == SIGNAL_OBSERVED:
                live_entries.setdefault(
                    (ev.strategy_id, ev.bar_key, ev.direction), []).append(ev)
        live_exits: Dict[Tuple, List[LiveEvent]] = {}
        for ev in live:
            if ev.event_type == EXIT_SIGNAL_OBSERVED:
                live_exits.setdefault(
                    (ev.strategy_id, ev.basket_id), []).append(ev)

        open_windows: Dict[str, List[list]] = {}
        closed_baskets: set = set()
        for ev in live:
            if ev.event_type == BASKET_OPEN_VERIFIED:
                open_windows.setdefault(ev.strategy_id, []).append(
                    [_parse_ts(ev.ts_utc), None])
            elif ev.event_type == BASKET_CLOSED_VERIFIED:
                closed_baskets.add(ev.basket_id)
                for w in open_windows.get(ev.strategy_id, []):
                    if w[1] is None:
                        w[1] = _parse_ts(ev.ts_utc)

        rejected_at: Dict[Tuple, bool] = {}
        for ev in live:
            if ev.event_type == SIGNAL_REJECTED and ev.bar_key:
                rejected_at[(ev.strategy_id, ev.bar_key)] = True

        def basket_open_at(strategy: str, ts: datetime) -> bool:
            for w in open_windows.get(strategy, []):
                if w[0] <= ts and (w[1] is None or ts <= w[1]):
                    return True
            return False

        matched_live_ids: set = set()
        taken_baskets: set = set()

        for exp in expected:
            summ = summaries[exp.strategy_id]
            if exp.decision_type == DecisionType.ENTRY:
                summ.expected_entries += 1
            else:
                summ.expected_exits += 1

            if exp.decision_type == DecisionType.ENTRY:
                key = (exp.strategy_id, exp.bar_key, exp.direction)
                cands = live_entries.get(key, [])
            else:
                key = (exp.strategy_id, exp.basket_id)
                cands = live_exits.get(key, [])

            if cands:
                live_ev = cands[0]
                matched_live_ids.add(live_ev.seq)
                if exp.decision_type == DecisionType.EXIT:
                    outcome = (OutcomeClass.MATCHED_TAKEN
                               if exp.basket_id in taken_baskets
                               else OutcomeClass.MATCHED_SHADOW)
                    records.append(MatchRecord(
                        exp, live_ev, outcome, ParityStatus.PASS,
                        "runtime exit signal observed"))
                    # taken/shadow are counted at the ENTRY record
                    continue
                # ENTRY matched (compare against the CANONICAL basket id,
                # which the runtime's open/reject records also carry)
                has_open = any(
                    e.event_type == BASKET_OPEN_VERIFIED
                    and e.basket_id == exp.basket_id and e.basket_id
                    for e in live)
                has_reject = any(
                    e.event_type == SIGNAL_REJECTED
                    and e.basket_id == exp.basket_id and e.basket_id
                    for e in live)
                if exp.strategy_id == CONTROL_STRATEGY_ID and has_open:
                    records.append(MatchRecord(
                        exp, live_ev, OutcomeClass.MATCHED_TAKEN,
                        ParityStatus.PASS,
                        "runtime signal matched; basket open verified"))
                    summ.taken += 1
                    taken_baskets.add(exp.basket_id or live_ev.basket_id)
                elif has_reject:
                    records.append(MatchRecord(
                        exp, live_ev, OutcomeClass.VALID_RUNTIME_BLOCK,
                        ParityStatus.PASS,
                        "runtime signal matched; execution rejected"))
                    summ.valid_blocks += 1
                else:
                    records.append(MatchRecord(
                        exp, live_ev, OutcomeClass.MATCHED_SHADOW,
                        ParityStatus.PASS,
                        "runtime signal matched (shadow observation)"))
                    summ.shadow += 1
            else:
                ts = _parse_ts(exp.timestamp_utc)
                if exp.decision_type == DecisionType.EXIT:
                    if exp.basket_id in closed_baskets:
                        records.append(MatchRecord(
                            exp, None, OutcomeClass.MATCHED_SHADOW,
                            ParityStatus.PASS,
                            "no exit-signal record but basket close verified"))
                        summ.shadow += 1
                    else:
                        # disputed exit: parity gate, same as entries
                        pst = self.parity.status_for(exp.bar_key)
                        if pst == ParityStatus.PASS:
                            records.append(MatchRecord(
                                exp, None, OutcomeClass.MISSED_SIGNAL, pst,
                                "expected exit not observed in runtime; "
                                "data parity PASS"))
                            summ.missed += 1
                            summ.unrecognized_expected += 1
                        else:
                            records.append(MatchRecord(
                                exp, None, OutcomeClass.DATA_DIVERGENCE, pst,
                                "disputed exit; data parity FAIL/UNKNOWN -> "
                                "fail closed, no runtime accusation"))
                            summ.data_divergence += 1
                    continue
                # ENTRY with no runtime signal: block or dispute
                if basket_open_at(exp.strategy_id, ts):
                    records.append(MatchRecord(
                        exp, None, OutcomeClass.VALID_RUNTIME_BLOCK,
                        ParityStatus.PASS,
                        "expected entry correctly blocked: basket already open"))
                    summ.valid_blocks += 1
                elif rejected_at.get((exp.strategy_id, exp.bar_key)):
                    records.append(MatchRecord(
                        exp, None, OutcomeClass.VALID_RUNTIME_BLOCK,
                        ParityStatus.PASS,
                        "expected entry blocked: runtime recorded rejection"))
                    summ.valid_blocks += 1
                else:
                    pst = self.parity.status_for(exp.bar_key)
                    if pst == ParityStatus.PASS:
                        records.append(MatchRecord(
                            exp, None, OutcomeClass.MISSED_SIGNAL, pst,
                            "canonical replay expects signal; runtime silent; "
                            "data parity PASS"))
                        summ.missed += 1
                        summ.unrecognized_expected += 1
                    else:
                        records.append(MatchRecord(
                            exp, None, OutcomeClass.DATA_DIVERGENCE, pst,
                            "disputed signal; data parity FAIL/UNKNOWN -> "
                            "fail closed, no runtime accusation"))
                        summ.data_divergence += 1

        # live signals with no expectation -> RUNTIME_ONLY_SIGNAL
        for ev in live:
            if ev.event_type != SIGNAL_OBSERVED:
                continue
            summ = summaries[ev.strategy_id]
            summ.runtime_signals += 1
            if ev.seq in matched_live_ids:
                continue
            records.append(MatchRecord(
                None, ev, OutcomeClass.RUNTIME_ONLY_SIGNAL,
                ParityStatus.UNKNOWN,
                "runtime reported a signal the canonical replay does not "
                "reproduce (bar-key/source/lookback drift suspected)"))
            summ.runtime_only += 1
            unmatched_live.append(ev)

        for s in STRATEGY_IDS:
            summ = summaries[s]
            summ.no_signal = (summ.expected_entries == 0
                              and summ.runtime_signals == 0)
        return records, summaries, unmatched_live
