# 2026 literature and code-read ledger

This ledger is the audit boundary for the 2026 material in `LIT_SURVEY.md`. It prevents a
metadata lookup, an abstract, or a repository landing page from being reported as a full-paper
and full-code read. The tags in the survey remain authoritative for individual entries.

## Evidence levels

| Level | Required evidence | Allowed use |
|---|---|---|
| `PDF+CODE` | Full paper or arXiv PDF read, experiment tables/limitations extracted, and the public repository inspected at a pinned commit | Method, benchmark, metric, and implementation design input |
| `PDF` | Full paper or arXiv PDF read with experiment and limitations notes | Method and evaluation design input. Code claims remain unverified |
| `ABSTRACT/DOI` | Abstract, DOI, proceedings record, or citation metadata only | Candidate reference and search lead. No detailed numerical or implementation claim |
| `REPO` | Repository tree, README, manifests, and relevant scripts inspected at a pinned commit | Reproducibility and harness design input. Paper claims remain unverified |
| `UNREAD` | Title or program listing only, or the survey explicitly says “not read” | Do not use for claims or baseline selection |

## Current 2026 coverage

The following entries are the high-priority sizing and benchmark references already documented in
`LIT_SURVEY.md`.

| Reference | Year/venue | Current level | What is extracted | Remaining action |
|---|---|---|---|---|
| AutoSizer | ICML 2026 | `PDF+CODE` | AMS-SizingBench scale, 300-sample budget, GA/BO/TuRBO/LEDRO/ADO-LLM/EEsizer baselines, self-reflection ablation | Keep its 24-circuit protocol as a calibration row |
| EEsizer | TCAS-I 2026 | `PDF+CODE` | Six basic circuits, 20-transistor op-amp, PTM 180/130/90, variation experiments and success flags | Preserve PTM and variation axes as capability checks |
| AgenticSizing | arXiv 2026 | `PDF+CODE` | Eight circuits, 55-transistor/60-variable integrated task, five repeats, Spectre | Add only as a paper-backed reference unless licensed Spectre is available |
| SAFTAC | NeurIPS 2026 claim/arXiv | `PDF` | Qwen3-8B SFT+GRPO, 8,626 tasks, 10 types, 114 netlists, pass@1 and feedback pass | Code and training data availability still need independent verification |
| AnalogScout | arXiv 2026 | `PDF` | 9-corner PVT, 500-sample mismatch, 16k simulation budget, confirmation seeds and Holm correction | No public method repository found. Do not call a clean-room row official |
| Long-Horizon Analog Design Bench | arXiv 2026 | `PDF+REPO` | 50 tasks, 17 designers, 15 configurations, 2,250 two-hour attempts, isolated verifier | Build a compatible source-native capability adapter before ranking |
| AMPICBench | 2026 repository | `REPO` | Public Sky130 decks and corner artifacts, source provenance | A common sizing objective and independent verifier are still required |
| SGAnalog | 2026 repository | `REPO` | Commit-pinned tapeout-derived tasks and native harness | Current direct Task 2 receipt is capability-only, not SIZ7g budget-matched |
| AnalogGym-Opt | TCAD 2026 claim/repository | `REPO` | GRPO/R-GNN optimizer, Pareto tracking and optional PVT | Record implementation provenance separately from paper reproduction |
| AnalogVerifier | ICML 2026 | `UNREAD` | Citation and PMLR listing only | Read full paper and inspect code before using its metrics or verifier design |
| ICCAD 2026 non-LLM sizing papers | ICCAD 2026 | `UNREAD` | Program titles only | Do not cite algorithmic details until PDFs are read |
| RFChipAgent, Analog-DB | arXiv 2026 | `UNREAD` | Titles and identifiers only | Retrieve PDFs and repositories, then classify scope |
| AnalogPortBench, LOADBench | arXiv/MLCAD 2026 | `ABSTRACT/DOI` | Task scale and headline protocol only | Read full papers and source manifests before adding benchmark rows |

## Code-read boundary

`docs/refs/REPO_ANALYSIS.md` records pinned source inspections for AnalogGym, AnalogGym-Opt,
the open-source 31-circuit suite, EEsizer, AnalogCoder-Pro, Analog Canvas, Virtuoso Bridge Lite,
ATLAS and related harnesses. It does not imply that every paper named in `LIT_SURVEY.md` has public
code. Paper-only rows remain clean-room adapters and are labelled in
`data/bench/paper_sizing_manifest.json`.

The current SPECTRA implementation therefore makes three separate claims.

1. A source or paper has been read at the level stated by its ledger tag.
2. A benchmark row is ranking-eligible only when its source task, simulator, PDK/model, budget,
   seed set, corner set and independent verifier are all present.
3. A literature reference can motivate a component or metric without being presented as an
   implemented baseline.

## Required update for each newly read 2026 item

Add the arXiv/DOI or official proceedings URL, retrieval date, local PDF SHA-256, repository URL
and commit, then record the benchmark scale, task split, simulator/PDK, baselines, metrics,
ablation axes, robustness protocol, limitations, and licensing status. If any item is unavailable,
leave its level as `ABSTRACT/DOI` or `UNREAD` and keep it out of the primary SOTA count.

