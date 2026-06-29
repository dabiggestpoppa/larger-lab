"""Start OCE backend with proper error handling."""
import os
import sys
import traceback

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONPATH"] = r"C:\Users\wifik\Desktop\projects\larger-lab"

# Change to project root
os.chdir(r"C:\Users\wifik\Desktop\projects\larger-lab")

# Write startup log
with open("oce-startup.log", "w") as f:
    f.write("Starting OCE backend...\n")
    f.write(f"Python: {sys.version}\n")
    f.write(f"CWD: {os.getcwd()}\n")
    f.write(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}\n")

try:
    from oce.backend.main import app
    with open("oce-startup.log", "a") as f:
        f.write("Import OK\n")
    
    import uvicorn
    with open("oce-startup.log", "a") as f:
        f.write("Starting uvicorn...\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
except Exception as e:
    with open("oce-startup.log", "a") as f:
        f.write(f"ERROR: {e}\n")
        f.write(traceback.format_exc())
    sys.exit(1)
