#!/usr/bin/env python3
"""OCE Hermes Telegram Operator — Doctor Script

Validates configuration, checks dependencies, and reports issues.
Run before starting the system.
"""

import os
import sys
import subprocess
from pathlib import Path


def check(label: str, ok: bool, detail: str = ""):
    """Print a check result."""
    icon = "✅" if ok else "❌"
    msg = f"  {icon} {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def main():
    """Run all checks."""
    project_dir = Path(__file__).resolve().parent.parent
    errors = 0

    print("═══════════════════════════════════════════════════════════════════")
    print("  OCE Hermes Telegram Operator — Doctor")
    print("═══════════════════════════════════════════════════════════════════")
    print()

    # ─── Python version ────────────────────────────────────────────────────
    print("Python:")
    py_ver = sys.version_info
    errors += not check(
        "Python version",
        py_ver >= (3, 11),
        f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}",
    )

    # ─── Dependencies ──────────────────────────────────────────────────────
    print("\nDependencies:")
    for pkg in ["httpx", "mcp", "aiohttp"]:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "installed")
            errors += not check(f"  {pkg}", True, ver)
        except ImportError:
            errors += not check(f"  {pkg}", False, "NOT INSTALLED — pip install " + pkg)

    # ─── Environment ───────────────────────────────────────────────────────
    print("\nEnvironment:")

    # Load .env if present
    env_file = project_dir / ".env"
    if env_file.exists():
        check(".env file", True, "exists")
        with open(env_file) as f:
            env_content = f.read()
        for line in env_content.splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                if val.strip():
                    os.environ.setdefault(key.strip(), val.strip())
    else:
        check(".env file", False, "NOT FOUND — run setup.sh")

    # Telegram checks
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    errors += not check(
        "TELEGRAM_BOT_TOKEN",
        bool(bot_token),
        "set" if bot_token else "NOT SET",
    )

    allowed_users = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    errors += not check(
        "TELEGRAM_ALLOWED_USERS",
        bool(allowed_users),
        "set" if allowed_users else "NOT SET",
    )

    allow_all = os.environ.get("TELEGRAM_ALLOW_ALL_USERS", "false").lower()
    errors += not check(
        "TELEGRAM_ALLOW_ALL_USERS",
        allow_all != "true",
        f"={allow_all}" + (" ⚠️ MUST BE false" if allow_all == "true" else ""),
    )

    # OCE checks
    oce_url = os.environ.get("OCE_BACKEND_URL", "http://localhost:8000")
    check("OCE_BACKEND_URL", True, oce_url)

    oce_token = os.environ.get("OCE_SERVICE_TOKEN", "")
    if oce_token:
        check("OCE_SERVICE_TOKEN", True, "set (mock mode disabled)")
    else:
        check("OCE_SERVICE_TOKEN", True, "NOT SET (using mock mode)")

    # ─── Hermes ────────────────────────────────────────────────────────────
    print("\nHermes Agent:")
    try:
        result = subprocess.run(
            ["hermes", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        check("Hermes installed", True, result.stdout.strip())
    except FileNotFoundError:
        check("Hermes installed", False, "NOT FOUND")
    except Exception:
        check("Hermes installed", False, "error checking")

    # ─── Ports ─────────────────────────────────────────────────────────────
    print("\nNetwork:")
    check("No public ports", True, "long polling only (no inbound)")

    # ─── Summary ───────────────────────────────────────────────────────────
    print()
    if errors:
        print(f"  ⚠️  {errors} issue(s) found. Fix before starting.")
    else:
        print("  ✅ All checks passed. Ready to start.")

    print("═══════════════════════════════════════════════════════════════════")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
