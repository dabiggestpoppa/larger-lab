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
    "if len(sys.argv) > 3 and sys.argv[3] == '--test-bridge':\n"
    "    bspec = u.spec_from_file_location('race_bridge', sys.argv[4])\n"
    "    bmod = u.module_from_spec(bspec)\n"
    "    sys.modules['race_bridge'] = bmod\n"
    "    bspec.loader.exec_module(bmod)\n"
    "    bmod.install(mod)\n"
    "    sys.argv = [sys.argv[1]] + sys.argv[5:]\n"
    "else:\n"
    "    sys.argv = [sys.argv[1]] + sys.argv[3:]\n"
    "mod.main()\n"
)


def load_engine(module_path=None):
    """Import pg-recovery.py as an in-process module object
    (B4-CXR7U9R47R2).

    B4-CXR7U9R47R2 removed the public ``--classify-state <arbitrary path>``
    surface, because it let a caller hand the engine a record AND, through
    ``os.path.dirname(path)``, the transition authority root that record was
    then validated against. Proofs that still need to classify a bare record
    now call the engine's explicitly private seam
    ``_test_classify_state_for_shell(record)`` in process instead of through a
    command line -- the record arrives as a value, never as a path, so there is
    no directory left for a caller to declare.

    Same discipline as ``cli_argv``: this is a test-only loader, unreachable
    from the production CLI, and the ONLY thing it can change about authority
    is ``bind_root``. ``module_path`` points at an explicitly constructed
    copy (used by the executable weakened controls); the default is the real
    shipped engine.
    """
    import importlib.util
    target = str(module_path or CLI)
    name = "pgrec_inprocess_" + str(abs(hash(target)) % 1000000)
    spec = importlib.util.spec_from_file_location(name, target)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def bind_root(mod, write_root):
    """Bind an in-process engine to a disposable governed root (test seam).

    The counterpart of ``_bind_test_recovery_root``: after this call the engine
    derives its governed transition directory from ``write_root`` alone. No
    environment variable participates, exactly as in ``cli_argv``.
    """
    mod._bind_test_recovery_root(str(write_root))
    return mod


def cli_argv(argv, write_root, bridge_path=None):
    """The real CLI, with `write_root` bound by the in-process test seam.
    With `bridge_path`, the child additionally loads a container-bridge module
    (explicitly constructed test dependency, same seam discipline as the
    write root: never reachable from the production CLI, no environment
    channel) so filesystem-only proofs can run the REAL engine phases."""
    base = [sys.executable, "-c", _BOOTSTRAP, str(CLI), str(write_root)]
    if bridge_path is not None:
        base += ["--test-bridge", str(bridge_path)]
    return base + [str(a) for a in argv]


def run_cli(argv, write_root=None, env_extra=None, timeout=300, bridge=None):
    """Run the real CLI. With `write_root` the seam binds that root; without it
    the engine runs exactly as a production caller runs it. With `bridge` the
    child loads the named container-bridge module (test-only; see cli_argv)."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)
    argv = [str(a) for a in argv]
    if write_root is None:
        return subprocess.run([sys.executable, str(CLI)] + argv,
                              capture_output=True, text=True, env=env, timeout=timeout)
    return subprocess.run(cli_argv(argv, write_root, bridge),
                          capture_output=True, text=True, env=env, timeout=timeout)
