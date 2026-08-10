# 📊 PHASE 3 — SIGMA STATE OCCUPATION STUDY

## Research Overview

This phase investigates the core hypothesis: **Do financial markets exhibit statistically persistent directional movement after occupying and accepting volatility-normalized sigma states?**

We analyze sigma state occupation patterns, focusing on:

### 3.1 Key Research Questions

1. **State Occupation Persistence**: What are the forward return distributions after sigma state occupation?
2. **Acceptance Effects**: How do acceptance criteria affect continuation probabilities?
3. **Optimal Occupancy**: What are the optimal occupancy thresholds?
4. **Event Classification**: How do different sigma state events (first touch, first close, etc.) affect forward behavior?

### 3.2 Core Hypotheses

#### 3.2.1 Hypothesis 1: Sigma State Occupation Contains Predictive Information
**Prediction**: Acceptance of sigma states will increase the probability of same-direction continuation relative to unconditional behavior.

#### 3.2.2 Hypothesis 2: Acceptance Thresholds Matter
**Prediction**: Optimal acceptance thresholds (50%, 60%, 66%, 75%, 80%) will show distinct patterns of continuation probability.

#### 3.2.3 Hypothesis 3: Event Type Matters
**Prediction**: Different sigma state events (E1-E8) will have distinct forward return distributions.

#### 3.2.4 Hypothesis 4: Time Horizon Effects
**Prediction**: Forward behavior will vary across different time horizons (1, 3, 6, 12, 24, 48 bars for H1; 1, 2, 3, 6, 12, 24 bars for H4; 1, 2, 3, 5, 10, 20 days for D1).

## Methodology

### 3.3 Data Preparation

#### 3.3.1 Primary Assets
- **EURUSD**: 2023-2026 (primary test asset)
- **GBPUSD**: 2023-2026 (secondary validation)
- **USDJPY**: 2023-2026 (third validation)

#### 3.3.2 Timeframes
- **H1**: 1-hour data (primary for detailed analysis)
- **D1**: Daily data (regime analysis)

#### 3.3.3 Anchor Selection
Using Monday Weekly Open ($A_1$) as primary anchor:
- Monday 07:00-15:00 UTC (03:00-11:00 EST)
- Forward-filled through Friday

### 3.4 Sigma State Definition

#### 3.4.1 State Width Parameter
$$n \in \{0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0\}$$

#### 3.4.2 Directional State
$$S_t = \text{sign}(M_t) \cdot \left\lfloor \frac{|M_t|}{\text{step}} \right\rfloor$$

#### 3.4.3 State Classification
- **State 0**: $|M_t| < \text{step}$ (neutral zone)
- **State 1**: $\text{step} \leq |M_t| < 2 \cdot \text{step}$ (first sigma)
- **State 2**: $2 \cdot \text{step} \leq |M_t| < 3 \cdot \text{step}$ (second sigma)
- **And so on...**

### 3.5 Event Definitions

#### 3.5.1 Sigma State Events

##### 3.5.1.1 First Touch ($E_1$)
First crossing of $+n$ sigma boundary:
$$E_1(t) = \text{true if } M_t > n \cdot \text{step} \text{ and } M_{t-1} \leq n \cdot \text{step}$$

##### 3.5.1.2 First Close ($E_2$)
First close beyond $+n$ sigma:
$$E_2(t) = \text{true if } M_t > n \cdot \text{step} \text{ and } M_{t-1} > n \cdot \text{step}$$

##### 3.5.1.3 Consecutive Closes ($E_3, E_4$)
- $E_3$: 2 consecutive closes beyond $+n$ sigma
- $E_4$: 3 consecutive closes beyond $+n$ sigma

##### 3.5.1.4 Occupancy ($E_5$)
$X\%$ occupancy beyond boundary over next $N$ bars:
$$E_5(t) = \text{true if } \frac{\sum_{i=0}^{N-1} \mathbb{1}(M_{t+i} > n \cdot \text{step})}{N} \geq X\%$$

##### 3.5.1.5 Breakout-Retest ($E_6$)
Breakout followed by retest of the boundary.

##### 3.5.1.6 Failure ($E_7$)
Breakout followed by failure to sustain.

