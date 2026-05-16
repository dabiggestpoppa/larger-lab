# DeekeScript — Android Automation Engine

Android automation framework for building content farms, auto-posting bots, and engagement automation.

**Use DeekeScript when:**
- Automating Android apps (TikTok, Instagram, CapCut, etc.)
- Building content posting bots
- Multi-account management on mobile platforms
- Batch content production on Android devices
- Growth hacking (auto-like, auto-comment, auto-follow)

**Requires:** Node.js, npm, Android device or emulator

## Quick Start

```bash
# 1. Clone and install
cd deekescript
npm install

# 2. Project structure
# src/          - TypeScript source code
# src/task/     - Task scripts (automation workflows)
# src/statistics/ - Analytics
# script/       - Compiled scripts
# images/       - Image resources for image recognition
# @deekeScript/ - Type definitions

# 3. Write automation scripts in TypeScript
# 4. Compile and deploy to Android device
```

## Core Capabilities

- **Simulate clicks/swipes** — control any Android app programmatically
- **Image recognition** — find UI elements by image matching
- **Multi-threading** — run concurrent tasks across devices
- **TypeScript** — full type-safe scripting
- **Device control** — screenshots, input, app management
- **Network requests** — API calls from scripts
- **Storage** — local data persistence

## Content Farm Use Cases

1. **Auto-posting** — script opens TikTok/Instagram, uploads video, adds caption, posts
2. **Batch editing** — controls CapCut/InShot to apply templates
3. **Engagement bots** — auto-like, auto-comment, auto-follow
4. **Account management** — warm up new accounts, rotate profiles
5. **Content repurposing** — reformat one video for multiple platforms

## Architecture

```
OpenClaw (Orchestrator)
    ↓
DeekeScript Runtime (on Android device/emulator)
    ↓
Target Apps (TikTok, Instagram, CapCut, etc.)
```

## Links

- **GitHub:** https://github.com/DeekeScript/deekescript
- **Website:** https://deeke.cn
- **Docs:** https://doc.deeke.cn
- **Example App:** https://github.com/DeekeScript/ad-deeke
