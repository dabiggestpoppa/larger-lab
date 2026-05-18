# 📋 Complete API List — Content Farm

> **Created:** 2026-05-18 08:15 EDT
> **Purpose:** Full list of APIs and credentials MAD needs to provide
> **Priority:** P0 = blocking production, P1 = needed soon, P2 = nice to have

---

## 🔴 P0 — BLOCKING (No production without these)

### 1. X / Twitter
- **API:** X API v2 (developer.x.com)
- **What we need:** API Key, API Secret, Access Token, Access Secret
- **Cost:** Free tier = 1,500 tweets/month read, 3,000 tweets/month write (Basic = $100/mo for more)
- **What it unlocks:** Posting tweets, threads, analytics
- **Auth:** OAuth 2.0
- **Notes:** X has tightened API access. Free tier may be enough to start.

### 2. Reddit
- **API:** Reddit API (reddit.com/dev/api)
- **What we need:** Client ID, Client Secret, Username, Password
- **Cost:** Free (with rate limits: 60 requests/min)
- **What it unlocks:** Posting to subreddits, reading trending, analytics
- **Auth:** OAuth 2.0 (script-type app)
- **Notes:** Create a "script" app at reddit.com/prefs/apps

### 3. Instagram
- **API:** Instagram Graph API (via Facebook Developers)
- **What we need:** Facebook App ID, App Secret, Instagram Business Account ID, Page Access Token
- **Cost:** Free
- **What it unlocks:** Posting images/videos, stories, analytics
- **Auth:** OAuth 2.0 via Facebook Login
- **Notes:** Instagram requires a BUSINESS or CREATOR account. Personal accounts can't use the API. If MAD has a personal account, he needs to convert it to Creator (free, in app settings).

### 4. TikTok
- **API:** TikTok for Developers API (developers.tiktok.com)
- **What we need:** Client Key, Client Secret, Access Token
- **Cost:** Free (with limits)
- **What it unlocks:** Posting videos, reading analytics
- **Auth:** OAuth 2.0
- **Notes:** TikTok API for posting is relatively new. May need to apply for access.

---

## 🟠 P1 — NEEDED FOR SCALE

### 5. CivitAI
- **API:** CivitAI API (civitai.com)
- **What we need:** API Key (from account settings)
- **Cost:** Free
- **What it unlocks:** Scraping AI models, images, prompts for content
- **Auth:** API Key in header
- **Notes:** This was a Day 1 blocker. Unlocks real content instead of placeholders.

### 6. YouTube
- **API:** YouTube Data API v3 (console.cloud.google.com)
- **What we need:** Google Cloud project + API key + OAuth credentials
- **Cost:** Free tier = 10,000 units/day
- **What it unlocks:** Posting shorts, reading analytics, trending data
- **Auth:** OAuth 2.0
- **Notes:** Need to create a Google Cloud project and enable YouTube API

### 7. Pinterest
- **API:** Pinterest API v5 (developers.pinterest.com)
- **What we need:** App ID, App Secret, Access Token
- **Cost:** Free
- **What it unlocks:** Pinning images, reading trending, analytics
- **Auth:** OAuth 2.0
- **Notes:** Great for AI art content. Very visual platform.

### 8. Telegram
- **API:** Telegram Bot API (core.telegram.org/bots/api)
- **What we need:** Bot Token (from @BotFather)
- **Cost:** Free
- **What it unlocks:** Posting to channels/groups, automation
- **Auth:** Bot Token
- **Notes:** Easiest API to set up. Create a bot via @BotFather in 2 minutes.

---

## 🟡 P2 — NICE TO HAVE

### 9. Discord
- **API:** Discord Developer Portal (discord.com/developers)
- **What we need:** Bot Token, Application ID
- **Cost:** Free
- **What it unlocks:** Posting to servers/channels, community building
- **Auth:** Bot Token

### 10. LinkedIn
- **API:** LinkedIn API (learn.microsoft.com/en-us/linkedin)
- **What we need:** Client ID, Client Secret, Access Token
- **Cost:** Free (limited)
- **What it unlocks:** Professional content, B2B audience
- **Auth:** OAuth 2.0
- **Notes:** More restrictive approval process

