#!/usr/bin/env python3
"""
MAD Content Farm — Content Performance Tracker

Logs each piece of content posted with metadata, tracks performance metrics
over time, and stores everything in a SQLite database.

Usage:
    # Log a new post
    python content_tracker.py log --platform douyin --niche fitness \\
        --format short_video --caption "Morning workout routine" \\
        --file-path "output/videos/workout_001.mp4"

    # Update metrics after 24h
    python content_tracker.py update --post-id <uuid> --views 5000 --likes 300 \\
        --comments 50 --shares 20 --followers 10

    # Show recent posts
    python content_tracker.py list --limit 20 --platform douyin

    # Show performance summary
    python content_tracker.py summary --days 7 --niche fitness

    # Export data for Oransim
    python content_tracker.py export --format json --output data/oransim_input.json
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parent.parent.parent
CONTENT_FARM = WORKSPACE / "content-farm"
DEFAULT_DB_PATH = CONTENT_FARM / "data" / "performance.db"


def get_db_path() -> Path:
    """Resolve DB path from config or use default."""
    config_path = CONTENT_FARM / "config" / "analytics.yaml"
    if config_path.exists():
        try:
            import yaml  # type: ignore
            with open(config_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            db_path = cfg.get("database", {}).get("path", "")
            if db_path:
                return WORKSPACE / db_path
        except ImportError:
            pass
    return DEFAULT_DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection and ensure schema exists."""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id         TEXT PRIMARY KEY,
            platform        TEXT NOT NULL,
            niche           TEXT NOT NULL,
            format          TEXT NOT NULL DEFAULT 'short_video',
            caption         TEXT,
            file_path       TEXT,
            tags            TEXT DEFAULT '[]',
            posted_at       TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            shortlink_id    TEXT,
            shortlink_url   TEXT,
            status          TEXT NOT NULL DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS metrics (
            metric_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id         TEXT NOT NULL,
            recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
            views           INTEGER DEFAULT 0,
            likes           INTEGER DEFAULT 0,
            comments        INTEGER DEFAULT 0,
            shares          INTEGER DEFAULT 0,
            followers       INTEGER DEFAULT 0,
            collections     INTEGER DEFAULT 0,
            click_through   INTEGER DEFAULT 0,
            completion_rate REAL DEFAULT 0.0,
            avg_watch_time  REAL DEFAULT 0.0,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        );

        CREATE TABLE IF NOT EXISTS daily_snapshots (
            snapshot_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id         TEXT NOT NULL,
            snapshot_date   TEXT NOT NULL,
            views           INTEGER DEFAULT 0,
            likes           INTEGER DEFAULT 0,
            comments        INTEGER DEFAULT 0,
            shares          INTEGER DEFAULT 0,
            followers       INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            FOREIGN KEY (post_id) REFERENCES posts(post_id),
            UNIQUE(post_id, snapshot_date)
        );

        CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
        CREATE INDEX IF NOT EXISTS idx_posts_niche ON posts(niche);
        CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
        CREATE INDEX IF NOT EXISTS idx_metrics_post_id ON metrics(post_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_post_id ON daily_snapshots(post_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_date ON daily_snapshots(snapshot_date);
    """)
    conn.commit()


# ── CRUD Operations ────────────────────────────────────────────────

def log_post(
    conn: sqlite3.Connection,
    platform: str,
    niche: str,
    format: str = "short_video",
    caption: str = "",
    file_path: str = "",
    tags: list[str] | None = None,
    posted_at: str | None = None,
    shortlink_id: str = "",
    shortlink_url: str = "",
) -> str:
    """Log a new post. Returns the post_id UUID."""
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO posts
           (post_id, platform, niche, format, caption, file_path, tags,
            posted_at, shortlink_id, shortlink_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            post_id,
            platform,
            niche,
            format,
            caption,
            file_path,
            json.dumps(tags or []),
            posted_at or now,
            shortlink_id,
            shortlink_url,
        ),
    )
    # Also create initial metrics row
    conn.execute(
        "INSERT INTO metrics (post_id) VALUES (?)",
        (post_id,),
    )
    conn.commit()
    return post_id


def update_metrics(
    conn: sqlite3.Connection,
    post_id: str,
    views: int | None = None,
    likes: int | None = None,
    comments: int | None = None,
    shares: int | None = None,
    followers: int | None = None,
    collections: int | None = None,
    click_through: int | None = None,
    completion_rate: float | None = None,
    avg_watch_time: float | None = None,
) -> None:
    """Update the latest metrics row for a post."""
    # Build dynamic UPDATE
    fields: list[str] = []
    values: list = []
    for col, val in [
        ("views", views),
        ("likes", likes),
        ("comments", comments),
        ("shares", shares),
        ("followers", followers),
        ("collections", collections),
        ("click_through", click_through),
        ("completion_rate", completion_rate),
        ("avg_watch_time", avg_watch_time),
    ]:
        if val is not None:
            fields.append(f"{col} = ?")
            values.append(val)
    if not fields:
        return
    # Get the latest metric_id for this post
    row = conn.execute(
        "SELECT metric_id FROM metrics WHERE post_id = ? ORDER BY metric_id DESC LIMIT 1",
        [post_id],
    ).fetchone()
    if row:
        conn.execute(
            f"UPDATE metrics SET {', '.join(fields)} WHERE metric_id = ?",
            values + [row["metric_id"]],
        )
    conn.commit()


def add_snapshot(
    conn: sqlite3.Connection,
    post_id: str,
    snapshot_date: str | None = None,
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    followers: int = 0,
) -> None:
    """Add a daily snapshot for a post."""
    date = snapshot_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    eng_rate = (likes + comments + shares) / max(views, 1)
    conn.execute(
        """INSERT OR REPLACE INTO daily_snapshots
           (post_id, snapshot_date, views, likes, comments, shares, followers, engagement_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (post_id, date, views, likes, comments, shares, followers, round(eng_rate, 6)),
    )
    conn.commit()


# ── Query Operations ───────────────────────────────────────────────

def list_posts(
    conn: sqlite3.Connection,
    limit: int = 20,
    platform: str | None = None,
    niche: str | None = None,
    days: int | None = None,
) -> list[dict]:
    """List posts with optional filters."""
    query = """
        SELECT p.*, m.views, m.likes, m.comments, m.shares, m.followers,
               m.collections, m.click_through, m.completion_rate
        FROM posts p
        LEFT JOIN metrics m ON m.post_id = p.post_id
        WHERE p.status = 'active'
    """
    params: list = []
    if platform:
        query += " AND p.platform = ?"
        params.append(platform)
    if niche:
        query += " AND p.niche = ?"
        params.append(niche)
    if days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query += " AND p.posted_at >= ?"
        params.append(cutoff)
    query += " ORDER BY p.posted_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_summary(
    conn: sqlite3.Connection,
    days: int = 7,
    niche: str | None = None,
    platform: str | None = None,
) -> dict:
    """Get performance summary for a time period."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = """
        SELECT
            COUNT(DISTINCT p.post_id) as total_posts,
            COALESCE(SUM(m.views), 0) as total_views,
            COALESCE(SUM(m.likes), 0) as total_likes,
            COALESCE(SUM(m.comments), 0) as total_comments,
            COALESCE(SUM(m.shares), 0) as total_shares,
            COALESCE(SUM(m.followers), 0) as total_followers,
            COALESCE(SUM(m.collections), 0) as total_collections
        FROM posts p
        LEFT JOIN metrics m ON m.post_id = p.post_id
        WHERE p.posted_at >= ?
    """
    params: list = [cutoff]
    if niche:
        query += " AND p.niche = ?"
        params.append(niche)
    if platform:
        query += " AND p.platform = ?"
        params.append(platform)
    row = conn.execute(query, params).fetchone()
    result = dict(row) if row else {}

    # Compute engagement rate
    total_views = result.get("total_views", 0) or 0
    total_eng = (
        (result.get("total_likes", 0) or 0)
        + (result.get("total_comments", 0) or 0)
        + (result.get("total_shares", 0) or 0)
    )
    result["engagement_rate"] = round(total_eng / max(total_views, 1), 4)
    result["period_days"] = days
    return result


def get_niche_performance(
    conn: sqlite3.Connection,
    days: int = 7,
) -> list[dict]:
    """Get per-niche performance breakdown."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """
        SELECT
            p.niche,
            COUNT(DISTINCT p.post_id) as post_count,
            COALESCE(SUM(m.views), 0) as total_views,
            COALESCE(SUM(m.likes), 0) as total_likes,
            COALESCE(SUM(m.comments), 0) as total_comments,
            COALESCE(SUM(m.shares), 0) as total_shares,
            COALESCE(SUM(m.followers), 0) as total_followers
        FROM posts p
        LEFT JOIN metrics m ON m.post_id = p.post_id
        WHERE p.posted_at >= ?
        GROUP BY p.niche
        ORDER BY total_views DESC
        """,
        (cutoff,),
    ).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        views = d.get("total_views", 0) or 0
        eng = (d.get("total_likes", 0) or 0) + (d.get("total_comments", 0) or 0) + (d.get("total_shares", 0) or 0)
        d["engagement_rate"] = round(eng / max(views, 1), 4)
        results.append(d)
    return results


def export_for_oransim(
    conn: sqlite3.Connection,
    days: int = 30,
) -> list[dict]:
    """Export performance data formatted for Oransim prediction input."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """
        SELECT
            p.post_id, p.platform, p.niche, p.format, p.caption, p.posted_at,
            m.views, m.likes, m.comments, m.shares, m.followers, m.collections,
            m.completion_rate, m.avg_watch_time
        FROM posts p
        LEFT JOIN metrics m ON m.post_id = p.post_id
        WHERE p.posted_at >= ?
        ORDER BY p.posted_at DESC
        """,
        (cutoff,),
    ).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        views = d.get("views", 0) or 0
        eng = (d.get("likes", 0) or 0) + (d.get("comments", 0) or 0) + (d.get("shares", 0) or 0)
        d["engagement_rate"] = round(eng / max(views, 1), 4)
        d["total_engagement"] = eng
        results.append(d)
    return results


# ── CLI Interface ──────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MAD Content Farm — Content Performance Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # log
    log_p = sub.add_parser("log", help="Log a new post")
    log_p.add_argument("--platform", required=True, choices=["douyin", "xiaohongshu", "tiktok", "kuaishou"])
    log_p.add_argument("--niche", required=True)
    log_p.add_argument("--format", default="short_video")
    log_p.add_argument("--caption", default="")
    log_p.add_argument("--file-path", default="")
    log_p.add_argument("--tags", nargs="*", default=[])
    log_p.add_argument("--shortlink-id", default="")
    log_p.add_argument("--shortlink-url", default="")

    # update
    upd_p = sub.add_parser("update", help="Update metrics for a post")
    upd_p.add_argument("--post-id", required=True)
    upd_p.add_argument("--views", type=int)
    upd_p.add_argument("--likes", type=int)
    upd_p.add_argument("--comments", type=int)
    upd_p.add_argument("--shares", type=int)
    upd_p.add_argument("--followers", type=int)
    upd_p.add_argument("--collections", type=int)
    upd_p.add_argument("--click-through", type=int)
    upd_p.add_argument("--completion-rate", type=float)
    upd_p.add_argument("--avg-watch-time", type=float)

    # snapshot
    snap_p = sub.add_parser("snapshot", help="Add daily snapshot")
    snap_p.add_argument("--post-id", required=True)
    snap_p.add_argument("--date", default="")
    snap_p.add_argument("--views", type=int, default=0)
    snap_p.add_argument("--likes", type=int, default=0)
    snap_p.add_argument("--comments", type=int, default=0)
    snap_p.add_argument("--shares", type=int, default=0)
    snap_p.add_argument("--followers", type=int, default=0)

    # list
    lst_p = sub.add_parser("list", help="List recent posts")
    lst_p.add_argument("--limit", type=int, default=20)
    lst_p.add_argument("--platform")
    lst_p.add_argument("--niche")
    lst_p.add_argument("--days", type=int)

    # summary
    sum_p = sub.add_parser("summary", help="Show performance summary")
    sum_p.add_argument("--days", type=int, default=7)
    sum_p.add_argument("--niche")
    sum_p.add_argument("--platform")

    # niches
    sub.add_parser("niches", help="Show per-niche performance")

    # export
    exp_p = sub.add_parser("export", help="Export data for Oransim")
    exp_p.add_argument("--format", choices=["json", "csv"], default="json")
    exp_p.add_argument("--output", default="")
    exp_p.add_argument("--days", type=int, default=30)

    # demo — seed sample data
    sub.add_parser("demo", help="Seed demo data for testing")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    conn = get_connection()

    if args.command == "log":
        post_id = log_post(
            conn,
            platform=args.platform,
            niche=args.niche,
            format=args.format,
            caption=args.caption,
            file_path=args.file_path,
            tags=args.tags,
            shortlink_id=args.shortlink_id,
            shortlink_url=args.shortlink_url,
        )
        print(f"✅ Logged post: {post_id}")

    elif args.command == "update":
        update_metrics(
            conn,
            post_id=args.post_id,
            views=args.views,
            likes=args.likes,
            comments=args.comments,
            shares=args.shares,
            followers=args.followers,
            collections=args.collections,
            click_through=args.click_through,
            completion_rate=args.completion_rate,
            avg_watch_time=args.avg_watch_time,
        )
        print(f"✅ Updated metrics for {args.post_id}")

    elif args.command == "snapshot":
        add_snapshot(
            conn,
            post_id=args.post_id,
            snapshot_date=args.date or None,
            views=args.views,
            likes=args.likes,
            comments=args.comments,
            shares=args.shares,
            followers=args.followers,
        )
        print(f"✅ Snapshot added for {args.post_id}")

    elif args.command == "list":
        posts = list_posts(
            conn,
            limit=args.limit,
            platform=args.platform,
            niche=args.niche,
            days=args.days,
        )
        if not posts:
            print("No posts found.")
        else:
            for p in posts:
                eng_rate = round(
                    (p.get("likes", 0) + p.get("comments", 0) + p.get("shares", 0))
                    / max(p.get("views", 1), 1),
                    4,
                )
                print(
                    f"  [{p['platform']}] {p['niche']:12s} | "
                    f"views={p.get('views', 0):>8,} | "
                    f"likes={p.get('likes', 0):>6,} | "
                    f"eng={eng_rate:.2%} | "
                    f"{p['posted_at'][:10]} | "
                    f"{p['post_id'][:8]}"
                )

    elif args.command == "summary":
        s = get_summary(conn, days=args.days, niche=args.niche, platform=args.platform)
        print(f"\n📊 Performance Summary (last {args.days} days)")
        print(f"   Posts:        {s.get('total_posts', 0)}")
        print(f"   Total Views:  {s.get('total_views', 0):,}")
        print(f"   Total Likes:  {s.get('total_likes', 0):,}")
        print(f"   Comments:     {s.get('total_comments', 0):,}")
        print(f"   Shares:       {s.get('total_shares', 0):,}")
        print(f"   Followers:    {s.get('total_followers', 0):,}")
        print(f"   Eng. Rate:    {s.get('engagement_rate', 0):.2%}")

    elif args.command == "niches":
        niches = get_niche_performance(conn, days=args.days if hasattr(args, "days") else 7)
        print(f"\n🏷️  Niche Performance (last 7 days)")
        for n in niches:
            print(
                f"   {n['niche']:12s} | posts={n['post_count']:>3} | "
                f"views={n['total_views']:>10,} | "
                f"eng={n['engagement_rate']:.2%}"
            )

    elif args.command == "export":
        data = export_for_oransim(conn, days=args.days)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if args.format == "json":
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                import csv
                if data:
                    with open(out_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            print(f"✅ Exported {len(data)} records to {args.output}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.command == "demo":
        _seed_demo_data(conn)

    conn.close()


def _seed_demo_data(conn: sqlite3.Connection) -> None:
    """Seed sample data for testing."""
    import random

    platforms = ["douyin", "xiaohongshu", "tiktok"]
    niches = ["fitness", "cooking", "tech", "lifestyle", "finance"]
    formats = ["short_video", "carousel", "long_video"]

    now = datetime.now(timezone.utc)
    count = 0
    for i in range(30):
        platform = random.choice(platforms)
        niche = random.choice(niches)
        fmt = random.choice(formats)
        posted_at = (now - timedelta(hours=random.randint(1, 168))).isoformat()
        post_id = log_post(
            conn,
            platform=platform,
            niche=niche,
            format=fmt,
            caption=f"Sample {niche} content #{i+1}",
            posted_at=posted_at,
        )
        # Simulate metrics with some variance by niche
        base_views = random.randint(500, 50000)
        if niche == "fitness":
            base_views = int(base_views * 1.3)  # fitness performs better
        elif niche == "finance":
            base_views = int(base_views * 0.7)  # finance lower reach

        eng_rate = random.uniform(0.02, 0.15)
        likes = int(base_views * eng_rate * 0.6)
        comments = int(base_views * eng_rate * 0.25)
        shares = int(base_views * eng_rate * 0.15)
        followers = int(random.uniform(0.001, 0.01) * base_views)

        update_metrics(
            conn,
            post_id=post_id,
            views=base_views,
            likes=likes,
            comments=comments,
            shares=shares,
            followers=followers,
            completion_rate=random.uniform(0.2, 0.8),
            avg_watch_time=random.uniform(3, 45),
        )
        count += 1

    print(f"✅ Seeded {count} demo posts with metrics")


if __name__ == "__main__":
    main()
