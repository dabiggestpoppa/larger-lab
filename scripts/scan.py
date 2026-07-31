import subprocess, ctypes, ctypes.wintypes

MAX_PATH = 260

def get_cmdline(pid):
    try:
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return "N/A"
        buf = ctypes.create_unicode_buffer(MAX_PATH)
        size = ctypes.c_size_t(ctypes.sizeof(buf))
        ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, ctypes.byref(buf), ctypes.byref(size))
        ctypes.windll.kernel32.CloseHandle(handle)
        return buf.value
    except:
        return "N/A"

import subprocess
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                       capture_output=True, text=True, errors='replace')
pids = []
for line in result.stdout.strip().split('\n')[1:]:
    parts = line.strip('"').split('","')
    if len(parts) >= 2:
        pids.append(int(parts[1]))

print(f"=== {len(pids)} PYTHON PROCESSES ===\n")
for pid in sorted(pids):
    cmd = get_cmdline(pid)
    # Extract key parts
    if 'demo_bridge' in cmd:
        tag = "[DEMO BRIDGE]"
    elif 'hermes_telegram' in cmd:
        tag = "[HERMES TELEGRAM]"
    elif 'po_heartbeat' in cmd:
        tag = "[PO HEARTBEAT]"
    elif 'cerebus_guardian' in cmd:
        tag = "[CEREBUS GUARDIAN]"
    elif 'cerebus_live_bridge' in cmd:
        tag = "[CEREBUS LIVE BRIDGE]"
    elif 'symmetry_trap_executor' in cmd:
        tag = "[ST EXECUTOR - SHOULD BE DEAD]"
    else:
        tag = "[UNKNOWN]"
    short = cmd.split('\\')[-1] if '\\' in cmd else cmd
    print(f"PID {pid:6d} | {tag} | {short}")

print("\n=== NEW/UNTRACKED FILES ===")
result2 = subprocess.run(['git', '-C', 'C:/Users/wifik/Desktop/projects/larger-lab', 'ls-files', '--others', '--exclude-standard'],
                        capture_output=True, text=True, cwd='C:/Users/wifik/Desktop/projects/larger-lab')
for line in result2.stdout.strip().split('\n'):
    if line.strip():
        print(f"  ?? {line}")