##### 3.5.1.7 State Advancement ($E_8$)
Consecutive sigma-state advancement.

#### 3.5.2 Symmetric Events
All events are defined symmetrically for negative states (below -n sigma).

### 3.6 Forward Horizon Definitions

#### 3.6.1 H1 (5-minute data)
- **1 bar**: 5 minutes
- **3 bars**: 15 minutes
- **6 bars**: 30 minutes
- **12 bars**: 1 hour
- **24 bars**: 2 hours
- **48 bars**: 4 hours

#### 3.6.2 H4 (1-hour data)
- **1 bar**: 1 hour
- **2 bars**: 2 hours
- **3 bars**: 3 hours
- **6 bars**: 6 hours
- **12 bars**: 12 hours
- **24 bars**: 1 day

#### 3.6.3 Daily (Daily data)
- **1 bar**: 1 day
- **2 bars**: 2 days
- **3 bars**: 3 days
- **5 bars**: 5 days
- **10 bars**: 10 days
- **20 bars**: 20 days

### 3.7 Occupancy Definition

#### 3.7.1 Core Formula
$$Occ(n, N) = \frac{\text{number of closes beyond } n \sigma}{N}$$

#### 3.7.2 Test Values
$$N \in \{3, 5, 8, 12\} \text{ bars}$$

#### 3.7.3 Acceptance Thresholds
$$A_{grid} = \{50\%, 60\%, 66\%, 75\%, 80\%\}$$

## Analysis Framework

### 3.8 Performance Metrics

#### 3.8.1 Event-Based Metrics
- **Event Count**: Number of each event type
- **Event Frequency**: Events per unit time
- **Event Duration**: Time between event start and end

#### 3.8.2 Forward Return Metrics
- **Conditional Expected Return**: $E[R_{t+1} | E_i]$
- **Conditional Median Return**: $Med[R_{t+1} | E_i]$
- **Return Skew**: $Skew[R_{t+1} | E_i]$
- **Tail Quantiles**: $Q_{0.01}[R_{t+1} | E_i]$, $Q_{0.05}[R_{t+1} | E_i]$

#### 3.8.3 State Transition Metrics
- **Next State Probability**: $P(S_{t+1}=j | S_t=i, E_i)$
- **Continuation Probability**: $P(S_{t+1}=S_t | E_i)$
- **Reversal Probability**: $P(S_{t+1}=-S_t | E_i)$

#### 3.8.4 Time Metrics
- **Time-to-Next-State**: $TNS = t_{next} - t_{current}$
- **Time-to-Failure**: $TTF = t_{failure} - t_{entry}$
- **Median Time-to-Next-State**: $Med[TNS | E_i]$
- **Median Time-to-Failure**: $Med[TTF | E_i]$

#### 3.8.5 Risk Metrics
- **Hazard of Failure**: $H(t) = \frac{f(t)}{1 - F(t)}$
- **Excursion Distribution**: Distribution of return magnitudes during events
- **Occupancy Duration**: Average time spent in sigma state

### 3.9 Statistical Analysis

#### 3.9.1 Bootstrap Confidence Intervals
For any statistic $\theta$:
1. Draw $B$ bootstrap samples (with replacement)
2. Calculate $\hat{\theta}^*_b$ for each sample
3. Use percentile method: $[\hat{\theta}_{(\alpha/2)}, \hat{\theta}_{(1-\alpha/2)}]$

#### 3.9.2 Hypothesis Testing
- **Null Hypothesis ($H_0$)**: Conditional return distribution equals unconditional distribution
- **Alternative Hypothesis ($H_1$)**: Conditional return distribution differs from unconditional distribution

#### 3.9.3 Effect Size Calculation
$$ES = \frac{\hat{\theta}_{cond} - \hat{\theta}_{uncond}}{\sigma_{uncond}}$$

## Implementation Plan

### 3.10 Core Functions

