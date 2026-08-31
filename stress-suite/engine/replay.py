"""Deterministic replay (G1 §15). initial state + ordered event stream +
versioned contracts -> terminal state + transition trace.

Same inputs and same contract versions must produce identical output — no model
call, no wall-clock dependence. Timestamps are injected via ReplayClock or
derived from ordering (seq).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence

from .base import ReplayClock
from .lifecycle import KnowledgeRecord, LifecycleEngine, LifecycleEdgeTable
from .phase import PhaseStateMachine, PhaseEdgeTable


class ReplayInputError(ValueError):
    pass


@dataclass(frozen=True)
class ReplayEvent:
    seq: int
    event_type: str                # "phase_step" | "lifecycle_step"
    machine: str                   # "phase" | "lifecycle"
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
    """Runs an event stream against fresh machine instances and returns a stable
    fingerprint. Events are applied in strict seq order; out-of-order or duplicate
    seq detection makes malformed streams fail closed."""

    def __init__(
        self,
        phase_graph: Optional[PhaseEdgeTable] = None,
        lifecycle_table: Optional[LifecycleEdgeTable] = None,
        clock: Optional[ReplayClock] = None,
        seed_records: Optional[Sequence[KnowledgeRecord]] = None,
    ):
        self.phase = PhaseStateMachine(edge_table=phase_graph or PhaseEdgeTable.default(), initial="STABLE")
        self.lifecycle = LifecycleEngine(edge_table=lifecycle_table or LifecycleEdgeTable.default())
        for r in seed_records or []:
            self.lifecycle.add(r)
        self.clock = clock or ReplayClock()

    def run(self, events: Sequence[ReplayEvent]) -> ReplayResult:
        trace: List[dict] = []
        # deterministic replay preserves the GIVEN order; enforce strict seq growth
        prev = -1
        for ev in events:
            if ev.seq <= prev:
                raise ReplayInputError(f"out-of-order seq {ev.seq} after {prev}")
            prev = ev.seq

        for ev in events:
            ts = self.clock.stamp(ev.seq)
            if ev.machine == "phase":
                decision = self.phase.attempt(
                    seq=ev.seq, actor=ev.actor, to_state=ev.payload.get("to_state", ""),
                    evidence_vector=ev.payload.get("evidence_vector", {}), authority_level=ev.payload.get("authority_level", "OBSERVER"),
                    mutation_class=ev.payload.get("mutation_class", "READ_ONLY"),
                    operator_required=ev.payload.get("operator_required", False),
                    evidence_refs=ev.payload.get("evidence_refs", []),
                    reason=ev.payload.get("reason", ""), timestamp=ts,
                )
                trace.append({"seq": ev.seq, "machine": "phase", "allowed": decision.allowed,
                              "from": decision.phase_from, "to": decision.phase_to, "rationale": decision.rationale})
            elif ev.machine == "lifecycle":
                rec = self.lifecycle.get(ev.target)
                if rec is None:
                    trace.append({"seq": ev.seq, "machine": "lifecycle", "allowed": False,
                                  "from": "?", "to": ev.payload.get("to_state", ""), "rationale": "unknown record"})
                    continue
                tr = rec.transition(
                    seq=ev.seq, to_state=ev.payload.get("to_state", ""), actor=ev.actor,
                    authority_basis=ev.payload.get("authority_basis", ""), authority_level=ev.payload.get("authority_level", "OBSERVER"),
                    reason=ev.payload.get("reason", ""), evidence_refs=ev.payload.get("evidence_refs", []), timestamp=ts,
                )
                trace.append({"seq": ev.seq, "machine": "lifecycle", "allowed": (rec.state == tr.to_state),
                              "from": tr.from_state, "to": tr.to_state, "rationale": tr.reason})
            else:
                raise ReplayInputError(f"unknown machine {ev.machine}")

        terminal_lifecycle = {rid: r.state for rid, r in self.lifecycle.records.items()}
        fp = deterministic_fp(self.phase.state, terminal_lifecycle, trace)
        return ReplayResult(
            terminal_phase=self.phase.state,
            terminal_lifecycle=terminal_lifecycle,
            trace=trace,
            fingerprint=fp,
        )


def deterministic_fp(phase: str, lifecycle: Dict[str, str], trace: List[dict]) -> str:
    from .base import deterministic_hex
    return deterministic_hex("replay", phase, lifecycle, trace, length=32)