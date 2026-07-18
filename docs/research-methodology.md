# Research Methodology & Continual Learning Metrics

This document defines the mathematical formulas, metrics, and statistical protocols implemented in **ForgetGuard AI** to ensure scientific honesty and reproducibility.

---

## 1. Core Continual Learning Metrics

We denote $a_{i, j}$ as the evaluation metric score (e.g. accuracy or exact match) on task $j$ after the model has completed training on task $i$.
Here, tasks are ordered sequentially from $1$ to $T$.

### 1.1 Average Accuracy ($A_k$)
The mean accuracy across all tasks learned up to task $k$.
$$A_k = \frac{1}{k} \sum_{j=1}^{k} a_{k, j}$$
- **Direction**: Higher is better.
- **Aggregation**: Arithmetic mean.

### 1.2 Forgetting Score ($F_{k, j}$)
The performance drop on task $j$ after learning subsequent tasks up to task $k$.
$$F_{k, j} = \max_{i \in \{1, \dots, k-1\}} (a_{i, j}) - a_{k, j}$$
- **Forgetting Average ($F_k$)**:
$$F_k = \frac{1}{k-1} \sum_{j=1}^{k-1} F_{k, j}$$
- **Direction**: Lower is better (representing higher retention).

### 1.3 Backward Transfer ($BWT_k$)
Measures the influence of learning new tasks on performance on previous tasks.
$$BWT_k = \frac{1}{k-1} \sum_{j=1}^{k-1} (a_{k, j} - a_{j, j})$$
- **Direction**: Positive is active reinforcement; negative is forgetting.

### 1.4 Forward Transfer ($FWT_k$)
Measures the influence of learning previous tasks on the learning speed/performance of unseen future tasks.
$$FWT_k = \frac{1}{k-1} \sum_{j=2}^{k} (a_{j-1, j} - b_j)$$
Where $b_j$ is the performance of a randomly initialized or base model on task $j$.
- **Direction**: Positive means knowledge transfers forward (zero-shot transfer).

---

## 2. Statistical Aggregation Protocols

### 2.1 Repeated Seeds & Variance
Every experiment configuration must support running multiple distinct seeds ($N \ge 3$).
For any reported metric $M$, we report:
- **Mean ($\mu$)**: $\frac{1}{N}\sum_{n=1}^N M_n$
- **Standard Deviation ($\sigma$)**: $\sqrt{\frac{1}{N-1}\sum_{n=1}^N (M_n - \mu)^2}$
- **Confidence Intervals (CI)**: 95% Confidence Interval using Student's $t$-distribution:
$$CI = \mu \pm t_{\alpha/2, N-1} \times \frac{\sigma}{\sqrt{N}}$$

### 2.2 Expected Calibration Error (ECE)
To ensure the LLM does not become overconfident and miscalibrated after fine-tuning, we compute ECE. We divide predictions into $M$ equally spaced bins $B_m \subset (0, 1]$ and calculate:
$$ECE = \sum_{m=1}^M \frac{|B_m|}{N} \left| acc(B_m) - conf(B_m) \right|$$
Where $acc(B_m)$ is the accuracy of samples in bin $m$, and $conf(B_m)$ is the average confidence of predictions in bin $m$.
- **Direction**: Lower is better.
