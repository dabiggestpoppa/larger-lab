---
name: hermes-maintenance
description: >
  Activate for Hermes agent maintenance routines. Use when auditing memory, updating skills,
  handling compaction, or performing regular agent hygiene. Covers the maintenance rules
  that keep an agent sharp over time.
version: 1.0.0
author: agent
platforms: [linux, macos, windows]
---

# Hermes Maintenance Skill

## Overview

Agents are teammates you keep training, not tools you finish setting up. This skill
covers the maintenance rules that keep a Hermes agent sharp over time.

## Maintenance Rules

### Rule 1: Wrong Twice → Update Immediately
- If the agent is wrong twice on the same thing, correct it on the spot
- Tell it to update the relevant skill or memory entry
- Don't let bad patterns compound

### Rule 2: Same Instruction Twice → Write a Skill
- If you find yourself giving the same instruction twice, ask Hermes to write a skill for it
- Skills are procedural memory — they make repeated work consistent
- "Every night at midnight Central, sync this repo" → becomes a cron + skill

### Rule 3: Verbose or Off-Tone → Edit the Soul
- If the agent is too verbose, edit SOUL.md to be more concise
- If the tone is wrong, update the personality section
- The soul evolves over time with feedback

### Rule 4: New Scheduled Task → Build a Skill + Cron
- Don't just ask for a one-off — build a skill, then ask Hermes to schedule it
- Each cron runs in a fresh isolated session
- Use CONTEXTFROM to pass output between chained jobs

### Rule 5: Something Breaks → Check Memory First
- Stale MEMORY.md is the #1 cause of weird agent behavior
- Audit: "Read me your memory file. Read me your soul file."
- Cut what's wrong, update what's stale

## Compaction Protocol

When auto-compaction fires (~136K tokens):
1. Hermes inserts a fallback context marker
2. Pauses crons that need pausing
3. Updates MEMORY.md with current state before continuing
4. If user doesn't understand: "Explain this to me. What does that fallback marker mean?"

## Audit Routine

Run this periodically (weekly or when behavior feels off):
1. "Read me your MEMORY.md" — check for stale entries
2. "Read me your SOUL.md" — check tone and personality alignment
3. "List your skills" — check for unused/stale skills
4. "List your crons" — check for unnecessary scheduled jobs
5. Review token usage patterns

## When to Spin Up a New Agent

Decision tree:
- Needs its own credentials, secrets, or tools? → **New agent**
- Needs its own long-term memory? → **New agent**
- Ongoing, repeated work that's basically a separate role? → **New agent**
- Otherwise → Keep it in the main personal agent

**Bad pattern**: One mega-agent with every API key, every skill, every cron. High confusion, high blast radius.

**Good pattern**: Main personal Hermes + split-off agents for marketing, finance, content, etc. Each in its own Docker container with scoped keys.

## Security Hygiene

- Each agent gets its own accounts (Gmail or agent mail), not yours
- Each agent gets its own API keys, scoped tight
- Named API keys per agent (OpenRouter, Perplexity, etc.) for spend tracking
- Least privilege: only the credentials and tools needed for the job
- Marketing agent doesn't need read access to QuickBooks
- Set up firewall on VPS, restrict to your IP, block unused ports
- Build a skill that runs a nightly security audit
