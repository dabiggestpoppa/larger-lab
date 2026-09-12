"""Book 3 — representative safe job definitions (B3-C8 proof).

Each job is a small, allowlisted ``python -c`` program that reads its
parameters from ``input/params.json`` inside the bounded attempt workspace
and writes artifacts into ``output/``. Jobs are executed through the real
production path (BoundedRunner + ContentAddressable artifact store), never
by direct function substitution. These prove worker execution only; the
synthetic backtest is deterministic fixture output and is NOT a validated
Quant Lab strategy. No broker / paper / live trading connection exists.
"""
from __future__ import annotations
import json
import textwrap
from pathlib import Path
from typing import Optional

# Task programme keyed by supported task type. Each returns python source.
_PROGRAMS: dict[str, str] = {}


def _define(job_type: str, src: str) -> None:
    src = textwrap.dedent(src).strip()
    _PROGRAMS[job_type] = src


_define("b3.deterministic-hash", """
import hashlib, json, pathlib
p = pathlib.Path("input/params.json")
params = json.loads(p.read_text(encoding="utf-8"))
value = str(params.get("value", ""))
digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
pathlib.Path("output/hash.json").write_text(
    json.dumps({"value": value, "sha256": digest}), encoding="utf-8")
""")

_define("b3.bounded-compute", """
import json, math, pathlib
p = json.loads(pathlib.Path("input/params.json").read_text(encoding="utf-8"))
n = max(0, int(p.get("n", 1000)))
total = sum(math.sqrt(i) for i in range(n))
pathlib.Path("output/compute.json").write_text(
    json.dumps({"n": n, "sum_sqrt": round(total, 6)}), encoding="utf-8")
""")

_define("b3.repo-inventory", """
import json, pathlib
lines = pathlib.Path("input/README.txt").read_text(encoding="utf-8").splitlines()
pathlib.Path("output/inventory.json").write_text(
    json.dumps({"lines": len(lines), "paths": ["input/README.txt"]}),
    encoding="utf-8")
""")

_define("b3.synthetic-backtest", """
# Deterministic synthetic fixture — proves worker execution ONLY.
# NOT a validated Quant Lab strategy.
import json, math, pathlib
p = json.loads(pathlib.Path("input/params.json").read_text(encoding="utf-8"))
seed = int(p.get("seed", 42)); n = max(1, int(p.get("n", 120)))
x = seed
returns = []
for _ in range(n):
    x = (1103515245 * x + 12345) % (2**31)
    returns.append(((x % 2000) / 10000.0) - 0.1)
cum = 1.0
for r in returns:
    cum *= (1.0 + r)
ann_ret = cum ** (1.0 / n) - 1.0
pathlib.Path("output/backtest.json").write_text(
    json.dumps({"fixture": "synthetic", "periods": n, "cumulative": round(cum, 6),
                "per_period_geometric_mean": round(ann_ret, 6),
                "note": "synthetic proof of worker execution only"}),
    encoding="utf-8")
""")

_define("b3.analysis-artifact", """
import json, pathlib
p = json.loads(pathlib.Path("input/params.json").read_text(encoding="utf-8"))
title = str(p.get("title", "OCE Analysis Report"))
rows = p.get("rows", 3)
html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1><ul>"
for i in range(1, rows + 1):
    html += f"<li>metric-{i}: ok</li>"
html += "</ul></body></html>"
pathlib.Path("output/report.html").write_text(html, encoding="utf-8")
""")

_define("b3.cancel-during-exec", """
import time, pathlib
for _ in range(100000):
    pathlib.Path("output/progress.txt").write_text("working", encoding="utf-8")
    time.sleep(0.5)
""")

_define("b3.timeout-violation", """
import time
time.sleep(60)
""")


def supported_job_types() -> list[str]:
    return list(_PROGRAMS)


def program_for(job_type: str) -> str:
    if job_type not in _PROGRAMS:
        raise KeyError(f"unsupported task type '{job_type}' — fail closed")
    return _PROGRAMS[job_type]


def prepare_workspace(workspace: Path, job_type: str, params: Optional[dict] = None) -> None:
    """Seed the input/output/cache directories and inputs a job needs."""
    (workspace / "input").mkdir(parents=True, exist_ok=True)
    (workspace / "output").mkdir(parents=True, exist_ok=True)
    (workspace / "cache").mkdir(parents=True, exist_ok=True)
    params = params or {}
    if job_type in ("b3.repo-inventory",):
        readme = workspace / "input" / "README.txt"
        readme.write_text("OCE representative repo inventory fixture line ONE\n"
                          "line two\n", encoding="utf-8")
    else:
        (workspace / "input" / "params.json").write_text(
            json.dumps(params), encoding="utf-8")


def job_type_requires_readme(job_type: str) -> bool:
    return job_type == "b3.repo-inventory"