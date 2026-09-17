#!/usr/bin/env python3
"""OCE Local Ground — immutable operation receipt index (B1-LOCAL, A-003; R8).

Every backup/restore/recovery operation receives ONE unique operation ID and
registers ONE immutable entry in a machine-readable operation index. Receipt
files live in `operations/<operation-id>/` under the operations root; each
index entry records their SHA-256 and size so a later modification of any
receipt is detectable. Entries are append-only: a duplicate operation ID
fails, and a later operation can never overwrite earlier evidence. A
convenience `latest.json` pointer MAY exist but is NOT authoritative — the
index plus per-operation receipt sets are the authoritative record.

Layout (root = the operations root):
  <root>/index.json                       authoritative index (append-only)
  <root>/latest.json                      convenience pointer (non-authoritative)
  <root>/operations/<operation-id>/...    immutable per-operation receipts

Subcommands:
  add --ops-root <root> --operation-id <id> --operation-type <backup|restore>
      --run-id <id> --commit <sha> --tree <sha>
      --started-at <ts> --finished-at <ts>
      --backup-id <id> --backup-scope <scope> --restore-mode <mode|-> 
      --source-database <db> --target-database <db>
      --final-result <success|failed|blocked>
      --rollback-result <none|ok|failed>
      --cloud-mutations <n> --cloud-cost-state <state>
      --receipt <src-file> [--receipt <src-file> ...]
    Copies each receipt into operations/<operation-id>/ (immutable), records
    its hash/size in the entry, rejects duplicate operation IDs, and appends
    the entry to index.json atomically. Writes latest.json as a pointer.

  verify --ops-root <root>
    Verifies the index: parses, operation IDs unique, every indexed receipt
    exists and still matches its recorded hash and size. Exits 0/1. Used by
    the independent gate and the regressions.
"""
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

ID_RE = re.compile(r"^[0-9a-f]{12,}$")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_index(index_path):
    if not os.path.isfile(index_path):
        return {"format": "oce-operation-index-v1", "operations": []}
    with open(index_path, encoding="utf-8") as f:
        idx = json.load(f)
    if idx.get("format") != "oce-operation-index-v1":
        raise ValueError(f"index format mismatch: {idx.get('format')!r}")
    return idx


