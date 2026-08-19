"""QL-EXEC-R5.1 — TradeLocker DEMO read-only integration runner.

Connects the R5 TradeLockerBrokerSession to a REAL TradeLocker DEMO API in
READ-ONLY mode and emits the live evidence artifacts.

ABSOLUTE RULES:
- DEMO only. Any non-demo base URL is refused before a connection is made.
- No orders, no modifications, no closes. Four independent barriers
  (runtime authority gate, session barrier, transport barrier, capability
  profile) — proven by ``DemoReadOnlyAudit`` on every run.
- Credentials are read from the environment ONLY (never committed):
    TRADELOCKER_EMAIL
    TRADELOCKER_PASSWORD
    TRADELOCKER_SERVER
    TRADELOCKER_DEV_API_KEY  (optional)
- If credentials are absent the runner reports WAITING_TRADELOCKER_DEMO_ACCESS
  and makes ZERO network calls.

Usage:
    python runtime/tradelocker_demo_readonly.py [--out DIR] [--max-accounts N]

Exit codes: 0 = audit completed or waiting-for-access; 2 = blocked/error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_QL = Path(__file__).resolve().parent.parent  # quant-lab/
if str(_QL) not in sys.path:
    sys.path.insert(0, str(_QL))

from execution_runtime.tradelocker import (  # noqa: E402
    DEMO_BASE_URL,
    DemoEnvironmentError,
    DemoReadOnlyAudit,
    UrllibTransport,
    render_artifacts,
)

DEFAULT_OUT = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "execution_runtime_foundation"
    / "r5_1_tradelocker_demo_read_only"
)

ENV_EMAIL = "TRADELOCKER_EMAIL"
ENV_PASSWORD = "TRADELOCKER_PASSWORD"
ENV_SERVER = "TRADELOCKER_SERVER"
ENV_DEV_KEY = "TRADELOCKER_DEV_API_KEY"


def _secret_provider(name: str) -> str:
    return os.environ.get(name, "")


def _credentials_present() -> bool:
    return bool(
        os.environ.get(ENV_EMAIL)
        and os.environ.get(ENV_PASSWORD)
        and os.environ.get(ENV_SERVER)
    )


def _write_decision(out_dir: Path, payload: dict) -> Path:
    path = out_dir / "QL_EXEC_R5_1_DECISION.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def _waiting_decision(base_commit: str, reason: str) -> dict:
    return {
        "checkpoint": "QL-EXEC-R5.1-TRADELOCKER-DEMO-READ-ONLY-INTEGRATION",
        "status": "WAITING_TRADELOCKER_DEMO_ACCESS",
        "base_commit": base_commit,
        "reason": reason,
        "real_tradelocker_demo_connected": False,
        "real_tradelocker_live_connected": False,
        "real_tradelocker_order_attempted": False,
        "broker_write_calls": 0,
        "live_execution_authorized": False,
        "production_authorized": False,
        "human_review_required": True,
        "r5_2_authorized": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TradeLocker DEMO read-only audit")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="artifact output directory"
    )
    parser.add_argument(
        "--base-url",
        default=DEMO_BASE_URL,
        help="TradeLocker base URL (DEMO only; anything else is refused)",
    )
    parser.add_argument("--max-accounts", type=int, default=8)
    args = parser.parse_args(argv)

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    base_commit = os.environ.get("QL_R5_1_BASE_COMMIT", "")
    try:
        import subprocess

        base_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode()
            .strip()
        )
    except Exception:
        pass

    if not _credentials_present():
        missing = [k for k in (ENV_EMAIL, ENV_PASSWORD, ENV_SERVER) if not os.environ.get(k)]
        decision = _waiting_decision(
            base_commit,
            f"demo credentials not provided (missing env: {', '.join(missing)}); "
            "no connection attempted",
        )
        _write_decision(out_dir, decision)
        print(
            "STATUS: WAITING_TRADELOCKER_DEMO_ACCESS\n"
            "No TradeLocker demo credentials in the environment — no connection "
            "attempted. Set TRADELOCKER_EMAIL / TRADELOCKER_PASSWORD / "
            "TRADELOCKER_SERVER and re-run."
        )
        return 0

    # Credentials are present: run the read-only demo audit.
    transport = UrllibTransport()
    audit_runner = DemoReadOnlyAudit(
        transport=transport,
        base_url=args.base_url,
        secret_provider=_secret_provider,
        email_ref=ENV_EMAIL,
        password_ref=ENV_PASSWORD,
        server=os.environ.get(ENV_SERVER, ""),
        developer_api_key_ref=ENV_DEV_KEY,
        max_accounts=args.max_accounts,
    )
    try:
        audit = audit_runner.run()
    except DemoEnvironmentError as err:
        print(f"BLOCKED_DEMO_ENVIRONMENT: {err}")
        _write_decision(
            out_dir,
            {
                "checkpoint": "QL-EXEC-R5.1-TRADELOCKER-DEMO-READ-ONLY-INTEGRATION",
                "status": "BLOCKED_NON_DEMO_ENVIRONMENT",
                "base_commit": base_commit,
                "reason": str(err),
            },
        )
        return 2
    except Exception as err:  # noqa: BLE001 — audit must never fake success
        print(f"READ_ONLY_AUDIT_FAILED: {err}")
        _write_decision(
            out_dir,
            {
                "checkpoint": "QL-EXEC-R5.1-TRADELOCKER-DEMO-READ-ONLY-INTEGRATION",
                "status": "AUDIT_FAILED",
                "base_commit": base_commit,
                "reason": str(err)[:500],
                "real_tradelocker_demo_connected": False,
                "broker_write_calls": 0,
                "live_execution_authorized": False,
                "production_authorized": False,
            },
        )
        return 2

    rendered = render_artifacts(audit, out_dir)
    audit["base_commit"] = base_commit
    audit["status"] = (
        "PASS" if audit["health"].get("overall") == "HEALTHY_READ_ONLY" else "DEGRADED"
    )
    audit["r5_2_authorized"] = False
    audit["live_execution_authorized"] = False
    audit["production_authorized"] = False
    audit["human_review_required"] = True
    _write_decision(out_dir, audit)

    print(
        "STATUS: PASS (HEALTHY_READ_ONLY)\n"
        f"accounts: {audit.get('account_count')}   "
        f"broker_write_calls: {audit.get('broker_write_calls')}   "
        f"transport_write_attempts: {audit.get('transport_write_attempts')}\n"
        f"artifacts: {out_dir}\n"
        f"files: {len(rendered)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
