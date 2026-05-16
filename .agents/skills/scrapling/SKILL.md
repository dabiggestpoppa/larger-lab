# Scrapling 🕷️

Scrapling is an adaptive Web Scraping framework that handles everything from a single request to a full-scale crawl.

**Use Scrapling when:**
- `web_fetch` fails or returns empty/blocked content
- The site has anti-bot protections (Cloudflare, DataDome, Kasada, etc.)
- You need to scrape/crawl JavaScript-rendered pages
- You need to write Python code to scrape or crawl websites
- You need full browser automation for data extraction

**Requires:** Python 3.10+, `scrapling` package installed globally.

## Quick Reference

### CLI Commands

```bash
# Simple sites (blogs, news, static pages)
scrapling extract get "https://example.com" output.md

# Dynamic/JS-rendered sites
scrapling extract fetch "https://example.com" output.md

# Protected sites (Cloudflare, anti-bot)
scrapling extract stealthy-fetch "https://example.com" output.md

# Extract specific content with CSS selectors
scrapling extract get "https://example.com" output.md --css-selector "article"

# AI-targeted mode (sanitizes hidden elements, extracts main content)
scrapling extract get "https://example.com" output.md --ai-targeted
```

**Escalation order:** `get` → `fetch` → `stealthy-fetch`. Start simple, escalate only if needed.

### Output Formats
- `.md` → Converts HTML to Markdown (best for docs/articles)
- `.html` → Raw HTML
- `.txt` → Clean text content
- `.json` → JSON data

### Key CLI Options

| Option | Description |
|--------|-------------|
| `-s, --css-selector TEXT` | CSS selector to extract specific content |
| `-H, --headers TEXT` | Custom headers ("Key: Value") |
| `--cookies TEXT` | Cookies string |
| `--timeout INTEGER` | Timeout in seconds (default: 30) |
| `--proxy TEXT` | Proxy URL |
| `--ai-targeted` | Sanitize for AI consumption |
| `--impersonate TEXT` | Browser to impersonate (chrome, firefox, safari) |

Browser-only options (`fetch` / `stealthy-fetch`):
| Option | Description |
|--------|-------------|
| `--headless / --no-headless` | Headless mode (default: True) |
| `--network-idle / --no-network-idle` | Wait for network idle |
| `--real-chrome / --no-real-chrome` | Use system Chrome |
| `--timeout INTEGER` | Timeout in ms (default: 30000) |

## Python API

### Fetchers (Single Requests)

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

# Simple HTTP request (fast)
page = Fetcher().get('https://example.com')
titles = page.css('h1::text').getall()

# Stealthy (anti-bot bypass)
page = StealthyFetcher.fetch('https://protected-site.com')
data = page.css('.content').getall()

# Dynamic (full browser)
page = DynamicFetcher.fetch('https://spa-app.com')
items = page.xpath('//div[@class="item"]/text()').getall()
```

### Sessions (Multiple Requests)

```python
from scrapling.fetchers import FetcherSession, StealthySession

# Persistent session with cookies/state
with FetcherSession(impersonate='chrome') as session:
    page1 = session.get('https://example.com/login')
    page2 = session.get('https://example.com/dashboard')
    data = page2.css('.data::text').getall()
```

### Spiders (Full Crawls)

```python
from scrapling.spiders import Spider, Response

class MySpider(Spider):
    name = "my_spider"
    start_urls = ["https://example.com/"]
    concurrent_requests = 10
    robots_txt_obey = True

    async def parse(self, response: Response):
        for item in response.css('.product'):
            yield {
                "title": item.css('h2::text').get(),
                "price": item.css('.price::text').get(),
            }
        next_page = response.css('.next a')
        if next_page:
            yield response.follow(next_page[0].attrib['href'])

result = MySpider().start()
result.items.to_json("output.json")
```

### Adaptive Scraping

```python
# Elements survive website design changes
page = StealthyFetcher.fetch('https://example.com')
products = page.css('.product', auto_save=True)  # Save fingerprint

# Later, even if site structure changes:
products = page.css('.product', adaptive=True)  # Auto-relocate elements
```

## MCP Server

Scrapling includes an MCP server for AI-assisted scraping. See: https://scrapling.readthedocs.io/en/latest/ai/mcp-server.html

## Links

- **Docs:** https://scrapling.readthedocs.io
- **GitHub:** https://github.com/D4Vinci/Scrapling
- **PyPI:** https://pypi.org/project/scrapling/
- **Skill Source:** https://github.com/D4Vinci/Scrapling/tree/main/agent-skill/Scrapling-Skill
