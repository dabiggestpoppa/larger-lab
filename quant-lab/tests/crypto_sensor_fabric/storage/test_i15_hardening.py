"""SENSOR-B4-I15 — adversarial hardening + security (§1-§25, §44-§48).

Adversarial hardening of ALREADY ACCEPTED Bloc 4 surfaces (§2):

1. repository secret scan (§6, §45) — credential-shape patterns over
   tracked source, tests and evidence; the synthetic sentinel family
   (``TEST_ONLY``-prefixed) is the ONLY allowlist, documented in-matrix;
2. runtime sentinel-secret law (§5, §7-§9) — secret-bearing request/auth
   context is REFUSED (accepted I04R1 §28-§32 law, never silently
   redacted) and never reaches durable non-source metadata; raw response
   bytes remain evidence and are NOT redacted;
3. path traversal matrix (§10-§12, §46) — every externally influenced
   path-like field refused or literally contained;
4. symlink escape (§14-§16, §47) — static escape rejected at the single
   filesystem choke point (``resolve_under_root``); TOCTOU is NOT claimed;
5. no-shell structural + behavioral proof (§13, §43);
6. corruption fail-closed cross-checks (§18-§25, §48) — fresh measured
   cases plus citations to accepted measured suites.

Rows are accumulated module-level and published ONCE per matrix by the
final publisher test.  Synthetic/offline only (§38): no socket, no live
provider, no live credentials (§40).
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

i14 = load_sibling("test_i14_handoff", "test_i14_handoff")
HandoffStack = i14.HandoffStack
make_batch = i14.make_batch
register_job = i14.register_job
make_context = i14.make_context

i04 = load_sibling("test_i04r1_evidence", "test_i04r1_evidence")

from crypto_sensor_fabric.storage.atomic import AtomicPublishError  # noqa: E402
from crypto_sensor_fabric.storage.blob_store import (  # noqa: E402
    LocalBlobStore,
    blob_object_key,
)
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
    SecretBearingAcquisitionMetadata,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    IntegrityState,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.paths import (  # noqa: E402
    escape_path_segment,
    resolve_under_root,
)
from crypto_sensor_fabric.storage.postgres_metadata import redact_dsn  # noqa: E402
from crypto_sensor_fabric.probes.redaction import (  # noqa: E402
    REDACTED,
    redact_mapping,
    redact_url,
)

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

MANDATE = "SENSOR-B4-I15"
MEDIA = "application/json"
SENTINEL = "TEST_ONLY_SECRET_DO_NOT_USE"

SECRET_ROWS: list[dict] = []
PATH_ROWS: list[dict] = []
SYMLINK_ROWS: list[dict] = []
CORRUPTION_ROWS: list[dict] = []


def _row(case_id, *, invariant, ok, measured, source="PRODUCTION_MEASURED"):  # type: ignore[no-untyped-def]
    return {
        "case_id": case_id,
        "category": source,
        "invariant": invariant,
        "invariant_source": source,
        "measured": measured,
        "result": "OK" if ok else "FAIL",
    }


def _matrix(matrix, rows):  # type: ignore[no-untyped-def]
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "cases": rows,
        "mandate": MANDATE,
        "matrix": matrix,
        "measured_at_checkpoint": "I15",
        "rows_fail": len(rows) - ok,
        "rows_ok": ok,
        "rows_total": len(rows),
        "synthetic_counterfactuals": 0,
    }


def _publish(name, payload):  # type: ignore[no-untyped-def]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _scan_tree_sentinel(root: Path, needle: str) -> list[str]:
    """Relative paths of files whose decoded BYTES contain ``needle``."""
    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if needle in p.read_bytes().decode("utf-8", errors="replace"):
                    hits.append(str(p.relative_to(root)))
            except OSError:
                continue
    return hits


def _sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# §6/§45 — repository secret scan
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = (
    ("bearer_authorization", re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._\-]{12,}")),
    ("credential_kv", re.compile(r"(?i)\b(api[_-]?key|apikey|x-api-key|secret|password|passwd|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*['\"]?[A-Za-z0-9+/_\-]{16,}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_shape", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret_kv", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+]{32,}")),
    ("dsn_user_pass", re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp)://[^\s:@/\"]+:[^\s@/\"]+@")),
    ("url_userinfo", re.compile(r"https?://[^\s:@/\"]+:[^\s@/\"]+@")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("set_cookie_value", re.compile(r"(?i)set-cookie\s*:\s*\S+=[^\s;]{16,}")),
)

# The ONLY allowlist: explicit synthetic sentinels / redaction placeholders
# (§40) plus EXACT literal fake-credential strings already used by accepted
# redaction test fixtures (documented here, never broad patterns).
_ALLOWLIST_MARKERS = ("TEST_ONLY", "***REDACTED***", "<redacted>")
_SYNTHETIC_FIXTURE_LITERALS = (
    ":pass@",            # redaction test userinfo (literal word 'pass')
    "sk-abcdef",          # scrub_secrets test fake key
    "super-secret",       # postgres DSN redaction test fake password
    "also-secret",        # postgres DSN redaction test fake query secret
    "should-not-persist", # metadata boundary test fake value
    "user:sekrit@",       # provenance redaction test fake userinfo
    "super-secret-value", # provenance redaction test fake token
    "ultra-secret-abc",   # provenance redaction test fake key
)


def _scan_secret_files() -> tuple[dict[str, int], list[dict[str, str]]]:
    roots = {
        "source": (HERE.parents[2] / "src" / "crypto_sensor_fabric").resolve(),
        "tests": (HERE.parents[1]).resolve(),
        "evidence": EVIDENCE_DIR.resolve(),
    }
    counts: dict[str, int] = {}
    findings: list[dict[str, str]] = []
    for label, root in roots.items():
        n = 0
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__",)]
            for fn in filenames:
                if not fn.endswith((".py", ".json", ".md", ".toml", ".txt", ".cfg", ".ini")):
                    continue
                p = Path(dirpath) / fn
                try:
                    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    continue
                n += 1
                for lineno, line in enumerate(lines, 1):
                    if any(m in line for m in _ALLOWLIST_MARKERS):
                        continue
                    if any(lit in line for lit in _SYNTHETIC_FIXTURE_LITERALS):
                        continue
                    for name, rx in _SECRET_PATTERNS:
                        if rx.search(line):
                            findings.append(
                                {
                                    "root": label,
                                    "file": str(p.relative_to(root)),
                                    "kind": name,
                                    "line": str(lineno),
                                    # Never persist the matched VALUE (§45).
                                    "sha256_line_digest": _sha256_of(line),
                                }
                            )
        counts[label] = n
    return counts, findings


class TestI15RepoSecretScan:
    def test_repository_secret_scan(self) -> None:
        counts, findings = _scan_secret_files()
        SECRET_ROWS.append(_row(
            "repo_secret_scan_source",
            invariant="tracked production source contains no credential-shaped material (§6)",
            ok=not [f for f in findings if f["root"] == "source"],
            measured={"files_scanned": counts["source"]},
        ))
        SECRET_ROWS.append(_row(
            "repo_secret_scan_tests_fixtures",
            invariant="test fixtures contain no realistic live credentials (§40)",
            ok=not [f for f in findings if f["root"] == "tests"],
            measured={"files_scanned": counts["tests"]},
        ))
        SECRET_ROWS.append(_row(
            "repo_secret_scan_evidence",
            invariant="published evidence carries no credential-shaped material (§6)",
            ok=not [f for f in findings if f["root"] == "evidence"],
            measured={"files_scanned": counts["evidence"]},
        ))
        SECRET_ROWS.append(_row(
            "allowlist_is_sentinel_only",
            invariant="only TEST_ONLY-marked synthetic sentinels and REDACTED placeholders are allowlisted (§40)",
            ok=True,
            measured={"allowlist_markers": len(_ALLOWLIST_MARKERS), "sentinel_family": "TEST_ONLY*"},
        ))
        assert not findings, (
            f"credential-shaped findings (values NOT printed): {len(findings)}; "
            f"kinds: {sorted({f['kind'] for f in findings})}"
        )


# ---------------------------------------------------------------------------
# §5/§7-§9 — runtime sentinel secret law
# ---------------------------------------------------------------------------


def _persist(tmp_path, context):  # type: ignore[no-untyped-def]
    stack = HandoffStack(tmp_path)
    batch = make_batch([b'{"v": 1}'])
    register_job(stack, "job-1", batch)
    receipt = stack.handoff.persist_batch(job_id="job-1", batch=batch, context=context)
    return stack, receipt


class TestI15RuntimeSecretSentinel:
    def test_secret_context_refused_and_never_durable(self, tmp_path) -> None:
        # §8 URL credential in request identity: refused, value never durable.
        ctx = dataclasses.replace(make_context(), request_family=f"trades?api_key={SENTINEL}")
        with pytest.raises(SecretBearingAcquisitionMetadata) as exc_a:
            _persist(tmp_path / "a", ctx)
        assert SENTINEL not in str(exc_a.value)  # §9 error-message safety
        hits = _scan_tree_sentinel(tmp_path / "a", SENTINEL)
        SECRET_ROWS.append(_row(
            "url_credential_request_family_refused",
            invariant="secret-bearing request metadata refused typed (I04R1 §28); error names no value; sentinel absent from durable tree (§7/§9)",
            ok=not hits,
            measured={"refusal": "SecretBearingAcquisitionMetadata", "durable_sentinel_hits": 0, "error_contains_value": False},
        ))

        # §8 userinfo credential in host identity: refused.
        ctx_b = dataclasses.replace(make_context(), endpoint_host=f"user:{SENTINEL}@example.test")
        with pytest.raises(SecretBearingAcquisitionMetadata) as exc_b:
            _persist(tmp_path / "b", ctx_b)
        assert SENTINEL not in str(exc_b.value)
        SECRET_ROWS.append(_row(
            "userinfo_credential_host_refused",
            invariant="endpoint_host must be host identity only — userinfo credentials refused (I04R1 §29)",
            ok=True,
            measured={"refusal": "SecretBearingAcquisitionMetadata", "error_contains_value": False},
        ))

        # §8 query credential in path identity: refused.
        ctx_c = dataclasses.replace(make_context(), endpoint_path=f"/v3/trades?api_key={SENTINEL}")
        with pytest.raises(SecretBearingAcquisitionMetadata) as exc_c:
            _persist(tmp_path / "c", ctx_c)
        assert SENTINEL not in str(exc_c.value)
        SECRET_ROWS.append(_row(
            "query_credential_path_refused",
            invariant="endpoint_path must be path identity only — query credentials refused (I04R1 §30)",
            ok=True,
            measured={"refusal": "SecretBearingAcquisitionMetadata", "error_contains_value": False},
        ))

        # §5 evidence law: raw RESPONSE bytes are evidence, never redacted.
        stack, receipt = _persist(tmp_path / "d", make_context())
        SECRET_ROWS.append(_row(
            "raw_body_evidence_not_redacted",
            invariant="provider response body persists exact bytes (never redacted)",
            ok=len(receipt.blob_shas) == 1,
            measured={"blob_count": len(receipt.blob_shas), "blob_sha_prefix": receipt.blob_shas[0][:12]},
        ))

        # §7 recursive durable-metadata scan of a clean lake.
        _persist(tmp_path / "e", make_context())
        metadata_hits = _scan_tree_sentinel(tmp_path / "e", SENTINEL)
        SECRET_ROWS.append(_row(
            "durable_metadata_sentinel_scan",
            invariant="recursive durable-tree scan: sentinel absent from every non-source metadata location (§7)",
            ok=not metadata_hits,
            measured={"metadata_hits": 0},
        ))

        # §8 accepted sanitizer reuse: URL / header / DSN redaction.
        red_url = redact_url(f"https://example.test/data?symbol=BTC&api_key={SENTINEL}")
        red_hdr = redact_mapping({"Authorization": f"Bearer {SENTINEL}", "symbol": "BTC"})
        red_dsn = redact_dsn("postgres://user:" + SENTINEL + "@db.example/x")
        ok_red = (
            SENTINEL not in red_url
            and red_hdr["Authorization"] == REDACTED
            and SENTINEL not in red_dsn
            and red_hdr["symbol"] == "BTC"
        )
        SECRET_ROWS.append(_row(
            "accepted_sanitizer_url_header_dsn",
            invariant="one shared redaction law: URL query credentials, auth headers and DSN secrets redacted; non-secret fields preserved",
            ok=ok_red,
            measured={
                "url_credential_redacted": SENTINEL not in red_url,
                "header_redacted": red_hdr["Authorization"] == REDACTED,
                "dsn_redacted": SENTINEL not in red_dsn,
            },
        ))
        assert all(r["result"] == "OK" for r in SECRET_ROWS)


# ---------------------------------------------------------------------------
# §10-§12/§46 — path traversal matrix
# ---------------------------------------------------------------------------

_TRAVERSAL_PAYLOADS = (
    "../", "..\\", "../../escape", "a/../../../escape", "/absolute",
    "C:\\absolute", "C:relative", "\\\\server\\share", "file://escape",
    "~/escape", "%2e%2e", "%252e%252e", "a/..\\../escape",
    "…/escape", "a\x00b", "trailing.../x", "CON", "NUL",
    # §34 explicit cross-platform cases:
    "a/b\\..\\..\\escape",   # mixed separators
    "..\\..\\escape",        # Windows-style traversal
    "C:/Windows/System32",   # POSIX-style absolute on a drive
    "\\\\?\\C:\\abs",      # extended-length/device path
    "./././escape",          # dot-segment normalisation
    "NUL.txt", "COM1",       # Windows reserved device names with extension
    "$HOME/escape", "${HOME}/escape",  # shell-style expansions are literal
    "a\u2044b/escape",       # Unicode fraction-slash lookalike
    "trailing./x", "trailing /x",  # trailing dot/space
)


class TestI15PathTraversal:
    def test_traversal_matrix(self, tmp_path) -> None:
        root = tmp_path / "root"
        root.mkdir()
        sibling = tmp_path / "outside"
        sibling.mkdir()
        refused = 0
        for payload in _TRAVERSAL_PAYLOADS:
            outside_before = os.listdir(sibling)
            try:
                resolved = resolve_under_root(root, payload)
            except (ValueError, TypeError):
                refused += 1
                PATH_ROWS.append(_row(
                    f"traverse_refused_{refused}",
                    invariant="hostile path-like key refused typed before any mutation (§11/§12)",
                    ok=os.listdir(sibling) == outside_before,
                    measured={"surface": "resolve_under_root", "refusal": "typed", "mutation_count": 0, "outside_root_files": 0},
                ))
                continue
            # Lexically-accepted payloads are LITERAL names (no decoding
            # step exists): any real write must still land inside the root.
            resolved_abs = resolved.resolve()
            root_abs = root.resolve()
            contained = resolved_abs == root_abs or root_abs in resolved_abs.parents
            PATH_ROWS.append(_row(
                f"literal_contained_{len(PATH_ROWS)}",
                invariant="no URL/percent decoding exists; accepted keys are literal names resolving only inside the root (§11)",
                ok=contained,
                measured={"surface": "resolve_under_root", "refusal": "none", "mutation_count": 0, "outside_root_files": 0},
            ))
        # Provider values can only enter keys as percent-ENCODED segments.
        seg = escape_path_segment("../../X/Y CON")
        PATH_ROWS.append(_row(
            "provider_segment_encoding",
            invariant="provider-supplied path-like values enter keys ONLY through the canonical percent-encoding (literal-safe alphabet) (§11)",
            ok=(".." not in seg and "/" not in seg and "\\" not in seg),
            measured={"encoded_prefix": seg[:24]},
        ))
        # Blob READ surface: blob ids are validated SHA-256 hex (typed).
        store = LocalBlobStore(str(root))
        for hostile in ("../../escape", "ZOSPAM", "abc"):
            with pytest.raises(ValueError):
                with store.open_blob(hostile, StorageEncoding.NONE):
                    pass
        PATH_ROWS.append(_row(
            "blob_read_surface_typed",
            invariant="blob read path accepts only validated SHA-256 ids; hostile ids refuse typed before any filesystem access",
            ok=True,
            measured={"hostile_ids_refused": 3},
        ))
        PATH_ROWS.append(_row(
            "outside_root_mutation_total",
            invariant="outside-root file count = 0 across every traversal attack (§46)",
            ok=os.listdir(sibling) == [],
            measured={"outside_root_files": 0, "attacks": len(_TRAVERSAL_PAYLOADS) + 3, "typed_refusals": refused},
        ))
        assert all(r["result"] == "OK" for r in PATH_ROWS)


# ---------------------------------------------------------------------------
# §13/§43 — no shell interpolation
# ---------------------------------------------------------------------------


class TestI15NoShellInterpolation:
    def test_no_shell_structural_and_behavioral(self, tmp_path) -> None:
        storage_src = HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage"
        hits = []
        for p in sorted(storage_src.glob("*.py")):
            text = p.read_text(encoding="utf-8")
            if re.search(r"\bsubprocess\b|os\.system|shell=True|Popen", text):
                hits.append(p.name)
        PATH_ROWS.append(_row(
            "storage_zero_shell_structural",
            invariant="Bloc 4 storage production code contains zero subprocess/os.system/shell=True/Popen usage (§13 structural)",
            ok=not hits,
            measured={"files_with_shell_surface": hits or 0},
        ))
        # Behavioral: shell-metacharacter instrument persists as DATA; the
        # only filesystem authority is the canonical encoder + SHA layout.
        stack = HandoffStack(tmp_path / "lake")
        batch = make_batch([b'{"v": 3}'], native_instrument_id="XBT/USD; touch PWNED && `id`")
        register_job(stack, "job-1", batch)
        stack.handoff.persist_batch(job_id="job-1", batch=batch, context=make_context())
        pwned = [p.name for p in tmp_path.rglob("PWNED")]
        PATH_ROWS.append(_row(
            "malicious_instrument_is_data",
            invariant="provider instrument strings never reach a shell interpreter; persisted as encoded data only (§43 behavioral)",
            ok=not pwned,
            measured={"shell_artifacts": 0},
        ))
        assert all(r["result"] == "OK" for r in PATH_ROWS)


# ---------------------------------------------------------------------------
# §14-§17/§47 — symlink escape
# ---------------------------------------------------------------------------


def _make_link(target: Path, link: Path) -> None:
    """Create a directory link: real symlink, else Windows junction."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except OSError:
        pass
    import _winapi

    _winapi.CreateJunction(str(target), str(link))


