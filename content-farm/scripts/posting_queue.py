#!/usr/bin/env python3
"""Posting Queue — Manage content queue for all platforms.

Usage:
    python posting_queue.py --add <file> --platform <platform> --scheduled <datetime>
    python posting_queue.py --list
    python posting_queue.py --status
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

FARM_ROOT = Path(__file__).parent.parent
QUEUE_FILE = FARM_ROOT / "coordination" / "posting-queue.json"

DEFAULT_QUEUE = {
    "version": "1.0",
    "created": datetime.now().isoformat(),
    "queue": []
}

def load_queue():
    """Load posting queue from file."""
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_QUEUE.copy()

def save_queue(queue_data):
    """Save posting queue to file."""
    os.makedirs(QUEUE_FILE.parent, exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue_data, f, indent=2)

def add_to_queue(file_path, platform, scheduled=None, caption="", tags=None):
    """Add a content piece to the posting queue."""
    queue_data = load_queue()
    
    entry = {
        "id": len(queue_data["queue"]) + 1,
        "file": file_path,
        "platform": platform,
        "scheduled": scheduled or datetime.now().isoformat(),
        "caption": caption,
        "tags": tags or [],
        "status": "queued",
        "created": datetime.now().isoformat()
    }
    
    queue_data["queue"].append(entry)
    save_queue(queue_data)
    print(f"✅ Added to queue: {file_path} → {platform}")
    return entry

def list_queue():
    """List all items in the posting queue."""
    queue_data = load_queue()
    items = queue_data.get("queue", [])
    
    if not items:
        print("📭 Posting queue is empty")
        return
    
    print(f"📋 Posting Queue ({len(items)} items)")
    print("-" * 60)
    
    for item in items:
        status_icon = {"queued": "⏳", "posted": "✅", "failed": "❌"}.get(item["status"], "❓")
        print(f"  {status_icon} #{item['id']} | {item['platform']:10s} | {item['scheduled'][:16]} | {item['file']}")

def show_status():
    """Show queue status summary."""
    queue_data = load_queue()
    items = queue_data.get("queue", [])
    
    platforms = {}
    statuses = {}
    for item in items:
        p = item["platform"]
        s = item["status"]
        platforms[p] = platforms.get(p, 0) + 1
        statuses[s] = statuses.get(s, 0) + 1
    
    print("📊 Posting Queue Status")
    print("-" * 40)
    print(f"  Total items: {len(items)}")
    print(f"  By status: {statuses}")
    print(f"  By platform: {platforms}")

def main():
    parser = argparse.ArgumentParser(description="Content Farm Posting Queue")
    parser.add_argument("--add", help="File to add to queue")
    parser.add_argument("--platform", help="Platform (tiktok, ig, x, reddit)")
    parser.add_argument("--scheduled", help="Scheduled datetime (ISO format)")
    parser.add_argument("--caption", default="", help="Caption for the post")
    parser.add_argument("--list", action="store_true", help="List queue")
    parser.add_argument("--status", action="store_true", help="Show status")
    
    args = parser.parse_args()
    
    if args.add and args.platform:
        add_to_queue(args.add, args.platform, args.scheduled, args.caption)
    elif args.list:
        list_queue()
    elif args.status:
        show_status()
    else:
        show_status()

if __name__ == "__main__":
    main()
