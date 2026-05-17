# CivitAI — Content Farm Integration Plan

> **Source:** https://github.com/civitai/civitai (open-source, public use)
> **API:** https://civitai.com/api/v1/
> **Strategy:** Copy 80% → Remix 50% → Original 10-20%

## What CivitAI Gives Us

- **Millions of AI-generated images** — PG to XXX, all categories
- **Model ecosystem** — checkpoints, LoRAs, embeddings, VAEs
- **Prompt metadata** — every image has generation params (prompt, seed, sampler)
- **Trending signals** — download counts, likes, comments show what's hot
- **Open-source platform** — we can study their entire stack
- **API access** — structured endpoints for bulk access
- **No content creation needed** — it's all already there

## The Play: Accumulate → Remix → Push

### Phase 1: Scrape & Accumulate (Week 1)
```
CivitAI API → Download trending images → Organize by category/NSFW level
```

**Endpoints to use:**
- `GET /api/v1/images?sort=Most Reactions&limit=100&nsfw=X` — top NSFW content
- `GET /api/v1/images?sort=Newest&limit=100` — fresh content
- `GET /api/v1/models?query=nsfw&sort=Most Downloaded` — popular NSFW models
- `GET /api/v1/models/{id}` → get model files + preview images

**Tools to use:**
- Confuzu's CivitAI Image Grabber: https://github.com/Confuzu/CivitAI_Image_grabber
- Confuzu's CivitAI Model Grabber: https://github.com/Confuzu/CivitAI-Model-grabber
- Or write custom Python scraper (see below)

**Storage structure:**
```
content-farm/data/civitai/
├── images/
│   ├── sfw/           # Safe content
│   ├── soft/          # Mild NSFW
│   ├── mature/        # Moderate NSFW
│   └── x/             # Explicit
├── models/            # Downloaded model files
├── prompts/           # Extracted prompt metadata
└── trending/          # Daily trending snapshots
```

### Phase 2: Remix Pipeline (Week 2)
```
Raw CivitAI content → Edit → Repackage → Ready to post
```

**Remix operations:**
- Crop / resize for platform specs (TikTok 9:16, IG 1:1, X 16:9)
- Add watermarks / branding
- Apply filters / color grading
- Combine multiple images into carousels
- Extract and rewrite prompts for our own generations
- Create "before/after" or "prompt breakdown" content

**Tools:**
- Python PIL/Pillow for batch image processing
- FFmpeg for video content
- Existing MoneyPrinterPlus for video generation
- DeekeScript for mobile posting

### Phase 3: Push to Platforms (Ongoing)
```
Remixed content → Platform-specific formatting → Auto-post via DeekeScript
```

**Platform strategy:**
- **TikTok:** Short-form video + image carousels, trending sounds
- **Instagram:** Reels + carousels + stories
- **X/Twitter:** Image threads + engagement bait
- **Reddit:** NSFW subreddits (huge organic reach)
- **OnlyFans/Fansly:** Premium content funnel
- **Pinterest:** Evergreen image traffic

### Phase 4: Loop (Continuous)
```
Post → Track performance → Double down on winners → Recycle burnt content
```

**When something works:**
- Front-load that content type
- Create variations on the winning theme
- Push across all platforms
- Once engagement drops (burnt), move to next winner
- Keep the chain going — always testing, always pushing

## API Token Setup

1. Create CivitAI account: https://civitai.com
2. Go to: https://civitai.com/user/account
3. Generate API token
4. Store in `content-farm/config/civitai-token.json`

## Quick Scraper Script

```python
# content-farm/scripts/civitai_scraper.py
import requests, json, time, os
from pathlib import Path

TOKEN = "YOUR_TOKEN"
BASE = "https://civitai.com/api/v1"
OUT = Path("content-farm/data/civitai/images")
OUT.mkdir(parents=True, exist_ok=True)

def scrape_images(sort="Most Reactions", nsfw="X", pages=10):
    for page in range(1, pages + 1):
        r = requests.get(f"{BASE}/images", params={
            "sort": sort, "nsfw": nsfw, "limit": 100, "page": page
        }, headers={"Authorization": f"Bearer {TOKEN}"})
        data = r.json()
        for img in data.get("items", []):
            # Download image, save metadata
            pass
        time.sleep(1)  # Rate limit
```

## Existing Tools to Leverage

| Tool | How It Helps |
|------|-------------|
| DeekeScript | Auto-post to TikTok, XHS, Kuaishou |
| MediaCrawler | Scrape additional content from other platforms |
| Spider_XHS | Xiaohongshu content + now CivitAI |
| MoneyPrinterPlus | Generate video content from images |
| Scrapling | Web scraping for additional sources |
| Violin | Translate Chinese content for Western platforms |
| Oransim | ROI prediction — which content types to focus on |

## Content Verticals to Test

1. **AI Art Showcase** — "Best AI art of the week" carousels
2. **Prompt Breakdowns** — "How this image was made" educational content
3. **Model Reviews** — "I tested X AI model for 30 days"
4. **NSFW (where allowed)** — Reddit, X, dedicated platforms
5. **Before/After** — Raw generation vs edited/polished
6. **Trending Reactions** — "The AI community is going crazy for this"
7. **Comparison Posts** — Model A vs Model B

## Revenue Funnel

```
Free content (TikTok/IG/X) → Followers → Paid platforms (OF/Fansly)
                         → Traffic → Affiliate links (AI tools, courses)
                         → Engagement → Sponsorship deals
```

## Next Steps

1. [ ] Create CivitAI account + API token
2. [ ] Clone Confuzu's Image Grabber
3. [ ] Run initial scrape: top 1000 NSFW images + metadata
4. [ ] Set up remix pipeline (crop, watermark, format)
5. [ ] Connect to DeekeScript posting automation
6. [ ] Test on 2-3 platforms, measure engagement
7. [ ] Scale what works, kill what doesn't
