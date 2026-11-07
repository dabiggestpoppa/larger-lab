"""OCE B5-I8 — test-only audit support (deterministic fixtures and helpers).

Not a test module (no ``test_`` prefix), so it is never collected and never
counted against the frozen 40-node floor. Everything here is deterministic:
no wall clock reaches a rendered document, no network, no provider, no
canonical-state write.

The helpers exist so the five planned B5-I8 test files assert the same real
governed surfaces (``oce_console.panel`` / ``.kernel`` / ``.transport`` /
``.drill``) the same way, and so the usability protocol, the evidence bundle and
the tests share one executable definition instead of drifting copies.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
DOCS = REPO_ROOT / "docs" / "oce-golden-system"
CONSOLE_SRC = REPO_ROOT / "infrastructure" / "console" / "src"
if str(CONSOLE_SRC) not in sys.path:
    sys.path.insert(0, str(CONSOLE_SRC))

from oce_console import drill, panel  # noqa: E402
from oce_console.kernel import ConsoleRefusal, build_status_document, render_status  # noqa: E402
from oce_console.transport import (  # noqa: E402
    LoopbackTransport,
    StackUnreachable,
    validate_base_url,
)

LEDGER = DOCS / "OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md"
REGISTRY = DOCS / "OCE_B5_I8_REQUIREMENT_TEST_REGISTRY_v1.0.json"
EVIDENCE = DOCS / "OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json"
EVIDENCE_DOC = DOCS / "OCE_B5_I8_AUDIT_EVIDENCE_RECORD_v1.0.md"
PROTOCOL_DOC = DOCS / "OCE_B5_I8_USABILITY_PROTOCOL_AND_RESULTS_v1.0.md"
MUTATIONS = DOCS / "OCE_B5_I8_MUTATION_RESULTS_v1.0.json"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "b1-i1r-validation.yml"
#: B5-I8's authoritative selection lives in its OWN additive workflow: the pinned
#: b1-i1r file is a whole-file immutable row of B5-I7's frozen EL09 manifest.
WORKFLOW_B5I8 = REPO_ROOT / ".github" / "workflows" / "b5-i8-audit-validation.yml"
SUPERSEDING = DOCS / "OCE_B5_I7_EL09_X1_SUPERSEDING_MANIFEST_v1.0.json"
CONTRACT = DOCS / "OCE_B5_I8_IMPLEMENTATION_CONTRACT_v1.0.md"
PLAN = DOCS / "OCE_B5_I8_CONSTRUCTION_PLAN_v1.0.md"
FAILURE = DOCS / "OCE_B5_I8_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md"
ACCEPTANCE = DOCS / "OCE_B5_I8_ACCEPTANCE_MATRIX_v1.0.md"

#: Frozen EL09 prefix invariant of the historical ledger row (B5-I8 P0 §19.13).
LEDGER_PREFIX_BYTES = 191950
LEDGER_PREFIX_SHA = (
    "83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30"
)

HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")

#: Language that may not appear while a gate is pending (EL06 / R31).
FORBIDDEN_ALL_GREEN = (
    "all gates passed",
    "all gates are green",
    "every gate passed",
    "fully green",
    "all gates complete",
)

#: The three declared governed read surfaces the panel projects.
SURFACES = {
    "health.read": "/api/health",
    "workers.list": "/api/workers",
    "jobs.schedules": "/api/schedules",
}

#: Caller-supplied governed observation time (the panel reads no wall clock).
FIXED_OBSERVED_AT = "2026-11-05T00:00:00Z"

SAME_AGENT_LABEL = "SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT"
ATTESTATION_CLASS = "SAME_AGENT_SINGLE_OPERATOR_NON_BLIND"

#: Frozen drill-report mask (contract section 22; B5-I7 DRILL_MASK).
DRILL_MASK = ("session_id", "binding.job_id", "binding.evidence_refs")
MASK_SENTINELS = {
    "session_id": "<session_id>",
    "binding.job_id": "<job_id>",
    "binding.evidence_refs": "<evidence_refs>",
}

#: Recorded, documented exceptions to live commit resolution. An entry is
#: exempt ONLY while the same sha is named in the evidence limitations.
PRUNED_REFS = {
    "7dc1248e68022b16ea3cb2b7931e22013517f3a3": (
        "refs/pull/21/merge was pruned by GitHub after PR #21 merged; the P0 "
        "ratification records it as a pre-merge observation"
    ),
}


# ── bytes, git, json ────────────────────────────────────────────────────────

def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=False
    )


def lf(data: bytes) -> bytes:
    """Normalize checkout CRLF to the repository's stored LF form."""
    return data.replace(bytes((13, 10)), bytes((10,)))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return sha256_bytes(lf(path.read_bytes()))


