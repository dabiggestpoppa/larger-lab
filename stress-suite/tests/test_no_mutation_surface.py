"""No production/cloud/capital mutation surface inside the engine (G1 §17).

A deterministic G1 harness must not import network clients, shell-out for side
effects, broker/capital execution libraries, or write files outside its own
fixtures. We scan IMPORT LINES specifically (not vocabulary) so deny-by-default
strings like "capital" in risk-class enums do not cause false positives.
"""
import pathlib
import re

ENGINE_DIR = pathlib.Path(__file__).resolve().parents[1] / "engine"

_BANNED_IMPORT_ROOTS = (
    "socket",
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
    "subprocess",
    "os.system",
    "broker",
    "exchange_",
    "oanda",
    "nautilus",
    "ccxt",
)


def _import_lines() -> list[str]:
    lines = []
    for p in ENGINE_DIR.glob("*.py"):
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                lines.append(s)
    return lines


def test_no_banned_imports():
    found = []
    for s in _import_lines():
        root = re.split(r"[. ]", s)[1] if s.startswith("from") else s.split()[1]
        root = root.split(".")[0]
        if root in _BANNED_IMPORT_ROOTS:
            found.append(s)
    assert not found, f"banned import roots used in engine: {found}"


def test_no_dangerous_static_calls():
    joined = "\n".join(p.read_text(encoding="utf-8") for p in ENGINE_DIR.glob("*.py"))
    # never call out to an external shell or network for side effects
    assert ".system(" not in joined
    assert "stdout=PIPE" not in joined
    assert "urlopen(" not in joined
    assert "socket(" not in joined


def test_no_secret_tokens():
    joined = "\n".join(p.read_text(encoding="utf-8") for p in ENGINE_DIR.glob("*.py"))
    for token in ("PRIVATE_KEY", "API_TOKEN=", "BEGIN RSA", "BEGIN OPENSSH"):
        assert token not in joined