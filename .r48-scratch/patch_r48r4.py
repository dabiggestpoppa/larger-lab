"""Rewrite `_classify_record_for_shell` as an explicit state dispatch table.

Behaviour is preserved exactly; the change is structural. Each durable state
gets ONE small pure handler, the verdict matrix is stated once, and the
cognitive complexity moves out of a single 100-line if-chain.
"""
import io
import os

CLI = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "infrastructure", "local-ground",
    "scripts", "pg-recovery.py"))

source = io.open(CLI, encoding="utf-8").read()

start = source.index("def _classify_record_for_shell(record, promote=None):")
end = source.index("def _test_classify_state_for_shell(record):")
head = source[:start]
tail = source[end:]

NEW = '''# B4-CXR7U9R48R4 -- ONE STATE DISPATCH TABLE
# ======================================================================
# R47's classifier was a single hundred-line if-chain. It was correct, but the
# verdict matrix was implicit: to answer "what does a ROLLING_BACK record with
# a spent selector produce", a reviewer had to read every branch above it in
# order. It also carried one function's worth of nesting on the two legs that
# matter most.
#
# The matrix is now STATED: one handler per durable state, one table, one
# dispatch. Each handler is PURE -- it reads only the immutable authority
# bundle and the record it was handed, and touches no filesystem. An unknown or
# contradictory state is not "unreachable": it is a table miss, and a miss is
# fail-closed by construction rather than by falling off the end of a chain.

_VERDICT_FRESH = 0
_VERDICT_NO_ROLLBACK = 3
_VERDICT_FAIL_CLOSED = 4
_VERDICT_FINALIZE_ABORT = 5
_VERDICT_ROLLBACK_RESUME = 6


def _classify_state_created(record, promote, authority):
    """A pre-promotion record offers no transition authority at all.

    With no promote receipt there is no exact binding to prove, so a canonical
    claim present at that coordinate is an impossible state/selector
    disagreement and fails closed. The documented pre-promotion disposition
    exists ONLY for the absent-selector shape the engine itself produces.
    """
    if promote is None and authority is not None:
        if _claim_state(authority.operation_id,
                        authority=authority) != "absent":
            return _VERDICT_FAIL_CLOSED
    return _VERDICT_FRESH


def _classify_state_promoted(record, promote, authority):
    """ONE admitted bundle decides the whole PROMOTED verdict: existence,
    coordinate admission, binding, branch and freshness."""
    if promote is not None and authority is not None:
        if _valid_transition_claim(authority.operation_id, "rollback", promote,
                                   authority=authority):
            return _VERDICT_ROLLBACK_RESUME
        if _valid_transition_claim(authority.operation_id, "finalize", promote,
                                   authority=authority):
            return _VERDICT_FINALIZE_ABORT
        # Defense in depth: if the admitted snapshot is not exactly consumable,
        # the selector is spent -- never fresh.
        if _classify_claim_content(
                authority.operation_id, authority.selector,
                expected_receipt_sha256=authority.expected_receipt_sha256) \\
                != "absent":
            return _VERDICT_FAIL_CLOSED
    elif authority is not None \\
            and _claim_state(authority.operation_id, authority=authority) \\
            != "absent":
        # PROMOTED with an existing canonical claim and NO receipt to bind:
        # the selector name exists, so the one-time authority is spent.
        return _VERDICT_FAIL_CLOSED
    return _VERDICT_FRESH


def _classify_state_finalizing(record, promote, authority):
    """A FINALIZING record names a durably selected finalize branch."""
    if record.get("commit_intent") is not None \\
            or record.get("commit_point") is not None:
        return _VERDICT_FAIL_CLOSED
    if not _selector_agrees_with_finalizing(
            record.get("operation_id"), promote, authority=authority):
        return _VERDICT_FAIL_CLOSED
    if record.get("selected_transition") == "finalize":
        return _VERDICT_FINALIZE_ABORT
    return _VERDICT_FAIL_CLOSED


def _classify_state_rolling_back(record, promote, authority):
    """An in-flight rollback is resumable only for the rollback branch."""
    if record.get("selected_transition") not in (None, "rollback"):
        return _VERDICT_FAIL_CLOSED
    if record.get("commit_intent") is not None \\
            or record.get("commit_point") is not None:
        return _VERDICT_FAIL_CLOSED
    if promote is None:
        return (_VERDICT_ROLLBACK_RESUME
                if record.get("selected_transition") == "rollback"
                else _VERDICT_FRESH)
    if authority is None or not _valid_transition_claim(
            record.get("operation_id"), "rollback", promote,
            authority=authority):
        return _VERDICT_FAIL_CLOSED
    return _VERDICT_ROLLBACK_RESUME


def _classify_state_rolled_back(record, promote, authority):
    """The terminal catalog truth is verified idempotently and is NEVER
    labelled fresh authority."""
    if promote is None or authority is None:
        return _VERDICT_FAIL_CLOSED
    if not _valid_transition_claim(record.get("operation_id"), "rollback",
                                   promote, authority=authority):
        return _VERDICT_FAIL_CLOSED
    return _VERDICT_ROLLBACK_RESUME


def _classify_state_failed(record, promote, authority):
    """A failed operation is ALWAYS fail-closed, with or without a receipt."""
    return _VERDICT_FAIL_CLOSED


def _classify_state_commit_intent(record, promote, authority):
    """Forward commit intent may not coexist with rollback authority."""
    intent = record.get("commit_intent")
    if not isinstance(intent, dict) \\
            or intent.get("marker") != "forward_commit":
        return _VERDICT_FAIL_CLOSED
    if promote is not None and not _valid_commit_intent(record, promote):
        return _VERDICT_FAIL_CLOSED
    return _VERDICT_NO_ROLLBACK


def _classify_state_commit_point(record, promote, authority):
    """Past the commit point there is no rollback, ever."""
    if promote is not None and not _valid_commit_intent(record, promote):
        return _VERDICT_FAIL_CLOSED
    commit_point = record.get("commit_point")
    if not isinstance(commit_point, dict) \\
            or commit_point.get("marker") != "quarantine_dropped":
        return _VERDICT_FAIL_CLOSED
    return _VERDICT_NO_ROLLBACK


# THE ONE AUTHORITATIVE STATE/VERDICT MATRIX. There is no second table and no
# classifier that is not dispatched from this one.
_STATE_DISPATCH = {
    "CREATED": _classify_state_created,
    "STAGED": _classify_state_created,
    "PROMOTED": _classify_state_promoted,
    "FINALIZING": _classify_state_finalizing,
    "ROLLING_BACK": _classify_state_rolling_back,
    "ROLLED_BACK": _classify_state_rolled_back,
    "FAILED": _classify_state_failed,
    "COMMIT_INTENT_RECORDED": _classify_state_commit_intent,
    "COMMIT_POINT_REACHED": _classify_state_commit_point,
    "FINALIZED": _classify_state_commit_point,
}


def _classify_record_for_shell(record, promote=None):
    """The single rollback-legality law for both engine callers and the shell.

    Code 0 is fresh rollback authority, code 5 is pre-intent finalize abort,
    code 6 is explicit rollback resume, code 3 forbids rollback after forward
    intent, and code 4 is malformed/unknown.

    B4-CXR7U9R48R1: the record judged is the one ADMITTED through the same
    pinned governed-directory descriptor as the selector, so the state and the
    selector can never come from two different directory generations.

    B4-CXR7U9R48R4: the verdict matrix is now ONE dispatch table over
    immutable decision material. Each handler is pure. An unknown state, a
    non-mapping record, an unknown format, or a bundle that cannot be acquired
    is a table miss or an explicit refusal, and every one of them fails
    closed.
    """
    if not isinstance(record, dict) \\
            or record.get("format") not in (None, TRANSITION_FORMAT):
        return _VERDICT_FAIL_CLOSED
    operation_id = record.get("operation_id")
    authority = None
    if isinstance(operation_id, str) and OPERATION_ID_RE.match(operation_id):
        try:
            authority = _acquire_recovery_authority(
                operation_id, promote, record=record)
        except _ExecutionAuthorityConflict:
            # The governed transition directory itself could not be admitted
            # without following a redirection. There is no authority root, so
            # there is nothing to decide: fail closed.
            return _VERDICT_FAIL_CLOSED
        # DECIDE FROM THE ADMITTED RECORD, not the caller's copy.
        admitted = authority.record
        if admitted is None:
            return _VERDICT_FAIL_CLOSED
        record = admitted
        operation_id = authority.operation_id
        selector_state = _claim_state(
            operation_id, authority=authority,
            expected_receipt_sha256=authority.expected_receipt_sha256)
        if selector_state == "malformed":
            return _VERDICT_FAIL_CLOSED
        if promote is not None and selector_state == "unbound_or_mismatched":
            return _VERDICT_FAIL_CLOSED
    state = record.get("state")
    handler = _STATE_DISPATCH.get(state)
    if handler is None:
        # Unknown or contradictory state: fail closed BY CONSTRUCTION.
        return _VERDICT_FAIL_CLOSED
    return handler(record, promote, authority)


'''

io.open(CLI, "w", encoding="utf-8", newline="").write(head + NEW + tail)
print("rewritten")