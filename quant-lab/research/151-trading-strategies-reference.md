# 151 Trading Strategies — Key Strategies for CEREBUS Enhancement
> Source: Kakushadze & Serur (2018) "151 Trading Strategies" + GitHub implementation
> Compiled: 2026-05-17 by OWL (OC2) for Quant Lab
> https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3247865
> https://github.com/ThewindMom/151-trading-strategies

## FX-Relevant Strategies (Direct Application)

### Section 8: FX Strategies
- **8.1 FX Moving Averages** — Single/dual/triple MA crossovers on forex pairs
- **8.2 FX Carry Trade** — Go long high-yield currencies, short low-yield currencies
- **8.5 FX Triangular Arbitrage** — Exploit cross-rate inconsistencies (e.g., EUR/USD vs EUR/GBP × GBP/USD)

## Equity/Index Strategies Adaptable to Forex

### Section 3: Stock Strategies
- **3.1 Price Momentum** — Buy past winners, sell past losers (works on forex too)
- **3.6 Multifactor Portfolio** — Combine momentum, value, low-vol (adapt to forex factors)
- **3.7 Residual Momentum** — Momentum not explained by Fama-French factors
- **3.8 Pairs Trading** — Cointegration-based pairs (works on correlated forex pairs)
- **3.9 Mean-Reversion Cluster** — Short-term mean reversion within clusters
- **3.10 Weighted Regression** — Time-series weighted regression for return prediction
- **3.11-3.13 Moving Averages** — Single, dual, triple MA systems
- **3.14 Support and Resistance** — Key level identification (directly applicable to CEREBUS)
- **3.15 Channel** — Trading within price channels (related to Asian Range)
- **3.17 Machine Learning (KNN)** — K-nearest neighbor for pattern recognition
- **3.18 Statistical Arbitrage** — Multi-asset stat arb (adapt to FX basket)
- **3.19 Market-Making** — Quote bid/ask around fair value
- **3.20 Alpha Combos** — Combine multiple alpha signals (directly aligns with RohOnChain framework)

### Section 4: ETF Strategies
- **4.1 Sector Momentum** — Sector rotation (adapt to currency rotation)
- **4.6 Multi-Asset Trend** — Trend following across asset classes

### Section 18: Crypto Strategies
- **18.2 ANN (Neural Network)** — Neural network-based prediction
- **18.3 Sentiment Analysis** — NLP-based sentiment signals

## Strategies Most Relevant to CEREBUS Manual

| CEREBUS Strategy | Matching 151 Strategy | Enhancement Opportunity |
|-----------------|----------------------|------------------------|
| CFD Expansion (P90) | 3.14 Support/Resistance + 3.15 Channel | Add weighted regression for level strength |
| Deep Mean Reversion | 3.9 Mean-Reversion Cluster + 3.8 Pairs | Cluster-based entry confirmation |
| Dual-Engine | 3.20 Alpha Combos | Already similar — optimize weighting |
| Stall-Harvest (168%) | 3.14 Support/Resistance | Add KNN pattern matching for stall zones |
| Failure Repair | 3.10 Weighted Regression | Time-weighted failure probability |
| Two Plays | 3.1 Price Momentum + 3.6 Multifactor | Add momentum confirmation layer |
| Constraint Anchor | 3.11-3.13 Moving Averages | Multi-timeframe MA confirmation |
| Regime Filter | 4.6 Multi-Asset Trend | Cross-asset regime detection |

## Implementation Notes
- GitHub repo has 68 strategies implemented in FastAPI: `github.com/ThewindMom/151-trading-strategies`
- Each strategy has a `/strategy-name` endpoint with JSON input/output
- Can use these as reference implementations for Nautilus adaptation
- Key Forex-specific strategies: 8.1 (MA), 8.2 (Carry), 8.5 (Triangular Arb)
- Most adaptable: 3.20 (Alpha Combos), 3.14 (S/R), 3.18 (Stat Arb), 3.6 (Multifactor)