#### 3.10.1 Sigma State Functions
```python
def classify_sigma_state(m_t, step):
    """Classify sigma state based on coordinate and step size"""
    if abs(m_t) < step:
        return 0
    else:
        return int(abs(m_t) // step)

def detect_sigma_events(m_t, m_t_minus1, step, n):
    """Detect sigma state events"""
    # First touch (E1)
    # First close (E2)
    # Consecutive closes (E3, E4)
    # Occupancy (E5)
    # Breakout-retest (E6)
    # Failure (E7)
    # State advancement (E8)
    pass

def calculate_occupancy(m_t, step, n, n_bars):
    """Calculate occupancy beyond sigma state"""
    # Count closes beyond n sigma
    # Calculate occupancy ratio
    pass
```

#### 3.10.2 Event Analysis Functions
```python
def analyze_event_returns(returns, events):
    """Analyze forward returns for each event type"""
    # Calculate conditional expected returns
    # Calculate conditional median returns
    # Calculate return skew
    # Calculate tail quantiles
    pass

def analyze_state_transitions(states, events):
    """Analyze state transitions for each event type"""
    # Calculate next state probabilities
    # Calculate continuation probabilities
    # Calculate reversal probabilities
    pass

def analyze_time_metrics(events):
    """Analyze time metrics for each event type"""
    # Calculate time-to-next-state
    # Calculate time-to-failure
    # Calculate median times
    pass
```

### 3.11 Analysis Functions

#### 3.11.1 Event Classification
```python
def classify_events_by_type(events, event_type):
    """Classify events by type"""
    # Filter events by type
    # Calculate statistics
    # Return classified events
    pass

def calculate_event_statistics(events):
    """Calculate comprehensive event statistics"""
    # Calculate event counts
    # Calculate event frequencies
    # Calculate event durations
    # Return statistics
    pass
```

#### 3.11.2 Forward Return Analysis
```python
def analyze_forward_returns(returns, events, horizons):
    """Analyze forward returns across different horizons"""
    # Calculate returns for each horizon
    # Group by event type
    # Calculate statistics
    # Return analysis results
    pass

def calculate_conditional_probabilities(states, events):
    """Calculate conditional state transition probabilities"""
    # Calculate P(S_{t+1}=j | S_t=i, E_i)
    # Calculate P(S_{t+1}=S_t | E_i)
    # Calculate P(S_{t+1}=-S_t | E_i)
    # Return probabilities
    pass
```

### 3.12 Visualization Functions

#### 3.12.1 Event Analysis Visualizations
```python
def plot_event_return_distributions(returns, events):
    """Plot return distributions for each event type"""
    # Create histograms
    # Add kernel density estimates
    # Highlight mean/median
    pass

def plot_event_probabilities(states, events):
    """Plot state transition probabilities for each event type"""
    # Create heatmaps
    # Show transition matrices
    # Highlight persistent states
    pass

def plot_event_time_metrics(events):
    """Plot time metrics for each event type"""
    # Create box plots
    # Show median times
    # Highlight outliers
    pass
```

## Expected Results

### 3.13 Primary Hypotheses

#### 3.13.1 Hypothesis 1: Sigma State Occupation Contains Predictive Information
**Prediction**: Conditional return distributions will differ significantly from unconditional distributions.

**Expected Results**:
- **Positive Events**: Higher expected returns for +n sigma events
- **Negative Events**: Lower expected returns for -n sigma events
- **Statistical Significance**: p-values < 0.05 for key comparisons
- **Effect Size**: ES > 0.5 for meaningful differences

#### 3.13.2 Hypothesis 2: Acceptance Thresholds Matter
**Prediction**: Optimal acceptance thresholds will show distinct patterns.

**Expected Results**:
- **50% Threshold**: Higher event frequency, lower continuation probability
- **80% Threshold**: Lower event frequency, higher continuation probability
- **Peak Performance**: Around 66-75% threshold

#### 3.13.3 Hypothesis 3: Event Type Matters
**Prediction**: Different event types will have distinct forward return distributions.

**Expected Results**:
- **E1 (First Touch)**: Lower continuation probability
- **E2 (First Close)**: Moderate continuation probability
- **E3/E4 (Consecutive Closes)**: High continuation probability
- **E5 (Occupancy)**: Very high continuation probability
- **E6 (Breakout-Retest)**: Variable continuation probability
- **E7 (Failure)**: Low continuation probability
- **E8 (State Advancement)**: Highest continuation probability

