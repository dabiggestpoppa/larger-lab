"""Deterministic replay (G1 §15; HARDENED G1R-03/04/07).

initial state + ordered event stream + versioned contracts -> terminal state +
transition trace, all routed through the GovernedTransitionExecutor so
constitutional cross-cutting rules cannot be bypassed via a lower API.

Contract-version policy (G1R-04, documented):
  * If a ReplayEvent supplies `contract_version`, the active machine edge
    contract MUST match; otherwise the event FAILS CLOSED and is recorded as a
    deterministic invalid event (CONTRACT_VERSION_MISMATCH) with no state change.
  * A blank ``""``/None version means "use the active contract" — permitted for
    smoke fixtures ONLY.
Historical traces never silently execute under a different edge contract.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence

from .base import ReplayClock
from .governed import GovernedTransitionExecutor, TraceEntry
from .lifecycle import KnowledgeRecord, LifecycleEngine, LifecycleEdgeTable
from .phase import PhaseStateMachine, PhaseEdgeTable
from .authority import AuthorityState


class ReplayInputError(ValueError):
    pass


@dataclass(frozen=True)
class ReplayEvent:
    seq: int
    event_type: str                # e.g. "phase_step" | "lifecycle_step"
    machine: str                   # "phase" | "lifecycle" | "authority" | "evidence" | "policy"
    actor: str
    target: str                    # institution ("@INST") or knowledge record_id
    payload: Dict[str, Any]
    contract_version: str = ""


@dataclass
class ReplayResult:
    terminal_phase: str
    terminal_lifecycle: Dict[str, str]
    trace: List[dict]
    fingerprint: str

    def to_dict(self) -> dict:
        return asdict(self)


class DeterministicReplay:
    """Runs an event stream against a governed executor and returns a stable
    fingerprint. Events are applied in strict seq order; out-of-order or duplicate
    seq detection makes malformed streams fail closed. No model call, no
    wall-clock dependence."""

    def __init__(
        self,
        phase_graph: Optional[PhaseEdgeTable] = None,
        lifecycle_table: Optional[LifecycleEdgeTable] = None,
        clock: Optional[ReplayClock] = None,
        seed_records: Optional[Sequence[KnowledgeRecord]] = None,
        authority: Optional[AuthorityState] = None,
    ):
        self.phase = PhaseStateMachine(edge_table=phase_graph or PhaseEdgeTable.default(), initial="STABLE")
        self.lifecycle = LifecycleEngine(edge_table=lifecycle_table or LifecycleEdgeTable.default())
        self.authority = authority or AuthorityState()
        for r in seed_records or []:
            self.lifecycle.add(r)
        self.clock = clock or ReplayClock()
        self.executor = GovernedTransitionExecutor(self.phase, self.lifecycle, self.authority)

    def run(self, events: Sequence[ReplayEvent]) -> ReplayResult:
        if not isinstance(events, (list, tuple)):
            events = list(events)
        prev = -1
        for ev in events:
            if ev.seq <= prev:
                raise ReplayInputError(f"out-of-order seq {ev.seq} after {prev}")
            prev = ev.seq

        trace: List[dict] = []
        for ev in events:
            entry = self.executor.execute(ev)
            trace.append(entry.to_dict())

        terminal_lifecycle = {rid: r.state for rid, r in self.lifecycle.records.items()}
        fp = deterministic_fp(self.phase.state, terminal_lifecycle, trace)
        return ReplayResult(
            terminal_phase=self.phase.state,
            terminal_lifecycle=terminal_lifecycle,
            trace=trace,
            fingerprint=fp,
        )

    def ledger_trace(self) -> List[dict]:
        """Raw machine ledger (decisions/transitions) — for forensic audit."""
        out = []
        for d in self.phase.decisions:
            out.append(d.to_dict())
        for rid, rec in self.lifecycle.records.items():
            for t in rec.transitions:
                out.append(t.to_dict())
        return out


def deterministic_fp(phase: str, lifecycle: Dict[str, str], trace: List[dict]) -> str:
    from .base import deterministic_hex
    return deterministic_hex("replay", phase, lifecycle, trace, length=32)