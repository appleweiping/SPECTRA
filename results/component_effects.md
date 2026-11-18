# Component effects

This table uses the frozen GPT-6.1-sol runs. Endpoint success and mechanism evidence are separate, and mixed or null effects remain visible.

| Component | Matched tasks | Success with | Success without | Delta (pp) | Mean sims with/without | W/L | Paired p | Evidence status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| diagnosis | 34 | 0.814 | 0.794 | +2.0 | 77.8/103.2 | 7/5 | 0.79219 | mixed |
| intent-program abstraction | 34 | 0.814 | 0.838 | -2.5 | 77.8/99.2 | 6/8 | 0.75453 | mixed |
| PVT-aware refinement | 23 | 0.899 | 0.696 | +20.3 | 47.5/24.6 | 7/3 | 0.05194 | directional |
| knowledge cards | 23 | 0.899 | 0.870 | +2.9 | 47.5/53.1 | 3/6 | 0.85903 | mixed |

Mechanism notes

- **diagnosis**. The failure-feedback path lowers mean simulations on the matched set and provides causal device/sensitivity evidence. E4 fault top-1 is raw 80.7% versus diagnosis 76.5%, so localization is a negative or mixed standalone result.
- **intent-program abstraction**. Median intent variables 10 versus 25 raw sizing variables (2.29x compression). First-order predictions are accurate for some metrics and poor for second-order metrics.
- **PVT-aware refinement**. Worst-condition CMA-ES refinement is the strongest endpoint contribution in the matched T3 block.
- **knowledge cards**. Cards encode topology, headroom, bias and stability constraints. The observed endpoint difference is small and the W/L test is non-significant, so the mechanism is retained without an essentiality claim.

Fault localization test. raw top-1=0.807, diagnosis top-1=0.765, exact McNemar p=0.21004.
