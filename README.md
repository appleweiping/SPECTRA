# SPECTRA: Specification-to-PVT-Closed Transistor-Level Analog Synthesis via Executable Design-Intent Programs

**SPECTRA** is a training-free neuro-symbolic synthesis framework that compiles natural-language analog and mixed-signal (AMS) circuit specifications into PVT-verified (45 corners) and Pelgrom-mismatch-checked transistor-level SPICE netlists on physical foundry device models.

Rather than prompting a language model to guess raw micrometre transistor widths or handing coupled width-and-length vectors to an unconstrained black-box optimizer, SPECTRA reformulates synthesis around **executable $g_m/I_D$ design-intent programs**:

1. **Executable Design-Intent Synthesis (`spectra/agent/dsl.py`)**: A sandboxed Python module declares low-dimensional physical intent parameters `PARAMS` ($g_m/I_D$, $L$, $I_D$, $C_c$, $k_z$; median 10 variables vs. 25 raw sizing variables, $2.3\times$ search compression) and a pure sizing procedure `design(p, lut, spec)`. Transistors are sized deterministically via pre-characterized multi-corner BSIM4 lookup tables (`lut.size` across 5 process corners $\times$ 3 temperatures) while emitting analytical self-predictions for every target specification.
2. **Zero-Cost Static ERC & Batch SPICE Evaluation (`spectra/sim/`)**: A canonical parser and electrical-rule checker (ERC) filters floating gates, illegal bulk ties, port mismatches, and geometry violations at zero simulation cost prior to batch `ngspice` BSIM4 simulation (DC, AC, transient, noise, temperature sweep, and mismatch Monte Carlo).
3. **Four-Channel Causal Diagnosis (`spectra/agent/diagnose.py`)**: Failed candidates trigger four deterministic evidence channels: normalized specification shortfalls, MOSFET operating-region headroom maps ($V_{DS} - V_{dsat}$), prediction-to-SPICE model-mismatch alerts, and finite-difference intent-parameter violation sensitivities, synthesized by 17 deterministic domain rules into root-cause hypotheses.
4. **Hierarchical Repair & Adaptive 45-Corner PVT Closure (`spectra/agent/spectra_agent.py`, `spectra/opt/`)**: Conditioned on diagnosis and retrieved topology cards, the synthesizer routes between `Edit` (rewriting symbolic topology or sizing equations), `Refine` (executing symmetry-preserving trust-region CMA-ES over top sensitivity-attributed intent knobs), and `Declare-Infeasible`, closing 45-corner PVT specifications via adaptive worst-corner active-set promotion ($|\mathcal{C}_r| \le 6$).

---

## Empirical Highlights

All quantitative claims across the repository and manuscripts are programmatically derived from committed evaluation artifacts in `results/` and verified by out-of-loop SPICE simulation.