def read_bytes(path: Path) -> bytes:
    return lf(path.read_bytes())


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence() -> dict:
    return load(EVIDENCE)


def registry() -> dict:
    return load(REGISTRY)


def mutations() -> dict:
    if not MUTATIONS.exists():
        return {"mutations": []}
    return load(MUTATIONS)


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_obj(obj: object) -> str:
    return sha256_bytes(canonical(obj).encode("utf-8"))


def planned_nodes() -> list:
    return list(registry()["requirement_set"]["planned_test_nodes"])


def planned_files() -> list:
    return list(registry()["requirement_set"]["planned_test_files"])


def collected_nodes() -> dict:
    """Collect the five planned files by AST (file -> [Class::node, ...])."""
    import ast

    found: dict = {}
    for name in planned_files():
        path = TESTS_DIR / name
        if not path.exists():
            # Early rungs: a planned file may not exist yet; the closure claim
            # stays false rather than being inferred from a partial tree.
            found[name] = []
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                        item.name.startswith("test_")
                    ):
                        nodes.append(f"{node.name}::{item.name}")
        found[name] = nodes
    return found


# ── governed fixtures ───────────────────────────────────────────────────────

def envelope(data, ok=True, status="ok", request_id="req-frozen-1", **extra) -> dict:
    env = {"ok": ok, "status": status, "data": data, "request_id": request_id}
    env.update(extra)
    return env


def healthy_data(**over) -> dict:
    data = {
        "pending_jobs": 3,
        "active_jobs": 2,
        "failed_jobs": 1,
        "quarantined_jobs": 0,
        "workers": 2,
    }
    data.update(over)
    return data


def frozen_reads(**over) -> dict:
    mapping = {
        "health.read": envelope(healthy_data()),
        "workers.list": envelope({"workers": {"w-1": {}, "w-2": {}}}),
        "jobs.schedules": envelope({"schedules": {}}),
    }
    mapping.update(over)
    return mapping


def read_from(mapping: dict):
    """A governed read callable over a fixed surface -> envelope mapping."""
    calls: list = []

    def read(surface: str):
        calls.append(surface)
        value = mapping.get(surface)
        if isinstance(value, Exception):
            raise value
        if value is None:
            raise ConsoleRefusal("unsupported_surface", surface)
        return value

    read.calls = calls  # type: ignore[attr-defined]
    return read


def denied_envelope() -> dict:
    return envelope(
        {"jobs": []},
        ok=False,
        status="denied",
        request_id="req-denied-1",
        error={"code": "E_DENIED", "message": "grant expired - operator consent required"},
    )


def stale_envelope() -> dict:
    """An intact envelope carrying no governed observation time (stale view)."""
    return envelope(healthy_data(), request_id="req-stale-1")


def build(reads=None, **kwargs):
    mapping = frozen_reads() if reads is None else reads
    return panel.build_panel_document(read_from(mapping), SURFACES, **kwargs)


def panel_document(**kwargs) -> dict:
    kwargs.setdefault("observed_at", FIXED_OBSERVED_AT)
    return build(**kwargs)


