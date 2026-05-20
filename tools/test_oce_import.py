import sys
sys.path.insert(0, 'oce')
try:
    from backend.main import app
    print("Import OK")
except Exception as e:
    print(f"Import FAILED: {e}")
