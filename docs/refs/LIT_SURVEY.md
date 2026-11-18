# Literature Survey: LLM Agents for End-to-End Analog Circuit Generation (2023–2026)

Compiled 2026-11-16 for an ICCAD submission (SPECTRA: NL spec → topology → sizing → SPICE/PVT verification).

## How this was verified

| Tag | Meaning |
|---|---|
| **[PDF]** | I read the arXiv full text (setup, results and limitations sections) on 2026-11-16. |
| **[DOI]** | Venue, pages and authors confirmed through the Crossref API, the PMLR index or the ACM/IEEE DOI. |
| **[arXiv]** | Title, authors and comments confirmed through the arXiv API. The venue claim comes from the arXiv comment or the paper header. |
| **[2nd]** | Details come from citing papers or a survey only. I did not read the paper itself. |
| **UNVERIFIED** | I could not confirm the item. Do not cite it without checking. |

Numbers are as reported by each paper's authors. Model names (for example "GPT-5", "Claude Opus 5.5", "Claude Fable 5") are quoted as each paper states them.

---

## 0. Executive summary (positioning for SPECTRA)

1. **Most LLM work on topology generation is evaluated with toy device models and functional pass/fail checks.**
   - AnalogCoder (24 tasks), AnalogAgent (30 tasks) and MenTeR use **Level-1 square-law MOSFETs** (`kp=100e-6, vto=0.5`) in PySpice/ngspice. A design passes on a functional check, not on numeric specs.
   - AnalogCoder-Pro moves to BPTM 45 nm and adds Bayesian-optimization (BO) sizing, but it optimizes a **single scalar FoM** (GBW·CL/Power). It does not check multi-spec satisfaction.
