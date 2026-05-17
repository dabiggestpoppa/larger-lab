# MAD Content Farm — Project Hub

> **Philosophy:** Systematic scale over creative perfection. Law of numbers.
> **Edge:** Chinese automation tools (free) + OpenClaw orchestration + AI translation

---

## Quick Start

### 1. Android Emulator Setup
```bash
# Install BlueStacks 5 or LDPlayer 9
# Download from: https://www.bluestacks.com or https://www.ldplayer.net

# Configure emulator:
# - Android 11 (API 30)
# - Resolution: 1080x1920
# - RAM: 2GB per instance
# - Enable ADB debugging
```

### 2. DeekeScript Installation
```bash
# Install DeekeScript APK on emulator
# Copy scripts from content-farm/scripts/ to device
# Configure deekeScript.json with your settings
```

### 3. First Automation
```bash
# Deploy dy_auto_engage.js to emulator
# Run via DeekeScript runtime
# Monitor logs in content-farm/logs/
```

---

## Project Structure
```
content-farm/
├── scripts/          # DeekeScript automation scripts
│   ├── dy_auto_engage.js      # 抖音 auto-engagement
│   ├── dy_auto_post.js        # 抖音 auto-posting (TODO)
│   ├── xhs_auto_engage.js     # 小红书 auto-engagement (TODO)
│   └── ks_auto_engage.js      # 快手 auto-engagement (TODO)
├── config/           # Configuration files
│   ├── accounts.json          # Account management
│   └── settings.json          # Farm settings
├── logs/             # Automation logs
├── output/           # Generated content
├── accounts/         # Account credentials (encrypted)
└── templates/        # Content templates
```

---

## CivitAI Integration

**New (2026-05-17):** CivitAI is now our primary content source. Open-source platform with millions of AI-generated images from PG to XXX. We copy 80%, remix 50%, and only produce 10-20% original content.

- **API:** https://civitai.com/api/v1/ (free, just need token)
- **Strategy:** Accumulate → Remix → Push → Loop
- **Plan:** `CIVITAI_INTEGRATION.md`
- **Key insight:** We never start from ground 0. CivitAI is production-grade content we just need to curate and repurpose.

## Tool Stack

| Tool | Role | Location | Status |
|------|------|----------|--------|
| DeekeScript | Android automation | deekescript/ | ✅ Installed |
| ad-deeke | 抖音 engagement | ad-deeke/ | ✅ Cloned |
| ad-dke | 抖音 commercial | ad-dke/ | ✅ Cloned |
| MoneyPrinterPlus | AI video gen | MoneyPrinterPlus/ | ✅ Cloned |
| ad-voice | AI voice cloning | ad-voice/ | ✅ Cloned |
| MediaCrawler | Data collection | MediaCrawler/ | ✅ Cloned |
| Spider_XHS | 小红书 crawler | Spider_XHS/ | ✅ Cloned |
| deeke-uid | Lead generation | deeke-uid/ | ✅ Cloned |
| shortLink | Attribution | shortLink/ | ✅ Cloned |
| GroupControlApp | Device management | GroupControlApp/ | ✅ Cloned |
| Scrapling | Web scraping | Python package | ✅ Installed |
| Violin | Video translation | Python package | ✅ Installed |
| Oransim | ROI prediction | oransim/ | ✅ Installed |
| OpenClaw | Orchestration | Gateway | ✅ Running |

---

## Revenue Targets

| Month | Farms | Accounts | Posts/Day | Revenue |
|-------|-------|----------|-----------|---------|
| 1 | 1 | 50 | 1,000 | $500-2K |
| 2 | 2 | 100 | 3,000 | $2K-5K |
| 3 | 5 | 250 | 8,000 | $5K-15K |
| 6 | 10 | 500 | 20,000 | $15K-50K |
| 12 | 20 | 1,000 | 50,000 | $50K-200K |

---

## Documentation

