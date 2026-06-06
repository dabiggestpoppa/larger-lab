"""Dump ALL python processes with their parent/cmdline."""
import psutil

print(f"psutil version: {psutil.__version__}")
print(f"Total python procs visible: {sum(1 for p in psutil.process_iter(['name']) if p.info['name'] == 'python.exe')}")
print()

for p in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'create_time']):
    try:
        if p.info['name'] and 'python' in p.info['name'].lower():
            cmd = ' '.join(p.info.get('cmdline') or [])[:200]
            ppid = p.info.get('ppid')
            ct = p.info.get('create_time')
            print(f"PID {p.info['pid']} parent={ppid} create={ct}")
            print(f"  cmd: {cmd}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
