# Api Endpoints

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Polymarket API Endpoints Reference

All endpoints are public REST (GET), return JSON, and need no authentication.

## Gamma API — gamma-api.polymarket.com

### Search Markets

```
GET /public-search?q=QUERY
```

Response structure:
```json
{
  "events": [
    {
      "id": "12345",
      "title": "Event title",
      "slug": "event-slug",
      "volume": 1234567.89,
      "markets": [
        {
          "question": "Will X happen?",
          "outcomePrices": "[\"0.65\", \"0.35\"]",
          "outcomes": "[\"Yes\", \"No\"]",
          "clobTokenIds": "[\"TOKEN_YES\", \"TOKEN_NO\"]",
          "conditionId": "0xabc...",
          "volume": 500000
        }
      ]
    }
  ],
  "pagination": {"hasMore": true, "totalResults": 100}
}
```

### List Events

```
GET /events?limit=N&active=true&closed=false&order=volume&ascending=false
```

Parameters:
- `limit` — max results (default varies)
- `offset` — pagination offset
- `active` — true/false
- `closed` — true/false
- `order` — sort field: `volume`, `createdAt`, `updatedAt`
- `ascending` — true/false
- `tag` — filter by tag slug
- `slug` — get specific event by slug

Response: array of event objects. Each event includes a `markets` array.

Event fields: `id`, `title`, `slug`, `description`, `volume`, `liquidity`,
`openInterest`, `active`, `closed`, `category`, `startDate`, `endDate`,
`markets` (array of market objects).

### List Markets

```
GET /markets?limit=N&active=true&closed=false&order=volume&ascending=false
```

Same filter parameters as events, plus:
- `slug` — get specific market by slug

Market fields: `id`, `question`, `conditionId`, `slug`, `description`,
`outcomes`, `outcomePrices`, `volume`, `liquidity`, `active`, `closed`,
`marketType`, `clobTokenIds`, `endDate`, `category`, `createdAt`.

Important: `outcomePrices`, `outcomes`, and `clobTokenIds` are JSON strings
(double-encoded). Parse with json.loads() in Python.

### List Tags

```
GET /tags
```

Returns array of tag objects: `id`, `label`, `slug`.
Use the `slug` value when filtering events/markets by tag.

---

## CLOB API — clob.polymarket.com

All CLOB price endpoints use `token_id` from the market's `clobTokenIds` field.
Index 0 = Yes outcome, Index 1 = No outcome.

### Current Price

```
GET /price?token_id=TOKEN_ID&side=buy
```

Response: `{"price": "0.650"}`

The `side` parameter: `buy` or `sell`.

### Midpoint Price

```
GET /midpoint?token_id=TOKEN_ID
```

Response: `{"mid": "0.645"}`

### Spread

```
GET /spread?token_id=TOKEN_ID
```

Response: `{"spread": "0.02"}`

### Orderbook

```
GET /book?token_id=TOKEN_ID
```

Response:
```json
{
  "market": "condition_id",
  "asset_id": "token_id",
  "bids": [{"price": "0.64", "size": "500"}, ...],
  "asks": [{"price": "0.66", "size": "300"}, ...],
  "min_order_size": "5",
  "tick_size": "0.01",
  "last_trade_price": "0.65"
}
```

Bids and asks are sorted by price. Size is in shares (USDC-denominated).

### Price History

```
GET /prices-history?market=CONDITION_ID&interval=INTERVAL&fidelity=N
```

Parameters:
- `market` — the conditionId (hex string with 0x prefix)
- `interval` — time range: `all`, `1d`, `1w`, `1m`, `3m`, `6m`, `1y`
- `fidelity` — number of data points to return

Response:
```json
{
  "history": [
    {"t": 1709000000, "p": "0.55"},
    {"t": 1709100000, "p": "0.58"}
  ]
}
```

`t` is Unix timestamp, `p` is price (probability).

Note: Very new markets may return empty history.

### CLOB Markets List

```
GET /markets?limit=N
```

