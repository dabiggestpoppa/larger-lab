# Miro

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Design System: Miro


> **Hermes Agent — Implementation Notes**
>
> The original site uses proprietary fonts. For self-contained HTML output, use these CDN substitutes:
> - **Primary:** `Inter` | **Mono:** `system monospace stack`
> - **Font stack (CSS):** `font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;`
> - **Mono stack (CSS):** `font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;`
> ```html
> <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
> ```
> Use `write_file` to create HTML, serve via `generative-widgets` skill (cloudflared tunnel).
> Verify visual accuracy with `browser_vision` after generating.

## 1. Visual Theme & Atmosphere

Miro's website is a clean, collaborative-tool-forward platform that communicates "visual thinking" through generous whitespace, pastel accent colors, and a confident geometric font. The design uses a predominantly white canvas with near-black text (`#1c1c1e`) and a distinctive pastel color palette — coral, rose, teal, orange, yellow, moss — each representing different collaboration contexts.

The typography uses Roobert PRO Medium as the primary display font with OpenType character variants (`"blwf", "cv03", "cv04", "cv09", "cv11"`) and negative letter-spacing (-1.68px at 56px). Noto Sans handles body text with its own stylistic set (`"liga" 0, "ss01", "ss04", "ss05"`). The design is built with Framer, giving it smooth animations and modern component patterns.

**Key Characteristics:**
- White canvas with near-black (`#1c1c1e`) text
- Roobert PRO Medium with multiple OpenType character variants
- Pastel accent palette: coral, rose, teal, orange, yellow, moss (light + dark pairs)
- Blue 450 (`#5b76fe`) as primary interactive color
- Success green (`#00b473`) for positive states
- Generous border-radius: 8px–50px range
- Framer-built with smooth motion patterns
- Ring shadow border: `rgb(224,226,232) 0px 0px 0px 1px`

## 2. Color Palette & Roles

### Primary
- **Near Black** (`#1c1c1e`): Primary text
- **White** (`#ffffff`): `--tw-color-white`, primary surface
- **Blue 450** (`#5b76fe`): `--tw-color-blue-450`, primary interactive
- **Actionable Pressed** (`#2a41b6`): `--tw-color-actionable-pressed`

### Pastel Accents (Light/Dark pairs)
- **Coral**: Light `#ffc6c6` / Dark `#600000`
- **Rose**: Light `#ffd8f4` / Dark (implied)
- **Teal**: Light `#c3faf5` / Dark `#187574`
- **Orange**: Light `#ffe6cd`
- **Yellow**: Dark `#746019`
- **Moss**: Dark `#187574`
- **Pink** (`#fde0f0`): Soft pink surface
- **Red** (`#fbd4d4`): Light red surface
- **Dark Red** (`#e3c5c5`): Muted red

### Semantic
- **Success** (`#00b473`): `--tw-color-success-accent`

### Neutral
- **Slate** (`#555a6a`): Secondary text
- **Input Placeholder** (`#a5a8b5`): `--tw-color-input-placeholder`
- **Border** (`#c7cad5`): Button borders
- **Ring** (`rgb(224,226,232)`): Shadow-as-border

## 3. Typography Rules

### Font Families
- **Display**: `Roobert PRO Medium`, fallback: Placeholder — `"blwf", "cv03", "cv04", "cv09", "cv11"`
- **Display Variants**: `Roobert PRO SemiBold`, `Roobert PRO SemiBold Italic`, `Roobert PRO`
- **Body**: `Noto Sans` — `"liga" 0, "ss01", "ss04", "ss05"`

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Display Hero | Roobert PRO Medium | 56px | 400 | 1.15 | -1.68px |
| Section Heading | Roobert PRO Medium | 48px | 400 | 1.15 | -1.44px |
| Card Title | Roobert PRO Medium | 24px | 400 | 1.15 | -0.72px |
| Sub-heading | Noto Sans | 22px | 400 | 1.35 | -0.44px |
| Feature | Roobert PRO Medium | 18px | 600 | 1.35 | normal |
| Body | Noto Sans | 18px | 400 | 1.45 | normal |
| Body Standard | Noto Sans | 16px | 400–600 | 1.50 | -0.16px |
| Button | Roobert PRO Medium | 17.5px | 700 | 1.29 | 0.175px |
| Caption | Roobert PRO Medium | 14px | 400 | 1.71 | normal |
| Small | Roobert PRO Medium | 12px | 400 | 1.15 | -0.36px |
| Micro Uppercase | Roobert PRO | 10.5px | 400 | 0.90 | uppercase |

## 4. Component Stylings

### Buttons
- Outlined: transparent bg, `1px solid #c7cad5`, 8px radius, 7px 12px padding
- White circle: 50% radius, white bg with shadow
- Blue primary (implied from interactive color)

### Cards: 12px–24px radius, pastel backgrounds
### Inputs: white bg, `1px solid #e9eaef`, 8px radius, 16px padding

## 5. Layout Principles
- Spacing: 1–24px base scale
- Radius: 8px (buttons), 10px–12px (cards), 20px–24px (panels), 40px–50px (large containers)
- Ring shadow: `rgb(224,226,232) 0px 0px 0px 1px`

## 6. Depth & Elevation
Minimal — ring shadow + pastel surface contrast

## 7. Do's and Don'ts
### Do
- Use pastel light/dark pairs for feature sections
- Apply Roobert PRO with OpenType character variants
- Use Blue 450 (#5b76fe) for interactive elements
### Don't
- Don't use heavy shadows
- Don't mix more than 2 pastel accents per section

## 8. Responsive Behavior
Breakpoints: 425px, 576px, 768px, 896px, 1024px, 1200px, 1280px, 1366px, 1700px, 1920px

## 9. Agent Prompt Guide
### Quick Color Reference
- Text: Near Black (`#1c1c1e`)
- Background: White (`#ffffff`)
- Interactive: Blue 450 (`#5b76fe`)
- Success: `#00b473`
- Border: `#c7cad5`
### Example Component Prompts
- "Create hero: white background. Roobert PRO Medium 56px, line-height 1.15, letter-spacing -1.68px. Blue CTA (#5b76fe). Outlined secondary (1px solid #c7cad5, 8px radius)."

LINKS:
[[Architecture]]
[[Claude]]
[[Principles]]
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