| Evaluation Track | Scope & Budget Protocol | Key Verified Findings | Primary Artifacts |
|---|---|---|---|
| **End-to-End Synthesis** | 117 SKY130 tasks across 12 circuit families (61 primary near-frontier T3 + 45-corner PVT tasks); $B_{\text{LLM}}=12$, $B_{\text{sim}}=300/600$ | **79.2%** primary closure (**85.5%** T3, **68.2%** 45-corner PVT) vs. **68.3%** AnalogCoder-style, **45.9%** SPECTRA-min ($p_{\text{Holm}}=2\times 10^{-5}$), and **23.0%** Gen+TPE ($p_{\text{Holm}}<10^{-4}$); **70% vs. 27%** on 10-spec op-amps | `results/E1g_summary.json`, `results/comparisons.json` |
| **8-Framework Fixed-Topology Sizing** | 36 tasks $\times$ 3 seeds (108 cells/row) and 92 tasks $\times$ 3 seeds (276 cells/row); $B_{\text{sim}}=300$, $B_{\text{LLM}}=12$, 45-corner verifier | `SPECTRA-FullGrid`: **80.6% TT / 19.4% PVT** (0 crashes; beats AnalogCoder/ATLAS/GLOVA at $p_{\text{Holm}} \le 7.5\times 10^{-9}$). Budget-aligned `SPECTRA-Union-TopK4`: **91.7% TT / 33.3% PVT** (0.2820 PVT viol.); 92-task `SPECTRA-Family`: **80.4% TT / 26.3% PVT** (0.3822 PVT viol. vs. AnaFlow 80.1%/22.8%, 0.6053) | `results/paper_sizing_multiseed.json`, `results/external_expansion_92_summary.json` |
| **Architectural Ablations** | 34-task stratified subset, 23-task T3 subset, and 18-task $\times$ 3-seed (54-cell) mechanism matrix | Removing repair loop drops closure **81.4% $\to$ 50.0%**; disabling CMA-ES drops T3 **89.9% $\to$ 69.6%** (54-cell TT **63.0% $\to$ 42.6%**); removing diagnosis increases simulation cost by **+32.6%** ($77.8 \to 103.2$ sims) | `results/comparisons.json`, `results/component_mechanism_matrix.json` |
| **Diagnostics & Fault Scope** | 137 synthesized intent programs; 25 TT-passing PVT-failing designs; 166 single-fault test cases (7 classes) | 1st-order self-predictions match SPICE (0.7 dB gain, 6% power, 11% UGBW) while 2nd-order metrics diverge (30% slew, 85% settling); **59%** of corner failures occur at **1.62 V**; standalone fault top-1 is **80.7%** raw LLM vs. **76.5%** with element diagnosis ($p=0.21$) | `results/E1g_spectra_prediction_accuracy.json`, `results/pvt_failure_conditions.json`, `results/E4g_summary.json` |
| **Cross-Simulator, Cross-PDK & Tapeouts** | `AnalogGym` (`HoiLee`, `Leung`), `GF180MCU`, `ASAP7`, `PTM180`, `PTM45`, `SGAnalog` (17 tapeout tasks), `ngspice-44.2` & `Xyce-7.10` | **100%/100%** (`HoiLee`) and **100%/66.7%** (`Leung`) staged PVT on `AnalogGym`; **17.7$\times$** lower `Xyce` PVT violation on `Leung` (0.1364 vs. 2.4186); **48/51 (94.1%)** converged on `SGAnalog` (0.850 mean fidelity) | `results/analoggym_pvt_staged_comparison.md`, `results/sganalog_native_gpt61_multiseed.json` |

---

## SPECTRA-Bench Overview

**SPECTRA-Bench** (`data/bench/tasks.jsonl`, `data/bench/designer_tasks.jsonl`) provides **117 specification-driven synthesis tasks** across **12 SKY130 1.8 V circuit families** (mean 5.1 quantitative constraints per task):

- **Amplification & Signal Conditioning**: Operational amplifiers / OTAs (22), single-ended voltage amplifiers (9), transimpedance amplifiers (7), active filters (11), op-amp feedback applications (11)
- **Biasing & Power Management**: Current mirrors (10), low-dropout regulators (10), self-biased bandgap voltage references (8)
- **Mixed-Signal & Timing**: Continuous-time comparators (7), StrongARM/double-tail clocked comparators (7), ring/control VCOs (10), Schmitt triggers (5)

Tasks combine **92 certified tasks** (constructed from 28 parametric circuit templates explored via random-scalarization CMA-ES over 17,390 SPICE evaluations, with minimax Pareto-frontier refinement on 58 hard references and verified executable feasibility certificates across TT or all 45 PVT conditions: `{TT, FF, SS, SF, FS}` $\times$ `{-40, 27, 125 °C}` $\times$ `{1.62, 1.80, 1.98 V}`) with **25 independent practitioner tasks** authored from textbook specifications.

---

## Environment Setup & Quick Start

### 1. Automated Environment Bootstrap
On Ubuntu 24.04 / Debian environments, `.agents/environment.json` installs `ngspice` ($\ge 42$), TeXLive (`acmart`, `latexmk`, fonts), `poppler-utils`, and Python dependencies (`numpy`, `scipy`, `cma`, `optuna`, `matplotlib`, `openai`, `pillow`).

