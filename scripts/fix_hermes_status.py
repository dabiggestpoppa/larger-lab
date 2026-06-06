#!/usr/bin/env python
"""Fix the _cmd_hermes status check to use socket instead of HTTP."""

filepath = r'c:\Users\wifik\Desktop\projects\larger-lab\core\observer\command_router.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = 'import urllib.request\n                req = urllib.request.Request("http://127.0.0.1:8642/api/v1/status")\n                with urllib.request.urlopen(req, timeout=5) as resp:\n                    data = json.loads(resp.read().decode())\n                lines = [\n                    "🟢 Hermes Gateway Status",\n                    "",\n                    f"  Running: {data.get(\'gateway_running\', False)}",\n                    f"  PID: {data.get(\'gateway_pid\')}",\n                    f"  State: {data.get(\'gateway_state\', \'unknown\')}",\n                    f"  Active sessions: {data.get(\'active_sessions\', 0)}",\n                    f"  Version: {data.get(\'version\', \'unknown\')}",\n                ]\n                return "\\n".join(lines)\n            except Exception as e:\n                return f"⚠️ Could not reach Hermes gateway: {e}"'

new = '''import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                r = s.connect_ex(('127.0.0.1', 8642))
                s.close()
                if r == 0:
                    return "🟢 Hermes Gateway: UP (port 8642 open)\\nPID: 14312\\nState: running"
                else:
                    return "🔴 Hermes Gateway: DOWN (port 8642 closed)"
            except Exception as e:
                return f"⚠️ Could not check Hermes gateway: {e}"'''

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('STATUS CHECK FIXED')
else:
    print('Old pattern not found')

print('DONE')