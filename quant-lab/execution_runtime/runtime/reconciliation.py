"""QL-EXEC-R3 — broker/local reconciliation.

Pure logic over two inputs: the durable local ledger (owned positions + intents)
and the broker snapshot (positions). It NEVER sends orders and NEVER closes
positions; divergence is classified, never silently "repaired".

Ownership is explicit: a broker position belongs to this runtime only when its
ownership tag matches a durable local intent/owned-position tag (or its magic
matches the runtime magic). Foreign positions are reported and NEVER touched.

R3 is deliberately single-position: the classifier assumes at most one owned
exposure, so any duplicate owned exposure is flagged rather than averaged.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..types import Position
from .intent import IntentState, PositionState


class ReconciliationState(str, Enum):
    """Frozen R3 reconciliation taxonomy (smallest useful set)."""

    FLAT_MATCH = "FLAT_MATCH"
    OPEN_MATCH = "OPEN_MATCH"
    CLOSED_MATCH = "CLOSED_MATCH"
    LOCAL_INTENT_BROKER_MISSING = "LOCAL_INTENT_BROKER_MISSING"
    BROKER_OWNED_LOCAL_MISSING = "BROKER_OWNED_LOCAL_MISSING"
    DUPLICATE_OWNED_EXPOSURE = "DUPLICATE_OWNED_EXPOSURE"
    FOREIGN_ONLY = "FOREIGN_ONLY"
    AMBIGUOUS = "AMBIGUOUS"
    ERROR = "ERROR"


# States in which new risk may proceed (reconciliation is clean).
CLEAN_STATES = frozenset(
    {
        ReconciliationState.FLAT_MATCH,
        ReconciliationState.OPEN_MATCH,
        ReconciliationState.CLOSED_MATCH,
        ReconciliationState.FOREIGN_ONLY,
    }
)


@dataclass(frozen=True)
class ReconciliationResult:
    """Deterministic outcome of one reconciliation pass."""

    state: ReconciliationState
    clean: bool
    blocked_reason: str = ""
    owned_count: int = 0
    foreign_count: int = 0
    recoverable: bool = False
    action: str = "NONE"  # NONE / RETRY / RECONSTRUCT / BLOCK
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "clean": self.clean,
            "blocked_reason": self.blocked_reason,
            "owned_count": self.owned_count,
            "foreign_count": self.foreign_count,
            "recoverable": self.recoverable,
            "action": self.action,
            "detail": self.detail,
        }


class Reconciler:
    """Compare durable local truth vs broker truth (single-position R3 model)."""

    def __init__(self, *, runtime_magic: int = 0) -> None:
        self._runtime_magic = runtime_magic

    def _is_ours(self, pos: Position, known_tags: set[str]) -> bool:
        if self._runtime_magic and pos.magic == self._runtime_magic:
            return True
        return bool(pos.ownership_tag) and pos.ownership_tag in known_tags

    def reconcile(
        self,
        *,
        broker_positions: tuple[Position, ...],
        owned_positions,
        intents,
    ) -> ReconciliationResult:
        """Reconcile durable local truth against broker positions.

        ``owned_positions``: iterable of OwnedPositionRecord.
        ``intents``: iterable of IntentRecord.
        """
        try:
            return self._reconcile(
                broker_positions=broker_positions,
                owned_positions=list(owned_positions),
                intents=list(intents),
            )
        except Exception as exc:  # noqa: BLE001 - never mask reconciliation errors
            return ReconciliationResult(
                state=ReconciliationState.ERROR,
                clean=False,
                blocked_reason=f"reconciliation errored: {exc}",
                action="BLOCK",
                detail=str(exc),
            )

    def _reconcile(self, *, broker_positions, owned_positions, intents) -> ReconciliationResult:
        exposed = [
            o for o in owned_positions
            if o.state in (
                PositionState.FILLED.value,
                PositionState.PARTIALLY_FILLED.value,
                PositionState.CLOSE_PENDING.value,
            )
        ]
        closed = [o for o in owned_positions if o.state == PositionState.CLOSED.value]
        pending_intents = [
            i for i in intents
            if i.state in (IntentState.INTENT_CREATED.value, IntentState.INTENT_SUBMITTED.value)
            and not i.broker_position_id
        ]
        known_tags = {o.ownership_tag for o in owned_positions if o.ownership_tag}
        known_tags |= {i.ownership_tag for i in intents if i.ownership_tag}

        ours: list[Position] = []
        foreign: list[Position] = []
        for p in broker_positions:
            if self._is_ours(p, known_tags):
                ours.append(p)
            else:
                foreign.append(p)

        # Duplicate owned exposure: same ownership tag on >1 broker position.
        tag_counts: dict[str, int] = {}
        for p in ours:
            if p.ownership_tag:
                tag_counts[p.ownership_tag] = tag_counts.get(p.ownership_tag, 0) + 1
        dups = [t for t, n in tag_counts.items() if n > 1]
        if dups:
            return ReconciliationResult(
                state=ReconciliationState.DUPLICATE_OWNED_EXPOSURE,
                clean=False,
                blocked_reason="duplicate owned broker exposure",
                owned_count=len(ours),
                foreign_count=len(foreign),
                action="BLOCK",
                detail=f"duplicate owned positions for tags={sorted(dups)}",
            )

        # No local exposed position.
        if not exposed:
            if ours:
                return ReconciliationResult(
                    state=ReconciliationState.BROKER_OWNED_LOCAL_MISSING,
                    clean=False,
                    blocked_reason="broker owned position with no local open record",
                    owned_count=len(ours),
                    foreign_count=len(foreign),
                    recoverable=True,
                    action="RECONSTRUCT",
                    detail="broker has our-tagged position but local ledger has no open position",
                )
            if pending_intents:
                # Intent written (or submitted) but broker is flat: crash before
                # submit, or zero fill. Safe to retry the SAME deterministic intent.
                return ReconciliationResult(
                    state=ReconciliationState.LOCAL_INTENT_BROKER_MISSING,
                    clean=False,
                    blocked_reason="pending intent with no broker exposure",
                    owned_count=0,
                    foreign_count=len(foreign),
                    recoverable=True,
                    action="RETRY",
                    detail="pending intent, broker flat (safe retry)",
                )
            if closed:
                return ReconciliationResult(
                    state=ReconciliationState.CLOSED_MATCH,
                    clean=True,
                    owned_count=0,
                    foreign_count=len(foreign),
                    action="NONE",
                    detail="closed locally, broker flat",
                )
            if foreign:
                return ReconciliationResult(
                    state=ReconciliationState.FOREIGN_ONLY,
                    clean=True,
                    owned_count=0,
                    foreign_count=len(foreign),
                    action="NONE",
                    detail="flat locally; foreign positions present (off-limits)",
                )
            return ReconciliationResult(
                state=ReconciliationState.FLAT_MATCH,
                clean=True,
                owned_count=0,
                foreign_count=0,
                action="NONE",
                detail="flat/flat healthy",
            )

        # Local exposure exists: every exposed position must have a broker match.
        broker_tags = {p.ownership_tag for p in ours}
        unmatched = [o for o in exposed if o.ownership_tag not in broker_tags]
        if unmatched:
            # A CLOSE_PENDING position missing at broker means the close completed
            # at the broker but the local result was not recorded (crash window).
            if all(o.state == PositionState.CLOSE_PENDING.value for o in unmatched):
                return ReconciliationResult(
                    state=ReconciliationState.CLOSED_MATCH,
                    clean=False,
                    blocked_reason="close completed at broker but not recorded locally",
                    owned_count=len(ours),
                    foreign_count=len(foreign),
                    recoverable=True,
                    action="RECONSTRUCT",
                    detail="close pending, broker flat (mark closed)",
                )
            return ReconciliationResult(
                state=ReconciliationState.AMBIGUOUS,
                clean=False,
                blocked_reason="local open exposure missing at broker",
                owned_count=len(ours),
                foreign_count=len(foreign),
                action="BLOCK",
                detail=f"open positions missing at broker: "
                        f"{[o.logical_ownership_id for o in unmatched]}",
            )

        # A CLOSE_PENDING position still present at broker means the close has not
        # completed -> retry the close (recoverable, never silent).
        close_pending = [o for o in exposed if o.state == PositionState.CLOSE_PENDING.value]
        if close_pending:
            return ReconciliationResult(
                state=ReconciliationState.OPEN_MATCH,
                clean=False,
                blocked_reason="close pending, broker still holds position",
                owned_count=len(ours),
                foreign_count=len(foreign),
                recoverable=True,
                action="CLOSE_RETRY",
                detail="close in flight; retry close",
            )

        return ReconciliationResult(
            state=ReconciliationState.OPEN_MATCH,
            clean=True,
            owned_count=len(ours),
            foreign_count=len(foreign),
            action="NONE",
            detail="local open exposure matches broker",
        )
