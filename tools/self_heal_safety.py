"""
Self-Heal Safety Watchdog
==========================
Runs in background during self-heal execution.
Checks every 60s if self-heal is still alive.
If self-heal dies/hangs → restarts gateway.
Self-terminates when self-heal completes (flag file) or after 5 min timeout.

This is the safety net MAD requested: agents can't fuck up the gateway
because this watchdog will restart it if self-heal goes sideways.
"""

import os
import sys
import time
import subprocess

if sys.platform == "win32":
    import ctypes

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
PID_FILE = os.path.join(WORKSPACE, ".self-heal-safety.pid")
STOP_FLAG = os.path.join(WORKSPACE, ".self-heal-complete.flag")
SELF_HEAL_PID_FILE = os.path.join(WORKSPACE, ".self-heal-running.pid")

MAX_RUNTIME = 300  # 5 minutes max
CHECK_INTERVAL = 60  # check every 60 seconds


def is_pid_alive(pid):
    """Check if a process is still running (Windows)."""
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(1, 0, pid)  # PROCESS_TERMINATE = 1
        if handle == 0:
            return False
        kernel32.CloseHandle(handle)
        return True
    except Exception:
        return True  # assume alive if we can't check


def restart_gateway():
    """Restart the OpenClaw gateway."""
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "restart"],
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        print(f"[SAFETY] Gateway restart triggered. Exit code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"[SAFETY] Failed to restart gateway: {e}")
        return False


def main():
    # Write our PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print(f"[SAFETY] Watchdog started (PID {os.getpid()}). Max runtime: {MAX_RUNTIME}s")

    deadline = time.time() + MAX_RUNTIME

    while time.time() < deadline:
        # Check if self-heal completed successfully
        if os.path.exists(STOP_FLAG):
            os.remove(STOP_FLAG)
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            print("[SAFETY] Self-heal completed successfully. Watchdog exiting.")
            return

        # Check if self-heal process is still alive
        if os.path.exists(SELF_HEAL_PID_FILE):
            try:
                with open(SELF_HEAL_PID_FILE, "r") as f:
                    pid = int(f.read().strip())

                if not is_pid_alive(pid):
                    print(f"[SAFETY] ⚠️  Self-heal process {pid} is DEAD!")
                    print("[SAFETY] Triggering gateway restart...")
                    restart_gateway()
                    # Clean up
                    if os.path.exists(PID_FILE):
                        os.remove(PID_FILE)
                    if os.path.exists(SELF_HEAL_PID_FILE):
                        os.remove(SELF_HEAL_PID_FILE)
                    return
                else:
                    print(f"[SAFETY] Self-heal (PID {pid}) still alive. OK.")
            except (ValueError, OSError) as e:
                print(f"[SAFETY] Error reading PID file: {e}")
        else:
            print("[SAFETY] No self-heal PID file found. Waiting...")

        time.sleep(CHECK_INTERVAL)

    # Timeout reached
    print("[SAFETY] 5-minute timeout reached. Cleaning up.")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


if __name__ == "__main__":
    main()
