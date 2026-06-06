"""Watch hermes_telegram processes over time to see when child spawns."""
import time
import psutil

print("Watching for hermes_telegram processes (Ctrl+C to stop)...")
seen = set()
for i in range(30):
    current = {}
    for p in psutil.process_iter(['pid', 'ppid', 'name', 'create_time']):
        try:
            cmdline = ' '.join(p.info.get('cmdline') or [])
            if 'hermes_telegram' in cmdline:
                pid = p.info['pid']
                current[pid] = (p.info['ppid'], p.info['create_time'], cmdline[:80])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Find new PIDs
    new_pids = set(current.keys()) - seen
    if new_pids:
        for pid in new_pids:
            ppid, ct, cmd = current[pid]
            print(f"  T+{i}s NEW PID {pid} parent={ppid} create={ct:.1f} cmd={cmd}")
    seen.update(current.keys())
    time.sleep(1)

print(f"\nFinal set: {seen}")