2. **Spec-driven end-to-end systems are recent (Dec 2025–Nov 2026) and evaluate nominal (TT) conditions only.**
   - AnalogSAGE: 10 op-amp specs on SKY130.
   - AaLLM: 24 op-amp target specs on SKY130.
   - SAFTAC (NeurIPS'26): 8,626 tasks, TSMC 180 nm-style models, fine-tuned Qwen3-8B.
   - A keyword scan of the full texts finds **0 PVT/Monte-Carlo verification** in AnalogCoder, AnalogCoder-Pro, AnalogAgent, AnalogSAGE, AaLLM, SAFTAC, MenTeR and AnalogXpert (§5, Table G1).
3. **PVT/Monte-Carlo-aware LLM work exists only for sizing a fixed topology, and only at small scale.**
   - AnalogScout: 3 OTAs, 9 corners, 16k-simulation budget, submitted to ISCAS'27.
   - OPERA: 6 op-amps, 15 corners post-layout, designer-taught, submitted to ISCAS'27.
   - SABLE: 2 tasks, 3 corners.
   - The Long-Horizon Analog Design Bench (Sep 2026) measures frontier coding agents on 50 tasks, some with 30 PVT conditions and 20 mismatch samples. Pass rates are 8–78%, and **electrical closure is the dominant failure** (it is a benchmark, not a method).
4. **Benchmark scale.** Among LLM sizing studies before AgenticSizing, benchmark breadth is "2 to 24 circuits, largest ≤20 transistors" (AgenticSizing, Table I).
   - The largest LLM-agent benchmarks with quantitative specs are: AMS-SizingBench (AutoSizer, ICML'26) with 24 SKY130 circuits for sizing only; AaLLM with 24 op-amp specs; Long-Horizon Bench with 50 tasks.
   - Topology-only benchmarks are larger but non-quantitative: AnalogXpert with 30 real + 2k synthetic tasks; AnalogAgent/AnalogCoder-Pro with 28–30 functional tasks.
5. **ICCAD 2026 (held Nov 8–12, 2026) had no regular paper on LLM-agent analog topology+sizing.** In program v19, the analog-sizing sessions are RL/BO-based (MetaSizing, hypervolume many-objective synthesis, mixed-variable hierarchical BO, ATLAS) plus AnalogRetriever (cross-modal IP retrieval). LLM-analog work appeared at ICCAD 2025 (AnaFlow invited, ASTRA, KG-agents, multi-agent generative synthesis invited) and DAC 2026 (special research sessions: PANDA, AnAutomate, HRL-Topo). The ICCAD 2027 slot for an end-to-end, PVT-verified LLM synthesis paper is open.

---

## 1. ICCAD submission format

### ICCAD 2026 (45th edition, San Jose, Nov 8–12, 2026). Source: official CFP PDF <https://ieee-cas.org/files/ieeecass/2026-02/iccad-2026-cfp.pdf> (same text as <https://confcats-siteplex.s3.amazonaws.com/iccad/files/iccad26-cfp_web-17.pdf>); CFP web page <https://iccad.com/2026/authors/call-for-papers>; submission site <https://iccad2026.hotcrp.com/>; camera-ready rules <https://iccad.com/2026/final-author-instructions>.

**Length and layout**
- A paper must be **no more than 8 pages (including the abstract, figures and tables), double-columned, 9 pt or 10 pt font**.
- **One page of references is allowed and does not count** toward the 8 pages.
- PDF only, with selectable text and embedded fonts.

**Review**
- **Double-blind.** No names or affiliations anywhere, including the abstract and the embedded PDF metadata. Self-citations must be in the third person.
- Do not link non-anonymized code. Describe it in text, or use anonymous.4open.science.
- arXiv preprints and non-archival workshop papers are allowed. Simultaneous submission leads to summary rejection.
- Papers are reviewed as finished work; "preliminary submissions will be at a disadvantage."
- Submission has two stages: (1) title, abstract and the full co-author list (for conflicts of interest) by the abstract deadline; (2) the PDF one week later. The abstract can still be edited in stage 2.

**Template**
- The CFP PDF names no template. The 2026 CFP web page's "Download Paper Template" link points to **ACM's proceedings template** (<https://www.acm.org/publications/proceedings-template>).
- The 2026 camera-ready page says "Authors must prepare their final manuscript using the latest ACM conference proceedings templates." This follows ICCAD's switch to **ACM Open Access**: an APC of $250 for ACM/SIG members or $350 for non-members, waived for ACM-OA institutions.
- By contrast, **ICCAD 2025 recommended the IEEE template** (<https://2025.iccad.com/authors/initial-author-information>).
- ⚠ The project CLAUDE.md says "IEEEtran conference". That was correct for 2025 but not for 2026. For 2027, check the new CFP. Keep the LaTeX portable between `IEEEtran` and `acmart` (`sigconf`).

**Abstract length:** the CFP sets **no word limit**. The abstract submitted in stage 1 may be revised at paper submission.

**Camera-ready:** 6 pages plus 1 page of references free. Up to 2 extra content pages at $150 each, to a maximum of 8 pages plus 1 page of references. Presentation must be in person.

**2026 dates**

| Milestone | Date |
|---|---|
| Abstract | Apr 7, 2026 |
| Paper | Apr 14, 2026, 23:59 AoE (no extensions) |
| Reviews / rebuttal start | Jun 10 |
| Rebuttal due | Jun 20 (HotCRP; the PDF says Jun 17) |
| Notification | Jul 11 |
| Camera-ready | Aug 24 |

**Acceptance:** HotCRP reports **371 of 1464 submissions accepted (25.3%)**.

### ICCAD 2027

**Not announced** as of 2026-11-16: `iccad.com/2027/call-for-papers` returns 404, and a search found no CFP. In past cycles the paper deadline fell in April or early May: Apr 21, 2025; Apr 14, 2026; May 5, 2024. Plan for roughly mid-April 2027.

---

## 2. Master comparison table (methods)

**Scope codes:** T = topology generation, S = sizing, V = verification, L = layout. **"Spec type":** F = functional pass/fail check; Q = quantitative multi-spec thresholds; FoM = scalar figure-of-merit optimization.

| Work (venue) | Scope | Benchmark scale | Spec type | Simulator / models | LLM(s) | PVT / MC | Code |
|---|---|---|---|---|---|---|---|
| AnalogCoder (AAAI'25) | T (+LLM-set sizes) | 24 tasks, 11 types | F | ngspice/PySpice, Level-1 | 40+ LLMs; GPT-4o, Claude-3.5 best | none | laiyao1/AnalogCoder |
| AnalogCoder-Pro (TCAD'26) | T + S (BO) | 28 tasks / 13 types; 12 sizing prompts | F + FoM | ngspice, BPTM 45 nm | GPT-5, Claude-3.7, GPT-4.1, DeepSeek-V3, Gemini-2.5-Flash, Qwen2.5-Coder | none | laiyao1/AnalogCoderPro |
| AnalogAgent (arXiv'26) | T | 30 tasks (AnalogCoder lineage) | F | ngspice, Level-1 | GPT-5, Gemini-2.5-Flash, Qwen-8B, Llama-3-8B, DS-V2-Lite | none | artifact-repro/analogagent-artifact |
| MenTeR (ICLAD'25) | T | 24 AnalogCoder tasks + 1 BGR | F | PySpice | GPT-4o | none | — |
| AnalogXpert (ISEDA'25) | T | 30 real + 2k synthetic | structural rules / human | none (no sim) | GPT-4o | none | — |
| Artisan (DAC'24) | T + S (op-amp) | [2nd] | Q | [2nd] | fine-tuned Llama2-7B [2nd] | UNVERIFIED | — |
| Atelier (TCAD'26) | T + S (op-amp) | [2nd] | Q | HSPICE [2nd]; sizing by CMA-ES [2nd] | general LLMs + KB | UNVERIFIED | — |
| AmpAgent (arXiv'24) | S (+formula derivation) | 7 multi-stage amps | Q | Spectre, 0.18 µm | GPT-4-1106 | none | — |
| AMSnet-KG/AMSgen (TODAES'25) | T + S (BO) | 2 case studies (op-amp, comparator) | Q | Spectre, SMIC 28 nm | GPT-4 | none | — |
| AnalogSAGE (arXiv'25) | T + S (BO) | 10 op-amp spec tasks | Q | ngspice, SKY130 | Gemini-2.5-Flash | none | xz-group/AnalogSAGE |
| AaLLM (arXiv'26) | T + S (no optimizer) | 24 op-amp spec targets; 12 sizing tasks ×2 seeds; 3 filters | Q | SPICE, SKY130; PTM 45 nm port | FLAN-T5 (FT) + Claude Haiku 4.5 / Sonnet 4.6 | none | anonymous.4open.science/r/AaLLM |
| SAFTAC (NeurIPS'26) | T + S (BO in reward) | 8,626 tasks / 10 types (114 netlists); eval on 5 types | Q | ngspice (testbenches ported from Spectre), tsmc18 models | Qwen3-8B (SFT+GRPO) vs GPT-5.2/5.4, Claude-Opus-4.7 | none | — |
| PANDA (DAC'26 SRS) | T + S + L | [2nd] | Q | — | — | — | PKU-IDEA/PANDA |
| OPERA (subm. ISCAS'27) | S + L (designer-taught gm/ID) | 6 op-amps + bias | Q | SKY130, gLayout, PEX | Claude Opus/Sonnet 5.5 | **15 PVT corners post-PEX** | AMPICLab/AMPICBench |
| ADO-LLM (ICCAD'24) | S | 2 circuits | FoM | HSPICE, commercial 90 nm | GPT-3.5-turbo | none | — |
| LEDRO (ICLAD'25) | S | 22 op-amps × 4 FinFET nodes | FoM | Spectre, PTM-MG 7/10/14/16 nm | LLaMA3-70B (+GPT-3.5) | none | dimplekochar/LEDRO |
| AnaFlow (ICCAD'25 inv.) | S | 2 op-amps | Q | ngspice, PTM 45 nm | Gemini 2.5 Pro/Flash, o3, Claude Sonnet 4/Opus 4, Grok 3 | none | — |
| EEsizer (TCSI'26) | S | 6 basic + 20-T op-amp, 3 nodes | Q | ngspice, PTM 180/130/90 nm | 8 LLMs (o3, GPT-4.1, Gemini-2.0-Flash…) | Gaussian W/Vth (10–50 samples), post hoc | — |
| AutoSizer (ICML'26) | S | **24 SKY130 circuits** (AMS-SizingBench) | Q + FoM | ngspice, SKY130 | Gemini-2.5-Flash | none | yuxi120407/AutoSizer |
| AgenticSizing (arXiv'26) | S | 8 circuits; up to 55 T / 60 vars | Q + FoM | Spectre | GPT-5.2 | none | aprilaihub/agentic-analog-sizing |
| AnalogScout (subm. ISCAS'27) | S | 3 OTAs SKY130 + 1 GF180 | Q (min power s.t. specs) | ngspice | DeepSeek "flash" | **9 corners + TT mismatch MC (N=500)** | (LAS baseline repo only) |
| TopoSizing (TCAD'26) | S | 4 AMS circuits | Q | TT corner | — | none | — |
| CktGNN (ICLR'23) | T + S | OCB: 10k op-amps | FoM | OCB simulator | GNN (no LLM) | none | zehao-dong/CktGNN |
| LaMAGIC / LaMAGIC2 (ICML'24/'25) | T (+duty cycle) | 3–6-component power converters, ~120k train | Q (ratio, efficiency; tolerance) | ngspice | Flan-T5-base (FT) | none | turtleben/LaMAGIC |
| AnalogGenie (ICLR'25) | T (+GA sizing) | 3,350 topologies, 11 types | validity / novelty / FoM | ngspice (BPTM 45 nm per AnalogCoder-Pro) | 11.8M-param decoder | none | xz-group/AnalogGenie |
| FALCON (NeurIPS'25) | T-select + S + L-aware | 1M sims, 20 topologies, 5 RF types | Q (≤20% error) | Spectre, 45 nm | GNN/MLP (no LLM) | none | AsalMehradfar/FALCON |

---

## 3. Detailed entries

### 3.1 LLM systems for topology generation and end-to-end design

#### AnalogCoder — [PDF][DOI]
- **Citation:** Yao Lai, Sungyoung Lee, Guojin Chen, Souradip Poddar, Mengkang Hu, David Z. Pan, Ping Luo. "AnalogCoder: Analog Circuit Design via Training-Free Code Generation." *AAAI 2025*, 39(1):379–387. DOI 10.1609/aaai.v39i1.32016. arXiv:2405.14918. AAAI Oral.
- **Scope:** topology plus nominal device values that the LLM writes in code. It is a functional-correctness task with no spec-driven sizing.
- **Pipeline:**
  - The LLM writes PySpice (Python) code instead of raw SPICE. Prompts use domain chain-of-thought and one in-context example.
  - A **feedback-enhanced flow** runs four checks: (1) requirement check (ports and components); (2) simulation and operating-point check (floating nodes, MOSFET regions); (3) DC sweep check (signal path, best bias); (4) function check (DC/AC/transient). Errors are returned to the LLM, with at most 3 generations (2 retries).
  - A **circuit tool library** stores verified subcircuits for composite tasks.
  - A fine-tuned GPT-3.5 variant is tested as an ablation.
- **Benchmark:** 24 tasks (8 easy, 5 medium, 11 hard). The task list is in `/home/user/refs/repos/analogcoder/src/problem_set.tsv`.
  - Covered: single, cascode and three-stage amplifiers; common-drain and common-gate stages; inverters; current mirrors; differential and two-stage op-amps; telescopic cascode op-amp; RC and Wien oscillators; integrator; differentiator; adder; subtractor; Schmitt trigger; VCO; PLL.
- **Simulator / models:** ngspice through PySpice. **Level-1 MOSFET models** (`nmos level=1 kp=100e-6 vto=0.5`; `pmos kp=50e-6 vto=-0.5`), W/L in µm.
- **Metrics:** Pass@1 and Pass@5 with n=30 trials (open-source LLMs, GPT-3.5) or n=15 (GPT-4, GPT-4o, fine-tuned models); #solved means at least one success in n.
- **Results:**
  - AnalogCoder (GPT-4o): **20/24 solved**, Pass@1 66.1, Pass@5 75.9. Plain GPT-4o: 15.
  - The repo README adds Claude-3.5-based AnalogCoder: 22/24 (76.1 / 86.3).
  - Leaderboard of 40+ LLMs.
- **Baselines:** raw LLMs, ablations (without context, flow or CoT; SPICE instead of Python), fine-tuned GPT-3.5.
- **Limitations stated:** "LLMs lack the capability to design highly complex analog circuits"; cost.
- **Limitations noted by others:** AnalogGenie reports a maximum of about 10 devices per circuit, 57.3% valid circuits, 8.9% novel topologies and op-amp FoM 1.7.
- **Repo:** <https://github.com/laiyao1/AnalogCoder> (local copy: `/home/user/refs/repos/analogcoder`).

#### AnalogCoder-Pro — [PDF][DOI]
- **Citation:** Yao Lai, Souradip Poddar, Sungyoung Lee, Guojin Chen, Mengkang Hu, Bei Yu, Ping Luo, David Z. Pan. "AnalogCoder-Pro: Unifying Analog Circuit Generation and Optimization via Multimodal LLMs." *IEEE TCAD* 45(11):5149–5162, Nov 2026. DOI 10.1109/TCAD.2026.3673493. arXiv:2508.02518.
- **Scope:** topology plus sizing.
- **Pipeline:**
  - **Multimodal diagnosis-and-repair** loop that reads error text plus waveform images.
  - Circuit tool library.
  - LLM **parameter extraction**: the LLM rewrites the netlist into `create_circuit(params)` with search ranges.
  - **Bayesian optimization** with Optuna TPE: **1000 trials**, 25% random initialization, multivariate sampling.
  - A new **multi-resolution DC-sweep input-bias search** (20/200/2000 steps) that sets Vout ≈ VDD/2.
  - "Target-guided" prompts put the optimization goal into topology generation.
- **Benchmark:**
  - Topology: **28 tasks over 13 types** (amplifiers, op-amps, current mirrors, mixers, filters, comparators, …); tasks 9 and 22–28 are composite.
  - Sizing: **12 design instructions** (single-stage amplifier and multi-stage op-amp × Gain / GBW / FoM objectives).
- **Simulator / models:** ngspice through PySpice; **BPTM 45 nm** ("consistent with AnalogGenie").
- **Metrics and runs:**
  - Pass@k with n=30 and up to 3 attempts; temperature 0.5 (0.0 for parameter extraction).
  - Best FoM over 30 runs of 1000 samples each. Bias-search comparison over 5 seeds.
  - FoM = GBW·CL/Power.
- **LLMs:** GPT-5, GPT-4.1, GPT-4.1-nano, GPT-4o, Claude-3.7-Sonnet, DeepSeek-V3, Gemini-2.5-Flash, Qwen-2.5-Coder-32B.
- **Results:**
  - GPT-5: **28/28 solved, Pass@5 98.6%**. The authors frame this as "doubled from 14 (GPT-3.5) to 28 (GPT-5)" since AnalogCoder.
  - **Up to 2× op-amp FoM vs AnalogGenie.**
- **Baselines:** AnalogCoder, AnalogGenie, CktGNN (FoM numbers taken from the original papers), ablations.
- **Gaps (my reading):**
  - Correctness is still a functional check.
  - Sizing maximizes a single FoM, with no constraint satisfaction on multiple specs.
  - No PVT or Monte Carlo.
  - AnalogSAGE measured AnalogCoder-Pro at **10% pass / 2% Pass@1 on spec-driven SKY130 tasks**.
- **Repo:** <https://github.com/laiyao1/AnalogCoderPro>.

#### AnalogAgent — [PDF][arXiv]
- **Citation:** Z. Bao, Z. Lin, J. Wang, J. Hu, Y. Gao, Y. Wu, X. Li, X. Xu. "AnalogAgent: Self-Improving Analog Circuit Design Automation with LLM Agents." arXiv:2603.23910, Mar 2026. Venue not stated.
- **Scope:** topology/netlist generation (functional).
- **Pipeline:** training-free multi-agent system with a Code Generator, Design Optimizer and Knowledge Curator. A **self-evolving memory** "playbook" distils execution feedback, which addresses "context attrition" in single-model loops.
- **Benchmark:** **30 tasks** (8 easy, 5 medium, 17 hard) adopted from AnalogCoder and AnalogCoder-Pro. Level-1 models. Pass@1 and Pass@5. 5 random trials, reported as mean±std.
- **LLMs:** GPT-5, Gemini-2.5-Flash, Qwen-8B, Llama-3-8B, DeepSeek-V2-Lite.
- **Results:**
  - GPT-5: **97.4 / 100.0** Pass@1 / Pass@5. Gemini-2.5-Flash: 92.0 / 99.9.
  - Qwen-8B: 72.1 Pass@1 overall; the abstract states "+48.8% average Pass@1 gain".
  - AnalogCoder-Pro with GPT-5: 88.6 / 98.2.
  - Time-to-first-success 1.3 min (vs 2.1 for AnalogCoder-Pro); about 32K tokens to first success (vs about 40K).
- **Baselines:** SPICEPilot, AnalogCoder, AnalogCoder-Pro.
- **Repo:** <https://github.com/artifact-repro/analogagent-artifact>, as cited in the paper.

#### MenTeR — [PDF][DOI]
- **Citation:** P.-H. Chen, Y.-S. Lin, W.-C. Lee, T.-Y. Leu, P.-H. Hsu, A. Dissanayake, S. Oh, C.-S. Chiu (MediaTek). "MenTeR: A fully-automated Multi-agenT workflow for end-to-end RF/Analog Circuits Netlist Design." *IEEE ICLAD 2025*, pp. 124–132. DOI 10.1109/ICLAD65226.2025.00015. arXiv:2505.22990.
- **Pipeline:** an "Investigator" agent decomposes the task and dispatches specialized agents that use RAG, PySpice code and self-validation.
- **Evaluation:** **AnalogCoder's 24 tasks** with at most 5 attempts per task, plus a CMOS bandgap reference. GPT-4o backbone.
- **Results:** average **Pass@1 84.2%**.
- **Baselines:** single-agent AnalogCoder with o3-mini and DeepSeek-R1-distill-32B.

#### AnalogXpert — [PDF][DOI]
- **Citation:** Haoyi Zhang, Shizhao Sun, Yibo Lin, Runsheng Wang, Jiang Bian. "AnalogXpert: Automating Analog Topology Synthesis by Incorporating Circuit Design Expertise into Large Language Models." *ISEDA 2025*, pp. 772–777. DOI 10.1109/ISEDA65950.2025.11100627. arXiv:2412.19824.
- **Scope:** topology only.
- **Pipeline:**
  - Subcircuit-level SPICE generation from a subcircuit library (real-device netlists, e.g. `nch_mac`).
  - CoT: block selection, then block connection.
  - In-context learning with the most similar example.
  - A deterministic **rule-based proofreading checker** labels I/O/V terminal types, flags block-selection and block-connection errors, and sends revise messages until success or the iteration limit.
- **Benchmark:** **30 real tasks plus 2,000 synthetic tasks**. Correct topology in one trial is judged by the rule checker (synthetic) or by humans (real). **No simulation.**
- **LLM:** GPT-4o.
- **Results:** **40% (synthetic) / 23% (real)**, vs GPT-4o 3% / 3% and AnalogCoder 8% / 6%.
- **Position stated:** criticizes "ideal model-based generation or ambiguous design requirements."

#### Artisan — [DOI] for the citation; details [2nd] / UNVERIFIED
- **Citation:** Zihao Chen, Jiangli Huang, Yiting Liu, Fan Yang, Li Shang, Dian Zhou, Xuan Zeng. "Artisan: Automated Operational Amplifier Design via Domain-specific Large Language Model." *DAC 2024* (61st), pp. 1–6. DOI 10.1145/3649329.3655903. Not on arXiv; I did not read it.
- **According to citing papers (EEsizer, AaLLM, the agentic-EDA survey):**
  - A domain LLM (fine-tuned Llama2-7B) with a bidirectional netlist↔natural-language representation.
  - Tree-of-Thoughts plus CoT "cascading dialogue" for op-amp topology and parameter design.
  - gm/Id-based sizing.
  - Relies on manually annotated data.
- **Experimental scale:** UNVERIFIED.

#### Atelier — [DOI]; abstract read; experiments [2nd]
- **Citation:** Jinyi Shen, Zihao Chen, Ji Zhuang, Jiangli Huang, Fan Yang, Li Shang, Zhaori Bi, Changhao Yan, Dian Zhou, Xuan Zeng. "Atelier: An Automated Analog Circuit Design Framework via Multiple Large Language Model-Based Agents." *IEEE TCAD* 45(1):31–44, Jan 2026. DOI 10.1109/TCAD.2025.3573228. Published online May 2025. OpenAlex lists the first author as "Juanyan Shen", Crossref as "Jinyi Shen"; use Crossref.
- **Pipeline (abstract):**
  - General-purpose LLMs plus a compact, task-oriented knowledge base built from literature.
  - Agents in a **graph-of-thoughts** for circuit analysis, topology selection, topology modification, parameter tuning and design decision.
  - Self-reflection, backtracking and tool use.
  - Claims better success rate, design quality and runtime than black-box optimizers, general LLMs and LLM methods.
- **From citing papers:**
  - AaLLM: sizing is delegated to **CMA-ES**.
  - AnalogSeeker: the op-amp task is gain > 85 dB, GBW > 5 MHz, PM > 55°, power < 250 µW, with at most 4 iterations and HSPICE netlists.

#### AmpAgent — [PDF][arXiv]; venue not found
- **Citation:** Chengjie Liu, Weiyu Chen, Anlan Peng, Yuan Du, Li Du, Jun Yang. "AmpAgent: An LLM-based Multi-Agent System for Multi-stage Amplifier Schematic Design from Literature for Process and Performance Porting." arXiv:2409.14739, 2024.
- **Pipeline:**
  - Three agents: Literature Analysis (RAG plus custom prompts), Mathematics Reasoning (transfer function, poles and zeros, per-stage gm targets) and Device Sizing (iterative).
  - Built on LangChain with GPT-4-1106-preview at temperature 0.
  - Schematic images are converted to netlists **manually**.
- **Benchmark:** **7 multi-stage amplifier types** with different compensation schemes (e.g. NMCNR), 0.18 µm, Cadence Spectre.
- **Baselines:** ABC and TuRBO, at most 100 iterations.
- **Results:**
  - Performance 1.63–27.25× better than the original papers.
  - 1.32–4× fewer iterations, 1.19–2.99× less time, 1.03–6.79× higher success rate.
- **Limitations stated:** GPT-4 hallucinations cause failures. Future work: a domain LLM, automatic netlist extraction, gm/Id.

#### AnalogSAGE — [PDF][arXiv]
- **Citation:** Zining Wang, Jian Gao, Weimin Fu, Xiaolong Guo, Xuan Zhang. "AnalogSAGE: Self-evolving Analog Design Multi-Agents with Stratified Memory and Grounded Experience." arXiv:2512.22435, Dec 2025.
- **Scope:** topology plus sizing, spec-driven.
- **Pipeline:**
  - Three stages: topology selection and refinement, then parameter optimization by BO.
  - Four stratified memory layers: Introspective Optimization, Evolution Memory, Stage Context Fusion, and others.
  - A topology database of 50 labelled candidates.
  - **RAG over about 10,000 ISSCC papers (1955–2024).**
  - PySpice converted to ngspice netlists.
- **Benchmark:** **10 op-amp spec tasks** (power, gain, CMRR, PSRR, GBW, PM, PSRN) in 3 difficulty levels. **SKY130 + ngspice** using AnalogGym scripts. At most 3 reasoning iterations, matching AnalogCoder-Pro.
- **LLM:** Gemini-2.5-Flash, with text-embedding-3-large.
- **Results:**
  - **100% pass rate, 96% Pass@1.**
  - Baselines: AnalogCoder-Pro 10% / 2%; SPICEPilot 0% / 0%; "Artisan-style" re-implementation 70% pass.
  - About 4× smaller parameter search space.
- **PVT:** none (nominal only).
- **Repo:** <https://github.com/xz-group/AnalogSAGE>.

#### AaLLM — [PDF][arXiv] (closest competitor in framing)
- **Citation:** Mohammed Ayman Habib, Rylan Hart, Morteza Fayazi. "AaLLM: An End-to-End Analog Circuit Design Framework from Topology Generation to Sizing Using Large Language Models." arXiv:2608.13472, Aug 2026. The code link is `anonymous.4open.science`, so the paper is likely under double-blind review.
- **Pipeline:**
  - Automatic construction of a knowledge base from papers and textbooks.
  - **RAG topology selection** with Claude Haiku 4.5.
  - **Novel topology generation** with a fine-tuned FLAN-T5 Seq2Seq model and constrained decoding.
  - **Tri-agent sizing**: Designer, Critic and Evaluator (Claude Sonnet 4.6, at most 20 iterations). It uses **no external optimizer** and adds curriculum-based sizing.
- **Benchmark:**
  - **24 target-spec op-amp suite** (gain, UGBW, PM, Ibias; success = all four met) in **SKY130**.
  - Topology Pass@1 over 50 samples per task (5 seeds × 10).
  - Sizing: 12 tasks × 2 seeds.
  - Active filters: Sallen-Key LPF/HPF and MFB BPF.
  - A PTM 45 nm port to compare with AnaFlow.
- **Results:**
  - 100% structural and electrical validity on all 24 specs.
  - Miller OTA meets 12/12 specs (22/24 runs). The novel topology meets 11/12.
  - Novel-topology FoM is comparable, and up to 3× higher on some circuits.
  - **2 SPICE calls vs 9 for AnaFlow (4.5×), 40× less wall-clock.** The abstract claims 3–4.5× fewer SPICE calls than prior multi-agent pipelines.
  - Compared head-to-head with Atelier on 4 two-stage circuits with 200–4000 s budgets.
- **PVT / MC:** none.

#### SAFTAC — [PDF][arXiv]
- **Citation:** Junsheng Huang, Yifan Sun, Zhuoer Zhang, Ning Wei, Yening Liu, Michael Molter, Pavan Kumar Hanumolu, Elyse Rosenbaum, Bin Hu, Huan Zhang. "SAFTAC: Simulation-Augmented Fine-Tuning of Open-Source LLMs for Analog Circuit Design." *NeurIPS 2026* (per the arXiv comment). arXiv:2611.08543.
- **Dataset:** **8,626 spec-conditioned tasks over 10 circuit types, derived from 114 unique netlists.**
  - Each task has a description, labelled I/O ports, a loading condition, target specs, a testbench and a reference netlist.
  - Targets are made Pareto-feasible by BO sizing.
  - Testbenches were ported from Cadence to **ngspice**; loop gain is measured by series and parallel injection.
  - Device models are TSMC 0.18 µm-style (`tsmc18dn/dp`).
- **Method:** 3-stage SFT (teacher GPT-5.4), then **GRPO with simulation rewards**: topology check → BO sizing → simulation.
- **Model:** **Qwen3-8B.**
- **Evaluation:** 5 representative types; pass@1 over 8 rollouts at temperature 0.2.
- **Results:** single-pass **71.4%**; two-pass with feedback **78.2%**. That is +15.9 and +7.8 points over the best closed model (GPT-5.2, GPT-5.4, Claude-Opus-4.7). Active-mixer pass@1 rises from 1.6% to 41.4%.
- **Limitations stated:** only one revision pass; a single model; BO and SPICE cost of reinforcement fine-tuning.
- **PVT:** none.

#### PANDA — [DOI][arXiv]; skimmed
- **Citation:** Haoyi Zhang, Weijian Fan, Xiaohan Gao, Bingyang Liu, Runsheng Wang, Yibo Lin. "PANDA: An LLM-Enhanced Performance-Driven Analog Design Framework Bridging Design Intent and Layout Generation." *DAC 2026 (Special Research Session)*, pp. 1–5. DOI 10.1145/3770743.3807767. arXiv:2606.15052.
- **Pipeline:** intent → guided topology synthesis → substructure-aware sizing → constraint-driven layout.
- **Repo:** <https://github.com/PKU-IDEA/PANDA>.

#### OPERA — [PDF][arXiv]
- **Citation:** Vishal Saxena, Soumyajit Mandal. "OPERA: OPamp Design by an Expert-Taught Reasoning Agent, from Specifications to Layout." arXiv:2610.39395, submitted to ISCAS 2027.
- **Pipeline:** a Claude agent in a Linux sandbox. Opus 5.5 was used for teaching and skill development, Sonnet 5.5 for the loops. A designer teaches **gm/ID lookup-table sizing** and the gLayout framework, with designer-approved gates.
- **Scope:** **SKY130**, one shared constant-gm bias and **6 op-amps** (5T, folded-cascode, telescopic; Miller, folded-cascode and telescopic two-stage).
- **Specs:** f_un ≥ 50 MHz, PM ≥ 60°, SR ≥ 25 V/µs into 1 pF, gain 30–60 dB.
- **Results:** all layouts are DRC-clean and LVS-matched, and **extracted netlists meet every target at all 15 PVT corners**.
- **Repo:** <https://github.com/AMPICLab/AMPICBench>.

#### AMSnet-KG / AMSgen and AMSNet — [PDF][DOI]
- **AMSnet-KG citation:** Yichen Shi, Zhuofu Tao, YuHao Gao, Tianjia Zhou, Cheng Chang, Yaxin Wang, Bingyu Chen, Genhao Zhang, Alvin Liu, Zhiping Yu, Ting-Jung Lin, Lei He. "AMSnet-KG: A Netlist Dataset for LLM-based AMS Circuit Auto-design Using Knowledge Graph RAG." *ACM TODAES* 30(6):1–37, 2025. DOI 10.1145/3736166. arXiv:2411.13560.
- **AMSgen pipeline:** spec → high-level strategy → KG retrieval of components → topology assembly → **BO sizing** → feedback.
- **Setup:** SMIC 28 nm, Spectre, GPT-4. Case studies: op-amp and comparator.
- **AMSNet citation:** Z. Tao et al. "AMSNet: Netlist Dataset for AMS Circuits." *IEEE LAD 2024*, pp. 1–5. DOI 10.1109/LAD62341.2024.10691781. arXiv:2405.09045. A schematic-to-netlist dataset; **894 circuits** per AMSnet-KG.

#### SPICEPilot — [PDF][DOI]
- **Citation:** Deepak Vungarala, Sakila Alam, Arnob Ghosh, Shaahin Angizi. "SPICEPilot: Navigating SPICE Code Generation and Simulation with AI Guidance." *IEEE ICRC 2024*, pp. 1–6. DOI 10.1109/ICRC64395.2024.10937006. arXiv:2410.20553.
- **Content:** a PySpice dataset plus benchmark metrics for SPICE code generation.
- **Repo:** <https://github.com/ACADLab/SPICEPilot>.
- **Used as a baseline** by AnalogSAGE (0% on spec tasks) and AnalogAgent.

#### Other end-to-end and agentic entries (brief)
- **AnalogMaster** [arXiv:2604.20916; abstract read]: X. R. Qin et al. A multimodal LLM framework from circuit image → netlist → parameter search → layout. 15-circuit benchmark. GPT-5 Pass@1 92.9%, Pass@5 99.9%.
- **HRL-Topo** [DOI only]: P. Vijayaraghavan, L. Shi, E. Degan, V. Mukherjee, X. Zhang. "Special Research Session: HRL-Topo: Hierarchical Reinforcement Learning with LLMs for Analog Circuit Topology Synthesis." *DAC 2026*, pp. 1–5. DOI 10.1145/3770743.3807772.
- **AnAutomate** [DOI only]: J. Wang, K. Chen, M. Ahmadzadeh, G. Gielen. "Special Research Session: AnAutomate — Towards Full Spec-to-Layout Agentic LLM-aided AMS Design Automation." *DAC 2026*. DOI 10.1145/3770743.3807768.
- **Circuit-Agent** [DOI only]: T. Yang, B. Li, Y. Li, W. Mao, G. Han. *AICAS 2025*. DOI 10.1109/AICAS64808.2025.11173131.
- **CircuitSynth** [DOI only]: P. Vijayaraghavan, L. Shi, E. Degan, X. Zhang. *IEEE LAD 2024*. DOI 10.1109/LAD62341.2024.10691716.
- **LADAC** (C. Liu, Y. Liu, Y. Du, L. Du; TechRxiv 2024): cited by ADO-LLM, AaLLM and AnalogToBi. **UNVERIFIED** (not retrieved).
- **SPICEAssistant** / "Evaluating LLM-based Workflows for Switched-Mode Power Supply Design" [arXiv:2507.10639]: S. Nau, J. Krummenauer, A. Zimmermann. PCB-level SMPS design with LTSpice tools and RAG. Solve rate rises from 15% to 91% on 269 tasks (v2).
- **RFChipAgent** (arXiv:2610.10858) and **Analog-DB** (arXiv:2609.01286): titles found, not read.

### 3.2 LLM-assisted sizing of a fixed topology

#### ADO-LLM — [PDF][DOI]
- **Citation:** Yuxuan Yin, Yu Wang, Boxun Xu, Peng Li. "ADO-LLM: Analog Design Bayesian Optimization with In-Context Learning of Large Language Models." *ICCAD 2024*, pp. 1–9. DOI 10.1145/3676536.3676816. arXiv:2406.18770.
- **Pipeline:** a GP-BO proposer and an LLM agent (GPT-3.5-turbo with ICL) share one dataset. The LLM supplies 5 initial points, then 1 candidate per iteration.
- **Benchmark:** **2 circuits** (two-stage differential amplifier, hysteresis comparator). HSPICE, commercial 90 nm.
- **Metric:** FoM vs iterations; ablations on ICL demonstrations.
- **Limitations stated:** dependence on closed APIs; LLMs not domain-adapted; quality depends on few-shot examples.

#### LEDRO — [PDF][DOI]
- **Citation:** Dimple Vijay Kochar, Hanrui Wang, Anantha P. Chandrakasan, Xin Zhang. "LEDRO: LLM-Enhanced Design Space Reduction and Optimization for Analog Circuits." *IEEE ICLAD 2025*, pp. 141–148. DOI 10.1109/ICLAD65226.2025.00011. arXiv:2411.12930. Also a DAC 2025 work-in-progress poster.
- **Pipeline:** LLaMA3-70B (greedy decoding) iteratively shrinks the design space; TuRBO searches inside it. GPT-3.5 is also tested.
- **Benchmark:** **22 op-amps** (10 low-complexity, 12 high-complexity) × **4 FinFET nodes** (PTM-MG 7, 10, 14, 16 nm). Spectre.
- **Baselines:** an actor-critic RL method and pure TuRBO / BO-1200.
- **Results:** +13% FoM with 2.15× speed-up on low-complexity op-amps; +48% FoM with 1.7× on high-complexity.
- **Repo:** <https://github.com/dimplekochar/LEDRO>.

#### AnaFlow — [PDF][DOI]
- **Citation:** Mohsen Ahmadzadeh, Kaichang Chen, Georges Gielen. "(Invited Paper) AnaFlow: Agentic LLM-based Workflow for Reasoning-Driven Explainable and Sample-Efficient Analog Circuit Sizing." *ICCAD 2025*, pp. 1–7. DOI 10.1109/ICCAD66269.2025.11240818. arXiv:2511.03697.
- **Agents:**
  - Circuit Explainer and Initial Designer.
  - Specs Reviewer with a Reasoning Sizer, and DC Reviewer with a DC Sizer (reasoning-only phase).
  - Advisor Reviewer with an Equipped Sizer, which **may call an external optimizer** (RL-based AnaCraft or BO) when it detects stagnation.
  - Learns from the optimization history.
- **Circuits:** **2**: a two-stage Miller op-amp, and a differential folded-cascode with CMFB. **PTM/BSIM 45 nm + ngspice.**
- **LLMs:** Gemini 2.5 Pro/Flash, OpenAI o3, Claude Sonnet 4, Claude Opus 4, Grok 3.
- **Results:** with Gemini 2.5 Pro, the two-stage design meets all hard constraints within 10 iterations without the optimizer. The folded-cascode needs 1 optimizer call and fewer than 100 simulations in total.
- **Limitations stated:** large LLMs have long runtimes and high token cost; some models fail to produce long structured outputs for the larger circuit; some runs exceeded 2 hours.

#### EEsizer (+ NEWCAS predecessor) — [PDF][DOI]
- **Citation:** Chang Liu, Danial Chitnis. "EEsizer: LLM-Based AI Agent for Sizing of Analog and Mixed Signal Circuit." *IEEE TCAS-I* 73(6):3825–3834, Jun 2026. DOI 10.1109/TCSI.2025.3646359. arXiv:2509.25510.
- **Predecessor:** C. Liu, E. A. Olowe, D. Chitnis. "LLM-based AI Agent for Sizing of Analog and Mixed Signal Circuit." *NEWCAS 2025*, pp. 90–94. DOI 10.1109/NEWCAS64648.2025.11107079.
- **Pipeline:** task decomposition, then a closed loop with ngspice and custom analysis functions, using CoT. Success means all spec flags are true and no transistor is in sub-threshold (a proxy for robustness).
- **Benchmark:**
  - 8 LLMs benchmarked on **6 basic circuits**.
  - The top 3 (Gemini 2.0 Flash, GPT-4.1, o3) size a **20-transistor rail-to-rail CMOS op-amp** at **PTM 180, 130 and 90 nm**.
  - At most 20 iterations; 10 attempts.
- **Results:** o3 reached the target at 90 nm in 3 test groups.
- **Variation:** Gaussian W and Vth variation, 10 and then 50 samples. **"Not all performance metrics achieved a 100% pass rate."**
- **Limitations stated:**
  - No layout.
  - "A full Monte Carlo simulation with accurate device models … should also be used."
  - PTM lacks noise models.
  - Analysis functions are hand-written. The authors suggest LLM testbench generation as future work.

#### AutoSizer — [PDF][DOI: PMLR]
- **Citation:** Xi Yu, Dmitrii Torbunov, Soumyajit Mandal, Yihui Ren. "AutoSizer: Automatic Sizing of Analog and Mixed-Signal Circuits via Large Language Model (LLM) Agents." *ICML 2026*, PMLR 306:151161–151186. arXiv:2602.02849.
- **Pipeline:** reflective two-loop meta-optimization.
  - The inner loop does the sizing; the LLM picks and configures optimizers.
  - The outer loop analyses optimization dynamics and refines the search space (ranges, variable priorities).
- **Benchmark:** **AMS-SizingBench: 24 AMS circuits in SKY130** (Easy, Medium, Hard), ngspice.
- **Setup:** Gemini-2.5-Flash; **300-sample budget**; 3 trials.
- **Baselines:** GA, BO (GP-UCB), TuRBO, plus LEDRO, ADO-LLM and EEsizer re-implemented on the same LLM.
- **Metrics:** FoM, evaluations to best, time, success rate.
- **Results:** best overall, with the largest margin on Hard circuits. Ablation on 5 circuits: removing the Self-Reflection Loop "causes 80% success rate drop" and costs −39.4% FoM.
- **PVT:** none.
- **Repo:** <https://github.com/yuxi120407/AutoSizer>.

#### AgenticSizing — [PDF][arXiv]
- **Citation:** Yijia Hao, Pratibha Verma, Dongxu Guo, Cristian Sestito, Michael O'Boyle, Christos-Savvas Bouganis, Themis Prodromakis. "AgenticSizing: A Large Language Model-based Multi-Agent Framework for Analog Circuit Sizing." arXiv:2609.25873, Sep 2026.
- **Pipeline:** topology decomposition into functional blocks; lightweight knowledge extraction; a planner coordinates role-specialized sizer agents. Built on LangGraph with GPT-5.2 at temperature 0.5.
- **Benchmark:**
  - **8 circuits.** Four textbook circuits build the knowledge base; the evaluation set is a folded-cascode amplifier, a BGR, an LDO, and an **integrated LDO+BGR+FC with 55 transistors and 60 variables**.
  - Cadence Spectre; 5 repeats.
- **Results:** on the integrated LDO, **60% success with an average of 83 iterations, where classical optimizers found no feasible point.**
- **Gap evidence (its Table I):** prior LLM sizing benchmarks span **2–24 circuits, with at most 20 transistors**.
- **Repo:** <https://github.com/aprilaihub/agentic-analog-sizing>.

#### AnalogScout — [PDF][arXiv] (most relevant to PVT and simulation efficiency)
- **Citation:** Yichen Long, Keren Zhu. "AnalogScout: Simulation-Efficient PVT-Aware Analog Sizing with LLM Agents." arXiv:2610.37319, submitted to ISCAS 2027.
- **Pipeline:**
  - Phase-Explore: 60 agent runs of up to 30 steps on DeepSeek "flash"; reuses elite designs; local sizing with **analytic gm/Id**; full-PVT checks.
  - Phase-Localize, Phase-Restructure.
  - Phase-Refine: CMA-ES over matched device groups.
- **Sign-off criteria:** full PVT, plus saturation margin ≥ 50 mV at all corners, plus **TT mismatch Monte Carlo yield ≥ 95% (N=500)**, plus independent re-measurement.
- **Benchmark:** **3 SKY130 OTAs** (Miller, folded-cascode, NMC) at 1.8 V, **9 corners**, plus a GF180MCU Miller OTA. ngspice.
- **Budget:** **16k simulations per method**, where one simulation is one testbench at one corner.
- **Seeds:** development seeds 1–3, confirmation seeds 4–8. Holm-corrected hypothesis tests.
- **Baselines:** CMA-ES (also at 2× budget), BO, "LAS-style" and "ACP-style" LLM flows (LLM proposes, global optimizer refines).
- **Results:**
  - **−43.3% power vs CMA-ES at equal budget.** Reaches CMA-ES's final power after **7.0%** of the budget.
  - GF180: −59.6% power; 99.8% MC yield.
- **Limitations and honesty:**
  - Independent re-measurement fails 29 of 111 AnalogScout cases, mostly the 50 mV margin.
  - The folded-cascode design reaches only 91.4% MC yield; the NMC design misses settling at one corner by 0.15%.
  - Phase-Localize and Phase-Restructure add little.
- **Repo:** the AnalogScout code itself was not found.

#### Other sizing entries

**Venue-verified (ICCAD 2025, TCAD 2026, DAC 2025)**
- **ASTRA: Automatic Sizing of Transistors with Reasoning Agents** [DOI only]: W. W. Xing, B. Ou, Y. Zhang, Z. Liu, Y. Hu. *ICCAD 2025*. DOI 10.1109/ICCAD66269.2025.11240675. Not read.
- **AI Analog Circuit Design Agents: On Knowledge Extraction and Transfer with Knowledge Graphs** [DOI only]: K. Somayaji N.S., P. Li. *ICCAD 2025*. DOI 10.1109/ICCAD66269.2025.11240770. Not read.
- **LLM-USO** [abstract][DOI]: N. S. K. Somayaji, P. Li. *IEEE TCAD* 45(4):1907–1920, 2026. DOI 10.1109/TCAD.2025.3604643. arXiv:2502.02764. Structured-text knowledge about sub-structures is reused across circuits, combined with BO.
- **TopoSizing** [abstract][DOI]: Z. Wei, Z. Kong, Y. Wang, D. Z. Pan, X. Tang. *IEEE TCAD* 45(11):5136–5148, 2026. DOI 10.1109/TCAD.2026.3685525. arXiv:2509.14169. Graph hierarchy (device–module–stage), LLM hypothesis–verification–refinement, LLM-guided BO initialization and trust-region updates. 4 circuits; TT corner only.
- **GLOVA** (non-LLM, PVT/mismatch) [abstract][DOI]: D. Kim et al. *DAC 2025*. DOI 10.1109/DAC63849.2025.11132461. arXiv:2505.11208. Risk-sensitive RL with an ensemble critic that handles global and local mismatch under PVT.

**arXiv only**
- **EasySize** [abstract]: X. Wu, F. Hu, S. J. Babu, Y. Zhao, X. Guo. arXiv:2508.05113. Qwen3-8B fine-tuned on 350 nm data; "ease of attainability" loss; DE plus PSO. 5 op-amps at 180, 45 and 22 nm. Beats AutoCkt on 86.67% of tasks.
- **VLM-CAD** [abstract]: G. Pan et al. arXiv:2601.07315 (submitted to a NeurIPS'26 workshop). Image2Net plus ExTuRBO (explainable TuRBO); 12 sizing tasks.
- **White-Op** [abstract]: Z. Chen et al. arXiv:2601.21321. Behavioral-level op-amp design with symbolic reasoning and numeric solving; 9 op-amp topologies.
- **HeaRT** [abstract]: S. Poddar, C.-T. Ho, Z. Wei, W. Cao, H. Ren, D. Z. Pan. arXiv:2511.19669. Hierarchical reasoning tree over a 40-circuit benchmark of flattened netlists; ≥3× faster convergence under spec shifts.
- **Self-Calibrating LLM-derived equations** [abstract]: A. J. Bujana, A. I. Karsilayan. arXiv:2604.07387. 8 topology families (6–30 transistors), 6 nodes (32–180 nm), 5 trials, 5 LLMs, TuRBO-1 baseline.
- **SABLE** [abstract]: X. Li, C. H. Kim. arXiv:2607.03701. NDA-safe Virtuoso/Maestro/Spectre loop; 11 LLM checkpoints; 2 tasks with 3-corner PVT sign-off.
- **CASCoDe** [abstract]: Z. Wei, B. Liu, D. Z. Pan. arXiv:2611.11710. Sizing-pool plus layout tree search; 20 SKY130 amplifiers; DRC, LVS and RC-extracted checks.
- **TL-GRPO** [abstract]: P. Li et al. arXiv:2601.16480. Turn-level GRPO evaluated on analog sizing.
- **ORACLE** [abstract]: O. Brempong, M. A. Habib, V. Poddar, M. Fayazi. arXiv:2608.04999. Multi-objective RL with LLM-guided exploration.

### 3.3 Learned topology generators (non-agentic or fine-tuned)

#### CktGNN + Open Circuit Benchmark (OCB) — [PDF][arXiv]
- **Citation:** Zehao Dong, Weidong Cao, Muhan Zhang, Dacheng Tao, Yixin Chen, Xuan Zhang. "CktGNN: Circuit Graph Neural Network for Electronic Design Automation." *ICLR 2023*. arXiv:2308.16406.
- **Method:** a two-level nested GNN over a subgraph basis; graph VAE plus latent-space BO for joint topology and sizing.
- **OCB:** **10k distinct op-amps** with simulated specs (gain, PM, bandwidth, FoM) and a simulator interface.
- **Repo:** <https://github.com/zehao-dong/CktGNN>.

#### LaMAGIC — [PDF][DOI: PMLR]
- **Citation:** C.-C. Chang, Y. Shen, S. Fan, J. Li, S. Zhang, N. Cao, Y. Chen, X. Zhang. "LaMAGIC: Language-Model-based Topology Generation for Analog Integrated Circuits." *ICML 2024*, PMLR 235:6253–6262. arXiv:2407.18269.
- **Task:** power-converter topologies (3, 4 and 5 components; 6 components for transfer) plus duty cycle, given a voltage conversion ratio and efficiency.
- **Model and data:** Flan-T5-base SFT; about 120k training and 12k evaluation points simulated with ngspice.
- **Result:** **success rate up to 96% at tolerance 0.01.**

#### LaMAGIC2 — [PDF][DOI: PMLR]
- **Citation:** C.-C. Chang, W.-H. Lin, Y. Shen, Y. Chen, X. Zhang. "LaMAGIC2: Advanced Circuit Formulations for Language Model-Based Analog Topology Generation." *ICML 2025*, PMLR 267:7351–7360. arXiv:2506.10235.
- **Method:** SFCI formulation (identifier-based, O(|V|) tokens).
- **Results:** +34% success at tolerance 0.01; 10× lower MSE; up to 58.5% better transfer to 6-component circuits (76k-circuit set).
- **Repo:** <https://github.com/turtleben/LaMAGIC>.
- **Follow-up:** **EXPLORE** [abstract] (G. Zhou et al., MLCAD 2026, arXiv:2607.13416) adds simulator-guided MCTS at test time. On 6-component circuits at tolerance 0.01, success rises from 12% (one-shot) and 33% (sample-and-filter) to 65%.

#### AutoCircuit-RL — [PDF][DOI: PMLR]
- **Citation:** P. Vijayaraghavan, L. Shi, E. Degan, V. Mukherjee, X. Zhang. "AUTOCIRCUIT-RL: Reinforcement Learning-Driven LLM for Automated Circuit Topology Generation." *ICML 2025*, PMLR 267:61498–61512. arXiv:2506.03122.
- **Method:** instruction-tuning plus RL refinement with reward models for validity, efficiency and Vout, on 4–5-component power converters; ngspice validation.
- **Base models:** Llama-3-8B, MPT-7B, GPT-Neo-2.7B, StableLM-3B and others.
- **Results:** about 12% more valid circuits, about 14% better efficiency, about 38% fewer duplicates; more than 60% success with limited data.

#### AnalogGenie — [PDF][arXiv]
- **Citation:** Jian Gao, Weidong Cao, Junyi Yang, Xuan Zhang. "AnalogGenie: A Generative Engine for Automatic Discovery of Analog Circuit Topologies." *ICLR 2025*. arXiv:2503.00205.
- **Data and model:**
  - **3,350 topologies, 11 types** (op-amp, LDO, BGR, comparator, PLL, LNA, PA, mixer, VCO, power converter, switched-capacitor sampler); largest 54 devices.
  - Pin-level Eulerian sequence representation; 70× augmentation.
  - 11.8M-parameter decoder-only transformer.
  - Pretraining, then fine-tuning for FoM.
- **Sizing:** **genetic algorithm.**
- **Metrics:** validity (simulatable with default sizing), scalability, novelty, FoM.
- **Results:**
  - 93.2% valid after fine-tuning; about 100% novel; up to 56–64 devices.
  - Op-amp FoM 36.5 vs CktGNN 10.9 and AnalogCoder 1.7.
  - Power converter 3.3 vs LaMAGIC 2.2.
  - Bandgap 21.9.
- **Limitation stated:** sample efficiency of GA sizing.
- **Repo:** <https://github.com/xz-group/AnalogGenie>.
- **Follow-up:** **AnalogGenie-Lite** [DOI: PMLR]: J. Gao, W. Cao, X. Zhang. *ICML 2025*, PMLR 267:18277–18289. Linear device-pin representation and subgraph mining. Reports 5.15–71.11× scalability and +23.5–33.6% validity [2nd].

#### FALCON — [PDF][arXiv]
- **Citation:** A. Mehradfar, X. Zhao, Y. Huang, E. Ceyani, Y. Yang, S. Han, H. Aghasi, S. Avestimehr. "FALCON: An ML Framework for Fully Automated Layout-Constrained Analog Circuit Design." *NeurIPS 2025*. arXiv:2505.21923.
- **Not an LLM method.**
- **Data:** **1M Cadence-Spectre-simulated mm-wave circuits, 45 nm, 20 topologies** (LNA, mixer, PA, voltage amplifier, VCO × 4 each).
- **Method:** MLP topology classifier; edge-centric GNN forward model; gradient-based inverse design with a differentiable layout cost.
- **Results:** >99% topology accuracy; <10% prediction error; **78.5% success (Cadence-verified within 20% of target) on 9,500 test instances**; under 1 s per instance on CPU.
- **Repo:** <https://github.com/AsalMehradfar/FALCON>.

#### Others (brief)
- **AnalogToBi** [abstract]: S. Kim, M. Kim, Y. Lee, Y. Kim. arXiv:2603.08720. Bipartite graph plus grammar-guided decoding plus circuit-type conditioning; high validity and novelty without human-in-the-loop training. Repo: Seungmin0825/AnalogToBi.
- **CircuitFormer** [abstract]: M. T. Islam, S. K. Saha, F. Farahmandi, M. Tehranipoor. arXiv:2605.05773. **31,341 netlist–natural-language pairs**; a circuit tokenizer (CKT) that mines frequent subcircuits.
- **Multi-Agent Generative Synthesis for Analog/RF Circuit** [DOI only]: S. Wang, Q. Li, H. He, J. Gao, Z. Wang, Y. Sun, X. Zhang, T. Chi, W. Cao. *ICCAD 2025*, invited. DOI 10.1109/ICCAD66269.2025.11240792.
- **AnalogFed** [DOI only]: Q. Li, S. Hong, T. Lan, W. Cao. *ICLAD 2026*, pp. 217–222. DOI 10.1109/ICLAD71857.2026.00039. Federated generative topology discovery.

### 3.4 Benchmarks, datasets and evaluation studies

#### AnalogGym — [PDF][DOI]
- **Citation:** Jintao Li, Haochang Zhi, Ruiyu Lyu, Wangzhen Li, Zhaori Bi, Keren Zhu, Yanhan Zeng, Weiwei Shan, Changhao Yan, Fan Yang, Yun Li, Xuan Zeng. "AnalogGym: An Open and Practical Testing Suite for Analog Circuit Synthesis." *ICCAD 2024 (invited)*, pp. 1–9. DOI 10.1145/3676536.3697117. arXiv:2409.08534.
- **Content:** **30 topologies in 5 categories** (sensing front ends, voltage references, LDOs, amplifiers, PLLs) with complete bias circuits and testbenches (DC, AC, PZ, transient).
- **Simulators and PDKs:**
  - **ngspice + SKY130** for amplifiers and LDOs.
  - Spectre or HSPICE with commercial 180, 130 and 22 nm for the others.
  - **PVT corner definitions** (SS, FF, SF, FS, TT × voltage × temperature).
- **Algorithms evaluated:** GCN-RL, WEIBO, cVTS, SMEA, MTEA; worst-case-PVT tables.
- **Future work stated:** topology search, layout.
- **Repo:** <https://github.com/CODA-Team/AnalogGym>.
- **Used by:** AnalogSAGE's ngspice/SKY130 scripts are adapted from AnalogGym.

#### Long-Horizon Analog Design Bench — [PDF][arXiv]
- **Citation:** "Analog Design Bench Team" (correspondence: Zhishuai Zhang, ETH Zürich). "Long-Horizon Analog Design Bench: Benchmarking Agents on Hours-Long Analog and Mixed-Signal Circuit Design Tasks." arXiv:2609.33356, Sep 2026.
- **Content:** **50 transistor-level tasks contributed by 17 chip designers.** Open-source SKY130 plus ngspice; an **isolated verifier** runs specification-based electrical tests. Example task: "across 30 PVT conditions and 20 mismatch samples".
- **Scale of evaluation:** **15 agent configurations × 2,250 two-hour attempts.**
- **Results:**
  - **Full-spec pass 8.0–78.0%.** The survey records a range of closed-model results. Those historical model names are literature context only and are excluded from the GPT-6.1-sol experiment chain.
  - Most failures pass legality checks but **fail electrical acceptance**.
  - A task-matched reference topology adds +18.7 points for DeepSeek V4 Pro. General skill documents help little.
- **Repo:** <https://github.com/Arcadia-1/analog-design-bench>.
- **Relevance:** the strongest external evidence that **electrical spec closure, not netlist syntax, is the bottleneck.**

#### Other benchmarks and datasets (brief)
- **AnalogPortBench** [abstract]: S. Rajabi, A. Moussa, V. Saxena, C. Yang, S. Patnaik. arXiv:2610.33088. **54 porting tasks** (10 circuits from 0.18 µm to SKY130), including infeasible ones. References verified at **5 process corners**. 6 frontier LLMs × 2 reasoning levels, with and without simulation feedback. Models "rarely redesign headroom-sensitive" circuits.
- **LOADBench** [abstract]: M. Leibl et al. *MLCAD 2026*. DOI 10.1145/3831599.3840321. arXiv:2610.21591. **More than 100 op-amp topologies in SKY130** with ngspice testbenches; NSGA-II data (about 10³ Pareto and 10⁶ intermediate points per topology); 6 tasks.
- **Masala-CHAI** [PDF]: J. Bhandari, V. Bhat, Y. He, H. Rahmani, S. Garg, R. Karri. arXiv:2411.14299. **7,500 SPICE netlists from 10 textbooks**, extracted from schematic images. GPT-4o fine-tuned on it gives AnalogCoder **+46% Pass@1**. Venue not found.
- **AnalogSeeker** (v3 retitled "Dataset Construction for Training LLM to Learn Analog Circuit Knowledge") [PDF]: Z. Chen, J. Zhuang, J. Shen, et al. (Fudan). arXiv:2508.10409.
  - Data: 7.26M tokens for continual pre-training and 112.65M tokens of question-thinking-solution-answer quadruples for SFT.
  - Qwen2.5-32B-Instruct with SFT plus KL regularization: **84.59% on AMSBench-TQA (+15.67 points)**.
  - Tested in Atelier's op-amp task.
  - Header in ACM TODAES format, but no published DOI was found.
- **AMSbench** [abstract]: Y. Shi et al. arXiv:2505.24138. About 8,000 questions on multimodal LLM schematic perception, analysis and design.
- **MMCircuitEval** [abstract]: C. Zhao et al. arXiv:2507.19525, "to appear in ICCAD 2025". 3,614 QA pairs.
- **CIRCUIT** [arXiv]: L. Skelic et al. arXiv:2502.07980. Circuit reasoning QA.
- **Image2Net** [abstract]: H. Xu et al. arXiv:2508.13157. Schematic image → netlist.
- **AnalogTester** [DOI]: W. Chen et al. *ISEDA 2025*, pp. 201–207. DOI 10.1109/ISEDA65950.2025.11100397. LLM testbench generation.
- **Schemato** [DOI]: R. Matsuo et al. *MLCAD 2025*. DOI 10.1109/MLCAD65511.2025.11189059. Netlist → schematic.
- **AnalogVerifier** [PMLR listing]: Y. Liu, M. Wang, P. Xu, R. Fu, B. Yu, T.-Y. Ho. *ICML 2026*, PMLR 306:78868–78924. Neuro-symbolic analog verification; not read.
- **"The Era of Vibe Tapeout"** [abstract]: K. Yoshioka. arXiv:2610.15240.
  - A cloud agent designed an 11-bit SAR ADC on SKY130 through PEX sign-off.
  - Local LLMs were tested on a commercial 65 nm PDK with 6 tasks.
  - Key finding: **"agents sometimes reported false passes, and verification independent of the design agent was essential."**

### 3.5 Classical (non-LLM) RL and BO sizing baselines

#### AutoCkt — [PDF][DOI]
- **Citation:** K. Settaluri, A. Haj-Ali, Q. Huang, K. Hakhamaneshi, B. Nikolić. "AutoCkt: Deep Reinforcement Learning of Analog Circuit Designs." *DATE 2020*, pp. 490–495. DOI 10.23919/DATE48585.2020.9116200. arXiv:2001.01808.
- **Method:** PPO trained on sparsely sampled target specs; generalizes to new specs.
- **Results:** **meets 96.3% of tested design goals** in schematic simulation; about **40× faster than a genetic algorithm**. Spectre and BAG in 16 nm FinFET, including post-layout.
- **Repo:** <https://github.com/ksettaluri6/AutoCkt>.

#### GCN-RL Circuit Designer — [PDF][DOI]
- **Citation:** H. Wang, K. Wang, J. Yang, L. Shen, N. Sun, H.-S. Lee, S. Han. "GCN-RL Circuit Designer: Transferable Transistor Sizing with Graph Neural Networks and Reinforcement Learning." *DAC 2020*, pp. 1–6. DOI 10.1109/DAC18072.2020.9218757. arXiv:2005.00406.
- **Method:** GCN plus DDPG.
- **Benchmark:** 4 circuits (two- and three-stage transimpedance amplifiers, LDO, two-stage voltage amplifier); transfer across **5 technology nodes** and 2 topologies.
- **Results:** beats BO, evolution strategies, random search and human experts on FoM.

#### ICCAD 2026 analog-sizing papers (non-LLM)
Titles are from program v19 (<https://confcats-event-sessions.s3.us-east-1.amazonaws.com/iccad26/uploads/ICCAD_2026_Program_v19.pdf>). I did not read the papers.
- **MetaSizing**: meta-RL for generalizable sizing (Wang, …, Cao).
- **Many-objective analog synthesis via learning-augmented hypervolume approximation** (Zhao, Yang, Guo, Bi; Fudan).
- **Hierarchical adaptive BO for mixed-variable analog design** (Tu et al.).
- **ATLAS**: TDA-guided transistor sizing.
- **AnalogRetriever**: cross-modal analog IP retrieval (Wang, Li, **Lai**, Wang, Lu); arXiv:2604.23195.

### 3.6 Requested items that are out of scope, misattributed or not found
- **CROP** [PDF][arXiv] (J. Pan et al., ICCAD 2025, arXiv:2507.02128): **not analog.** It is LLM+RAG tuning of **digital VLSI** flow parameters (Synopsys flow, RTLRewriter benchmark, 7 nm and 5 nm industrial cores; 9.9% power reduction). Cite it only as RAG-guided parameter search.
- **CircuitMind** (arXiv:2504.14625, "Towards Optimal Circuit Generation: Multi-Agent Collaboration Meets Collective Intelligence"): **digital gate-level** circuit generation (TC-Bench, 28 circuits). Not analog.
- **"Spec2Netlist"**: **not found** in arXiv or web search. Do not cite.
- **ADO-LLM venue:** confirmed **ICCAD 2024**.
- **AnalogGym venue:** confirmed **ICCAD 2024 (invited)**.
- **AnalogXpert venue:** **ISEDA 2025**, not DAC/ICCAD.

---

## 4. Experimental-scale reference (targets to match or exceed)

| Dimension | Strongest prior setting | Source |
|---|---|---|
| Functional topology tasks | 30 tasks (Level-1 models), Pass@1/5, n=30 trials, 5 repeats | AnalogAgent; AnalogCoder-Pro (28 tasks, n=30) |
| Spec-driven end-to-end (T+S) tasks | 24 op-amp target specs (SKY130), 12 sized × 2 seeds; 10 op-amp spec tasks (SKY130) | AaLLM; AnalogSAGE |
| Spec-conditioned training data | 8,626 tasks / 10 types / 114 netlists | SAFTAC |
| Sizing benchmark breadth | 24 SKY130 circuits, 300-sample budget, 3 trials, 6 baselines | AutoSizer (ICML'26) |
| Sizing circuit size | 55 transistors / 60 variables, 5 repeats | AgenticSizing |
| PVT rigor (LLM sizing) | 9 corners + mismatch MC N=500 (≥95% yield), 16k-sim budget, 5 confirmation seeds, Holm-corrected tests | AnalogScout |
| PVT rigor (post-layout) | 15 PVT corners on PEX netlists, 6 op-amps | OPERA |
| Agentic benchmark scale | 50 tasks × 15 configurations × 2,250 two-hour attempts; some tasks with 30 PVT conditions + 20 MC | Long-Horizon Analog Design Bench |
| Topology dataset scale | 3,350 real topologies (11 types); 31,341 netlist–NL pairs; 1M simulated RF circuits | AnalogGenie; CircuitFormer; FALCON |
| Baseline set (sizing) | GA, BO, TuRBO, CMA-ES + LEDRO, ADO-LLM, EEsizer, LAS-style and ACP-style | AutoSizer; AnalogScout |
| Baseline set (T+S) | AnalogCoder-Pro, SPICEPilot, Artisan-style, Atelier, AnaFlow | AnalogSAGE; AaLLM |
| LLM sweep | Up to 40+ models; typical 4–8 including GPT-5-class, Claude, Gemini, open 8B | AnalogCoder; EEsizer; AnalogAgent |
| Efficiency metrics | #SPICE calls (2 vs 9), wall-clock (40×), time-to-first-success (1.3 min), tokens-to-success (about 32K) | AaLLM; AnalogAgent |

---

## 5. Gap analysis

### Table G1: verification rigor, from a keyword scan of the full texts

Method: counted "PVT", "corner", "Monte Carlo" and "mismatch" in each PDF's text, then inspected every hit. Hits that only appear in a reference title are counted as 0.

| Work | Uses PVT corners in its evaluation? | Monte Carlo / mismatch in its evaluation? |
|---|---|---|
| AnalogCoder, AnalogCoder-Pro, AnalogAgent, MenTeR | No (Level-1 or BPTM, TT) | No |
| AnalogSAGE, AaLLM, SAFTAC | No (TT) | No |
| AnalogXpert, Masala-CHAI, SPICEPilot | No simulation-based specs | No |
| ADO-LLM, LEDRO, AnaFlow, AutoSizer, AgenticSizing, TopoSizing, LLM-USO | No ("PVT" appears only in cited titles) | No |
| EEsizer | No | Post hoc Gaussian W/Vth, 10–50 samples; not every metric passes |
| SABLE | 3 corners, 2 tasks | No |
| AnalogScout | 9 corners, 3–4 OTAs | TT mismatch MC, N=500 |
| OPERA | 15 corners (post-layout), 6 op-amps | No |
| AnalogPortBench | References checked at 5 corners | No |
| Long-Horizon Bench | Some tasks up to 30 PVT conditions | Some tasks with 20 mismatch samples |

### Gap 1: no robust (PVT/MC), quantitative, multi-spec satisfaction in a system that also generates the topology

**Evidence**
- Every system that does both topology and sizing (AnalogCoder-Pro, AnalogSAGE, AaLLM, SAFTAC, AMSgen, Atelier) verifies only at nominal conditions (Table G1).
- AnalogCoder-Pro optimizes a scalar FoM, not constraint satisfaction.
- The only PVT/MC-verified LLM works size a **given** topology (AnalogScout) or are designer-taught case studies (OPERA, 6 op-amps).
- EEsizer states the gap directly: "a full Monte Carlo simulation with accurate device models … should also be used."
- Long-Horizon Bench shows that frontier agents fail mainly at "electrical acceptance."
- AnalogScout shows that even PVT-aware loops pass independent re-measurement unreliably: 29 of 111 cases fail. The folded-cascode design reaches only 91.4% MC yield.

**Opportunity:** report spec-satisfaction rate at TT, at all corners, and as MC yield, as separate tiers, on a real PDK. Use an independent verifier, as Long-Horizon Bench and Vibe-Tapeout recommend.

### Gap 2: evaluation realism and benchmark scale for end-to-end, spec-driven design

**Evidence**
- The most-cited LLM topology benchmarks (AnalogCoder 24 tasks, AnalogAgent 30, MenTeR) use Level-1 models (kp=100 µA/V², Vt=0.5 V) and functional checks.
- AnalogXpert uses no simulation at all.
- Spec-driven end-to-end benchmarks are small and op-amp-only: AnalogSAGE has 10 tasks; AaLLM has 24 spec targets over essentially one circuit family.
- Prior LLM sizing breadth is "2–24 circuits, at most 20 transistors" (AgenticSizing, Table I).
- Larger benchmarks cover a single stage only:
  - AnalogGym (30 topologies, sizing only; topology search is "future work").
  - AMS-SizingBench (24 circuits, sizing only).
  - LOADBench (more than 100 op-amps, ML tasks).
- SAFTAC's 8,626 tasks come from just 114 netlists, use TSMC 180 nm-style models, and are evaluated on 5 types.

**Opportunity:** a benchmark of more than 50 spec-driven tasks across at least 6 circuit families (OTA, two-stage, folded-cascode, LDO, BGR, comparator and so on). Each task should have multi-spec thresholds and **PVT/MC tiers** on SKY130, with infeasible-spec controls as in AnalogPortBench. Evaluation would use pass@k plus a simulation budget.

### Gap 3: simulation efficiency and fair accounting

**Evidence**
- Budgets are reported inconsistently:
  - AnalogCoder-Pro: 1000 BO trials per run, 30 runs.
  - AutoSizer: 300 samples.
  - AnalogScout: 16k corner-simulations.
  - AaLLM: "SPICE calls" (2 vs 9).
  - AnaFlow: fewer than 100 simulations.
- Only AnalogScout counts **corner × testbench** simulations and compares at equal budget with statistical tests.
- LLM token or dollar cost is rarely reported. AnalogAgent reports tokens-to-success; AnaFlow notes runtime and cost but gives no consistent cost metric.
- Simulator-call accounting under PVT, where cost scales with corners × iterations, is missing for every topology+sizing system.

**Opportunity:**
- Report simulations-to-first-feasible (TT and all-corner), LLM tokens and USD, and wall-clock time.
- Compare at matched budgets against CMA-ES, BO and TuRBO, and against re-implemented LLM flows on the same LLM, as AutoSizer does.

### Gap 4: actionable failure diagnosis and design-intent representations

**Evidence**
- Feedback in AnalogCoder and AnalogCoder-Pro is error text, operating-point and DC checks, or waveform images.
- AnaFlow uses spec deviation and DC reviewers.
- AaLLM uses Designer/Critic/Evaluator arbitration.
- None attributes a spec violation to specific devices or poles through sensitivities or Vds−Vdsat margins and then maps it to a parameter change.
- gm/Id appears only in AnalogScout (local analytic sizing), OPERA (taught), Artisan [2nd] and White-Op (behavioral level).
- EEsizer's success criterion uses "no sub-threshold devices" as a stand-in for robustness.
- AnalogCoder-Pro needs a dedicated input-bias search because LLM-set biases are fragile.

**Opportunity:** gm/Id design-intent programs, so that sizing is the choice of (gm/Id, L, I) instead of raw W/L, combined with causal diagnosis that uses operating-point margins and pole/zero sensitivities. Measure diagnosis accuracy directly through a fault-injection study.

### Gap 5 (secondary): reproducibility and statistics
- Many results rest on 1–3 seeds (AutoSizer 3 trials; AaLLM 2 seeds), on reimplemented baselines, or on baseline numbers copied from the original papers (AnalogCoder-Pro takes AnalogGenie and CktGNN FoMs from the papers).
- Only AnalogScout uses pre-registered development and confirmation seeds and Holm-corrected tests.
- Several 2026 works have no public code (AnalogScout, AaLLM is anonymous, SAFTAC).

**Opportunity:** release the benchmark and harness; use at least 5 seeds with confidence intervals.

**Not gaps (avoid overclaiming)**
- Layout co-design is being covered by PANDA, CASCoDe, OPERA, AnalogMaster and AnAutomate. The project's non-goals exclude layout anyway.
- Fine-tuning (SAFTAC, EasySize, AnalogSeeker, Artisan) is also covered.
- Topology novelty is covered by AnalogGenie, AnalogToBi, AaLLM's Seq2Seq and EXPLORE.

---

## 6. BibTeX

Only entries whose metadata I verified (Crossref, PMLR, arXiv API or DOI) are included. Fields come from those sources. Entries marked `UNVERIFIED` in `note` have unconfirmed venue or details.

```bibtex
@inproceedings{lai2025analogcoder,
  author    = {Yao Lai and Sungyoung Lee and Guojin Chen and Souradip Poddar and Mengkang Hu and David Z. Pan and Ping Luo},
  title     = {{AnalogCoder}: Analog Circuit Design via Training-Free Code Generation},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume    = {39},
  number    = {1},
  pages     = {379--387},
  year      = {2025},
  doi       = {10.1609/aaai.v39i1.32016},
  eprint    = {2405.14918},
  archivePrefix = {arXiv}
}

@article{lai2026analogcoderpro,
  author  = {Yao Lai and Souradip Poddar and Sungyoung Lee and Guojin Chen and Mengkang Hu and Bei Yu and Ping Luo and David Z. Pan},
  title   = {{AnalogCoder-Pro}: Unifying Analog Circuit Generation and Optimization via Multimodal {LLMs}},
  journal = {IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems},
  volume  = {45},
  number  = {11},
  pages   = {5149--5162},
  year    = {2026},
  doi     = {10.1109/TCAD.2026.3673493},
  eprint  = {2508.02518},
  archivePrefix = {arXiv}
}

@misc{bao2026analogagent,
  author = {Zhixuan Bao and Zhuoyi Lin and Jiageng Wang and Jinhai Hu and Yuan Gao and Yaoxin Wu and Xiaoli Li and Xun Xu},
  title  = {{AnalogAgent}: Self-Improving Analog Circuit Design Automation with {LLM} Agents},
  year   = {2026},
  eprint = {2603.23910},
  archivePrefix = {arXiv}
}

@inproceedings{chen2025menter,
  author    = {Pin-Han Chen and Yu-Sheng Lin and Wei-Cheng Lee and Tin-Yu Leu and Po-Hsiang Hsu and Anjana Dissanayake and Sungjin Oh and Chinq-Shiun Chiu},
  title     = {{MenTeR}: A fully-automated Multi-agenT workflow for end-to-end {RF/Analog} Circuits Netlist Design},
  booktitle = {2025 IEEE International Conference on LLM-Aided Design (ICLAD)},
  pages     = {124--132},
  year      = {2025},
  doi       = {10.1109/ICLAD65226.2025.00015}
}

@inproceedings{zhang2025analogxpert,
  author    = {Haoyi Zhang and Shizhao Sun and Yibo Lin and Runsheng Wang and Jiang Bian},
  title     = {{AnalogXpert}: Automating Analog Topology Synthesis by Incorporating Circuit Design Expertise into Large Language Models},
  booktitle = {2025 International Symposium of Electronics Design Automation (ISEDA)},
  pages     = {772--777},
  year      = {2025},
  doi       = {10.1109/ISEDA65950.2025.11100627}
}

@inproceedings{chen2024artisan,
  author    = {Zihao Chen and Jiangli Huang and Yiting Liu and Fan Yang and Li Shang and Dian Zhou and Xuan Zeng},
  title     = {Artisan: Automated Operational Amplifier Design via Domain-specific Large Language Model},
  booktitle = {Proceedings of the 61st ACM/IEEE Design Automation Conference (DAC)},
  pages     = {1--6},
  year      = {2024},
  doi       = {10.1145/3649329.3655903},
  note      = {Citation verified via Crossref; full text not read}
}

@article{shen2026atelier,
  author  = {Jinyi Shen and Zihao Chen and Ji Zhuang and Jiangli Huang and Fan Yang and Li Shang and Zhaori Bi and Changhao Yan and Dian Zhou and Xuan Zeng},
  title   = {Atelier: An Automated Analog Circuit Design Framework via Multiple Large Language Model-Based Agents},
  journal = {IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems},
  volume  = {45},
  number  = {1},
  pages   = {31--44},
  year    = {2026},
  doi     = {10.1109/TCAD.2025.3573228}
}

@misc{liu2024ampagent,
  author = {Chengjie Liu and Weiyu Chen and Anlan Peng and Yuan Du and Li Du and Jun Yang},
  title  = {{AmpAgent}: An {LLM}-based Multi-Agent System for Multi-stage Amplifier Schematic Design from Literature for Process and Performance Porting},
  year   = {2024},
  eprint = {2409.14739},
  archivePrefix = {arXiv},
  note   = {Peer-reviewed venue UNVERIFIED}
}

@misc{wang2025analogsage,
  author = {Zining Wang and Jian Gao and Weimin Fu and Xiaolong Guo and Xuan Zhang},
  title  = {{AnalogSAGE}: Self-evolving Analog Design Multi-Agents with Stratified Memory and Grounded Experience},
  year   = {2025},
  eprint = {2512.22435},
  archivePrefix = {arXiv}
}

@misc{habib2026aallm,
  author = {Mohammed Ayman Habib and Rylan Hart and Morteza Fayazi},
  title  = {{AaLLM}: An End-to-End Analog Circuit Design Framework from Topology Generation to Sizing Using Large Language Models},
  year   = {2026},
  eprint = {2608.13472},
  archivePrefix = {arXiv}
}

@inproceedings{huang2026saftac,
  author    = {Junsheng Huang and Yifan Sun and Zhuoer Zhang and Ning Wei and Yening Liu and Michael Molter and Pavan Kumar Hanumolu and Elyse Rosenbaum and Bin Hu and Huan Zhang},
  title     = {{SAFTAC}: Simulation-Augmented Fine-Tuning of Open-Source {LLMs} for Analog Circuit Design},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2026},
  eprint    = {2611.08543},
  archivePrefix = {arXiv},
  note      = {Venue per arXiv comment ("Accepted to NeurIPS 2026"); proceedings pages not yet available}
}

@inproceedings{zhang2026panda,
  author    = {Haoyi Zhang and Weijian Fan and Xiaohan Gao and Bingyang Liu and Runsheng Wang and Yibo Lin},
  title     = {Special Research Session: {PANDA}: An {LLM}-Enhanced Performance-Driven Analog Design Framework Bridging Design Intent and Layout Generation},
  booktitle = {Proceedings of the 63rd ACM/IEEE Design Automation Conference (DAC)},
  pages     = {1--5},
  year      = {2026},
  doi       = {10.1145/3770743.3807767}
}

@inproceedings{vijayaraghavan2026hrltopo,
  author    = {Prashanth Vijayaraghavan and Luyao Shi and Ehsan Degan and Vandana Mukherjee and Xin Zhang},
  title     = {Special Research Session: {HRL-Topo}: Hierarchical Reinforcement Learning with Large Language Models for Analog Circuit Topology Synthesis},
  booktitle = {Proceedings of the 63rd ACM/IEEE Design Automation Conference (DAC)},
  pages     = {1--5},
  year      = {2026},
  doi       = {10.1145/3770743.3807772}
}

@inproceedings{wang2026anautomate,
  author    = {Jiaqi Wang and Kaichang Chen and Mohsen Ahmadzadeh and Georges G. E. Gielen},
  title     = {Special Research Session: {AnAutomate} -- Towards Full Spec-to-Layout Agentic {LLM}-aided Analog/Mixed-Signal Design Automation},
  booktitle = {Proceedings of the 63rd ACM/IEEE Design Automation Conference (DAC)},
  pages     = {1--5},
  year      = {2026},
  doi       = {10.1145/3770743.3807768}
}

@misc{saxena2026opera,
  author = {Vishal Saxena and Soumyajit Mandal},
  title  = {{OPERA}: {OPamp} Design by an Expert-Taught Reasoning Agent, from Specifications to Layout},
  year   = {2026},
  eprint = {2610.39395},
  archivePrefix = {arXiv}
}

@article{shi2025amsnetkg,
  author  = {Yichen Shi and Zhuofu Tao and YuHao Gao and Tianjia Zhou and Cheng Chang and Yaxin Wang and Bingyu Chen and Genhao Zhang and Alvin Liu and Zhiping Yu and Ting-Jung Lin and Lei He},
  title   = {{AMSnet-KG}: A Netlist Dataset for {LLM}-based {AMS} Circuit Auto-design Using Knowledge Graph {RAG}},
  journal = {ACM Transactions on Design Automation of Electronic Systems},
  volume  = {30},
  number  = {6},
  pages   = {1--37},
  year    = {2025},
  doi     = {10.1145/3736166}
}

@inproceedings{tao2024amsnet,
  author    = {Zhuofu Tao and Yichen Shi and Yiru Huo and Rui Ye and Zonghang Li and Li Huang and Chen Wu and Na Bai and Zhiping Yu and Ting-Jung Lin and Lei He},
  title     = {{AMSNet}: Netlist Dataset for {AMS} Circuits},
  booktitle = {2024 IEEE LLM Aided Design Workshop (LAD)},
  pages     = {1--5},
  year      = {2024},
  doi       = {10.1109/LAD62341.2024.10691781}
}

@inproceedings{vungarala2024spicepilot,
  author    = {Deepak Vungarala and Sakila Alam and Arnob Ghosh and Shaahin Angizi},
  title     = {{SPICEPilot}: Navigating {SPICE} Code Generation and Simulation with {AI} Guidance},
  booktitle = {2024 IEEE International Conference on Rebooting Computing (ICRC)},
  pages     = {1--6},
  year      = {2024},
  doi       = {10.1109/ICRC64395.2024.10937006}
}

@inproceedings{yin2024adollm,
  author    = {Yuxuan Yin and Yu Wang and Boxun Xu and Peng Li},
  title     = {{ADO-LLM}: Analog Design Bayesian Optimization with In-Context Learning of Large Language Models},
  booktitle = {Proceedings of the 43rd IEEE/ACM International Conference on Computer-Aided Design (ICCAD)},
  pages     = {1--9},
  year      = {2024},
  doi       = {10.1145/3676536.3676816}
}

@inproceedings{kochar2025ledro,
  author    = {Dimple Vijay Kochar and Hanrui Wang and Anantha P. Chandrakasan and Xin Zhang},
  title     = {{LEDRO}: {LLM}-Enhanced Design Space Reduction and Optimization for Analog Circuits},
  booktitle = {2025 IEEE International Conference on LLM-Aided Design (ICLAD)},
  pages     = {141--148},
  year      = {2025},
  doi       = {10.1109/ICLAD65226.2025.00011}
}

@inproceedings{ahmadzadeh2025anaflow,
  author    = {Mohsen Ahmadzadeh and Kaichang Chen and Georges Gielen},
  title     = {(Invited Paper) {AnaFlow}: Agentic {LLM}-based Workflow for Reasoning-Driven Explainable and Sample-Efficient Analog Circuit Sizing},
  booktitle = {2025 IEEE/ACM International Conference On Computer Aided Design (ICCAD)},
  pages     = {1--7},
  year      = {2025},
  doi       = {10.1109/ICCAD66269.2025.11240818}
}

@inproceedings{xing2025astra,
  author    = {Wei W. Xing and Baowen Ou and Yuxuan Zhang and Zhuohua Liu and Yuanqi Hu},
  title     = {{ASTRA}: Automatic Sizing of Transistors with Reasoning Agents},
  booktitle = {2025 IEEE/ACM International Conference On Computer Aided Design (ICCAD)},
  pages     = {1--9},
  year      = {2025},
  doi       = {10.1109/ICCAD66269.2025.11240675},
  note      = {Citation verified via Crossref; full text not read}
}

@inproceedings{somayaji2025kgagents,
  author    = {Karthik Somayaji N.S and Peng Li},
  title     = {{AI} Analog Circuit Design Agents: On Knowledge Extraction and Transfer with Knowledge Graphs},
  booktitle = {2025 IEEE/ACM International Conference On Computer Aided Design (ICCAD)},
  pages     = {1--9},
  year      = {2025},
  doi       = {10.1109/ICCAD66269.2025.11240770},
  note      = {Citation verified via Crossref; full text not read}
}

@inproceedings{wang2025multiagentgen,
  author    = {Shikai Wang and Qiufeng Li and Houbo He and Jian Gao and Zining Wang and Yu Sun and Xuan Zhang and Taiyun Chi and Weidong Cao},
  title     = {Invited Paper: Multi-Agent Generative Synthesis for Analog/{RF} Circuit: from Scalable Topology Generation to Efficient Inverse Design},
  booktitle = {2025 IEEE/ACM International Conference On Computer Aided Design (ICCAD)},
  pages     = {1--9},
  year      = {2025},
  doi       = {10.1109/ICCAD66269.2025.11240792},
  note      = {Citation verified via Crossref; full text not read}
}

@article{somayaji2026llmuso,
  author  = {N. S. Karthik Somayaji and Peng Li},
  title   = {{LLM-USO}: Large Language Model-Based Universal Sizing Optimizer},
  journal = {IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems},
  volume  = {45},
  number  = {4},
  pages   = {1907--1920},
  year    = {2026},
  doi     = {10.1109/TCAD.2025.3604643}
}

@article{liu2026eesizer,
  author  = {Chang Liu and Danial Chitnis},
  title   = {{EEsizer}: {LLM}-Based {AI} Agent for Sizing of Analog and Mixed Signal Circuit},
  journal = {IEEE Transactions on Circuits and Systems I: Regular Papers},
  volume  = {73},
  number  = {6},
  pages   = {3825--3834},
  year    = {2026},
  doi     = {10.1109/TCSI.2025.3646359}
}

@inproceedings{liu2025llmsizingagent,
  author    = {Chang Liu and Emmanuel A. Olowe and Danial Chitnis},
  title     = {{LLM}-Based {AI} Agent for Sizing of Analog and Mixed Signal Circuit},
  booktitle = {2025 23rd IEEE Interregional NEWCAS Conference (NEWCAS)},
  pages     = {90--94},
  year      = {2025},
  doi       = {10.1109/NEWCAS64648.2025.11107079}
}

@inproceedings{yu2026autosizer,
  author    = {Xi Yu and Dmitrii Torbunov and Soumyajit Mandal and Yihui Ren},
  title     = {{AutoSizer}: Automatic Sizing of Analog and Mixed-Signal Circuits via Large Language Model ({LLM}) Agents},
  booktitle = {Proceedings of the 43rd International Conference on Machine Learning (ICML)},
  series    = {PMLR},
  volume    = {306},
  pages     = {151161--151186},
  year      = {2026}
}

@misc{hao2026agenticsizing,
  author = {Yijia Hao and Pratibha Verma and Dongxu Guo and Cristian Sestito and Michael O'Boyle and Christos-Savvas Bouganis and Themis Prodromakis},
  title  = {{AgenticSizing}: A Large Language Model-based Multi-Agent Framework for Analog Circuit Sizing},
  year   = {2026},
  eprint = {2609.25873},
  archivePrefix = {arXiv}
}

@misc{long2026analogscout,
  author = {Yichen Long and Keren Zhu},
  title  = {{AnalogScout}: Simulation-Efficient {PVT}-Aware Analog Sizing with {LLM} Agents},
  year   = {2026},
  eprint = {2610.37319},
  archivePrefix = {arXiv}
}

@article{wei2026toposizing,
  author  = {Ziming Wei and Zichen Kong and Yuan Wang and David Z. Pan and Xiyuan Tang},
  title   = {{TopoSizing}: An {LLM}-Aided Framework of Topology-Based Understanding and Sizing for {AMS} Circuits},
  journal = {IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems},
  volume  = {45},
  number  = {11},
  pages   = {5136--5148},
  year    = {2026},
  doi     = {10.1109/TCAD.2026.3685525}
}

@misc{wu2025easysize,
  author = {Xinyue Wu and Fan Hu and Shaik Jani Babu and Yi Zhao and Xinfei Guo},
  title  = {{EasySize}: Elastic Analog Circuit Sizing via {LLM}-Guided Heuristic Search},
  year   = {2025},
  eprint = {2508.05113},
  archivePrefix = {arXiv}
}

@misc{poddar2025heart,
  author = {Souradip Poddar and Chia-Tung Ho and Ziming Wei and Weidong Cao and Haoxing Ren and David Z. Pan},
  title  = {{HeaRT}: A Hierarchical Circuit Reasoning Tree-Based Agentic Framework for {AMS} Design Optimization},
  year   = {2025},
  eprint = {2511.19669},
  archivePrefix = {arXiv}
}

@misc{li2026sable,
  author = {Xunqi Li and Chris H. Kim},
  title  = {{SABLE}: An {NDA}-Safe Closed-Loop {LLM} Framework for Analog Circuit Optimization in Industrial {EDA} Flows},
  year   = {2026},
  eprint = {2607.03701},
  archivePrefix = {arXiv}
}

@misc{wei2026cascode,
  author = {Ziming Wei and Bingyang Liu and David Z. Pan},
  title  = {{CASCoDe}: A Closed-Loop Agentic Framework for Analog Sizing and Layout Co-Design},
  year   = {2026},
  eprint = {2611.11710},
  archivePrefix = {arXiv}
}

@inproceedings{kim2025glova,
  author    = {Dongjun Kim and Junwoo Park and Chaehyeon Shin and Jaeheon Jung and Kyungho Shin and Seungheon Baek and Sanghyuk Heo and Woongrae Kim and Inchul Jeong and Joohwan Cho and Jongsun Park},
  title     = {{GLOVA}: Global and Local Variation-Aware Analog Circuit Design with Risk-Sensitive Reinforcement Learning},
  booktitle = {2025 62nd ACM/IEEE Design Automation Conference (DAC)},
  pages     = {1--7},
  year      = {2025},
  doi       = {10.1109/DAC63849.2025.11132461}
}

@inproceedings{dong2023cktgnn,
  author    = {Zehao Dong and Weidong Cao and Muhan Zhang and Dacheng Tao and Yixin Chen and Xuan Zhang},
  title     = {{CktGNN}: Circuit Graph Neural Network for Electronic Design Automation},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2023},
  eprint    = {2308.16406},
  archivePrefix = {arXiv}
}

@inproceedings{chang2024lamagic,
  author    = {Chen-Chia Chang and Yikang Shen and Shaoze Fan and Jing Li and Shun Zhang and Ningyuan Cao and Yiran Chen and Xin Zhang},
  title     = {{LaMAGIC}: Language-Model-based Topology Generation for Analog Integrated Circuits},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning (ICML)},
  series    = {PMLR},
  volume    = {235},
  pages     = {6253--6262},
  year      = {2024}
}

@inproceedings{chang2025lamagic2,
  author    = {Chen-Chia Chang and Wan-Hsuan Lin and Yikang Shen and Yiran Chen and Xin Zhang},
  title     = {{LaMAGIC2}: Advanced Circuit Formulations for Language Model-Based Analog Topology Generation},
  booktitle = {Proceedings of the 42nd International Conference on Machine Learning (ICML)},
  series    = {PMLR},
  volume    = {267},
  pages     = {7351--7360},
  year      = {2025}
}

@inproceedings{vijayaraghavan2025autocircuitrl,
  author    = {Prashanth Vijayaraghavan and Luyao Shi and Ehsan Degan and Vandana Mukherjee and Xin Zhang},
  title     = {{AUTOCIRCUIT-RL}: Reinforcement Learning-Driven {LLM} for Automated Circuit Topology Generation},
  booktitle = {Proceedings of the 42nd International Conference on Machine Learning (ICML)},
  series    = {PMLR},
  volume    = {267},
  pages     = {61498--61512},
  year      = {2025}
}

@inproceedings{gao2025analoggenie,
  author    = {Jian Gao and Weidong Cao and Junyi Yang and Xuan Zhang},
  title     = {{AnalogGenie}: A Generative Engine for Automatic Discovery of Analog Circuit Topologies},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  eprint    = {2503.00205},
  archivePrefix = {arXiv}
}

@inproceedings{gao2025analoggenielite,
  author    = {Jian Gao and Weidong Cao and Xuan Zhang},
  title     = {{AnalogGenie-Lite}: Enhancing Scalability and Precision in Circuit Topology Discovery through Lightweight Graph Modeling},
  booktitle = {Proceedings of the 42nd International Conference on Machine Learning (ICML)},
  series    = {PMLR},
  volume    = {267},
  pages     = {18277--18289},
  year      = {2025}
}

@inproceedings{mehradfar2025falcon,
  author    = {Asal Mehradfar and Xuzhe Zhao and Yilun Huang and Emir Ceyani and Yankai Yang and Shihao Han and Hamidreza Aghasi and Salman Avestimehr},
  title     = {{FALCON}: An {ML} Framework for Fully Automated Layout-Constrained Analog Circuit Design},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2025},
  eprint    = {2505.21923},
  archivePrefix = {arXiv},
  note      = {Venue per arXiv comment}
}

@misc{zhou2026explore,
  author = {Guanglei Zhou and Chen-Chia Chang and Yikang Shen and Jonathan Ku and Isaac Jacobson and Jingyu Pan and Yiran Chen and Xin Zhang},
  title  = {{EXPLORE}: Exploration with Guided Search for Analog Topology Generation using Language Models},
  year   = {2026},
  eprint = {2607.13416},
  archivePrefix = {arXiv},
  note   = {MLCAD 2026 per arXiv comment}
}

@misc{kim2026analogtobi,
  author = {Seungmin Kim and Mingun Kim and Yuna Lee and Yulhwa Kim},
  title  = {{AnalogToBi}: Device-Level Analog Circuit Topology Generation via Bipartite Graph and Grammar Guided Decoding},
  year   = {2026},
  eprint = {2603.08720},
  archivePrefix = {arXiv}
}

@misc{islam2026circuitformer,
  author = {Md Touhidul Islam and Sujan Kumar Saha and Farimah Farahmandi and Mark Tehranipoor},
  title  = {{CircuitFormer}: A Circuit Language Model for Analog Topology Design from Natural Language Prompt},
  year   = {2026},
  eprint = {2605.05773},
  archivePrefix = {arXiv}
}

@inproceedings{li2026analogfed,
  author    = {Qiufeng Li and Shu Hong and Tian Lan and Weidong Cao},
  title     = {{AnalogFed}: Privacy-Preserving Discovery of Analog Circuits at Scale with Federated Generative {AI}},
  booktitle = {2026 IEEE International Conference on LLM-Aided Design (ICLAD)},
  pages     = {217--222},
  year      = {2026},
  doi       = {10.1109/ICLAD71857.2026.00039}
}

@inproceedings{li2024analoggym,
  author    = {Jintao Li and Haochang Zhi and Ruiyu Lyu and Wangzhen Li and Zhaori Bi and Keren Zhu and Yanhan Zeng and Weiwei Shan and Changhao Yan and Fan Yang and Yun Li and Xuan Zeng},
  title     = {{AnalogGym}: An Open and Practical Testing Suite for Analog Circuit Synthesis},
  booktitle = {Proceedings of the 43rd IEEE/ACM International Conference on Computer-Aided Design (ICCAD)},
  pages     = {1--9},
  year      = {2024},
  doi       = {10.1145/3676536.3697117}
}

@misc{adbench2026longhorizon,
  author = {{Analog Design Bench Team}},
  title  = {Long-Horizon Analog Design Bench: Benchmarking Agents on Hours-Long Analog and Mixed-Signal Circuit Design Tasks},
  year   = {2026},
  eprint = {2609.33356},
  archivePrefix = {arXiv}
}

@misc{rajabi2026analogportbench,
  author = {Saeid Rajabi and Aly Moussa and Vishal Saxena and Chengmo Yang and Satwik Patnaik},
  title  = {{AnalogPortBench}: Benchmarking {LLMs} on Analog Circuit Porting},
  year   = {2026},
  eprint = {2610.33088},
  archivePrefix = {arXiv}
}

@inproceedings{leibl2026loadbench,
  author    = {M. Leibl and F. Azevedo and S. Uhlich and A. Bonetti and A. Venkitaraman and C. Hsieh and P. Pham and L. Servadei and H. Graeb and R. Martins},
  title     = {{LOADBench}: A Large Open Analog Dataset and Benchmark for Machine Learning in {IC} Design},
  booktitle = {Proceedings of the ACM/IEEE Symposium on Machine Learning for CAD (MLCAD)},
  year      = {2026},
  doi       = {10.1145/3831599.3840321},
  eprint    = {2610.21591},
  archivePrefix = {arXiv},
  note      = {DOI from arXiv metadata; pages not verified}
}

@misc{bhandari2024masalachai,
  author = {Jitendra Bhandari and Vineet Bhat and Yuheng He and Hamed Rahmani and Siddharth Garg and Ramesh Karri},
  title  = {{Masala-CHAI}: A Large-Scale {SPICE} Netlist Dataset for Analog Circuits by Harnessing {AI}},
  year   = {2024},
  eprint = {2411.14299},
  archivePrefix = {arXiv},
  note   = {Peer-reviewed venue UNVERIFIED}
}

@misc{chen2025analogseeker,
  author = {Zihao Chen and Ji Zhuang and Jinyi Shen and Xiaoyue Ke and Xinyi Yang and Mingjie Zhou and Zhuoyao Du and Xu Yan and Zhouyang Wu and Zhenyu Xu and Jiangli Huang and Li Shang and Xuan Zeng and Fan Yang},
  title  = {Dataset Construction for Training {LLM} to Learn Analog Circuit Knowledge (formerly: {AnalogSeeker}: An Open-source Foundation Language Model for Analog Circuit Design)},
  year   = {2025},
  eprint = {2508.10409},
  archivePrefix = {arXiv}
}

@inproceedings{chen2025analogtester,
  author    = {Weiyu Chen and Chengjie Liu and Wenhao Huang and Jinyang Lyu and Mingqian Yang and Yuan Du and Li Du and Jun Yang},
  title     = {{AnalogTester}: A Large Language Model-Based Framework for Automatic Testbench Generation in Analog Circuit Design},
  booktitle = {2025 International Symposium of Electronics Design Automation (ISEDA)},
  pages     = {201--207},
  year      = {2025},
  doi       = {10.1109/ISEDA65950.2025.11100397}
}

@inproceedings{matsuo2025schemato,
  author    = {Ryoga Matsuo and Stefan Uhlich and Arun Venkitaraman and Andrea Bonetti and Chia-Yu Hsieh and Ali Momeni and Lukas Mauch and Augusto Capone and Eisaku Ohbuchi and Lorenzo Servadei},
  title     = {Schemato -- An {LLM} for Netlist-to-Schematic Conversion},
  booktitle = {2025 ACM/IEEE 7th Symposium on Machine Learning for CAD (MLCAD)},
  pages     = {1--7},
  year      = {2025},
  doi       = {10.1109/MLCAD65511.2025.11189059}
}

@misc{yoshioka2026vibetapeout,
  author = {Kentaro Yoshioka},
  title  = {The Era of Vibe Tapeout: Dark Age or Golden Age for Analog Circuit Design?},
  year   = {2026},
  eprint = {2610.15240},
  archivePrefix = {arXiv}
}

@inproceedings{settaluri2020autockt,
  author    = {Keertana Settaluri and Ameer Haj-Ali and Qijing Huang and Kourosh Hakhamaneshi and Borivoje Nikolic},
  title     = {{AutoCkt}: Deep Reinforcement Learning of Analog Circuit Designs},
  booktitle = {2020 Design, Automation \& Test in Europe Conference \& Exhibition (DATE)},
  pages     = {490--495},
  year      = {2020},
  doi       = {10.23919/DATE48585.2020.9116200}
}

@inproceedings{wang2020gcnrl,
  author    = {Hanrui Wang and Kuan Wang and Jiacheng Yang and Linxiao Shen and Nan Sun and Hae-Seung Lee and Song Han},
  title     = {{GCN-RL} Circuit Designer: Transferable Transistor Sizing with Graph Neural Networks and Reinforcement Learning},
  booktitle = {2020 57th ACM/IEEE Design Automation Conference (DAC)},
  pages     = {1--6},
  year      = {2020},
  doi       = {10.1109/DAC18072.2020.9218757}
}

@inproceedings{vijayaraghavan2024circuitsynth,
  author    = {Prashanth Vijayaraghavan and Luyao Shi and Ehsan Degan and Xin Zhang},
  title     = {{CircuitSynth}: Leveraging Large Language Models for Circuit Topology Synthesis},
  booktitle = {2024 IEEE LLM Aided Design Workshop (LAD)},
  pages     = {1--6},
  year      = {2024},
  doi       = {10.1109/LAD62341.2024.10691716}
}

@inproceedings{yang2025circuitagent,
  author    = {Tingjie Yang and Bo Li and Yongfu Li and Wei Mao and Genquan Han},
  title     = {{Circuit-Agent}: A Large Language Model Based Circuit Agent Framework for Analog/Mixed-signal Circuit Design Automation},
  booktitle = {2025 IEEE 7th International Conference on Artificial Intelligence Circuits and Systems (AICAS)},
  pages     = {1--5},
  year      = {2025},
  doi       = {10.1109/AICAS64808.2025.11173131}
}

@inproceedings{pan2025crop,
  author    = {Jingyu Pan and Isaac Jacobson and Zheng Zhao and Tung-Chieh Chen and Guanglei Zhou and Chen-Chia Chang and Vineet Rashingkar and Yiran Chen},
  title     = {{CROP}: Circuit Retrieval and Optimization with Parameter Guidance using {LLMs}},
  booktitle = {IEEE/ACM International Conference on Computer-Aided Design (ICCAD)},
  year      = {2025},
  eprint    = {2507.02128},
  archivePrefix = {arXiv},
  note      = {Digital VLSI flow tuning, not analog; venue per arXiv comment}
}

% ---- UNVERIFIED (do not cite without checking) ----
% LADAC: C. Liu, Y. Liu, Y. Du, L. Du, "LADAC: Large language model-driven auto-designer for analog circuits," TechRxiv preprint, 2024. (Only seen in citing papers.)
% "Spec2Netlist": not found anywhere.
```
