# Prop Firm Payout System — Mathematical Breakdown
> Source: MAD context 2026-05-30 | Format: Q&A Ontology Style
> Reference: ChatGPT breakdown of Aqua prop firm structure

---

## Q1: What is the core equation prop firms optimize?

**A:** The entire firm exists to minimize:

```
E = P(W) · G - P(L) · D - V
```

Where:
- **P(W)** = probability of trader winning
- **G** = payout obligation
- **P(L)** = probability trader fails
- **D** = retained challenge capital
- **V** = volatility exposure from abnormal payout spikes

**Key insight:** The ENTIRE firm exists to suppress **V = payout variance**. Not profitability.

---

## Q2: What is the Consistency Rule mathematically?

**A:** The real constraint equation:

```
C = D_max / P_total
```

Where:
- **D_max** = largest profitable day
- **P_total** = total accumulated profits
- **Constraint:** C ≤ 0.15 or 0.20 (depending on account type)

**Example:**
- Largest day = $4,000
- P_required = 4000 / 0.15 = **$26,666 minimum total profit**
- One explosive day forces ~26k total profit requirement

**Translation:** Consistency rules are **power-law dampeners**. They exist because payout distributions follow `P(x) ~ x^(-α)`. A tiny number of traders generate massive asymmetrical wins during high-volatility events with nonlinear RR. Those traders destroy prop-firm cashflow stability.

---

## Q3: What is the Trailing Drawdown equation?

**A:** Effective survivability:

```
B = E - T(E_max)
```

Where:
- **B** = usable buffer
- **E** = current equity
- **T(E_max)** = trailing drawdown anchored to peak equity

**Critical dynamic:** As equity rises, buffer compresses. A trader who hits +15% may actually become MORE fragile than at account start. That's intentional.

---

## Q4: What is the firm's ideal trader profile?

**A:** Mathematically:

```
σ_p → 0
```

They want **minimal payout volatility**:
- Smooth equity curves
- Low kurtosis
- Low skew
- Low payout clustering

---

## Q5: What breaks their model?

**A:** CEREBUS-style trading generates:
- **High skew**
- **High convexity**
- **Impulse extraction**
- **Clustered gains** (few trades produce most returns)

This breaks the expected distribution model. That's exactly what our system does.

---

## Q6: What is the actual game?

**A:** It's NOT "pass the challenge."

The actual game is:

```
optimize payout extraction against constraint equations
```

Every rule exists to smooth **capital outflow entropy**:
- Consistency rules
- Buffer rules
- Scaling rules
- Minimum trading days
- Payout delays

---

## Q7: What is the firm's internal optimization function?

**A:**

```
R = μ_p / σ_p
```

They optimize **mean retained revenue** against **payout volatility**. Everything else is UI/branding layered on top.

---

## Key Takeaways for CEREBUS Integration

1. **Our edge is their weakness:** High skew + clustered gains = breaks their distribution model
2. **Consistency rule navigation:** Need to manage D_max / P_total ratio — don't let one big day blow the consistency constraint
3. **Trailing DD awareness:** Higher equity = more fragile buffer. Manage position size as equity grows.
4. **The real target:** Not just passing — optimizing payout extraction against their constraint equations
5. **System design implication:** Our impulse extraction style is exactly what they try to filter out. Need to understand the thresholds.

---

## Connection to Existing Work

This connects to the CEREBUS quantitative framework:
- **P90 Kinetic Engine** = impulse extraction (high skew generator)
- **Symmetry Trap** = structural edge (clustered gains)
- **Dual-Engine Convergence** = the highest convexity setups
- **Risk management** = needs to account for prop firm constraint equations, not just raw edge

The prop firm system is a **constraint layer** on top of our trading system. Both need to be optimized simultaneously.
