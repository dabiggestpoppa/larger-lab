# Gmail Search Syntax

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Gmail Search Syntax

Standard Gmail search operators work in the `query` argument.

## Common Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `is:unread` | `is:unread` | Unread messages |
| `is:starred` | `is:starred` | Starred messages |
| `is:important` | `is:important` | Important messages |
| `in:inbox` | `in:inbox` | Inbox only |
| `in:sent` | `in:sent` | Sent folder |
| `in:drafts` | `in:drafts` | Drafts |
| `in:trash` | `in:trash` | Trash |
| `in:anywhere` | `in:anywhere` | All mail including spam/trash |
| `from:` | `from:alice@example.com` | Sender |
| `to:` | `to:bob@example.com` | Recipient |
| `cc:` | `cc:team@example.com` | CC recipient |
| `subject:` | `subject:invoice` | Subject contains |
| `label:` | `label:work` | Has label |
| `has:attachment` | `has:attachment` | Has attachments |
| `filename:` | `filename:pdf` | Attachment filename/type |
| `larger:` | `larger:5M` | Larger than size |
| `smaller:` | `smaller:1M` | Smaller than size |

## Date Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `newer_than:` | `newer_than:7d` | Within last N days (d), months (m), years (y) |
| `older_than:` | `older_than:30d` | Older than N days/months/years |
| `after:` | `after:2026/02/01` | After date (YYYY/MM/DD) |
| `before:` | `before:2026/03/01` | Before date |

## Combining

| Syntax | Example | Description |
|--------|---------|-------------|
| space | `from:alice subject:meeting` | AND (implicit) |
| `OR` | `from:alice OR from:bob` | OR |
| `-` | `-from:noreply@` | NOT (exclude) |
| `()` | `(from:alice OR from:bob) subject:meeting` | Grouping |
| `""` | `"exact phrase"` | Exact phrase match |

## Common Patterns

```
# Unread emails from the last day
is:unread newer_than:1d

# Emails with PDF attachments from a specific sender
from:accounting@company.com has:attachment filename:pdf

# Important unread emails (not promotions/social)
is:unread -category:promotions -category:social

# Emails in a thread about a topic
subject:"Q4 budget" newer_than:30d

# Large attachments to clean up
has:attachment larger:10M older_than:90d
```

LINKS:
[[Architecture]]
[[Claude]]
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
[[Api Endpoints]]
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
