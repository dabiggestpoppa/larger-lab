# 📊 PHASE 2 — FROZEN SIGMA VS LIVE SIGMA

## Research Overview

This phase investigates the fundamental hypothesis: **Does frozen sigma better measure consumption of the volatility budget than live sigma?**

We compare two distinct state fields:

### Live Field ($M_{live}$)
$$M_{live}(t) = \frac{\ln(P_t / A_t)}{\sigma_{live}(t) \cdot \sqrt{\tau}}$$

### Frozen Field ($M_{frozen}$)
At activation time $t_0$:
$$\sigma^* = \sigma(t_0)$$

Then:
$$M_{frozen}(t) = \frac{\ln(P_t / A_t)}{\sigma^* \cdot \sqrt{\tau}}$$

## Research Questions

1. **Volatility Field Comparison**: Does frozen sigma provide better signal quality than live sigma?
2. **Volatility Expansion Effects**: How do volatility expansion ratios affect state persistence?
3. **Regime Classification**: Can we identify meaningful volatility regimes?
4. **Threshold Optimization**: What are optimal volatility expansion thresholds?

## Methodology

### 2.1 Data Preparation

#### Primary Assets
- **EURUSD**: 2023-2026 (primary test asset)
- **GBPUSD**: 2023-2026 (secondary validation)
- **USDJPY**: 2023-2026 (third validation)

#### Timeframes
- **H1**: 1-hour data (primary for detailed analysis)
- **D1**: Daily data (regime analysis)

#### Anchor Selection
Using Monday Weekly Open ($A_1$) as primary anchor:
- Monday 07:00-15:00 UTC (03:00-11:00 EST)
- Forward-filled through Friday

### 2.2 Volatility Estimators

We test seven volatility estimators:

#### 2.2.1 Close-to-Close Rolling Standard Deviation ($V_1$)
$$\sigma_{t}^{(1)} = \sqrt{\frac{1}{n-1} \sum_{i=0}^{n-1} (r_{t-i} - \bar{r})^2}$$

#### 2.2.2 EWMA Volatility ($V_2$)
$$\sigma_{t}^{(2)} = \sqrt{\lambda \cdot \sigma_{t-1}^2 + (1-\lambda) \cdot r_{t-1}^2}$$

#### 2.2.3 Parkinson Range Volatility ($V_3$)
$$\sigma_{t}^{(3)} = \sqrt{\frac{1}{4n} \sum_{i=1}^{n} \left[\ln\left(\frac{H_i}{L_i}\right)\right]^2}$$

#### 2.2.4 Garman-Klass Volatility ($V_4$)
$$\sigma_{t}^{(4)} = \sqrt{0.5 \cdot \sigma_{close}^2 - (2\ln2 - 1) \cdot \sigma_{range}^2}$$

#### 2.2.5 ATR-Normalized Realized Volatility ($V_5$)
$$\sigma_{t}^{(5)} = \frac{ATR_t}{\sqrt{\tau}}$$

#### 2.2.6 Robust MAD-Based Volatility ($V_6$)
$$\sigma_{t}^{(6)} = 1.4826 \cdot \text{MAD}(r_t, n)$$

#### 2.2.7 GARCH(1,1) Volatility ($V_7$)
$$\sigma_t^2 = \omega + \alpha \cdot r_{t-1}^2 + \beta \cdot \sigma_{t-1}^2$$

### 2.3 Volatility Expansion Ratio

#### 2.3.1 Core Formula
$$C_t = \frac{\sigma_{live}(t)}{\sigma_{frozen}}$$

#### 2.3.2 State Classification
Based on $C_t$:
- **Contraction**: $C_t < 0.80$
- **Normal**: $0.80 \leq C_t \leq 1.20$
- **Expansion**: $C_t > 1.20$

#### 2.3.3 Sensitivity Grids
We test multiple threshold combinations:
- **Expansion thresholds**: 0.70, 0.80, 0.90, 1.10, 1.20, 1.30, 1.50
- **Contraction thresholds**: 0.70, 0.80, 0.90

### 2.4 Sigma State Definition

#### 2.4.1 State Width Parameter
$$n \in \{0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0\}$$

#### 2.4.2 Directional State
$$S_t = \text{sign}(M_t) \cdot \left\lfloor \frac{|M_t|}{\text{step}} \right\rfloor$$

## Analysis Framework

### 3.1 Performance Metrics

#### 3.1.1 Signal Quality Metrics
- **Hit Rate**: Percentage of correct directional predictions
- **Average Directional Accuracy**: Mean of correct predictions
- **Mean Absolute Error**: Average magnitude of prediction errors

