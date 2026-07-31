import subprocess, time
# Kill old API server
result = subprocess.run(
    ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like \"*api_server*\"} | Stop-Process -Force; Write-Host \"killed\"'],
    capture_output=True, text=True, timeout=10
)
print(result.stdout, result.stderr)
time.sleep(1)

# Start new API server
proc = subprocess.Popen(
    ['python', '-m', 'uvicorn', 'api_server:app', '--host', '0.0.0.0', '--port', '8090'],
    cwd=r'C:\Users\wifik\Desktop\projects\larger-lab\sniper-dashboard',
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
print(f"API server started, PID {proc.pid}")
time.sleep(3)

# Quick test
import urllib.request
try:
    resp = urllib.request.urlopen('http://localhost:8090/api/true-costs?size_k=50', timeout=5)
    data = json.loads(resp.read()) if False else None
    print("TRUE-COSTS endpoint: OK")
except Exception as e:
    print(f"TRUE-COSTS endpoint: {e}")

try:
    resp = urllib.request.urlopen('http://localhost:8090/api/matrix', timeout=5)
    print("MATRIX endpoint: OK")
except Exception as e:
    print(f"MATRIX endpoint: {e}")

print("Done.")