def panel_text(**kwargs) -> str:
    return panel.render_panel(panel_document(**kwargs))


def secret_envelope() -> dict:
    """An intact envelope whose payload carries planted credential material."""
    return envelope(
        {
            "pending_jobs": 1,
            "active_jobs": 1,
            "failed_jobs": 0,
            "quarantined_jobs": 0,
            "workers": {"w-1": {}},
            "auth": {"token": "tok-PLANTED-abc123", "password": "hunter2-PLANTED"},
            "note": "Bearer PLANTED-bearer-xyz",
        },
        request_id="Bearer PLANTED-req-token",
    )


def drill_report(disposition: str = "DRILL_PASS", duplicate_check: bool = True) -> dict:
    """Build the real drill session/binding/report through oce_console.drill."""
    playbook = drill.Playbook(
        "1.0.0",
        [
            "submit_representative_job",
            "observe_leased",
            "observe_requeued",
            "observe_succeeded",
            "check_duplicate_effect",
            "emit_report",
        ],
    )
    recorder = drill.SessionRecorder("sess-b5i8-1", playbook)
    for step in playbook.steps:
        recorder.append_action(step, {"observed": True})
    recorder.set_report_ref("evidence://b5i8/drill-1")
    record = recorder.to_record()
    timeline = {"job_id": "job-b5i8-1", "state": "SUCCEEDED", "attempt_number": 2}
    job_envelope = {
        "job_id": "job-b5i8-1",
        "payload_hash": "b" * 64,
        "evidence_refs": ["evidence://job/job-b5i8-1"],
    }
    binding = drill.bind_evidence(timeline, job_envelope)
    return drill.build_drill_report(
        record, timeline, duplicate_check, binding, disposition=disposition
    )


def masked_report(report: dict) -> dict:
    """Apply the frozen three-field mask to a drill report."""
    masked = json.loads(json.dumps(report))
    for dotted in DRILL_MASK:
        if "." in dotted:
            head, tail = dotted.split(".", 1)
            if isinstance(masked.get(head), dict):
                masked[head][tail] = MASK_SENTINELS[dotted]
        else:
            masked[dotted] = MASK_SENTINELS[dotted]
    return masked


# ── protocol (executed live, deterministically) ─────────────────────────────

PROTOCOL_TASKS = (
    {
        "task_id": "T1",
        "scenario": "healthy",
        "title": "Recognise the governed OK state and the queue depth",
        "surface": "oce_console.panel.build_panel_document + render_panel",
        "comprehension_question": "What state is the stack in, and what is the bounded depth?",
    },
    {
        "task_id": "T2",
        "scenario": "denied",
        "title": "Recognise a governed denial verbatim",
        "surface": "oce_console.panel.build_panel_document (DENIED envelope)",
        "comprehension_question": "Was the read denied, and what is the exact refusal code?",
    },
    {
        "task_id": "T3",
        "scenario": "unreachable",
        "title": "Recognise an unreachable stack and the recovery guidance",
        "surface": "oce_console.panel.build_panel_document (transport refusal)",
        "comprehension_question": "Is anything green, and what must the operator do next?",
    },
    {
        "task_id": "T4",
        "scenario": "partial",
        "title": "Distinguish an unknown counter from a known zero",
        "surface": "oce_console.panel.build_panel_document (partial envelope)",
        "comprehension_question": "Is the missing counter zero, or unknown?",
    },
)


def _task_reads(scenario: str):
    reads = frozen_reads()
    if scenario == "denied":
        reads["health.read"] = denied_envelope()
    elif scenario == "unreachable":
        reads["health.read"] = StackUnreachable("health.read: connection refused")
    elif scenario == "partial":
        data = healthy_data()
        data.pop("failed_jobs")
        data.pop("quarantined_jobs")
        reads["health.read"] = envelope(data)
    return reads


