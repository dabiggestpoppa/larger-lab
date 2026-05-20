# ⚙️ Content Pipeline — Batch Creation Workflow

> **Date:** 2026-05-19 | **Version:** 1.0
> **Purpose:** Maximize output, minimize daily time investment
> **Target:** 1 week of content in 4 hours (batch day)

---

## 🎯 Pipeline Philosophy

**Batch creation > daily creation.** Instead of creating content every day, we batch-produce a full week of content in one session, then spend the rest of the week on engagement and optimization.

**Time investment:** 4 hours on batch day + 45 min/day engagement = ~7 hours/week total

---

## 📅 Weekly Batch Schedule

### Monday — Prompt Engineering (1 hour)
**Goal:** Create all prompts for the week

| Time | Task | Output |
|------|------|--------|
| 0:00-0:20 | Review trending AI art styles | 5 trending styles identified |
| 0:20-0:40 | Write 15 new prompts (3 per platform per day) | 15 prompts documented |
| 0:40-0:50 | Review and refine prompts | 15 finalized prompts |
| 0:50-1:00 | Organize prompts by day/platform | Weekly prompt sheet |

**Output:** `data/prompts/week-[number]-prompts.md`

### Tuesday — Image Generation (1.5 hours)
**Goal:** Generate all images for the week

| Time | Task | Output |
|------|------|--------|
| 0:00-0:30 | Generate TikTok images (5 videos worth) | 5-10 images |
| 0:30-0:50 | Generate Instagram images (5 posts) | 5-10 images |
| 0:50-1:10 | Generate X/Twitter images (7 tweets) | 7-14 images |
| 1:10-1:20 | Generate Reddit images (2 posts) | 2-4 images |
| 1:20-1:30 | Quality check + select best | All images selected |

**Output:** `output/{platform}/week-[number]-[content-id].png`

### Wednesday — Caption Writing (1 hour)
**Goal:** Write all captions for the week

| Time | Task | Output |
|------|------|--------|
| 0:00-0:15 | Write TikTok captions (10 videos) | 10 captions |
| 0:15-0:30 | Write Instagram captions (5 posts) | 5 captions |
| 0:30-0:45 | Write X/Twitter tweets (14 tweets) | 14 tweets |
| 0:45-0:55 | Write Reddit posts (2 posts) | 2 posts |
| 0:55-1:00 | Add hashtags from rotation sets | All captions hashtagged |

**Output:** `data/captions/week-[number]-captions.md`

### Thursday — Scheduling (30 minutes)
**Goal:** Schedule all content for the week

| Time | Task | Output |
|------|------|--------|
| 0:00-0:10 | Upload to scheduling tool | All content uploaded |
| 0:10-0:20 | Assign captions and hashtags | All captions assigned |
| 0:20-0:25 | Verify posting times | Times confirmed |
| 0:25-0:30 | Test first post | First post verified |

**Output:** All content scheduled in Later/Buffer/Ayrshare

### Friday-Sunday — Engagement Only (45 min/day)
**Goal:** Engage, respond, optimize

| Time | Task | Duration |
|------|------|----------|
| 8:00 AM | Morning engagement sweep | 15 min |
| 12:00 PM | Proactive commenting | 10 min |
| 5:00 PM | Afternoon engagement | 10 min |
| 9:00 PM | Evening sweep + metrics log | 10 min |

---

## 🔄 Content Recycling System

### Tier 1: Direct Repost (Same content, different platform)
- TikTok video → Instagram Reel → YouTube Short
- Instagram carousel → Pinterest pin → X/Twitter thread
- Reddit post → X/Twitter thread → LinkedIn post

### Tier 2: Reformat (Same core, different format)
- Carousel → Thread (each slide = 1 tweet)
- Thread → Carousel (each tweet = 1 slide)
- Video → Carousel (key frames as slides)
- Single image → Story series (zoom into details)

### Tier 3: Remix (Same concept, new execution)
- "Rate This" → "Before/After" → "Tutorial"
- "Comparison" → "Ranking" → "Hot Take"
- "Tutorial" → "Mistake Post" → "Myth Busting"

