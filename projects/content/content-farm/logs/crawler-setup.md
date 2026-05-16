# Content Farm — Crawler Setup Summary

**Date:** 2026-05-16  
**Agent:** OWL (Research Lead)  
**Status:** ✅ Dry-run complete — scripts verified, no live crawls executed

---

## What Was Built

### 1. `content-farm/config/crawler.yaml`

Unified configuration file for all crawler backends:

- **Backend selection:** MediaCrawler (7 platforms) and Spider_XHS (XHS-dedicated)
- **Per-platform defaults:** keywords, crawl limits, comment settings, sort order, output format
- **Proxy settings:** provider, pool count, rotation interval
- **Rate limiting:** concurrency, request delay, daily max requests

**Default keywords per platform:**

| Platform   | Keywords (Chinese)                                  |
|------------|-----------------------------------------------------|
| 小红书     | 健身, 美食, 科技, 生活方式, 理财                    |
| 抖音       | 健身教程, 美食制作, 科技数码, 生活技巧, 财经知识    |
| 快手       | 健身, 美食, 科技                                    |

### 2. `content-farm/scripts/unified_crawler.py`

Unified orchestrator script that:

- **Accepts CLI args:** `--platform`, `--keywords`, `--limit`, `--backend`, `--dry-run`
- **Supports platforms:** douyin, xiaohongshu, kuaishou, bilibili, weibo, tieba, zhihu, all
- **Auto-selects backend:** MediaCrawler for most platforms; Spider_XHS optional for XHS
- **Saves output to:** `content-farm/output/YYYY-MM-DD/<backend>_<platform>/`
- **Writes manifests:** JSON files alongside output documenting what was requested
- **Logs to:** `content-farm/logs/crawler_YYYYMMDD_HHMMSS.log`
- **Writes summaries:** `content-farm/logs/summary_YYYYMMDD_HHMMSS.json`

### 3. Backend Details

#### MediaCrawler (`MediaCrawler/`)

- **How it runs:** `uv run main.py --platform <code> --lt qrcode --type search --keywords <kw>`
- **Platform codes:** xhs, dy, ks, bili, wb, tieba, zhihu
- **Auth:** QR code scan (default), phone, or cookie
- **Output formats:** json, csv, sqlite, db (MySQL)
- **Features:** comments, sub-comments, proxy pool, CDP mode, word cloud
- **Dependencies:** Python 3.9+, uv, Node.js 16+, Playwright

#### Spider_XHS (`Spider_XHS/`)

- **How it runs:** Python `Data_Spider` class with `spider_some_search_note()` method
- **Auth:** Cookie-based (from `.env` file)
- **Output formats:** Excel (.xlsx), media files (images/videos)
- **Features:** user notes, search, comments, creator platform APIs, no watermark media
- **Dependencies:** Python 3.7+, Node.js 18+, `pip install -r requirements.txt`, `npm install`

---

## Dry-Run Test Results

### Test 1: Single platform (douyin) via MediaCrawler
```
python unified_crawler.py --dry-run --platform douyin --keywords "健身教程" --limit 5
```
✅ Command: `uv run main.py --platform dy --lt qrcode --type search --keywords 健身教程 --start 1 --get_comment true --save_data_option json`  
✅ Output dir: `output/2026-05-16/media_crawler_douyin/`  
✅ Manifest written

### Test 2: XHS via Spider_XHS backend
```
python unified_crawler.py --dry-run --platform xiaohongshu --keywords "美食" --backend spider_xhs --limit 3
```
✅ Command: `python Spider_XHS/_farm_runner.py` (auto-generated runner)  
✅ Output dir: `output/2026-05-16/spider_xhs_xiaohongshu/`  
✅ Manifest written

### Test 3: Multi-platform (all)
```
python unified_crawler.py --dry-run --platform all --limit 2
```
✅ Dispatched to 3 platforms: douyin, xiaohongshu, kuaishou  
✅ All keywords loaded from config.yaml  
✅ 3 output dirs created with manifests

---

## Usage Examples

```bash
# Crawl douyin for fitness content (live run)
python content-farm/scripts/unified_crawler.py --platform douyin --keywords "健身教程" --limit 20

# Crawl XHS using the dedicated spider
python content-farm/scripts/unified_crawler.py --platform xiaohongshu --keywords "美食探店" --backend spider_xhs --limit 10

# Crawl all platforms with config defaults
python content-farm/scripts/unified_crawler.py --platform all

# Dry run to verify commands
python content-farm/scripts/unified_crawler.py --dry-run --platform kuaishou --keywords "科技" --limit 5
```

---

## File Structure

```
content-farm/
├── config/
│   ├── accounts.json          # Existing: account/device/proxy config
│   └── crawler.yaml           # NEW: unified crawler configuration
├── scripts/
│   ├── dy_auto_engage.js      # Existing: Douyin engagement script
│   ├── xhs_auto_engage.js     # Existing: XHS engagement script
│   └── unified_crawler.py     # NEW: unified crawler orchestrator
├── output/
│   └── 2026-05-16/            # Created by crawler runs
│       ├── media_crawler_douyin/
│       │   └── manifest.json
│       ├── media_crawler_xiaohongshu/
│       │   └── manifest.json
│       ├── media_crawler_kuaishou/
│       │   └── manifest.json
│       └── spider_xhs_xiaohongshu/
│           └── manifest.json
└── logs/
    ├── crawler_20260516_122754.log
    ├── summary_20260516_122754.json
    └── crawler-setup.md       # THIS FILE
```

---

## Next Steps (Before Live Crawls)

1. **Configure accounts:** Fill in `accounts.json` with actual platform credentials
2. **Set up proxies:** Enable proxy in `crawler.yaml` and configure provider
3. **Install MediaCrawler deps:** `cd MediaCrawler && uv sync && uv run playwright install`
4. **Install Spider_XHS deps:** `cd Spider_XHS && pip install -r requirements.txt && npm install`
5. **Set XHS cookies:** Add cookies to `Spider_XHS/.env` (F12 → Network → copy cookie header)
6. **Test login:** Run MediaCrawler once manually to cache login state via QR scan
7. **Start small:** Run with `--limit 5` first to verify everything works end-to-end

---

## Notes

- MediaCrawler uses Playwright (browser automation) — first run requires QR code scan
- Spider_XHS uses direct API calls — requires valid cookies in `.env`
- Both crawlers respect rate limits configured in `crawler.yaml`
- The unified script does NOT modify the original crawler code — it only orchestrates them
- All output is organized by date for easy tracking
