"""
System Guardrail Monitor
========================
Checks for:
1. New non-Microsoft scheduled tasks
2. New startup folder entries
3. Tasks with restrictive ACLs

Run periodically or on-demand. Reports findings, does NOT auto-delete.
"""
import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("scripts/guardrail_state.json")
STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

# Ignore Microsoft/system tasks
IGNORED_PREFIXES = (
    "\\Microsoft\\", "\\MicrosoftEdge", "\\Mozilla\\", "\\Google\\",
    "\\Adobe\\", "\\HP\\", "\\Dell\\", "\\Intel\\", "\\NVIDIA\\",
    "\\Realtek\\", "\\Lenovo\\", "\\ASUS\\", "\\Logitech\\",
    "\\Dropbox\\", "\\OneDrive\\", "\\Spotify\\", "\\Discord\\",
    "\\Steam\\", "\\Epic\\", "\\Razer\\", "\\Corsair\\", "\\MSI\\",
    "\\Samsung\\", "\\Apple\\", "\\Oracle\\", "\\Java\\",
    "\\OpenSSH", "\\WSL\\", "\\Docker\\", "\\Git\\",
    "\\Node.js", "\\Python\\", "\\VSCode", "\\VisualStudio",
    "\\JetBrains\\", "\\Slack\\", "\\Teams\\", "\\Zoom\\",
    "\\Skype\\", "\\Telegram", "\\WhatsApp", "\\Signal\\",
    "\\VLC\\", "\\WinRAR\\", "\\7-Zip", "\\Firefox", "\\Chrome",
    "\\Edge\\", "\\Brave\\", "\\Opera\\", "\\Windows\\",
)


def get_tasks():
    """Get all scheduled tasks."""
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "LIST", "/v"],
            capture_output=True, text=True, timeout=30
        )
        tasks = []
        current = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("TaskName:"):
                if current.get("task_name"):
                    tasks.append(current)
                current = {"task_name": line.split(":", 1)[1].strip()}
            elif ":" in line and current:
                key, val = line.split(":", 1)
                current[key.strip().lower()] = val.strip()
        if current.get("task_name"):
            tasks.append(current)
        return tasks
    except Exception as e:
        return [{"error": str(e)}]


def get_startup():
    """Get startup folder entries."""
    entries = []
    if STARTUP_DIR.exists():
        for f in STARTUP_DIR.iterdir():
            if f.suffix.lower() not in (".disabled", ".bak"):
                entries.append({
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                })
    return entries


def check_acl(task_name):
    """Check if task file has restrictive ACLs."""
    task_path = Path(f"C:\\Windows\\System32\\Tasks\\{task_name}")
    if not task_path.exists():
        return None
    try:
        result = subprocess.run(["icacls", str(task_path)], capture_output=True, text=True, timeout=10)
        user = os.environ.get("USERNAME", "")
        for line in result.stdout.splitlines():
            if user.lower() in line.lower():
                if "(F)" not in line and "(M)" not in line:
                    return f"RESTRICTED: {line.strip()}"
        return "OK"
    except Exception as e:
        return f"ERROR: {e}"


def is_ignored(name):
    """Check if task name should be ignored."""
    for prefix in IGNORED_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


def main():
    print("=" * 60)
    print("SYSTEM GUARDRAIL CHECK")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"known_tasks": {}, "known_startup": [], "last_check": None}
    alerts = []

    # ── Scheduled tasks ──
    print("\n[1] Scheduled Tasks (non-Microsoft only)")
    tasks = get_tasks()
    current_names = set()

    for task in tasks:
        name = task.get("task_name", "")
        if not name or name == "error":
            continue
        if is_ignored(name):
            continue
        current_names.add(name)
        status = task.get("status", "?")
        run_as = task.get("run as user", "?")
        cmd = task.get("task to run", "?")[:80]

        if name not in state.get("known_tasks", {}):
            alerts.append(f"NEW TASK: {name} (status={status}, run_as={run_as})")
            print(f"  WARNING NEW: {name}")
            print(f"    Status: {status} | Run as: {run_as}")
            print(f"    Command: {cmd}")
        else:
            print(f"  OK {name} ({status})")

        # ACL check
        short = name.lstrip("\\")
        acl = check_acl(short)
        if acl and acl.startswith("RESTRICTED"):
            alerts.append(f"RESTRICTED ACL: {name}")
            print(f"    DANGER RESTRICTED ACL: {acl}")

    for old in state.get("known_tasks", {}):
        if old not in current_names:
            print(f"  INFO REMOVED: {old}")

    # ── Startup folder ──
    print("\n[2] Startup Folder")
    startup = get_startup()
    current_startup = {e["name"] for e in startup}

    for entry in startup:
        if entry["name"] not in state.get("known_startup", []):
            alerts.append(f"NEW STARTUP: {entry['name']}")
            print(f"  WARNING NEW: {entry['name']} ({entry['size']} bytes)")
        else:
            print(f"  OK {entry['name']}")

    for old in state.get("known_startup", []):
        if old not in current_startup:
            print(f"  INFO REMOVED: {old}")

    # ── Summary ──
    print("\n" + "=" * 60)
    if alerts:
        print(f"DANGER {len(alerts)} ALERT(S):")
        for a in alerts:
            print(f"   * {a}")
    else:
        print("OK No new issues found.")

    # Save state
    state["known_tasks"] = {n: True for n in current_names}
    state["known_startup"] = list(current_startup)
    state["last_check"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"\nState saved to {STATE_FILE}")
    return len(alerts)


if __name__ == "__main__":
    sys.exit(main())