Response:
```json
{
  "data": [
    {
      "condition_id": "0xabc...",
      "question": "Will X?",
      "tokens": [
        {"token_id": "123...", "outcome": "Yes", "price": 0.65},
        {"token_id": "456...", "outcome": "No", "price": 0.35}
      ],
      "active": true,
      "closed": false
    }
  ],
  "next_cursor": "cursor_string",
  "limit": 100,
  "count": 1000
}
```

---

## Data API — data-api.polymarket.com

### Recent Trades

```
GET /trades?limit=N
GET /trades?market=CONDITION_ID&limit=N
```

Trade fields: `side` (BUY/SELL), `size`, `price`, `timestamp`,
`title`, `slug`, `outcome`, `transactionHash`, `conditionId`.

### Open Interest

```
GET /oi?market=CONDITION_ID
```

---

## Field Cross-Reference

To go from a Gamma market to CLOB data:

1. Get market from Gamma: has `clobTokenIds` and `conditionId`
2. Parse `clobTokenIds` (JSON string): `["YES_TOKEN", "NO_TOKEN"]`
3. Use YES_TOKEN with `/price`, `/book`, `/midpoint`, `/spread`
4. Use `conditionId` with `/prices-history` and Data API endpoints

LINKS:
[[Architecture]]
[[Api Reference]]
[[Claude]]
[[Api Execution Architecture 20260531]]
[[Api Reference Summary]]
[[Api Test Note]]
[[Tradovate Api Discovery 20260531]]
[[3D Scene]]
[[Action]]
[[Advanced Usage]]
[[Aged Academia]]
[[Airbnb]]
[[Airtable]]
[[Analysis Framework]]
[[Analysis Modules]]
[[Animation]]
[[Animations]]
[[Animation Design Thinking]]
[[Api Evaluation]]
[[Apple]]
[[Artifacts]]
[[Attribution]]
[[Audio Reactive]]
[[Autoreason Methodology]]
[[Auto Selection]]
[[Base Prompt]]
[[Benchmark Guide]]
[[Bento Grid]]
[[Binary Comparison]]
[[Block Types]]
[[Blueprint]]
[[Bmw]]
[[Bold Graphic]]
[[Bridge]]
[[Bug Report]]
[[Cal]]
[[Camera And 3D]]
[[Chalk]]
[[Chalkboard]]
[[Character Template]]
[[Checklists]]
[[Cinematic]]
[[Circular Flow]]
[[Citation Workflow]]
[[Ci Troubleshooting]]
[[Clay]]
[[Claymation]]
[[Clickhouse]]
[[Cohere]]
[[Coinbase]]
[[Colors]]
[[Color Systems]]
[[Comic Strip]]
[[Comparison Matrix]]
[[Composio]]
[[Composition]]
[[Concept Story]]
[[Configuration]]
[[Context Budget Discipline]]
[[Conventional Commits]]
[[Core Api]]
[[Corporate Memphis]]
[[Craft Handmade]]
[[Cursor]]
[[Custom Tasks]]
[[Cyberpunk Neon]]
[[Dark Mode]]
[[Dashboard]]
[[Dat Scripting]]
[[Decorations]]
[[Dense]]
[[Dense Modules]]
[[Description]]
[[Distributed Eval]]
[[Dogfood Report Template]]
[[Dramatic]]
[[Editing]]
[[Editorial]]
[[Effects]]
[[Elegant]]
[[Elevenlabs]]
[[Energetic]]
[[Equations]]
[[Examples]]
[[Experiment Patterns]]
[[Expo]]
[[Export Pipeline]]
[[External Data]]
[[Failures]]
[[Fantasy Animation]]
[[Feature Request]]
[[Figma]]
[[Flat]]
[[Flat Doodle]]
[[Formatting]]
[[Four Panel]]
[[Framer]]
[[Full Prompt Library]]
[[Funnel]]
[[Gates Taxonomy]]
[[Geometry Comp]]
[[Github Api Cheatsheet]]
[[Glsl]]
[[Gmail Search Syntax]]
[[Graphs And Data]]
[[Hand Drawn Edu]]
[[Hashicorp]]
[[Heuristics]]
[[Hierarchical Layers]]
[[Hub Discovery]]
[[Hub Spoke]]
[[Human Evaluation]]
[[Ibm]]
[[Iceberg]]
[[Ikea Manual]]
[[Ink Brush]]
[[Ink Notes]]
[[Inputs]]
[[Integrations]]
[[Interaction]]
[[Intercom]]
[[Intuition Machine]]
[[Isometric Map]]
[[Issue Taxonomy]]
[[Jailbreak Templates]]
[[Jigsaw]]
[[Kawaii]]
[[Knolling]]
[[Kraken]]
[[Layout Compositor]]
[[Lego Brick]]
[[Ligne Claire]]
[[Linear.App]]
[[Linear Progression]]
[[Lovable]]
[[Macaron]]
[[Manga]]
[[Mcp Tools]]
[[Message Composition]]
[[Methods Guide]]
[[Midi Osc]]
[[Minimal]]
[[Minimalist]]
[[Minimax]]
[[Mintlify]]
[[Miro]]
[[Mistral.Ai]]
[[Mixed]]
[[Mobjects]]
[[Modules]]
[[Mongodb]]
[[Mono Ink]]
[[Morandi Journal]]
[[Nature]]
[[Neon]]
[[Network Patterns]]
[[Neutral]]
[[Notion]]
[[Nvidia]]
[[Official Cli]]
[[Ohmsha]]
[[Ohmsha Guide]]
[[Ollama]]
[[Opencode.Ai]]
[[Operators]]
[[Operator Tips]]
[[Optimization]]
[[Optimizers]]
[[Origami]]
[[Output Formats]]
[[Palettes]]
[[Panel Ui]]
[[Paper Explainer]]
[[Paper Types]]
[[Partial Workflows]]
[[Particles]]
[[Patterns]]
[[Periodic Table]]
[[Pinterest]]
[[Pitfalls]]
[[Pixel Art]]
[[Playful]]
[[Pmb Codex Lane Prompt]]
[[Pop Laboratory]]
[[Port Notes]]
[[Postfx]]
[[Posthog]]
[[Pptxgenjs]]
[[Production Quality]]
[[Projection Mapping]]
[[Prompt Construction]]
[[Pr Body Bugfix]]
[[Pr Body Feature]]
[[Python Api]]
[[Quantization]]
[[Raycast]]
[[Realistic]]
[[Refusal Detection]]
[[Rendering]]
[[Replicate]]
[[Replicator]]
[[Resend]]
[[Rest Api]]
[[Retro]]
[[Retro Pop Grid]]
[[Reviewer Guidelines]]
[[Review Output Template]]
[[Revolut]]
[[Romantic]]
[[Runwayml]]
[[Sanity]]
[[Scenes]]
[[Scene Planning]]
[[Scientific]]
[[Screen Print]]
[[Sentry]]
[[Server]]
[[Server Deployment]]
[[Shaders]]
[[Shapes And Geometry]]
[[Shoujo]]
[[Sketch]]
[[Sketch Notes]]
[[Skill]]
[[Sources]]
[[Spacex]]
[[Splash]]
[[Spotify]]
[[Standard]]
[[Starter]]
[[Storyboard Template]]
[[Storybook Watercolor]]
[[Story Mountain]]
[[Stripe]]
[[Structural Breakdown]]
[[Structured Content Template]]
[[Styles]]
[[Style Presets]]
[[Subway Map]]
[[Supabase]]
[[Superhuman]]
[[Sweeps]]
[[System]]
[[Technical Schematic]]
[[Template Integrity]]
[[Together.Ai]]
[[Tree Branching]]
[[Troubleshooting]]
[[Typography]]
[[Uber]]
[[Ui Wireframe]]
[[Updaters And Trackers]]
[[Usage]]
[[Vector Illustration]]
[[Venn Diagram]]
[[Vercel]]
[[Vintage]]
[[Visual Design]]
[[Visual Effects]]
[[Voltagent]]
[[Warm]]
[[Warp]]
[[Watercolor]]
[[Webflow]]
[[Webgl And 3D]]
[[Webtoon]]
[[Winding Roadmap]]
[[Wise]]
[[Workflow]]
[[Workflow Format]]
[[Writing Guide]]
[[Wuxia]]
[[X.Ai]]
[[Zapier]]
