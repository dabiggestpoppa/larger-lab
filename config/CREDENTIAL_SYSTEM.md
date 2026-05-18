# 🔐 Credential & Connector System Design

> **Version:** 1.0 | **Date:** 2026-05-18
> **Author:** Infrastructure Researcher (security-focused)
> **Purpose:** Secure credential storage and platform connector architecture for agent workspace

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CREDENTIAL SYSTEM ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │  PRIVATE      │     │  LOCAL        │     │  AGENT       │    │
│  │  GITHUB REPO  │────▶│  DECRYPTED    │────▶│  RUNTIME     │    │
│  │  (encrypted)  │ pull│  VAULT        │ read│  USAGE       │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│        │                     │                     │            │
│        │              ┌──────┴──────┐              │            │
│        │              │  MASTER KEY │              │            │
│        │              │  (env var)  │              │            │
│        │              └─────────────┘              │            │
│        │                                           │            │
│  ┌─────┴───────────────────────────────────────────┴─────┐     │
│  │                  CONNECTOR LAYER                       │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │     │
│  │  │ X/Twitter│  │Instagram│  │ Reddit  │  │  APIs   │ │     │
│  │  │(browser) │  │(browser)│  │(browser)│  │(tokens) │ │     │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │     │
│  └───────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Credential Storage — Recommended Approach

### 2.1 Source of Truth: Private GitHub Repo (encrypted)

MAD's credentials live in a private GitHub repo, encrypted at rest.

**Recommended tool: `git-crypt`** (not transcrypt, not blackbox)

| Tool | Pros | Cons | Verdict |
|------|------|------|---------|
| **git-crypt** | AES-256-GCM, transparent, GPG or symmetric key, well-maintained | Requires git-crypt install on all machines | ✅ **RECOMMENDED** |
| transcrypt | Simple, no GPG needed | Weaker crypto (AES-128-CBC), less audited | ⚠️ Acceptable |
| blackbox | GPG-based, good for teams | GPG complexity, harder on Windows | ❌ Overkill |
| git-secret | GPG-based | Same GPG issues on Windows | ❌ Overkill |

**Setup:**
```bash
# On MAD's machine (one-time)
git-crypt init
git-crypt export-key /path/to/keyfile  # BACKUP SECURELY
# Add files to .gitattributes:
#   config/secrets.json filter=git-crypt diff=git-crypt
#   config/*.env filter=git-crypt diff=git-crypt
```

### 2.2 Local Vault: Decrypted at Runtime

The private repo is cloned to a local directory. Files are decrypted using the git-crypt key.

**Local structure:**
```
config/
├── .git/                    # Private repo (encrypted)
├── .gitattributes           # git-crypt filter rules
├── secrets.json             # ENCRYPTED — all credentials
├── accounts.json            # ENCRYPTED — platform account metadata
├── api-tokens.json          # ENCRYPTED — API keys/tokens
└── README.md                # Unencrypted — file format docs
```

**Decryption flow:**
1. Agent starts → checks for `GIT_CRYPT_KEY` env var
2. If present → `git-crypt unlock` (decrypts all files)
3. Agent reads decrypted JSON files
4. Credentials are NEVER logged, never printed to chat, never written to output files

### 2.3 Master Key Management

The git-crypt symmetric key must be available to agents but not exposed.

**Approach: Environment Variable + Windows DPAPI**

```powershell
# One-time setup (MAD runs this):
# Encrypt the git-crypt key using Windows DPAPI, store in user environment
$key = Get-Content "C:\secure\git-crypt-key" -Raw
$encrypted = [System.Security.Cryptography.ProtectedData]::Protect(
    [System.Text.Encoding]::UTF8.GetBytes($key),
    $null,
    [System.Security.Cryptography.DataProtectionScope]::CurrentUser
)
[Environment]::SetEnvironmentVariable("VAULT_KEY_B64", [Convert]::ToBase64String($encrypted), "User")
```

Agent reads the key at runtime:
```python
import os, base64
from ctypes import windll

def get_vault_key():
    encrypted_b64 = os.environ.get("VAULT_KEY_B64")
    if not encrypted_b64:
        raise RuntimeError("VAULT_KEY_B64 not set — unlock vault first")
    # Decrypt via DPAPI
    # ... (Windows-specific decryption)
    return key
```

---

## 3. Credential File Format

### `config/secrets.json` (encrypted)

```json
{
  "version": "1.0",
  "last_updated": "2026-05-18",
  "platforms": {
    "twitter": {
      "username": "@MAD_handle",
      "email": "mad@example.com",
      "password": "encrypted:AES256:...",
      "two_factor_secret": "encrypted:AES256:...",
      "cookies_file": "config/twitter-cookies.json"
    },
    "instagram": {
      "username": "mad_handle",
      "password": "encrypted:AES256:...",
      "two_factor_secret": "encrypted:AES256:..."
    },
    "reddit": {
      "username": "mad_user",
      "password": "encrypted:AES256:...",
      "client_id": "encrypted:AES256:...",
      "client_secret": "encrypted:AES256:..."
    },
    "tiktok": {
      "email": "mad@example.com",
      "password": "encrypted:AES256:..."
    }
  },
  "apis": {
    "civitai": {
      "token": "encrypted:AES256:..."
    },
    "openai": {
      "api_key": "encrypted:AES256:..."
    },
    "github": {
      "token": "encrypted:AES256:..."
    }
  }
}
```

