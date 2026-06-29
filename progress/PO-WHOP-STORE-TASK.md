# PO TASK — MAD LABS Whop Store Build Verification

> **Assigned by:** CC (Claude Code)
> **Date:** 2026-06-26
> **For:** PM2 (Polymorph 2) — PO Field Tester
> **Status:** READY TO EXECUTE

---

## Context

CC received a mission to build a Whop storefront for MAD LABS. Before CC executes the full build, PO must verify the current workspace state and prepare the infrastructure.

## Your Task

### Phase 1: Workspace Audit (5 min)
Run these commands and report findings:

```powershell
# Check if whop-related files exist
Get-ChildItem -Path "." -Recurse -Filter "*whop*" -ErrorAction SilentlyContinue | Select-Object FullName

# Check if there's a whop store config
Get-ChildItem -Path "." -Recurse -Filter "*.whop*" -ErrorAction SilentlyContinue | Select-Object FullName

# Check existing store/frontend structure
Get-ChildItem -Path "oce/frontend" -Filter "*.tsx" -ErrorAction SilentlyContinue | Select-Object Name

# Check for any existing MAD LABS branding files
Get-ChildItem -Path "." -Recurse -Filter "*mad*" -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Path "." -Recurse -Filter "*labs*" -ErrorAction SilentlyContinue | Select-Object FullName
```

### Phase 2: Whop API Research (10 min)
Use the OCE backend to research Whop:

```powershell
# Test if Whop MCP tools are available
python -c "
import urllib.request, json
r = urllib.request.urlopen('http://127.0.0.1:8000/api/po/mcp/tools', timeout=5)
tools = json.loads(r.read().decode())
whop_tools = [t for t in tools.get('tools', []) if 'whop' in str(t).lower()]
print(f'Whop tools found: {len(whop_tools)}')
for t in whop_tools:
    print(f'  {t}')
if not whop_tools:
    print('No Whop MCP tools registered')
    print(f'Available tools: {len(tools.get(\"tools\", []))}')
    for t in tools.get('tools', [])[:10]:
        print(f'  {t.get(\"name\", \"?\")} — {t.get(\"description\", \"?\")[:60]}')
"
```

### Phase 3: Store Structure Design (15 min)
Create the Whop store directory structure:

```powershell
# Create store directories
New-Item -ItemType Directory -Force -Path "whop-store"
New-Item -ItemType Directory -Force -Path "whop-store/products"
New-Item -ItemType Directory -Force -Path "whop-store/products/consultations"
New-Item -ItemType Directory -Force -Path "whop-store/products/digital"
New-Item -ItemType Directory -Force -Path "whop-store/products/bootcamps"
New-Item -ItemType Directory -Force -Path "whop-store/products/software"
New-Item -ItemType Directory -Force -Path "whop-store/community"
New-Item -ItemType Directory -Force -Path "whop-store/branding"
New-Item -ItemType Directory -Force -Path "whop-store/payments"
New-Item -ItemType Directory -Force -Path "whop-store/integrations"
```

### Phase 4: Product Configuration Files (20 min)
Create JSON config files for each product:

**File: `whop-store/products/consultations.json`**
```json
{
  "consultations": [
    {
      "id": "trading-consultation",
      "name": "Private Trading Consultation",
      "type": "service",
      "price": 100,
      "currency": "USD",
      "description": "One-on-one strategy consulting focused on market structure, execution systems, and trading performance optimization.",
      "status": "active",
      "booking_url": "https://calendly.com/madlabs/trading",
      "delivery": "external_calendly"
    },
    {
      "id": "ai-consultation",
      "name": "AI Systems Consultation",
      "type": "service",
      "price": 150,
      "currency": "USD",
      "description": "Private consulting focused on AI systems, workflow automation, infrastructure design, and technical implementation strategy.",
      "status": "active",
      "booking_url": "https://calendly.com/madlabs/ai-systems",
      "delivery": "external_calendly"
    },
    {
      "id": "investment-consultation",
      "name": "Investment Strategy Consultation",
      "type": "service",
      "price": 200,
      "currency": "USD",
      "description": "Consultation focused on financial systems design, capital deployment, strategic allocation, and long-term investment architecture.",
      "status": "active",
      "booking_url": "https://calendly.com/madlabs/investment",
      "delivery": "external_calendly"
    }
  ]
}
```

