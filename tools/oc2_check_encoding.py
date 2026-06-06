"""Check OC2 session file encoding."""
import json
from pathlib import Path

f = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions\f37df753-11ce-478e-ae3a-6ed2cba4c9a7.jsonl")

# Read as bytes first
raw = f.read_bytes()
print(f"File size: {len(raw)} bytes")
print(f"First 50 bytes hex: {raw[:50].hex()}")

# Try reading as UTF-8
try:
    text = raw.decode("utf-8")
    print(f"UTF-8 decode: OK ({len(text)} chars)")
    # Parse JSON
    lines = text.strip().splitlines()
    print(f"Lines: {len(lines)}")
    for i, line in enumerate(lines[:5]):
        try:
            d = json.loads(line)
            dtype = d.get("type", "?")
            if dtype == "message":
                role = d.get("message", {}).get("role", "?")
                content = d.get("message", {}).get("content", "")
                text_val = ""
                if isinstance(content, list):
                    for p in content:
                        if isinstance(p, dict) and p.get("type") == "text":
                            text_val += p.get("text", "")
                print(f"  [{i}] {role}: {text_val[:100]!r}")
            else:
                print(f"  [{i}] {dtype}")
        except Exception as e:
            print(f"  [{i}] parse err: {e}")
except UnicodeDecodeError as e:
    print(f"UTF-8 decode FAILED: {e}")
    # Try latin-1
    text = raw.decode("latin-1")
    print(f"Latin-1 decode: OK ({len(text)} chars)")
