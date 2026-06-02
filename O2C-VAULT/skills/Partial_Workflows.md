# Partial Workflows

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Partial Workflows

Options to run specific parts of the workflow. Trigger these via natural language (e.g., "just the storyboard", "regenerate page 3").

## Options Summary

| Option | Steps Executed | Output |
|--------|----------------|--------|
| Storyboard only | 1-3 | `storyboard.md` + `characters/` |
| Prompts only | 1-5 | + `prompts/*.md` |
| Images only | 7-8 | + images |
| Regenerate N | 7 (partial) | Specific page(s) |

---

## Storyboard-only

Generate storyboard and characters without prompts or images.

**User cue**: "storyboard only", "just the outline", "don't generate images yet".

**Workflow**: Steps 1-3 only (stop after storyboard + characters)

**Output**:
- `analysis.md`
- `storyboard.md`
- `characters/characters.md`

**Use case**: Review and edit the storyboard before generating images. Useful for:
- Getting feedback on the narrative structure
- Making manual adjustments to panel layouts
- Defining custom characters

---

## Prompts-only

Generate storyboard, characters, and prompts without images.

**User cue**: "prompts only", "write the prompts but don't generate yet".

**Workflow**: Steps 1-5 (generate prompts, skip images)

**Output**:
- `analysis.md`
- `storyboard.md`
- `characters/characters.md`
- `prompts/*.md`

**Use case**: Review and edit prompts before image generation. Useful for:
- Fine-tuning image generation prompts
- Ensuring visual consistency before committing to generation
- Making style adjustments at the prompt level

---

## Images-only

Generate images from existing prompts (starts at Step 7).

**User cue**: "generate images from existing prompts", "run the images now" (pointing at an existing `comic/topic-slug/` directory).

**Workflow**: Skip to Step 7, then 8

**Prerequisites** (must exist in directory):
- `prompts/` directory with page prompt files
- `storyboard.md` with style information
- `characters/characters.md` with character definitions

**Output**:
- `characters/characters.png` (if not exists)
- `NN-{cover|page}-[slug].png` images

**Use case**: Re-generate images after editing prompts. Useful for:
- Recovering from failed image generation
- Trying different image generation settings
- Regenerating after manual prompt edits

---

## Regenerate

Regenerate specific pages only.

**User cue**: "regenerate page 3", "redo pages 2, 5, 8", "regenerate the cover".

**Workflow**:
1. Read existing prompts for specified pages
2. Regenerate images only for those pages via `image_generate`
3. Download each returned URL and overwrite the existing PNG

**Prerequisites** (must exist):
- `prompts/NN-{cover|page}-[slug].md` for specified pages
- `characters/characters.md` (for agent-side consistency checks, if it was used originally)

**Output**:
- Regenerated `NN-{cover|page}-[slug].png` for specified pages

**Use case**: Fix specific pages without regenerating entire comic. Useful for:
- Fixing a single problematic page
- Iterating on specific visuals
- Regenerating pages after prompt edits

**Page numbering**:
- `0` = Cover page
- `1-N` = Content pages

LINKS:
[[Architecture]]
[[Claude]]
[[User]]
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
