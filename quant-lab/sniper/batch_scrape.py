"""
Batch scrape all firm challenge pages and compile real pricing.
Uses browser to navigate and extract pricing from each firm's /challenges page.
Run this script to build the complete real_pricing.json file.
"""
import json
from datetime import datetime
from pathlib import Path

SNAPSHOT_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\sniper\snapshots")

# All firm slugs to scrape
FIRM_SLUGS = {
    # Futures
    "apex-trader-funding": "Apex Trader Funding",
    "my-funded-futures": "My Funded Futures",
    "topstep": "Topstep",
    "fundednext-futures": "FundedNext Futures",
    "lucid-trading": "Lucid Trading",
    "alpha-futures": "Alpha Futures",
    "tradeify": "Tradeify",
    "top-one-futures": "Top One Futures",
    "funded-futures-family": "Funded Futures Family",
    "e8-futures": "E8 Futures",
    "goat-funded-futures": "Goat Funded Futures",
    "traders-launch": "Traders Launch",
    "take-profit-trader": "Take Profit Trader",
    "tradeday": "TradeDay",
    "futureselite": "FuturesElite",
    # Forex
    "blueberry-funded": "Blueberry Funded",
    "for-traders": "For Traders",
    "e8-markets": "E8 Markets",
    "blue-guardian": "Blue Guardian",
    "brightfunded": "BrightFunded",
}

JS_EXTRACT = """
() => {
    const rows = document.querySelectorAll('table tbody tr');
    const data = [];
    for (const row of rows) {
        const cells = row.querySelectorAll('td');
        if (cells.length < 4) continue;
        const size = (cells[1]?.textContent||'').trim();
        const activation = (cells[3]?.textContent||'').trim();
        const priceText = (cells[cells.length-1]?.textContent||'').trim();
        const prices = priceText.split('\n').map(s=>s.trim()).filter(Boolean);
        const promo = prices.find(p=>p.startsWith('$'));
        let promoVal = null, billing = 'unknown';
        if (promo) { promoVal = parseFloat(promo.replace('$','').replace(/,/g,'')); }
        const billWord = prices.find(p=>p.toLowerCase().includes('monthly')||p.toLowerCase().includes('one time'));
        if (billWord) billing = billWord.toLowerCase().includes('monthly') ? 'monthly' : 'one time';
        let actVal = 0;
        if (activation && activation !== 'None') { const m = activation.match(/[\\d.]+/); if (m) actVal = parseFloat(m); }
        const sizeNum = parseInt(size)||0;
        data.push({size, sizeNum, activation: actVal, promo: promoVal, billing, total: promoVal != null ? promoVal + actVal : null});
    }
    return JSON.stringify(data);
}
"""

if __name__ == '__main__':
    # Output the JS and URL list for the browser tool to execute
    print("=== BATCH SCRAPE CONFIG ===")
    for slug, name in FIRM_SLUGS.items():
        print(f"NAVIGATE: https://propfirmmatch.com/futures/prop-firms/{slug}/challenges")
        print(f"EXTRACT: {name}")
    print("\n=== JS TO RUN ON EACH PAGE ===")
    print(JS_EXTRACT)
