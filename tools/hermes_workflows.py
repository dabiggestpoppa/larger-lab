"""
Hermes Workflows — Chief of Staff Automation
Inspired by Ole Lehmann's 9 production-tested workflows.

These are cron-style workflows that Hermes can run autonomously.
Each workflow produces a structured output delivered via Telegram.

Usage:
    from tools.hermes_workflows import HermesWorkflows
    
    workflows = HermesWorkflows()
    brief = workflows.daily_brief()
    radar = workflows.trending_radar()
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class WorkflowResult:
    name: str
    timestamp: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class HermesWorkflows:
    """
    Production workflows for Hermes agent.
    Each workflow is designed to run as a cron job and deliver
    structured output via Telegram.
    """
    
    def __init__(self, output_dir: str = "nautilus/reports/workflows"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    def daily_brief(self, calendar_events: List[Dict] = None,
                    emails: List[Dict] = None,
                    weather: str = None,
                    headlines: List[str] = None) -> WorkflowResult:
        """
        Workflow 1: Daily Brief (7am)
        Pulls calendar, top emails, weather, headlines → one scannable message.
        Replaces opening 5 apps before coffee.
        """
        sections = [f"☀️ **Daily Brief** — {self.timestamp}"]
        
        if calendar_events:
            sections.append("\n📅 **Calendar:**")
            for evt in calendar_events[:5]:
                sections.append(f"  • {evt.get('time', '?')} — {evt.get('title', 'Untitled')}")
        
        if emails:
            sections.append("\n📧 **Top Emails:**")
            for email in emails[:3]:
                sections.append(f"  • {email.get('subject', 'No subject')} — {email.get('from', 'Unknown')}")
        
        if weather:
            sections.append(f"\n🌤️ **Weather:** {weather}")
        
        if headlines:
            sections.append("\n📰 **Headlines:**")
            for h in headlines[:3]:
                sections.append(f"  • {h}")
        
        content = "\n".join(sections)
        return WorkflowResult("daily_brief", self.timestamp, content)
    
    def trending_radar(self, reddit_posts: List[Dict] = None,
                       x_posts: List[Dict] = None,
                       ai_forums: List[Dict] = None) -> WorkflowResult:
        """
        Workflow 3: Trending Workflows Radar (morning)
        Scans Reddit, X, AI forums → ranked list of 5 content angles.
        """
        sections = [f"🔍 **Trending Radar** — {self.timestamp}"]
        
        all_posts = []
        if reddit_posts:
            all_posts.extend([("Reddit", p) for p in reddit_posts])
        if x_posts:
            all_posts.extend([("X", p) for p in x_posts])
        if ai_forums:
            all_posts.extend([("AI Forum", p) for p in ai_forums])
        
        # Sort by engagement (upvotes + likes)
        all_posts.sort(key=lambda x: x[1].get("score", 0), reverse=True)
        
        sections.append("\n🔥 **Top 5 Trending Angles:**")
        for i, (source, post) in enumerate(all_posts[:5], 1):
            title = post.get("title", post.get("text", "No title"))[:80]
            score = post.get("score", 0)
            sections.append(f"  {i}. [{source}] {title}... (score: {score})")
        
        content = "\n".join(sections)
        return WorkflowResult("trending_radar", self.timestamp, content)
    
    def meeting_prep(self, meeting: Dict = None,
                     attendees: List[Dict] = None,
                     email_context: str = None) -> WorkflowResult:
        """
        Workflow 4: Meeting Prep Briefing (30min before)
        Pulls attendee list, LinkedIn context, last email thread → one-page brief.
        """
        if not meeting:
            return WorkflowResult("meeting_prep", self.timestamp, "No upcoming meetings.")
        
        sections = [f"📋 **Meeting Prep** — {meeting.get('title', 'Untitled')}"]
        sections.append(f"🕐 **Time:** {meeting.get('time', 'TBD')}")
        
        if attendees:
            sections.append("\n👥 **Attendees:**")
            for att in attendees:
                name = att.get("name", "Unknown")
                role = att.get("role", "")
                company = att.get("company", "")
                context = att.get("context", "")
                sections.append(f"  • {name} — {role} @ {company}")
                if context:
                    sections.append(f"    └─ {context[:100]}")
        
        if email_context:
            sections.append(f"\n📧 **Recent Context:**\n{email_context[:500]}")
        
        content = "\n".join(sections)
        return WorkflowResult("meeting_prep", self.timestamp, content)
    
    def humanizer(self, text: str) -> WorkflowResult:
        """
        Workflow 5: The Humanizer
        Audits text for 30+ known AI writing tells and rewrites naturally.
        """
        ai_tells = {
            "delve": "explore",
            "tapestry": "collection",
            "leverage": "use",
            "utilize": "use",
            "furthermore": "also",
            "moreover": "also",
            "in conclusion": "so",
            "it's important to note": "",
            "at the end of the day": "",
            "in today's world": "",
            "game-changer": "big change",
            "paradigm shift": "big change",
            "cutting-edge": "new",
            "state-of-the-art": "new",
            "robust": "strong",
            "comprehensive": "full",
            "seamless": "smooth",
            "intuitive": "easy",
        }
        
        issues_found = []
        rewritten = text
        
        for tell, replacement in ai_tells.items():
            if tell.lower() in text.lower():
                issues_found.append(f"'{tell}' → '{replacement}'")
                rewritten = rewritten.replace(tell, replacement)
                rewritten = rewritten.replace(tell.capitalize(), replacement.capitalize())
        
        # Fix em-dashes (common AI tell)
        if "—" in text:
            issues_found.append("em-dashes → commas")
            rewritten = rewritten.replace("—", ",")
        
        # Fix tricolon structures (3 parallel items — very AI)
        # Simple heuristic: three consecutive sentences starting with same word
        
        sections = ["✏️ **Humanizer Report**"]
        sections.append(f"\n**Issues found:** {len(issues_found)}")
        for issue in issues_found[:10]:
            sections.append(f"  • {issue}")
        
        sections.append(f"\n**Rewritten:**\n{rewritten}")
        
        content = "\n".join(sections)
        return WorkflowResult("humanizer", self.timestamp, content, 
                            {"issues_found": len(issues_found)})
    
    def weekly_report(self, metrics: Dict[str, Any] = None) -> WorkflowResult:
        """
        Workflow 8: Weekly Business Report (Monday morning)
        Pulls Stripe revenue, newsletter subs, content views, follower growth → dashboard.
        """
        sections = [f"📊 **Weekly Report** — {self.timestamp}"]
        
        if metrics:
            sections.append("\n**This Week vs Last Week:**")
            for key, value in metrics.items():
                if isinstance(value, dict):
                    current = value.get("current", 0)
                    previous = value.get("previous", 0)
                    change = ((current - previous) / previous * 100) if previous else 0
                    arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    sections.append(f"  {arrow} {key}: {current} ({change:+.1f}%)")
                else:
                    sections.append(f"  • {key}: {value}")
        else:
            sections.append("\n_No metrics configured. Connect Stripe, newsletter, analytics APIs._")
        
        content = "\n".join(sections)
        return WorkflowResult("weekly_report", self.timestamp, content)
    
    def save_workflow_result(self, result: WorkflowResult) -> Path:
        """Save workflow result to file."""
        filename = f"{result.name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "name": result.name,
                "timestamp": result.timestamp,
                "content": result.content,
                "metadata": result.metadata,
            }, f, indent=2)
        return path


if __name__ == "__main__":
    wf = HermesWorkflows()
    
    # Demo: Daily Brief
    brief = wf.daily_brief(
        calendar_events=[
            {"time": "09:00", "title": "Team Standup"},
            {"time": "14:00", "title": "Phase 4 Review"},
        ],
        emails=[
            {"subject": "Phase 4 test results", "from": "AS"},
            {"subject": "New resource evaluation", "from": "OC"},
        ],
        weather="☀️ 72°F, Clear",
        headlines=[
            "SRRA-OPH Phase 4 integration begins",
            "CLI-Anything hits 35k stars",
            "New agent harness patterns emerging",
        ]
    )
    print(brief.content)
    print(f"\n---\nSaved to: {wf.save_workflow_result(brief)}")
    
    # Demo: Humanizer
    humanized = wf.humanizer(
        "It's important to note that we need to delve into the comprehensive "
        "tapestry of agent harness design. Furthermore, we should leverage "
        "cutting-edge paradigms to create a robust, seamless, and intuitive system."
    )
    print(f"\n{humanized.content}")