#### 3.1.2 Volatility Metrics
- **Volatility Persistence**: Autocorrelation of volatility estimates
- **Regime Duration**: Average length of volatility regimes
- **Transition Frequency**: Number of volatility regime changes

#### 3.1.3 State Metrics
- **State Persistence**: Probability of remaining in same state
- **State Transition Probability**: $P(S_{t+1}=j | S_t=i)$
- **Mean Time in State**: Average duration in each state

### 3.2 Statistical Tests

#### 3.2.1 Hypothesis Testing
- **Null Hypothesis ($H_0$)**: Frozen sigma does not provide better signal quality than live sigma
- **Alternative Hypothesis ($H_1$)**: Frozen sigma provides better signal quality than live sigma

#### 3.2.2 Significance Testing
- **t-tests**: For comparing means between frozen and live fields
- **Wilcoxon signed-rank tests**: Non-parametric alternative
- **Bootstrap confidence intervals**: For effect size estimation

### 3.3 Comparative Analysis

#### 3.3.1 Live vs Frozen Comparison
For each volatility estimator:
1. Calculate $M_{live}$ and $M_{frozen}$
2. Compare signal quality metrics
3. Analyze state persistence differences
4. Test statistical significance

#### 3.3.2 Volatility Estimator Comparison
Compare all seven volatility estimators:
1. **Stability**: Variance of volatility estimates over time
2. **Responsiveness**: Speed of volatility adaptation to new information
3. **Realized Coverage**: How well volatility predicts future realized volatility
4. **Outlier Sensitivity**: Robustness to extreme market conditions
5. **State Persistence**: Effect on sigma state persistence

## Implementation Plan

### 4.1 Core Functions

#### 4.1.1 Volatility Estimator Functions
```python
def calculate_volatility_estimators(prices, window=20):
    """Calculate all seven volatility estimators"""
    # Close-to-close rolling standard deviation
    # EWMA volatility
    # Parkinson range volatility
    # Garman-Klass volatility
    # ATR-normalized realized volatility
    # MAD-based robust volatility
    # GARCH(1,1) volatility
    pass

def calculate_sigma_fields(prices, anchors, volatility_estimators):
    """Calculate both live and frozen sigma fields"""
    # Calculate activation points
    # Calculate sigma* at activation
    # Calculate M_live and M_frozen
    pass
```

#### 4.1.2 State Classification Functions
```python
def classify_volatility_regime(expansion_ratio):
    """Classify volatility regime based on expansion ratio"""
    if expansion_ratio < 0.80:
        return "CONTRACTION"
    elif expansion_ratio <= 1.20:
        return "NORMAL"
    else:
        return "EXPANSION"

def classify_sigma_state(sigma_coordinate, step):
    """Classify sigma state based on coordinate and step size"""
    if abs(sigma_coordinate) < step:
        return 0
    else:
        return int(abs(sigma_coordinate) // step)
```

### 4.2 Analysis Functions

#### 4.2.1 Signal Quality Analysis
```python
def compare_signal_quality(m_live, m_frozen):
    """Compare signal quality between live and frozen fields"""
    # Calculate hit rates
    # Calculate directional accuracy
    # Perform statistical tests
    pass

def analyze_volatility_regimes(expansion_ratios):
    """Analyze volatility regime characteristics"""
    # Calculate regime durations
    # Analyze transition frequencies
    # Test regime persistence
    pass
```

#### 4.2.2 State Transition Analysis
```python
def calculate_transition_matrix(states):
    """Calculate state transition probability matrix"""
    # Count transitions
    # Calculate probabilities
    # Normalize matrix
    pass

def analyze_state_persistence(states):
    """Analyze state persistence characteristics"""
    # Calculate mean time in state
    # Analyze persistence patterns
    # Test statistical significance
    pass
```

### 4.3 Visualization Functions

#### 4.3.1 Core Visualizations
```python
def plot_volatility_comparison(m_live, m_frozen, title):
    """Plot comparison of live vs frozen sigma fields"""
    # Create time series plot
    # Add confidence bands
    # Highlight regime changes
    pass

def plot_volatility_regimes(expansion_ratios, regimes):
    """Plot volatility regime classification"""
    # Create regime timeline
    # Highlight expansion/contraction/normal periods
    # Show duration statistics
    pass

def plot_state_transitions(transition_matrix):
    """Plot state transition matrix"""
    # Create heatmap
    # Show transition probabilities
    # Highlight persistent states
    pass
```

## Expected Results

### 5.1 Primary Hypotheses

