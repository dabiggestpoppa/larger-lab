# 📅 Day 1 Plan — MAD Content Farm

> **Date:** 2026-05-18
> **Manager:** Content Farm Manager
> **Status:** ACTIVE

---

## Executive Summary

The content farm is at **Day 0** — only agent skeleton files exist. No strategy docs, no content, no platform accounts, no tools/scripts, no config. Day 1 is about **laying the foundation** while producing the first batch of actionable intelligence and content.

---

## 🔴 CRITICAL BLOCKERS (Must Resolve First)

| Blocker | Impact | Owner | Resolution |
|---------|--------|-------|------------|
| No `content-strategy.md` | All agents lack strategic direction | Manager | Create immediately (this file) |
| No `competitor-research.md` | Research agent has no baseline | Manager | Create immediately |
| No `MONETIZATION_STRATEGY` doc | Marketing agent lacks revenue framework | Manager | Create immediately |
| No `config/accounts.json` | Unknown platform account status | MAD | MAD must provide account info |
| No `config/civitai-token.json` | CivitAI scraper cannot run | MAD | MAD must provide API token |
| No `scripts/` directory | No scraper, remix pipeline, or posting queue | PM/Tools | Build scripts or work around |
| No `templates/captions.md` | Content Creation lacks caption framework | Manager | Create immediately |
| No `output/` directory | No content storage | Manager | Create structure |
| No content exists anywhere | Starting from zero | All | Day 1 production |

---

## Phase 1: Foundation (Manager — Immediate)

**The Manager must create these files FIRST before agents can work:**

1. **`content-farm/coordination/content-strategy.md`** — Content strategy with verticals, brand voice, content mix
2. **`content-farm/coordination/competitor-research.md`** — Initial competitor analysis
3. **`content-farm/reports/MONETIZATION_STRATEGY_20260518.md`** — Revenue streams and monetization plan
4. **`content-farm/templates/captions.md`** — Caption templates and hook formulas
5. **`content-farm/coordination/content-calendar.md`** — Empty content calendar structure
6. **`content-farm/coordination/posting-schedule.md`** — Posting frequency per platform
7. **`content-farm/coordination/content-status.md`** — Content tracking
8. **Directory structure:** `output/`, `data/`, `config/`, `scripts/`, `templates/`

---

## Phase 2: Research Agent Tasks (Priority 1)

**Agent:** Content Research
**Depends on:** Foundation files created by Manager
**Deadline:** End of Day 1

### Tasks:
1. **Create `agents/content-research/TRENDS.md`**
   - Research top 10 trending AI art topics/hashtags on TikTok
   - Research top 5 trending sounds/formats for AI content
   - Research top 5 competitor posts from the last 48 hours
   - Identify 3 content gaps/opportunities
   - *Note: Use web_search since CivitAI scraper may not be available*

2. **Create `agents/content-research/hashtag-research.md`**
   - Best hashtags per vertical (AI art, AI tools, AI tutorials, AI memes, AI NSFW)
   - Hashtag volume/competition estimates
   - Platform-specific hashtag strategies

3. **Create `agents/content-research/viral-analysis.md`**
   - Top 5 viral AI content formats (transformations, before/after, tutorials, memes, showcases)
   - Hook patterns that work
   - Optimal posting times per platform

### Success Criteria:
- [ ] TRENDS.md has real, searchable trend data (not fabricated)
- [ ] Hashtag research covers all 5 verticals
- [ ] Viral analysis identifies specific formats with examples

---

## Phase 3: Content Creation Agent Tasks (Priority 2)

**Agent:** Content Creation
**Depends on:** Research agent's TRENDS.md + Manager's strategy/templates
**Deadline:** End of Day 1

### Tasks:
1. **Create directory structure:**
   - `agents/content-creation/output/` — For produced content
   - `agents/content-creation/captions/` — For caption files
   - `agents/content-creation/prompt-packs/` — For prompt compilations

2. **Produce first content batch (10 pieces):**
   - 3 TikTok-ready concepts (1080x1920) — detailed briefs with prompts
   - 3 Instagram-ready concepts (1080x1080 + 1080x1350) — detailed briefs
   - 2 X/Twitter-ready concepts (1200x675) — detailed briefs
   - 2 Reddit-ready concepts (text + image post ideas)
   - *Note: Since we may not have image generation tools, produce detailed CONTENT BRIEFES with prompts, descriptions, and visual directions*

