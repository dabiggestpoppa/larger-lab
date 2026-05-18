# Strategy: LSTM EUR/USD Directional Prediction

## Sources
- arXiv:2408.13214 — "EUR/USD Exchange Rate Forecasting Based on Information Fusion with LLMs and Deep Learning" (IUS framework)
- arXiv:2411.07560 — "EUR/USD Forecasting with Text Mining + PSO-LSTM" (2024)
- arXiv:2409.04471 — "Predicting EUR/USD Direction Using ML" (58.52% accuracy, 32.48% annual return)

## Core Logic
Use LSTM (Long Short-Term Memory) neural network to predict EUR/USD directional movement. Trade in the predicted direction with confirmation filters.

### Model Architecture (from papers)
- **Input features:** OHLCV + technical indicators (12-15 features)
- **Model:** Bidirectional LSTM with attention mechanism
- **Hyperparameter optimization:** Optuna (automated)
- **Output:** Probability of upward movement (0-1)

### Feature Set
1. Returns (1, 5, 10, 20 bar)
2. EMA 20, 50, 200
3. RSI (14)
4. MACD (12, 26, 9)
5. Bollinger Band %B
6. ATR (14)
7. ADX (14)
8. Stochastic %K, %D
9. Volume (if available)
10. Hour of day (encoded cyclically)
11. Day of week (encoded cyclically)
12. Volatility ratio (ATR 14 / ATR 50)

### Trading Rules
1. **Prediction:** LSTM outputs P(up) for next bar/day
2. **Entry threshold:** P(up) > 0.60 → long, P(up) < 0.40 → short
3. **Confirmation:** Only trade if ADX > 15 (some trend exists)
4. **Stop loss:** 1.5× ATR from entry
5. **Take profit:** 2× risk or next support/resistance
6. **No trade zone:** 0.40 ≤ P(up) ≤ 0.60 (uncertain → stay flat)

### Training Approach
- Walk-forward training (retrain monthly)
- 80% train, 20% validation split (temporal, not random)
- Early stopping on validation loss
- Input normalization (rolling z-score)

## Expected Performance
- Directional accuracy: 55-60% (from papers)
- Annual return: 25-35% (from 2409.04471 paper, 2022 data)
- Sharpe ratio: ~1.0-1.5 (estimated)
- Key risk: model degradation in regime changes → need regular retraining

## Implementation Approach
1. Collect and preprocess EUR/USD data
2. Engineer features (technical indicators + calendar features)
3. Train LSTM with walk-forward validation
4. Generate predictions for next bar
5. Apply trading rules with risk management
6. Retrain model monthly or when accuracy drops below 52%
