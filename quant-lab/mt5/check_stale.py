import subprocess
import sys

pids = [6600, 19852, 23588]
for pid in pids:
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Process -Id {} -ErrorAction Stop | Select-Object Id, ProcessName, @{N="CmdLine";E={(Get-CimInstance Win32_Process -Filter "ProcessId={}").CommandLine}}'.format(pid, pid)],
            capture_output=True, text=True, timeout=5
        )
        out = result.stdout.strip()
        if out:
            print('PID {}: {}'.format(pid, out))
        else:
            print('PID {}: Not found (already dead)'.format(pid))
    except:
        print('PID {}: Not found or access denied'.format(pid))
