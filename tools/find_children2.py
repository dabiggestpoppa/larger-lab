"""Find all python processes and their parents via psutil."""
try:
    import psutil
except ImportError:
    print("psutil not installed")
    raise SystemExit(1)

for p in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        if 'hermes_telegram' in cmd:
            print(f"PID {p.info['pid']} parent={p.info['ppid']} name={p.info['name']}")
            print(f"  cmd: {cmd[:200]}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
