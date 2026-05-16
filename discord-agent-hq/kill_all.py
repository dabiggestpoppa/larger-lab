import os, signal, subprocess

# Find all python processes
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
                       capture_output=True, text=True)
print("Python processes:")
print(result.stdout)

# Kill all except current
current_pid = os.getpid()
for line in result.stdout.strip().split('\n'):
    if line.strip():
        parts = line.strip().split(',')
        if len(parts) >= 2:
            pid_str = parts[1].strip('"')
            try:
                pid = int(pid_str)
                if pid != current_pid:
                    print(f"Killing PID {pid}")
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            except:
                pass

# Verify
result2 = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
                        capture_output=True, text=True)
print("\nAfter cleanup:")
print(result2.stdout)
