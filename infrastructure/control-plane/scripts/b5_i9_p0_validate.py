#!/usr/bin/env python3
"""B5-I9 P0 packet validator — read-only, standard library only, offline.

Validates the planning packet against itself: identity, classification, arithmetic,
closure, handoff-state truth, boundary, style and the append-only ledger prefix. It
executes no B5-I9 implementation behaviour, because none exists.

Coverage is reported in stable categories so the mandatory total cannot shrink:

  mandatory      deterministic invariants over committed bytes; identical for a tree
  candidates     per-path inspections (boundary rows, citations); counted, never skipped
  git            one aggregate boundary check; scan total reported even when zero

Usage (repository root):
    python infrastructure/control-plane/scripts/b5_i9_p0_validate.py
    python infrastructure/control-plane/scripts/b5_i9_p0_validate.py --json
    python infrastructure/control-plane/scripts/b5_i9_p0_validate.py --self-check

`--self-check` validates twice in-process and fails if the mandatory count, the
candidate count or the packet digest differs between runs. Exit 0 means every
mandatory check passed; any failure prints `FAIL <check>: <detail>` and exits non-zero.
There is no flag that disables a check.
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
RATIFICATION = "OCE_B5_I9_P0_OPERATOR_RATIFICATION_v1.0.md"
RATIFICATION_IMPL = "OCE_B5_I9_IMPLEMENTATION_RATIFICATION_v1.0.md"
DELIVERABLES = [CONTRACT, BOUNDARY, REGISTRY, ACCEPTANCE, FAILURE, PLAN]

STATES = {"PLANNED", "MAPPED", "DEFERRED_WITH_OWNER", "BLOCKED"}
BINDINGS = {"test", "attestation", "static", "deferred", "runner"}
CATEGORIES = {"stage_identity", "extraction", "no_platform_law", "packaging",
              "book6_handoff", "g16", "boundary"}
CLASSES = {"EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "REFERENCE_ONLY",
           "PLATFORM_INTERNAL", "PRIVATE_API", "AUTHORITY_BEARING", "PROHIBITED",
           "DEFERRED_TO_BOOK_6", "NOT_APPLICABLE"}
STATUS_DRAFT = "DRAFT_FOR_OPERATOR_REVIEW"
STATUS_RATIFIED = "OPERATOR_ACCEPTED_PLANNING_FROZEN"
HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
PATHISH = re.compile(r"\.(py|md|json|yml|yaml)$|/")
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{20,}"), re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

failures: list[str] = []
warnings: list[str] = []
checks = 0
candidates = 0


def check(name, ok, detail=""):
    global checks
    checks += 1
    if not ok:
        failures.append("FAIL {}: {}".format(name, detail))
    return ok


def candidate(name, ok, detail=""):
    """Per-path inspection: counted separately, failures still mandatory."""
    global candidates
    candidates += 1
    if not ok:
        failures.append("FAIL {}: {}".format(name, detail))
    return ok


def text(name):
    return (DOCS / name).read_bytes().decode("utf-8")


def norm(name):
    return text(name).replace("\r\n", "\n")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def validate():
    """Run one full validation pass. Returns (mandatory, candidates, digest)."""
    global failures, warnings, checks, candidates
    failures, warnings, checks, candidates = [], [], 0, 0

    # ------------------------------------------------------------ identity
    reg = json.loads(text(REGISTRY))
    reqs = reg["requirements"]
    ids = [r["id"] for r in reqs]
    status = reg["status"]
    impl = reg.get("implementation") or {}
    IMPLEMENTED = impl.get("status") in {"IMPLEMENTED_PENDING_OPERATOR_REVIEW", "OPERATOR_ACCEPTED"}

    check("registry/kind", reg["kind"] == "oce-b5-i9-requirement-test-registry", reg["kind"])
    check("registry/base_sha", reg["base_sha"] == BASE, reg["base_sha"])
    check("registry/status_known", status in {STATUS_DRAFT, STATUS_RATIFIED}, status)
    expected = "IMPLEMENTED" if IMPLEMENTED else "NOT_STARTED"
    check("registry/implementation", reg["implementation_status"] == expected,
          reg["implementation_status"])
    check("ids/unique", len(ids) == len(set(ids)), "duplicate requirement id")
    check("ids/format", all(re.fullmatch(r"B5I9-[A-Z]{2}-\d{2}", i) for i in ids),
          [i for i in ids if not re.fullmatch(r"B5I9-[A-Z]{2}-\d{2}", i)])

    # ------------------------------------------------------------ state vocabulary
    vocab = reg.get("state_vocabulary") or {}
    check("vocab/present", isinstance(vocab, dict) and vocab, "state_vocabulary missing")
    check("vocab/covers_states", STATES <= set(vocab), sorted(STATES - set(vocab)))
    check("vocab/defines_mapped_node", "node" in vocab.get("MAPPED", "").lower(),
          vocab.get("MAPPED", ""))
    check("vocab/defines_planned_no_node",
          "no node" in vocab.get("PLANNED", "").lower()
          or "not applicable" in vocab.get("PLANNED", "").lower(),
          vocab.get("PLANNED", ""))

    # ------------------------------------------------------------ arithmetic
    cats, binds, states = {}, {}, {}
    for r in reqs:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
        binds[r["binding"]] = binds.get(r["binding"], 0) + 1
        states[r["state"]] = states.get(r["state"], 0) + 1

    arith = reg["arithmetic"]
    check("arith/total", arith["requirements_total"] == len(reqs),
          (arith["requirements_total"], len(reqs)))
    for key, local in (("by_category", cats), ("by_binding", binds), ("by_state", states)):
        check("arith/" + key, arith[key] == local, (arith[key], local))
    check("arith/pass_zero", arith["pass_claims"] == 0 and states.get("PASS", 0) == 0,
          states.get("PASS"))
    check("arith/categories_declared", set(cats) <= CATEGORIES, sorted(set(cats) - CATEGORIES))
    check("arith/bindings_declared", set(binds) <= BINDINGS, sorted(set(binds) - BINDINGS))
    check("arith/states_declared", set(states) <= STATES, sorted(set(states) - STATES))
    check("one_binding_each", all(r["binding"] in BINDINGS for r in reqs), "unknown binding")
    check("no_runner_binding", "runner" not in binds, "runner binding must be justified")

    # state vocabulary applied consistently: MAPPED <=> test, PLANNED <=> static/attestation
    bad_mapped = [r["id"] for r in reqs if (r["state"] == "MAPPED") != (r["binding"] == "test")]
    check("vocab/mapped_is_test_bound", not bad_mapped, bad_mapped)
    bad_planned = [r["id"] for r in reqs
                   if (r["state"] == "PLANNED") != (r["binding"] in {"static", "attestation"})]
    check("vocab/planned_is_non_executable", not bad_planned, bad_planned)
    bad_deferred = [r["id"] for r in reqs
                    if (r["state"] == "DEFERRED_WITH_OWNER") != (r["binding"] == "deferred")]
    check("vocab/deferred_is_deferred", not bad_deferred, bad_deferred)

    # ------------------------------------------------------------ closure
    nodes = [r["node"] for r in reqs if r["node"]]
    check("nodes/unique", len(nodes) == len(set(nodes)), "duplicate planned node")
    inventory = []
    for f in reg["planned_surface"]["files"]:
        target = ROOT / "infrastructure/control-plane" / f["path"]
        check("nodes/plan_only", target.exists() if IMPLEMENTED else not target.exists(),
              f["path"])
        inventory.extend(f["nodes"])
    check("nodes/inventory_matches", sorted(inventory) == sorted(nodes),
          set(inventory) ^ set(nodes))
    check("nodes/count", arith["planned_nodes"] == len(nodes),
          (arith["planned_nodes"], len(nodes)))
    check("nodes/files", arith["planned_files"] == len(reg["planned_surface"]["files"]),
          (arith["planned_files"], len(reg["planned_surface"]["files"])))
    check("nodes/test_rows_only", all(r["node"] for r in reqs if r["binding"] == "test"),
          [r["id"] for r in reqs if r["binding"] == "test" and not r["node"]])
    check("nodes/non_test_rows_none",
          all(not r["node"] for r in reqs if r["binding"] != "test"),
          [r["id"] for r in reqs if r["binding"] != "test" and r["node"]])
    check("nodes/class_qualified",
          all("::" in n and n.split("::")[0].startswith("Test") for n in nodes),
          [n for n in nodes if "::" not in n])
    if IMPLEMENTED:
        import ast as _ast
        harvested = []
        for f in reg["planned_surface"]["files"]:
            src = (ROOT / "infrastructure/control-plane" / f["path"]).read_text(encoding="utf-8")
            for node in _ast.parse(src).body:
                if isinstance(node, _ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, _ast.FunctionDef) and item.name.startswith("test_"):
                            harvested.append("{}::{}".format(node.name, item.name))
        check("nodes/executable_inventory", sorted(harvested) == sorted(nodes),
              sorted(set(harvested) ^ set(nodes)))
        check("nodes/no_orphans", len(harvested) == len(set(harvested)) == len(nodes),
              (len(harvested), len(set(harvested)), len(nodes)))

    deferred = [r for r in reqs if r["binding"] == "deferred"]
    check("deferred/owner", all(r.get("deferred_owner") and r.get("future_stage")
                                and r.get("observable") for r in deferred),
          [r["id"] for r in deferred if not r.get("deferred_owner")])
    check("deferred/owner_all_rows", all(r.get("owner") for r in reqs), "missing owner")

    # ------------------------------------------------------------ failure and mutation closure
    declared = {f["id"] for f in reg["failure_classes"]}
    used = {r["failure_class"] for r in reqs}
    check("failure/undeclared_reference", used <= declared, sorted(used - declared))
    check("failure/all_declared_bound", declared == used, sorted(declared - used))
    check("failure/count", arith["failure_classes_declared"] == len(declared),
          (arith["failure_classes_declared"], len(declared)))
    check("failure/bound_count", arith["failure_classes_bound"] == len(used),
          (arith["failure_classes_bound"], len(used)))
    check("failure/floor", len(declared) >= arith["failure_class_floor"], len(declared))
    fm = norm(FAILURE)
    for fid in sorted(declared):
        candidate("failure/matrix_row_" + fid, ("| " + fid + " |") in fm, "missing row")
    check("failure/matrix_no_extra",
          set(re.findall(r"^\| (F\d{2}) \|", fm, re.M)) == declared,
          sorted(set(re.findall(r"^\| (F\d{2}) \|", fm, re.M)) ^ declared))

    muts = [m["id"] for m in reg["mutations"]]
    check("mutation/unique", len(muts) == len(set(muts)), "duplicate mutation")
    check("mutation/floor", len(muts) >= arith["mutation_floor"] >= 10, len(muts))
    check("mutation/count", arith["mutations_planned"] == len(muts),
          (arith["mutations_planned"], len(muts)))
    check("mutation/discriminator", all(m["discriminator"] for m in reg["mutations"]),
          "missing discriminator")
    for m in reg["mutations"]:
        candidate("mutation/row_" + m["id"], ("| `" + m["id"] + "` |") in fm,
                  "missing mutation row")
    if IMPLEMENTED:
        check("mutation/executed", impl.get("nodes_executed") == len(nodes),
              (impl.get("nodes_executed"), len(nodes)))
        mutated = impl.get("mutations_executed") or 0
        check("mutation/mutations_executed", mutated == len(muts), (mutated, len(muts)))
        check("mutation/floor_executed", mutated >= arith["mutation_floor"], mutated)
        check("mutation/failure_classes_executed",
              impl.get("failure_classes_executed") == len(declared),
              impl.get("failure_classes_executed"))

    # ------------------------------------------------------------ classification boundary
    bnd = norm(BOUNDARY)
    rows = [l for l in bnd.split("\n") if re.match(r"^\| \d+ \| ", l)]
    check("classification/row_count", len(rows) == arith["extraction_candidates_classified"],
          (len(rows), arith["extraction_candidates_classified"]))
    seen = set()
    for line in rows:
        cells = [c.strip() for c in line.split("|")]
        cls = cells[4].strip("`")
        seen.add(cls)
        candidate("classification/vocabulary/" + cells[1][:24], cls in CLASSES, cls)
        src = cells[3].strip("`")
        for token in re.findall(r"`([^`]+)`", cells[3]) or ([src] if PATHISH.search(src) else []):
            token = token.split(",")[0].strip()
            if PATHISH.search(token) and "§" not in token and "*" not in token:
                candidate("classification/source_exists/" + token,
                          (ROOT / token).exists() or (DOCS / token).exists(), token)
        if cls.startswith("EXTRACTABLE"):
            candidate("classification/public_only/" + cells[1][:24],
                      cells[5] in {"Public doc", "Public JSON", "Public test", "Public schema",
                                   "Internal package", "Internal script"}, cells[5])
    check("classification/all_nine_used", seen == CLASSES, sorted(CLASSES ^ seen))
    check("classification/negative_control", "Negative control (worked)" in bnd,
          "missing worked negative control")
    check("classification/no_authority_promoted",
          not any("AUTHORITY_BEARING" in l and "EXTRACTABLE" in l for l in rows),
          "authority item promoted")
    for clause in ("NP-1", "NP-2", "NP-3", "NP-4", "NP-5", "NP-6", "NP-7", "NP-8"):
        check("law/" + clause, clause in bnd, "missing law clause")

    # ------------------------------------------------------------ matrix equality
    am = norm(ACCEPTANCE)
    matrix_ids = re.findall(r"^\| `(B5I9-[A-Z]{2}-\d{2})` \|", am, re.M)
    check("matrix/ids_unique", len(matrix_ids) == len(set(matrix_ids)), "duplicate matrix row")
    check("matrix/ids_equal_registry", set(matrix_ids) == set(ids),
          sorted(set(matrix_ids) ^ set(ids)))
    check("matrix/no_pass", "| PASS |" not in am, "matrix claims PASS")
    check("matrix/arithmetic_total", ("| Requirements | {} |".format(len(reqs))) in am,
          "total not stated")
    check("matrix/bindings_stated", all(b in am for b in binds), "binding missing from matrix")

    # ------------------------------------------------------------ status coherence
    ctr = norm(CONTRACT)
    impl_ratified = reg.get("implementation", {}).get("status") == "OPERATOR_ACCEPTED"
    if IMPLEMENTED:
        if impl_ratified:
            tokens = ["B5-I9 P0 = OPERATOR_ACCEPTED — PLANNING FROZEN",
                      "B5-I9 IMPLEMENTATION          = OPERATOR_ACCEPTED — RATIFIED",
                      "B5-I9 COMPLETE                = true",
                      "BOOK_5 GOVERNANCE COMPLETE    = true",
                      "MERGE_AUTHORIZED              = true (PR #25 only)",
                      "BOOK_6_AUTHORIZED             = false",
                      "BOOK_6_STARTED                = false",
                      "POST_BOOK_6_EVALUATION        = UNSTARTED"]
            check("status/implementation_ratification_present",
                  (DOCS / RATIFICATION_IMPL).exists(),
                  "ratified implementation without an implementation ratification record")
        else:
            tokens = ["B5-I9 P0 = OPERATOR_ACCEPTED — PLANNING FROZEN",
                      "B5-I9 IMPLEMENTATION          = IMPLEMENTED — PENDING OPERATOR REVIEW",
                      "MERGE_AUTHORIZED              = false",
                      "BOOK_6_AUTHORIZED             = false",
                      "BOOK_6_STARTED                = false",
                      "POST_BOOK_6_EVALUATION        = UNSTARTED"]
        check("status/ratification_present", (DOCS / RATIFICATION).exists(),
              "implemented status without a ratification record")
    elif status == STATUS_DRAFT:
        tokens = ["B5-I9 P0 = DRAFT FOR OPERATOR REVIEW", "B5-I9 IMPLEMENTATION = NOT STARTED",
                  "MERGE_AUTHORIZED              = false", "BOOK_6_AUTHORIZED             = false",
                  "BOOK_6_STARTED                = false",
                  "POST_BOOK_6_EVALUATION        = UNSTARTED"]
        check("status/ratification_absent", not (DOCS / RATIFICATION).exists(),
              "ratification record exists while status is draft")
    else:
        tokens = ["B5-I9 P0 = OPERATOR_ACCEPTED — PLANNING FROZEN",
                  "B5-I9 IMPLEMENTATION = NOT STARTED",
                  "MERGE_AUTHORIZED              = true (PR #24 only)",
                  "BOOK_6_AUTHORIZED             = false",
                  "BOOK_6_STARTED                = false",
                  "POST_BOOK_6_EVALUATION        = UNSTARTED"]
        check("status/ratification_present", (DOCS / RATIFICATION).exists(),
              "ratified status without a ratification record")
    for token in tokens:
        check("contract/status_" + token.split("=")[0].strip(), token in ctr, token)
    for name in DELIVERABLES:
        check("deliverable/" + name, (DOCS / name).exists(), name)

    # ------------------------------------------------------------ handoff truth
    locks = reg["locks"]
    check("handoff/book6_unauthorized", locks["book_6_authorized"] is False, "authorized")
    check("handoff/book6_not_started", locks["book_6_started"] is False, "started")
    check("handoff/evaluation_unstarted", locks["post_book_6_evaluation"] == "UNSTARTED",
          locks["post_book_6_evaluation"])
    if IMPLEMENTED:
        if impl_ratified:
            check("handoff/merge_scoped_pr25",
                  locks["merge_authorized"] is False
                  and "PR #25" in str(reg["implementation_ratification"]
                                      .get("merge_authorized_scope", "")),
                  reg["implementation_ratification"].get("merge_authorized_scope"))
        else:
            check("handoff/merge_false", locks["merge_authorized"] is False,
                  "merge authorized at implementation stage")
        check("handoff/contract_ratified", locks.get("book_6_contract_ratified") is True,
              locks.get("book_6_contract_ratified"))
    elif status == STATUS_DRAFT:
        check("handoff/merge_false", locks["merge_authorized"] is False, "merge authorized")
        check("handoff/contract_not_ratified",
              locks.get("book_6_contract_ratified") is False,
              locks.get("book_6_contract_ratified"))
    else:
        check("handoff/merge_scoped",
              locks["merge_authorized"] is True
              and "PR #24" in str(locks.get("merge_authorization_scope", "")),
              locks.get("merge_authorization_scope"))
        check("handoff/contract_ratified", locks.get("book_6_contract_ratified") is True,
              locks.get("book_6_contract_ratified"))
    ready = locks.get("book_6_input_ready") or {}
    check("handoff/input_ready_scope",
          "upstream" in str(ready.get("scope", "")).lower()
          and "excludes" in ready, ready)
    check("handoff/input_ready_true", ready.get("value") is True, ready.get("value"))
    check("handoff/input_ready_not_authorization",
          "never" in bnd.lower() and "authorization" in bnd.lower(), "no non-implication text")
    check("g16/open", locks["g16"]["status"] == "OPEN" and locks["g16"]["blocker"] == "B5I8-DF05",
          locks["g16"])
    check("g16/no_close_claim", "G16 = CLOSED" not in ctr and "G16 = CLOSED" not in bnd,
          "claims closed")
    check("g16/owner", "independent auditor" in locks["g16"]["owner"], locks["g16"]["owner"])
    check("capital/none", locks["capital_authority"] == "none", "capital authority present")
    check("cost/zero", locks["cost_usd"] == 0 and locks["cloud_mutations"] == 0, "cost")

    # ------------------------------------------------------------ file boundary (aggregate)
    allowed = {"docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md",
               "infrastructure/control-plane/scripts/b5_i9_p0_validate.py"}
    prefixes = ["docs/oce-golden-system/OCE_B5_I9_"]
    if IMPLEMENTED:
        prefixes += ["infrastructure/control-plane/tests/test_b5_i9_",
                     "infrastructure/control-plane/scripts/b5_i9_",
                     "infrastructure/control-plane/evidence/b5-i9/",
                     ".github/workflows/b5-i9-"]
    status_lines = [l for l in git("status", "--porcelain", "--untracked-files=all").stdout.splitlines() if l.strip()]
    offenders, untracked = [], []
    for line in status_lines:
        path = line[3:].strip().strip('"').replace("\\", "/")
        ok = any(path.startswith(p) for p in prefixes) or path in allowed
        if line.startswith("??"):
            untracked.append(path)
        if not ok:
            offenders.append(path)
    check("boundary/paths_authorized", not offenders, offenders)
    warnings.append("git candidates scanned: {} (untracked {})".format(
        len(status_lines), len(untracked)))
    test_files = sorted(ROOT.glob("infrastructure/control-plane/tests/test_b5_i9_*.py"))
    workflows = sorted(p for p in (ROOT / ".github/workflows").glob("*.yml")
                       if "b5_i9" in p.read_text(encoding="utf-8", errors="ignore").lower())
    if IMPLEMENTED:
        check("boundary/no_test_artifact", len(test_files) == len(reg["planned_surface"]["files"]),
              [p.name for p in test_files])
        check("boundary/no_workflow_artifact", len(workflows) == 1,
              [p.name for p in workflows])
        if workflows:
            wf = workflows[0].read_text(encoding="utf-8")
            for f in reg["planned_surface"]["files"]:
                check("selection/" + f["path"], f["path"] in wf, "not selected: " + f["path"])
            check("selection/validator", "b5_i9_p0_validate.py" in wf, "validator not invoked")
            check("selection/battery", "b5_i9_mutation_battery.py" in wf, "battery not invoked")
            check("selection/reproduce", "--check" in wf, "packet not reproduced")
    else:
        check("boundary/no_test_artifact", not test_files, "a B5-I9 test file exists")
        check("boundary/no_workflow_artifact", not workflows, "a workflow mentions b5_i9")
    exempt = {f["path"].split("/")[-1] for f in reg["planned_surface"]["files"]}
    if IMPLEMENTED:
        exempt |= {p.name for p in (ROOT / "infrastructure/control-plane/evidence/b5-i9").glob("*")}
    book6 = [p for p in ROOT.rglob("*") if p.is_file()
             and re.search(r"(book[_-]?6|b6)[_-]", p.name.lower())
             and ".git" not in p.parts and "__pycache__" not in p.parts
             and p.name not in exempt]
    check("boundary/no_book6_artifact", not book6, [p.name for p in book6])
    check("boundary/no_web_view_change", not any("frontend" in p for p in offenders),
          "frontend changed")

    # ------------------------------------------------------------ implemented packet
    if IMPLEMENTED:
        packet_dir = ROOT / "infrastructure/control-plane/evidence/b5-i9"
        check("packet/present", (packet_dir / "manifest.json").exists(), "no manifest")
        if (packet_dir / "manifest.json").exists():
            man = json.loads((packet_dir / "manifest.json").read_text(encoding="utf-8"))
            check("packet/artifact_count", man["artifact_count"] == len(man["artifacts"]),
                  man["artifact_count"])
            for row in man["artifacts"]:
                body = (packet_dir / row["path"]).read_bytes().replace(b"\r\n", b"\n")
                check("packet/hash_" + row["path"],
                      hashlib.sha256(body).hexdigest() == row["sha256"]
                      and len(body) == row["size_bytes"], row["path"])
        validation = packet_dir / "validation.json"
        check("packet/validation_present", validation.exists(), "no validation.json")
        if validation.exists():
            doc = json.loads(validation.read_text(encoding="utf-8"))
            check("packet/validation_clean", doc["failures"] == 0, doc["failures"])
            check("packet/validation_count", doc["checks_total"] >= 10, doc["checks_total"])
        gen = subprocess.run(
            [sys.executable, str(ROOT / "infrastructure/control-plane/scripts/b5_i9_factory_gate.py"),
             "--check"], cwd=ROOT, capture_output=True, text=True)
        check("packet/deterministic", gen.returncode == 0, (gen.stdout + gen.stderr)[-300:])
        battery = subprocess.run(
            [sys.executable, str(ROOT / "infrastructure/control-plane/scripts/b5_i9_mutation_battery.py"),
             "--json", str(ROOT / ".b5i9-battery-check.json")], cwd=ROOT,
            capture_output=True, text=True)
        check("mutation/battery_green", battery.returncode == 0,
              (battery.stdout + battery.stderr)[-300:])
        residue = ROOT / ".b5i9-battery-check.json"
        if residue.exists():
            residue.unlink()
        check("boundary/no_scratch_residue", not residue.exists(), str(residue))

    # ------------------------------------------------------------ style, secrets, prefix
    def consistent_newlines(raw):
        """One newline style, no bare CR. CRLF is a checkout artefact, not a law."""
        cr = bytes([13])
        lf = bytes([10])
        if cr in raw.replace(cr + lf, b""):
            return False
        has_crlf = (cr + lf) in raw
        lone_lf = raw.count(lf) - raw.count(cr + lf)
        return not (has_crlf and lone_lf > 0)

    for name in DELIVERABLES:
        raw = (DOCS / name).read_bytes()
        check("style/newlines_" + name, consistent_newlines(raw),
              "mixed or bare-CR newlines")
        check("style/no_trailing_ws_" + name,
              not [l for l in raw.decode("utf-8").replace("\r\n", "\n").split("\n")
                   if l.rstrip() != l], "trailing whitespace")
    ledger_text = LEDGER.read_bytes().decode("utf-8").replace("\r\n", "\n")
    marker = "## 21. B5-I9 P0"
    check("style/ledger_newlines", consistent_newlines(LEDGER.read_bytes()),
          "ledger has mixed or bare-CR newlines")
    check("style/appended_section_clean",
          not [l for l in ledger_text[ledger_text.index(marker):].split("\n")
               if l.rstrip() != l], "trailing whitespace in the appended section")
    for pattern in SECRET_PATTERNS:
        for name in DELIVERABLES:
            check("secret/" + pattern.pattern, not pattern.search(text(name)), name)

    raw = LEDGER.read_bytes()
    ledger_norm = raw.replace(b"\r\n", b"\n")
    check("ledger/prefix_sha",
          hashlib.sha256(ledger_norm[:PREFIX_LEN]).hexdigest() == PREFIX_SHA,
          hashlib.sha256(ledger_norm[:PREFIX_LEN]).hexdigest())
    check("ledger/grew", len(ledger_norm) > PREFIX_LEN, len(ledger_norm))
    check("ledger/section_present", b"## 21. B5-I9 P0" in ledger_norm, "missing section 21")

    diff_check = git("diff", "--check")
    check("git/diff_check", diff_check.returncode == 0, diff_check.stdout.strip()[:400])
    cited = sorted(set(HEX40.findall("".join(norm(n) for n in DELIVERABLES))))
    for sha in cited:
        candidate("citation/resolves_" + sha[:10],
                  git("cat-file", "-e", sha).returncode == 0, sha)

    digest = hashlib.sha256()
    for name in DELIVERABLES:
        digest.update(name.encode("utf-8"))
        digest.update(hashlib.sha256(norm(name).encode("utf-8")).digest())
    return checks, candidates, digest.hexdigest()


def main(argv):
    as_json = "--json" in argv
    self_check = "--self-check" in argv
    m1, c1, d1 = validate()
    f1 = list(failures)
    if self_check:
        m2, c2, d2 = validate()
        stable = (m1 == m2 and c1 == c2 and d1 == d2 and f1 == failures)
        if not stable:
            failures.append("FAIL self_check/stability: {} {} {} vs {} {} {}".format(
                m1, c1, d1[:12], m2, c2, d2[:12]))
    ledger_norm = LEDGER.read_bytes().replace(b"\r\n", b"\n")
    out = {
        "validator": "b5_i9_p0_validate.py",
        "status": "PASS" if not failures else "FAIL",
        "mandatory_checks": m1,
        "candidate_inspections": c1,
        "failures": len(failures),
        "warnings": warnings,
        "ledger_normalized_bytes": len(ledger_norm),
        "ledger_prefix_sha": hashlib.sha256(ledger_norm[:PREFIX_LEN]).hexdigest(),
        "packet_digest": d1,
        "details": failures,
    }
    if as_json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print("B5-I9 P0 validator")
        print("  status", out["status"])
        print("  mandatory checks", m1, "| failures", len(failures))
        print("  candidate inspections", c1)
        for w in warnings:
            print("  note", w)
        print("  ledger normalized bytes", len(ledger_norm),
              "| prefix", out["ledger_prefix_sha"][:16])
        print("  packet digest", d1)
        for line in failures:
            print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
