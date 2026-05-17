# Infrastructure Status — Content Farm

> **Written by:** Infrastructure Lead (Subagent)
> **Last Updated:** 2026-05-17 06:15 EST
> **Status:** ✅ Infrastructure Ready

---

## What's Built

### 1. CivitAI Scraper (`scripts/civitai_scraper.py`)
- **Status:** ✅ Complete
- **What it does:** Scrapes trending images from CivitAI API, downloads with full metadata
- **Features:**
  - Supports all NSFW levels: sfw, soft, mature, x
  - Sort by Most Reactions, Newest, Most Downloaded, etc.
  - Pagination support for bulk downloads
  - Rate limiting (1 req/s default, configurable)
  - Saves metadata (prompt, seed, stats, tags) alongside each image
  - Saves prompts separately for easy access
  - Trending snapshot mode for daily tracking
  - Deduplication (skips already-downloaded images)
- **Output:** `data/civitai/images/{sfw|soft|mature|x}/`
- **Config needed:** `config/civitai-token.json` (API token from civitai.com)

### 2. Remix Pipeline (`scripts/remix_pipeline.py`)
- **Status:** ✅ Complete
- **What it does:** Batch processes images into platform-specific formats
- **Platform specs:**
  - TikTok: 1080x1920 (9:16)
  - Instagram: 1080x1080 (1:1) and 1080x1350 (4:5)
  - X/Twitter: 1200x675 (16:9)
  - Reddit: keeps original aspect, caps at 2048px
- **Features:**
  - Center-crop or letterbox padding
  - Watermark support (image PNG or text overlay)
  - Filter presets: warm, cool, vivid, muted, contrast, bright, dark, sharp, blur
  - Carousel split (wide images → multi-slide for IG/TikTok)
  - Batch processing from directory
- **Output:** `output/{platform}/{nsfw_level}/`

### 3. Posting Queue (`scripts/posting_queue.py`)
- **Status:** ✅ Complete
- **What it does:** Manages scheduled content distribution across platforms
- **Features:**
  - Add single files or batch directories
  - Priority system (1-10)
  - Platform rotation support
  - Deduplication tracking (SHA256 hash per file per platform)
  - Post logging to `logs/posts.jsonl`
  - Queue persistence in `data/posting-queue.json`
  - Stats and pending views
- **Data files:**
  - Queue: `data/posting-queue.json`
  - Post log: `logs/posts.jsonl`
  - Dedup: `data/posted-hashes.json`

### 4. Farm Status Dashboard (`scripts/farm_status.py`)
- **Status:** ✅ Complete
- **What it does:** Monitors and reports on farm state
- **Metrics tracked:**
  - Images downloaded (by NSFW level)
  - Images processed/remixed (by platform)
  - Queue depth (pending/posted)
  - Post log stats (total, 24h, by platform)
  - Engagement totals (likes, shares, comments, views)
  - Pipeline conversion rates
  - Trending snapshot availability
- **Output:** Console report or saved to `logs/daily_report_{date}.md`
- **Watch mode:** Auto-refreshes every 60s

### 5. Config Template (`config/civitai-token.json`)
- **Status:** ✅ Created (needs user token)
- **Action required:** Replace `YOUR_CIVITAI_API_TOKEN_HERE` with actual token

---

## Directory Structure

```
content-farm/
├── scripts/
│   ├── civitai_scraper.py      # Image scraper
│   ├── remix_pipeline.py        # Batch image processor
│   ├── posting_queue.py         # Queue manager
│   └── farm_status.py           # Dashboard
├── config/
│   ├── civitai-token.json       # API token (needs filling)
│   ├── accounts.json            # Existing account config
│   ├── analytics.yaml
│   ├── content.yaml
│   └── crawler.yaml
├── data/
│   ├── civitai/
│   │   ├── images/
│   │   │   ├── sfw/             # Safe content
│   │   │   ├── soft/            # Mild NSFW
│   │   │   ├── mature/          # Moderate NSFW
│   │   │   └── x/               # Explicit
│   │   ├── prompts/             # Extracted prompts
│   │   └── trending/            # Daily snapshots
│   ├── posting-queue.json       # Queue state
│   └── posted-hashes.json       # Dedup tracking
├── output/
│   ├── tiktok/                  # 1080x1920
│   ├── instagram/               # 1080x1080 / 1080x1350
│   ├── twitter/                 # 1200x675
│   └── reddit/                  # Various
├── logs/
│   ├── posts.jsonl              # Post history
│   └── daily_report_*.md        # Generated reports
└── coordination/
    ├── infra-status.md          # This file
    └── content-status.md        # Written by Content Operator
```

---

## Dependencies

- Python 3.12+
- `requests` (installed)
- `Pillow` (installed)

All scripts use only standard library + requests + Pillow.

---

## Next Steps (Pending Operator)

1. **Add CivitAI API token** to `config/civitai-token.json`
2. **Run initial scrape:** `python scripts/civitai_scraper.py --sort "Most Reactions" --nsfw x --pages 5`
3. **Run remix:** `python scripts/remix_pipeline.py --input data/civitai/images/x --platform tiktok`
4. **Queue content:** `python scripts/posting_queue.py --add-batch output/tiktok --platform tiktok`
5. **Coordinate with Content Operator** for captions, hashtags, and posting decisions

---

## Notes for Content Operator

- All scripts are CLI-runnable and modular
- Each script does one thing — chain them in pipeline order
- Metadata JSON files alongside images contain prompts, seeds, stats
- Prompts are also extracted to `data/civitai/prompts/` for easy reading
- The posting queue tracks what's been posted where — no duplicates
- Watermark and filter options available in remix pipeline
- Carousel split available for Instagram/TikTok
