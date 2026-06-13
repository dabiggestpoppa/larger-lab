# 🎬 Content Farm — Presentation, Video & Image Tools

> **Last Updated:** 2026-06-12 | All tools from your GitHub list + tools-catalog

---

## 📊 Presentations & Decks

### Open Design (Forked ✅)
**Location:** `content-farm/design/open-design/` | **Stars:** 63.9k

**Presentation Skills:**
| Skill | Description |
|-------|-------------|
| `deck-guizang-editorial` | Magazine-style web PPT |
| `deck-open-slide-canvas` | Open slide canvas |
| `deck-swiss-international` | Swiss International-style deck |
| `frontend-slides` | Frontend slide decks |
| `slides` | General slide generation |

**Output Formats:** HTML, PDF, PPTX, MP4  
**Design Systems:** 150 brand-grade (Linear, Stripe, Vercel, Airbnb, Apple, Tesla, Notion, etc.)  
**Plugins:** 261 official plugins

### D2 Diagrams (Forked ✅)
**Location:** `tools/d2/` | **Stars:** 24.4k

Text-to-diagram for architecture docs, flowcharts, system diagrams. Exports SVG/PNG/PDF.

---

## 🎬 Video Tools

### Already Forked
| Repo | Location | Purpose |
|------|----------|---------|
| `averygan/reclip` | `content-farm/sites/reclip/` | Self-hosted video downloader (1000+ sites) |
| `LottieFiles/dotlottie-web` | `vtuber_integration/dotlottie-web/` | Animation engine |

### Open Design Video Skills
| Skill | Description |
|-------|-------------|
| `8-bit-orbit-video-template` | 8-bit style video |
| `swiss-user-research-video-template` | User research video |
| `weread-year-in-review-video-template` | Year in review video |
| `video-hyperframes` | HTML → MP4 motion graphics |
| `video-downloader` | Video download skill |
| `fal-video-edit` | AI video editing (Fal.ai) |

### Open Design Video Plugins
| Plugin | Description |
|--------|-------------|
| `video-templates/` | 50+ video templates (HyperFrames, Seedance, Veo) |

### External Video Tools (Free)
| Tool | URL | Purpose |
|------|-----|---------|
| cobalt.tools | https://cobalt.tools | Universal video/audio downloader |
| yt-dlp | https://github.com/yt-dlp/yt-dlp | CLI YouTube downloader |
| 4K Video Downloader | https://www.4kdownload.com | Desktop YouTube downloader |
| greenvideo.cc | https://greenvideo.cc | Bilibili, Weibo, Xiaohongshu |
| tiktokio.bio | https://tiktokio.bio | Watermark-free TikTok |
| savefrom.net | https://en1.savefrom.net/ | Instagram/Facebook |
| openshorts | (search GitHub) | AI video clipping + subtitles |
| openscreen | (search GitHub) | Screen recorder |

---

## 🖼️ Image Tools

### Open Design Image Skills
| Skill | Description |
|-------|-------------|
| `imagegen` | AI image generation |
| `imagegen-frontend-web` | Web-focused image generation |
| `imagegen-frontend-mobile` | Mobile-focused image generation |
| `imagen` | Google Imagen integration |
| `image-enhancer` | Image enhancement |
| `image-to-code-skill` | Image → code conversion |
| `fal-image-edit` | AI image editing (Fal.ai) |
| `venice-image-generate` | Venice AI image generation |
| `venice-image-edit` | Venice AI image editing |
| `ecommerce-image-workflow` | E-commerce image pipeline |
| `pixelbin-media` | Media management |

### Open Design Image Plugins
| Plugin | Description |
|--------|-------------|
| `image-templates/` | 45+ image prompt templates |

### External Image Tools (Free)
| Tool | URL | Purpose |
|------|-----|---------|
| Photopea | https://photopea.com | Browser Photoshop |
| MagicEraser | https://magiceraser.org | Image watermark removal |
| TinyWow | https://tinywow.com | 300+ free tools |

---

## 🎙️ Voice & Audio

| Repo | Location | Replaces | Purpose |
|------|----------|----------|---------|
| `dograh-hq/dograh` | `vtuber_integration/dograh/` | Vapi + Retell | Self-hosted voice AI |
| `jamiepine/voicebox` | `tools/voicebox/` | ElevenLabs | Local voice cloning |
| `debpalash/OmniVoice-Studio` | Not forked | ElevenLabs | Multi-engine TTS |
| `openai/whisper` | Not forked | Otter.ai | Open-source STT |

---

## 📱 Social Media Templates

### Content Engine (Exists ✅)
| Template | Description |
|----------|-------------|
| `TIKTOK_TEMPLATE.md` | TikTok content template |
| `TWEET_TEMPLATE.md` | Twitter/X post template |

### Open Design Social Skills
| Skill | Description |
|-------|-------------|
| `social-x-post-card` | X/Twitter post card |
| `social-reddit-card` | Reddit post card |
| `social-spotify-card` | Spotify-style card |

---

## 🎯 Recommended Workflow

### Create a Presentation
```bash
# 1. Generate deck with Open Design
cd content-farm/design/open-design
od plugin run deck-swiss-international --brief "MAD LABS Q2 Report"

# 2. Add diagrams with D2
d2 architecture.d2 architecture.svg

# 3. Export to PPTX/PDF (built into Open Design)
```

### Create Social Media Content
```bash
# 1. Generate image
od plugin run imagegen --brief "Dark scientific dashboard visualization"

# 2. Create post card
od plugin run social-x-post-card --brief "New trading system live"

# 3. Download reference videos
cd content-farm/sites/reclip
python app.py  # Web UI at localhost:8899
```

### Create Video Content
```bash
# 1. Download source videos (ReClip or cobalt.tools)
# 2. Generate shorts (Open Design video-hyperframes)
# 3. Add animations (dotlottie-web)
```

---

## 📋 Fork Status

| Repo | Forked | Location |
|------|--------|----------|
| nexu-io/open-design | ✅ | `content-farm/design/open-design/` |
| averygan/reclip | ✅ | `content-farm/sites/reclip/` |
| LottieFiles/dotlottie-web | ✅ | `vtuber_integration/dotlottie-web/` |
| dograh-hq/dograh | ✅ | `vtuber_integration/dograh/` |
| jamiepine/voicebox | ✅ | `tools/voicebox/` |
| capcom6/android-sms-gateway | ✅ | `tools/sms-gateway/` |
| terrastruct/d2 | ✅ | `tools/d2/` |
| mattpocock/skills | ✅ | `skills/` |
| Leonxlnx/taste-skill | ✅ | `skills/taste-skill/` |
| virgiliojr94/book-to-skill | ✅ | `core/cognition/procedural/book-to-skill/` |
| microsoft/markitdown | ✅ | `core/parser/markitdown/` |
| opendataloader-project | ✅ | `core/parser/odl-pdf/` |
| run-llama/liteparse | ✅ | `core/parser/liteparse/` |
| datalab-to/chandra | ✅ | `core/parser/chandra/` |
| RyanCodrai/turbovec | ✅ | `core/semantic/vector/turbovec/` |
| teng-lin/notebooklm-py | ✅ | `content-farm/github-repos/notebooklm-py/` |
| Thysrael/Horizon | ✅ | `core/research/horizon/` |
| debpalash/OmniVoice-Studio | ❌ | Needs forking |
| unslothai/unsloth | ❌ | Needs forking |
