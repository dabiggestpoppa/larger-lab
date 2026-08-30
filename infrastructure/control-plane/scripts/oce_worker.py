#!/usr/bin/env python3
"""OCE Book 3 local worker-fabric CLI (B3-C7).

    python scripts/oce_worker.py <command> [options]

    worker configure <id> --cmd <argv...>
    worker admit <id> [--cap a --cap b]
    worker start <id>
    worker drain <id>
    worker status [<id>]
    worker pause <id> | resume <id> | restart <id> | revoke <id> | stop <id>
    worker doctor
    worker cleanup
    worker console         # operator-console view

Only PO-authorized admission is honored; processes are tracked by runtime-
owned PID files (never broad pkill).
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oce_control.worker_identity import (WorkerAuthority, CapabilityRegistry)  # noqa: E402
from oce_control.worker_supervisor import (WorkerSupervisor,  # noqa: E402
                                           BOOTSTRAP_CAPABILITIES)


def build_supervisor() -> WorkerSupervisor:
    reg = CapabilityRegistry()
    for cap in BOOTSTRAP_CAPABILITIES:
        reg.admit_capability(cap, "operator:po")
    au = WorkerAuthority(reg)
    runtime = Path(os.environ.get("OCE_RUNTIME_DIR",
                                  Path.home() / ".oce-control-plane" / "runtime"))
    return WorkerSupervisor(runtime, au)


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    sup = build_supervisor()
    if cmd == "console":
        print_json(sup.operator_view())
        return 0
    if cmd == "doctor":
        print_json(sup.doctor())
        return 0
    if cmd == "cleanup":
        print_json(sup.cleanup())
        return 0
    if cmd in ("configure", "admit", "start", "drain", "status", "pause",
               "resume", "restart", "revoke", "stop"):
        worker_id = args[1] if len(args) > 1 else ""
        if not worker_id:
            print("worker subcommand requires a worker id", file=sys.stderr)
            return 2
        if cmd == "configure":
            rest = args[2:]
            cmd_i = rest.index("--cmd") if "--cmd" in rest else -1
            command = rest[cmd_i + 1:] if cmd_i >= 0 else [sys.executable]
            caps = [c.split("--cap ", 1)[1] for c in rest if c.startswith("--cap ")]
            print_json(sup.configure(worker_id, command,
                                     capabilities=caps or None).to_dict())
            return 0
        if cmd == "admit":
            caps = [a.split("--cap ", 1)[1] for a in args[2:] if a.startswith("--cap ")]
            ident = sup.admit(worker_id, caps or None, actor="operator:po")
            print_json(ident.to_dict())
            return 0
        result = getattr(sup, cmd)(worker_id)
        print_json(result.to_dict() if hasattr(result, "to_dict") else result)
        return 0
    print(f"unknown command '{cmd}'", file=sys.stderr)
    return 2


def print_json(obj) -> None:
    import json
    print(json.dumps(obj, indent=2, default=str))


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())