---

## 4. Connector Architecture

### 4.1 Two-Tier Approach

**Tier 1: Browser Automation (for platforms without posting APIs)**
- X/Twitter, Instagram, TikTok, Reddit
- Uses Playwright with persistent browser profiles
- MAD logs in ONCE manually → session cookies saved → agents reuse

**Tier 2: API Tokens (for platforms with APIs)**
- CivitAI, GitHub, OpenAI, etc.
- Direct API calls with tokens from vault
- No browser needed

### 4.2 Browser Automation Details

**Persistent Profile Pattern (recommended):**

```javascript
// connectors/twitter.js
const { chromium } = require('playwright');

async function postToTwitter({ text, mediaPath }) {
  // Use persistent context — MAD already logged in
  const context = await chromium.launchPersistentContext(
    './browser-profiles/twitter',
    { headless: true, viewport: { width: 1280, height: 720 } }
  );
  const page = await context.newPage();
  await page.goto('https://x.com/home', { waitUntil: 'networkidle' });
  
  // Check if still logged in
  const composer = await page.$('div[role="textbox"][data-testid="tweetTextarea_0"]');
  if (!composer) {
    throw new Error('Twitter session expired — MAD needs to re-login');
  }
  
  // Post
  await page.click('div[role="textbox"][data-testid="tweetTextarea_0"]');
  await page.fill('div[role="textbox"][data-testid="tweetTextarea_0"]', text);
  
  if (mediaPath) {
    const fileInput = await page.$('input[data-testid="fileInput"]');
    await fileInput.setInputFiles(mediaPath);
    await page.waitForTimeout(3000);
  }
  
  await page.click('div[data-testid="tweetButtonInline"]');
  await page.waitForTimeout(5000);
  await context.close();
}
```

**Session persistence per platform:**
```
browser-profiles/
├── twitter/          # MAD's Twitter login session
├── instagram/        # MAD's Instagram login session
├── tiktok/           # MAD's TikTok login session
└── reddit/           # MAD's Reddit login session
```

### 4.3 Anti-Detection Measures

