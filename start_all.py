"""CEREBUS 24/7 - Single process manages all scanners. No spawning, no duplicates."""
import subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
LOG = ROOT / "logs" / "start_all.log"
LOG.parent.mkdir(exist_ok=True)

SCANNERS = [
    ("OCE",     [PY, "-m", "oce.backend.main"]),
    ("TG",      [PY, "scripts/telegram_gateway.py"]),
    ("CEREBUS", [PY, "quant-lab/ml/run_cerebus_live.py", "--interval", "300", "--engine", "both"]),
    ("MLR",     [PY, "quant-lab/mlr_validation/mlr_scanner.py"]),
    ("SIGNAL",  [PY, "scripts/signal_bot.py"]),
]

def log(m):
    t = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{t}] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    log("CEREBUS 24/7 STARTING")
    procs = {}
    for name, cmd in SCANNERS:
        p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs[name] = p
        log(f"  {name} PID={p.pid}")
        time.sleep(2)
    log(f"All {len(SCANNERS)} running")
    try:
        while True:
            time.sleep(30)
            for name, cmd in SCANNERS:
                if procs[name].poll() is None:
                    continue
                log(f"  {name} died, restarting...")
                p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                procs[name] = p
                log(f"  {name} restarted PID={p.pid}")
    except KeyboardInterrupt:
        for n, p in procs.items():
            if p.poll() is None:
                p.terminate()

if __name__ == "__main__":
    main()
