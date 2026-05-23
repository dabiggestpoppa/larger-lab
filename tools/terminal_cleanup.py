"""
Terminal Cleanup Utility
Kills stale python/node processes. Active PIDs tracked via .active-pids.json.
Usage: python tools/terminal_cleanup.py --force
Register: python tools/terminal_cleanup.py --register PID
"""
import os, sys, json, signal
from pathlib import Path
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

WORKSPACE_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent
PID_FILE = TOOLS_DIR / ".active-pids.json"
STALE_THRESHOLD_MINUTES = 30

def get_active_pids():
    if PID_FILE.exists():
        try:
            data = json.loads(PID_FILE.read_text())
            return set(data.get("pids", []))
        except Exception:
            pass
    return set()

def register_pid(pid):
    active = get_active_pids()
    active.add(int(pid))
    PID_FILE.write_text(json.dumps({"pids": list(active), "updated": datetime.now().isoformat()}))

def unregister_pid(pid):
    active = get_active_pids()
    active.discard(int(pid))
    PID_FILE.write_text(json.dumps({"pids": list(active), "updated": datetime.now().isoformat()}))

def get_python_processes():
    if not HAS_PSUTIL:
        return []
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            info = proc.info
            if info["name"] and "python" in info["name"].lower():
                cmdline = " ".join(info["cmdline"]) if info["cmdline"] else ""
                create_time = datetime.fromtimestamp(info["create_time"])
                age_minutes = (datetime.now() - create_time).total_seconds() / 60
                if info["pid"] == os.getpid():
                    continue
                if "terminal_cleanup" in cmdline:
                    continue
                processes.append({"pid": info["pid"], "cmdline": cmdline[:200],
                                  "age_minutes": round(age_minutes, 1)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def is_active(pid, cmdline):
    if pid in get_active_pids():
        return True
    keywords = ["test_11_1_b","chaos_20x","chaos_engine","chaos_scaled","chaos_amplified",
                "chaos_continuous","chaos_long","chaos_runner","owl_autopilot","progress-sync",
                "progress_sync","memory_sync","chat_sync","jupyter","uvicorn","flask","streamlit",
                "stability_runner","semantic_test","analyze_topology","observability_stress"]
    cl = cmdline.lower()
    return any(k in cl for k in keywords)

def cleanup_stale(force=False, threshold=STALE_THRESHOLD_MINUTES):
    processes = get_python_processes()
    if not processes:
        print("[CLEANUP] No python processes found.")
        return []
    print(f"\n[CLEANUP] {len(processes)} python process(es):")
    print(f"{'PID':<8} {'Age':<10} {'Status':<8} {'Command'}")
    print("-" * 80)
    killed, kept = [], []
    for p in processes:
        active = is_active(p["pid"], p["cmdline"])
        stale = p["age_minutes"] > threshold
        status = "ACTIVE" if active else ("STALE" if stale else "RECENT")
        print(f"{p['pid']:<8} {p['age_minutes']:<10.1f} {status:<8} {p['cmdline'][:60]}")
        if stale and not active:
            if force:
                try:
                    psutil.Process(p["pid"]).terminate()
                    killed.append(p["pid"])
                    print(f"  -> KILLED PID {p['pid']}")
                except Exception as e:
                    print(f"  -> FAILED: {e}")
            else:
                print(f"  -> WOULD KILL (use --force)")
        else:
            kept.append(p["pid"])
    print(f"\n[CLEANUP] Killed: {len(killed)}, Kept: {len(kept)}")
    return killed

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--threshold", type=int, default=STALE_THRESHOLD_MINUTES)
    parser.add_argument("--register", type=int)
    parser.add_argument("--unregister", type=int)
    args = parser.parse_args()

    if args.register:
        register_pid(args.register)
        print(f"[CLEANUP] Registered PID {args.register}")
        return
    if args.unregister:
        unregister_pid(args.unregister)
        print(f"[CLEANUP] Unregistered PID {args.unregister}")
        return

    print("=" * 50)
    print("  TERMINAL CLEANUP")
    print(f"  Active PIDs: {get_active_pids()}")
    print(f"  Force: {args.force}")
    cleanup_stale(force=args.force, threshold=args.threshold)

if __name__ == "__main__":
    main()
