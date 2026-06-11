import os, sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Simulate what telegram_gateway.py does
_file = os.path.abspath(r'C:\Users\wifik\Desktop\projects\larger-lab\scripts\telegram_gateway.py')
_env_path = os.path.join(os.path.dirname(os.path.dirname(_file)), ".env")
print(f"env path: {_env_path}")
print(f"exists: {os.path.exists(_env_path)}")

if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _parts = _line.split("=", 1)
                os.environ.setdefault(_parts[0].strip(), _parts[1].strip())

print(f"TELEGRAM_TOKEN: {'SET' if os.environ.get('TELEGRAM_TOKEN') else 'NOT SET'}")
if os.environ.get('TELEGRAM_TOKEN'):
    print(f"Token length: {len(os.environ['TELEGRAM_TOKEN'])}")
    print(f"Token starts with: {os.environ['TELEGRAM_TOKEN'][:10]}...")