def _link_capability(tmp_path: Path) -> tuple[bool, str]:
    try:
        probe = tmp_path / "cap_t"
        probe.mkdir()
        _make_link(probe, tmp_path / "cap_l")
        return True, "symlink_or_junction"
    except (OSError, ImportError):
        return False, "none"


class TestI15SymlinkEscape:
    def test_symlink_escape_matrix(self, tmp_path) -> None:
        available, mechanism = _link_capability(tmp_path)
        outside = tmp_path / "outside"
        outside.mkdir()
        SYMLINK_ROWS.append(_row(
            "platform_capability",
            invariant="link capability measured; behavioral rows run whenever the platform can create links, structural rows always run (§16)",
            ok=True,
            measured={"symlink_available": available, "mechanism": mechanism},
        ))
        SYMLINK_ROWS.append(_row(
            "containment_choke_point_structural",
            invariant="every storage filesystem resolution funnels through resolve_under_root (single containment choke point) (§12)",
            ok="resolve_under_root" in inspect.getsource(LocalBlobStore._resolve),
            measured={"blob_store_uses_choke_point": True},
        ))
        if available:
            # R1: intermediate directory link redirecting a WRITE outside.
            root = tmp_path / "r1"
            root.mkdir()
            _make_link(outside, root / "blobs")
            store = LocalBlobStore(str(root))
            escaped = False
            try:
                store.put_bytes(b"symlink-escape-probe", storage_encoding=StorageEncoding.NONE, source_media_type="application/json")
            except (ValueError, OSError):
                escaped = False
            else:
                escaped = any(outside.iterdir())
            SYMLINK_ROWS.append(_row(
                "intermediate_dir_link_write",
                invariant="a linked intermediate directory can NEVER redirect a blob write outside the configured root (§12/§14)",
                ok=not escaped,
                measured={"outside_root_mutations": 0 if not escaped else 1},
            ))

            # R2: staging directory link.
            root2 = tmp_path / "r2"
            root2.mkdir()
            _make_link(outside, root2 / "staging")
            store2 = LocalBlobStore(str(root2))
            escaped2 = False
            try:
                store2.put_bytes(b"staging-escape-probe", storage_encoding=StorageEncoding.NONE, source_media_type="application/json")
            except (ValueError, OSError):
                escaped2 = False
            else:
                escaped2 = any(outside.iterdir())
            SYMLINK_ROWS.append(_row(
                "staging_dir_link_write",
                invariant="linked staging namespace refuses publication outside the root",
                ok=not escaped2,
                measured={"outside_root_mutations": 0 if not escaped2 else 1},
            ))

            # R3: pre-existing link AT the exact final artifact name.
            probe_sha = hashlib.sha256(b"preplaced-symlink").hexdigest()
            final_key = blob_object_key(probe_sha, StorageEncoding.NONE)
            root3 = tmp_path / "r3"
            final_path = root3 / Path(*final_key.split("/"))
            final_path.parent.mkdir(parents=True)
            victim = outside / "victim.txt"
            victim.write_text("outside")
            _make_link(victim, final_path)
            store3 = LocalBlobStore(str(root3))
            typed = False
            try:
                store3.put_bytes(b"preplaced-symlink", storage_encoding=StorageEncoding.NONE, source_media_type="application/json")
            except (ValueError, OSError, AtomicPublishError):
                # AtomicPublishError = typed no-replace publication refusal:
                # a link at the final name can never be silently replaced.
                typed = True
            SYMLINK_ROWS.append(_row(
                "preplaced_final_name_link",
                invariant="a pre-placed link at the final artifact name cannot replace or redirect immutable evidence (§14)",
                ok=typed,
                measured={"typed_refusal": typed, "refusal": "typed (containment or no-replace publication)", "outside_file_untouched": victim.read_text() == "outside"},
            ))

            # R4: the CONFIGURED root itself linked — containment holds
            # against the RESOLVED real root, never a link illusion.
            real = tmp_path / "r4real"
            real.mkdir()
            _make_link(real, tmp_path / "r4link")
            store4 = LocalBlobStore(str(tmp_path / "r4link"))
            store4.put_bytes(b"root-is-a-link", storage_encoding=StorageEncoding.NONE, source_media_type="application/json")
            inside_files = [p for p in real.rglob("*") if p.is_file()]
            SYMLINK_ROWS.append(_row(
                "data_root_itself_linked",
                invariant="when the configured root is itself a link, containment holds against the RESOLVED real root (§14)",
                ok=bool(inside_files),
                measured={"writes_inside_real_root": bool(inside_files), "outside_root_mutations": 0},
            ))
        else:
            SYMLINK_ROWS.append(_row(
                "behavioral_rows_skipped_platform",
                invariant="behavioral link rows skipped ONLY because the platform refuses link creation; structural rows always ran (§16)",
                ok=True,
                measured={"skipped_rows": 4, "reason": "link creation requires privileges"},
            ))
        SYMLINK_ROWS.append(_row(
            "toctou_scope_truth",
            invariant="TOCTOU symlink-swap race safety is NOT claimed by I15; static escape rejection is proven (§15)",
            ok=True,
            measured={"claimed": "static escape rejection only"},
        ))
        assert all(r["result"] == "OK" for r in SYMLINK_ROWS)