#### 5.1.1 Hypothesis 1: Frozen Sigma Superiority
**Prediction**: Frozen sigma fields will show:
- Higher hit rates
- Better directional accuracy
- Lower mean absolute error
- More stable state persistence

#### 5.1.2 Hypothesis 2: Optimal Expansion Thresholds
**Prediction**: Expansion thresholds around 1.20 will optimize:
- Signal quality
- State persistence
- Trend continuation probability

#### 5.1.3 Hypothesis 3: Volatility Regime Effects
**Prediction**: HIGH displacement + HIGH volatility expansion will:
- Increase continuation probability
- Enhance trend capture
- Improve signal quality

### 5.2 Statistical Significance

We expect:
- **p-values < 0.05** for key comparisons
- **Effect sizes > 0.5** for meaningful differences
- **Confidence intervals** that do not overlap zero

### 5.3 Economic Significance

We expect:
- **Economic value** after transaction costs
- **Risk-adjusted returns** that beat baselines
- **Robust performance** across assets and timeframes

## Implementation Timeline

### 6.1 Phase 2 Completion
**Target**: 2-3 weeks

#### 6.1.1 Week 1: Core Implementation
- Implement volatility estimators
- Calculate live and frozen sigma fields
- Set up basic analysis framework

#### 6.1.2 Week 2: Analysis and Testing
- Implement signal quality comparisons
- Analyze volatility regimes
- Conduct statistical tests

#### 6.1.3 Week 3: Validation and Refinement
- Validate results across assets
- Refine threshold parameters
- Prepare Phase 3 materials

### 6.2 Deliverables

#### 6.2.1 Research Outputs
1. **VOLATILITY_COMPARISON.md** - This document (✅ Complete)
2. **volatility.py** - Volatility estimator implementations
3. **morphic_coordinates.py** - Sigma field calculations
4. **regime.py** - Volatility regime analysis
5. **results/volatility_comparison/** - Analysis results

#### 6.2.2 Code Deliverables
1. **src/mve/volatility.py** - Core volatility functions
2. **src/mve/morphic_coordinates.py** - Sigma field calculations
3. **src/mve/regime.py** - Volatility regime analysis
4. **tests/mve/test_volatility.py** - Volatility tests
5. **tests/mve/test_regime.py** - Regime tests

## Quality Assurance

### 7.1 Testing Strategy

#### 7.1.1 Unit Tests
- Test each volatility estimator against known values
- Validate sigma field calculations
- Test regime classification logic

#### 7.1.2 Integration Tests
- Test end-to-end pipeline
- Validate cross-asset consistency
- Test performance with large datasets

#### 7.1.3 Statistical Validation
- Validate bootstrap confidence intervals
- Test statistical power
- Validate effect size calculations

### 7.2 Code Quality

#### 7.2.1 Documentation
- Document all functions and parameters
- Provide usage examples
- Include mathematical derivations

#### 7.2.2 Code Style
- Follow PEP 8 guidelines
- Use descriptive variable names
- Implement comprehensive error handling

#### 7.2.3 Performance
- Optimize for large datasets
- Implement efficient algorithms
- Use vectorized operations where possible

## Risk Management

### 8.1 Technical Risks

#### 8.1.1 Data Quality Risks
- **Risk**: Missing or corrupted data
- **Mitigation**: Implement robust data validation
- **Backup**: Use multiple data sources

#### 8.1.2 Computational Risks
- **Risk**: Memory or performance issues
- **Mitigation**: Implement efficient algorithms
- **Backup**: Use incremental processing

### 8.2 Research Risks

#### 8.2.1 Hypothesis Risks
- **Risk**: Hypotheses not supported by data
- **Mitigation**: Implement fail-closed approach
- **Backup**: Document negative results

#### 8.2.2 Interpretation Risks
- **Risk**: Misinterpretation of results
- **Mitigation**: Implement peer review
- **Backup**: Use multiple validation methods

## Conclusion

Phase 2 establishes the foundation for understanding whether **frozen sigma provides superior signal quality compared to live sigma**. This research is critical because:

1. **Volatility Budget**: Frozen sigma better measures consumption of the volatility budget
2. **Signal Stability**: Frozen sigma provides more stable signals
3. **Trend Continuation**: Frozen sigma may better predict trend continuation
4. **Risk Management**: Frozen sigma may reduce false signals

The results will inform:
- **Phase 3**: Sigma state occupation study
- **Phase 4**: Acceptance/persistence model
- **Phase 5**: Volatility × displacement regime map
- **Phase 8**: Early strategy tests

The mathematical framework is now established for proceeding to Phase 3 (Sigma State Occupation Study) and subsequent phases. The research will continue until clear evidence emerges or all stop conditions are met.