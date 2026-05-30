import time
import sys

# Simple test: does a Python process with time.sleep survive when started with Start-Process -WindowStyle Hidden?
for i in range(3):
    print(f"Cycle {i}", flush=True)
    time.sleep(5)
print("DONE", flush=True)
