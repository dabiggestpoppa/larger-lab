import subprocess, sys
for pid in [12684, 19772, 26700, 27800]:
    try:
        result = subprocess.run(
            ['wmic', 'process', 'where', 'ProcessId={}'.format(pid), 'get', 'CommandLine'],
            capture_output=True, text=True, timeout=5
        )
        cmd = result.stdout.strip().split('\n')[-1].strip() if result.stdout else '?'
        print("PID {}: {}".format(pid, cmd[:120]))
    except Exception as e:
        print("PID {}: error - {}".format(pid, e))
