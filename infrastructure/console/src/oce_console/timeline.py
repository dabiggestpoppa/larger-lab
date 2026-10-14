"""Dual-clock lifecycle timeline (B5-I5, charter increment I-4; S-2 + F-3).

Assembles a representative job's lifecycle from observed governed job
envelopes into a deterministic, reproducible timeline sorted on
**event-time** (the engine clock's own timestamp for each state) with
**knowledge-time** annotations (when the console observed that state).
Charter section 9 reconciliation: "Timeline assembled by sorting events on
event-time with knowledge-time annotations; deterministic and reproducible."

F-3 (B5-I3 registry, deferred to I-4): a partial/failed task renders its
``failure_envelope`` VERBATIM and is never summarized as ``succeeded`` —
no false success anywhere in the document.

Laws:
- event-time is derived ONLY from the governed envelope's own engine-clock
  fields (``created_at``, ``lease.leased_at``/``heartbeat_at``,
  ``result.completed_at``, ``failure_envelope.failed_at``); the console
  never invents a timestamp;
- knowledge-time is the console's own observation instant, carried beside
  each transition — never presented as event-time;
- sorting is total and deterministic (event_time, then observation
  sequence) so identical observations render byte-identically (S-2 gate:
  "timeline reproducible");
- the console holds no state: two renders of identical observations are
  byte-identical.

Client-only: imports no ``oce_control`` module and no store/model runtime.
Stdlib only; no LLM; no provider.
"""
from __future__ import annotations

import json
from typing import Iterable, Sequence, Tuple

TIMELINE_KIND = "oce-console-timeline"
TIMELINE_VERSION = "1.0.0"

# (knowledge_time_iso, governed_job_envelope_dict)
Observation = Tuple[str, dict]


def _event_time(status: str, env: dict) -> str:
    """Derive the engine event-time for an observed state, verbatim.

    Uses ONLY the governed envelope's own engine-clock fields. An unresolvable
    state falls back to ``created_at`` (still an engine value), never to a
    console-supplied time.
    """
    lease = env.get("lease") or {}
    result = env.get("result") or {}
    failure = env.get("failure_envelope") or {}
    if status == "succeeded" and result.get("completed_at"):
        return result["completed_at"]
    if status == "failed" and failure.get("failed_at"):
        return failure["failed_at"]
    if status == "running":
        return lease.get("heartbeat_at") or lease.get("leased_at") or env.get("created_at", "")
    if status in ("leased", "scheduled") and lease.get("leased_at"):
        return lease["leased_at"]
    return env.get("created_at", "")


def build_timeline(observations: Sequence[Observation]) -> dict:
    """Build the dual-clock timeline from ordered governed observations.

    ``observations`` is a sequence of ``(knowledge_time_iso, envelope)`` pairs
    in the order the console observed them. Returns a timeline document with
    a deterministic ``transitions`` list (sorted on event-time, observation
    sequence as the stable tiebreak) and a summary ``state``.
    """
    transitions = []
    job_id = ""
    for seq, (knowledge_time, env) in enumerate(observations):
        if not isinstance(env, dict):
            # An un-envelope observation is an explicit gap, never fabricated.
            transitions.append({
                "state": "UNVERIFIABLE",
                "event_time": "",
                "knowledge_time": knowledge_time,
                "sequence": seq,
                "reason": "response_not_an_envelope",
            })
            continue
        # A structurally incomplete dict (denial payload, partial or hostile
        # response) is NOT a job: it renders as an explicit gap, never as a
        # lifecycle state (B5-I5 R5, §7/§5 negative controls).
        if "denial" in env:
            # §7 law: a denial must never collapse into a lifecycle event.
            transitions.append({
                "state": "UNVERIFIABLE",
                "event_time": "",
                "knowledge_time": knowledge_time,
                "sequence": seq,
                "reason": "denial_envelope",
            })
            continue
        missing = [
            field for field in ("job_id", "status", "created_at")
            if not isinstance(env.get(field), str) or not env.get(field)
        ]
        if missing:
            transitions.append({
                "state": "UNVERIFIABLE",
                "event_time": "",
                "knowledge_time": knowledge_time,
                "sequence": seq,
                "reason": f"incomplete_envelope:{','.join(missing)}",
            })
            continue
        job_id = job_id or env.get("job_id", "")
        status = env.get("status", "")
        transition = {
            "state": status,
            "event_time": _event_time(status, env),
            "knowledge_time": knowledge_time,
            "sequence": seq,
        }
        # Render governed sub-objects verbatim (never rename/default).
        if env.get("failure_envelope"):
            transition["failure_envelope"] = env["failure_envelope"]
        if env.get("result"):
            transition["result"] = env["result"]
        if env.get("lease"):
            transition["lease"] = env["lease"]
        transitions.append(transition)

    transitions.sort(key=lambda t: (t["event_time"], t["sequence"]))
    return {
        "kind": TIMELINE_KIND,
        "version": TIMELINE_VERSION,
        "job_id": job_id,
        "transitions": transitions,
        "state": _summary_state(transitions),
    }


def _summary_state(transitions: Iterable[dict]) -> str:
    """Derive the timeline summary state — F-3: never a false success.

    The summary is the LAST transition's state in event-time order. A failed
    final state (with its failure envelope) is rendered ``failed``; it can
    never be summarized ``succeeded``. An all-unverifiable timeline is
    ``UNVERIFIABLE``.
    """
    last = None
    saw_envelope = False
    for t in transitions:
        last = t
        if t.get("failure_envelope"):
            saw_envelope = True
    if last is None:
        return "UNVERIFIABLE"
    if last["state"] == "UNVERIFIABLE":
        return "UNVERIFIABLE"
    if last["state"] == "failed" or (saw_envelope and last["state"] != "succeeded"):
        # F-3: a task that ended failed (or carries a failure envelope without
        # a later success) is reported failed — never green.
        return "failed"
    return last["state"]


def render_timeline(document: dict) -> str:
    """Deterministic render: identical documents -> byte-identical text."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
