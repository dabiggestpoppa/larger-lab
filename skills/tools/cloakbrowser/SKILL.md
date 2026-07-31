# CloakBrowser Skill

**Purpose:** Stealth Chromium for bot-resistant web scraping. Drop-in Playwright replacement with source-level fingerprint patches.

**Install:** `pip install cloakbrowser`

**When to use:**
- Scraping sites with Cloudflare Turnstile, FingerprintJS, BrowserScan
- When Scrapling StealthyFetcher gets blocked
- Any site that detects automation frameworks

**Basic usage:**
```python
from cloakbrowser import launch

browser = launch()
page = browser.new_page()
page.goto("https://example.com")
content = page.content()
browser.close()
```

**With proxy (residential recommended):**
```python
browser = launch(
    proxy="http://user:pass@residential-proxy:port",
    geoip=True,
    headless=False,
    humanize=True,
)
```

**Key flags:**
- `humanize=True` — human-like mouse/keyboard/scroll
- `geoip=True` — match timezone/locale to proxy IP
- `headless=False` — some sites detect headless even with patches

**Integration with Scrapling:** Use CloakBrowser as the browser backend for Scrapling's StealthyFetcher when extra stealth is needed.

**Note:** First run downloads ~200MB stealth Chromium binary. Cached locally.
**Source:** https://github.com/CloakHQ/CloakBrowser
