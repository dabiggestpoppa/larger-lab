#!/usr/bin/env python3
"""
Posting Queue — Scheduled Content Distribution for Content Farm

Manages a queue of content ready to post across platforms.
Tracks what's been posted where to avoid duplicates.
Supports platform rotation and scheduling.

Queue file:      ../data/posting-queue.json
Post log:        ../logs/posts.jsonl
Dedup tracking:  ../data/posted-hashes.json

Usage:
    python posting_queue.py --add ../output/tiktok/image1.jpg --platform tiktok --caption "Check this out"
    python posting_queue.py --add-batch ../output/tiktok --platform tiktok
    python posting_queue.py --list
    python posting_queue.py --pending
    python posting_queue.py --mark-posted queue_id --platform tiktok
    python posting_queue.py --rotate --platforms tiktok instagram twitter
    python posting_queue.py --stats
"""

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FARM_DIR = SCRIPT_DIR.parent
QUEUE_FILE = FARM_DIR / "data" / "posting-queue.json"
POST_LOG = FARM_DIR / "logs" / "posts.jsonl"
DEDUP_FILE = FARM_DIR / "data" / "posted-hashes.json"
OUTPUT_BASE = FARM_DIR / "output"

for d in [QUEUE_FILE.parent, POST_LOG.parent]:
    d.mkdir(parents=True, exist_ok=True)

VALID_PLATFORMS = ["tiktok", "instagram", "twitter", "reddit"]


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_json(path: Path, default=None):
    """Load JSON file, return default if not exists."""
    if default is None:
        default = {}
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    """Save data as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def file_hash(filepath: Path) -> str:
    """Generate SHA256 hash of file for dedup."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in f.read(8192 * 16):
            h.update(chunk)
    return h.hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Queue operations
# ---------------------------------------------------------------------------

def add_to_queue(
    file_path: str,
    platform: str,
    caption: str = "",
    hashtags: list = None,
    scheduled_time: str = None,
    priority: int = 5,
    metadata: dict = None,
) -> dict:
    """Add a single item to the posting queue."""
    if platform not in VALID_PLATFORMS:
        print(f"ERROR: Invalid platform '{platform}'. Choose from: {VALID_PLATFORMS}")
        return {}

    fpath = Path(file_path)
    if not fpath.exists():
        print(f"ERROR: File not found: {file_path}")
        return {}

    queue = load_json(QUEUE_FILE, default={"queue": [], "archived": []})
    fhash = file_hash(fpath)

    # Check for exact duplicate in queue
    for item in queue.get("queue", []):
        if item.get("file_hash") == fhash and item.get("platform") == platform:
            print(f"SKIP: Already in queue for {platform}: {fpath.name}")
            return item

    item = {
        "id": str(uuid.uuid4())[:8],
        "file_path": str(fpath.resolve()),
        "file_name": fpath.name,
        "file_hash": fhash,
        "platform": platform,
        "caption": caption,
        "hashtags": hashtags or [],
        "scheduled_time": scheduled_time,
        "priority": priority,  # 1=highest, 10=lowest
        "status": "pending",
        "created_at": now_iso(),
        "posted_at": None,
        "post_url": None,
        "metadata": metadata or {},
    }

    queue.setdefault("queue", []).append(item)
    save_json(QUEUE_FILE, queue)
    print(f"ADDED: [{item['id']}] {fpath.name} → {platform}")
    return item


def add_batch(directory: str, platform: str, caption_template: str = "", **kwargs):
    """Add all images from a directory to the queue."""
    d = Path(directory)
    if not d.exists():
        print(f"ERROR: Directory not found: {directory}")
        return []

    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov"}
    files = sorted(f for f in d.rglob("*") if f.suffix.lower() in image_exts)
    added = []

    print(f"Adding {len(files)} files from {directory} → {platform}")
    for fpath in files:
        # Skip metadata JSONs and non-media
        if fpath.suffix == ".json":
            continue
        caption = caption_template.replace("{filename}", fpath.stem)
        item = add_to_queue(str(fpath), platform, caption, **kwargs)
        if item:
            added.append(item)

    print(f"\nTotal added: {len(added)}")
    return added


