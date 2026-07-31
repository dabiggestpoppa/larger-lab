"""Find OC2 / openclaw / node processes."""
import psutil

print("=== OC2 / openclaw processes ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info.get('cmdline') or [])
        if 'openclaw' in cmd.lower() or 'oc2' in cmd.lower() or 'gateway.cmd' in cmd.lower():
            print(f"PID {p.info['pid']} {p.info['name']}: {cmd[:200]}")
    except Exception:
        pass

print()
print("=== All node processes ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'node' in p.info.get('name', '').lower():
            cmd = ' '.join(p.info.get('cmdline') or [])
            print(f"PID {p.info['pid']}: {cmd[:200]}")
    except Exception:
        pass

print()
print("=== Hermes / telegram bot processes ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info.get('cmdline') or [])
        if 'hermes_telegram' in cmd or 'telegram_gateway' in cmd:
            print(f"PID {p.info['pid']} {p.info['name']}: {cmd[:200]}")
    except Exception:
        pass
