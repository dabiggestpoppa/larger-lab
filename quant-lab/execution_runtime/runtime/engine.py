"""QL-EXEC-R3 — GenericRuntime (single-instance).

One runtime, one account binding, one process. The engine drives the frozen
lifecycle: START -> load durable state -> validate identity -> connect broker ->
verify account truth -> reconstruct local state -> reconcile broker truth ->
warm strategy -> observe events -> admit capital -> translate -> write-ahead
intent -> execute ONLY through an injected broker (SimBrokerSession in tests) ->
verify broker truth -> persist -> survive restart -> heartbeat -> stop.

Dependencies are ALL injected (strategy / capital policy / translation /
broker / store / clock / singleton). There are no hidden globals, no strategy
imports, no Capital Routing math, no MetaTrader5.

Write-ahead discipline: an ExecutionIntent is committed BEFORE
``broker.submit_order``. No broker call is made inside a SQLite write
transaction. The crash window is handled by reconciliation on restart, never by
blind resubmission.

Crash injection is explicit (``CrashPoint``) and raises ``SimulatedCrash`` at a
deterministic boundary so tests can emulate process death without killing the
test process.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from ..account import AccountObservedState, AccountProfile
from ..authority import derive_execution_authority, identity_gate
from ..compatibility import evaluate_compatibility
from ..enums import (
    AuthenticationMode,
    BrokerErrorCategory,
    CapitalDecisionKind,
    DesiredState,
    FillPolicy,
    MarketStatus,
    OrderSide,
    OrderType,
    QuantityUnit,
    RuntimeHealth,
)
from ..hashing import config_hash
from ..interfaces import (
    BrokerSession,
    CapitalPolicyAdapter,
    CapitalTranslationAdapter,
    StrategyAdapter,
)
from ..ownership import (
    LogicalOwnershipId,
    OwnershipNamespace,
    encode_broker_ownership,
    magic_for_namespace,
)
from ..profiles import RuntimeProfile, RuntimeState as AuthorityRuntimeState
from ..types import (
    BoundAccountSnapshot,
    CapitalRequest,
    EconomicTarget,
    InstrumentTarget,
    OrderIntent,
    StrategyEvent,
    StrategyExposureContext,
    stable_hash,
    utcnow_iso,
)
from .adapters import EVENT_KIND_ENTRY, EVENT_KIND_EXIT
from .heartbeat import Heartbeat, TelemetrySnapshot
from .intent import (
    ExecutionIntent,
    IntentState,
    PositionState,
    execution_intent_id,
)
from .reconciliation import (
    ReconciliationResult,
    ReconciliationState,
    Reconciler,
)
from .singleton import SingletonConflict, SingletonLock
from .state import RuntimeState, validate_transition
from .store import RuntimeStore


class SimulatedCrash(RuntimeError):
    """Raised at an injected CrashPoint to emulate process death."""


class CrashPoint(str, Enum):
    NONE = "NONE"
    AFTER_INTENT_COMMIT = "AFTER_INTENT_COMMIT"
    AFTER_BROKER_SUBMIT = "AFTER_BROKER_SUBMIT"
    AFTER_CLOSE_SUBMIT = "AFTER_CLOSE_SUBMIT"


@dataclass(frozen=True)
class _RuntimeContext:
    runtime_id: str
    account_id: str
    strategy_id: str
    deployment_generation: str


class GenericRuntime:
    """Generic single-instance execution runtime (all deps injected)."""

    def __init__(
        self,
        *,
        profile: RuntimeProfile,
        account_profile: AccountProfile,
        strategy: StrategyAdapter,
        capital_policy: CapitalPolicyAdapter,
        capital_translation: CapitalTranslationAdapter,
        broker: BrokerSession,
        store: RuntimeStore,
        clock: Optional[Callable[[], str]] = None,
        singleton: Optional[SingletonLock] = None,
        crash_point: CrashPoint = CrashPoint.NONE,
    ) -> None:
        self._profile = profile
        self._account = account_profile
        self._strategy = strategy
        self._capital_policy = capital_policy
        self._translation = capital_translation
        self._broker = broker
        self._store = store
        self._clock = clock or utcnow_iso
        self._crash_point = crash_point

        self._state = RuntimeState.CREATED
        self._desired_state = DesiredState.RUNNING
        self._blocking_reason = ""
        self._last_error = ""
        self._identity_match = False
        self._reconciliation: Optional[ReconciliationResult] = None
        self._authority_reasons: tuple[str, ...] = ()
        self._last_strategy_event_id = ""

        lock_path = Path(store.db_path).parent / "runtime.lock"
        self._singleton = singleton or SingletonLock(lock_path)
        self._reconciler = Reconciler()
        self._strategy_context = _RuntimeContext(
            runtime_id=profile.runtime_id,
            account_id=account_profile.account_id,
            strategy_id=getattr(strategy, "strategy_id", ""),
            deployment_generation=profile.deployment_generation,
        )

    # ── public state accessors ────────────────────────────────────────────

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def desired_state(self) -> DesiredState:
        return self._desired_state

    @property
    def blocking_reason(self) -> str:
        return self._blocking_reason

    @property
    def reconciliation(self) -> Optional[ReconciliationResult]:
        return self._reconciliation

    # ── lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> RuntimeState:
        """Run the fail-closed startup sequence and return the resulting state."""
        self._set_state(RuntimeState.STARTING)

        # 1-2. profile/config hash + runtime_id validity
        profile_hash = config_hash(self._profile)
        account_hash = config_hash(self._account)

        # 3-4. singleton acquire
        try:
            self._singleton.acquire(f"{self._profile.runtime_id}:instance")
        except SingletonConflict as exc:
            self._last_error = str(exc)
            self._set_state(RuntimeState.FAILED)
            return self._state

        # 5-6. open store + validate schema/version
        try:
            if not self._store.connected:
                self._store.open()
            problems = self._store.integrity_check()
            if problems:
                self._last_error = "; ".join(problems)
                self._set_state(RuntimeState.FAILED)
                return self._state
            blockers = self._store.startup_check(
                runtime_id=self._profile.runtime_id,
                deployment_generation=self._profile.deployment_generation,
                profile_hash=profile_hash,
                account_hash=account_hash,
            )
            if blockers:
                self._blocking_reason = "; ".join(blockers)
                self._set_state(RuntimeState.BLOCKED)
                return self._state
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"store validation failed: {exc}"
            self._set_state(RuntimeState.FAILED)
            return self._state

        # 7-8. desired state
        self._desired_state = self._resolve_desired_state()
        if self._desired_state is DesiredState.STOPPED_BY_USER:
            self._set_state(RuntimeState.STOPPED)
            self._broker.disconnect()
            self._release_singleton()
            return self._state

        # 9-17. connect -> identity -> account truth -> reconcile -> warm -> run
        self._advance_through_startup()
        return self._state

    def _advance_through_startup(self) -> None:
        if self._state is RuntimeState.FAILED or self._state is RuntimeState.STOPPED:
            return
        # connect
        self._set_state(RuntimeState.CONNECTING)
        connected = self._try_connect()
        if not connected:
            self._blocking_reason = "broker unavailable"
            self._set_state(RuntimeState.WAITING_FOR_BROKER)
            return

        # identity check
        self._set_state(RuntimeState.IDENTITY_CHECK)
        identity_ok, identity_blockers = self._evaluate_identity()
        if not identity_ok:
            self._blocking_reason = "; ".join(identity_blockers)
            self._set_state(RuntimeState.BLOCKED)
            return
        self._identity_match = True

        # account truth + reconciliation
        self._set_state(RuntimeState.RECONCILING)
        rec = self._run_reconciliation()
        if rec.state is ReconciliationState.ERROR:
            self._blocking_reason = rec.blocked_reason
            self._set_state(RuntimeState.BLOCKED)
            return
        if rec.action == "BLOCK":
            self._blocking_reason = rec.blocked_reason
            self._set_state(RuntimeState.BLOCKED)
            return
        if rec.action in ("RETRY", "RECONSTRUCT", "CLOSE_RETRY"):
            self._recover(rec)
            rec = self._run_reconciliation()  # re-evaluate after recovery

        # warm strategy (and restore state if persisted)
        self._set_state(RuntimeState.WARMING)
        try:
            stored = self._store.meta("strategy_state")
            if stored:
                self._strategy.restore_state(stored)
            self._strategy.warm(None)
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"strategy warm failed: {exc}"
            self._blocking_reason = self._last_error
            self._set_state(RuntimeState.BLOCKED)
            return

        self._set_state(RuntimeState.RUNNING)

    def step(self, market_snapshot: object = None) -> TelemetrySnapshot:
        """One deterministic processing step. Returns a read-only snapshot."""
        if self._state in (RuntimeState.STOPPED, RuntimeState.FAILED):
            return self.telemetry()

        desired = self._resolve_desired_state()
        if desired is DesiredState.STOPPED_BY_USER:
            self._stop_clean()
            return self.telemetry()

        # Recover from temporary broker unavailability / a cleared blocker.
        if self._state is RuntimeState.WAITING_FOR_BROKER:
            self._set_state(RuntimeState.CONNECTING)
            if self._try_connect():
                self._set_state(RuntimeState.IDENTITY_CHECK)
                ok, blockers = self._evaluate_identity()
                if not ok:
                    self._blocking_reason = "; ".join(blockers)
                    self._set_state(RuntimeState.BLOCKED)
                    return self.telemetry()
                self._set_state(RuntimeState.RECONCILING)
            else:
                self._blocking_reason = "broker unavailable"
                self._set_state(RuntimeState.WAITING_FOR_BROKER)
                return self.telemetry()

        if not self._broker.health().get("connected", False):
            self._blocking_reason = "broker unavailable"
            self._set_state(RuntimeState.WAITING_FOR_BROKER)
            return self.telemetry()

        # Reconcile every step (fresh observation replaces stale status).
        self._set_state(RuntimeState.RECONCILING)
        rec = self._run_reconciliation()
        if rec.state is ReconciliationState.ERROR or rec.action == "BLOCK":
            self._blocking_reason = rec.blocked_reason
            self._set_state(RuntimeState.BLOCKED)
            return self.telemetry()
        if rec.action in ("RETRY", "RECONSTRUCT", "CLOSE_RETRY"):
            self._recover(rec)
            rec = self._run_reconciliation()

        if not rec.clean:
            self._blocking_reason = rec.blocked_reason
            self._set_state(RuntimeState.BLOCKED)
        else:
            self._blocking_reason = ""
            self._set_state(RuntimeState.RUNNING)

        # Process new events only when running and new-risk authorized.
        if self._state is RuntimeState.RUNNING:
            self._process_events(market_snapshot)

        self._persist_heartbeat()
        return self.telemetry()

    def stop(self) -> None:
        """Intentional stop: persist STOPPED_BY_USER and disconnect cleanly."""
        self._store.write_desired_state(DesiredState.STOPPED_BY_USER.value, self._profile.runtime_id)
        self._desired_state = DesiredState.STOPPED_BY_USER
        self._stop_clean()

    def _stop_clean(self) -> None:
        if self._state in (RuntimeState.STOPPED, RuntimeState.FAILED):
            return
        if self._state is RuntimeState.CREATED:
            self._set_state(RuntimeState.STOPPED)
            return
        self._set_state(RuntimeState.STOPPING)
        try:
            self._broker.disconnect()
        except Exception:  # noqa: BLE001
            pass
        self._release_singleton()
        self._set_state(RuntimeState.STOPPED)

    # ── connection / identity / reconciliation ────────────────────────────

    def _try_connect(self) -> bool:
        try:
            ok = self._broker.connect()
        except Exception:  # noqa: BLE001
            ok = False
        return bool(ok) and bool(self._broker.health().get("connected", False))

    def _evaluate_identity(self) -> tuple[bool, tuple[str, ...]]:
        observed = self._build_observed_state()
        ok, blockers = identity_gate(self._account, observed)
        self._identity_match = ok
        return ok, tuple(blockers)

    def _build_observed_state(self) -> AccountObservedState:
        ident = self._broker.identity()
        acct = self._broker.account_state()
        rec_clean = bool(self._reconciliation and self._reconciliation.clean)
        return AccountObservedState(
            account_id=self._account.account_id,
            observed_at=self._clock(),
            transport_connected=bool(self._broker.health().get("connected", False)),
            authenticated=self._account.authentication_mode is AuthenticationMode.NONE,
            observed_broker_company=ident.broker_company,
            observed_server=ident.server,
            observed_account_identifier=ident.account_identifier,
            observed_environment=ident.environment,
            observed_currency=ident.currency,
            observed_account_mode=ident.account_mode,
            hedging_or_netting=ident.hedging_netting,
            observed_terminal_binding="",
            equity=acct.equity,
            balance=acct.balance,
            margin=acct.margin,
            free_margin=acct.free_margin,
            buying_power=acct.buying_power,
            market_status=MarketStatus.OPEN,
            reconciled=rec_clean,
            runtime_health=RuntimeHealth.UNKNOWN,
            blocking_reasons=(self._blocking_reason,) if self._blocking_reason else (),
        )

    def _run_reconciliation(self) -> ReconciliationResult:
        snapshot = self._broker.reconcile_snapshot()
        owned = self._store.owned_positions()
        intents = self._store.intents()
        result = self._reconciler.reconcile(
            broker_positions=snapshot.positions,
            owned_positions=owned,
            intents=intents,
        )
        self._reconciliation = result
        self._store.record_reconciliation_run(
            run_id=stable_hash("REC", self._profile.runtime_id, self._clock(), n=16),
            state=result.state.value,
            clean=result.clean,
            blocked_reason=result.blocked_reason,
            owned_count=result.owned_count,
            foreign_count=result.foreign_count,
            detail=result.detail,
        )
        self._store.append_event(
            "RECONCILED",
            payload=result.to_dict(),
        )
        return result

    def _recover(self, result: ReconciliationResult) -> None:
        snapshot = self._broker.reconcile_snapshot()
        if result.action == "RETRY":
            self._retry_pending_intents()
        elif result.action == "RECONSTRUCT":
            if result.state is ReconciliationState.BROKER_OWNED_LOCAL_MISSING:
                self._reconstruct_from_broker(snapshot)
            elif result.state is ReconciliationState.CLOSED_MATCH:
                self._mark_close_pending_closed()
        elif result.action == "CLOSE_RETRY":
            self._retry_close()

    # ── authority ─────────────────────────────────────────────────────────

    def _current_authority(self):
        observed = self._build_observed_state()
        ident = self._broker.identity()
        compat = evaluate_compatibility(
            self._account.account_role,
            ident.hedging_netting,
            same_symbol_overlap=False,
            account_id=self._account.account_id,
        )
        runtime_state = AuthorityRuntimeState(
            runtime_id=self._profile.runtime_id,
            desired_state=self._resolve_desired_state(),
            safety_blocked=self._state in (RuntimeState.BLOCKED, RuntimeState.WAITING_FOR_BROKER),
        )
        authority = derive_execution_authority(
            self._account, observed, runtime_state, compat
        )
        self._authority_reasons = authority.reasons
        return authority

    # ── event processing ──────────────────────────────────────────────────

    def _process_events(self, market_snapshot: object) -> None:
        authority = self._current_authority()
        if not authority.can_submit_new_risk:
            self._blocking_reason = "; ".join(authority.reasons) or "new-risk denied"
            self._set_state(RuntimeState.BLOCKED)
            return
        for event in self._strategy.produce_events():
            self._process_event(event, authority)

    def _process_event(self, event: StrategyEvent, authority) -> None:
        # Dedup: same event (scoped by strategy + generation) never reprocesses.
        if self._store.has_strategy_event(event.event_id):
            self._last_strategy_event_id = event.event_id
            return
        self._store.record_strategy_event(
            event.event_id,
            event.strategy_id,
            event.event_kind,
            event.deployment_generation,
            event.signal_time,
            event.payload,
        )
        self._last_strategy_event_id = event.event_id
        self._store.append_event(
            "EVENT_OBSERVED",
            dedup_key=f"ev:{event.event_id}:{event.deployment_generation}",
            payload={"event_id": event.event_id, "event_kind": event.event_kind},
        )

        if event.event_kind == EVENT_KIND_EXIT:
            self._process_exit(event)
            return
        if event.event_kind != EVENT_KIND_ENTRY:
            return

        # Capital admission (no sizing science here).
        request = CapitalRequest(
            request_id=stable_hash("REQ", event.event_id, n=24),
            event_id=event.event_id,
            strategy_id=event.strategy_id,
            family="",
            requested_f=1.0,
            portfolio_group_id=self._account.portfolio_group_id or "",
            account_id=self._account.account_id,
            policy_id=self._capital_policy.policy_id,
        )
        decision = self._capital_policy.admit(request)
        self._store.record_capital_decision(
            decision.decision_id,
            event.event_id,
            event.strategy_id,
            decision.kind.value,
            decision.admitted_f,
            decision.reservation_id,
            decision.policy_id,
            decision.reason,
        )
        if not decision.admitted:
            self._store.append_event(
                "CAPITAL_DECISION",
                dedup_key=f"cap:{event.event_id}",
                payload={"admitted": False, "reason": decision.reason},
            )
            return

        account_snapshot = self._bound_account_snapshot()
        strategy_context = StrategyExposureContext(
            strategy_id=event.strategy_id, exposure_kind=event.event_kind
        )
        target = self._translation.translate(
            event, decision, account_snapshot, strategy_context
        )
        for inst in target.instruments:
            self._execute_instrument(event, decision, target, inst)

    def _execute_instrument(
        self,
        event: StrategyEvent,
        decision,
        target: EconomicTarget,
        inst: InstrumentTarget,
    ) -> None:
        target_id = stable_hash(
            "TGT1", event.event_id, inst.instrument_id, inst.side, n=24
        )
        quantity = float(inst.target_quantity or 0.0)
        self._store.record_economic_target(
            target_id,
            event.event_id,
            event.strategy_id,
            self._account.account_id,
            inst.instrument_id,
            inst.broker_symbol,
            inst.side,
            inst.target_quantity,
            inst.target_notional,
        )
        self._store.append_event(
            "TARGET_CREATED",
            dedup_key=f"tgt:{target_id}",
            payload={"target_id": target_id, "instrument": inst.instrument_id},
        )

        intent_id = execution_intent_id(
            runtime_id=self._profile.runtime_id,
            account_id=self._account.account_id,
            strategy_id=event.strategy_id,
            deployment_generation=event.deployment_generation,
            event_id=event.event_id,
            economic_target_id=target_id,
            instrument=inst.instrument_id,
            side=inst.side,
            broker_quantity=quantity,
        )
        logical = LogicalOwnershipId(
            account_id=self._account.account_id,
            runtime_id=self._profile.runtime_id,
            strategy_id=event.strategy_id,
            deployment_generation=event.deployment_generation,
            intent_id=intent_id,
        )
        tag = encode_broker_ownership(logical)
        side = OrderSide(inst.side) if inst.side in ("BUY", "SELL") else OrderSide.BUY

        intent = ExecutionIntent(
            intent_id=intent_id,
            runtime_id=self._profile.runtime_id,
            account_id=self._account.account_id,
            strategy_id=event.strategy_id,
            deployment_generation=event.deployment_generation,
            event_id=event.event_id,
            economic_target_id=target_id,
            instrument=inst.instrument_id,
            broker_symbol=inst.broker_symbol,
            side=side.value,
            broker_quantity=quantity,
            logical_ownership_id=logical.id(),
            ownership_tag=tag.comment,
            broker_magic=tag.magic,
        )

        # Write-ahead: commit intent BEFORE any broker call.
        created = self._store.create_intent(intent)
        if not created:
            return  # deterministic id already exists -> idempotent no-op
        self._store.append_event(
            "INTENT_CREATED",
            dedup_key=f"intent:{intent_id}",
            payload={"intent_id": intent_id},
        )

        order_intent = OrderIntent(
            intent_id=intent_id,
            account_id=self._account.account_id,
            symbol=inst.broker_symbol,
            side=side,
            volume=quantity,
            quantity_unit=QuantityUnit.LOT,
            order_type=OrderType.MARKET,
            fill_policy=FillPolicy.BROKER_DEFAULT,
            broker_magic=tag.magic,
            ownership_tag=tag.comment,
        )

        self._maybe_crash(CrashPoint.AFTER_INTENT_COMMIT)
        result = self._broker.submit_order(order_intent)
        self._maybe_crash(CrashPoint.AFTER_BROKER_SUBMIT)
        self._record_submit_result(intent, order_intent, result)

    def _record_submit_result(
        self, intent: ExecutionIntent, order_intent: OrderIntent, result
    ) -> None:
        if result.ok:
            self._store.update_intent(
                intent.intent_id,
                state=IntentState.INTENT_SUBMITTED.value,
                broker_order_id=result.broker_order_id,
            )
            self._store.record_broker_order(
                result.broker_order_id,
                intent.intent_id,
                order_intent.symbol,
                order_intent.side.value,
                order_intent.volume,
                order_intent.volume,
                "ACCEPTED",
                intent.ownership_tag,
            )
            self._store.append_event(
                "ORDER_SUBMITTED",
                dedup_key=f"order:{intent.intent_id}",
                payload={"broker_order_id": result.broker_order_id},
            )
            self._verify_fill(intent, order_intent, result.broker_order_id)
        else:
            if result.error_category is BrokerErrorCategory.ORDER_REJECTED:
                state = IntentState.INTENT_REJECTED.value
            else:
                state = IntentState.INTENT_TRANSPORT_ERROR.value
            self._store.update_intent(
                intent.intent_id, state=state, reason=result.reason
            )
            self._store.append_event(
                "ORDER_REJECTED" if state == IntentState.INTENT_REJECTED.value else "ORDER_TRANSPORT_ERROR",
                dedup_key=f"rej:{intent.intent_id}",
                payload={"reason": result.reason, "error_category": result.error_category.value},
            )

    def _verify_fill(
        self, intent: ExecutionIntent, order_intent: OrderIntent, broker_order_id: str
    ) -> None:
        snapshot = self._broker.reconcile_snapshot()
        matches = [p for p in snapshot.positions if p.ownership_tag == intent.ownership_tag]
        if not matches:
            # Accepted order but zero fill: NEVER mark OPEN_VERIFIED.
            self._store.update_intent(
                intent.intent_id,
                state=IntentState.INTENT_ABORTED.value,
                reason="zero fill",
            )
            self._store.upsert_owned_position(
                intent.logical_ownership_id,
                runtime_id=intent.runtime_id,
                account_id=intent.account_id,
                strategy_id=intent.strategy_id,
                intent_id=intent.intent_id,
                event_id=intent.event_id,
                symbol=intent.broker_symbol,
                side=intent.side,
                requested_quantity=order_intent.volume,
                filled_quantity=0.0,
                state=PositionState.ABORTED.value,
                broker_position_id="",
                broker_order_id=broker_order_id,
                ownership_tag=intent.ownership_tag,
                fill_price=None,
            )
            return
        pos = matches[0]
        filled = float(pos.volume)
        full = filled >= order_intent.volume - 1e-9
        pos_state = PositionState.FILLED.value if full else PositionState.PARTIALLY_FILLED.value
        intent_state = IntentState.INTENT_FILLED.value if full else IntentState.INTENT_PARTIALLY_FILLED.value
        self._store.update_intent(
            intent.intent_id,
            state=intent_state,
            broker_position_id=pos.position_id,
            filled_quantity=filled,
            fill_price=pos.price_open,
        )
        self._store.upsert_owned_position(
            intent.logical_ownership_id,
            runtime_id=intent.runtime_id,
            account_id=intent.account_id,
            strategy_id=intent.strategy_id,
            intent_id=intent.intent_id,
            event_id=intent.event_id,
            symbol=intent.broker_symbol,
            side=intent.side,
            requested_quantity=order_intent.volume,
            filled_quantity=filled,
            state=pos_state,
            broker_position_id=pos.position_id,
            broker_order_id=broker_order_id,
            ownership_tag=intent.ownership_tag,
            fill_price=pos.price_open,
        )
        event_name = "POSITION_OPEN_VERIFIED" if full else "PARTIAL_FILL_OBSERVED"
        self._store.append_event(
            event_name,
            dedup_key=f"open:{intent.intent_id}",
            payload={"position_id": pos.position_id, "filled": filled},
        )

    def _process_exit(self, event: StrategyEvent) -> None:
        open_positions = self._store.owned_positions()
        open_positions = [
            p for p in open_positions
            if p.state in (PositionState.FILLED.value, PositionState.PARTIALLY_FILLED.value)
        ]
        if not open_positions:
            return
        for pos in open_positions:
            self._close_position(event, pos)

    def _close_position(self, event: StrategyEvent, pos) -> None:
        # Durable close intent (write-ahead for the exit).
        self._store.upsert_owned_position(
            pos.logical_ownership_id,
            runtime_id=pos.runtime_id,
            account_id=pos.account_id,
            strategy_id=pos.strategy_id,
            intent_id=pos.intent_id,
            event_id=pos.event_id,
            symbol=pos.symbol,
            side=pos.side,
            requested_quantity=pos.requested_quantity,
            filled_quantity=pos.filled_quantity,
            state=PositionState.CLOSE_PENDING.value,
            broker_position_id=pos.broker_position_id,
            broker_order_id=pos.broker_order_id,
            ownership_tag=pos.ownership_tag,
            fill_price=pos.fill_price,
        )
        self._store.append_event(
            "EXIT_REQUESTED",
            dedup_key=f"exit:{event.event_id}:{pos.logical_ownership_id}",
            payload={"event_id": event.event_id, "position_id": pos.broker_position_id},
        )
        result = self._broker.close_position(pos.broker_position_id, reason="strategy exit")
        self._maybe_crash(CrashPoint.AFTER_CLOSE_SUBMIT)
        if result.ok:
            self._store.update_intent(pos.intent_id, state=IntentState.INTENT_CLOSED.value)
            self._store.upsert_owned_position(
                pos.logical_ownership_id,
                runtime_id=pos.runtime_id,
                account_id=pos.account_id,
                strategy_id=pos.strategy_id,
                intent_id=pos.intent_id,
                event_id=pos.event_id,
                symbol=pos.symbol,
                side=pos.side,
                requested_quantity=pos.requested_quantity,
                filled_quantity=pos.filled_quantity,
                state=PositionState.CLOSED.value,
                broker_position_id=pos.broker_position_id,
                broker_order_id=pos.broker_order_id,
                ownership_tag=pos.ownership_tag,
                fill_price=pos.fill_price,
            )
            self._store.append_event(
                "POSITION_CLOSED_VERIFIED",
                dedup_key=f"closed:{pos.logical_ownership_id}",
                payload={"position_id": pos.broker_position_id},
            )
        else:
            self._store.append_event(
                "CLOSE_REJECTED",
                dedup_key=f"close-rej:{pos.logical_ownership_id}",
                payload={"reason": result.reason},
            )

    # ── recovery helpers ──────────────────────────────────────────────────

    def _retry_pending_intents(self) -> None:
        for intent in self._store.intents():
            if intent.state in (
                IntentState.INTENT_CREATED.value,
                IntentState.INTENT_SUBMITTED.value,
            ) and not intent.broker_position_id:
                self._resubmit_intent(intent.intent_id)

    def _resubmit_intent(self, intent_id: str) -> None:
        row = self._store.intent_row(intent_id)
        if row is None:
            return
        side = OrderSide(row["side"]) if row["side"] in ("BUY", "SELL") else OrderSide.BUY
        order_intent = OrderIntent(
            intent_id=row["intent_id"],
            account_id=row["account_id"],
            symbol=row["broker_symbol"],
            side=side,
            volume=float(row["broker_quantity"] or 0.0),
            order_type=OrderType.MARKET,
            broker_magic=int(row["broker_magic"] or 0),
            ownership_tag=row["ownership_tag"] or "",
        )
        result = self._broker.submit_order(order_intent)
        if result.ok:
            self._store.update_intent(
                intent_id,
                state=IntentState.INTENT_SUBMITTED.value,
                broker_order_id=result.broker_order_id,
            )
            # Re-verify fill using the durable intent fields.
            intent = ExecutionIntent(
                intent_id=row["intent_id"],
                runtime_id=row["runtime_id"],
                account_id=row["account_id"],
                strategy_id=row["strategy_id"],
                deployment_generation=row["deployment_generation"],
                event_id=row["event_id"],
                economic_target_id=row["economic_target_id"],
                instrument=row["instrument"],
                broker_symbol=row["broker_symbol"],
                side=row["side"],
                broker_quantity=float(row["broker_quantity"] or 0.0),
                logical_ownership_id=row["logical_ownership_id"],
                ownership_tag=row["ownership_tag"] or "",
                broker_magic=int(row["broker_magic"] or 0),
            )
            self._verify_fill(intent, order_intent, result.broker_order_id)
        else:
            self._store.update_intent(
                intent_id,
                state=IntentState.INTENT_TRANSPORT_ERROR.value,
                reason=result.reason,
            )

    def _reconstruct_from_broker(self, snapshot) -> None:
        ours = [
            p for p in snapshot.positions
            if p.ownership_tag
            and any(i.ownership_tag == p.ownership_tag for i in self._store.intents())
        ]
        for pos in ours:
            intent = next(
                (i for i in self._store.intents() if i.ownership_tag == pos.ownership_tag),
                None,
            )
            if intent is None:
                continue
            row = self._store.intent_row(intent.intent_id)
            if row is None:
                continue
            full = float(pos.volume) >= float(row["broker_quantity"] or 0.0) - 1e-9
            state = PositionState.FILLED.value if full else PositionState.PARTIALLY_FILLED.value
            intent_state = IntentState.INTENT_FILLED.value if full else IntentState.INTENT_PARTIALLY_FILLED.value
            self._store.update_intent(
                intent.intent_id,
                state=intent_state,
                broker_position_id=pos.position_id,
                broker_order_id=row["broker_order_id"],
                filled_quantity=float(pos.volume),
                fill_price=pos.price_open,
            )
            self._store.upsert_owned_position(
                row["logical_ownership_id"],
                runtime_id=row["runtime_id"],
                account_id=row["account_id"],
                strategy_id=row["strategy_id"],
                intent_id=row["intent_id"],
                event_id=row["event_id"],
                symbol=row["broker_symbol"],
                side=row["side"],
                requested_quantity=float(row["broker_quantity"] or 0.0),
                filled_quantity=float(pos.volume),
                state=state,
                broker_position_id=pos.position_id,
                broker_order_id=row["broker_order_id"],
                ownership_tag=pos.ownership_tag,
                fill_price=pos.price_open,
            )
            self._store.append_event(
                "POSITION_OPEN_VERIFIED",
                dedup_key=f"reconstruct-open:{intent.intent_id}",
                payload={"position_id": pos.position_id},
            )

    def _mark_close_pending_closed(self) -> None:
        for pos in self._store.owned_positions():
            if pos.state == PositionState.CLOSE_PENDING.value:
                self._store.update_intent(pos.intent_id, state=IntentState.INTENT_CLOSED.value)
                self._store.upsert_owned_position(
                    pos.logical_ownership_id,
                    runtime_id=pos.runtime_id,
                    account_id=pos.account_id,
                    strategy_id=pos.strategy_id,
                    intent_id=pos.intent_id,
                    event_id=pos.event_id,
                    symbol=pos.symbol,
                    side=pos.side,
                    requested_quantity=pos.requested_quantity,
                    filled_quantity=pos.filled_quantity,
                    state=PositionState.CLOSED.value,
                    broker_position_id=pos.broker_position_id,
                    broker_order_id=pos.broker_order_id,
                    ownership_tag=pos.ownership_tag,
                    fill_price=pos.fill_price,
                )
                self._store.append_event(
                    "POSITION_CLOSED_VERIFIED",
                    dedup_key=f"reconstruct-closed:{pos.logical_ownership_id}",
                    payload={"position_id": pos.broker_position_id},
                )

    def _retry_close(self) -> None:
        for pos in self._store.owned_positions():
            if pos.state == PositionState.CLOSE_PENDING.value and pos.broker_position_id:
                result = self._broker.close_position(pos.broker_position_id, reason="recover close")
                if result.ok:
                    self._store.update_intent(pos.intent_id, state=IntentState.INTENT_CLOSED.value)
                    self._store.upsert_owned_position(
                        pos.logical_ownership_id,
                        runtime_id=pos.runtime_id,
                        account_id=pos.account_id,
                        strategy_id=pos.strategy_id,
                        intent_id=pos.intent_id,
                        event_id=pos.event_id,
                        symbol=pos.symbol,
                        side=pos.side,
                        requested_quantity=pos.requested_quantity,
                        filled_quantity=pos.filled_quantity,
                        state=PositionState.CLOSED.value,
                        broker_position_id=pos.broker_position_id,
                        broker_order_id=pos.broker_order_id,
                        ownership_tag=pos.ownership_tag,
                        fill_price=pos.fill_price,
                    )

    # ── helpers ───────────────────────────────────────────────────────────

    def _bound_account_snapshot(self) -> BoundAccountSnapshot:
        acct = self._broker.account_state()
        return BoundAccountSnapshot(
            account_id=self._account.account_id,
            account_role=self._account.account_role,
            portfolio_group_id=self._account.portfolio_group_id or "",
            equity=acct.equity,
            account_currency=acct.currency,
            observed_at=self._clock(),
        )

    def _resolve_desired_state(self) -> DesiredState:
        stored = self._store.read_desired_state()
        if stored == DesiredState.STOPPED_BY_USER.value:
            self._desired_state = DesiredState.STOPPED_BY_USER
        else:
            self._desired_state = DesiredState.RUNNING
        return self._desired_state

    def _maybe_crash(self, point: CrashPoint) -> None:
        if self._crash_point is point:
            raise SimulatedCrash(f"simulated crash at {point.value}")

    def _set_state(self, new_state: RuntimeState) -> None:
        if self._state is new_state:
            return
        validate_transition(self._state, new_state)
        self._state = new_state

    def _release_singleton(self) -> None:
        try:
            self._singleton.release()
        except Exception:  # noqa: BLE001
            pass

    def _persist_heartbeat(self) -> None:
        hb = Heartbeat(
            runtime_id=self._profile.runtime_id,
            state=self._state.value,
            desired_state=self._resolve_desired_state().value,
            observed_at=self._clock(),
            broker_connected=bool(self._broker.health().get("connected", False)),
            last_reconciliation_state=(
                self._reconciliation.state.value if self._reconciliation else ""
            ),
            last_strategy_event_id=self._last_strategy_event_id,
            blocking_reason=self._blocking_reason,
        )
        self._store.record_heartbeat(
            hb.runtime_id, hb.state, hb.desired_state, hb.blocking_reason
        )

    def telemetry(self) -> TelemetrySnapshot:
        # Recompute a FRESH reconciliation view so counts reflect the CURRENT
        # broker/ledger state (events processed this step included).
        snapshot = self._broker.reconcile_snapshot()
        rec = self._reconciler.reconcile(
            broker_positions=snapshot.positions,
            owned_positions=self._store.owned_positions(),
            intents=self._store.intents(),
        )
        authority = self._current_authority()
        unresolved = len(
            [
                i
                for i in self._store.intents()
                if i.state in (
                    IntentState.INTENT_CREATED.value,
                    IntentState.INTENT_SUBMITTED.value,
                    IntentState.INTENT_PARTIALLY_FILLED.value,
                )
            ]
        )
        return TelemetrySnapshot(
            runtime_id=self._profile.runtime_id,
            account_id=self._account.account_id,
            strategy_id=self._strategy_context.strategy_id,
            runtime_state=self._state.value,
            desired_state=self._resolve_desired_state().value,
            broker_connected=bool(self._broker.health().get("connected", False)),
            identity_match=self._identity_match,
            reconciliation_state=rec.state.value,
            reconciliation_clean=rec.clean,
            new_risk_authorized=authority.can_submit_new_risk,
            owned_positions_count=rec.owned_count,
            foreign_positions_count=rec.foreign_count,
            unresolved_intents=unresolved,
            last_heartbeat="",
            last_error=self._last_error,
            blocking_reason=self._blocking_reason,
            blockers=authority.reasons,
        )