def mark_posted(queue_id: str, platform: str, post_url: str = "", stats: dict = None):
    """Mark a queue item as posted."""
    queue = load_json(QUEUE_FILE, default={"queue": [], "archived": []})
    posted_hash = None

    for i, item in enumerate(queue.get("queue", [])):
        if item["id"] == queue_id and item["platform"] == platform:
            item["status"] = "posted"
            item["posted_at"] = now_iso()
            item["post_url"] = post_url
            item["stats"] = stats or {}
            posted_hash = item.get("file_hash")

            # Move to archived
            queue.setdefault("archived", []).append(item)
            queue["queue"].pop(i)

            save_json(QUEUE_FILE, queue)

            # Log to posts.jsonl
            log_entry = {
                "id": queue_id,
                "platform": platform,
                "file": item["file_name"],
                "file_hash": posted_hash,
                "caption": item.get("caption", ""),
                "posted_at": item["posted_at"],
                "post_url": post_url,
                "stats": stats or {},
            }
            with open(POST_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            # Track hash for dedup
            dedup = load_json(DEDUP_FILE)
            dedup[posted_hash] = {
                "platform": platform,
                "posted_at": item["posted_at"],
                "file": item["file_name"],
            }
            save_json(DEDUP_FILE, dedup)

            print(f"POSTED: [{queue_id}] {item['file_name']} → {platform}")
            if post_url:
                print(f"  URL: {post_url}")
            return item

    print(f"ERROR: Queue item not found: {queue_id} / {platform}")
    return None


def get_pending(platform: str = None, limit: int = None) -> list:
    """Get pending items, optionally filtered by platform."""
    queue = load_json(QUEUE_FILE, default={"queue": [], "archived": []})
    items = queue.get("queue", [])

    pending = [i for i in items if i.get("status") == "pending"]
    if platform:
        pending = [i for i in pending if i["platform"] == platform]

    # Sort by priority (low number = high priority), then creation time
    pending.sort(key=lambda x: (x.get("priority", 5), x.get("created_at", "")))

    if limit:
        pending = pending[:limit]

    return pending


def get_next_rotation(platforms: list) -> dict:
    """
    Get the next item for each platform, rotating evenly.
    Returns {platform: item} dict.
    """
    result = {}
    for platform in platforms:
        pending = get_pending(platform, limit=1)
        if pending:
            result[platform] = pending[0]
    return result


def check_duplicate(file_path: str, platform: str) -> bool:
    """Check if a file has already been posted to a platform."""
    fpath = Path(file_path)
    if not fpath.exists():
        return False
    fhash = file_hash(fpath)
    dedup = load_json(DEDUP_FILE)
    entry = dedup.get(fhash)
    if entry and entry.get("platform") == platform:
        return True
    return False


def get_stats() -> dict:
    """Get queue statistics."""
    queue = load_json(QUEUE_FILE, default={"queue": [], "archived": []})
    pending = [i for i in queue.get("queue", []) if i.get("status") == "pending"]
    archived = queue.get("archived", [])

    by_platform_pending = {}
    by_platform_posted = {}
    for p in VALID_PLATFORMS:
        by_platform_pending[p] = len([i for i in pending if i["platform"] == p])
        by_platform_posted[p] = len([i for i in archived if i["platform"] == p])

    return {
        "pending": len(pending),
        "posted": len(archived),
        "total": len(pending) + len(archived),
        "by_platform_pending": by_platform_pending,
        "by_platform_posted": by_platform_posted,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Posting Queue — Content distribution manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python posting_queue.py --add ../output/tiktok/img1.jpg --platform tiktok --caption "Amazing art!"
  python posting_queue.py --add-batch ../output/tiktok --platform tiktok
  python posting_queue.py --list
  python posting_queue.py --pending
  python posting_queue.py --pending --platform tiktok
  python posting_queue.py --mark-posted abc123 --platform tiktok --url "https://..."
  python posting_queue.py --rotate --platforms tiktok instagram twitter
  python posting_queue.py --stats
  python posting_queue.py --check-dup ../output/tiktok/img1.jpg --platform tiktok
        """,
    )
    parser.add_argument("--add", type=str, help="Add a file to the queue")
    parser.add_argument("--add-batch", type=str, help="Add all files from directory")
    parser.add_argument("--platform", type=str, choices=VALID_PLATFORMS,
                        help="Target platform")
    parser.add_argument("--caption", type=str, default="", help="Post caption")
    parser.add_argument("--hashtags", type=str, default="",
                        help="Comma-separated hashtags")
    parser.add_argument("--priority", type=int, default=5,
                        help="Priority 1-10 (1=highest, default: 5)")
    parser.add_argument("--list", action="store_true", help="List all queue items")
    parser.add_argument("--pending", action="store_true", help="Show pending items")
    parser.add_argument("--mark-posted", type=str, help="Mark queue item as posted (by ID)")
    parser.add_argument("--url", type=str, default="", help="Post URL when marking posted")
    parser.add_argument("--rotate", action="store_true",
                        help="Show next items for rotation across platforms")
    parser.add_argument("--platforms", type=str, nargs="+",
                        help="Platforms for rotation mode")
    parser.add_argument("--stats", action="store_true", help="Show queue statistics")
    parser.add_argument("--check-dup", type=str, help="Check if file already posted")
    parser.add_argument("--limit", type=int, default=None, help="Limit results")

    args = parser.parse_args()

    print("=" * 60)
    print("  Posting Queue — Content Farm")
    print("=" * 60)

    if args.add:
        hashtags = [h.strip() for h in args.hashtags.split(",") if h.strip()] if args.hashtags else []
        add_to_queue(args.add, args.platform, args.caption, hashtags, priority=args.priority)

    elif args.add_batch:
        if not args.platform:
            print("ERROR: --platform required for batch add")
            sys.exit(1)
        add_batch(args.batch, args.platform, args.caption)

    elif args.list:
        queue = load_json(QUEUE_FILE, default={"queue": [], "archived": []})
        items = queue.get("queue", [])
        archived = queue.get("archived", [])

        print(f"\n--- PENDING ({len(items)}) ---")
        for item in items:
            print(f"  [{item['id']}] {item['file_name']} → {item['platform']} "
                  f"(P{item.get('priority', 5)}, {item.get('status', 'pending')})")

        print(f"\n--- ARCHIVED/POSTED ({len(archived)}) ---")
        for item in archived[-20:]:  # Show last 20
            print(f"  [{item['id']}] {item['file_name']} → {item['platform']} "
                  f"({item.get('posted_at', 'unknown')})")

    elif args.pending:
        items = get_pending(args.platform, args.limit)
        platform_label = args.platform or "all"
        print(f"\n--- PENDING ({len(items)}) [{platform_label}] ---")
        for item in items:
            print(f"  [{item['id']}] {item['file_name']} → {item['platform']} "
                  f"(P{item.get('priority', 5)})")
            if item.get("caption"):
                print(f"    Caption: {item['caption'][:80]}...")

    elif args.mark_posted:
        if not args.platform:
            print("ERROR: --platform required")
            sys.exit(1)
        mark_posted(args.mark_posted, args.platform, args.url)

    elif args.rotate:
        platforms = args.platforms or VALID_PLATFORMS
        rotation = get_next_rotation(platforms)
        print(f"\n--- ROTATION ({', '.join(platforms)}) ---")
        for platform, item in rotation.items():
            print(f"  {platform}: [{item['id']}] {item['file_name']}")
        missing = set(platforms) - set(rotation.keys())
        for p in missing:
            print(f"  {p}: (no pending items)")

    elif args.stats:
        stats = get_stats()
        print(f"\n--- QUEUE STATS ---")
        print(f"  Pending : {stats['pending']}")
        print(f"  Posted  : {stats['posted']}")
        print(f"  Total   : {stats['total']}")
        print(f"\n  By Platform (pending):")
        for p, c in stats["by_platform_pending"].items():
            print(f"    {p:12s}: {c}")
        print(f"\n  By Platform (posted):")
        for p, c in stats["by_platform_posted"].items():
            print(f"    {p:12s}: {c}")

    elif args.check_dup:
        if not args.platform:
            print("ERROR: --platform required")
            sys.exit(1)
        is_dup = check_duplicate(args.check_dup, args.platform)
        if is_dup:
            print(f"DUPLICATE: {args.check_dup} already posted to {args.platform}")
        else:
            print(f"OK: {args.check_dup} not yet posted to {args.platform}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