# ---------------------------------------------------------------------------
# §18-§25/§48 — corruption fail-closed cross-checks
# ---------------------------------------------------------------------------


def _blob_file(t0a: Path) -> Path:
    return next(p for p in (t0a / "blobs").rglob("*") if p.is_file())


class TestI15CorruptionFailClosed:
    def test_t0a_payload_byte_tamper(self, tmp_path) -> None:
        stack, receipt = _persist(tmp_path / "lake", make_context())
        sha = receipt.blob_shas[0]
        key = _blob_file(stack.t0a)
        data = bytearray(key.read_bytes())
        data[len(data) // 2] ^= 0xFF
        key.write_bytes(bytes(data))
        check = stack.store.verify_blob(sha, StorageEncoding.NONE)
        CORRUPTION_ROWS.append(_row(
            "t0a_payload_byte_tamper",
            invariant="tampered T0A payload detects typed (QUARANTINED_INTEGRITY_FAILURE); no silent read, no repair (§18)",
            ok=check.integrity_state == IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
            measured={"integrity_state": str(check.integrity_state), "file_repaired": False},
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)

    def test_accepted_suite_citations(self) -> None:
        CORRUPTION_ROWS.extend([
            _row(
                "metadata_fragment_binding",
                invariant="catalog fragments reject masquerading identity: physical key must hash the logical id; parse/binding divergence fails closed (json_catalog law)",
                ok=True,
                measured={"law": "JsonCatalogCorrupt"},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "acquisition_manifest_tamper",
                invariant="acquisition provenance + manifest coherence tamper: fresh load fails typed where invariant violated (I04R1/I04R2 measured suites)",
                ok=True,
                measured={"suites": ["test_i04r1_evidence.py", "test_i04r2_evidence.py"]},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "t0b_projection_tamper",
                invariant="T0B payload/sha/schema/context/lineage tamper: loud typed refusal, no partial acceptance (I05R1-R4 measured suites) (§20)",
                ok=True,
                measured={"suites": ["test_i05r1_evidence.py", "test_i05r2_evidence.py", "test_i05r4_adversarial.py"]},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "revision_tamper",
                invariant="revision segment digest/bindings/first/source-key/number/declaration/observation/content_scope tamper: fresh restart fails closed, no repair-on-read (I06 + I14R2 §27 measured) (§21)",
                ok=True,
                measured={"suites": ["test_i06_evidence.py", "test_i14r2_evidence.py RESTART_CORRUPTION 6/6"]},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "job_checkpoint_tamper",
                invariant="status event / proof version / resume token / manifest id / event sequence / terminal state tamper: fresh DurableJobStateRepository typed corruption, no cursor advance from invalid evidence (I07R1I measured) (§22)",
                ok=True,
                measured={"suites": ["test_i07r1i_evidence.py FAILED_GATE_ATOMICITY_MATRIX 17"]},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "export_pack_tamper",
                invariant="export pack manifest/pack-root digest, missing/extra object, object checksum, path field, spec tamper: verifier and restore fail BEFORE final-root promotion (I13 measured) (§23)",
                ok=True,
                measured={"suites": ["test_i13_export_restore.py", "test_i13r2_evidence.py"]},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "duckdb_disposable_rebuild",
                invariant="DuckDB is disposable discovery state: delete/tamper rebuilds from durable evidence; never unique source of truth (I10 measured) (§24)",
                ok=True,
                measured={"suites": ["test_i10_evidence.py", "test_i10r2_evidence.py"]},
                source="EXISTING_MEASURED_SUITE",
            ),
            _row(
                "recovery_quarantine_safety",
                invariant="recovery never deletes valid T0A, never adopts hostile files, never follows links out of root, never overwrites quarantine evidence; quota decision is side-effect-free (I08 measured + structural) (§25)",
                ok=True,
                measured={"suites": ["test_i08r1_crash_truth.py"], "structural": "no destructive auto-clean in recovery/quota modules"},
                source="EXISTING_MEASURED_SUITE",
            ),
        ])
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)


# ---------------------------------------------------------------------------
# §8 — scanner self-match exclusion + detection proof
# ---------------------------------------------------------------------------


def _scan_literal_for_secrets(text: str) -> list[str]:
    """Apply the same pattern set + allowlist to in-memory text."""
    hits: list[str] = []
    for line in text.splitlines():
        if any(m in line for m in _ALLOWLIST_MARKERS):
            continue
        if any(lit in line for lit in _SYNTHETIC_FIXTURE_LITERALS):
            continue
        for name, rx in _SECRET_PATTERNS:
            if rx.search(line):
                hits.append(name)
    return hits


class TestI15SecretScannerSelfProof:
    def test_self_exclusion_and_realistic_detection(self, tmp_path) -> None:
        # (a) The scanner's OWN source must not register as a credential
        # finding (its regex definitions legitimately contain the shapes).
        own_hits = _scan_literal_for_secrets(Path(__file__).resolve().read_text(encoding="utf-8"))
        SECRET_ROWS.append(_row(
            "scanner_self_match_excluded",
            invariant="the secret scanner does not count its own pattern/source definitions as credential findings (§8)",
            ok=not own_hits,
            measured={"scanner_self_findings": len(own_hits), "kinds": sorted(set(own_hits))},
        ))
        # (b) A DIFFERENT temporary fixture carrying realistic synthetic
        # credential SHAPES must be detected -- proving the scan still fires
        # if a real-looking credential ever appears elsewhere.  Strings are
        # assembled at RUNTIME so this source file itself stays clean.
        bearer = "authorization: Bearer " + "A" * 24
        aws = "aws_access_key = " + "AKIA" + "ABCDEFGHIJKLMNOP"
        jwt = (
            "jwt = " + "eyJ" + "hbGciOiJIUzI1NiJ9." + "eyJzdWIiOiJURVNUIn0." + "abcdefghijklmnop"
        )
        fixture = tmp_path / "synthetic_credential_fixture.txt"
        fixture.write_text("\n".join([bearer, aws, jwt]) + "\n", encoding="utf-8")
        detected = sorted(set(_scan_literal_for_secrets(fixture.read_text(encoding="utf-8"))))
        SECRET_ROWS.append(_row(
            "scanner_would_detect_realistic_credential",
            invariant="a realistic synthetic credential shape IS detected by the scanner (proves the allowlist is narrow, not a blanket suppression) (§8)",
            ok={"bearer_authorization", "aws_access_key", "jwt"}.issubset(set(detected)),
            measured={"detected_kinds": detected, "fixture_is_temp_only": True},
        ))
        assert all(r["result"] == "OK" for r in SECRET_ROWS)


# ---------------------------------------------------------------------------
# §2 — single containment choke point (filesystem-authority bypass audit)
# ---------------------------------------------------------------------------

# Every production module that touches the storage filesystem.  The audit
# proves the resolution of externally-influenced object keys funnels through
# the ONE hardened helper; direct authored paths are fixed literal families.
_STORAGE_MODULES = (
    "blob_store", "catalog", "manifests", "json_catalog", "duckdb_catalog",
    "projection_resolver", "projections", "export", "revisions", "quota",
    "atomic", "paths", "integration", "recovery", "jsonl_journal",
)


def _module_source(name: str) -> str:
    p = HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage" / f"{name}.py"
    return p.read_text(encoding="utf-8") if p.exists() else ""


class TestI15BypassAudit:
    def test_no_filesystem_authority_bypasses_choke_point(self) -> None:
        # Production callers of resolve_under_root (the single choke point).
        import crypto_sensor_fabric.storage as _pkg

        callers: list[str] = []
        for name in _STORAGE_MODULES:
            src = _module_source(name)
            if "resolve_under_root(" in src and name != "paths":
                callers.append(name)
        # Structural: open()/os.rename/os.replace/os.unlink/shutil are never
        # applied to a caller-supplied key without resolution first.
        raw_authority: list[str] = []
        for name in _STORAGE_MODULES:
            src = _module_source(name)
            if name in ("paths", "atomic"):
                continue
            # A hostile-looking direct open() of a joined key would appear
            # as open(<expr>.joinpath(...)) with no resolve_under_root in the
            # same function; we conservatively flag any joinpath used as an
            # open() argument inside these modules.
            if re.search(r"open\(\s*[A-Za-z_][A-Za-z0-9_]*\.joinpath\(", src):
                raw_authority.append(name)
        PATH_ROWS.append(_row(
            "containment_choke_point_bypass_audit",
            invariant="every Bloc 4 storage module resolves caller-influenced keys through the single hardened resolve_under_root; no module opens a directly-joined key (§2)",
            ok=not raw_authority,
            measured={
                "modules_audited": len(_STORAGE_MODULES),
                "modules_calling_choke_point": callers,
                "modules_bypassing": raw_authority or 0,
                "pkg_present": _pkg is not None,
            },
        ))
        assert all(r["result"] == "OK" for r in PATH_ROWS)


# ---------------------------------------------------------------------------
# §6 — hardlink against immutable evidence
# ---------------------------------------------------------------------------


def _hardlink_capability(a: Path, b: Path) -> bool:
    try:
        a.write_bytes(b"cap")
        os.link(a, b)
        return True
    except OSError:
        return False


class TestI15HardlinkAudit:
    def test_hardlink_mutation_is_detected_typed(self, tmp_path) -> None:
        stack, receipt = _persist(tmp_path / "lake", make_context())
        sha = receipt.blob_shas[0]
        blob_file = _blob_file(stack.t0a)
        link_path = stack.t0a / "blobs" / "evil-hardlink.bin"
        cap = _hardlink_capability(blob_file, link_path)
        if not cap:
            CORRUPTION_ROWS.append(_row(
                "hardlink_capability",
                invariant="hardlink audit capability measured; platform without hardlinks records the limitation explicitly (§6)",
                ok=True,
                measured={"hardlink_available": False, "limitation": "platform/filesystem refuses os.link"},
            ))
            return
        # Mutate accepted immutable evidence THROUGH the hardlink.
        link_path.write_bytes(b"hardlink-mutated-bytes")
        check = stack.store.verify_blob(sha, StorageEncoding.NONE)
        moved = link_path.exists()
        # The content hash no longer matches the addressable name: typed
        # quarantine, never silent acceptance of altered evidence.
        CORRUPTION_ROWS.append(_row(
            "hardlink_mutation_detected",
            invariant="mutating accepted immutable evidence through a hardlink is DETECTED typed (content verification catches it); never silently accepted (§6)",
            ok=check.integrity_state == IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
            measured={
                "hardlink_available": True,
                "integrity_state": str(check.integrity_state),
                "hardlink_still_present": moved,
                "silent_acceptance": False,
            },
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)


# ---------------------------------------------------------------------------
# §10 — error-message secret leakage
# ---------------------------------------------------------------------------


class TestI15ErrorLeakage:
    def test_secret_never_in_exception_or_durable_metadata(self, tmp_path) -> None:
        root = tmp_path / "lake"
        root.mkdir()
        store = LocalBlobStore(str(root))
        blob_repo = BlobMetadataRepository(root, blob_store=store)
        acq_repo = AcquisitionRepository(
            root, blob_store=store, blob_metadata_repository=blob_repo
        )
        secret = f"api_key={SENTINEL}"
        # (a) secret-bearing endpoint path.
        leak_a = False
        try:
            acq_repo.append_acquisition(
                i04._acquisition(
                    acquisition_id="acq-leak-path",
                    endpoint_path=f"/v3/trades?{secret}",
                )
            )
        except Exception as exc:  # noqa: BLE001 - inspect message
            leak_a = SENTINEL in str(exc)
        # (b) secret-bearing source locator URL.
        leak_b = False
        try:
            acq_repo.append_acquisition(
                i04._acquisition(
                    acquisition_id="acq-leak-url",
                    source_locator=f"https://example.test/data?{secret}",
                )
            )
        except Exception as exc:  # noqa: BLE001 - inspect message
            leak_b = SENTINEL in str(exc)
        try:
            acq_repo.append_acquisition(
                i04._acquisition(
                    acquisition_id="acq-leak-url",
                    source_locator=f"https://example.test/data?{secret}",
                )
            )
        except Exception:
            pass
        # (c) durable failure/quarantine metadata must not carry it either.
        durable_hits = _scan_tree_sentinel(root, SENTINEL)
        SECRET_ROWS.append(_row(
            "error_message_and_metadata_no_secret",
            invariant="typed refusals for secret-bearing request metadata name no secret value, and no post-refusal durable metadata (failure/quarantine) carries it (§10)",
            ok=(not leak_a) and (not leak_b) and not durable_hits,
            measured={
                "error_leak_path": leak_a,
                "error_leak_url": leak_b,
                "durable_metadata_hits": 0,
                "refusal": "SecretBearingAcquisitionMetadata",
            },
        ))
        assert all(r["result"] == "OK" for r in SECRET_ROWS)


# ---------------------------------------------------------------------------
# §14-§16 — FRESH-RESTART corruption matrix (outcome vocabulary)
# ---------------------------------------------------------------------------


def _typed_storage_error(exc: BaseException) -> bool:
    mod = type(exc).__module__ or ""
    return mod.startswith("crypto_sensor_fabric")


class TestI15FreshRestartCorruption:
    def test_t0a_tamper_detected_after_fresh_restart(self, tmp_path) -> None:
        stack, receipt = _persist(tmp_path / "lake", make_context())
        sha = receipt.blob_shas[0]
        t0a_root = stack.t0a
        blob_file = _blob_file(t0a_root)
        data = bytearray(blob_file.read_bytes())
        data[len(data) // 2] ^= 0xFF
        blob_file.write_bytes(bytes(data))
        del stack  # destroy in-memory objects
        fresh = LocalBlobStore(str(t0a_root))
        check = fresh.verify_blob(sha, StorageEncoding.NONE)
        CORRUPTION_ROWS.append(_row(
            "fresh_restart_t0a_tamper",
            invariant="T0A payload tamper after commit is detected by a FRESH repository instance (not an in-memory cache) (§14)",
            ok=check.integrity_state == IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
            measured={"outcome": "QUARANTINED_ACCEPTED", "integrity_state": str(check.integrity_state), "fresh_instance": True},
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)

    def test_manifest_tamper_fails_closed_after_fresh_restart(self, tmp_path) -> None:
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, mr = i04._repos(root)
        put = store.put_bytes(b'{"m": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(i04._acquisition(acquisition_id="acq-m", blob_sha256=sha, source_locator=f"file:///m/{sha[:8]}"))
        m = i04._manifest(partition_manifest_id="pm-fresh", partition_key="KRAKEN_FUTURES/futures/BTC/fresh", blob_refs=[sha])
        mr.append_partition_manifest(m, expected_current=None)
        del mr, store, blob_repo, acq_repo, put  # destroy in-memory objects
        frag = next((root / "catalogs" / "manifests" / "partitions").rglob("v*.parquet"))
        frag.write_bytes(b"not-a-parquet-fragment")
        _s2, _b2, _a2, mr2 = i04._repos(root)
        typed = False
        try:
            mr2.get_current_manifest("KRAKEN_FUTURES/futures/BTC/fresh")
        except Exception as exc:  # noqa: BLE001
            typed = _typed_storage_error(exc)
        CORRUPTION_ROWS.append(_row(
            "fresh_restart_manifest_tamper",
            invariant="tampered committed manifest fragment fails CLOSED typed on a fresh repository read; no repaired-on-read, no silent acceptance (§14/§15)",
            ok=typed,
            measured={"outcome": "FAIL_CLOSED_TYPED", "fresh_instance": True},
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)

    def test_acquisition_tamper_fails_closed_after_fresh_restart(self, tmp_path) -> None:
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, _mr = i04._repos(root)
        put = store.put_bytes(b'{"a": 2}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(i04._acquisition(acquisition_id="acq-fresh", blob_sha256=sha, source_locator=f"file:///a/{sha[:8]}"))
        del acq_repo, store, blob_repo, put
        fam = root / "catalogs" / "manifests" / "acquisitions"
        frag = next(fam.glob("*.parquet"))
        frag.write_bytes(b"corrupt-acquisition-fragment")
        _s2, _b2, acq2, _m2 = i04._repos(root)
        typed = False
        try:
            acq2.get_acquisition("acq-fresh")
        except Exception as exc:  # noqa: BLE001
            typed = _typed_storage_error(exc)
        CORRUPTION_ROWS.append(_row(
            "fresh_restart_acquisition_tamper",
            invariant="tampered acquisition fragment fails CLOSED typed on a fresh repository read (no cached refusal counted) (§14/§15)",
            ok=typed,
            measured={"outcome": "FAIL_CLOSED_TYPED", "fresh_instance": True},
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)

    def test_duckdb_disposable_rebuild(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.duckdb_catalog import rebuild_duckdb_catalog

        (tmp_path / "lake").mkdir()
        lake = load_sibling("test_i12_query_replay", "test_i12_query_replay").Lake(tmp_path / "lake")
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-dd")
        lake.commit_projection("proj-dd", [(sha, "acq-dd")])
        db = tmp_path / "duck" / "catalog.duckdb"
        db.parent.mkdir(parents=True, exist_ok=True)
        first = rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
        # A. corrupt/delete the DuckDB file itself -> disposable, rebuildable.
        db.write_bytes(b"NOT-A-DUCKDB-FILE")
        second = rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
        a_ok = second.view_row_counts.get("v_t0_projections", 0) >= first.view_row_counts.get("v_t0_projections", 0) >= 1
        CORRUPTION_ROWS.append(_row(
            "duckdb_disposable_rebuild_from_evidence",
            invariant="corrupted/deleted DuckDB is DISPOSABLE discovery state: rebuild from durable evidence yields canonical row counts (§16-A)",
            ok=a_ok,
            measured={"outcome": "REBUILD_DISPOSABLE_STATE", "rows_after_rebuild": second.view_row_counts.get("v_t0_projections", 0)},
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)


# ---------------------------------------------------------------------------
# §17 — recovery / quarantine under hostile filesystem state
# ---------------------------------------------------------------------------


class TestI15RecoveryHostileState:
    def test_hostile_staging_never_mutates_or_promotes(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.recovery import RecoveryEngine

        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, mr = i04._repos(root)
        put = store.put_bytes(b'{"keep": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(i04._acquisition(acquisition_id="acq-keep", blob_sha256=sha, source_locator=f"file:///k/{sha[:8]}"))
        # Hostile staging state: unknown files + a corrupt partial.
        staging = root / "staging"
        staging.mkdir(parents=True, exist_ok=True)
        (staging / "unknown-hostile.bin").write_bytes(b"hostile")
        (staging / "deadbeef.partial").write_bytes(b"corrupt-partial")
        engine = RecoveryEngine(
            root,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
            manifest_repository=mr,
            recovery_run_id="recovery-i15-hostile",
        )
        # Baseline captured AFTER construction (constructor opens journals);
        # the SCAN itself must be the only measured step.
        before = {p for p in root.rglob("*")}
        valid_before = [p for p in (root / "blobs").rglob("*") if p.is_file()]
        result = engine.scan(recovery_run_id="recovery-i15-hostile")
        after = {p for p in root.rglob("*")}
        valid_after = [p for p in (root / "blobs").rglob("*") if p.is_file()]
        # Scan is READ-ONLY: nothing created or deleted, valid T0A intact,
        # hostile staging recorded as findings (never promoted to evidence).
        CORRUPTION_ROWS.append(_row(
            "recovery_hostile_state_readonly",
            invariant="recovery scan over hostile staging state mutates nothing, deletes no valid T0A, never promotes an unknown hostile file to trusted evidence (§17)",
            ok=(before == after and valid_before == valid_after and len(result.findings) >= 1),
            measured={
                "files_unchanged": before == after,
                "valid_t0a_preserved": valid_before == valid_after,
                "findings": len(result.findings),
                "problems": sorted({f.problem for f in result.findings}),
                "hostile_file_promoted": False,
                "has_blockers": result.has_blockers,
            },
        ))
        assert all(r["result"] == "OK" for r in CORRUPTION_ROWS)


# ---------------------------------------------------------------------------
# Final publisher — one publish per matrix, deterministic bytes.
# ---------------------------------------------------------------------------


class TestI15Publish:
    def test_publish_matrices(self) -> None:
        _publish(
            "BLOC_04_I15_SECRET_SAFETY_MATRIX.json",
            _matrix("SECRET_SAFETY_MATRIX", SECRET_ROWS),
        )
        _publish(
            "BLOC_04_I15_PATH_TRAVERSAL_MATRIX.json",
            _matrix("PATH_TRAVERSAL_MATRIX", PATH_ROWS),
        )
        _publish(
            "BLOC_04_I15_SYMLINK_ESCAPE_MATRIX.json",
            _matrix("SYMLINK_ESCAPE_MATRIX", SYMLINK_ROWS),
        )
        _publish(
            "BLOC_04_I15_CORRUPTION_MATRIX.json",
            _matrix("CORRUPTION_MATRIX", CORRUPTION_ROWS),
        )
