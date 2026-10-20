"""Console-local durable session store (B5-I6; C4.S4 recovery + F-4/F-6).

Persistence for the charter section 8.1 session record — the console's ONLY
permitted local write (charter section 5: "the console's own writes are
limited to its append-only local session records"). This module never
touches canonical state: it writes exactly one console-local JSON file per
session, validated fail-closed by the frozen B5-I5 record validator
(``drill.validate_session_record``) before every write and every read.

Laws made executable here (charter sections 5/9; plan section 5 C4.S3/S4):

- **Append-only (F-4/§9 Interruption):** a stored record may only ever GROW
  by appending — the previously stored action list must remain a byte-exact
  prefix. Prior actions can never be rewritten, reordered or removed.
- **Partial by construction:** every persisted record carries
  ``status: "partial"``; only an explicit completion flip with a non-empty
  ``drill_report_ref`` writes ``status: "complete"``. A console killed
  mid-drill therefore leaves a durable PARTIAL record — never a false
  completion — with every pre-crash action already flushed (RPO 0 for the
  console record).
- **Completion is terminal:** once a record is ``complete`` it can never be
  mutated or re-completed; a later save or resume is refused fail-closed.
- **Consent-governed replay (F-6):** ``resume`` refuses without explicit
  operator consent and refuses a completed session, so a drill replay can
  only re-execute remaining steps with consent, never silently.
- **Fail-closed storage:** unknown session, torn/corrupt file, invalid
  status, malformed id (traversal chars) → ``DrillRefusal`` before any
  action; a corrupt file is never fabricated into a record.

Determinism: the file is a canonical (sorted-keys) JSON document written
atomically (temp file + replace); identical records serialize
byte-identically. Durability = close/flush of a completed write (no fsync
claim). Client-only: imports no ``oce_control`` module; stdlib only
(json, pathlib, typing — inside the frozen B5-I4 import allowlist); no LLM,
no provider, no network.
"""
from __future__ import annotations

import json
from pathlib import Path

from .drill import DrillRefusal, validate_session_record

SESSION_STATUS_PARTIAL = "partial"
SESSION_STATUS_COMPLETE = "complete"
SESSION_STATUSES = (SESSION_STATUS_PARTIAL, SESSION_STATUS_COMPLETE)
MAX_SESSION_ID_CHARS = 128
_RECORD_SUFFIX = ".json"


def _validate_session_id(session_id: str) -> str:
    """Refuse malformed/traversal session ids fail-closed (no I/O)."""
    sid = str(session_id)
    if not sid or len(sid) > MAX_SESSION_ID_CHARS:
        raise DrillRefusal("session_id_malformed", f"empty or over-long: {session_id!r}")
    if any(ch in sid for ch in ("/", "\\", "..", "%", "?", "#", "\r", "\n", "\t")):
        raise DrillRefusal("session_id_malformed", f"path-traversal or control char: {session_id!r}")
    return sid


class SessionStore:
    """Append-only, console-local persistence for session records."""

    def __init__(self, directory: Path | str):
        self._dir = Path(directory)

    @property
    def directory(self) -> Path:
        return self._dir

    def path_for(self, session_id: str) -> Path:
        """The single declared file path for a session (traversal-free)."""
        return self._dir / f"{_validate_session_id(session_id)}{_RECORD_SUFFIX}"

    def save(self, record: dict, *, complete: bool = False) -> dict:
        """Persist ``record`` fail-closed; returns the stored document.

        Refuses (before any write) when: the record fails the frozen
        schema validator; the session id is malformed; an existing record
        already completed (completion is terminal); the new action list
        would not be a pure append over the stored one; or ``complete``
        is requested without a non-empty ``drill_report_ref``.
        """
        if not isinstance(record, dict):
            raise DrillRefusal("session_record_not_an_object", type(record).__name__)
        validate_session_record(record)  # fail-closed on any schema breach
        sid = _validate_session_id(record.get("session_id", ""))
        path = self.path_for(sid)
        existing = self._load_existing(path, sid) if path.is_file() else None
        if existing is not None:
            if existing.get("status") == SESSION_STATUS_COMPLETE:
                raise DrillRefusal("session_already_complete",
                                   "a completed record is terminal (append-only)")
            old_actions = existing.get("actions", [])
            new_actions = record.get("actions", [])
            if (len(new_actions) < len(old_actions)
                    or new_actions[:len(old_actions)] != old_actions):
                raise DrillRefusal(
                    "session_record_not_append_only",
                    "prior actions must remain an unchanged prefix")
        if complete:
            if not str(record.get("drill_report_ref", "")):
                raise DrillRefusal("completion_requires_report_ref",
                                   "complete requires a non-empty drill_report_ref")
            status = SESSION_STATUS_COMPLETE
        else:
            status = SESSION_STATUS_PARTIAL
        document = json.loads(json.dumps(record))
        document["status"] = status
        validate_session_record(document)
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(document, indent=2, sort_keys=True,
                                  ensure_ascii=True) + "\n", encoding="utf-8")
        tmp.replace(path)
        return document

    def load(self, session_id: str) -> dict:
        """Load a stored record fail-closed; never fabricates a record."""
        path = self.path_for(session_id)
        if not path.is_file():
            raise DrillRefusal("unknown_session", str(session_id))
        return self._load_existing(path, str(session_id))

    def resume(self, session_id: str, *, consent: bool = False) -> dict:
        """F-6 consent gate: replay of a partial session needs consent.

        Returns the stored record only when the session exists, has not
        completed (completion is terminal), and the caller passes explicit
        operator ``consent``. Refuses fail-closed in every other case —
        before any action is taken.
        """
        record = self.load(session_id)
        if record.get("status") == SESSION_STATUS_COMPLETE:
            raise DrillRefusal("session_already_complete",
                               "a completed session is never replayed")
        if consent is not True:
            raise DrillRefusal("replay_consent_required",
                               "operator consent is required to resume a drill session")
        return record

    def _load_existing(self, path: Path, session_id: str) -> dict:
        """Read + validate one stored file; a torn/corrupt file refuses."""
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise DrillRefusal("session_record_corrupt",
                               f"{session_id}: {type(exc).__name__}") from exc
        if not isinstance(document, dict):
            raise DrillRefusal("session_record_corrupt",
                               f"{session_id}: not an object")
        validate_session_record(document)
        if document.get("status") not in SESSION_STATUSES:
            raise DrillRefusal("session_record_corrupt",
                               f"{session_id}: invalid status {document.get('status')!r}")
        if document.get("session_id") != _validate_session_id(session_id):
            raise DrillRefusal("session_record_corrupt",
                               f"{session_id}: file/record id mismatch")
        return document