#### 3.13.4 Hypothesis 4: Time Horizon Effects
**Prediction**: Forward behavior will vary across time horizons.

**Expected Results**:
- **Short Horizons (1-3 bars)**: Higher noise, lower predictability
- **Medium Horizons (6-12 bars)**: Optimal predictability
- **Long Horizons (24-48 bars)**: Lower noise, higher predictability

## Implementation Timeline

### 3.14 Phase 3 Completion
**Target**: 3-4 weeks

#### 3.14.1 Week 1: Core Implementation
- Implement sigma state classification
- Implement event detection
- Set up basic analysis framework

#### 3.14.2 Week 2: Event Analysis
- Implement event classification
- Analyze forward returns
- Calculate state transition probabilities

#### 3.14.3 Week 3: Statistical Analysis
- Implement bootstrap confidence intervals
- Conduct hypothesis testing
- Calculate effect sizes

#### 3.14.4 Week 4: Validation and Refinement
- Validate results across assets
- Refine event definitions
- Prepare Phase 4 materials

### 3.15 Deliverables

#### 3.15.1 Research Outputs
1. **SIGMA_OCCUPATION_RESULTS.md** - This document (✅ Complete)
2. **sigma_states.py** - Sigma state classification
3. **events.py** - Event detection and analysis
4. **results/sigma_occupation/** - Analysis results

#### 3.15.2 Code Deliverables
1. **src/mve/sigma_states.py** - Core sigma state functions
2. **src/mve/events.py** - Event detection and analysis
3. **tests/mve/test_sigma_states.py** - Sigma state tests
4. **tests/mve/test_events.py** - Event tests

## Quality Assurance

### 3.16 Testing Strategy

#### 3.16.1 Unit Tests
- Test sigma state classification against known values
- Validate event detection logic
- Test forward return calculations

#### 3.16.2 Integration Tests
- Test end-to-end pipeline
- Validate cross-asset consistency
- Test performance with large datasets

#### 3.16.3 Statistical Validation
- Validate bootstrap confidence intervals
- Test statistical power
- Validate effect size calculations

### 3.17 Code Quality

#### 3.17.1 Documentation
- Document all functions and parameters
- Provide usage examples
- Include mathematical derivations

#### 3.17.2 Code Style
- Follow PEP 8 guidelines
- Use descriptive variable names
- Implement comprehensive error handling

#### 3.17.3 Performance
- Optimize for large datasets
- Implement efficient algorithms
- Use vectorized operations where possible

## Risk Management

### 3.18 Technical Risks

#### 3.18.1 Data Quality Risks
- **Risk**: Missing or corrupted data
- **Mitigation**: Implement robust data validation
- **Backup**: Use multiple data sources

#### 3.18.2 Computational Risks
- **Risk**: Memory or performance issues
- **Mitigation**: Implement efficient algorithms
- **Backup**: Use incremental processing

### 3.19 Research Risks

#### 3.19.1 Hypothesis Risks
- **Risk**: Hypotheses not supported by data
- **Mitigation**: Implement fail-closed approach
- **Backup**: Document negative results

#### 3.19.2 Interpretation Risks
- **Risk**: Misinterpretation of results
- **Mitigation**: Implement peer review
- **Backup**: Use multiple validation methods

## Conclusion

Phase 3 establishes the foundation for understanding whether **sigma state occupation contains measurable predictive information**. This research is critical because:

1. **Core Hypothesis**: The primary research question is whether state occupation contains predictive information
2. **Foundation**: Results will inform all subsequent phases
3. **Strategy Development**: Understanding occupation patterns is essential for strategy development
4. **Risk Management**: Understanding occupation effects helps manage strategy risk

The results will inform:
- **Phase 4**: Acceptance/Persistence model
- **Phase 5**: Volatility × displacement regime map
- **Phase 6**: Morphic rekey hypothesis
- **Phase 8**: Early strategy tests

The mathematical framework is now established for proceeding to Phase 4 (Acceptance/Persistence Model) and subsequent phases. The research will continue until clear evidence emerges or all stop conditions are met.