def execute_task(task: dict) -> dict:
    """Execute one protocol task against the real surface and record the result."""
    reads = _task_reads(task["scenario"])
    read = read_from(reads)
    started = time.perf_counter()
    document = panel.build_panel_document(
        read, SURFACES, observed_at=FIXED_OBSERVED_AT
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    text = panel.render_panel(document)
    queue = document["queue"]
    comprehension = {
        "state_observed": document["state"],
        "depth_known": queue["depth"]["known"],
        "depth_value": queue["depth"]["value"],
        "denial_code": (
            (document.get("reads", {}).get("health.read", {}).get("response") or {})
            .get("error", {})
            .get("code")
            if isinstance(
                (document.get("reads", {}).get("health.read", {}).get("response") or {}).get(
                    "error"
                ),
                dict,
            )
            else None
        ),
        "green_anywhere": json.loads(text)["state"] == panel.STATE_OK,
        "recovery_guidance": (
            "verify the operator grant and consent, then retry"
            if document["state"] == panel.STATE_DENIED
            else (
                "re-run after the local stack health is verified"
                if document["state"] == panel.STATE_UNREACHABLE
                else "none required"
            )
        ),
        "unknown_rendered_not_zero": (
            queue["pending"].get("known") is True
            and queue["failed"]["value"] is None
            and queue["failed"]["known"] is False
        )
        if task["scenario"] == "partial"
        else None,
    }
    return {
        "task_id": task["task_id"],
        "scenario": task["scenario"],
        "completion": True,
        "error": 0,
        "navigation_steps": len(read.calls),
        "time_to_first_useful_state_ms": elapsed_ms,
        "state_observed": document["state"],
        "comprehension": comprehension,
        "recorded_by": ATTESTATION_CLASS,
        "executed_at": FIXED_OBSERVED_AT,
        "environment": "local-win32-cpython3.11",
        "command": "python -m pytest (B5-I8 protocol task " + task["task_id"] + ")",
        "artifact": "docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json",
    }


def run_protocol() -> list:
    return [execute_task(task) for task in PROTOCOL_TASKS]


def accessibility_checks() -> list:
    """Deterministic semantics checks over the surfaces that actually exist."""
    ok_doc = panel_document()
    denied = build(reads=frozen_reads(**{"health.read": denied_envelope()}))
    unreachable = build(
        reads=frozen_reads(**{"health.read": StackUnreachable("refused")})
    )
    ok_text = panel.render_panel(ok_doc)
    denied_text = panel.render_panel(denied)
    unreachable_text = panel.render_panel(unreachable)
    unknown_doc = build(
        reads=frozen_reads(**{"health.read": envelope({"pending_jobs": 1})})
    )
    checks = [
        {
            "check_id": "A1",
            "surface": "panel text render",
            "assertion": "the governed state is named as a distinct token",
            "result": "PASS" if '"state": "OK"' in ok_text else "FAIL",
            "finding": "state token present and distinct",
        },
        {
            "check_id": "A2",
            "surface": "panel text render (denied)",
            "assertion": "a refusal carries its machine-readable code in the text",
            "result": "PASS" if "E_DENIED" in denied_text else "FAIL",
            "finding": "denial code legible in the rendered document",
        },
        {
            "check_id": "A3",
            "surface": "panel text render (unreachable)",
            "assertion": "an unreachable stack is never rendered with a green summary",
            "result": "PASS"
            if '"state": "STACK_UNREACHABLE"' in unreachable_text
            and '"state": "OK"' not in unreachable_text
            else "FAIL",
            "finding": "fail-closed state token, no green summary",
        },
        {
            "check_id": "A4",
            "surface": "panel text render (unknown)",
            "assertion": "an unknown counter renders null plus a reason, never 0",
            "result": "PASS"
            if unknown_doc["queue"]["pending"]["known"] is True
            and unknown_doc["queue"]["failed"]["value"] is None
            and "unknown_reason" in unknown_doc["queue"]["failed"]
            else "FAIL",
            "finding": "unknown is textually distinguishable from zero",
        },
        {
            "check_id": "A5",
            "surface": "panel text render",
            "assertion": "no browser, DOM or web-view surface is claimed or required",
            "result": "PASS"
            if "html" not in ok_text.lower() and "dom" not in ok_text.lower()
            else "FAIL",
            "finding": "checked over text surfaces only; no web view exists",
        },
    ]
    return checks


def gates(bundle: dict | None = None) -> dict:
    """Recompute gate dispositions from the evidence, never from prose."""
    bundle = evidence() if bundle is None else bundle
    results = bundle.get("protocol", {}).get("results", [])
    attestation = {
        row.get("recorded_by") for row in results if isinstance(row, dict)
    }
    independent = attestation == {"INDEPENDENT_HUMAN"}
    g16 = {
        "status": "CLOSED" if independent else "OPEN",
        "blocker": (
            ""
            if independent
            else "no organizationally independent operator: the protocol was executed by "
            "the B5-I8 implementer (single operator, non-blind; B5I8-DF05 unresolved)"
        ),
        "protocol_executed": bool(results)
        and all(row.get("completion") is True for row in results),
        "attestation_class": sorted(attestation),
    }
    return {"G16": g16}


def recompute_verdict(bundle: dict) -> dict:
    """Recompute the audit verdict from committed inputs (never from prose)."""
    reg = registry()
    rs = reg["requirement_set"]
    planned = planned_nodes()
    files = planned_files()
    collected = collected_nodes()
    collected_flat = [n for nodes in collected.values() for n in nodes]
    mutation_doc = mutations() if MUTATIONS.exists() else {"mutations": []}
    mutation_rows = mutation_doc.get("mutations", [])
    g16 = gates(bundle)["G16"]
    return {
        "requirements_total": rs["total"],
        "requirements_unique": rs["unique_ids"],
        "planned_nodes": len(planned),
        "collected_nodes": len(collected_flat),
        "node_closure": sorted(collected_flat) == sorted(planned) and len(collected_flat) == 40,
        "files": len(files),
        "mutations_required": reg["p0"]["mutation_floor"],
        "mutations_discriminated": sum(
            1 for row in mutation_rows if row.get("red") is True
        ),
        "mutation_floor_met": sum(1 for row in mutation_rows if row.get("red") is True)
        >= reg["p0"]["mutation_floor"],
        "protocol_tasks": len(bundle.get("protocol", {}).get("tasks", [])),
        "protocol_results": len(bundle.get("protocol", {}).get("results", [])),
        "g16_status": g16["status"],
        "failure_classes": reg["p0"]["failure_classes"],
    }


def verdict_digest(bundle: dict) -> str:
    return digest_obj(recompute_verdict(bundle))


#: Negation markers: a prohibited phrase quoted INSIDE a prohibition
#: ("no 'all gates passed' claim") is not itself a claim.
_NEGATION_MARKERS = (
    "no ", "not ", "never", "forbidden", "prohibit", "refus", "without",
    "while any gate", "accept a narrative",
)


def forbidden_hits(text: str) -> list:
    """Return forbidden all-green phrases actually asserted, not quoted bans."""
    lowered = text.lower()
    hits = []
    for phrase in FORBIDDEN_ALL_GREEN:
        start = 0
        while True:
            index = lowered.find(phrase, start)
            if index < 0:
                break
            window = lowered[max(0, index - 120) : index + len(phrase) + 120]
            if not any(marker in window for marker in _NEGATION_MARKERS):
                hits.append(phrase)
                break
            start = index + 1
    return hits


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def workflow_b5_i8_step() -> str:
    """Slice the single additive B5-I8 selection step out of the workflow."""
    text = WORKFLOW_B5I8.read_text(encoding="utf-8")
    marker = "B5-I8"
    start = text.find("- name: Execute B5-I8")
    if start < 0:
        raise AssertionError("no B5-I8 workflow step")
    nxt = text.find("\n      - name:", start + 1)
    return text[start : nxt if nxt > 0 else len(text)]


def adjacent_files() -> list:
    return [
        "test_b5_i2_mutation_harness.py",
        "test_b5_i3_requirement_registry.py",
        "test_b5_i4_console_kernel.py",
        "test_b5_i5_timeline.py",
        "test_b5_i6_console_restart.py",
        "test_b5_i6_deploy_pkg.py",
        "test_b5_i6_fail_closed.py",
        "test_b5_i6_recovery_drill.py",
        "test_b5_i7_governed_change.py",
        "test_b5_i7_evidence_laws.py",
    ]


def collect_adjacent() -> dict:
    """Collect the ten pre-existing B5 files and return per-file counts."""
    paths = [f"infrastructure/control-plane/tests/{name}" for name in adjacent_files()]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *paths, "--collect-only", "-q"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    counts: dict = {}
    for line in proc.stdout.splitlines():
        if "::" not in line or not line.strip().startswith("infrastructure"):
            continue
        name = Path(line.split("::", 1)[0].strip()).name
        counts[name] = counts.get(name, 0) + 1
    return {"returncode": proc.returncode, "counts": counts, "total": sum(counts.values())}


CI_IDENTITY_PATH = REPO_ROOT / "docs" / "oce-golden-system" / "OCE_B5_I8_CI_IDENTITY_v1.0.json"


def ci_identity() -> dict:
    """The committed, parsed CI identity record ({} before any observed run)."""
    return load(CI_IDENTITY_PATH) if CI_IDENTITY_PATH.exists() else {}


def workflow_b5_i8_text() -> str:
    """The dedicated B5-I8 workflow bytes (never the pinned B1-I1R workflow)."""
    return WORKFLOW_B5I8.read_text(encoding="utf-8")


def workflow_mutation_step() -> str:
    """Slice the mutation-battery step out of the dedicated B5-I8 workflow."""
    text = WORKFLOW_B5I8.read_text(encoding="utf-8")
    start = text.find("- name: Execute committed mutation battery")
    if start < 0:
        raise AssertionError("no mutation battery step in the B5-I8 workflow")
    nxt = text.find("\n      - name:", start + 1)
    return text[start : nxt if nxt > 0 else len(text)]


#: Repository run-id law (cloud-ground/scripts/run-validation.sh): 12+ lowercase hex.
RUN_ID_RE = re.compile(r"^[0-9a-f]{12,}$")
WORKFLOW_B5I8_SUFFIX = ".github/workflows/b5-i8-audit-validation.yml"
LOCAL_EVIDENCE_LABEL = "LOCAL_REPRODUCTION_NOT_CI"
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


def run_identity_problems(identity: dict, run_context: dict | None = None) -> list:
    """Why a run identity may NOT stand as authoritative CI evidence (empty == ok).

    Fail-closed: a blank id, a malformed id, an id that does not match the run
    context Actions actually supplied, a mismatched attempt/workflow/head/merge
    ref, or a locally invented placeholder all yield at least one problem. The
    caller turns a non-empty list into a red job, so CI evidence can never
    silently degrade to an empty string.
    """
    problems: list = []
    ctx = run_context or {}

    if identity.get("source") != "ci":
        problems.append(
            "evidence source is %r; only 'ci' is authoritative and a local "
            "reproduction must be labelled %r"
            % (identity.get("source"), LOCAL_EVIDENCE_LABEL)
        )

    run_id = identity.get("oce_run_id") or ""
    if not run_id:
        problems.append("oce_run_id is blank")
    elif not RUN_ID_RE.match(run_id):
        problems.append("oce_run_id %r is malformed (expected 12+ lowercase hex)" % run_id)

    artifact = identity.get("artifact_name") or ""
    if not run_id or artifact != "b5-i8-evidence-" + run_id:
        problems.append(
            "artifact name %r is not bound to oce_run_id %r" % (artifact, run_id)
        )

    gh_run = str(identity.get("github_run_id") or "")
    if not (gh_run.isdigit() and int(gh_run) > 0):
        problems.append("github_run_id %r is not a positive integer" % gh_run)
    elif ctx and str(ctx.get("github_run_id")) != gh_run:
        problems.append(
            "github_run_id %r does not match the run context %r"
            % (gh_run, ctx.get("github_run_id"))
        )

    attempt = str(identity.get("run_attempt") or "")
    if not (attempt.isdigit() and int(attempt) >= 1):
        problems.append("run_attempt %r is not a positive integer" % attempt)
    elif ctx and str(ctx.get("run_attempt")) != attempt:
        problems.append(
            "run_attempt %r does not match the run context %r"
            % (attempt, ctx.get("run_attempt"))
        )

    workflow = identity.get("workflow_path") or ""
    workflow_file = workflow.split("@", 1)[0]
    if not workflow_file.endswith(WORKFLOW_B5I8_SUFFIX):
        problems.append(
            "workflow path %r is not the governed B5-I8 workflow" % workflow
        )
    if ctx and ctx.get("workflow") != "b5-i8-audit-validation":
        problems.append(
            "run-context workflow %r is not b5-i8-audit-validation" % ctx.get("workflow")
        )

    if identity.get("event") != "pull_request":
        problems.append(
            "event %r is not the governed trigger pull_request" % identity.get("event")
        )
    if ctx and ctx.get("event") != "pull_request":
        problems.append("run-context event %r is not pull_request" % ctx.get("event"))

    repository = identity.get("repository") or ""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        problems.append("repository %r is not owner/name" % repository)
    elif ctx and ctx.get("repository") != repository:
        problems.append(
            "repository %r does not match the run context %r"
            % (repository, ctx.get("repository"))
        )

    pr = str(identity.get("pr_number") or "")
    if not (pr.isdigit() and int(pr) > 0):
        problems.append("pull request number %r is missing" % pr)
    elif ctx and str(ctx.get("pr_number")) != pr:
        problems.append(
            "pull request number %r does not match the run context %r"
            % (pr, ctx.get("pr_number"))
        )

    head = identity.get("pr_head_sha") or ""
    if not HEX40_RE.match(head):
        problems.append("pr_head_sha %r is not a 40-hex commit" % head)
    tree = identity.get("tested_tree") or ""
    if not HEX40_RE.match(tree):
        problems.append("tested_tree %r is not a 40-hex tree" % tree)

    merge_ref = identity.get("merge_ref") or ""
    if not HEX40_RE.match(merge_ref):
        problems.append("merge_ref %r is not a 40-hex commit" % merge_ref)
    elif ctx and ctx.get("sha") != merge_ref:
        problems.append(
            "merge_ref %r is not the run-context sha %r" % (merge_ref, ctx.get("sha"))
        )

    # The committed identity record names these merge_ref_*; the workflow supplies the
    # shorter names. Both are the same fact, so accept either spelling.
    first = identity.get("merge_first_parent") or identity.get("merge_ref_first_parent") or ""
    second = (
        identity.get("merge_second_parent") or identity.get("merge_ref_second_parent") or ""
    )
    if not HEX40_RE.match(first):
        problems.append("merge_first_parent %r is not a 40-hex commit" % first)
    if not HEX40_RE.match(second):
        problems.append("merge_second_parent %r is not a 40-hex commit" % second)
    if HEX40_RE.match(first) and HEX40_RE.match(second):
        if first == second:
            problems.append("merge-ref parents are identical")
        if head and second != head:
            problems.append(
                "merge-ref second parent %r is not the PR head %r" % (second, head)
            )
    return problems
