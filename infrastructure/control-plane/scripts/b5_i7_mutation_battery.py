#!/usr/bin/env python3
"""B5-I7 governed mutation battery (construction plan §4.6; ``B5I7-EL10``).

For every mutation: apply ONE textual change to the governed panel module, run
the node that is supposed to detect it, record the observed exit status, then
restore the pristine bytes and PROVE restoration by sha256.

Design laws:

- every row must show an actual failing execution (``RED``); a mutation whose
  node still passes is recorded ``NOT_DISCRIMINATED`` and fails the battery —
  an expected-failure annotation is never accepted as discrimination;
- mutations are textual and single-anchor (the anchor must occur exactly once),
  so a silent no-op mutation is impossible;
- restoration is byte-exact and hash-verified, and the worktree must be clean
  afterwards (``B5I7-EL11``);
- the battery never imports the module under test in-process: each run is a
  fresh interpreter, so a mutation cannot leak into the next row.

Usage::

    python infrastructure/control-plane/scripts/b5_i7_mutation_battery.py [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PANEL = REPO_ROOT / "infrastructure" / "console" / "src" / "oce_console" / "panel.py"
TESTS = "infrastructure/control-plane/tests/test_b5_i7_governed_change.py"

R18 = TESTS + "::TestPanelFailClosed::test_unknown_queue_depth_rendered_unknown_not_zero"
R17 = TESTS + "::TestPanelFailClosed::test_unreachable_stack_never_renders_healthy"
R21 = TESTS + "::TestPanelSecurity::test_panel_output_contains_no_secret_material"
R19 = TESTS + "::TestPanelDeterminism::test_identical_inputs_render_byte_identically"
R22 = TESTS + "::TestPanelBounds::test_oversized_and_malformed_input_refused"
R16 = TESTS + "::TestPanelReadOnly::test_panel_issues_only_get_requests"
R15 = TESTS + "::TestPanelContract::test_undeclared_surface_refused_before_io"
R07 = TESTS + "::TestChangeCycle::test_change_has_positive_and_negative_proofs"
R02 = TESTS + "::TestSingleChange::test_exactly_one_governed_change_recorded"

MUTATIONS = [
    (
        "M01",
        "render an unknown counter as a known 0 (unknown becomes zero)",
        '    return {"value": None, "known": False, "unknown_reason": reason}',
        '    return {"value": 0, "known": True, "unknown_reason": None}',
        R18,
    ),
    (
        "M02",
        "stop marking a queue read partial when counters are missing",
        '    if health_state == STATE_OK and known_count < len(QUEUE_FIELDS):\n'
        '        reads["health.read"]["partial"] = True',
        '    if False and health_state == STATE_OK:\n'
        '        reads["health.read"]["partial"] = True',
        R18,
    ),
    (
        "M03",
        "summarize a governed denial as OK (bypass the denial state)",
        '        if STATE_DENIED in read_states:\n            state = STATE_DENIED',
        '        if STATE_DENIED in read_states:\n            state = STATE_OK',
        R18,
    ),
    (
        "M04",
        "remove recursive redaction of scalars (carry values verbatim)",
        '    if isinstance(value, str):\n'
        '        text, _ = _bounded_text(value, field)\n'
        '        return text',
        '    if isinstance(value, str):\n        return value',
        R21,
    ),
    (
        "M05",
        "stop recursing into nested mappings and sequences",
        '            rendered[key_text] = _sanitize(item, f"{field}.{key_text}", depth + 1)',
        '            rendered[key_text] = item if isinstance(item, (str, int, float, bool)) else REDACTED',
        R21,
    ),
    (
        "M06",
        "accept any surface present in the pack (widen panel authority)",
        '        if entry not in PANEL_SURFACES or entry not in surfaces:',
        '        if entry not in surfaces:',
        R15,
    ),
    (
        "M07",
        "drop duplicate-surface detection (double-count queue depth)",
        '        if entry in seen:',
        '        if False:',
        R15,
    ),
    (
        "M08",
        "remove deterministic ordering of collection ids",
        '    rendered.sort()',
        '    rendered.reverse()',
        R19,
    ),
    (
        "M09",
        "render non-ASCII characters raw (locale-dependent bytes)",
        '    text = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True)',
        '    text = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False)',
        R19,
    ),
    (
        "M10",
        "remove the per-string bound (truncate instead of refusing)",
        '    if len(value.encode("utf-8")) > MAX_STRING_BYTES:',
        '    if False and len(value.encode("utf-8")) > MAX_STRING_BYTES:',
        R22,
    ),
    (
        "M11",
        "introduce a write verb into the read-only module",
        '    selected = _validate_requested(surfaces, surfaces_requested)',
        '    selected = _validate_requested(surfaces, surfaces_requested)\n'
        '    if False:  # dead branch: invisible to execution, visible to the AST law\n'
        '        surface.write("mutation")',
        R16,
    ),
    (
        "M12",
        "fabricate a healthy read instead of failing closed when unreachable",
        '        except Exception as exc:  # fail closed, whole document (R17 / F-1)\n'
        '            unreachable = True\n'
        '            interrupted_at = f"{surface}: {type(exc).__name__}"\n'
        '            break',
        '        except Exception as exc:  # MUTATION: fabricate a healthy read\n'
        '            responses[surface] = {"ok": True, "status": "ok", "data": {}}\n'
        '            continue',
        R17,
    ),
    (
        "M13",
        "drop the explicit non_authoritative declaration",
        '        # The panel never claims canonical authority (charter section 5 rule 9).\n'
        '        "non_authoritative": True,',
        '        # The panel never claims canonical authority (charter section 5 rule 9).\n'
        '        "non_authoritative": False,',
        R07,
    ),
    (
        "M14",
        "add a second governed builder (a second change)",
        '\ndef _unreachable_document(',
        '\ndef build_second_panel(read):\n'
        '    """MUTATION: a second change would be a B5I7-R02 violation."""\n'
        '    return {}\n'
        '\n\ndef _unreachable_document(',
        R02,
    ),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _porcelain() -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"], cwd=str(REPO_ROOT),
        capture_output=True, text=True, check=False,
    )
    return proc.stdout.strip()


def _run_node(node: str) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q", "--tb=no", "-p", "no:randomly"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, check=False,
    )
    return proc.returncode


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="B5-I7 mutation battery")
    parser.add_argument("--out", default="", help="write the result JSON here")
    args = parser.parse_args(argv)

    pristine_bytes = PANEL.read_bytes()
    pristine_sha = hashlib.sha256(pristine_bytes).hexdigest()
    source = pristine_bytes.decode("utf-8")
    # A Windows checkout stores CRLF while .gitattributes stores LF; anchors are
    # authored in LF, so they are translated to the file's native ending before
    # matching. Restoration always writes the ORIGINAL bytes back.
    crlf = chr(13) + chr(10)
    native = crlf if crlf in source else None

    rows = []
    failures = []
    for mid, description, old, new, node in MUTATIONS:
        old_n = old if native is None else old.replace(chr(10), native)
        new_n = new if native is None else new.replace(chr(10), native)
        if source.count(old_n) != 1:
            failures.append(f"{mid}: anchor count {source.count(old_n)} (expected 1)")
            rows.append({"mutation_id": mid, "description": description,
                         "result": "ANCHOR_MISSING", "expected_node": node,
                         "observed_node": "", "pytest_rc": None,
                         "restored_sha256": pristine_sha,
                         "restoration_ok": False})
            continue
        mutated = source.replace(old_n, new_n, 1)
        try:
            PANEL.write_bytes(mutated.encode("utf-8"))
            rc = _run_node(node)
        finally:
            PANEL.write_bytes(pristine_bytes)
        restored_sha = _sha(PANEL)
        restoration_ok = restored_sha == pristine_sha and PANEL.read_bytes() == pristine_bytes
        result = "RED" if rc != 0 else "NOT_DISCRIMINATED"
        if result != "RED":
            failures.append(f"{mid}: node still passed (rc=0) — not discriminated")
        if not restoration_ok:
            failures.append(f"{mid}: restoration mismatch")
        rows.append({
            "mutation_id": mid,
            "description": description,
            "expected_node": node,
            "observed_node": node if rc != 0 else "",
            "pytest_rc": rc,
            "result": result,
            "mutated_sha256": hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
            "pristine_sha256": pristine_sha,
            "restored_sha256": restored_sha,
            "restoration_ok": restoration_ok,
        })

    # Final pristine rerun: the battery must leave a green suite behind.
    final_rc = _run_node(TESTS)
    clean = _porcelain()
    payload = {
        "kind": "oce-b5-i7-mutation-battery",
        "version": "1.0.0",
        "target": "infrastructure/console/src/oce_console/panel.py",
        "mutations": len(rows),
        "floor": 12,
        "floor_met": len(rows) >= 12,
        "discriminated": sum(1 for row in rows if row["result"] == "RED"),
        "not_discriminated": sum(1 for row in rows if row["result"] != "RED"),
        "restoration_verified": all(row["restoration_ok"] for row in rows),
        "pristine_sha256": pristine_sha,
        "final_pristine_suite_rc": final_rc,
        "final_pristine_suite_green": final_rc == 0,
        "worktree_porcelain_after": clean,
        "worktree_clean_after": clean == "",
        "rows": rows,
        "verdict": "PASS" if (not failures and final_rc == 0 and clean == ""
                              and len(rows) >= 12) else "FAIL",
        "failures": failures,
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    sys.stdout.write(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
