---
name: hermes-workflows
description: 9 Chief of Staff automation workflows for Hermes agent. Daily brief, trending radar, meeting prep, humanizer, weekly report, and more.
---

# Hermes Workflows Skill

Production-tested automation workflows for the Hermes agent. Each workflow runs as a cron job and delivers structured output via Telegram.

## Available Workflows

| # | Workflow | Schedule | Description |
|---|----------|----------|-------------|
| 1 | **Daily Brief** | 7am daily | Calendar + email + weather + headlines → Telegram |
| 2 | **Viral Swipe File** | Nightly | Auto-extract engaging posts → structured swipe file |
| 3 | **Trending Radar** | Morning | Scan Reddit/X/AI forums → ranked content angles |
| 4 | **Meeting Prep** | 30min before | Attendees + context → one-page brief |
| 5 | **Humanizer** | On-demand | Audit text for AI tells → rewrite naturally |
| 6 | **Bookmark Inbox** | Continuous | X bookmarks → summarize → tag → Obsidian |
| 7 | **Support Cron** | Morning | Scan inbox → categorize → Discord |
| 8 | **Weekly Report** | Monday AM | Revenue + subs + views → dashboard |
| 9 | **Obsidian Wiki** | Daily | Daily reports → Obsidian vault |

## Usage

```python
from tools.hermes_workflows import HermesWorkflows

wf = HermesWorkflows()

# Daily Brief
brief = wf.daily_brief(
    calendar_events=[{"time": "09:00", "title": "Standup"}],
    emails=[{"subject": "Test results", "from": "AS"}],
    weather="☀️ 72°F, Clear",
    headlines=["SRRA-OPH Phase 4 begins"]
)
print(brief.content)

# Humanizer
result = wf.humanizer("We need to delve into the comprehensive tapestry...")
print(result.content)

# Save result
path = wf.save_workflow_result(brief)
```

## Integration

- Connect to Google Calendar API for daily brief
- Connect to Gmail API for email scanning
- Connect to X API for trending radar + bookmarks
- Connect to Stripe API for weekly report
- Connect to Obsidian for knowledge management
- Deliver all output via Telegram bot
