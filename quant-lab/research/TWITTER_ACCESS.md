# X/Twitter Access for Agents

> **Created:** 2026-05-17 per MAD directive

## Method 1: fxtwitter API (Preferred — No Login Needed)
```
https://api.fxtwitter.com/[username]/status/[tweet_id]
```
Returns full tweet content as JSON including article text for long posts.

Example:
```
https://api.fxtwitter.com/RohOnChain/status/2041180375838498950
```

## Method 2: Browser (Fallback)
Use the `browser` tool to open x.com directly. No login needed for public posts.
```
browser action=open url=https://x.com/[username]/status/[tweet_id]
browser action=snapshot
```

## Method 3: web_fetch
```
web_fetch url=https://x.com/[username]/status/[tweet_id]
```
May not work due to X bot detection. Use fxtwitter or browser instead.

## Key Accounts to Monitor
- @RohOnChain — Alpha combination, prediction markets, quant frameworks
- Search for: "forex trading strategy", "EUR/USD", "algorithmic trading"
