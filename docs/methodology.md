# Evaluation Methodology and Scoring Formulations

## Mathematical Formulation

### 1. Multi-Criteria Semantic Quality Score

Given a set of $M$ active criteria $C = \{c_1, c_2, \dots, c_M\}$ and corresponding normalized user weights $W = \{w_1, w_2, \dots, w_M\}$ where:

$$\sum_{i=1}^{M} w_i = 1.0, \quad w_i \ge 0$$

The raw semantic quality score $Q(r)$ for candidate response $r$ evaluated across criteria scores $S_i(r) \in [0, 10]$ is:

$$Q(r) = \sum_{i=1}^{M} w_i \cdot S_i(r)$$

---

### 2. Min-Max Normalization of Resource Metrics

Resource metrics (token count $T$, API cost $C$, and latency $L$) have differing scales and dimensions. To incorporate them fairly into composite scoring without arbitrary unit distortion, we apply min-max normalization across all $N$ candidate responses in the run:

$$\tilde{T}(r) = \frac{T(r) - \min_{j} T(j)}{\max_{j} T(j) - \min_{j} T(j) + \epsilon}$$

$$\tilde{C}(r) = \frac{C(r) - \min_{j} C(j)}{\max_{j} C(j) - \min_{j} C(j) + \epsilon}$$

$$\tilde{L}(r) = \frac{L(r) - \min_{j} L(j)}{\max_{j} L(j) - \min_{j} L(j) + \epsilon}$$

where $\epsilon = 10^{-6}$ prevents division by zero when all candidates have identical metrics.

---

### 3. Resource Penalty and Scoring Modes

The aggregate resource penalty $P(r)$ is computed according to the active scoring mode:

| Scoring Mode | Formula for Penalty $P(r)$ | Description |
|---|---|---|
| **Quality-First** | $P(r) = 0$ | No penalties; ranking is strictly based on semantic quality $Q(r)$. |
| **Balanced** | $P(r) = 0.08 \cdot \tilde{C}(r) + 0.04 \cdot \tilde{T}(r) + 0.04 \cdot \tilde{L}(r)$ | Slight penalty for disproportionately slow or expensive responses. |
| **Cost-Aware** | $P(r) = 0.20 \cdot \tilde{C}(r) + 0.05 \cdot \tilde{T}(r) + 0.05 \cdot \tilde{L}(r)$ | Heavy penalty on API cost, favoring cost-efficient models. |
| **User-Customized** | $P(r) = w_{\text{cost}} \cdot \tilde{C}(r) + w_{\text{token}} \cdot \tilde{T}(r) + w_{\text{latency}} \cdot \tilde{L}(r)$ | User directly allocates resource weights in the preference panel. |

The composite overall score $S(r)$ is then computed and clamped to the $[0, 10]$ interval:

$$S(r) = \text{clamp}\left(0, 10, Q(r) \cdot (1 - \lambda) - 10 \cdot P(r) + \lambda \cdot 5.0\right)$$

where $\lambda$ represents the resource penalty influence factor.

---

### 4. Synthesis Improvement Percentage

To measure the relative gain of adaptive multi-LLM synthesis over selecting the single highest-performing candidate model:

$$\Delta_{\text{improvement}}\% = \frac{Q(\text{synthesis}) - \max_{j} Q(r_j)}{\max_{j} Q(r_j)} \times 100$$

A positive $\Delta_{\text{improvement}}\%$ indicates that the structured synthesis produced an answer superior to any individual candidate model.

---

### 5. Pareto Optimality Criteria

A model or synthesis output $A$ **Pareto-dominates** output $B$ ($A \succ B$) if and only if:

$$Q(A) \ge Q(B) \quad \text{and} \quad \text{Cost}(A) \le \text{Cost}(B)$$

with at least one strict inequality:

$$(Q(A) > Q(B)) \lor (\text{Cost}(A) < \text{Cost}(B))$$

The **Pareto Frontier** consists of all responses that are not Pareto-dominated by any other response in the comparison set.

---

### 6. Contradiction Resolution Protocol

When the Conflict Analyzer identifies a contradiction between Candidate $A$ and Candidate $B$:
1. Check if either claim is corroborated by Candidate $C$.
2. Check if the claim contains verifiable factual data (e.g., standard RFCs, IEEE definitions, textbook algorithms).
3. If uncorroborated and in conflict, the Synthesizer is instructed to:
   - State the consensus facts.
   - Explicitly note the divergence or nuance without taking an unverified side.
   - Recommend the standard/canonical interpretation.
