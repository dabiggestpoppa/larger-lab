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