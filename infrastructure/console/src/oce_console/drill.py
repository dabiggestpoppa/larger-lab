"""Drill session, playbook and evidence binding (B5-I5; I-5 + I-6 B5-I5 half).

Provides the console-side constructs for a bounded, versioned recovery-drill
session (charter sections 8.1/9; I-5 G9/G5; I-6 G8/S-3):

- ``Playbook`` — a versioned, bounded step list. Unknown or over-bound steps
  are refused fail-closed BEFORE any action (Gate G5). No drill logic exists
  outside the playbook (I-5 non-goal).
- ``SessionRecorder`` — an APPEND-ONLY, schema-validated session record
  ``{session_id, playbook_version, actions[], drill_report_ref}``
  (charter section 8.1). Actions are appended in order; the record never
  mutates an existing action.
- ``bind_evidence`` — Gate G9: anchors the timeline to the engine's own job
  operation identity (``job_id`` + ``payload_hash`` + ``evidence_refs``) with
  a deterministic timeline digest, so the binding references the correct
  operation. The authoritative artifact digest stays engine-owned
  (``EvidenceBuilder.outer_digest``); this record is the console's reference,
  cross-checked against the engine by a two-sided test.
- ``build_drill_report`` — the drill report carrying the no-duplicate-effect
  check result and a disposition (``DRILL_PASS`` after a completed drill,
  I-6 evidence).

Engine-ownership law (Gate G8): this module performs NO recovery, re-queue,
lease or state write. It only records observations and computes digests over
data it is handed. The console observes; the engine enacts.

Client-only: imports no ``oce_control`` module and no store/model runtime.
Stdlib only; no LLM; no provider.
"""
from __future__ import annotations

import json
from typing import Iterable, List, Optional, Sequence

PLAYBOOK_VERSION = "1.0.0"
SESSION_SCHEMA_VERSION = "1.0.0"

# The bounded drill step vocabulary (S-3). A playbook may only use these, and
# is bounded to at most MAX_PLAYBOOK_STEPS steps (Gate G5: refused before side
# effects).
DRILL_STEPS = frozenset({
    "submit_representative_job",
    "observe_leased",
    "observe_worker_loss",
    "observe_requeued",
    "observe_succeeded",
    "check_duplicate_effect",
    "emit_report",
})
MAX_PLAYBOOK_STEPS = 8


