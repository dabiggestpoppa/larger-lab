#!/usr/bin/env python3
"""
CivitAI Scraper — Content Farm Image Accumulator

Scrapes trending images from CivitAI API, downloads them with metadata,
and organizes by NSFW level.

Usage:
    python civitai_scraper.py --sort "Most Reactions" --nsfw X --pages 5 --limit 100
    python civitai_scraper.py --sort Newest --nsfw None --pages 10
    python civitai_scraper.py --trending-snapshot

Config:
    API token read from: ../config/civitai-token.json
    Output base:        ../data/civitai/

Rate limit: 1 request/second (configurable)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FARM_DIR = SCRIPT_DIR.parent
CONFIG_FILE = FARM_DIR / "config" / "civitai-token.json"
OUTPUT_BASE = FARM_DIR / "data" / "civitai"
IMAGES_DIR = OUTPUT_BASE / "images"
PROMPTS_DIR = OUTPUT_BASE / "prompts"
TRENDING_DIR = OUTPUT_BASE / "trending"
LOGS_DIR = FARM_DIR / "logs"

for d in [IMAGES_DIR, PROMPTS_DIR, TRENDING_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

NSFW_LEVELS = ["sfw", "soft", "mature", "x"]
BASE_URL = "https://civitai.com/api/v1"
DEFAULT_RATE_LIMIT = 1.0  # seconds between requests

# NSFW query param mapping
NSFW_PARAM = {
    "sfw": "None",
    "soft": "Soft",
    "mature": "Mature",
    "x": "X",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_token() -> str:
    """Load API token from config file."""
    if not CONFIG_FILE.exists():
        print(f"ERROR: Token config not found at {CONFIG_FILE}")
        print("Create it with: {\"api_token\": \"YOUR_CIVITAI_TOKEN\"}")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    token = cfg.get("api_token", "").strip()
    if not token:
        print("ERROR: Empty api_token in config file.")
        sys.exit(1)
    return token


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "ContentFarm-Scraper/1.0",
    }


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Make a safe filename from arbitrary string."""
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    safe = safe.strip().replace(" ", "_")
    return safe[:max_len]


