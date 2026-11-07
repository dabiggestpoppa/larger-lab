#!/usr/bin/env python3
"""B5-I9 P0 packet validator — read-only, standard library only, offline.

Validates the planning packet against itself: identity, classification, arithmetic,
closure, boundary, style and the append-only ledger prefix. It executes no B5-I9
implementation behaviour, because none exists.

Exit code 0 means every check passed. Any failure prints `FAIL <check>: <detail>` and
exits non-zero. There is no flag that turns a check off.

Usage (from the repository root):
    python infrastructure/control-plane/scripts/b5_i9_p0_validate.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs/oce-golden-system"
BASE = "833f7d1b9f2dfec2986fb9516d0abde06bf23dae"
LEDGER = DOCS / "OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md"
PREFIX_LEN = 191950
PREFIX_SHA = "83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30"

CONTRACT = "OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md"
BOUNDARY = "OCE_B5_I9_EXTRACTION_AND_PACKAGING_BOUNDARY_v1.0.md"
REGISTRY = "OCE_B5_I9_REQUIREMENT_TEST_REGISTRY_v1.0.json"
ACCEPTANCE = "OCE_B5_I9_ACCEPTANCE_MATRIX_v1.0.md"
FAILURE = "OCE_B5_I9_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md"
PLAN = "OCE_B5_I9_CONSTRUCTION_PLAN_v1.0.md"
DELIVERABLES = [CONTRACT, BOUNDARY, REGISTRY, ACCEPTANCE, FAILURE, PLAN]

STATES = {"PLANNED", "MAPPED", "DEFERRED_WITH_OWNER", "BLOCKED"}
BINDINGS = {"test", "attestation", "static", "deferred", "runner"}
CATEGORIES = {"stage_identity", "extraction", "no_platform_law", "packaging", "book6_handoff", "g16", "boundary"}
CLASSES = {"EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "REFERENCE_ONLY",
           "PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED",
           "DEFERRED_TO_BOOK_6", "NOT_APPLICABLE"}
HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{20,}"), re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

failures: list[str] = []
checks = 0


def check(name, ok, detail=""):
    global checks
    checks += 1
    if not ok:
        failures.append("FAIL {}: {}".format(name, detail))
    return ok


def text(name):
    return (DOCS / name).read_bytes().decode("utf-8")


def norm(name):
    return text(name).replace("\r\n", "\n")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


# ---------------------------------------------------------------- identity
reg = json.loads(text(REGISTRY))
reqs = reg["requirements"]
ids = [r["id"] for r in reqs]

check("registry/kind", reg["kind"] == "oce-b5-i9-requirement-test-registry", reg["kind"])
check("registry/base_sha", reg["base_sha"] == BASE, reg["base_sha"])
check("registry/status", reg["status"] == "DRAFT_FOR_OPERATOR_REVIEW", reg["status"])
check("registry/implementation", reg["implementation_status"] == "NOT_STARTED", reg["implementation_status"])
check("ids/unique", len(ids) == len(set(ids)), "duplicate requirement id")
check("ids/format", all(re.fullmatch(r"B5I9-[A-Z]{2}-\d{2}", i) for i in ids),
      [i for i in ids if not re.fullmatch(r"B5I9-[A-Z]{2}-\d{2}", i)])

# ---------------------------------------------------------------- arithmetic recomputed
cats, binds, states = {}, {}, {}
for r in reqs:
    cats[r["category"]] = cats.get(r["category"], 0) + 1
    binds[r["binding"]] = binds.get(r["binding"], 0) + 1
    states[r["state"]] = states.get(r["state"], 0) + 1

arith = reg["arithmetic"]
check("arith/total", arith["requirements_total"] == len(reqs), (arith["requirements_total"], len(reqs)))
for key, local in (("by_category", cats), ("by_binding", binds), ("by_state", states)):
    check("arith/" + key, arith[key] == local, (arith[key], local))
check("arith/pass_zero", arith["pass_claims"] == 0 and states.get("PASS", 0) == 0, states.get("PASS"))
check("arith/categories_declared", set(cats) <= CATEGORIES, sorted(set(cats) - CATEGORIES))
check("arith/bindings_declared", set(binds) <= BINDINGS, sorted(set(binds) - BINDINGS))
check("arith/states_declared", set(states) <= STATES, sorted(set(states) - STATES))
check("one_binding_each", all(r["binding"] in BINDINGS for r in reqs),
      [r["id"] for r in reqs if r["binding"] not in BINDINGS])
check("no_runner_binding", "runner" not in binds, "a runner binding must be justified, none is")

# ---------------------------------------------------------------- closure
nodes = [r["node"] for r in reqs if r["node"]]
check("nodes/unique", len(nodes) == len(set(nodes)), "duplicate planned node")
inventory = []
for f in reg["planned_surface"]["files"]:
    check("nodes/file_exists_as_plan_only", not (ROOT / f["path"]).exists(), f["path"])
    inventory.extend(f["nodes"])
check("nodes/inventory_matches", sorted(inventory) == sorted(nodes),
      set(inventory) ^ set(nodes))
check("nodes/count", arith["planned_nodes"] == len(nodes), (arith["planned_nodes"], len(nodes)))
check("nodes/files", arith["planned_files"] == len(reg["planned_surface"]["files"]),
      (arith["planned_files"], len(reg["planned_surface"]["files"])))
check("nodes/test_rows_only", all(r["node"] for r in reqs if r["binding"] == "test"),
      [r["id"] for r in reqs if r["binding"] == "test" and not r["node"]])
check("nodes/non_test_rows_none", all(not r["node"] for r in reqs if r["binding"] != "test"),
      [r["id"] for r in reqs if r["binding"] != "test" and r["node"]])
check("nodes/class_qualified", all("::" in n and n.split("::")[0].startswith("Test")
                                   for n in nodes), [n for n in nodes if "::" not in n])

deferred = [r for r in reqs if r["binding"] == "deferred"]
check("deferred/owner", all(r.get("deferred_owner") and r.get("future_stage") for r in deferred),
      [r["id"] for r in deferred if not r.get("deferred_owner")])
check("deferred/attested_owner", all(r.get("owner") for r in reqs), "missing owner")
check("deferred/count", arith.get("requirements_total") == len(reqs))

# ---------------------------------------------------------------- failure and mutation closure
declared = {f["id"] for f in reg["failure_classes"]}
used = {r["failure_class"] for r in reqs}
check("failure/undeclared_reference", used <= declared, sorted(used - declared))
check("failure/all_declared_bound", declared == used, sorted(declared - used))
check("failure/count", arith["failure_classes_declared"] == len(declared),
      (arith["failure_classes_declared"], len(declared)))
check("failure/floor", len(declared) >= arith["failure_class_floor"], len(declared))
fm = norm(FAILURE)
for fid in declared:
    check("failure/matrix_row_" + fid, ("| " + fid + " |") in fm, "missing row")
check("failure/matrix_no_extra",
      set(re.findall(r"^\| (F\d{2}) \|", fm, re.M)) == declared,
      sorted(set(re.findall(r"^\| (F\d{2}) \|", fm, re.M)) ^ declared))

muts = [m["id"] for m in reg["mutations"]]
check("mutation/unique", len(muts) == len(set(muts)), "duplicate mutation")
check("mutation/floor", len(muts) >= arith["mutation_floor"] >= 10, len(muts))
check("mutation/discriminator", all(m["discriminator"] for m in reg["mutations"]), "missing discriminator")
for m in reg["mutations"]:
    check("mutation/row_" + m["id"], ("| `" + m["id"] + "` |") in fm, "missing mutation row")

# ---------------------------------------------------------------- classification boundary
bnd = norm(BOUNDARY)
rows = [l for l in bnd.split("\n") if re.match(r"^\| \d+ \| ", l)]
check("classification/row_count", len(rows) == arith["extraction_candidates_classified"],
      (len(rows), arith["extraction_candidates_classified"]))
seen = set()
for line in rows:
    cells = [c.strip() for c in line.split("|")]
    cls = cells[4].strip("`")
    seen.add(cls)
    check("classification/vocabulary", cls in CLASSES, cls)
    if cls.startswith("EXTRACTABLE"):
        check("classification/public_only", cells[5] in {"Public doc", "Public JSON", "Public test", "Public schema", "Internal package", "Internal script"},
              (cells[1], cells[5]))
check("classification/all_nine_used", seen == CLASSES, sorted(CLASSES ^ seen))
check("classification/negative_control", "Negative control (worked)" in bnd, "missing worked negative control")
check("classification/no_authority_promoted",
      not any("AUTHORITY_BEARING" in l and "EXTRACTABLE" in l for l in rows), "authority item promoted")
for clause in ("NP-1", "NP-2", "NP-3", "NP-4", "NP-5", "NP-6", "NP-7", "NP-8"):
    check("law/" + clause, clause in bnd, "missing law clause")

# ---------------------------------------------------------------- contract/matrix equality
am = norm(ACCEPTANCE)
matrix_ids = re.findall(r"^\| `(B5I9-[A-Z]{2}-\d{2})` \|", am, re.M)
check("matrix/ids_unique", len(matrix_ids) == len(set(matrix_ids)), "duplicate matrix row")
check("matrix/ids_equal_registry", set(matrix_ids) == set(ids), sorted(set(matrix_ids) ^ set(ids)))
check("matrix/no_pass", "| PASS |" not in am, "matrix claims PASS")
check("matrix/arithmetic_total", ("| Requirements | {} |".format(len(reqs))) in am, "total not stated")
check("matrix/bindings_stated", all(b in am for b in binds), "binding missing from matrix")

ctr = norm(CONTRACT)
for token in ("B5-I9 P0 = DRAFT FOR OPERATOR REVIEW", "B5-I9 IMPLEMENTATION = NOT STARTED",
              "MERGE_AUTHORIZED              = false", "BOOK_6_AUTHORIZED             = false",
              "BOOK_6_STARTED                = false", "POST_BOOK_6_EVALUATION        = UNSTARTED"):
    check("contract/status_" + token.split("=")[0].strip(), token in ctr, token)
for name in DELIVERABLES:
    check("deliverable/" + name, (DOCS / name).exists(), name)

# ---------------------------------------------------------------- handoff and G16 truth
check("handoff/book6_unauthorized", reg["locks"]["book_6_authorized"] is False, "authorized")
check("handoff/book6_not_started", reg["locks"]["book_6_started"] is False, "started")
check("handoff/evaluation_unstarted", reg["locks"]["post_book_6_evaluation"] == "UNSTARTED",
      reg["locks"]["post_book_6_evaluation"])
check("handoff/merge_false", reg["locks"]["merge_authorized"] is False, "merge authorized")
check("g16/open", reg["locks"]["g16"]["status"] == "OPEN" and reg["locks"]["g16"]["blocker"] == "B5I8-DF05",
      reg["locks"]["g16"])
check("g16/no_close_claim", "G16 = CLOSED" not in ctr and "G16 = CLOSED" not in bnd, "claims closed")
check("g16/owner", "independent auditor" in reg["locks"]["g16"]["owner"], reg["locks"]["g16"]["owner"])
check("capital/none", reg["locks"]["capital_authority"] == "none", "capital authority present")
check("cost/zero", reg["locks"]["cost_usd"] == 0 and reg["locks"]["cloud_mutations"] == 0, "cost")

# ---------------------------------------------------------------- boundary of files
status = git("status", "--porcelain", "--untracked-files=all").stdout.splitlines()
allowed_prefix = "docs/oce-golden-system/OCE_B5_I9_"
ALLOWED = {"docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md",
           "infrastructure/control-plane/scripts/b5_i9_p0_validate.py"}
changed = []
for line in status:
    if not line:
        continue
    path = line[3:].strip().strip('"').replace("\\", "/")
    if line.startswith("??"):
        check("boundary/untracked", path.startswith(allowed_prefix) or path in ALLOWED, path)
        continue
    changed.append(path)
for path in changed:
    ok = (path.startswith(allowed_prefix)
          or path in {"docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md",
                      "infrastructure/control-plane/scripts/b5_i9_p0_validate.py"})
    check("boundary/changed_path", ok, path)
check("boundary/no_test_artifact", not list(ROOT.glob("infrastructure/control-plane/tests/test_b5_i9_*.py")),
      "a B5-I9 test file exists")
check("boundary/no_workflow_artifact",
      not [p for p in (ROOT / ".github/workflows").glob("*.yml") if "b5_i9" in p.read_text(encoding="utf-8", errors="ignore").lower()],
      "a workflow mentions b5_i9")
check("boundary/no_book6_artifact",
      not [p for p in ROOT.rglob("*") if p.is_file()
           and re.search(r"(book[_-]?6|b6)[_-]", p.name.lower())
           and ".git" not in p.parts and "book5" not in str(p).lower()],
      "a Book 6 artifact exists")
check("boundary/no_web_view_change", not any("frontend" in c for c in changed), "frontend changed")

# ---------------------------------------------------------------- style, secrets, prefix
for name in DELIVERABLES:
    raw = (DOCS / name).read_bytes()
    check("style/crlf_" + name, b"\r\n" in raw, "not CRLF")
    check("style/no_trailing_ws_" + name,
          not [l for l in raw.decode("utf-8").replace("\r\n", "\n").split("\n") if l.rstrip() != l],
          "trailing whitespace")
ledger_text = LEDGER.read_bytes().decode("utf-8").replace("\r\n", "\n")
marker = "## 21. B5-I9 P0"
check("style/ledger_crlf", b"\r\n" in LEDGER.read_bytes(), "ledger not CRLF")
check("style/appended_section_clean",
      not [l for l in ledger_text[ledger_text.index(marker):].split("\n") if l.rstrip() != l],
      "trailing whitespace in the appended section")
for pattern in SECRET_PATTERNS:
    for name in DELIVERABLES:
        check("secret/" + pattern.pattern, not pattern.search(text(name)), name)

raw = LEDGER.read_bytes()
ledger_norm = raw.replace(b"\r\n", b"\n")
check("ledger/prefix_sha", hashlib.sha256(ledger_norm[:PREFIX_LEN]).hexdigest() == PREFIX_SHA,
      hashlib.sha256(ledger_norm[:PREFIX_LEN]).hexdigest())
check("ledger/grew", len(ledger_norm) > PREFIX_LEN, len(ledger_norm))
check("ledger/section_present", b"## 21. B5-I9 P0" in ledger_norm, "missing B5-I9 section")

diff_check = git("diff", "--check")
check("git/diff_check", diff_check.returncode == 0, diff_check.stdout.strip()[:400])
cited = sorted(set(HEX40.findall("".join(norm(n) for n in DELIVERABLES))))
for sha in cited:
    rc = git("cat-file", "-e", sha).returncode
    check("citation/resolves_" + sha[:10], rc == 0, sha)

# ---------------------------------------------------------------- report
digest = hashlib.sha256()
for name in DELIVERABLES:
    digest.update(name.encode("utf-8"))
    digest.update(hashlib.sha256(norm(name).encode("utf-8")).digest())
print("B5-I9 P0 validator")
print("  requirements", len(reqs), "| nodes", len(nodes), "| files", len(reg["planned_surface"]["files"]))
print("  categories", cats)
print("  bindings", binds)
print("  states", states)
print("  failure classes", len(declared), "| mutations", len(muts))
print("  ledger normalized bytes", len(ledger_norm), "| prefix", hashlib.sha256(ledger_norm[:PREFIX_LEN]).hexdigest()[:16])
print("  packet digest", digest.hexdigest())
print("  checks", checks, "| failures", len(failures))
for line in failures:
    print(line)
sys.exit(1 if failures else 0)