To avoid platform bans:
1. **Random delays** between actions (3-20 seconds)
2. **Daily post limits** (configurable per platform)
3. **Activity windows** (only post during MAD's timezone waking hours)
4. **Human-like warmup** (scroll feed before posting)
5. **Real user-agent** (match MAD's actual browser)
6. **Never run concurrent sessions** on same platform

### 4.4 Platform-Specific Notes

| Platform | Method | API Available? | Difficulty | Risk |
|----------|--------|----------------|------------|------|
| **X/Twitter** | Playwright + persistent profile | Yes (paid) | Medium | Medium |
| **Instagram** | Playwright + persistent profile | Limited (Graph API) | High | High |
| **TikTok** | Playwright + persistent profile | No | High | High |
| **Reddit** | Playwright or PRAW (API) | Yes (PRAW) | Low | Low |
| **YouTube** | API (youtube-upload) | Yes (Data API) | Low | Low |
| **Discord** | Bot token | Yes (Bot API) | Low | Low |

---

## 5. Security Model

### 5.1 Core Rules

| Rule | Implementation |
|------|----------------|
| **Never log credentials** | All credential access goes through `vault.py` which redacts from logs |
| **Read-only at runtime** | Agents read credentials but never write copies to workspace files |
| **No chat exposure** | Credential values never appear in agent messages or tool output |
| **Encrypted at rest** | All credential files encrypted via git-crypt |
| **Key in env var only** | Master key never stored in workspace files |
| **Per-agent scoped access** | Agents only get credentials they need (not all credentials) |

### 5.2 Agent Credential Access Pattern

```python
# vault.py — the ONLY module that touches credentials
import json, os

_VAULT_CACHE = None

def get_credential(platform, field):
    """Get a single credential. Never returns the full vault."""
    global _VAULT_CACHE
    if _VAULT_CACHE is None:
        _VAULT_cache = _load_vault()
    
    value = _VAULT_CACHE["platforms"][platform][field]
    
    # Decrypt if encrypted
    if value.startswith("encrypted:"):
        value = _decrypt(value)
    
    return value

def _load_vault():
    vault_path = os.path.join(os.environ.get("VAULT_PATH", "config"), "secrets.json")
    with open(vault_path, 'r') as f:
        return json.load(f)

def _decrypt(encrypted_value):
    # Decrypt using key from env var
    # ...
    pass
```

### 5.3 Compromise Mitigation

If an agent is compromised:
1. Credentials are NOT in the agent's memory (only the specific value needed)
2. Full vault is NOT accessible (agents request specific fields)
3. All access is logged (audit trail)
4. MAD can rotate credentials by updating the private repo
5. git-crypt key can be rotated (re-encrypt all files)

### 5.4 Credential Rotation

1. MAD updates `config/secrets.json` in private repo
2. `git commit && git push`
3. Agent workspace pulls latest: `cd config && git pull`
4. `git-crypt unlock` (if key changed)
5. Agents pick up new credentials on next read (no restart needed if using fresh reads)

---

## 6. MVP Implementation Plan (This Week)

### Phase 1: Foundation (Day 1-2)

| Step | Task | Owner | Output |
|------|------|-------|--------|
| 1.1 | Create private GitHub repo for credentials | MAD | Private repo URL |
| 1.2 | Install git-crypt on Windows | MAD | `git-crypt` available |
| 1.3 | Initialize git-crypt in repo | MAD | `.gitattributes` configured |
| 1.4 | Add first credentials (Twitter) | MAD | `secrets.json` encrypted |
| 1.5 | Clone repo to `config/` in workspace | Agent | Local encrypted copy |
| 1.6 | Set up env var for git-crypt key | MAD | `VAULT_KEY_B64` set |

### Phase 2: Connector MVP (Day 3-4)

| Step | Task | Owner | Output |
|------|------|-------|--------|
| 2.1 | Write `vault.py` credential reader | Agent | `config/vault.py` |
| 2.2 | Install Playwright | Agent | `npm install playwright` |
| 2.3 | MAD logs into Twitter in persistent profile | MAD | `browser-profiles/twitter/` |
| 2.4 | Write `connectors/twitter.js` | Agent | Working Twitter poster |
| 2.5 | Test: post a tweet via agent | Agent | Test tweet posted |

### Phase 3: Expand (Day 5-7)

| Step | Task | Owner | Output |
|------|------|-------|--------|
| 3.1 | Add Instagram profile | MAD | `browser-profiles/instagram/` |
| 3.2 | Write `connectors/instagram.js` | Agent | Working IG poster |
| 3.3 | Add Reddit via PRAW | Agent | `connectors/reddit.py` |
| 3.4 | Add API token connectors | Agent | `connectors/civitai.js`, etc. |
| 3.5 | Write posting scheduler | Agent | `tools/social-scheduler.py` |

---

## 7. File Structure

```
config/
├── .git/                          # Private repo
├── .gitattributes                 # git-crypt filters
├── secrets.json                   # ENCRYPTED — all credentials
├── accounts.json                  # ENCRYPTED — account metadata
├── api-tokens.json                # ENCRYPTED — API keys
├── vault.py                       # Credential reader (unencrypted)
├── README.md                      # File format docs
├── browser-profiles/
│   ├── twitter/                   # Persistent browser profile
│   ├── instagram/
│   ├── tiktok/
│   └── reddit/
└── connectors/
    ├── twitter.js                 # X/Twitter connector
    ├── instagram.js               # Instagram connector
    ├── tiktok.js                  # TikTok connector
    ├── reddit.py                  # Reddit connector (PRAW)
    ├── civitai.js                 # CivitAI API connector
    └── github.js                  # GitHub API connector
```

---

## 8. What MAD Needs to Do vs What Agents Can Do

### MAD Must Do (cannot be delegated):
1. **Create private GitHub repo** for credentials
2. **Install git-crypt** on Windows (`choco install git-crypt` or download binary)
3. **Add credentials** to `secrets.json` (passwords, API tokens, 2FA secrets)
4. **Log into each platform** in the persistent browser profiles (one-time per platform)
5. **Set environment variable** `VAULT_KEY_B64` with the encrypted git-crypt key
6. **Provide CivitAI API token** (if not already in vault)

### Agents Can Do (once MAD completes above):
1. Write `vault.py` credential reader
2. Write all connector scripts
3. Write posting scheduler
4. Test all connectors
5. Build content queue system
6. Automate posting workflows

---

## 9. Security Anti-Patterns to Avoid

| ❌ Never | ✅ Instead |
|----------|-----------|
| Store credentials in workspace files | Use encrypted vault |
| Print credentials to chat/logs | Use vault.py with redaction |
| Use `.env` files in workspace | Use git-crypt encrypted JSON |
| Hardcode tokens in connector scripts | Read from vault at runtime |
| Run browser automation with fresh login each time | Use persistent profiles |
| Post at super-human speeds | Add random delays, daily limits |
| Store git-crypt key in workspace | Use Windows DPAPI + env var |

---

## 10. Future Enhancements (Post-MVP)

1. **OneCLI-style gateway** — HTTP proxy that injects credentials (agents call `localhost:3115/twitter/post` instead of touching credentials)
2. **Per-agent scoped tokens** — Each agent gets its own OAuth token with limited scopes
3. **Credential usage audit log** — Track every credential access
4. **Auto-rotation** — Scheduled credential refresh for APIs that support it
5. **MCP server wrapper** — Wrap connectors as MCP servers for standardized tool access

---

*Document: config/CREDENTIAL_SYSTEM.md — Infrastructure Researcher, 2026-05-18*
*Classification: Internal — contains security architecture details*