- **Architecture:** `docs/content-farm-architecture.md`
- **Ecosystem Blueprint:** `docs/deeke-ecosystem-blueprint.md`
- **US vs China Tools:** `docs/us-vs-china-tools.md`
- **Agent Config:** `config/content-farm-agents.yaml`
- **Translation Pipeline:** `config/translation-pipeline.yaml`

---

## CivitAI Infrastructure (Active)

The content farm now has a full CivitAI → Remix → Post pipeline.

### Quick Start

1. **Set up API token:**
   ```bash
   # Edit config/civitai-token.json with your CivitAI API token
   # Get token from: https://civitai.com/user/account → API Keys
   ```

2. **Scrape images:**
   ```bash
   # Scrape trending NSFW images (5 pages, 100 per page)
   python scripts/civitai_scraper.py --sort "Most Reactions" --nsfw x --pages 5

   # Scrape all NSFW levels
   python scripts/civitai_scraper.py --all-levels --sort "Most Reactions" --pages 3

   # Take a trending snapshot
   python scripts/civitai_scraper.py --trending-snapshot
   ```

3. **Remix for platforms:**
   ```bash
   # Process for TikTok (9:16)
   python scripts/remix_pipeline.py --input data/civitai/images/x --platform tiktok

   # Process for Instagram (4:5)
   python scripts/remix_pipeline.py --input data/civitai/images/x --platform instagram --aspect 4:5

   # Process for X/Twitter (16:9) with watermark
   python scripts/remix_pipeline.py --input data/civitai/images/x --platform twitter --watermark-text "@madfarm"

   # Process for Reddit with carousel split
   python scripts/remix_pipeline.py --input data/civitai/images/x --platform reddit --carousel

   # Batch process all levels for TikTok
   python scripts/remix_pipeline.py --batch-all --nsfw x --platform tiktok --filter vivid
   ```

4. **Queue for posting:**
   ```bash
   # Add single image
   python scripts/posting_queue.py --add output/tiktok/image1.jpg --platform tiktok --caption "Amazing art!"

   # Add entire directory
   python scripts/posting_queue.py --add-batch output/tiktok --platform tiktok

   # Check pending
   python scripts/posting_queue.py --pending

   # Mark as posted
   python scripts/posting_queue.py --mark-posted <queue_id> --platform tiktok --url "https://..."

   # View stats
   python scripts/posting_queue.py --stats
   ```

5. **Check farm status:**
   ```bash
   # Quick status
   python scripts/farm_status.py

   # Full report (saved to logs/)
   python scripts/farm_status.py --report --save

   # Live watch
   python scripts/farm_status.py --watch
   ```

### Posting Schedule Template

| Platform | Best Times (EST) | Content Type |
|----------|-----------------|--------------|
| TikTok   | 11:00, 15:00, 20:00 | 9:16 video/images |
| Instagram| 09:00, 12:00, 19:00 | 1:1 / 4:5 carousels |
| X        | 08:00, 12:00, 17:00 | 16:9 images + threads |
| Reddit   | 06:00, 12:00, 18:00 | Various, text + image |

### Platform Accounts Needed

- [ ] TikTok account(s) — phone verified
- [ ] Instagram account(s) — linked to FB
- [ ] X/Twitter account(s) — API access for auto-post
- [ ] Reddit account(s) — aged 30+ days for NSFW subs

### Data Flow

```
CivitAI API
    ↓ scrape
content-farm/data/civitai/images/{sfw|soft|mature|x}/
    ↓ remix
content-farm/output/{tiktok|instagram|twitter|reddit}/
    ↓ queue
content-farm/data/posting-queue.json
    ↓ post (via DeekeScript / manual)
content-farm/logs/posts.jsonl
```

### Coordination

- **Infrastructure status:** `coordination/infra-status.md` (written by Infra Lead)
- **Content status:** `coordination/content-status.md` (written by Content Operator)

---

*MAD Content Farm — Built by OWL 🦉*
