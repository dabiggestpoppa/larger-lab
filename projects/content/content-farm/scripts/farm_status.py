#!/usr/bin/env python3
"""
Farm Status Dashboard — Content Farm Monitoring

Generates a daily summary report of the content farm's state:
- Images downloaded (by NSFW level)
- Images remixed/processed (by platform)
- Posts queued / posted / pending
- Platform performance (from post log)
- Daily summary report

Usage:
    python farm_status.py
    python farm_status.py --report
    python farm_status.py --report --save
    python farm_status.py --watch  # Refresh every 60s
"""

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FARM_DIR = SCRIPT_DIR.parent
DATA_DIR = FARM_DIR / "data"
OUTPUT_DIR = FARM_DIR / "output"
LOGS_DIR = FARM_DIR / "logs"
REPORTS_DIR = LOGS_DIR

QUEUE_FILE = DATA_DIR / "posting-queue.json"
POST_LOG = LOGS_DIR / "posts.jsonl"
DEDUP_FILE = DATA_DIR / "posted-hashes.json"
IMAGES_DIR = DATA_DIR / "civitai" / "images"

NSFW_LEVELS = ["sfw", "soft", "mature", "x"]
PLATFORMS = ["tiktok", "instagram", "twitter", "reddit"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

def count_images() -> dict:
    """Count downloaded images by NSFW level."""
    counts = {}
    for level in NSFW_LEVELS:
        level_dir = IMAGES_DIR / level
        if level_dir.exists():
            images = [f for f in level_dir.iterdir()
                      if f.suffix.lower() in IMAGE_EXTENSIONS]
            counts[level] = len(images)
        else:
            counts[level] = 0
    counts["total"] = sum(counts.values())
    return counts


def count_remuxed() -> dict:
    """Count processed/output images by platform."""
    counts = {}
    for platform in PLATFORMS:
        platform_dir = OUTPUT_DIR / platform
        if platform_dir.exists():
            total = 0
            for level_dir in platform_dir.iterdir():
                if level_dir.is_dir():
                    images = [f for f in level_dir.iterdir()
                              if f.suffix.lower() in IMAGE_EXTENSIONS]
                    total += len(images)
            counts[platform] = total
        else:
            counts[platform] = 0
    counts["total"] = sum(counts.values())
    return counts


def get_queue_stats() -> dict:
    """Get posting queue statistics."""
    if not QUEUE_FILE.exists():
        return {"pending": 0, "posted": 0, "total": 0, "by_platform": {}}

    with open(QUEUE_FILE, encoding="utf-8") as f:
        queue = json.load(f)

    pending = [i for i in queue.get("queue", []) if i.get("status") == "pending"]
    archived = queue.get("archived", [])

    by_platform = {}
    for p in PLATFORMS:
        by_platform[p] = {
            "pending": len([i for i in pending if i["platform"] == p]),
            "posted": len([i for i in archived if i["platform"] == p]),
        }

    return {
        "pending": len(pending),
        "posted": len(archived),
        "total": len(pending) + len(archived),
        "by_platform": by_platform,
    }


def get_post_log_stats() -> dict:
    """Analyze the post log for performance data."""
    if not POST_LOG.exists():
        return {"total_posts": 0, "by_platform": {}, "recent_24h": 0, "recent": [], "engagement": {}}

    posts = []
    with open(POST_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    posts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    by_platform = Counter(p.get("platform", "unknown") for p in posts)

    # Recent posts (last 24h)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = []
    for p in posts:
        try:
            posted_at = datetime.fromisoformat(p.get("posted_at", ""))
            if posted_at >= cutoff:
                recent.append(p)
        except (ValueError, TypeError):
            pass

    # Engagement totals
    engagement = {}
    for p in posts:
        platform = p.get("platform", "unknown")
        stats = p.get("stats", {})
        if platform not in engagement:
            engagement[platform] = {"likes": 0, "shares": 0, "comments": 0, "views": 0}
        for key in ("likes", "shares", "comments", "views"):
            engagement[platform][key] += stats.get(key, 0)

    return {
        "total_posts": len(posts),
        "by_platform": dict(by_platform),
        "recent_24h": len(recent),
        "recent": recent[-10:],  # Last 10 posts
        "engagement": engagement,
    }


def get_trending_snapshots() -> list:
    """List available trending snapshots."""
    trending_dir = DATA_DIR / "civitai" / "trending"
    if not trending_dir.exists():
        return []
    return sorted(trending_dir.glob("trending_*.json"))


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(save: bool = False) -> str:
    """Generate a comprehensive daily report."""
    now = datetime.now(timezone.utc)
    images = count_images()
    remuxed = count_remuxed()
    queue = get_queue_stats()
    posts = get_post_log_stats()
    snapshots = get_trending_snapshots()

    lines = []
    lines.append("=" * 60)
    lines.append("  📊 CONTENT FARM — DAILY STATUS REPORT")
    lines.append(f"  Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("=" * 60)

    # Images downloaded
    lines.append("\n🖼️  IMAGES DOWNLOADED")
    lines.append("-" * 40)
    for level in NSFW_LEVELS:
        lines.append(f"  {level:10s}: {images.get(level, 0):>6,}")
    lines.append(f"  {'TOTAL':10s}: {images.get('total', 0):>6,}")

    # Images processed
    lines.append("\n🎨 IMAGES PROCESSED (REMIXED)")
    lines.append("-" * 40)
    for platform in PLATFORMS:
        lines.append(f"  {platform:12s}: {remuxed.get(platform, 0):>6,}")
    lines.append(f"  {'TOTAL':12s}: {remuxed.get('total', 0):>6,}")

    # Posting queue
    lines.append("\n📮 POSTING QUEUE")
    lines.append("-" * 40)
    lines.append(f"  Pending : {queue['pending']:>6,}")
    lines.append(f"  Posted  : {queue['posted']:>6,}")
    lines.append(f"  Total   : {queue['total']:>6,}")
    lines.append(f"\n  {'Platform':12s} {'Pending':>8s} {'Posted':>8s}")
    lines.append(f"  {'-'*12} {'-'*8} {'-'*8}")
    for platform in PLATFORMS:
        bp = queue.get("by_platform", {}).get(platform, {})
        lines.append(f"  {platform:12s} {bp.get('pending', 0):>8,} {bp.get('posted', 0):>8,}")

    # Post log
    lines.append("\n📈 POST LOG")
    lines.append("-" * 40)
    lines.append(f"  Total posts     : {posts['total_posts']:>6,}")
    lines.append(f"  Posts (24h)     : {posts['recent_24h']:>6,}")
    if posts["by_platform"]:
        lines.append(f"\n  {'Platform':12s} {'Posts':>8s}")
        lines.append(f"  {'-'*12} {'-'*8}")
        for platform, count in sorted(posts["by_platform"].items()):
            lines.append(f"  {platform:12s} {count:>8,}")

    # Engagement
    if posts.get("engagement"):
        lines.append("\n💬 ENGAGEMENT (TOTAL)")
        lines.append("-" * 40)
        lines.append(f"  {'Platform':12s} {'Likes':>8s} {'Shares':>8s} {'Comments':>10s} {'Views':>8s}")
        lines.append(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*10} {'-'*8}")
        for platform, eng in sorted(posts["engagement"].items()):
            lines.append(
                f"  {platform:12s} {eng.get('likes', 0):>8,} "
                f"{eng.get('shares', 0):>8,} {eng.get('comments', 0):>10,} "
                f"{eng.get('views', 0):>8,}"
            )

    # Trending snapshots
    lines.append("\n📸 TRENDING SNAPSHOTS")
    lines.append("-" * 40)
    lines.append(f"  Available: {len(snapshots)}")
    if snapshots:
        latest = snapshots[-1]
        lines.append(f"  Latest: {latest.name}")

    # Pipeline health
    lines.append("\n🔧 PIPELINE HEALTH")
    lines.append("-" * 40)
    total_raw = images.get("total", 0)
    total_processed = remuxed.get("total", 0)
    total_posted = queue.get("posted", 0)
    conversion = (total_processed / total_raw * 100) if total_raw > 0 else 0
    lines.append(f"  Raw → Processed : {conversion:.1f}% ({total_processed}/{total_raw})")
    lines.append(f"  Processed → Posted: {(total_posted / total_processed * 100) if total_processed > 0 else 0:.1f}% ({total_posted}/{total_processed})")
    lines.append(f"  Queue depth     : {queue['pending']} pending")

    lines.append("\n" + "=" * 60)
    lines.append("  END OF REPORT")
    lines.append("=" * 60)

    report = "\n".join(lines)

    if save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = now.strftime("%Y-%m-%d")
        report_path = REPORTS_DIR / f"daily_report_{date_str}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved: {report_path}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Farm Status Dashboard — Content farm monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python farm_status.py
  python farm_status.py --report
  python farm_status.py --report --save
  python farm_status.py --watch
        """,
    )
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--save", action="store_true", help="Save report to logs/")
    parser.add_argument("--watch", action="store_true", help="Refresh every 60s")
    parser.add_argument("--interval", type=int, default=60,
                        help="Watch interval in seconds (default: 60)")

    args = parser.parse_args()

    if args.watch:
        print("Watching farm status (Ctrl+C to stop)...")
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                report = generate_report(save=args.save)
                try:
                    print(report)
                except UnicodeEncodeError:
                    print(report.encode("ascii", errors="replace").decode())
                print(f"\nRefreshing in {args.interval}s... (Ctrl+C to stop)")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        report = generate_report(save=args.save)
        try:
            print(report)
        except UnicodeEncodeError:
            print(report.encode("ascii", errors="replace").decode())


if __name__ == "__main__":
    main()
