# Analytics Pipeline — Setup Summary

**Date:** 2026-05-16
**Agent:** OWL (Research Lead)
**Status:** ✅ Complete & Verified

---

## What Was Built

### 1. `content-farm/config/analytics.yaml`
Central configuration for the entire analytics pipeline:
- **Metrics per platform** — views, likes, comments, shares, followers, completion rate, etc.
- **Engagement benchmarks by niche** — fitness, cooking, tech, lifestyle, finance
- **Report schedule** — daily (06:00 UTC) + weekly (Sunday 08:00 UTC)
- **Oransim model settings** — mock mode, platform alloc, feature toggles, niche list
- **Content classification rules** — scale/keep/kill thresholds
- **Database config** — SQLite path + backup settings
- **shortLink attribution** — UTM tracking config

### 2. `content-farm/scripts/content_tracker.py`
SQLite-based content performance tracker:
- **Schema:** 3 tables — `posts`, `metrics`, `daily_snapshots`
- **CLI commands:**
  - `log` — Record a new post with metadata (platform, niche, format, caption, shortlink)
  - `update` — Update performance metrics for a post
  - `snapshot` — Add daily snapshot for trend tracking
  - `list` — List posts with filters (platform, niche, days)
  - `summary` — Aggregate performance stats
  - `niches` — Per-niche engagement breakdown
  - `export` — Export data as JSON/CSV for Oransim
  - `demo` — Seed 30 sample posts for testing
- **Database:** `content-farm/data/performance.db`

### 3. `content-farm/scripts/analytics.py`
Analytics engine with Oransim integration:
- **OransimPredictor** — Wraps the Oransim causal engine for niche/platform ROI predictions
  - Calls actual Oransim `WM.simulate_impression()` + `AG.simulate()` when engine is available
  - Falls back to heuristic benchmarks (industry CTR/CVR by niche × platform multiplier)
- **ReportGenerator** — Generates markdown reports with:
  - Summary stats, niche performance, top/bottom performers
  - Oransim prediction table (CTR, CVR, ROAS by niche × platform)
  - Actionable recommendations (scale/keep/kill)
- **CLI commands:**
  - `report` — Generate daily report
  - `predict` — Run Oransim prediction for a niche
  - `compare` — Compare all niches side-by-side
  - `run-all` — Full pipeline: predict → report

### 4. `content-farm/output/reports/2026-05-16.md`
Sample daily report generated from demo data.

---

## Test Results

All commands verified working:

| Command | Status | Notes |
|---------|--------|-------|
| `content_tracker.py demo` | ✅ | Seeded 30 posts across 5 niches, 3 platforms |
| `content_tracker.py summary` | ✅ | 30 posts, 692K views, 10.05% eng. rate |
| `content_tracker.py list` | ✅ | Shows posts with engagement rates |
| `content_tracker.py niches` | ✅ | Per-niche breakdown sorted by views |
| `analytics.py predict` | ✅ | Oransim engine: fitness/douyin → 9.47% CTR, 17.2x ROAS |
| `analytics.py compare` | ✅ | All 5 niches × 2 platforms compared |
| `analytics.py run-all` | ✅ | Full pipeline: predictions + report generated |

### Oransim Integration
- Engine bootstraps in ~1 second (100K agent population)
- Mock mode works without API key
- Predictions use actual `WM.simulate_impression()` + `AG.simulate()` pipeline
- Heuristic fallback available if Oransim engine unavailable

---

## File Structure

```
content-farm/
├── config/
│   ├── analytics.yaml          # Analytics configuration
│   └── accounts.json           # (existing)
├── scripts/
│   ├── content_tracker.py      # SQLite performance tracker
│   ├── analytics.py            # Oransim + report generator
│   ├── dy_auto_engage.js       # (existing)
│   └── xhs_auto_engage.js      # (existing)
├── data/
│   └── performance.db          # SQLite database (auto-created)
├── output/
│   └── reports/
│       ├── 2026-05-16.md       # Sample daily report
│       └── weekly/             # Weekly reports (future)
└── logs/
    └── analytics-setup.md      # This file
```

---

## Next Steps (When Ready to Go Live)

1. **Set up automated scheduling** — Add a cron job or Windows Task Scheduler entry:
   ```
   # Daily at 6 AM UTC
   python scripts/analytics.py run-all
   ```

2. **Connect to real data** — Replace `demo` seeding with actual post logging from DeekeScript automation:
   ```bash
   python scripts/content_tracker.py log --platform douyin --niche fitness \
       --caption "Morning workout" --file-path "output/videos/workout_001.mp4"
   ```

3. **Enable Oransim API mode** — Set `LLM_MODE=api` + `LLM_API_KEY` in environment for LLM-backed soul personas

4. **Wire up shortLink attribution** — Use shortLink's tracking to attribute follower growth to specific posts

5. **Build dashboard** — The markdown reports can be served via a simple web UI or sent to Telegram/Discord

---

*Setup completed by OWL 🦉 — 2026-05-16*
