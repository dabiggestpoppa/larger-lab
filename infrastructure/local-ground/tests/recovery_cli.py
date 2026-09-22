#!/usr/bin/env python3
"""Explicitly constructed test seam for pg-recovery.py's receipt-write root.

B4-CXR7U9R39-R2 made receipt-write authority PROGRAM IDENTITY: the engine writes
its transition receipts under `<program root>/var/recovery`, and no environment
variable can grant that authority (the former OCE_RECOVERY_STATE_DIR escape
hatch is gone). Tests still need a private, disposable root, so this module
constructs one explicitly: it launches the REAL CLI in a child process whose
first action is to import the engine and bind a test root in process.

Nothing here is reachable from the production CLI, nothing reads an environment
variable, and the production default is untouched whenever the seam is unused
(`run_cli(argv)` with no root runs the engine as a production caller does).
"""
import os
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / "scripts"
CLI = SCRIPTS / "pg-recovery.py"
GOVERNED_ROOT = SCRIPTS.parent / "var" / "recovery"

_BOOTSTRAP = (
    "import importlib.util as u, sys\n"
    "spec = u.spec_from_file_location('pgrec_seam', sys.argv[1])\n"
    "mod = u.module_from_spec(spec)\n"
    "sys.modules['pgrec_seam'] = mod\n"
    "spec.loader.exec_module(mod)\n"
    "mod._bind_test_recovery_root(sys.argv[2])\n"
    "sys.argv = [sys.argv[1]] + sys.argv[3:]\n"
    "mod.main()\n"
)


def cli_argv(argv, write_root):
    """The real CLI, with `write_root` bound by the in-process test seam."""
    return ([sys.executable, "-c", _BOOTSTRAP, str(CLI), str(write_root)]
            + [str(a) for a in argv])


def run_cli(argv, write_root=None, env_extra=None, timeout=300):
    """Run the real CLI. With `write_root` the seam binds that root; without it
    the engine runs exactly as a production caller runs it."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)
    argv = [str(a) for a in argv]
    if write_root is None:
        return subprocess.run([sys.executable, str(CLI)] + argv,
                              capture_output=True, text=True, env=env, timeout=timeout)
    return subprocess.run(cli_argv(argv, write_root),
                          capture_output=True, text=True, env=env, timeout=timeout)
