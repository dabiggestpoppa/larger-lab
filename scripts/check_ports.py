import socket
services = [(8000,'OCE Backend'),(3000,'OCE Frontend'),(8642,'Hermes'),(8765,'MCP'),(18790,'OC2')]
for port, name in services:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    r = s.connect_ex(('127.0.0.1', port))
    s.close()
    status = 'UP' if r == 0 else 'DOWN'
    icon = 'OK' if r == 0 else 'FAIL'
    print(f'  [{icon}] {name} :{port} {status}')