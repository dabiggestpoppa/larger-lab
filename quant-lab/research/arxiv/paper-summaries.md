# ArXiv Research — Forex Trading Strategy Papers
> Compiled: 2026-05-17 by OWL (OC2) for Algo Agent

## Paper 1: AI-Powered Energy Algorithmic Trading (2407.19858)
- **Title**: Integrating Hidden Markov Models with Neural Networks
- **Authors**: Tiago Monteiro
- **Published**: July 2024 (updated Nov 2025)
- **Platform**: QuantConnect
- **Key Results**: 83% return, Sharpe 0.77 during COVID (2019-2022)
- **Method**:
  - HMM for market state detection
  - Neural network for price prediction within each state
  - Black-Litterman portfolio optimization
  - Log returns for optimal state selection
  - Three-year warm-up period
- **Adaptable to Forex**: Yes — HMM for regime detection + NN for prediction
- **Code**: https://github.com/tiagomonteiro0715/AI-Powered-Energy-Algorithmic-Trading-Integrating-Hidden-Markov-Models-with-Neural-Networks

## Paper 2: Deep RL for Forex (May 2024)
- **Title**: A Deep Reinforcement Learning Approach for Trading Optimization in the Forex Market with Multi-Agent Asynchronous Distribution
- **Authors**: Davoud Sarani, Parviz Rashidi-Khazaee
- **Key Method**: Multi-agent async distribution for forex trading
- **Adaptable to Forex**: Directly applicable

## Paper 3: Event-Driven LSTM (Feb 2021)
- **Title**: Event-Driven LSTM For Forex Price Prediction
- **Authors**: Ling Qi, Matloob Khushi, Josiah Poon
- **Key Method**: LSTM with event-driven features for forex
- **Adaptable to Forex**: Directly applicable

## Paper 4: GA-MSSR (2024)
- **Title**: Genetic Algorithm Maximizing Sharpe and Sterling Ratio Method for RoboTrading
- **Authors**: Zezheng Zhang, Matloob Khushi
- **Key Method**: GA-optimized strategy parameters for max Sharpe + Sterling ratio
- **Adaptable to Forex**: Yes — optimization framework

## Paper 5: News Sentiment for Forex (Mar 2024)
- **Title**: Applying News and Media Sentiment Analysis for Generating Forex Trading Signals
- **Authors**: Oluwafemi F Olaiyapo
- **Key Method**: NLP sentiment → forex trading signals
- **Adaptable to Forex**: Yes — sentiment as alpha source

## Paper 6: Neural Network Multi-Timeframe HFT (2508.02356)
- **Title**: Neural Network-Based Algorithmic Trading Systems: Multi-Timeframe Analysis and High-Frequency Execution in Cryptocurrency Markets
- **Author**: Wěi Zhāng
- **Published**: August 2025
- **Key Method**:
  - Multi-head CNN processing of timeframe-specific market data (minute, hourly, daily OHLCV + technical indicators)
  - Broader market context (S&P 500, Bitcoin dominance)
  - Specialized linear processing of orderbook statistics, sentiment data, on-chain metrics
  - Self-attention mechanism dynamically weights all feature inputs
  - Final classification into directional trading signals
  - Trend Networks: Bitcoin dominance + network transaction volumes + multi-timeframe MAs → trend score (-1 to +1)
  - Direction Networks: Multi-head CNN → high-frequency direction prediction
- **Key Results**: Profit factor exceeding traditional approaches, consistent across market conditions
- **Adaptable to Forex**: Yes — multi-timeframe CNN + attention mechanism directly applicable
- **Key Innovation**: Self-attention weighting of diverse data sources (market + on-chain + sentiment + orderbook)

## Synthesis: Best Approaches for EUR/USD
1. **HMM + LSTM + Black-Litterman** (Paper 1) — Most complete framework
2. **Multi-Timeframe CNN + Attention** (Paper 6) — Best for multi-source data fusion
3. **Multi-Agent RL** (Paper 2) — Best for async, multi-timeframe
4. **GA-Optimized Parameters** (Paper 4) — Best for strategy optimization
5. **Sentiment Alpha** (Paper 5) — Good additional signal layer
