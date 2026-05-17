---
name: lazyweb
description: Install and use Lazyweb MCP for AI-agent design research, UI references, screenshots, comparisons, and design feedback.
version: 1.0.0
tags:
  - design-research
  - ui-references
  - mcp
---

# Lazyweb

Use this skill when the user asks for UI inspiration, design research, app screenshots, product flow examples, onboarding patterns, pricing or paywall examples, competitive UI references, or feedback on an existing interface.

Lazyweb gives the agent access to real product screenshots and design patterns through the Lazyweb MCP server.

## Token

The Lazyweb MCP token is stored in `~/.lazyweb/lazyweb_mcp_token`. It is a free no-billing bearer token for UI reference and design research tools.

## Setup (already configured)

Lazyweb MCP is configured in OpenClaw config under `mcp.servers.lazyweb`:
- URL: `https://www.lazyweb.com/mcp`
- Transport: Streamable HTTP
- Auth: Bearer token in config

## When To Use

- Before creating a landing page, app screen, onboarding flow, checkout, pricing page, dashboard, settings page, or mobile app UI.
- When asked to compare a design against real products.
- When asked to improve a screenshot or produce design recommendations.
- When a coding agent needs concrete UI examples instead of generic visual guesses.
- Multi-team architecture and workflow design — use for design material and template references.

## When Not To Use

- Backend-only tasks.
- Database schema work.
- Legal, medical, finance, or non-design research.
- Generic code cleanup with no UI or product-design component.

## Available MCP Tools

- `lazyweb_health` — Check Lazyweb service health
- `lazyweb_search` — Search for UI references, screenshots, design patterns
- Additional tools may be available depending on Lazyweb's current MCP surface

## Usage Examples

```
# Check health
lazyweb_health

# Search for pricing page examples
lazyweb_search {"query": "pricing page", "limit": 3}

# Search for onboarding flows
lazyweb_search {"query": "mobile app onboarding flow", "limit": 5}

# Search for dashboard UI
lazyweb_search {"query": "analytics dashboard dark mode", "limit": 5}
```

## Pricing

Lazyweb is free for humans and agents. There are no product rate limits for the V1 MCP setup path.
