#!/usr/bin/env python3
"""OCE Book 3 local worker-fabric CLI (B3-C7, hardened B3-R4).

    python scripts/oce_worker.py <command> [options]

    worker configure <id> --cmd <argv...> [--cap a --cap b]
    worker admit     <id> [--cap a --cap b]
    worker start|up  <id>
    worker status    [<id>]
    worker pause|resume|restart|revoke|stop <id>
    worker drain <id>
    worker doctor
    worker cleanup
    worker console         # operator-console view

B3-R4: state PERSISTS across CLI processes (state.json under the runtime
dir); repeated ``--cap`` is parsed by argparse into a real list; every
admission/revoke is PO-only; only PO-authorized admission is honored;
processes are tracked by runtime-owned PID files (never broad pkill).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oce_control.worker_identity import WorkerAuthority, CapabilityRegistry, \
    CapabilityAdmissionError  # noqa: E402
from oce_control.worker_supervisor import (WorkerSupervisor,  # noqa: E402
                                           BOOTSTRAP_CAPABILITIES, _os_class)


def _runtime_dir(args) -> Path:
    # B4-CXR5R6: the worker CLI runtime dir holds persistent state (logs,
    # pids, lease state) — authority-bearing. The governed DURABLE authority
    # (the approved secret store `.runtime/secrets.json`) is a fixed-path
    # constant and can never be redirected by this value; the fence here
    # rejects traversal, symlink escape, repository overwrite and
    # secret-store overlap. An explicit operator/test state dir elsewhere is
    # permitted (isolated worker fabric state, never durable authority).
    base = Path(args.runtime_dir or os.environ.get(
        "OCE_RUNTIME_DIR", Path.home() / ".oce-control-plane" / "runtime"))
    if args.runtime_dir or os.environ.get("OCE_RUNTIME_DIR"):
        if ".." in base.parts:
            raise SystemExit(
                "FAIL: OCE_RUNTIME_DIR contains traversal segments — refused "
                "(B4-CXR5R6)")
        try:
            resolved = base.resolve()
        except OSError as exc:
            raise SystemExit(
                f"FAIL: OCE_RUNTIME_DIR cannot be resolved safely: {exc} "
                "(B4-CXR5R6)") from exc
        control = Path(__file__).resolve().parent.parent
        if resolved == control or control in resolved.parents:
            raise SystemExit(
                "FAIL: OCE_RUNTIME_DIR overlaps the governed control-plane "
                "package/secret store — refused (B4-CXR5R6)")
    base.mkdir(parents=True, exist_ok=True)
    base.chmod(0o700)
    return base


def build_supervisor(runtime: Path) -> WorkerSupervisor:
    reg = CapabilityRegistry()
    for cap in BOOTSTRAP_CAPABILITIES:
        reg.admit_capability(cap, "operator:po")
    au = WorkerAuthority(reg)
    return WorkerSupervisor(runtime, au)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    # Capture the worker command explicitly: everything after the first `--`
    # is the worker argv, verbatim (so a leading-dash `-c` is never misparsed
    # by argparse). Everything before `--` is parsed normally.
    worker_command: list[str] = []
    if "--" in argv:
        idx = argv.index("--")
        worker_command = argv[idx + 1:]
        argv = argv[:idx]

    p = argparse.ArgumentParser(prog="oce_worker",
                                description="OCE Book 3 worker-fabric CLI")
    p.add_argument("--runtime-dir", default=None,
                   help="runtime dir (default OCE_RUNTIME_DIR or ~/.oce-control-plane/runtime)")
    sub = p.add_subparsers(dest="command", required=True)

    conf = sub.add_parser("configure", help="configure a worker (does NOT admit)")
    conf.add_argument("worker_id")
    conf.add_argument("--cap", action="append", default=[],
                      help="capability (repeatable) — operator declaration")
    conf.add_argument("--actor", default="operator:po")

    admit = sub.add_parser("admit", help="PO-only admission")
    admit.add_argument("worker_id")
    admit.add_argument("--cap", action="append", default=[],
                       help="capability (repeatable)")
    admit.add_argument("--actor", default="operator:po")
    admit.add_argument("--confirm", action="store_true",
                       help="admission is a governance action; pass to confirm PO intent")

    for cmd in ("start", "up", "status", "pause", "resume", "drain",
                "restart", "revoke", "stop"):
        sp = sub.add_parser(cmd, help=f"worker {cmd}")
        sp.add_argument("worker_id", nargs="?")

    sub.add_parser("doctor", help="run fabric doctor checks")
    sub.add_parser("cleanup", help="clean disposable state (preserve durable)")
    cns = sub.add_parser("console", help="operator-console view")

    args = p.parse_args(argv)
    sup = build_supervisor(_runtime_dir(args))
    cmd = args.command

    if cmd == "console":
        print_json(sup.operator_view())
        return 0
    if cmd == "doctor":
        print_json(sup.doctor())
        return 1 if not sup.doctor()["ok"] else 0
    if cmd == "cleanup":
        print_json(sup.cleanup())
        return 0

    wid = getattr(args, "worker_id", "") or ""
    if cmd == "configure":
        command = worker_command or [sys.executable]
        rec = sup.configure(wid, command=command,
                            capabilities=args.cap or None, actor=args.actor)
        print_json(rec.to_dict())
        return 0
    if cmd == "admit":
        if not args.confirm:
            print("admission is a governance action — re-run with --confirm "
                  "to authorize PO admission", file=sys.stderr)
            return 2
        try:
            ident = sup.admit(wid, requested=args.cap or None, actor=args.actor)
        except PermissionError as e:
            print(f"DENIED: {e}", file=sys.stderr)
            return 2
        print_json(ident.to_dict())
        return 0
    if cmd in ("start", "up", "status", "pause", "resume", "drain",
               "restart", "revoke", "stop"):
        try:
            if cmd == "status" and not wid:
                print_json(sup.status())   # full dashboard across workers
                return 0
            if not wid:
                print(f"worker {cmd} requires a worker id", file=sys.stderr)
                return 2
            result = sup.status(wid) if cmd == "status" else getattr(sup, cmd)(wid)
        except (PermissionError, KeyError) as e:
            print(f"DENIED/error: {e}", file=sys.stderr)
            return 2
        print_json(result.to_dict() if hasattr(result, "to_dict") else result)
        return 0

    print(f"unknown command '{cmd}'", file=sys.stderr)
    return 2


def print_json(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())