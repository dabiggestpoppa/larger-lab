"""CLI status view — the mandatory first-release console interface (I-3).

Charter section 8.1: the local command interface is the mandatory
first-release surface. This module is a thin deterministic shell over the
kernel and transport: it parses operator input, issues contract-validated
reads against a loopback base URL, and renders the status document.

Exit codes are the operator contract and are DERIVED from the
authoritative document state (never from parsing rendered text):

===============================  =====  ==================================
Document / input outcome         Exit   Meaning
===============================  =====  ==================================
``state == OK``                   ``0``  every section answered ``ok``
``state == DEGRADED``             ``4``  a governed denial / not-ok section
``state == UNVERIFIABLE``         ``5``  at least one explicit gap section
``state == STACK_UNREACHABLE``    ``2``  stack down; nothing green rendered
refused before any I/O            ``3``  hostile/malformed input or usage
unexpected internal failure       ``1``  reported, never rendered as success
===============================  =====  ==================================

The frozen B5-I4 plan requires "CLI exits nonzero" for the stack-down
class (F-1) and for pre-I/O refusals (X1); every mapping above is
strictly nonzero for every non-healthy outcome, so no partial, denied or
unverifiable view can be mistaken for success by a scripted operator.

B5-I4-X2 repairs (demonstrated defects, each now executable-tested):

- argparse usage errors (unknown flag, missing value) exited ``2`` —
  indistinguishable from "stack unreachable" — because argparse's own
  usage exit code collided with ``EXIT_UNREACHABLE``. A malformed
  configuration is now ``EXIT_REFUSED`` (3), decided before any I/O;
- the previous ``except StackUnreachable`` branch was DEAD code: the
  kernel collapses every transport failure into the document itself, so
  no ``StackUnreachable`` could ever reach it. The exit result now reads
  the document's own summary state, and an unrecognized summary fails
  closed instead of succeeding.

B5-I4-X3 repair (demonstrated defect): the FROZEN interface — the
literal command line ``python -m oce_console status`` (P0 gap/scope
contract; charter section 8.1) — was rejected by the CLI's own parser:
the ``status`` token was not declared, so the documented invocation
failed with a usage error (exit 2 before this rung, i.e. misreported as
a stack verdict). The token is now accepted explicitly, defaults to
``status`` so the bare module invocation works too, and any other
command stays a refused usage error decided before any I/O.

No writes, no retries, no cache, no provider: stdlib argparse + the
loopback transport only.
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from .kernel import (
    STATE_DEGRADED,
    STATE_OK,
    STATE_UNREACHABLE,
    STATE_UNVERIFIABLE,
    ConsoleRefusal,
    build_status_document,
    render_status,
)
from .transport import LoopbackTransport, validate_base_url

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_UNREACHABLE = 2
EXIT_REFUSED = 3
EXIT_DEGRADED = 4
EXIT_UNVERIFIABLE = 5

# The single authoritative exit map: document summary state -> exit code.
# There is no string parsing of rendered output and no code path that
# returns EXIT_OK for a summary state other than OK.
EXIT_BY_DOCUMENT_STATE = {
    STATE_OK: EXIT_OK,
    STATE_UNREACHABLE: EXIT_UNREACHABLE,
    STATE_DEGRADED: EXIT_DEGRADED,
    STATE_UNVERIFIABLE: EXIT_UNVERIFIABLE,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m oce_console status",
        description=(
            "OCE console status view (client-only, loopback-only): renders "
            "governed control-plane reads verbatim. Never mutates state."
        ),
    )
    # B5-I4-X3: the frozen interface (P0 gap/scope contract, charter
    # section 8.1) is the literal command line
    # ``python -m oce_console status``. The token is accepted explicitly
    # (and defaults to ``status``) so the documented invocation works,
    # while any other token stays a refused usage error — before any I/O.
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=("status",),
        help="command to run (default: %(default)s)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8448",
        help="loopback base URL of the local control plane (default: %(default)s)",
    )
    parser.add_argument("--grant", default="", help="operator read grant id (passed verbatim)")
    parser.add_argument("--actor", default="", help="operator actor id (passed verbatim)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 for --help and 2 for a usage error. A usage
        # error is a MALFORMED CONFIGURATION (matrix X2) and must never
        # masquerade as EXIT_UNREACHABLE; --help stays a clean success.
        if exc.code in (0, None):
            return EXIT_OK
        sys.stderr.write("refused: malformed_arguments: see usage above\n")
        return EXIT_REFUSED
    try:
        # Refusal ordering (matrix X1/X2): the base URL is validated
        # before the pack is even loaded — a hostile URL performs zero
        # work and no file reads.
        validate_base_url(args.base_url)
        client = LoopbackTransport(args.base_url, grant_id=args.grant, actor_id=args.actor)
        document = build_status_document(client.read, client.routes)
    except ConsoleRefusal as refusal:
        sys.stderr.write(f"refused: {refusal.reason}: {refusal.detail}\n")
        return EXIT_REFUSED
    except Exception as exc:
        # Unexpected internal failure: reported, never rendered as
        # success and never disguised as a stack verdict (X2).
        sys.stderr.write(f"internal_error: {type(exc).__name__}: {exc}\n")
        return EXIT_INTERNAL
    sys.stdout.write(render_status(document))
    # F-1 fail-closed: the kernel collapses a transport failure INTO the
    # document (whole view), so the exit code reads the document's own
    # summary state — a STACK_UNREACHABLE, DEGRADED or UNVERIFIABLE view
    # never exits 0, and an unknown summary cannot succeed.
    code = EXIT_BY_DOCUMENT_STATE.get(document.get("state"))
    if code is None:
        sys.stderr.write(f"internal_error: unknown document state {document.get('state')!r}\n")
        return EXIT_INTERNAL
    return code


if __name__ == "__main__":  # pragma: no cover — module entry shim
    raise SystemExit(main())
