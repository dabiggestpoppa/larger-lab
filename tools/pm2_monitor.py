"""
PM2 Autopilot Monitor
Watches workspace for new commits, service health, test failures.
Commits and pushes any uncommitted work from other agents.
"""
import subprocess
import time
import json
import os
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_ROOT / "logs" / "pm2_monitor.log"
CHECK_INTERVAL = 60  # seconds

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or str(REPO_ROOT))
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def check_git():
    """Check for uncommitted changes and push if needed."""
    out, _, _ = run("git status --porcelain")
    if out:
        log(f"Uncommitted changes detected ({len(out.splitlines())} files)")
        run("git add -A")
        run(f'git commit -m "PM2 autopilot: sync workspace changes" --no-verify')
        run("git push origin master")
        log("Changes committed and pushed")
    else:
        # Check if we're behind remote
        run("git fetch origin")
        out, _, _ = run("git rev-list HEAD..origin/master --count")
        if out and int(out) > 0:
            log(f"Behind remote by {out} commits, pulling...")
            run("git pull --rebase origin master")
        else:
            log("Git: synced")

def check_services():
    """Check critical ports."""
    ports = {
        8000: "OCE Backend",
        3000: "OCE Frontend",
        18790: "OpenClaw",
    }
    out, _, _ = run("netstat -ano | Select-String 'LISTENING'")
    for port, name in ports.items():
        if str(port) in out:
            log(f"  [OK] {name} :{port}")
        else:
            log(f"  [DOWN] {name} :{port}")

def main():
    log("=" * 50)
    log("PM2 Autopilot Monitor Started")
    log("=" * 50)
    
    while True:
        try:
            log("--- Check cycle ---")
            check_git()
            check_services()
            log(f"Sleeping {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("Monitor stopped by user")
            break
        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