### 11. Gumroad
- **API:** Gumroad API (gumroad.com/api)
- **What we need:** Access Token (from account settings)
- **Cost:** Free
- **What it unlocks:** Product management, sales analytics
- **Auth:** Access Token
- **Notes:** For selling prompt packs, guides, templates

### 12. Medium
- **API:** Medium API (github.com/Medium/medium-api-docs)
- **What we need:** Integration Token
- **Cost:** Free
- **What it unlocks:** Cross-posting articles
- **Auth:** Integration Token

---

## 🔧 INFRASTRUCTURE APIS (For Agent Automation)

### 13. UI-TARS Desktop (bytedance/UI-TARS-desktop)
- **What it is:** Open-source multimodal AI agent that can control browser/desktop via vision
- **Why it matters:** For platforms WITHOUT APIs (or with restrictive APIs), UI-TARS can automate browser interactions — log in, navigate, post, click buttons — just like a human
- **Install:** `npm install @agent-tars/cli@latest -g` (Node.js 22+)
- **Needs:** An LLM API key (Anthropic, OpenAI, Volcengine, etc.)
- **Use case:** Instagram posting if API is too restrictive, TikTok browser automation, any platform without a clean API
- **Repo:** https://github.com/bytedance/UI-TARS-desktop

### 14. Ayrshare (Unified Social API)
- **What it is:** Single API to post to 14+ social networks
- **Why it matters:** Instead of integrating each platform separately, Ayrshare handles all of them
- **Cost:** Free tier = 200 posts/month, paid from $99/mo
- **API:** RESTful, simple key-based auth
- **Platforms:** X, Instagram, Facebook, LinkedIn, TikTok, Reddit, YouTube, Pinterest, Telegram, Discord, Bluesky, Threads, Tumblr, Medium
- **Link:** ayrshare.com

### 15. Buffer / Hootsuite (Alternative Unified APIs)
- **Buffer API:** buffer.com/developers — simpler, cheaper than Ayrshare
- **Hootsuite API:** hootsuite.com/developers — enterprise-grade, more expensive

---

## 📊 SUMMARY — What MAD Needs to Provide

### Immediate (P0):
| # | Platform | What to Provide | Where to Get It |
|---|----------|----------------|-----------------|
| 1 | X/Twitter | API Key + Secret + Access Token + Secret | developer.x.com |
| 2 | Reddit | Client ID + Secret + Username + Password | reddit.com/prefs/apps |
| 3 | Instagram | FB App ID + Secret + IG Account ID + Token | developers.facebook.com |
| 4 | TikTok | Client Key + Secret + Access Token | developers.tiktok.com |

### Soon (P1):
| # | Platform | What to Provide | Where to Get It |
|---|----------|----------------|-----------------|
| 5 | CivitAI | API Key | civitai.com (account settings) |
| 6 | YouTube | Google Cloud API Key + OAuth | console.cloud.google.com |
| 7 | Pinterest | App ID + Secret + Token | developers.pinterest.com |
| 8 | Telegram | Bot Token | @BotFather on Telegram |

### Infrastructure:
| # | Tool | What to Provide | Where to Get It |
|---|------|----------------|-----------------|
| 9 | UI-TARS | LLM API key (Anthropic/OpenAI) | Already have OpenClaw keys |
| 10 | Ayrshare | API Key | ayrshare.com (free tier) |

---

## 🔐 Credential Format

All credentials should go into the private GitHub repo in this structure:

```
credentials/
├── social/
│   ├── twitter.json      # { apiKey, apiSecret, accessToken, accessSecret }
│   ├── reddit.json       # { clientId, clientSecret, username, password }
│   ├── instagram.json    # { appId, appSecret, accountId, accessToken }
│   ├── tiktok.json       # { clientKey, clientSecret, accessToken }
│   ├── telegram.json     # { botToken }
│   ├── youtube.json      # { apiKey, clientId, clientSecret }
│   ├── pinterest.json    # { appId, appSecret, accessToken }
│   └── civitai.json      # { apiKey }
├── services/
│   ├── gumroad.json      # { accessToken }
│   ├── ayrshare.json     # { apiKey }
│   └── ui-tars.json      # { provider, model, apiKey }
└── README.md             # What each file is, when it was last rotated
```

---

*Last updated: 2026-05-18 08:15 EDT*
*Next: MAD provides credentials → agents configure connectors → production begins*
