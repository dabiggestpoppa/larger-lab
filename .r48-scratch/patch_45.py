"""Replace the 45R2/45R3 weakened transforms by index (em-dash safe)."""
import io
import os

TESTS = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "infrastructure", "local-ground", "tests")
Q = chr(39) * 3

OLD = (Q + "    elif authority is not None " + chr(92) * 2 + "\n"
       "            and _claim_state(authority.operation_id,"
       " authority=authority) " + chr(92) * 2 + "\n"
       '            != "absent":\n'
       "        # PROMOTED with an existing canonical claim and NO receipt"
       " to bind:\n"
       "        # the selector name exists, so the one-time authority is"
       " spent.\n"
       "        return _VERDICT_FAIL_CLOSED\n" + Q)
NEW = Q + "    elif False:\n" + Q

REPLACEMENT = "_WEAKENED_TRANSFORM = (" + OLD + ", " + NEW + ")"


def rewrite(name, end_marker):
    path = os.path.join(TESTS, name)
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    start = text.index("_WEAKENED_TRANSFORM = (")
    stop = text.index(end_marker, start)
    text = text[:start] + REPLACEMENT + text[stop:]
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    compile(text, path, "exec")
    print("rewrote", name)


rewrite("test_b4_cxr7u9r45r2_claim_path_admission.py",
        "\n\n\ndef _weakened_engine")
rewrite("test_b4_cxr7u9r45r3_selector_classification_law.py",
        "\n\n\ndef ")
print("done")