def _write_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def cmd_add(args):
    kw = {}
    receipts = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--receipt":
            i += 1
            receipts.append(args[i] if i < len(args) else None)
        elif a in ("--ops-root", "--operation-id", "--operation-type", "--run-id",
                   "--commit", "--tree", "--started-at", "--finished-at",
                   "--backup-id", "--backup-scope", "--restore-mode",
                   "--source-database", "--target-database", "--final-result",
                   "--rollback-result", "--cloud-mutations", "--cloud-cost-state"):
            i += 1
            kw[a[2:].replace("-", "_")] = args[i] if i < len(args) else None
        else:
            print(f"USAGE_ERROR: unknown arg '{a}'", file=sys.stderr)
            return 2
        i += 1
    root = kw.get("ops_root")
    opid = kw.get("operation_id", "")
    if not root:
        print("USAGE_ERROR: --ops-root required", file=sys.stderr)
        return 2
    if not opid or not ID_RE.match(opid):
        print(f"USAGE_ERROR: invalid --operation-id {opid!r}", file=sys.stderr)
        return 2
    required = ("operation_type", "run_id", "commit", "tree", "started_at",
                "finished_at", "backup_id", "backup_scope", "restore_mode",
                "source_database", "target_database", "final_result",
                "rollback_result", "cloud_mutations", "cloud_cost_state")
    missing = [r for r in required if kw.get(r) in (None, "")]
    if missing:
        print(f"USAGE_ERROR: missing required fields: {missing}", file=sys.stderr)
        return 2
    op_dir = os.path.join(root, "operations", opid)
    if os.path.isdir(op_dir):
        print(f"DUPLICATE_OPERATION_ID: {opid} already exists — immutable, cannot overwrite",
              file=sys.stderr)
        return 2
    os.makedirs(op_dir, exist_ok=True)
    copied = []
    for src in receipts:
        if not src or not os.path.isfile(src):
            print(f"USAGE_ERROR: receipt file missing: {src}", file=sys.stderr)
            shutil.rmtree(op_dir, ignore_errors=True)
            return 2
        name = os.path.basename(src)
        dst = os.path.join(op_dir, name)
        shutil.copy2(src, dst)
        copied.append({"path": os.path.relpath(dst, root).replace(os.sep, "/"),
                       "sha256": sha256_file(dst), "size": os.path.getsize(dst)})
    if not copied:
        print("USAGE_ERROR: at least one --receipt is required", file=sys.stderr)
        shutil.rmtree(op_dir, ignore_errors=True)
        return 2
    entry = {"operation_id": opid,
             "operation_type": kw["operation_type"],
             "run_id": kw["run_id"],
             "commit": kw["commit"],
             "tree": kw["tree"],
             "started_at": kw["started_at"],
             "finished_at": kw["finished_at"],
             "backup_id": kw["backup_id"],
             "backup_scope": kw["backup_scope"],
             "restore_mode": kw["restore_mode"],
             "source_database": kw["source_database"],
             "target_database": kw["target_database"],
             "final_result": kw["final_result"],
             "rollback_result": kw["rollback_result"],
             "cloud_mutations": int(kw["cloud_mutations"]),
             "cloud_cost_state": kw["cloud_cost_state"],
             "receipts": copied}
    index_path = os.path.join(root, "index.json")
    try:
        idx = load_index(index_path)
    except Exception as e:
        print(f"BLOCKED: cannot read existing index: {e}", file=sys.stderr)
        return 1
    if any(op.get("operation_id") == opid for op in idx.get("operations", [])):
        print(f"DUPLICATE_OPERATION_ID: {opid} already indexed — immutable, cannot overwrite",
              file=sys.stderr)
        shutil.rmtree(op_dir, ignore_errors=True)
        return 2
    idx.setdefault("operations", []).append(entry)
    _write_atomic(index_path, idx)
    _write_atomic(os.path.join(root, "latest.json"),
                  {"format": "oce-operation-index-latest-v1", "operation_id": opid,
                   "entry": entry, "note": "convenience pointer; NOT authoritative"})
    print(f"operation {opid} indexed ({len(copied)} receipts)")
    return 0


def cmd_verify(args):
    kw = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--ops-root":
            i += 1
            kw["ops_root"] = args[i] if i < len(args) else None
        else:
            print(f"USAGE_ERROR: unknown arg '{a}'", file=sys.stderr)
            return 2
        i += 1
    root = kw.get("ops_root")
    if not root:
        print("USAGE_ERROR: --ops-root required", file=sys.stderr)
        return 2
    index_path = os.path.join(root, "index.json")
    if not os.path.isfile(index_path):
        print("UNVERIFIED: operation index missing (index.json)", file=sys.stderr)
        return 1
    problems = []
    try:
        idx = load_index(index_path)
    except Exception as e:
        print(f"UNVERIFIED: index unreadable: {e}", file=sys.stderr)
        return 1
    ops = idx.get("operations", [])
    if not ops:
        problems.append("index contains no operations")
    seen = {}
    for op in ops:
        opid = op.get("operation_id", "")
        if opid in seen:
            problems.append(f"duplicate operation_id {opid}")
        seen[opid] = True
        for rec in op.get("receipts", []):
            p = os.path.join(root, rec["path"])
            if not os.path.isfile(p):
                problems.append(f"{opid}: indexed receipt missing: {rec['path']}")
                continue
            if sha256_file(p) != rec.get("sha256") or os.path.getsize(p) != rec.get("size"):
                problems.append(f"{opid}: indexed receipt hash/size mismatch: {rec['path']}")
    if problems:
        print("UNVERIFIED: " + "; ".join(problems), file=sys.stderr)
        return 1
    print(f"operation index verified ({len(ops)} operations)")
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    rest = args[1:]
    if cmd == "add":
        return cmd_add(rest)
    if cmd == "verify":
        return cmd_verify(rest)
    print(f"USAGE_ERROR: unknown subcommand '{cmd}'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
