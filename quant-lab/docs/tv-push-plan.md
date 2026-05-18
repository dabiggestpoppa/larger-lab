# TradingView Push Plan — Deep Mean Reversion

> **Date:** 2026-05-18
> **Author:** Quant Lab Manager
> **Target:** Push DMR PineScript to TradingView
> **Status:** Ready for execution

---

## 1. Current Situation

- **No public TradingView API exists** for programmatically uploading PineScript code (confirmed 2024-2025)
- The TV-MCP server is stdio-based and requires an MCP client (not available in current setup)
- Browser automation is blocked by Monaco editor's lack of exposed API
- **The only reliable method is manual paste** or browser automation (fragile)

---

## 2. Recommended Approach: Manual Paste (Primary)

### Why Manual
- **Reliable** — Works 100% of the time
- **Fast** — Takes ~2 minutes per script
- **Safe** — No risk of breaking ToS or credentials exposure
- **Auditable** — MAD can verify the code matches the source file

### Prerequisites
1. MAD must have a TradingView account (free tier works for private scripts)
2. MAD must be logged into TradingView in their browser
3. The refined PineScript file must be ready at:
   `quant-lab/conversions/pinescript/deep_mean_reversion.pine`

### Step-by-Step Instructions for MAD

#### Step 1: Open TradingView
1. Go to https://www.tradingview.com/
2. Log in to your account
3. Open any EUR/USD chart (or create a new one)

#### Step 2: Open Pine Editor
1. Click the "Pine Editor" tab at the bottom of the screen
2. If there's existing code, select all and delete it
3. Click "Open" → "New blank indicator"

#### Step 3: Paste the Code
1. Open the file `quant-lab/conversions/pinescript/deep_mean_reversion.pine`
2. Select ALL text (Ctrl+A)
3. Copy (Ctrl+C)
4. Go back to TradingView Pine Editor
5. Paste (Ctrl+V)

#### Step 4: Save the Script
1. Click "Save" (or Ctrl+S)
2. Name it: `QL_DMR_v2` (Quant Lab — Deep Mean Reversion v2)
3. Set visibility: **Private** (do not publish publicly)
4. Click "Save"

#### Step 5: Add to Chart
1. Click "Add to Chart" (or the "More" menu → "Add to Chart")
2. The strategy will appear on the chart with backtest results

#### Step 6: Configure Settings
1. Click the gear icon (⚙️) next to the strategy name on the chart
2. Verify these settings:
   - **Initial Capital:** $10,000
   - **Order Size:** 5% of equity
   - **Commission:** $0.35 per order
   - **Slippage:** 2 ticks
3. Click "OK"

#### Step 7: Verify
1. Check the "Strategy Tester" tab at the bottom
2. Verify the following metrics appear:
   - Net Profit: Should be positive
   - Win Rate: Should be > 80% (TradingView's backtest may differ from Python)
   - PF: Should be > 10
   - Max DD: Should be < 15%
3. If metrics look reasonable, the push is successful

---

## 3. Alternative Approach: Browser Automation (Secondary)

If MAD wants to automate this for future pushes, we can use Playwright/Puppeteer.

### Caveats
- **Fragile** — TradingView UI changes can break the automation
- **ToS risk** — May violate TradingView's Terms of Service
- **2FA issues** — If 2FA is enabled, automation becomes complex
- **Maintenance** — Requires updates when TV changes their UI

### Sketch of Automation Script
```python
# Pseudocode — NOT production ready
from playwright.sync_api import sync_playwright

def push_to_tradingview(pine_file_path, script_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Login (credentials from env)
        page.goto("https://www.tradingview.com/")
        page.fill("#username", TV_USERNAME)
        page.fill("#password", TV_PASSWORD)
        page.click("button[type='submit']")
        
        # Open Pine Editor
        page.click(".tab-pine-editor")
        page.click("button.open-button")
        page.click("text=New blank indicator")
        
        # Paste code
        with open(pine_file_path) as f:
            code = f.read()
        page.click(".monaco-editor")
        page.keyboard.press("Control+a")
        page.keyboard.insert_text(code)
        
        # Save
        page.keyboard.press("Control+s")
        page.fill("#script-title", script_name)
        page.click("button.save-button")
        
        browser.close()
```

### Recommendation
**Do NOT automate yet.** Use manual paste for DMR. If we need to push 5+ scripts regularly, revisit automation.

---

## 4. Future Push Queue

Once DMR is successfully pushed, the queue is:

| Priority | Strategy | Status | Depends On |
|----------|----------|--------|------------|
| 1 | Deep_Mean_Reversion | ✅ Ready | — |
| 2 | Composite_Alpha | ⏳ Forward test | 22 months OOS data |
| 3 | Blind_Structural_Chain | ⏳ Fix + retest | 4-6h dev work |
| 4-9 | Other 7 strategies | 🔴 Abandon? | MAD decision |

---

## 5. Verification Checklist

After MAD pushes DMR to TradingView:

- [ ] Script appears in "My Scripts" list
- [ ] Script loads without compilation errors
- [ ] Strategy Tester shows trades
- [ ] Win Rate > 80% (TradingView backtest)
- [ ] Net Profit > 0
- [ ] Key levels (Activation, Deep State, Kill Switch) appear on chart
- [ ] Alerts are configured (optional)

---

## 6. Credentials & Security

- **Do NOT store TradingView credentials in the repo**
- **Do NOT commit .env files with TV passwords**
- Use environment variables or OpenClaw's secret management
- If using browser automation, store credentials in OpenClaw's config only

---

*TV Push Plan — Quant Lab Manager, 2026-05-18*
*Recommended: Manual paste by MAD (~2 minutes)*
*File: quant-lab/conversions/pinescript/deep_mean_reversion.pine*