def download_image(url: str, dest: Path, retries: int = 3) -> bool:
    """Download an image with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=30, stream=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
        except Exception as e:
            if attempt < retries:
                time.sleep(2 * attempt)
            else:
                print(f"  FAILED download after {retries} attempts: {e}")
                return False
    return False


# ---------------------------------------------------------------------------
# Core scraping
# ---------------------------------------------------------------------------

def scrape_images(
    token: str,
    sort: str = "Most Reactions",
    nsfw_level: str = "x",
    pages: int = 10,
    limit: int = 100,
    rate_limit: float = DEFAULT_RATE_LIMIT,
) -> dict:
    """
    Scrape images from CivitAI API.

    Returns stats dict with counts of downloaded/skipped/failed.
    """
    headers = get_headers(token)
    nsfw_param = NSFW_PARAM.get(nsfw_level, "X")
    dest_dir = IMAGES_DIR / nsfw_level
    dest_dir.mkdir(parents=True, exist_ok=True)

    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "total": 0}

    for page in range(1, pages + 1):
        print(f"[Page {page}/{pages}] sort={sort} nsfw={nsfw_level} ...")
        try:
            resp = requests.get(
                f"{BASE_URL}/images",
                params={
                    "sort": sort,
                    "nsfw": nsfw_param,
                    "limit": limit,
                    "page": page,
                },
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                print("ERROR: Invalid API token. Check config/civitai-token.json")
                sys.exit(1)
            print(f"  HTTP error on page {page}: {e}")
            stats["failed"] += limit
            continue
        except Exception as e:
            print(f"  Request error on page {page}: {e}")
            stats["failed"] += limit
            continue

        items = data.get("items", [])
        if not items:
            print(f"  No more items on page {page}. Stopping.")
            break

        for img in items:
            stats["total"] += 1
            img_id = img.get("id", "unknown")
            img_url = img.get("url", "")

            if not img_url:
                print(f"  [#{img_id}] No URL, skipping.")
                stats["skipped"] += 1
                continue

            # Determine file extension
            ext = ".png"  # default
            if "." in img_url.split("?")[0].split("/")[-1]:
                parsed_ext = img_url.split("?")[0].rsplit(".", 1)[-1].lower()
                if parsed_ext in ("jpg", "jpeg", "png", "webp", "gif"):
                    ext = f".{parsed_ext}"

            filename = f"civitai_{img_id}{ext}"
            img_path = dest_dir / filename

            # Skip if already downloaded
            if img_path.exists():
                print(f"  [#{img_id}] Already exists, skipping.")
                stats["skipped"] += 1
                continue

            # Download image
            print(f"  [#{img_id}] Downloading {ext} ...")
            if download_image(img_url, img_path):
                # Save metadata alongside
                meta = {
                    "id": img_id,
                    "url": img_url,
                    "source": "civitai",
                    "nsfw_level": nsfw_level,
                    "sort": sort,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "prompt": img.get("meta", {}).get("prompt", ""),
                    "negative_prompt": img.get("meta", {}).get("negativePrompt", ""),
                    "seed": img.get("meta", {}).get("seed"),
                    "model": img.get("meta", {}).get("Model", ""),
                    "sampler": img.get("meta", {}).get("sampler", ""),
                    "steps": img.get("meta", {}).get("steps"),
                    "cfg_scale": img.get("meta", {}).get("cfgScale"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "stats": {
                        "likes": img.get("stats", {}).get("likeCount", 0),
                        "heart": img.get("stats", {}).get("heartCount", 0),
                        "laugh": img.get("stats", {}).get("laughCount", 0),
                        "cry": img.get("stats", {}).get("cryCount", 0),
                        "comment": img.get("stats", {}).get("commentCount", 0),
                        "tip": img.get("stats", {}).get("tippedAmountCount", 0),
                    },
                    "tags": [t.get("name", "") for t in img.get("tags", [])],
                    "model_id": img.get("modelId"),
                    "post_id": img.get("postId"),
                    "username": img.get("username", ""),
                }
                meta_path = dest_dir / f"civitai_{img_id}.json"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)

                # Also save prompt separately for easy access
                if meta["prompt"]:
                    prompt_path = PROMPTS_DIR / f"civitai_{img_id}.txt"
                    with open(prompt_path, "w", encoding="utf-8") as f:
                        f.write(meta["prompt"])

                stats["downloaded"] += 1
            else:
                stats["failed"] += 1

            time.sleep(rate_limit)

        # Pagination: check if there's a next page
        metadata = data.get("metadata", {})
        next_page = metadata.get("nextPage")
        if not next_page or next_page <= page:
            print(f"  No more pages after {page}. Stopping.")
            break

        time.sleep(rate_limit)

    return stats


def take_trending_snapshot(token: str, rate_limit: float = DEFAULT_RATE_LIMIT):
    """Take a snapshot of current trending across all NSFW levels."""
    headers = get_headers(token)
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "levels": {},
    }

    for level, param in NSFW_PARAM.items():
        print(f"[Trending Snapshot] nsfw={level} ...")
        try:
            resp = requests.get(
                f"{BASE_URL}/images",
                params={"sort": "Most Reactions", "nsfw": param, "limit": 20, "page": 1},
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            snapshot["levels"][level] = [
                {
                    "id": img.get("id"),
                    "url": img.get("url"),
                    "likes": img.get("stats", {}).get("likeCount", 0),
                    "hearts": img.get("stats", {}).get("heartCount", 0),
                    "prompt": img.get("meta", {}).get("prompt", "")[:200],
                    "username": img.get("username", ""),
                }
                for img in items
            ]
        except Exception as e:
            print(f"  Error fetching {level}: {e}")
            snapshot["levels"][level] = []

        time.sleep(rate_limit)

    # Save snapshot
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snap_path = TRENDING_DIR / f"trending_{ts}.json"
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    print(f"Snapshot saved: {snap_path}")
    return snapshot


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CivitAI Scraper — Download trending images for content farm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python civitai_scraper.py --sort "Most Reactions" --nsfw x --pages 5
  python civitai_scraper.py --sort Newest --nsfw sfw --pages 10 --limit 50
  python civitai_scraper.py --trending-snapshot
  python civitai_scraper.py --all-levels --sort "Most Reactions" --pages 3
        """,
    )
    parser.add_argument("--sort", default="Most Reactions",
                        help="Sort order: Most Reactions, Newest, Most Downloaded, etc.")
    parser.add_argument("--nsfw", default="x", choices=NSFW_LEVELS,
                        help="NSFW level to scrape (default: x)")
    parser.add_argument("--pages", type=int, default=5,
                        help="Number of pages to scrape (default: 5)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Items per page, max 100 (default: 100)")
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT,
                        help=f"Seconds between requests (default: {DEFAULT_RATE_LIMIT})")
    parser.add_argument("--trending-snapshot", action="store_true",
                        help="Take a trending snapshot across all NSFW levels")
    parser.add_argument("--all-levels", action="store_true",
                        help="Scrape all NSFW levels sequentially")

    args = parser.parse_args()
    token = load_token()

    print("=" * 60)
    print("  CivitAI Scraper — Content Farm")
    print("=" * 60)

    if args.trending_snapshot:
        snapshot = take_trending_snapshot(token, args.rate_limit)
        print("\nSnapshot complete.")
        return

    if args.all_levels:
        total_stats = {"downloaded": 0, "skipped": 0, "failed": 0, "total": 0}
        for level in NSFW_LEVELS:
            print(f"\n{'='*40}\n  Scraping NSFW level: {level}\n{'='*40}")
            stats = scrape_images(token, args.sort, level, args.pages, args.limit, args.rate_limit)
            for k in total_stats:
                total_stats[k] += stats.get(k, 0)
        stats = total_stats
    else:
        stats = scrape_images(token, args.sort, args.nsfw, args.pages, args.limit, args.rate_limit)

    print("\n" + "=" * 60)
    print("  Scrape Complete")
    print(f"  Downloaded : {stats['downloaded']}")
    print(f"  Skipped    : {stats['skipped']}")
    print(f"  Failed     : {stats['failed']}")
    print(f"  Total seen : {stats['total']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
