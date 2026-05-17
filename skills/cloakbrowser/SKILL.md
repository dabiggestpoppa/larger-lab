# CloakBrowser Skill

## Purpose
Stealth Chromium browser automation that passes every bot detection test. Drop-in Playwright replacement with source-level fingerprint patches. Use when `web_fetch` and `browser` tools fail due to bot detection.

## When to Use
- `web_fetch` returns 403/429 or bot detection pages
- `browser` tool fails Cloudflare Turnstile / FingerprintJS / reCAPTCHA
- Scraping protected sites (Cloudflare, Akamai, PerimeterX)
- Testing OCE frontend against bot detection
- Any browser automation that gets blocked

## Installation
```bash
pip install cloakbrowser  # Python
npm install cloakbrowser playwright-core  # JavaScript
```

## Python Usage
```python
from cloakbrowser import launch

browser = launch()
page = browser.new_page()
page.goto("https://protected-site.com")  # No more blocks
content = page.content()
browser.close()
```

## With Humanize (bypasses behavioral detection)
```python
browser = launch(humanize=True)  # Human-like mouse/keyboard/scroll
```

## With Proxy + GeoIP
```python
browser = launch(
    proxy="socks5://user:pass@host:port",
    geoip=True  # Auto-detect timezone/locale from proxy IP
)
```

## Persistent Profiles (keeps cookies/sessions)
```python
context = launch_persistent_context(profile_path="./my_profile")
```

## Integration with Existing Tools

### Replacing web_fetch for protected sites
When `web_fetch` fails:
```python
from cloakbrowser import launch
browser = launch()
page = browser.new_page()
page.goto(url)
content = page.inner_text("body")
browser.close()
```

### Replacing browser tool
When OpenClaw's `browser` tool is blocked:
```python
from cloakbrowser import launch
browser = launch(humanize=True)
page = browser.new_page()
page.goto(url)
# ... interact with page ...
screenshot = page.screenshot()
browser.close()
```

### Integration with Scrapling
```python
from cloakbrowser import launch
from scrapling import Fetcher

browser = launch()
# Use Scrapling with CloakBrowser's stealth context
```

## Detection Bypass Results
| Detection | Stock Playwright | CloakBrowser |
|-----------|-----------------|--------------|
| reCAPTCHA v3 | 0.1 (bot) | 0.9 (human) |
| Cloudflare Turnstile | FAIL | PASS |
| FingerprintJS | DETECTED | PASS |
| BrowserScan | DETECTED | NORMAL |
| ShieldSquare | BLOCKED | PASS |

## Constraints
- First run downloads ~200MB Chromium binary (cached locally)
- Use `humanize=True` for behavioral detection bypass
- Persistent profiles for session continuity
- Bring your own proxies for IP rotation
- Does NOT solve CAPTCHAs — prevents them from appearing

## Related Skills
- `skills/scrapling/SKILL.md` — Adaptive web scraping
- `skills/use-my-browser/SKILL.md` — Control real Chrome via Tampermonkey
