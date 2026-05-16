#!/usr/bin/env python3
"""
Content Farm — Unified Crawler
================================
Orchestrates MediaCrawler and Spider_XHS backends.

Usage:
    python unified_crawler.py --platform douyin --keywords "健身教程" --limit 10
    python unified_crawler.py --platform xiaohongshu --keywords "美食" --backend media_crawler
    python unified_crawler.py --platform xiaohongshu --keywords "美食" --backend spider_xhs
    python unified_crawler.py --platform all --keywords "科技" --limit 5
    python unified_crawler.py --dry-run --platform douyin --keywords "test"

Supported platforms: douyin, xiaohongshu, kuaishou, bilibili, weibo, tieba, zhihu, all
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ── paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
CONTENT_FARM = REPO_ROOT / "content-farm"
CONFIG_FILE = CONTENT_FARM / "config" / "crawler.yaml"
OUTPUT_BASE = CONTENT_FARM / "output"
LOG_DIR = CONTENT_FARM / "logs"

# backends
MEDIA_CRAWLER_DIR = REPO_ROOT / "MediaCrawler"
SPIDER_XHS_DIR = REPO_ROOT / "Spider_XHS"

# ── logging ──────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# On Windows, stdout may not handle CJK — force UTF-8
_stream = sys.stdout
if hasattr(_stream, "reconfigure"):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(_stream),
    ],
)
logger = logging.getLogger("unified_crawler")

# ── helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load crawler.yaml.  Falls back to an empty dict if missing."""
    if not CONFIG_FILE.exists():
        logger.warning("Config file not found: %s — using defaults", CONFIG_FILE)
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def today_dir() -> Path:
    """Return (and create) output/YYYY-MM-DD/."""
    d = OUTPUT_BASE / datetime.now().strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_cmd(cmd: list[str], cwd: Path, dry_run: bool = False) -> subprocess.CompletedProcess | None:
    """Run a subprocess, log it, return result (or None on dry-run)."""
    logger.info("CMD: %s  cwd=%s", " ".join(cmd), cwd)
    if dry_run:
        logger.info("[DRY RUN] skipping execution")
        return None
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            logger.error("STDERR: %s", result.stderr[:2000])
        else:
            logger.info("STDOUT: %s", result.stdout[:1000])
        return result
    except subprocess.TimeoutExpired:
        logger.error("Command timed out after 600 s")
        return None
    except FileNotFoundError as exc:
        logger.error("Executable not found: %s", exc)
        return None


# ── backend: MediaCrawler ────────────────────────────────────────────────────

MEDIA_CRAWLER_PLATFORM_MAP = {
    "xiaohongshu": "xhs",
    "douyin": "dy",
    "kuaishou": "ks",
    "bilibili": "bili",
    "weibo": "wb",
    "tieba": "tieba",
    "zhihu": "zhihu",
}