class DrillRefusal(Exception):
    """Fail-closed refusal raised BEFORE any drill action/side effect."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail

    def to_dict(self) -> dict:
        return {"refusal": self.reason, "detail": self.detail}


class Playbook:
    """A versioned, bounded drill playbook (I-5; Gate G5)."""

    def __init__(self, version: str, steps: Sequence[str]):
        self.version = version
        self.steps = list(steps)
        self.validate()

    def validate(self) -> None:
        """Refuse an unknown or over-bound playbook before any action."""
        if len(self.steps) > MAX_PLAYBOOK_STEPS:
            raise DrillRefusal(
                "playbook_over_bound", f"{len(self.steps)} > {MAX_PLAYBOOK_STEPS}")
        unknown = [s for s in self.steps if s not in DRILL_STEPS]
        if unknown:
            raise DrillRefusal("playbook_unknown_step", str(sorted(set(unknown))))
        if not self.steps:
            raise DrillRefusal("playbook_empty", "no steps declared")


class SessionRecorder:
    """Append-only, schema-validated session record (charter section 8.1)."""

    def __init__(self, session_id: str, playbook: Playbook):
        self._record = {
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_id": session_id,
            "playbook_version": playbook.version,
            "actions": [],
            "drill_report_ref": "",
        }

    def append_action(self, step: str, detail: Optional[dict] = None) -> None:
        """Append one action in order. Existing actions are never mutated."""
        if step not in DRILL_STEPS:
            raise DrillRefusal("unknown_step", step)
        self._record["actions"].append({
            "seq": len(self._record["actions"]),
            "step": step,
            "detail": detail or {},
        })

    def set_report_ref(self, ref: str) -> None:
        self._record["drill_report_ref"] = ref

    def to_record(self) -> dict:
        """Return a validated copy of the session record."""
        record = json.loads(json.dumps(self._record))
        validate_session_record(record)
        return record


def validate_session_record(record: dict) -> None:
    """Structural schema validation for the session record (fail-closed)."""
    required = ("schema_version", "session_id", "playbook_version", "actions", "drill_report_ref")
    missing = [k for k in required if k not in record]
    if missing:
        raise DrillRefusal("session_record_missing_fields", str(missing))
    if not isinstance(record["session_id"], str) or not record["session_id"]:
        raise DrillRefusal("session_record_bad_session_id", repr(record["session_id"]))
    if not isinstance(record["playbook_version"], str) or not record["playbook_version"]:
        raise DrillRefusal("session_record_bad_playbook_version", repr(record["playbook_version"]))
    if not isinstance(record["actions"], list):
        raise DrillRefusal("session_record_actions_not_list", type(record["actions"]).__name__)
    for i, action in enumerate(record["actions"]):
        if not isinstance(action, dict) or action.get("seq") != i or "step" not in action:
            raise DrillRefusal("session_record_bad_action", f"index {i}")
        if action["step"] not in DRILL_STEPS:
            raise DrillRefusal("session_record_unknown_step", action["step"])
    if not isinstance(record["drill_report_ref"], str):
        raise DrillRefusal("session_record_bad_report_ref", type(record["drill_report_ref"]).__name__)


def bind_evidence(timeline: dict, job_envelope: dict,
                  operation: str = "jobs.submit") -> dict:
    """Gate G9: anchor the timeline to the engine's own operation identity.

    The binding references the governed job's ``job_id``, ``payload_hash`` and
    ``evidence_refs`` (the engine's own identity/evidence pointers) plus a
    deterministic digest over the timeline, so the console's timeline is bound
    to the correct operation. The authoritative artifact digest remains
    engine-owned; this record is the console reference cross-checked against
    the engine by a two-sided test.
    """
    if not isinstance(job_envelope, dict) or "job_id" not in job_envelope:
        raise DrillRefusal("evidence_binding_no_operation", "job envelope missing job_id")
    # §8 fail-closed guards (B5-I5 R5): denial payloads, incomplete identity
    # and cross-job evidence never enter the bound-success domain.
    if "denial" in job_envelope:
        raise DrillRefusal("evidence_binding_denial_envelope", "denial payload refused")
    payload_hash = job_envelope.get("payload_hash")
    if not isinstance(payload_hash, str) or not payload_hash:
        raise DrillRefusal("evidence_binding_no_payload_hash",
                           "engine payload_hash missing — evidence not bound")
    if "evidence_refs" not in job_envelope or not isinstance(
            job_envelope.get("evidence_refs"), list):
        raise DrillRefusal("evidence_binding_no_evidence_refs",
                           "engine evidence_refs missing — evidence not bound")
    timeline_job = timeline.get("job_id", "") if isinstance(timeline, dict) else ""
    if timeline_job and timeline_job != job_envelope["job_id"]:
        raise DrillRefusal(
            "evidence_binding_job_mismatch",
            f"timeline job {timeline_job!r} != envelope job {job_envelope['job_id']!r}",
        )
    # The console references the ENGINE-owned identity (job_id + payload_hash,
    # which is the engine's own sha256 of the payload, + evidence_refs) and
    # carries a deterministic canonical serialization of the timeline. It does
    # NOT mint a digest of its own: the authoritative digest stays engine-owned
    # (Gate G9), keeping the console import closure stdlib/hash-free.
    canonical = json.dumps({
        "operation": operation,
        "job_id": job_envelope.get("job_id", ""),
        "payload_hash": job_envelope.get("payload_hash", ""),
        "evidence_refs": job_envelope.get("evidence_refs", []),
        "timeline": timeline,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        "operation": operation,
        "job_id": job_envelope.get("job_id", ""),
        "payload_hash": job_envelope.get("payload_hash", ""),
        "evidence_refs": list(job_envelope.get("evidence_refs", [])),
        "timeline_canonical": canonical,
    }


def build_drill_report(session_record: dict, timeline: dict,
                       duplicate_effect_check: bool,
                       binding: dict,
                       disposition: str = "DRILL_PASS") -> dict:
    """Build the drill report (I-6 evidence): disposition + duplicate check.

    ``disposition`` is ``DRILL_PASS`` only when the caller has observed a
    completed drill whose engine-owned duplicate-effect check held; this
    function records the caller's observed result and never fabricates one.

    Fail-closed claim guard (B5-I5 R5 §8): ``DRILL_PASS`` is refused unless
    the engine-owned duplicate-effect check held AND this session's own
    append-only record contains that ``check_duplicate_effect`` observation —
    so a report can never be minted from an unobserved or reused session.
    """
    validate_session_record(session_record)
    binding_hash = binding.get("payload_hash", "")
    if not isinstance(binding_hash, str) or not binding_hash:
        raise DrillRefusal("drill_report_unbound",
                           "binding payload_hash missing — report not bound")
    if disposition == "DRILL_PASS":
        if duplicate_effect_check is not True:
            raise DrillRefusal(
                "drill_pass_requires_duplicate_effect_check",
                "engine-owned duplicate-effect check did not hold",
            )
        observed = [
            a for a in session_record["actions"]
            if a.get("step") == "check_duplicate_effect"
        ]
        if not observed:
            raise DrillRefusal(
                "drill_pass_requires_check_action",
                "session record contains no check_duplicate_effect observation",
            )
    # The report is digest-referenced via the ENGINE-owned identity carried by
    # the binding (payload_hash), never a console-minted digest (Gate G9).
    return {
        "kind": "oce-console-drill-report",
        "version": PLAYBOOK_VERSION,
        "session_id": session_record.get("session_id", ""),
        "disposition": disposition,
        "duplicate_effect_check": bool(duplicate_effect_check),
        "timeline_state": timeline.get("state", ""),
        "binding": {
            "operation": binding.get("operation", ""),
            "job_id": binding.get("job_id", ""),
            "payload_hash": binding.get("payload_hash", ""),
            "evidence_refs": list(binding.get("evidence_refs", [])),
        },
    }


def capture_authoritative_view(read_envelopes: Iterable[dict]) -> List[dict]:
    """Capture a stable, comparable view of governed job envelopes (G6 helper).

    Used to prove restart-identity: the console holds no state, so two
    independent captures of the same authoritative state (modulo request ids)
    are identical. Only canonical identity fields are captured; no console
    state is introduced.
    """
    view = []
    for env in read_envelopes:
        if not isinstance(env, dict):
            view.append({"unverifiable": True})
            continue
        view.append({
            "job_id": env.get("job_id", ""),
            "status": env.get("status", ""),
            "payload_hash": env.get("payload_hash", ""),
            "attempt_number": env.get("attempt_number", 0),
        })
    return sorted(view, key=lambda v: v.get("job_id", ""))