**File: `whop-store/products/digital.json`**
```json
{
  "digital_products": [
    {
      "id": "beginner-framework",
      "name": "The Beginner Trading Framework",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Foundational framework for systematic trading approach.",
      "status": "coming_soon",
      "delivery": "whop_digital"
    },
    {
      "id": "risk-playbook",
      "name": "Risk Management Playbook",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Comprehensive risk management framework and guidelines.",
      "status": "coming_soon",
      "delivery": "whop_digital"
    },
    {
      "id": "ai-blueprint",
      "name": "AI Automation Blueprint",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Complete guide to AI workflow automation systems.",
      "status": "coming_soon",
      "delivery": "whop_digital"
    },
    {
      "id": "systems-guide",
      "name": "Trading Systems Architecture Guide",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Technical guide to building institutional-grade trading systems.",
      "status": "coming_soon",
      "delivery": "whop_digital"
    },
    {
      "id": "market-structure",
      "name": "Market Structure Engineering Framework",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Advanced market structure analysis and engineering methodology.",
      "status": "coming_soon",
      "delivery": "whop_digital"
    }
  ]
}
```

**File: `whop-store/products/bootcamps.json`**
```json
{
  "bootcamps": [
    {
      "id": "algo-trading-bootcamp",
      "name": "Algorithmic Trading Bootcamp",
      "type": "service",
      "price": 0,
      "currency": "USD",
      "description": "Structured implementation program teaching system development, strategy engineering, backtesting, and automation design.",
      "status": "coming_soon",
      "delivery": "whop_community"
    },
    {
      "id": "ai-systems-bootcamp",
      "name": "AI Systems Build Bootcamp",
      "type": "service",
      "price": 0,
      "currency": "USD",
      "description": "Structured implementation service focused on AI workflows, agents, automation systems, and technical infrastructure.",
      "status": "coming_soon",
      "delivery": "whop_community"
    }
  ]
}
```

**File: `whop-store/products/software.json`**
```json
{
  "software": [
    {
      "id": "tv-indicators",
      "name": "TradingView Indicator Suite",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Professional TradingView indicator package for market analysis.",
      "status": "pending",
      "note": "TradingView Essential Plan not yet purchased",
      "delivery": "whop_digital"
    },
    {
      "id": "automation-engine",
      "name": "Trading Automation Engine",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Automated trading execution engine for systematic strategies.",
      "status": "in_development",
      "delivery": "whop_digital"
    },
    {
      "id": "backtesting-dashboard",
      "name": "Backtesting Dashboard",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Professional backtesting infrastructure for strategy validation.",
      "status": "in_development",
      "delivery": "whop_digital"
    },
    {
      "id": "strategy-scanner",
      "name": "Strategy Scanner Engine",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Real-time market scanning and opportunity detection system.",
      "status": "in_development",
      "delivery": "whop_digital"
    },
    {
      "id": "prop-optimizer",
      "name": "Prop Firm Optimization Engine",
      "type": "digital_download",
      "price": 0,
      "currency": "USD",
      "description": "Optimization system for prop firm challenge completion.",
      "status": "in_development",
      "delivery": "whop_digital"
    }
  ]
}
```

### Phase 5: Community Configuration (10 min)

**File: `whop-store/community/tiers.json`**
```json
{
  "tiers": [
    {
      "id": "free",
      "name": "Public Discord Community",
      "type": "free",
      "price": 0,
      "billing": "one_time",
      "features": [
        "Announcements channel",
        "Public discussions",
        "General networking"
      ],
      "status": "active",
      "discord_role": "community"
    },
    {
      "id": "premium",
      "name": "Research Community",
      "type": "subscription",
      "price": 0,
      "billing": "monthly",
      "features": [
        "Private research channels",
        "Research releases",
        "Premium discussions",
        "Advanced market breakdowns"
      ],
      "status": "coming_soon",
      "discord_role": "research"
    },
    {
      "id": "vip",
      "name": "Operator Circle",
      "type": "subscription",
      "price": 0,
      "billing": "monthly",
      "features": [
        "Founder access",
        "Private discussions",
        "Early access products",
        "Technical development discussions"
      ],
      "status": "coming_soon",
      "discord_role": "operator"
    }
  ]
}
```

