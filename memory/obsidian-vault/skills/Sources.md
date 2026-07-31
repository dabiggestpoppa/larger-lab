# Sources

> Category: skills | Imported: 2026-06-02 01:13 UTC

Tags: #skills

# Source Bibliography

This document lists all authoritative sources used to build this skill, organized by topic.

---

## Origin & Attribution

The writing philosophy, citation verification workflow, and conference reference materials in this skill were originally compiled by **[Orchestra Research](https://github.com/orchestra-research)** as the `ml-paper-writing` skill (January 2026), drawing on Neel Nanda's blog post and other researcher guides listed below. The skill was integrated into hermes-agent by teknium (January 2026), then expanded into the current `research-paper-writing` pipeline by SHL0MS (April 2026, PR #4654), which added experiment design, execution monitoring, iterative refinement, and submission phases while preserving the original writing philosophy and reference files.

---

## Writing Philosophy & Guides

### Primary Sources (Must-Read)

| Source | Author | URL | Key Contribution |
|--------|--------|-----|------------------|
| **Highly Opinionated Advice on How to Write ML Papers** | Neel Nanda | [Alignment Forum](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) | Narrative framework, "What/Why/So What", time allocation |
| **How to Write ML Papers** | Sebastian Farquhar (DeepMind) | [Blog](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/) | 5-sentence abstract formula, structure templates |
| **A Survival Guide to a PhD** | Andrej Karpathy | [Blog](http://karpathy.github.io/2016/09/07/phd/) | Paper structure recipe, contribution framing |
| **Heuristics for Scientific Writing** | Zachary Lipton (CMU) | [Blog](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/) | Word choice, section balance, intensifier warnings |
| **Advice for Authors** | Jacob Steinhardt (UC Berkeley) | [Blog](https://jsteinhardt.stat.berkeley.edu/blog/advice-for-authors) | Precision over brevity, consistent terminology |
| **Easy Paper Writing Tips** | Ethan Perez (Anthropic) | [Blog](https://ethanperez.net/easy-paper-writing-tips/) | Micro-level tips, apostrophe unfolding, clarity tricks |

### Foundational Scientific Writing

| Source | Author | URL | Key Contribution |
|--------|--------|-----|------------------|
| **The Science of Scientific Writing** | Gopen & Swan | [PDF](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf) | Topic/stress positions, old-before-new, 7 principles |
| **Summary of Science of Scientific Writing** | Lawrence Crowl | [Summary](https://www.crowl.org/Lawrence/writing/GopenSwan90.html) | Condensed version of Gopen & Swan |

### Additional Resources

| Source | URL | Key Contribution |
|--------|-----|------------------|
| How To Write A Research Paper In ML | [Blog](https://grigorisg9gr.github.io/machine%20learning/research%20paper/how-to-write-a-research-paper-in-machine-learning/) | Practical walkthrough, LaTeX tips |
| A Recipe for Training Neural Networks | [Karpathy Blog](http://karpathy.github.io/2019/04/25/recipe/) | Debugging methodology that translates to paper structure |
| ICML Paper Writing Best Practices | [ICML](https://icml.cc/Conferences/2022/BestPractices) | Official venue guidance |
| Bill Freeman's Writing Slides | [MIT](https://billf.mit.edu/sites/default/files/documents/cvprPapers.pdf) | Visual guide to paper structure |

---

## Official Conference Guidelines

### NeurIPS

| Document | URL | Purpose |
|----------|-----|---------|
| Paper Checklist Guidelines | [NeurIPS](https://neurips.cc/public/guides/PaperChecklist) | 16-item mandatory checklist |
| Reviewer Guidelines 2025 | [NeurIPS](https://neurips.cc/Conferences/2025/ReviewerGuidelines) | Evaluation criteria, scoring |
| Style Files | [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | LaTeX templates |

### ICML

| Document | URL | Purpose |
|----------|-----|---------|
| Paper Guidelines | [ICML](https://icml.cc/Conferences/2024/PaperGuidelines) | Submission requirements |
| Reviewer Instructions 2025 | [ICML](https://icml.cc/Conferences/2025/ReviewerInstructions) | Review form, evaluation |
| Style & Author Instructions | [ICML](https://icml.cc/Conferences/2022/StyleAuthorInstructions) | Formatting specifications |

### ICLR

| Document | URL | Purpose |
|----------|-----|---------|
| Author Guide 2026 | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | Submission requirements, LLM disclosure |
| Reviewer Guide 2025 | [ICLR](https://iclr.cc/Conferences/2025/ReviewerGuide) | Review process, evaluation |

### ACL/EMNLP

| Document | URL | Purpose |
|----------|-----|---------|
| ACL Style Files | [GitHub](https://github.com/acl-org/acl-style-files) | LaTeX templates |
| ACL Rolling Review | [ARR](https://aclrollingreview.org/) | Submission process |

### AAAI

| Document | URL | Purpose |
|----------|-----|---------|
| Author Kit 2026 | [AAAI](https://aaai.org/authorkit26/) | Templates and guidelines |

### COLM

| Document | URL | Purpose |
|----------|-----|---------|
| Template | [GitHub](https://github.com/COLM-org/Template) | LaTeX templates |

---

## Citation APIs & Tools

### APIs

| API | Documentation | Best For |
|-----|---------------|----------|
| **Semantic Scholar** | [Docs](https://api.semanticscholar.org/api-docs/) | ML/AI papers, citation graphs |
| **CrossRef** | [Docs](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | DOI lookup, BibTeX retrieval |
| **arXiv** | [Docs](https://info.arxiv.org/help/api/basics.html) | Preprints, PDF access |
| **OpenAlex** | [Docs](https://docs.openalex.org/) | Open alternative, bulk access |

### Python Libraries

| Library | Install | Purpose |
|---------|---------|---------|
| `semanticscholar` | `pip install semanticscholar` | Semantic Scholar wrapper |
| `arxiv` | `pip install arxiv` | arXiv search and download |
| `habanero` | `pip install habanero` | CrossRef client |

### Citation Verification

| Tool | URL | Purpose |
|------|-----|---------|
| Citely | [citely.ai](https://citely.ai/citation-checker) | Batch verification |
| ReciteWorks | [reciteworks.com](https://reciteworks.com/) | In-text citation checking |

---

## Visualization & Formatting

### Figure Creation

| Tool | URL | Purpose |
|------|-----|---------|
| PlotNeuralNet | [GitHub](https://github.com/HarisIqbal88/PlotNeuralNet) | TikZ neural network diagrams |
| SciencePlots | [GitHub](https://github.com/garrettj403/SciencePlots) | Publication-ready matplotlib |
| Okabe-Ito Palette | [Reference](https://jfly.uni-koeln.de/color/) | Colorblind-safe colors |

### LaTeX Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Overleaf Templates | [Overleaf](https://www.overleaf.com/latex/templates) | Online LaTeX editor |
| BibLaTeX Guide | [CTAN](https://ctan.org/pkg/biblatex) | Modern citation management |

---

## Research on AI Writing & Hallucination

| Source | URL | Key Finding |
|--------|-----|-------------|
| AI Hallucinations in Citations | [Enago](https://www.enago.com/academy/ai-hallucinations-research-citations/) | ~40% error rate |
| Hallucination in AI Writing | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10726751/) | Types of citation errors |
| NeurIPS 2025 AI Report | [ByteIota](https://byteiota.com/neurips-2025-100-ai-hallucinations-slip-through-review/) | 100+ hallucinated citations |

---

## Quick Reference by Topic

### For Narrative & Structure
→ Start with: Neel Nanda, Sebastian Farquhar, Andrej Karpathy

### For Sentence-Level Clarity
→ Start with: Gopen & Swan, Ethan Perez, Zachary Lipton

### For Word Choice & Style
→ Start with: Zachary Lipton, Jacob Steinhardt

### For Conference-Specific Requirements
→ Start with: Official venue guidelines (NeurIPS, ICML, ICLR, ACL)

### For Citation Management
→ Start with: Semantic Scholar API, CrossRef, citation-workflow.md

### For Reviewer Expectations
→ Start with: Venue reviewer guidelines, reviewer-guidelines.md

### For Human Evaluation
→ Start with: human-evaluation.md, Prolific/MTurk documentation

### For Non-Empirical Papers (Theory, Survey, Benchmark, Position)
→ Start with: paper-types.md

---

## Human Evaluation & Annotation

| Source | URL | Key Contribution |
|--------|-----|------------------|
| **Datasheets for Datasets** | Gebru et al., 2021 ([arXiv](https://arxiv.org/abs/1803.09010)) | Structured dataset documentation framework |
| **Model Cards for Model Reporting** | Mitchell et al., 2019 ([arXiv](https://arxiv.org/abs/1810.03993)) | Structured model documentation framework |
| **Crowdsourcing and Human Computation** | [Survey](https://arxiv.org/abs/2202.06516) | Best practices for crowdsourced annotation |
| **Krippendorff's Alpha** | [Wikipedia](https://en.wikipedia.org/wiki/Krippendorff%27s_alpha) | Inter-annotator agreement metric reference |
| **Prolific** | [prolific.co](https://www.prolific.co/) | Recommended crowdsourcing platform for research |

## Ethics & Broader Impact

| Source | URL | Key Contribution |
|--------|-----|------------------|
| **ML CO2 Impact** | [mlco2.github.io](https://mlco2.github.io/impact/) | Compute carbon footprint calculator |
| **NeurIPS Broader Impact Guide** | [NeurIPS](https://neurips.cc/public/guides/PaperChecklist) | Official guidance on impact statements |
| **ACL Ethics Policy** | [ACL](https://www.aclweb.org/portal/content/acl-code-ethics) | Ethics requirements for NLP research |

LINKS:
[[Architecture]]
[[Claude]]
[[Debugging]]
[[Principles]]
[[Tools]]
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
