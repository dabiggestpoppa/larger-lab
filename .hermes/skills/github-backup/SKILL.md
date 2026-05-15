---
name: github-backup
description: >
  Activate for setting up automated GitHub backup of agent memory, skills, and configuration.
  Use when deploying a new Hermes agent or when the backup cron needs maintenance.
  Prevents data loss if VPS gets corrupted.
version: 1.0.0
author: agent
platforms: [linux, macos, windows]
---

# GitHub Backup Skill

## Overview

If the VPS gets corrupted, your skills and memory are gone. With a GitHub backup,
you spin up a new Hermes, point it at the repo, and you're back online.

## What to Back Up

- `MEMORY.md` — agent's persistent memory
- `USER.md` — user profile
- `SOUL.md` — agent identity
- `skills/` directory — all agent-created skills
- `config.yaml` — non-secret configuration
- `cron/jobs.json` — scheduled jobs

## What NOT to Back Up

- `.env` — API keys and secrets (NEVER commit)
- `auth.json` — OAuth credentials
- Any file containing tokens, passwords, or private keys

## Setup Steps

### 1. Create Private GitHub Repo
- Create a new private repo on GitHub
- Generate a classic GitHub token scoped to `repo` + `contents` (read/write only)
- Don't grant more permissions than needed

### 2. Configure Git in Container
```bash
git config --global user.email "agent@hermes"
git config --global user.name "Hermes Agent"
```

### 3. Create .gitignore
```
.env
auth.json
*.log
state.db
```

### 4. Set Up Cron
```
/goal every night at midnight UTC, push all files except secrets to my private GitHub repo at git@github.com:<user>/<repo>.git
```

The agent will:
- Build the skill
- Set the cron
- Write the .gitignore so secrets never get committed

### 5. Verify
- Check that the repo receives nightly pushes
- Confirm no secrets are in the repo
- Test recovery: clone repo into a new container, verify memory/skills load

## Recovery Procedure

If VPS is corrupted:
1. Spin up new Hermes container
2. Clone the backup repo
3. Copy MEMORY.md, USER.md, SOUL.md, skills/ into `~/.hermes/`
4. Re-enter API keys via `hermes config set KEY value`
5. Agent is back online with full memory

## Token Best Practice

- Classic GitHub token (not fine-grained)
- Scoped to `repo` + `contents` only (read and write)
- Don't grant more than the agent needs
- Store via `hermes config set GITHUB_TOKEN <token>` — never in chat
