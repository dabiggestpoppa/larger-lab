# Gates Taxonomy

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Gates Taxonomy

Canonical gate types for validation checkpoints across any workflow that spawns subagents, runs review loops, or has human-approval pauses. Every validation checkpoint maps to one of these four types — naming them explicitly makes the workflow legible and prevents "what happens when this check fails?" confusion.

Adapted from the GSD (Get Shit Done) project's gates reference — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)).

## The four gate types

### 1. Pre-flight gate

**Purpose:** Validates preconditions before starting an operation.

**Behavior:** Blocks entry if conditions unmet. No partial work created — bail before anything changes.

**Recovery:** Fix the missing precondition, then retry.

**Examples:**
- Implementation phase checks that the plan file exists before it starts writing code.
- Delegated subagent checks that required env vars are set before making API calls.
- Commit checks that tests passed before pushing.

### 2. Revision gate

**Purpose:** Evaluates output quality and routes to revision if insufficient.

**Behavior:** Loops back to the producer with specific feedback. Bounded by an iteration cap (typically 3).

**Recovery:** Producer addresses feedback; checker re-evaluates. The loop escalates early if issue count does not decrease between consecutive iterations (stall detection). After max iterations, escalates to the user unconditionally — never loop forever.

**Examples:**
- Plan reviewer reads a draft plan, returns specific issues, planner revises, reviewer re-reads (max 3 cycles).
- Code reviewer checks subagent-produced code against must-haves; dispatches fixes back to the implementer if any must-have failed.
- Test coverage checker validates new tests exercise the new paths; if not, sends back to author.

### 3. Escalation gate

**Purpose:** Surfaces unresolvable issues to the human for a decision.

**Behavior:** Pauses workflow, presents options, waits for human input. Never guesses, never picks a default.

**Recovery:** Human chooses action; workflow resumes on the selected path.

**Examples:**
- Revision loop exhausted after 3 iterations.
- Merge conflict during automated worktree cleanup.
- Ambiguous requirement — two reasonable interpretations and the choice changes the approach.
- Subagent reports "the plan says X but the codebase actually does Y" — human decides which is right.

### 4. Abort gate

**Purpose:** Terminates the operation to prevent damage or waste.

**Behavior:** Stops immediately, preserves state (checkpoint current progress), reports the specific reason.

**Recovery:** Human investigates root cause, fixes, restarts from checkpoint.

**Examples:**
- Context window critically low during execution (POOR tier, >70%) — abort cleanly rather than produce truncated output.
- Critical dependency unavailable mid-run (network down, API key revoked).
- Unrecoverable filesystem state (disk full, permissions lost).
- Safety invariant violated (agent attempted an irreversible destructive action outside approved scope).

## How to use this in a skill

When you write an orchestration skill that has validation checkpoints, **name each checkpoint by its gate type explicitly** and answer three questions:

1. **What condition triggers this gate?** (e.g., "plan file missing", "issue count didn't decrease", "context >70%")
2. **What happens when it fails?** (block / loop back / ask human / abort)
3. **Who resumes, and from where?** (fix precondition + retry, revise + re-check, human decision, restart from checkpoint)

Answering these three up front means your skill never hits "what do we do now?" at runtime.

## Example — a review loop with all four gate types

```
[Pre-flight] plan.md exists and is non-empty?   → no: bail, ask user to write a plan first
                ↓ yes
[Execute]  subagent implements task
                ↓
[Revision] reviewer checks against must-haves  → fail: loop back to subagent (max 3)
                ↓ pass
[Pre-flight] tests pass?                       → no: bail, report failing tests
                ↓ yes
[Commit]
                ↓
(on revision loop exhaustion)
[Escalation] "3 review cycles failed to converge on issue X — pick: force-merge, rewrite task, abandon"
                ↓ user picks
(on any tier-POOR context pressure during loop)
[Abort] "context at 73%, checkpointing and stopping"
```

The vocabulary is small on purpose. Every gate in every workflow should fit one of these four. If you find yourself inventing a fifth, it's probably a revision gate with extra branching, or an escalation gate in disguise.

LINKS:
[[Architecture]]
[[Agents]]
[[Claude]]
[[User]]
[[Progress]]
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
[[Taxonomy]]
[[Test Taxonomy]]
