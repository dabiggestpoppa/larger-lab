import urllib.request
req = urllib.request.Request("http://localhost:12393/", method="GET")
with urllib.request.urlopen(req, timeout=5) as resp:
    print(f"Status: {resp.status}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Content-Length: {resp.headers.get('Content-Length')}")
    body = resp.read()
    print(f"\nBody ({len(body)} bytes):")
    print(body[:500].decode('utf-8', errors='replace'))
