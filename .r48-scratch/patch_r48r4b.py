"""Retarget the negative controls onto the R48R4 dispatch-table shape."""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LG = os.path.join(ROOT, "infrastructure", "local-ground")
ENGINE = os.path.join(LG, "scripts", "pg-recovery.py")
TESTS = os.path.join(LG, "tests")
Q = chr(39) * 3          # '''
BS = chr(92)             # backslash, never inside an escaped literal


def patch(path, pairs):
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    for old, new in pairs:
        n = text.count(old)
        if n != 1:
            raise SystemExit("anchor count %d in %s:\n%r" % (n, path, old))
        text = text.replace(old, new)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("patched", os.path.basename(path))


# ------------------------------------------------------------------ engine
patch(ENGINE, [
    ("""    if promote is None and authority is not None:
        if _claim_state(authority.operation_id,
                        authority=authority) != "absent":
            return _VERDICT_FAIL_CLOSED
    return _VERDICT_FRESH""",
     """    del record
    if promote is None and authority is not None:
        if _claim_state(authority.operation_id,
                        authority=authority) != "absent":
            return _VERDICT_FAIL_CLOSED
    return _VERDICT_FRESH"""),
    ("""    if promote is not None and authority is not None:
        if _valid_transition_claim(authority.operation_id, "rollback", promote,
                                   authority=authority):
            return _VERDICT_ROLLBACK_RESUME""",
     """    del record
    if promote is not None and authority is not None:
        if _valid_transition_claim(authority.operation_id, "rollback", promote,
                                   authority=authority):
            return _VERDICT_ROLLBACK_RESUME"""),
    ("""def _classify_state_failed(record, promote, authority):
    \"\"\"A failed operation is ALWAYS fail-closed, with or without a receipt.\"\"\"
    return _VERDICT_FAIL_CLOSED""",
     """def _classify_state_failed(record, promote, authority):
    \"\"\"A failed operation is ALWAYS fail-closed, with or without a receipt.\"\"\"
    del record, promote, authority
    return _VERDICT_FAIL_CLOSED"""),
    ("""    intent = record.get("commit_intent")
    if not isinstance(intent, dict) \\
            or intent.get("marker") != "forward_commit":""",
     """    del authority
    intent = record.get("commit_intent")
    if not isinstance(intent, dict) \\
            or intent.get("marker") != "forward_commit":"""),
    ("""    if promote is not None and not _valid_commit_intent(record, promote):
        return _VERDICT_FAIL_CLOSED
    commit_point = record.get("commit_point")""",
     """    del authority
    if promote is not None and not _valid_commit_intent(record, promote):
        return _VERDICT_FAIL_CLOSED
    commit_point = record.get("commit_point")"""),
])

# ------------------------------------------------------- 45r2 and 45r3
old_45 = (Q + "    elif authority is not None " + BS + BS + "\n"
          "            and _claim_state(operation_id, authority=authority)"
          ' != "absent":\n'
          "            # PROMOTED with an existing canonical claim and NO"
          " receipt to bind:\n"
          "            # the selector name exists, so the one-time authority"
          " is spent \u2014\n"
          "            # never fresh (B4-CXR7U9R45R1).\n"
          "            return 4\n"
          "        return 0\n" + Q)
new_45 = (Q + "    elif authority is not None " + BS + BS + "\n"
          "            and _claim_state(authority.operation_id,"
          " authority=authority) " + BS + BS + "\n"
          '            != "absent":\n'
          "        # PROMOTED with an existing canonical claim and NO"
          " receipt to bind:\n"
          "        # the selector name exists, so the one-time authority"
          " is spent.\n"
          "        return _VERDICT_FAIL_CLOSED\n" + Q)
repl_45 = Q + "    elif False:\n" + Q

path = os.path.join(TESTS, "test_b4_cxr7u9r45r2_claim_path_admission.py")
with io.open(path, encoding="utf-8") as fh:
    text = fh.read()
if old_45 not in text:
    raise SystemExit("45r2 anchor missing")
text = text.replace(old_45, new_45, 1)
# the replacement half of the tuple: the short "return 0" body
old_tail = Q + "        return 0\n" + Q + ")"
new_tail = repl_45 + ")"
if text.count(old_tail) != 1:
    raise SystemExit("45r2 tail anchor count %d" % text.count(old_tail))
text = text.replace(old_tail, new_tail)
with io.open(path, "w", encoding="utf-8", newline="") as fh:
    fh.write(text)
print("patched 45r2")

