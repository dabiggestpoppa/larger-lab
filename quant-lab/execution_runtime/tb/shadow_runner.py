"""QL-EXEC-R4.2 — ShadowRuntime: live shadow observation loop.

Consumes legacy-exported observations (Option B), recomputes PRIMARY + CONTROL
decisions with the canonical TB science via the generic adapters, builds
HYPOTHETICAL execution plans (never submittable), compares against the legacy
record with frozen tolerances, persists isolated state, and emits telemetry.

Invariants (hard):
- broker_write_calls == 0 at all times
- no MT5 import, no independent MT5 attach (Option B)
- no executable OrderIntent is ever constructed on the shadow path
- a mismatch records/alerts but never alters science or authority
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ..types import (
    BoundAccountSnapshot,
    CapitalRequest,
    StrategyExposureContext,
    stable_hash,
)
from .adapters import (
    TBCapitalPolicyAdapter,
    TBStrategyAdapter,
    TBTranslationAdapter,
)
from .parity import ParityTier
from .shadow import (
    ReadOnlyBrokerSession,
    ShadowExecutionPlan,
    ShadowLeg,
    ShadowRuntimeAuthority,
)
from .shadow_feed import ShadowExportFeed, ShadowFeedError
from .shadow_parity import (
    LiveParityVerdict,
    compare_live_record,
    mismatches,
)
from .shadow_store import ShadowStore

# canonical types (pure; no MT5)
import sys  # noqa: E402
from pathlib import Path as _P  # noqa: E402

_QL = _P(__file__).resolve().parents[2]  # quant-lab/
for _p in (_QL, _QL / "engines", _QL / "tb_live"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engines.triangular_basis_engine import TriangularBar  # noqa: E402
from tb_live.market_data import (  # noqa: E402
    ClosedBar,
    FailureCode,
    TriangleSignalSnapshot,
)

BROKER_SYMBOLS = ("GBPAUD.PRO", "GBPNZD.PRO", "AUDNZD.PRO")


class JsonlWriter:
    """Bounded append-only JSONL writer (parity / mismatch streams)."""

    def __init__(self, path: str | Path, max_bytes: int = 5 * 1024 * 1024) -> None:
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        if self.path.exists() and self.path.stat().st_size >= self.max_bytes:
            return  # bounded: drop new observations rather than grow unbounded
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
            f.flush()


def measure_resource() -> dict:
    """Lightweight resource instrumentation (best-effort, stdlib-first)."""
    out: dict = {"cpu_seconds": 0.0, "mem_rss_bytes": None}
    try:
        out["cpu_seconds"] = time.process_time()
    except Exception:
        pass
    try:
        import psutil  # type: ignore

        p = psutil.Process()
        out["mem_rss_bytes"] = p.memory_info().rss
    except Exception:
        pass
    return out


def build_snapshot(record: dict) -> Optional[TriangleSignalSnapshot]:
    """Reconstruct a canonical TriangleSignalSnapshot from an export record.

    Returns None when the record is not a usable synchronized closed bar
    (market closed / missing legs) — the shadow then skips engine processing
    (market-close behaviour, non-latching).
    """
    if not record.get("market_open", False):
        return None
    bars = record.get("bars") or {}
    try:
        ts = datetime.fromisoformat(str(record["bar_key"]))
    except (KeyError, ValueError):
        return None

    def closed(symbol: str) -> Optional[ClosedBar]:
        b = bars.get(symbol)
        if not b:
            return None
        return ClosedBar(
            symbol=symbol,
            bar_open_time=ts,
            bar_close_time=ts + timedelta(minutes=5),
            open=float(b["open"]), high=float(b["high"]),
            low=float(b["low"]), close=float(b["close"]),
            is_closed=True,
            bar_id=f"{symbol}|{ts.isoformat()}",
        )

    ga, gn, an = closed("GBPAUD"), closed("GBPNZD"), closed("AUDNZD")
    if ga is None or gn is None or an is None:
        return None
    return TriangleSignalSnapshot(
        signal_bar_close_time=ts,
        gbpaud_bar=ga,
        gbpnzd_bar=gn,
        audnzd_bar=an,
        all_same_bar_close=True,
        all_closed=True,
        signal_snapshot_valid=True,
        failure_code=FailureCode.OK,
        snapshot_id=f"shadow|{ts.isoformat()}",
    )


def build_tri_bar(record: dict) -> Optional[TriangularBar]:
    """Rebuild a canonical TriangularBar from an export record (warm path)."""
    bars = record.get("bars") or {}
    try:
        ts = datetime.fromisoformat(str(record["bar_key"]))
        ga, gn, an = bars["GBPAUD"], bars["GBPNZD"], bars["AUDNZD"]
    except (KeyError, ValueError):
        return None
    return TriangularBar(
        timestamp=ts,
        gbp_aud=float(ga["close"]), gbp_nzd=float(gn["close"]),
        aud_nzd=float(an["close"]),
        gbp_aud_high=float(ga["high"]), gbp_aud_low=float(ga["low"]),
        gbp_nzd_high=float(gn["high"]), gbp_nzd_low=float(gn["low"]),
        aud_nzd_high=float(an["high"]), aud_nzd_low=float(an["low"]),
    )


@dataclass
class ShadowCounters:
    bars_compared: int = 0
    decision_opportunities: int = 0
    primary_signals: int = 0
    control_signals: int = 0
    full_lifecycles: int = 0
    parity_exact: int = 0
    parity_normalized: int = 0
    mismatches: int = 0
    hypothetical_intents: int = 0
    execution_gate_denials: int = 0
    broker_write_calls: int = 0
    submit_attempts: int = 0
    close_attempts: int = 0
    cancel_attempts: int = 0
    order_check_attempts: int = 0
    restart_drills: int = 0
    market_close_cycles: int = 0
    feed_gaps: int = 0
    feed_corrupt: int = 0
    market_closed_bars: int = 0

    def to_dict(self) -> dict:
        return {k: int(v) for k, v in vars(self).items()}


class ShadowRuntime:
    """One generic TB shadow runtime (observer only)."""

    def __init__(
        self,
        *,
        runtime_id: str,
        deployment_generation: str,
        profile_hash: str,
        shadow_profile_hash: str,
        store: ShadowStore,
        feed: ShadowExportFeed,
        primary: TBStrategyAdapter,
        control: TBStrategyAdapter,
        translation: Optional[TBTranslationAdapter] = None,
        policy: Optional[TBCapitalPolicyAdapter] = None,
        broker: Optional[ReadOnlyBrokerSession] = None,
        authority: Optional[ShadowRuntimeAuthority] = None,
        parity_path: str | Path | None = None,
        mismatch_path: str | Path | None = None,
        basket_notional_usd: float = 5000.0,
        warm_window: int = 400,
    ) -> None:
        self.runtime_id = runtime_id
        self.deployment_generation = deployment_generation
        self.profile_hash = profile_hash
        self.shadow_profile_hash = shadow_profile_hash
        self.store = store
        self.feed = feed
        self.primary = primary
        self.control = control
        self.translation = translation or TBTranslationAdapter(
            basket_notional_usd=basket_notional_usd)
        self.policy = policy or TBCapitalPolicyAdapter()
        self.broker = broker or ReadOnlyBrokerSession(truth={})
        self.authority = authority or ShadowRuntimeAuthority()
        self.basket_notional_usd = basket_notional_usd
        self.warm_window = warm_window
        self.parity_writer = JsonlWriter(parity_path) if parity_path else None
        self.mismatch_writer = JsonlWriter(mismatch_path) if mismatch_path else None
        self.counters = ShadowCounters()
        self.state = "CREATED"
        self.latest_bar = ""
        self._basket_state_primary = "FLAT"
        self._basket_state_control = "FLAT"
        self._control_open_plan_id = ""
        self._last_error = ""
        self._warmed = False

    # ── lifecycle ────────────────────────────────────────────────────────

    def start(self) -> str:
        """Load desired state; warm from replay history; return state."""
        self._validate_authority()
        desired = self.store.desired_state(default="RUNNING")
        if desired == "STOPPED_BY_USER":
            self.state = "STOPPED"
            return self.state
        # Restore persisted hypothetical basket state across restart.
        self._basket_state_control = self.store.meta(
            "control_basket_state", "FLAT")
        self._control_open_plan_id = self.store.meta("control_open_plan_id", "")
        # Replay warm buffer from the feed (records before the resume point).
        from_seq = self.store.last_processed_seq()
        self._warm_from_feed(from_seq)
        self.state = "RUNNING"
        return self.state

    def _validate_authority(self) -> None:
        a = self.authority
        if a.shadow_mode != "SHADOW_OBSERVE_ONLY" or a.can_submit_new_risk:
            raise RuntimeError("shadow authority misconfigured: writes enabled")
        if self.broker.broker_write_calls != 0:
            raise RuntimeError("broker_write_calls != 0 at shadow start")

    def _warm_from_feed(self, from_seq: int) -> None:
        bars: list[TriangularBar] = []
        try:
            for _seq, rec in self.feed.iter_after(0):
                if rec["seq"] > from_seq:
                    break  # step() resumes from from_seq + 1
                tb = build_tri_bar(rec)
                if tb is not None:
                    bars.append(tb)
        except ShadowFeedError:
            pass  # warm is best-effort; corrupt records are blocked at step()
        if bars:
            self.primary.warm(bars)
            self.control.warm(bars)
        self._warmed = True

    def step(self, record: dict, *, is_replay: bool = False) -> list[LiveParityVerdict]:
        """Process one export record; returns per-surface parity verdicts."""
        seq = int(record["seq"])
        bar_key = str(record.get("bar_key", ""))
        self.latest_bar = bar_key
        self.counters.bars_compared += 1

        snap = build_snapshot(record)
        market_open = snap is not None
        if market_open:
            self.counters.decision_opportunities += 1
        if not market_open:
            # market-close observation: skip engine, keep parity surfaces.
            self.state = "WAITING_FOR_MARKET"
            self.counters.market_closed_bars += 1
            self._prev_market_closed = True
            verdicts = compare_live_record(
                bar_key,
                _legacy_subset(record),
                self._generic_dict(record, no_signal=True),
            )
        else:
            reopened = bool(getattr(self, "_prev_market_closed", False))
            if reopened:
                self.counters.market_close_cycles += 1
                self._prev_market_closed = False
            self.state = "RUNNING"
            self._feed_engines(snap)
            verdicts = compare_live_record(
                bar_key,
                _legacy_subset(record),
                self._generic_dict(record, no_signal=False),
            )

        self._record_verdicts(seq, bar_key, verdicts)
        self.store.record_processed(seq, bar_key, _verdict_summary(verdicts))
        return verdicts

    def _feed_engines(self, snap: TriangleSignalSnapshot) -> None:
        for tag, adapter in (("primary", self.primary), ("control", self.control)):
            obs = adapter.process_observation(snap)
            events = adapter.produce_events()
            if tag == "primary":
                self._obs_primary = obs
                self._last_plan_primary = None
                for ev in events:
                    self.counters.primary_signals += 1
                    self._last_plan_primary = self._make_hypothetical("primary", ev, obs)
            else:
                self._obs_control = obs
                self._last_plan_control = None
                for ev in events:
                    if ev.event_kind == "ENTRY":
                        self.counters.control_signals += 1
                        self._last_plan_control = self._make_hypothetical("control", ev, obs)
                        self._control_open_plan_id = str(ev.payload.get("basket_id", ""))
                        self._basket_state_control = "OPEN"
                        self.control.engine.on_basket_open_confirmed(
                            self._control_open_plan_id)
                        self._persist_basket_state()
                    elif ev.event_kind == "EXIT":
                        self._make_hypothetical("control", ev, obs)
                        self._basket_state_control = "CLOSED"
                        if self._control_open_plan_id:
                            self.counters.full_lifecycles += 1
                            self._control_open_plan_id = ""
                        self._persist_basket_state()

    def _make_hypothetical(self, tag: str, ev, obs: dict) -> ShadowExecutionPlan:
        """Build a ShadowExecutionPlan (hypothetical; never submittable)."""
        plan = self._admit_and_translate(tag, ev)
        self.counters.hypothetical_intents += 1
        # every hypothetical would have been an execution attempt -> denied
        self.counters.execution_gate_denials += 1
        self._append_plan(plan)
        return plan

    def _admit_and_translate(self, tag: str, ev) -> ShadowExecutionPlan:
        request = CapitalRequest(
            request_id=stable_hash("REQ", ev.event_id, n=24),
            event_id=ev.event_id, strategy_id=ev.strategy_id,
            family="TB", requested_f=1.0,
            portfolio_group_id="", account_id=self.runtime_id,
            policy_id=self.policy.policy_id,
        )
        decision = self.policy.admit(request)
        account_snapshot = BoundAccountSnapshot(
            account_id=self.runtime_id, account_currency="USD")
        ctx = StrategyExposureContext(strategy_id=ev.strategy_id, exposure_kind="ENTRY")
        target = self.translation.translate(ev, decision, account_snapshot, ctx)
        payload = ev.payload or {}
        weights = tuple(
            (str(leg.get("canonical_symbol", "")), round(float(leg.get("model_weight", 0.0)), 6))
            for leg in (payload.get("legs") or [])
        )
        legs = tuple(
            ShadowLeg(
                canonical_symbol=inst.instrument_id,
                broker_symbol=inst.broker_symbol,
                side=inst.side,
                model_weight=float((inst.metadata or {}).get("model_weight", 0.0)),
                target_notional=float(inst.target_notional or 0.0),
                target_lots=float(inst.target_quantity or 0.0),
            )
            for inst in target.instruments
        )
        return ShadowExecutionPlan(
            plan_id=str(payload.get("basket_id", "")),
            strategy_id=ev.strategy_id,
            runtime_id=self.runtime_id,
            deployment_generation=ev.deployment_generation,
            bar_key=str(ev.signal_time),
            decision=ev.event_kind,
            direction=str(payload.get("direction", "NONE")),
            event_id=ev.event_id,
            basis=float(payload.get("basis", 0.0)) or None,
            z_score=float(payload.get("zscore", 0.0)) or None,
            weights=weights,
            legs=legs,
            exit_reason=str(payload.get("exit_reason", "")),
        )

    def _append_plan(self, plan: ShadowExecutionPlan) -> None:
        if self.parity_writer is not None:
            self.parity_writer.append(
                {"kind": "hypothetical_plan", **plan.to_dict()})

    def _generic_dict(self, record: dict, *, no_signal: bool) -> dict:
        bar_key = str(record.get("bar_key", ""))
        if no_signal:
            return {
                "bar_key": bar_key,
                "source_timestamp": str(record.get("source_timestamp", "")),
                "session": bool(record.get("session", False)),
                "basket_state": self._basket_state_control,
                "primary": {"basis": None, "z": None, "decision": "NO_SIGNAL",
                            "direction": "NONE", "weights": {}, "lots": {}},
                "control": {"basis": None, "z": None, "decision": "NO_SIGNAL",
                            "direction": "NONE", "weights": {}, "lots": {}},
            }
        p_obs = getattr(self, "_obs_primary", None) or self.primary.last_observation()
        c_obs = getattr(self, "_obs_control", None) or self.control.last_observation()
        p_plan = getattr(self, "_last_plan_primary", None)
        c_plan = getattr(self, "_last_plan_control", None)
        return {
            "bar_key": bar_key,
            "source_timestamp": str(record.get("source_timestamp", "")),
            "session": bool(record.get("session", False)),
            "basket_state": self._basket_state_control,
            "primary": _tag_generic(p_obs, p_plan),
            "control": _tag_generic(c_obs, c_plan),
        }

    def _record_verdicts(self, seq: int, bar_key: str,
                         verdicts: list[LiveParityVerdict]) -> None:
        m = mismatches(verdicts)
        exact = sum(1 for v in verdicts if v.tier is ParityTier.EXACT)
        norm = sum(1 for v in verdicts if v.tier is ParityTier.NORMALIZED_EQUIVALENT)
        self.counters.parity_exact += exact
        self.counters.parity_normalized += norm
        self.counters.mismatches += len(m)
        row = {
            "seq": seq, "bar_key": bar_key,
            "verdicts": [v.to_dict() for v in verdicts],
        }
        if self.parity_writer is not None:
            self.parity_writer.append(row)
        for v in m:
            self.store.record_mismatch(
                bar_key=bar_key, mismatch_class=v.mismatch_class.value,
                legacy_value=json.dumps(v.legacy_value, default=str),
                generic_value=json.dumps(v.generic_value, default=str),
                detail=v.detail)
            if self.mismatch_writer is not None:
                self.mismatch_writer.append(v.to_dict())

    # ── telemetry / control ──────────────────────────────────────────────

    def telemetry(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "generation": self.deployment_generation,
            "shadow_mode": self.authority.shadow_mode,
            "desired_state": self.store.desired_state(default="RUNNING"),
            "process_alive": True,
            "latest_export_seq": self.store.last_processed_seq(),
            "latest_common_bar": self.latest_bar,
            "state": self.state,
            "counters": self.counters.to_dict(),
            "broker_write_calls": self.broker.broker_write_calls,
            "execution_gate_denials": self.counters.execution_gate_denials,
            "resource": measure_resource(),
            "last_error": self._last_error,
        }

    def heartbeat(self) -> None:
        self.store.record_heartbeat(
            state=self.state, latest_bar=self.latest_bar,
            bars_compared=self.counters.bars_compared,
            broker_write_calls=self.broker.broker_write_calls,
            last_error=self._last_error)

    def stop(self) -> None:
        self.state = "STOPPED"
        self.heartbeat()

    def set_desired_state(self, state: str) -> None:
        self.store.set_desired_state(state)

    def _persist_basket_state(self) -> None:
        self.store.set_meta("control_basket_state", self._basket_state_control)
        if self._basket_state_control == "OPEN":
            self.store.set_meta("control_open_plan_id", self._control_open_plan_id)
        else:
            self.store.set_meta("control_open_plan_id", "")

    def record_feed_gap(self, expected: int, found: int) -> None:
        self.counters.feed_gaps += 1
        self._last_error = f"feed sequence gap: expected {expected}, found {found}"
        if self.mismatch_writer is not None:
            self.mismatch_writer.append({
                "kind": "feed_gap", "expected": expected, "found": found})

    def record_feed_corrupt(self, seq, error: str) -> None:
        self.counters.feed_corrupt += 1
        self._last_error = f"feed corrupt record seq={seq}: {error}"
        if self.mismatch_writer is not None:
            self.mismatch_writer.append({
                "kind": "feed_corrupt", "seq": seq, "error": error})


def _tag_generic(obs: dict, plan: Optional[ShadowExecutionPlan]) -> dict:
    """Per-strategy generic surface for parity (weights/lots only on ENTRY)."""
    d = {
        "basis": obs.get("basis"), "z": obs.get("z"),
        "decision": obs.get("decision", "NO_SIGNAL"),
        "direction": obs.get("direction", "NONE"),
        "weights": obs.get("weights") or {},
        "lots": {},
    }
    if obs.get("decision") == "ENTRY" and plan is not None:
        d["lots"] = {leg.broker_symbol: leg.target_lots for leg in plan.legs}
    return d


def _legacy_subset(record: dict) -> dict:
    """The parity-relevant legacy surface from an export record."""
    return {
        "bar_key": str(record.get("bar_key", "")),
        "source_timestamp": str(record.get("source_timestamp", "")),
        "session": bool(record.get("session", False)),
        "basket_state": str(record.get("basket_state", "FLAT")),
        "primary": record.get("primary") or {},
        "control": record.get("control") or {},
    }


def _verdict_summary(verdicts: list[LiveParityVerdict]) -> str:
    if not verdicts:
        return "EMPTY"
    if any(v.tier is ParityTier.MISMATCH for v in verdicts):
        return "MISMATCH"
    return "EXACT"
