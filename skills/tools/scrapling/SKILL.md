# Scrapling — Stealth Web Scraping Tool

> **Version:** 0.4.8 | **Installed:** ✅ `pip install scrapling`
> **Use for:** Scraping prop firm data from PropFirmMatch, PayoutJunction, and any anti-bot-protected site.

## Why Scrapling

- **StealthyFetcher** — bypasses Cloudflare Turnstile, FingerprintJS out of the box
- **Adaptive parser** — learns from site changes, auto-relocates elements when DOM updates
- **Spider framework** — concurrent multi-session crawls with pause/resume
- **Drop-in Playwright replacement** from `pip install cloakbrowser` (Scrapling uses Playwright under the hood)

## Key Fetchers

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

# Simple fetch (no stealth)
page = Fetcher().get('https://example.com')

# Stealthy fetch (bypasses anti-bot)
page = StealthyFetcher.fetch('https://propfirmmatch.com/futures', headless=True, network_idle=True)

# Dynamic fetch (for JS-heavy pages)
page = DynamicFetcher().get('https://example.com')
```

## Selecting Elements

```python
# CSS selectors
firms = page.css('.firm-card')
prices = page.css('.price::text').getall()

# XPath
names = page.xpath('//div[@class="firm-name"]/text()').getall()

# Adaptive mode (survives DOM changes)
products = page.css('.product', auto_save=True)  # saves selector fingerprint
products = page.css('.product', adaptive=True)   # auto-heals if DOM changes
```

## Spiders (Full Crawls)

```python
from scrapling.spiders import Spider, Response

class PropFirmSpider(Spider):
    name = "prop_firms"
    start_urls = ["https://propfirmmatch.com/futures"]

    async def parse(self, response: Response):
        for card in response.css('.firm-card'):
            yield {
                "name": card.css('.name::text').get(),
                "size": card.css('.size::text').get(),
                "cost": card.css('.cost::text').get(),
                "payout_days": card.css('.payout::text').get(),
            }

PropFirmSpider().start()
```

## For PropFirmMatch Scraping

The site likely has anti-bot. Use `StealthyFetcher`:
```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    'https://propfirmmatch.com/futures',
    headless=True,
    network_idle=True,
    timeout=30000,
)
# Then use css() or xpath() to extract firm cards, pricing, promos
```

## Output Convention

Always output scraped data as structured dicts → write to JSON:
```python
import json
data = [{"name": ..., "cost": ..., ...}]
with open('scraped_firms.json', 'w') as f:
    json.dump(data, f, indent=2)
```
