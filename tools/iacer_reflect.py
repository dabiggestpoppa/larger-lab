"""
IACER Reflection Engine
=======================
Run after every 5 tool calls or task completions.
Produces a structured reflection using the IACER framework.

Usage: python tools/iacer_reflect.py [--check]
  --check: only print the counter status, don't increment
"""
import json, os, sys, datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COUNTER_FILE = os.path.join(
    r"C:\Users\wifik\Desktop\projects\larger-lab",
    "memory-bank", "iacer_counter.json"
)

def load_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return json.load(f)
    return {"count": 0, "last_reflect": None, "total_reflections": 0}

def save_counter(data):
    os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def reset_counter():
    save_counter({"count": 0, "last_reflect": datetime.datetime.now().isoformat(), "total_reflections": 0})

if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_counter()
        print("[IACER] Counter reset.")
    elif "--check" in sys.argv:
        c = load_counter()
        remaining = 5 - c["count"]
        print(f"[IACER] Count: {c['count']}/5 | Remaining: {c['count']}/5 | Total reflections: {c['total_reflections']}")
        if remaining <= 0:
            print("[IACER] READY FOR REFLECTION")
        else:
            print(f"[IACER] {remaining} more calls until reflection")
    else:
        c = load_counter()
        c["count"] += 1
        remaining = 5 - c["count"]
        if remaining <= 0:
            c["count"] = 0
            c["total_reflections"] += 1
            c["last_reflect"] = datetime.datetime.now().isoformat()
            save_counter(c)
            print("[IACER] REFLECTION DUE — write IACER check now.")
        else:
            save_counter(c)
            print(f"[IACER] Count: {c['count']}/5 | {remaining} until next reflection")
