"""
Simple keep-alive for CEREBUS scanner + Discord bot.
Restarts if crashed. No guarddog — just a lightweight loop.
"""
import os, sys, time, subprocess
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
REPO_ROOT = Path(__file__).parent.parent

PROCESSES = [
    {
        "name": "CEREBUS Scanner",
        "cmd": [sys.executable, str(REPO_ROOT / "quant-lab" / "ml" / "run_cerebus_unified.py"), "--interval", "300"],
        "pid_file": REPO_ROOT / ".scanner.pid",
    },
    {
        "name": "Discord Signal Bot",
        "cmd": [sys.executable, str(REPO_ROOT / "scripts" / "discord_signal_bot.py")],
        "pid_file": REPO_ROOT / ".discord_bot.pid",
    },
]

CHECK_INTERVAL = 30  # seconds between checks


def is_running(pid_file):
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        # Check if process exists
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return str(pid) in result.stdout
    except Exception:
        return False


def start_process(proc_info):
    """Start a process and save its PID."""
    try:
        proc = subprocess.Popen(
            proc_info["cmd"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        proc_info["pid_file"].write_text(str(proc.pid))
        print(f"[KEEP_ALIVE] Started {proc_info['name']} (PID {proc.pid})")
        return True
    except Exception as e:
        print(f"[KEEP_ALIVE] Failed to start {proc_info['name']}: {e}")
        return False


def main():
    print("=" * 50)
    print("CEREBUS Keep-Alive — 24/7 Process Monitor")
    print("=" * 50)
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Processes: {[p['name'] for p in PROCESSES]}")
    print()

    # Start all processes initially
    for proc_info in PROCESSES:
        if not is_running(proc_info["pid_file"]):
            start_process(proc_info)
        else:
            pid = int(proc_info["pid_file"].read_text().strip())
            print(f"[KEEP_ALIVE] {proc_info['name']} already running (PID {pid})")

    # Monitor loop
    while True:
        time.sleep(CHECK_INTERVAL)
        for proc_info in PROCESSES:
            if not is_running(proc_info["pid_file"]):
                print(f"[KEEP_ALIVE] {proc_info['name']} crashed! Restarting...")
                start_process(proc_info)


if __name__ == "__main__":
    main()