### Recycling Schedule
| Original Post | Recycle As | When |
|---------------|-----------|------|
| TikTok video | Instagram Reel | Same day |
| Instagram carousel | Pinterest pin | Next day |
| X/Twitter thread | LinkedIn post | Next day |
| Reddit post | Blog post | Within 1 week |
| Best-performing post | Repost with new caption | 30 days later |

---

## 📊 Content Quality Checklist

Before any content is scheduled, it must pass:

### Image Quality
- [ ] Resolution correct for platform (1080x1080 IG, 1080x1920 TikTok, 1200x675 X)
- [ ] No watermarks or artifacts
- [ ] Visually striking (would stop your scroll?)
- [ ] On-brand style and colors
- [ ] Safe for platform (no NSFW on main accounts)

### Caption Quality
- [ ] Hook in first line (curiosity, challenge, or value)
- [ ] CTA included (question, link, or action)
- [ ] Hashtags assigned from rotation set
- [ ] Emoji usage appropriate for platform
- [ ] Length appropriate for platform
- [ ] No typos or grammatical errors

### Strategic Quality
- [ ] Fits the day's theme
- [ ] Aligns with content strategy
- [ ] Includes monetization CTA (where appropriate)
- [ ] Has tracking link (if applicable)
- [ ] Scheduled at optimal time

---

## 🛠 Tool Stack

### Content Generation
| Tool | Use | Cost |
|------|-----|------|
| Midjourney | Primary image generation | $10-30/month |
| Flux 2.0 | Alternative/backup | Free-$10/month |
| Stable Diffusion | Advanced control | Free (local) |
| Runway Gen-4 | Video generation | $15/month |
| Kling 2.0 | Video generation | Free tier |

### Design & Editing
| Tool | Use | Cost |
|------|-----|------|
| Canva AI | Carousels, graphics | Free-$13/month |
| Figma | Custom designs | Free |
| CapCut | Video editing | Free |
| Remove.bg | Background removal | Free tier |

### Scheduling & Publishing
| Tool | Use | Cost |
|------|-----|------|
| Later | IG, TikTok, Pinterest | $15/month |
| Buffer | IG, X, Facebook | $15/month |
| Ayrshare | All-in-one API | Free tier (200 posts) |
| Hootsuite | Enterprise | $29/month |

### Analytics
| Tool | Use | Cost |
|------|-----|------|
| Platform native | Basic analytics | Free |
| Google Analytics | Link tracking | Free |
| Gumdash | Gumroad analytics | Free |
| Notion/Airtable | Custom tracking | Free tier |

---

## 📈 Scaling Triggers

### When to Increase Frequency
- **Trigger:** Engagement rate > 5% for 2 consecutive weeks
- **Action:** Add 1 post/day on primary platform
- **Monitor:** Engagement rate for 1 week after change

### When to Add Platforms
- **Trigger:** Primary platform > 1,000 followers
- **Action:** Add Pinterest or YouTube
- **Monitor:** Cross-platform traffic for 2 weeks

### When to Add Team Members
- **Trigger:** Engagement response time > 4 hours consistently
- **Action:** Hire part-time engagement manager
- **Monitor:** Response time and engagement rate

### When to Scale Content Production
- **Trigger:** Content library < 10 unused pieces
- **Action:** Increase batch production by 50%
- **Monitor:** Content quality scores

---

## 🚨 Pipeline Failure Modes & Recovery

| Failure Mode | Detection | Recovery |
|-------------|-----------|----------|
| AI tool downtime | Generation fails | Switch to backup tool (Flux ↔ SD ↔ MJ) |
| Content quality drops | Engagement < 2% | Pause posting, review quality checklist |
| Scheduling tool fails | Posts don't go out | Manual posting for the day, fix tool next day |
| Engagement backlog | >50 unresponded comments | 30-min engagement blitz, reduce posting temporarily |
| Platform algorithm change | Reach drops >30% | Research new algorithm, adjust content format |
| Burnout | Missing batch days | Reduce frequency, focus on engagement only for 1 week |

---

*Content Pipeline v1.0 — Content Farm Manager, Day 4, 2026-05-19*
*Next: Execute first batch day → measure output → optimize workflow*