# ------------------------------------------------------------------- 43
patch(os.path.join(TESTS, "test_b4_cxr7u9r43_lock_inode_rollback_resume.py"), [
    ("""        tmp_path, lambda source: source.replace(
            '        return 6\\n    if state == "ROLLED_BACK":',
            '        return 0\\n    if state == "ROLLED_BACK":'))""",
     """        tmp_path, lambda source: source.replace(
            '    if authority is None or not _valid_transition_claim(\\n'
            '            record.get("operation_id"), "rollback", promote,\\n'
            '            authority=authority):\\n'
            '        return _VERDICT_FAIL_CLOSED\\n'
            '    return _VERDICT_ROLLBACK_RESUME',
            '    if authority is None or not _valid_transition_claim(\\n'
            '            record.get("operation_id"), "rollback", promote,\\n'
            '            authority=authority):\\n'
            '        return _VERDICT_FAIL_CLOSED\\n'
            '    return _VERDICT_FRESH'))"""),
])

# ----------------------------------------------------------------- 41r2
path = os.path.join(TESTS, "test_b4_cxr7u9r41r2_crash_coherence.py")
with io.open(path, encoding="utf-8") as fh:
    text = fh.read()
o = (Q + "        if record.get(\"commit_intent\") is not None or"
     " record.get(\"commit_point\") is not None:" + BS + "n"
     "            return 4" + BS + "n" + Q)
n = (Q + "    if record.get(\"commit_intent\") is not None " + BS + BS + "\n"
     "            or record.get(\"commit_point\") is not None:" + BS + "n"
     "        return _VERDICT_FAIL_CLOSED" + BS + "n"
     "    if not _selector_agrees_with_finalizing(" + Q)
if text.count(o) != 1:
    raise SystemExit("41r2 old anchor count %d" % text.count(o))
text = text.replace(o, n)
o2 = (Q + "        marker = record.get(\"commit_point\")" + BS + "n"
      "        return 3 if isinstance(marker, dict) and"
      " marker.get(\"marker\") else 0" + BS + "n" + Q)
n2 = (Q + "    marker = record.get(\"commit_point\")" + BS + "n"
      "    return 3 if isinstance(marker, dict) and"
      " marker.get(\"marker\") else 0" + BS + "n"
      "    if not _selector_agrees_with_finalizing(" + Q)
if text.count(o2) != 1:
    raise SystemExit("41r2 new anchor count %d" % text.count(o2))
text = text.replace(o2, n2)
with io.open(path, "w", encoding="utf-8", newline="") as fh:
    fh.write(text)
print("patched 41r2")

# ----------------------------------------------------------------- 47r1
path = os.path.join(TESTS, "test_b4_cxr7u9r47r1_authority_snapshot.py")
with io.open(path, encoding="utf-8") as fh:
    text = fh.read()
o = (Q + "        if promote is not None and authority is not None:"
     + BS + "n"
     "            if _valid_transition_claim(operation_id, \"rollback\","
     " promote," + BS + "n"
     "                                       authority=authority):"
     + BS + "n"
     "                return 6" + BS + "n"
     "            if _valid_transition_claim(operation_id, \"finalize\","
     " promote," + BS + "n"
     "                                       authority=authority):"
     + BS + "n"
     "                return 5" + BS + "n" + Q)
n = (Q + "    if promote is not None and authority is not None:" + BS + "n"
     "        if _valid_transition_claim(authority.operation_id,"
     " \"rollback\", promote," + BS + "n"
     "                                   authority=authority):" + BS + "n"
     "            return _VERDICT_ROLLBACK_RESUME" + BS + "n"
     "        if _valid_transition_claim(authority.operation_id,"
     " \"finalize\", promote," + BS + "n"
     "                                   authority=authority):" + BS + "n"
     "            return _VERDICT_FINALIZE_ABORT" + BS + "n" + Q)
if text.count(o) != 1:
    raise SystemExit("47r1 old anchor count %d" % text.count(o))
text = text.replace(o, n)
o2 = Q + "        if promote is not None and authority is not None:"
n2 = (Q + "    if promote is not None and authority is not None:" + BS + "n"
      "            _claim_state(authority.operation_id, authority=authority)"
      + BS + "n"
      "            authority = _acquire_recovery_authority(" + BS + "n"
      "                authority.operation_id, promote, record=record)")
if text.count(o2) != 1:
    raise SystemExit("47r1 two-read anchor count %d" % text.count(o2))
text = text.replace(o2, n2)
with io.open(path, "w", encoding="utf-8", newline="") as fh:
    fh.write(text)
print("patched 47r1")

print("done")