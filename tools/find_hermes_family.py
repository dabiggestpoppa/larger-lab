"""Find Hermes process family tree."""
import psutil

for p in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'create_time']):
    try:
        cmd = ' '.join(p.info.get('cmdline') or [])
        if 'hermes_telegram' in cmd and 'python' in cmd:
            parent_pid = p.info['ppid']
            try:
                parent = psutil.Process(parent_pid).name() if parent_pid > 0 else 'N/A'
            except:
                parent = '?'
            print(f"PID {p.info['pid']} parent_pid={parent_pid} parent_name={parent} create_t={p.info['create_time']:.2f}")
            print(f"  cmd: {cmd[:200]}")
    except Exception as e:
        pass
