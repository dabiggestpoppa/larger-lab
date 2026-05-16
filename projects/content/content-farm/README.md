# MAD Content Farm — Project Hub

> **Philosophy:** Systematic scale over creative perfection. Law of numbers.
> **Edge:** Chinese automation tools (free) + OpenClaw orchestration + AI translation

---

## Quick Start

### 1. Android Emulator Setup
```bash
# Install BlueStacks 5 or LDPlayer 9
# Download from: https://www.bluestacks.com or https://www.ldplayer.net

# Configure emulator:
# - Android 11 (API 30)
# - Resolution: 1080x1920
# - RAM: 2GB per instance
# - Enable ADB debugging
```

### 2. DeekeScript Installation
```bash
# Install DeekeScript APK on emulator
# Copy scripts from content-farm/scripts/ to device
# Configure deekeScript.json with your settings
```

### 3. First Automation
```bash
# Deploy dy_auto_engage.js to emulator
# Run via DeekeScript runtime
# Monitor logs in content-farm/logs/
```

---

## Project Structure
```
content-farm/
├── scripts/          # DeekeScript automation scripts
│   ├── dy_auto_engage.js      # 抖音 auto-engagement
│   ├── dy_auto_post.js        # 抖音 auto-posting (TODO)
│   ├── xhs_auto_engage.js     # 小红书 auto-engagement (TODO)
│   └── ks_auto_engage.js      # 快手 auto-engagement (TODO)
├── config/           # Configuration files
│   ├── accounts.json          # Account management
│   └── settings.json          # Farm settings
├── logs/             # Automation logs
├── output/           # Generated content
├── accounts/         # Account credentials (encrypted)
└── templates/        # Content templates
```

---

## Tool Stack

| Tool | Role | Location | Status |
|------|------|----------|--------|
| DeekeScript | Android automation | deekescript/ | ✅ Installed |
| ad-deeke | 抖音 engagement | ad-deeke/ | ✅ Cloned |
| ad-dke | 抖音 commercial | ad-dke/ | ✅ Cloned |
| MoneyPrinterPlus | AI video gen | MoneyPrinterPlus/ | ✅ Cloned |
| ad-voice | AI voice cloning | ad-voice/ | ✅ Cloned |
| MediaCrawler | Data collection | MediaCrawler/ | ✅ Cloned |
| Spider_XHS | 小红书 crawler | Spider_XHS/ | ✅ Cloned |
| deeke-uid | Lead generation | deeke-uid/ | ✅ Cloned |
| shortLink | Attribution | shortLink/ | ✅ Cloned |
| GroupControlApp | Device management | GroupControlApp/ | ✅ Cloned |
| Scrapling | Web scraping | Python package | ✅ Installed |
| Violin | Video translation | Python package | ✅ Installed |
| Oransim | ROI prediction | oransim/ | ✅ Installed |
| OpenClaw | Orchestration | Gateway | ✅ Running |

---

## Revenue Targets

| Month | Farms | Accounts | Posts/Day | Revenue |
|-------|-------|----------|-----------|---------|
| 1 | 1 | 50 | 1,000 | $500-2K |
| 2 | 2 | 100 | 3,000 | $2K-5K |
| 3 | 5 | 250 | 8,000 | $5K-15K |
| 6 | 10 | 500 | 20,000 | $15K-50K |
| 12 | 20 | 1,000 | 50,000 | $50K-200K |

---

## Documentation

- **Architecture:** `docs/content-farm-architecture.md`
- **Ecosystem Blueprint:** `docs/deeke-ecosystem-blueprint.md`
- **US vs China Tools:** `docs/us-vs-china-tools.md`
- **Agent Config:** `config/content-farm-agents.yaml`
- **Translation Pipeline:** `config/translation-pipeline.yaml`

---

*MAD Content Farm — Built by OWL 🦉*
