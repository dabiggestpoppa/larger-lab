"""CLI status view — the mandatory first-release console interface (I-3).

Charter section 8.1: the local command interface is the mandatory
first-release surface. This module is a thin deterministic shell over the
kernel and transport: it parses operator input, issues contract-validated
reads against a loopback base URL, and renders the status document. Exit
codes are the operator contract:

- ``0`` — status document rendered (state OK or UNVERIFIABLE sections;
  the document itself carries per-section truth);
- ``2`` — ``STACK_UNREACHABLE``: the local stack could not answer a read;
  nothing green was rendered (F-1 fail-closed);
- ``3`` — refused fail-closed (non-loopback URL, malformed input,
  undeclared surface, unreadable pack) BEFORE any request.

No writes, no retries, no cache, no provider: stdlib argparse + the
loopback transport only.
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from .kernel import (
    ConsoleRefusal,
    STATE_UNREACHABLE,
    build_status_document,
    render_status,
)
from .transport import LoopbackTransport, StackUnreachable, validate_base_url

EXIT_OK = 0
EXIT_UNREACHABLE = 2
EXIT_REFUSED = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m oce_console status",
        description=(
            "OCE console status view (client-only, loopback-only): renders "
            "governed control-plane reads verbatim. Never mutates state."
        ),
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
    args = build_parser().parse_args(argv)
    try:
        # Refusal ordering (matrix X1/X2): the base URL is validated
        # before the pack is even loaded — a hostile URL performs zero
        # work and no file reads.
        validate_base_url(args.base_url)
        transport = LoopbackTransport(args.base_url, grant_id=args.grant, actor_id=args.actor)
        document = build_status_document(transport.read, transport.routes)
    except ConsoleRefusal as refusal:
        sys.stderr.write(f"refused: {refusal.reason}: {refusal.detail}\n")
        return EXIT_REFUSED
    except StackUnreachable as unreachable:
        # F-1 fail-closed: render the whole-view marker, never green.
        sys.stdout.write(
            render_status(
                {
                    "kind": "oce-console-status",
                    "state": STATE_UNREACHABLE,
                    "detail": str(unreachable),
                }
            )
        )
        return EXIT_UNREACHABLE
    sys.stdout.write(render_status(document))
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover — module entry shim
    raise SystemExit(main())
