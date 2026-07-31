"""Find all python processes and their parents."""
import subprocess

WMI_CMD = 'wmic process where "name=\'python.exe\'" get ProcessId,ParentProcessId,CommandLine /format:list'
result = subprocess.run(WMI_CMD, shell=True, capture_output=True, text=True)
procs = []
current = {}
for line in result.stdout.splitlines():
    line = line.strip()
    if not line:
        if current:
            procs.append(current)
            current = {}
    elif '=' in line:
        k, v = line.split('=', 1)
        current[k] = v
if current:
    procs.append(current)

# Filter only hermes-related
for p in procs:
    cmd = p.get('CommandLine', '')
    if 'hermes' in cmd.lower():
        print(f"PID {p.get('ProcessId')} parent={p.get('ParentProcessId')}")
        print(f"  cmd: {cmd[:200]}")
        print()
