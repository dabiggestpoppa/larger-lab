"""
Twitter/X Reader via Nitter RSS
No API key needed. Uses public Nitter instances to read tweets via RSS.

Usage:
    python twitter_nitter.py user <username>           -- Get user's recent tweets
    python twitter_nitter.py tweet <tweet_id>          -- Get specific tweet by ID
    python twitter_nitter.py search <query>            -- Search tweets
    python twitter_nitter.py trending                  -- Get trending topics
    python twitter_nitter.py bookmark <url>            -- Read any tweet URL
"""

import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import json
import re
from typing import List, Dict, Optional

# Public Nitter instances (fallback chain)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
    "https://nitter.fdn.fr",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
]


def fetch_rss(url: str, timeout: int = 15) -> Optional[str]:
    """Try fetching RSS from multiple Nitter instances."""
    for instance in NITTER_INSTANCES:
        try:
            req = urllib.request.Request(
                url if url.startswith("http") else f"{instance}{url}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            continue
    return None


def parse_rss_items(rss_text: str) -> List[Dict]:
    """Parse RSS XML into list of tweet dicts."""
    items = []
    try:
        root = ET.fromstring(rss_text)
        channel = root.find("channel")
        if channel is None:
            return items
        for item in channel.findall("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            # Extract tweet ID from link
            tweet_id = ""
            if "/status/" in link:
                tweet_id = link.split("/status/")[-1].split("?")[0].split("#")[0]
            items.append({
                "title": title,
                "link": link,
                "description": desc,
                "pub_date": pub_date,
                "tweet_id": tweet_id,
            })
    except ET.ParseError:
        pass
    return items


def get_user_tweets(username: str, count: int = 10) -> List[Dict]:
    """Get recent tweets from a user via Nitter RSS."""
    rss_text = fetch_rss(f"/{username}/rss")
    if not rss_text:
        return []
    items = parse_rss_items(rss_text)
    return items[:count]


def get_tweet(tweet_id: str, username: str = None) -> Optional[Dict]:
    """Get a specific tweet. If username known, go direct; otherwise search."""
    if username:
        rss_text = fetch_rss(f"/{username}/rss")
        if rss_text:
            items = parse_rss_items(rss_text)
            for item in items:
                if item.get("tweet_id") == tweet_id:
                    return item
    # Try fetching the tweet page directly
    for instance in NITTER_INSTANCES:
        try:
            url = f"{instance}/i/status/{tweet_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
                # Extract tweet text from HTML
                text_match = re.search(r'class="tweet-content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
                if text_match:
                    text = re.sub(r'<[^>]+>', '', text_match.group(1)).strip()
                    return {"title": text, "link": url, "tweet_id": tweet_id}
        except:
            continue
    return None


def search_tweets(query: str, count: int = 10) -> List[Dict]:
    """Search tweets via Nitter RSS."""
    encoded = urllib.parse.quote(query)
    rss_text = fetch_rss(f"/search/rss?f=tweets&q={encoded}")
    if not rss_text:
        return []
    items = parse_rss_items(rss_text)
    return items[:count]


def extract_tweet_id_from_url(url: str) -> Optional[str]:
    """Extract tweet ID from various Twitter/X URL formats."""
    patterns = [
        r'twitter\.com/\w+/status/(\d+)',
        r'x\.com/\w+/status/(\d+)',
        r't\.co/\w+',  # Can't resolve t.co without following redirect
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def format_tweet(tweet: Dict) -> str:
    """Format a tweet for display."""
    lines = []
    if tweet.get("title"):
        lines.append(tweet["title"][:300])
    if tweet.get("pub_date"):
        lines.append(f"  Date: {tweet['pub_date']}")
    if tweet.get("link"):
        lines.append(f"  Link: {tweet['link']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import urllib.parse

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "user" and len(sys.argv) >= 3:
        username = sys.argv[2].lstrip("@")
        tweets = get_user_tweets(username)
        if tweets:
            print(f"@{username} recent tweets ({len(tweets)}):")
            for i, t in enumerate(tweets, 1):
                print(f"\n{i}. {format_tweet(t)}")
        else:
            print(f"Could not fetch tweets for @{username}")

    elif cmd == "tweet" and len(sys.argv) >= 3:
        tweet_id = sys.argv[2]
        username = sys.argv[3] if len(sys.argv) >= 4 else None
        tweet = get_tweet(tweet_id, username)
        if tweet:
            print(format_tweet(tweet))
        else:
            print(f"Could not fetch tweet {tweet_id}")

    elif cmd == "search" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        tweets = search_tweets(query)
        if tweets:
            print(f"Search: '{query}' ({len(tweets)} results):")
            for i, t in enumerate(tweets, 1):
                print(f"\n{i}. {format_tweet(t)}")
        else:
            print(f"No results for '{query}'")

    elif cmd == "url" and len(sys.argv) >= 3:
        url = sys.argv[2]
        tweet_id = extract_tweet_id_from_url(url)
        if tweet_id:
            tweet = get_tweet(tweet_id)
            if tweet:
                print(format_tweet(tweet))
            else:
                print(f"Could not fetch tweet {tweet_id}")
        else:
            print(f"Could not extract tweet ID from URL: {url}")

    elif cmd == "trending":
        print("Trending not yet implemented via Nitter RSS")

    else:
        print(__doc__)