### Phase 6: Brand Configuration (10 min)

**File: `whop-store/branding/config.json`**
```json
{
  "brand": {
    "name": "MAD LABS",
    "tagline": "Applied Intelligence for High Performance Operators.",
    "category": "Technology + AI + Trading + Financial Intelligence + Automation",
    "aesthetic": {
      "background": "#000000",
      "primary_color": "#ffffff",
      "accent_color": "#c96442",
      "style": "premium_minimalist",
      "feel": "futuristic_technology"
    },
    "keywords": [
      "Precision",
      "Intelligence",
      "Research",
      "Automation",
      "High Performance",
      "Engineering",
      "Systems"
    ],
    "avoid": [
      "forex education branding",
      "retail trading influencer",
      "trading signal services",
      "beginner mentorship language"
    ],
    "resemble": [
      "research lab",
      "financial technology company",
      "AI systems company",
      "institutional intelligence brand",
      "premium consulting ecosystem"
    ]
  },
  "external_links": {
    "calendly": "https://calendly.com/madlabs",
    "discord": "https://discord.gg/madlabs",
    "linktree": "https://linktr.ee/madlabs"
  }
}
```

### Phase 7: Payment Configuration (5 min)

**File: `whop-store/payments/config.json`**
```json
{
  "payment": {
    "primary": "whop_payments",
    "secondary": "stripe",
    "fallback": "paypal",
    "supported_types": [
      "one_time_purchase",
      "subscription_billing",
      "recurring_memberships",
      "future_digital_products"
    ],
    "currency": "USD"
  }
}
```

### Phase 8: Integration Config (5 min)

**File: `whop-store/integrations/config.json`**
```json
{
  "integrations": {
    "calendly": {
      "status": "active",
      "purpose": "booking_system",
      "url": "https://calendly.com/madlabs"
    },
    "discord": {
      "status": "active",
      "purpose": "community_infrastructure",
      "url": "https://discord.gg/madlabs"
    },
    "linktree": {
      "status": "active",
      "purpose": "traffic_hub",
      "url": "https://linktr.ee/madlabs"
    }
  }
}
```

### Phase 9: Master Store Config (5 min)

**File: `whop-store/store.json`**
```json
{
  "store": {
    "name": "MAD LABS",
    "url": "madlabs.whop.com",
    "status": "pre_launch",
    "created": "2026-06-26",
    "version": "1.0.0"
  },
  "sections": [
    "hero_banner",
    "company_overview",
    "services",
    "community_access",
    "research_products",
    "software_tools",
    "book_consultation"
  ],
  "active_offerings": [
    "private_trading_consultation",
    "ai_systems_consultation",
    "investment_strategy_consultation"
  ],
  "future_offerings": [
    "ebooks",
    "bootcamps",
    "tradingview_indicators",
    "discord_memberships",
    "ai_products",
    "trading_software",
    "research_subscriptions"
  ]
}
```

### Phase 10: Verification Test (5 min)
After creating all files, run this verification:

```powershell
# Verify all files created
$files = @(
    "whop-store/products/consultations.json",
    "whop-store/products/digital.json",
    "whop-store/products/bootcamps.json",
    "whop-store/products/software.json",
    "whop-store/community/tiers.json",
    "whop-store/branding/config.json",
    "whop-store/payments/config.json",
    "whop-store/integrations/config.json",
    "whop-store/store.json"
)

foreach ($f in $files) {
    if (Test-Path $f) {
        $size = (Get-Item $f).Length
        Write-Host "OK $f ($size bytes)"
    } else {
        Write-Host "MISSING $f"
    }
}

# Validate JSON
foreach ($f in $files) {
    try {
        $null = Get-Content $f -Raw | ConvertFrom-Json
        Write-Host "VALID JSON: $f"
    } catch {
        Write-Host "INVALID JSON: $f — $_"
    }
}
```

---

## Deliverables

1. All 9 config files created in `whop-store/`
2. All JSON validates correctly
3. Results written to `O2C-VAULT/journal_20260626T141000Z_po_whop_store_build.md`
4. `progress/PM2-progress.md` updated with completion status

## Success Criteria
- 9/9 files created ✅
- 9/9 JSON valid ✅
- All products configured ✅
- All integrations linked ✅
- Vault updated ✅
