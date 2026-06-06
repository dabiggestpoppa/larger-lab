"""Check Hermes PIDs."""
import psutil
for p in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline']):
    try:
        cmdline = ' '.join(p.info.get('cmdline') or [])
        if 'hermes_telegram' in cmdline:
            print(f"PID {p.info['pid']} parent={p.info['ppid']} name={p.info['name']} alive={p.is_running()}")
            print(f"  cmd: {cmdline[:200]}")
    except Exception:
        pass