3. **Create `agents/content-creation/prompt-packs/50-viral-ai-prompts.md`**
   - 50 viral AI art prompts organized by category
   - Include model recommendations (Midjourney, SDXL, Flux, etc.)
   - Include style tags and negative prompts

4. **Write 20 captions** using templates from `content-farm/templates/captions.md`
   - 8 TikTok captions (short, hook-heavy)
   - 6 Instagram captions (medium, emoji-rich)
   - 4 X/Twitter captions (concise, thread-ready)
   - 2 Reddit captions (long-form, value-driven)

5. **Update `content-farm/coordination/content-calendar.md`** with Day 1 production

### Success Criteria:
- [ ] 10 content briefs produced with full specifications
- [ ] 50-viral-ai-prompts.md compiled
- [ ] 20 captions written across all platforms
- [ ] Content calendar updated

---

## Phase 4: Marketing & Ads Agent Tasks (Priority 3)

**Agent:** Marketing & Ads
**Depends on:** Research agent's TRENDS.md + Manager's monetization strategy
**Deadline:** End of Day 1

### Tasks:
1. **Create `agents/marketing-ads/campaigns/content-funnel.md`**
   - SFW → Engagement → Monetization funnel design
   - Platform-specific funnel paths (TikTok, IG, X, Reddit)
   - CTA strategy per platform
   - Lead magnet ideas (free prompt packs, AI art guides)

2. **Create `agents/marketing-ads/copy/ad-copy-bank.md`**
   - 10 ad headlines for AI art content
   - 5 CTAs per platform (TikTok, IG, X, Reddit)
   - 3 promotional post templates
   - Hook formulas for paid and organic

3. **Create `agents/marketing-ads/reports/revenue-projections.md`**
   - Month 1-3 revenue projections by stream:
     - Affiliate marketing (AI tools, courses)
     - Digital products (prompt packs, presets, LUTs)
     - Sponsored content
     - Ad revenue (TikTok Creator Fund, IG Reels, X)
   - Quick win priorities (what generates revenue fastest)
   - Budget allocation starting from $0 (organic-first approach)

### Success Criteria:
- [ ] Funnel strategy documented with clear stages
- [ ] Ad copy bank has usable, tested copy
- [ ] Revenue projections are realistic and actionable

---

## Dependency Chain

```
Manager (Foundation Files)
  ├──→ Research Agent (TRENDS.md, hashtags, viral analysis)
  │       ├──→ Content Creation (uses trends + research to produce content)
  │       └──→ Marketing & Ads (uses trends + research for campaigns)
  └──→ All Agents (strategy + templates)
```

---

## End-of-Day Deliverables

| Agent | Deliverable | Location |
|-------|------------|----------|
| Manager | Foundation files (strategy, templates, calendar) | `content-farm/coordination/`, `content-farm/templates/` |
| Research | TRENDS.md | `agents/content-research/TRENDS.md` |
| Research | hashtag-research.md | `agents/content-research/hashtag-research.md` |
| Research | viral-analysis.md | `agents/content-research/viral-analysis.md` |
| Creation | 10 content briefs | `agents/content-creation/output/` |
| Creation | 50-viral-ai-prompts.md | `agents/content-creation/prompt-packs/` |
| Creation | 20 captions | `agents/content-creation/captions/` |
| Marketing | content-funnel.md | `agents/marketing-ads/campaigns/` |
| Marketing | ad-copy-bank.md | `agents/marketing-ads/copy/` |
| Marketing | revenue-projections.md | `agents/marketing-ads/reports/` |

---

## Day 2 Preview

Once Day 1 foundation is set:
- Research: Deep dive into specific trending topics, begin competitor tracking
- Creation: Begin actual image generation (if tools available), produce first real content
- Marketing: Begin platform account setup, first organic posts
- Manager: Review all outputs, adjust strategy based on findings

---

*Day 1 Plan — Created by Content Farm Manager, 2026-05-18*
*Next review: End of Day 1*