Manual installation:
```bash
sudo apt-get update && sudo apt-get install -y ngspice texlive-latex-extra texlive-publishers texlive-science texlive-bibtex-extra texlive-fonts-extra latexmk poppler-utils
python3 -m pip install numpy scipy cma optuna matplotlib openai pillow
```

### 2. Integrity & Contract Smoke Check
Verify repository schemas, netlist ERC/compiler contracts, and data digests offline:
```bash
PYTHONPATH=. python3 scripts/smoke_contracts.py
```

### 3. Lookup Table Generation & Benchmark Execution
```bash
# Pre-characterize SKY130 1.8 V BSIM4 gm/Id lookup tables across 5 corners x 3 temperatures
PYTHONPATH=. python3 -m scripts.gen_lut tt ff ss sf fs T=-40 T=27 T=125

# Run end-to-end synthesis on SPECTRA-Bench (requires OPENAI_API_KEY)
PYTHONPATH=. python3 -m scripts.run_bench --exp E1g --model gpt-6.1-sol --methods spectra,direct,genbo,spectra_min --seeds 0,1,2
```

---

## 2027 Conference Manuscript Packages

The `paper/` directory provides three tailored, double-anonymous 2027 submission packages built from shared data-verified macros (`paper/numbers.tex`, `paper/external_numbers.tex`, `paper/verified_macros.tex`) and Google Scholar-standardized bibliography (`paper/refs.bib`):

| Target Venue | Directory | Format & Page Budget | Compiled Deliverables |
|---|---|---|---|
| **ICCAD 2027** | `paper/` & `paper/iccad2027/` | ACM `acmart` (`sigconf,review,anonymous`), **8 + 1 pages** (8 technical pages + 1 reference page) + separate 5-page supplement | `paper/main.pdf`, `paper/supplement.pdf`, `paper/iccad2027/spectra_iccad2027{,_supplement}.pdf` |
| **DAC 2027** | `paper/dac2027/` | ACM `acmart` (`sigconf,review,anonymous`), **6 + 1 pages** (6 technical pages + 1 reference page) + separate 5-page supplement | `paper/dac2027/main.pdf`, `paper/dac2027/supplement.pdf` |
| **ICML 2027** | `paper/icml2027/` | Official `icml2027.sty` + `icml2027.bst` (unmodified spacing), **8 pages** main body + `Impact Statement` + `References` + single-column Appendix A–D | `paper/icml2027/main.pdf` |

To regenerate all tables, figures, macros, and compile every 2027 venue PDF with zero-overfull verification:
```bash
bash scripts/finalize_paper.sh
```

---

## Repository Structure

```text
spectra/
  agent/          Executable gm/Id DSL, subprocess sandbox, 4-channel causal diagnosis, knowledge cards, SPECTRA loop
  sim/            Canonical SPICE parser, static ERC, SKY130 compiler, BSIM4 LUT API, ngspice/Xyce runners, testbenches
  opt/            Intent-space trust-region CMA-ES, Optuna TPE, Bayesian & classical baselines
  bench/          Parametric circuit templates, Pareto-frontier refinement, natural-language task renderer
  baselines/      Direct codegen, generate-then-optimize, and external framework adapters
data/
  bench/          SPECTRA-Bench tasks (117), fixed-topology manifests (36 & 92 tasks), fault cases (166), cross-domain schemas
  lut/            Pre-characterized SKY130 1.8 V BSIM4 lookup tables (5 corners x 3 temperatures)
pdk/sky130/       Redistributable Apache-2.0 SkyWater SKY130 1.8 V BSIM4 FET, PNP, poly-resistor, and mismatch models
results/          Verified evaluation summaries, paired statistical tests, multi-seed matrices, and cross-domain benchmarks
scripts/          Experiment runners, statistical analyzers, macro/figure/table generators, and contract validators
paper/            Shared sections/tables/figures + ICCAD 2027, DAC 2027, and ICML 2027 LaTeX packages
docs/             Evaluation protocols, component attribution maps, and literature surveys
```