def run_media_crawler(
    platform: str,
    keywords: str,
    limit: int,
    get_comments: bool,
    save_format: str,
    start_page: int,
    dry_run: bool,
) -> Path | None:
    """Invoke MediaCrawler for a single platform.  Returns output dir or None."""
    mc_platform = MEDIA_CRAWLER_PLATFORM_MAP.get(platform)
    if not mc_platform:
        logger.error("MediaCrawler does not support platform '%s'", platform)
        return None

    out_dir = today_dir() / f"media_crawler_{platform}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build command — MediaCrawler uses `uv run main.py`
    cmd = [
        "uv", "run", "main.py",
        "--platform", mc_platform,
        "--lt", "qrcode",
        "--type", "search",
        "--keywords", keywords,
        "--start", str(start_page),
        "--get_comment", "true" if get_comments else "false",
        "--save_data_option", save_format,
    ]

    logger.info("=== MediaCrawler  platform=%s  keywords=%s  limit=%s ===", platform, keywords, limit)

    # We also write a small manifest so we know what was requested
    manifest = {
        "backend": "media_crawler",
        "platform": platform,
        "mc_platform": mc_platform,
        "keywords": keywords,
        "limit": limit,
        "get_comments": get_comments,
        "save_format": save_format,
        "start_page": start_page,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cmd": " ".join(cmd),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    result = run_cmd(cmd, cwd=MEDIA_CRAWLER_DIR, dry_run=dry_run)
    if result is None and not dry_run:
        return None

    return out_dir


# ── backend: Spider_XHS ─────────────────────────────────────────────────────

def run_spider_xhs(
    keywords: str,
    limit: int,
    dry_run: bool,
) -> Path | None:
    """Invoke Spider_XHS for XHS search.  Returns output dir or None."""
    out_dir = today_dir() / "spider_xhs_xiaohongshu"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Spider_XHS is driven by editing main.py or calling its Data_Spider class.
    # We generate a small runner script and execute it.
    runner = SPIDER_XHS_DIR / "_farm_runner.py"
    runner.write_text(
        f'''#!/usr/bin/env python3
"""Auto-generated runner — do not edit by hand."""
import sys, os
sys.path.insert(0, r"{SPIDER_XHS_DIR}")
os.chdir(r"{SPIDER_XHS_DIR}")

from main import Data_Spider
from xhs_utils.common_util import init

cookies_str, base_path = init()
spider = Data_Spider()

note_list, success, msg = spider.spider_some_search_note(
    query={json.dumps(keywords)},
    require_num={limit},
    cookies_str=cookies_str,
    base_path=base_path,
    save_choice="excel",
    sort_type_choice=0,
    note_type=0,
    note_time=0,
    note_range=0,
    pos_distance=0,
    geo=None,
    excel_name={json.dumps(keywords)},
    proxies=None,
)
print(f"Spider_XHS done: success={{success}}  msg={{msg}}  notes={{len(note_list)}}")
''',
        encoding="utf-8",
    )

    manifest = {
        "backend": "spider_xhs",
        "platform": "xiaohongshu",
        "keywords": keywords,
        "limit": limit,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    cmd = [sys.executable, str(runner)]
    result = run_cmd(cmd, cwd=SPIDER_XHS_DIR, dry_run=dry_run)

    # cleanup runner
    if not dry_run and runner.exists():
        runner.unlink()

    if result is None and not dry_run:
        return None
    return out_dir


# ── main orchestrator ────────────────────────────────────────────────────────

def crawl(
    platform: str,
    keywords: str,
    limit: int,
    backend: str | None,
    dry_run: bool,
    config: dict,
) -> list[Path]:
    """Dispatch to the right backend(s).  Returns list of output dirs."""
    results: list[Path] = []
    platforms_cfg = config.get("platforms", {})

    if platform == "all":
        targets = ["douyin", "xiaohongshu", "kuaishou"]
    else:
        targets = [platform]

    for plat in targets:
        plat_cfg = platforms_cfg.get(plat, {})
        effective_backend = backend or plat_cfg.get("backend", "media_crawler")
        effective_limit = limit or plat_cfg.get("max_notes", 50)
        effective_keywords = keywords or ", ".join(plat_cfg.get("keywords", []))
        get_comments = plat_cfg.get("get_comments", True)
        save_format = plat_cfg.get("save_format", "json")
        start_page = plat_cfg.get("start_page", 1)

        if not effective_keywords:
            logger.warning("No keywords for platform %s — skipping", plat)
            continue

        if plat == "xiaohongshu" and effective_backend == "spider_xhs":
            out = run_spider_xhs(effective_keywords, effective_limit, dry_run)
        else:
            out = run_media_crawler(
                plat, effective_keywords, effective_limit,
                get_comments, save_format, start_page, dry_run,
            )

        if out:
            results.append(out)

    return results


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Content Farm — Unified Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--platform", "-p",
        required=True,
        choices=["douyin", "xiaohongshu", "kuaishou", "bilibili", "weibo", "tieba", "zhihu", "all"],
        help="Target platform (or 'all' for multi-platform)",
    )
    parser.add_argument(
        "--keywords", "-k",
        type=str,
        default="",
        help="Comma-separated keywords (overrides config defaults)",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="Max notes to crawl per platform (overrides config)",
    )
    parser.add_argument(
        "--backend", "-b",
        choices=["media_crawler", "spider_xhs"],
        default=None,
        help="Force a specific backend (auto-selected by default)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    logger.info("=" * 60)
    logger.info("Content Farm — Unified Crawler")
    logger.info("  platform : %s", args.platform)
    logger.info("  keywords : %s", args.keywords or "(from config)")
    logger.info("  limit    : %s", args.limit or "(from config)")
    logger.info("  backend  : %s", args.backend or "(auto)")
    logger.info("  dry_run  : %s", args.dry_run)
    logger.info("=" * 60)

    # Verify backends exist
    if not MEDIA_CRAWLER_DIR.exists():
        logger.error("MediaCrawler directory not found: %s", MEDIA_CRAWLER_DIR)
        sys.exit(1)
    if not SPIDER_XHS_DIR.exists():
        logger.error("Spider_XHS directory not found: %s", SPIDER_XHS_DIR)
        sys.exit(1)

    start = time.time()
    output_dirs = crawl(
        platform=args.platform,
        keywords=args.keywords,
        limit=args.limit,
        backend=args.backend,
        dry_run=args.dry_run,
        config=config,
    )
    elapsed = time.time() - start

    # Summary
    summary = {
        "platform": args.platform,
        "keywords": args.keywords,
        "dry_run": args.dry_run,
        "elapsed_seconds": round(elapsed, 2),
        "output_dirs": [str(d) for d in output_dirs],
        "log_file": str(log_file),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = LOG_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("=" * 60)
    logger.info("Done.  Output dirs: %s", [str(d) for d in output_dirs])
    logger.info("Summary : %s", summary_path)
    logger.info("Log     : %s", log_file)
    logger.info("Elapsed : %.1f s", elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
