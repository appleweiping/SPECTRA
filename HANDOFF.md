# SPECTRA 项目交接文档（Handoff）

> 交接时间：2026-11-17 05:00 UTC。交接方：Claude Code（Opus 5.5，执行者）。接手方：GPT（或任何后续执行者）。
> 仓库：`https://github.com/appleweiping/spectra-analog-agent`（分支 `main`）。本地路径曾为 `/home/user/spectra`。
> 本文档是**唯一的入口**：先通读第 1–3 节，再按第 7 节的顺序执行。所有其它文档的位置见第 3 节。
> 交接时**所有实验已按用户要求停止**，在途的运行被中断（其 LLM 调用和仿真结果已缓存，重跑同一 run 时会复用，几乎不花钱）。

---

## 0. 一句话

我们在做一个面向 **ICCAD** 投稿的端到端 LLM-agent 模拟电路自动设计项目 **SPECTRA**：自然语言规格 → 拓扑 → 器件尺寸 → 在 SKY130 工艺上通过 45 个 PVT 条件验证的 SPICE 网表。核心想法是让 LLM 写 *design-intent program*（用 g<sub>m</sub>/I<sub>D</sub> 查表给每个管子定尺寸、并预测自身性能的 Python 程序），确定性层负责执行、仿真、诊断，数值搜索在程序的低维 intent 空间里做（含 PVT 最坏条件自适应）。同时发布基准 **SPECTRA-Bench**（117 个任务、12 个电路族）。论文草稿（ACM sigconf，匿名）已基本成型，**实验未完成**，**规模需要按用户最新要求扩展**（第 7.2 节）。

---

## 0.5 最重要的变更：后续全部改用 GPT 家族模型（优先于本文其它任何冲突表述）

用户原话（2026-11-17）：“让gpt来做了，那就是gpt系列的东西，因为claude额度不够了，后面让gpt按照你的思路做，就是让他有gpt家族的模型来做，如果需要消耗token”。

含义与执行要求：
1. **Claude 额度已用完**，后续不再调用任何 Claude 模型（包括 `claude -p`）。
2. **执行者**（写代码、跑实验、写论文的 agent）= GPT 家族模型。
3. **实验中智能体消耗 token 的 LLM**（SPECTRA 及所有 LLM baseline 的骨干，E4 诊断里的 LLM）= GPT 家族模型。所有方法必须用**同一个** GPT 模型做主实验（公平性）。
4. **ARIS 审稿者** = GPT 家族模型（ARIS 默认的审稿后端就是 Codex/GPT，见 ARIS 仓库 `skills/shared-references/reviewer-backends.md`）。为保持独立性，审稿用与执行者不同的 GPT 模型、每次新开会话、只读权限；仍属同族 → ARIS 记为 provisional。
5. **已有结果是用 Claude Opus 5.5（和 Haiku 5.5）作为骨干跑出来的，不能与 GPT 骨干的结果混在同一个比较里。** 处理方式：
   - 主实验（E1）、消融（E2）、PVT（E3）、故障注入（E4）**全部用 GPT 主模型重跑**，论文主结果改为 GPT 骨干；
   - 已有 Claude 结果保留在 `results/raw/E1`、`E2`、`E4`、`E5` 中，**作为“跨厂商骨干”补充研究**（在匹配任务上与 GPT 结果对比）。它们不完整：例如在 34 个难任务（`subset_primary`）上 Opus 的 seed-0 覆盖为 SPECTRA 24、direct 22、Gen+TPE 18、SPECTRA-min 19，只能在实际完成的匹配任务上报告，并注明“部分覆盖、额度所限”；
   - 建议把新 GPT 结果写到新的实验名下（例如 `E1g`、`E2g`、`E3g`、`E4g`、`E5g`），并把方法目录写成 `method@<gpt模型简称>`，避免与旧目录混淆；`analyze.py`/`comparisons.py`/`make_tables.py`/`paper_numbers.py` 需要相应参数化实验名。
6. **需要做的代码改动**（详见 7.0）：
   - 给 `spectra/agent/llm.py` 加 OpenAI/GPT 后端；
   - 把 `tools/aris_review.py` 改为 GPT 审稿（或用 ARIS 的 Codex MCP 路线）；
   - `scripts/run_bench.py` 增加 `--model` 的 GPT 选项。
7. **token 预算估计**（按 Claude 实测的每 run 用量，GPT 会有差异）：每 run 输入约 4–23k、输出约 8–44k token；SPECTRA 约 45k、direct 约 43–67k、Gen+TPE 约 13–24k、SPECTRA-min 约 22–25k token/run。按 7.1+7.2+7.3 的完整规模（约 1500–2500 个 run）估计**约 5–9 千万 token**。开始前请与用户确认使用哪个 GPT 模型、预算上限，并把模型 ID 和单价写进 `EXPERIMENT_LOG.md`。
8. 论文中所有 “Claude Opus 5.5 through the Claude Code CLI” 的表述要改为实际使用的 GPT 模型；合同 A8 中对应文字同步修改（属于协议变更，记录在 `EXPERIMENT_LOG.md`）。

---

## 1. 用户要求（全部，必须遵守）

### 1.1 原始目标（/goal，原文中文，逐条解释）
原文：“我们想做一个端到端的agent模拟电路自动化生成，你仔细研读理解近年多个相关顶会，但是我们的论文和科研项目质量还有规模都要做到一致甚至是超越，理解他是怎么设置各个实验规格和模块，framework的。你自己考量，科研利益最大化即可。同时请你参考多个顶会论文，近年，最近的相关顶会论文，理解研读他们的论文，研读他的论文框架，内容和github仓库如果有，仔细理解，创新我们的。我们要求投ICCAD，你论文规格标准字数质量要按照ICCAD来做，用auto claude code research in sleep (https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep.git)这个自动科研框架来规范你自动科研(你用opus5.5orfable5.1当executer和reviewer)，做这个项目，最后达成投稿程度。做到本地（没有就新建），github(记得commit push,没有就新建)”

要点：
1. **端到端 agent**：自然语言规格 → 可仿真、满足规格的晶体管级网表。
2. **对标近年顶会**（AnalogCoder AAAI'25、AnalogCoder-Pro TCAD'26、AnalogAgent、AnalogSAGE、AaLLM、AutoSizer ICML'26、AnalogScout、OPERA、Long-Horizon Bench 等，见 `docs/refs/LIT_SURVEY.md`）：质量和**规模要一致甚至超越**，实验规格、模块、framework 要对齐，并有创新。
3. **投 ICCAD**：格式、篇幅、质量按 ICCAD（见 1.4）。
4. **用 ARIS 框架规范科研流程**（W1 idea → W1.5 实验 → W2 审稿循环 → W3 写论文，产物放规范位置）。原指定执行者/审稿者为 Opus 5.5 或 Fable 5.1；**交接后执行者、审稿者和实验中的 LLM 全部改为 GPT 家族**（见 0.5 节）。
5. **达到可投稿程度**。
6. **本地 + GitHub 同步**：所有产物 commit 并 push（GitHub 仓库已由用户创建：`appleweiping/spectra-analog-agent`）。

### 1.2 用户的后续要求（2026-11-17）
原文：“目前的baseline，metrics，benchmark，总共有几个，顶会论文一般是几个，要规模对齐。另外消融实验里，我们的framework，component每一个都要有贡献，实验质量也要solid。这是一个顶会项目。”
1. **baseline / metric / benchmark 的数量和规模要与顶会对齐**（现状与差距见第 6 节表格，扩展方案见 7.2）。
2. **消融实验：framework 的每个 component 都要有贡献，且实验要 solid**。执行方式见 7.3。重要：贡献与否由数据决定，**不能**通过挑任务、挑种子、改指标让组件“显得有用”。如果充分功效的消融显示某组件无贡献，需要**询问用户**是“删除/合并该组件、简化方法”（交接方推荐）还是“保留并如实报告无显著效果”。用户尚未回答这个问题（交接前提出的选择题被用户以本交接指令代替）。
3. “这是一个顶会项目”：质量标准按顶会审稿人的要求。
4. 2026-11-17 交接指令：“把所有的要求写在项目交接文档里，停下你手头上的所有内容，全部更新到github上，然后之后我让gpt按照你的思路做完整个项目，你写的详细一点。” 以及 0.5 节的模型切换要求。

### 1.3 项目硬性规则（`CLAUDE.md`，必须遵守）
- **论文中的所有数字必须来自 `results/` 里的文件；禁止编造结果。** 本项目实现为：所有数字由 `scripts/paper_numbers.py` 生成宏（`paper/numbers.tex`），表格由 `scripts/make_tables.py` 生成，图由 `scripts/make_figures.py` 生成。**不要在 `paper/sections/*.tex` 里手写结果数字。**
- 非目标：版图、寄生提取、微调模型。
- 计算预算：4 CPU 核，ngspice-42，LLM 通过 `claude -p` 调用；每次 LLM 调用的 token/美元记录在 `results/llm_usage.jsonl`。
- 隐私：不要把用户的个人信息（邮箱等）发给任何外部服务。

### 1.4 ICCAD 格式（2026 CFP）
- ACM `acmart` 模板，`sigconf`，投稿用 `review,anonymous` 选项；**正文（含图表）≤ 8 页 + 参考文献 ≤ 1 页**；双盲；匿名代码用 anonymous.4open.science。
- LaTeX 保持可移植到 IEEEtran。
- 当前 `paper/main.tex` 已按此设置（`\acmConference[ICCAD '27]`）。编译：`cd paper && latexmk -pdf main.tex`（需要 texlive + `texlive-fonts-extra`（Libertine）+ inconsolata）。

---

## 2. 研究内容（读完即可理解项目）

### 2.1 问题与动机
- 现有 LLM 模拟电路 agent 的评测多用 Level-1 平方律模型 + 功能性 pass/fail（AnalogCoder 系列），或只做运放、只在 TT 角（AnalogSAGE、AaLLM）；做 PVT 的 LLM 方法只给定拓扑做 sizing（AnalogScout、OPERA）。Long-Horizon Analog Design Bench 证明前沿模型主要失败在**电学收敛**（同时满足所有定量指标）。
- 我们的 pilot 也证明：规格若从普通设计点放宽，所有方法都几乎 100% 成功（基准饱和）；所以基准必须**接近性能前沿 + 跨 PVT**。

### 2.2 方法 SPECTRA（代码 `spectra/agent/`）
1. **Design-intent program**（`prompts.py`、`dsl.py`、`sandbox_worker.py`）：LLM 写 `PARAMS = {name: (init, lo, hi)}` 和 `design(p, lut, spec) -> (Netlist, predictions)`。每个管子用 `lut.size(type, gm/Id, L, Id, vds, vsb)` 从 PDK g<sub>m</sub>/I<sub>D</sub> 查找表得到 W；程序返回网表 + 对每个指标的**自我预测**。沙箱执行（受限 builtins、禁止 import/IO/反射）。
2. **静态检查**：解析成规范网表 + ERC（`spectra/sim/netlist.py`）。
3. **仿真 + 器件级诊断**（`diagnose.py`）：规格表、工作区/裕量（V<sub>DS</sub>−V<sub>dsat</sub>、三极管区、弱反型、截止）、预测–仿真偏差（>25% / 6 dB / 10°）、接近可行时对 intent 变量的有限差分灵敏度、17 条规则生成的假设。
4. **分层修复策略**：LLM 选择 `Refine`（结构对，交给数值优化，可改初值和边界）/ `Edit`（重写程序）/ `Declare-Infeasible`。
5. **Intent 空间精修**：CMA-ES（σ0=0.15，种群 max(8, 4+⌊3 ln n⌋)，每块 80 次仿真，先评估当前点），每个候选都重新执行程序（匹配/镜像比例/偏置关系天然保持）。
6. **PVT-aware 精修**：鲁棒任务在 TT 通过后做 45 条件验证；失败则活动集 = TT + 最差 2 个条件，精修 → 再验证 → 加入新最差 2 个（最多 6 个），最多 3 轮；仍失败把逐条件失败表交还 LLM。
7. **SPECTRA-min**（关键对照）：1 次规划调用（+最多 2 次修程序错误）+ 全预算 intent CMA-ES + 相同 PVT 环，无诊断、无 LLM 修复。

### 2.3 基准 SPECTRA-Bench（`data/bench/`，构建代码 `spectra/bench/`、`scripts/build_bench.py` 等）
- 12 个电路族：运放、放大器、TIA、电流镜、LDO、基准源、连续时间比较器、时钟锁存比较器、VCO、滤波器、施密特触发器、运放应用（`spectra/sim/families.py`）。每族有单独 testbench 与指标提取（`tb_opamp.py`、`families.py`、`measure.py`）。
- 117 个任务 = 92 个认证任务（`tasks.jsonl`：T1 13、T2 21、T3 39、Robust 19）+ 25 个独立编写的 designer 任务（`designer_tasks.jsonl`，含 3 个鲁棒任务）。
- 认证任务：28 个专家参数化模板（`spectra/bench/templates.py`），CMA-ES 随机标量化探索得到参考设计，T3/鲁棒参考先做 **frontier refinement**（31/58 被改进），规格 = 参考性能按层级收紧的裕量（T1/T2/T3：−10/−5/−1 dB 等），每个任务的参考网表在 TT（鲁棒任务在 45 条件）重新仿真通过 = **可行性证书**。
- 45 PVT 条件：5 个工艺角（tt/ff/ss/sf/fs）× {−40, 27, 125 °C} × {1.62, 1.8, 1.98 V}。失配 Monte Carlo：tt_mc 角，按 PDK Pelgrom 系数逐实例 agauss，`.option seed=k`。
- 预算：每 run ≤12 次 LLM 调用；条件评估数（一个设计在一个 PVT 条件评估一次算 1）名义任务 300、鲁棒任务 600。成功判定由**智能体外部、不计预算**的重新仿真决定（`scripts/run_bench.py::verify`）。

### 2.4 实验设计（编号沿用）
| 编号 | 内容 | 状态 |
|---|---|---|
| E1 | 主实验：SPECTRA vs AnalogCoder-style（`direct`）vs Gen+TPE（`genbo`，AnalogCoder-Pro-style）vs SPECTRA-min，全部任务；主终点 = T3 ∪ 鲁棒任务（61 个） | 进行中（见 5.1） |
| E2 | 消融：w/o diagnosis、w/o intent（raw W/L 程序）、w/o refinement、w/o knowledge cards、AnalogCoder-style w/o cards | 部分完成 |
| E3 | PVT 策略：SPECTRA w/o PVT-aware refinement（`spectra_pvt_nominal`）、Gen+TPE-full（12 次再生成 + 自适应角） | 未开始 |
| E4 | 故障注入：7 类单故障 × 166 个案例，规则诊断 vs LLM+raw vs LLM+SPECTRA 诊断（Opus、Haiku） | 完成（Haiku summary 需重生成，见 7.1） |
| E5 | 骨干模型：Haiku 5.5 下 SPECTRA vs direct | 部分完成 |
| MC | 鲁棒任务最终设计的 100 样本失配 Monte Carlo | 未开始 |

### 2.5 假设（`refine-logs/FINAL_PROPOSAL.md`）与现状
- H1 端到端优势 → E1；H2 intent 抽象 → E2 w/o intent；H3 诊断 → E2 w/o diagnosis + E4；H4 PVT 精修 → E3；H5 跨骨干 → E5；H6 不可行声明 → 原 controls 已撤回（构建有误），**不得做此声明**。

---

## 3. 仓库地图

| 路径 | 内容 |
|---|---|
| `CLAUDE.md` | 项目状态 YAML + 硬性规则（接手后请更新状态） |
| `HANDOFF.md` | 本文档 |
| `RESEARCH_BRIEF.md` | 研究简报（W1 输入） |
| `idea-stage/` | `IDEA_REPORT.md`、`GATE1_REVIEW.md`（审稿意见）、`GATE1_RESPONSE.md` |
| `refine-logs/` | `FINAL_PROPOSAL.md`（研究合同/假设）、`EXPERIMENT_PLAN.md`、`CODE_REVIEW_R1.md` |
| `EXPERIMENT_LOG.md` | **所有实验协议及每一次偏离/修正的完整记录**（必读） |
| `review-stage/` | `ROUND1_REVIEW.md`（W2 第 1 轮，5/10，not-ready）、`AUTO_REVIEW.md`（逐条处理表） |
| `NARRATIVE_REPORT.md` | W3 输入：故事线、主张–证据矩阵 |
| `paper/` | LaTeX：`main.tex`、`sections/*.tex`、`tables/*.tex`（`families.tex`、`compare.tex` 手写，其余生成）、`figs/`（`overview.tex` TikZ、`program.tex` 代码清单、生成的 PDF）、`numbers.tex`（生成）、`refs.bib`、`CITATION_AUDIT.md`（PASS）、`PAPER_ACCEPTANCE_CONTRACT.md`（验收合同，已冻结）、`.contract_r{1,2,3}.md`（审稿方合同谈判原文） |
| `docs/refs/` | `LIT_SURVEY.md`（60+ 篇文献的细读笔记、实验规模对标表 §4、差距分析 §5）、`REPO_ANALYSIS.md`（参考仓库静态分析，含 AnalogGym 细节） |
| `spectra/sim/` | ngspice 运行器（磁盘缓存 + 跨进程 flock 槽）、网表/ERC/SKY130 编译、各族 testbench、LUT API、`evaluate.py`（NOMINAL、PVT 45 条件、MC 100） |
| `spectra/agent/` | SPECTRA 主循环 `spectra_agent.py`、`llm.py`（`claude -p` 封装 + 缓存 + 用量日志）、`common.py`（预算/上下文/硬上限）、`diagnose.py`、`prompts.py`、`knowledge.py`（所有方法共享的 PDK 说明与拓扑知识卡）、`dsl.py`、沙箱 |
| `spectra/baselines/` | `direct.py`（AnalogCoder-style）、`genbo.py`（Gen+TPE / Gen+CMA-ES / Gen+TPE-full）、`oracle.py`（专家模板 + 优化器） |
| `spectra/bench/` | 模板、族 profile、自然语言规格渲染 |
| `pdk/sky130/` | 最小化 SKY130 1.8 V FET + PNP 模型库（5 角 + tt_mc）、poly 电阻温度模型 |
| `data/lut/` | g<sub>m</sub>/I<sub>D</sub> 查找表（11 L × 10 VDS × 5 VSB × 181 VGS，W_ref=5 µm，5 角 × 3 温度） |
| `data/bench/` | 任务文件：`tasks.jsonl`、`designer_tasks.jsonl`、`E1_primary.jsonl`（61）、`E1_t3.jsonl`（39）、`E1_robust.jsonl`（22）、`E1_other.jsonl`、`subset_E2.jsonl`（35）、`subset_T3.jsonl`（23）、`subset_robust.jsonl`（11）、`subset_primary.jsonl`（34 = 23+11） |
| `data/llm_cache/`、`data/sim_cache/` | LLM 响应缓存（按 model+system+prompt+run_tag 哈希）、仿真结果缓存；**重跑同一 run 免费且确定** |
| `results/raw/<exp>/<method>/<task>/s<seed>.json` | 每个 run 的完整记录（状态、最终网表、程序、事件轨迹、调用/仿真/token/美元、外部验证结果） |
| `results/raw_cap1200_archive/` | 79 个在旧 1200 预算下跑的鲁棒 run（已归档，**任何分析都不得使用**） |
| `results/*.json` | 汇总：`E1_summary.json`、`comparisons.json`、`E4_*`、`E1_failures.json`、`E1_spectra_failure_modes.json`、`E1_spectra_prediction_accuracy.json`、`pvt_failure_conditions.json`、`llm_usage.jsonl` 等 |
| `scripts/` | 运行：`run_bench.py`、`run_E1_v3.sh`、`run_E2_E3_v2.sh`、`run_rerun_cap600.sh`、`run_mc.sh`、`relaunch_all.sh`；分析：`analyze.py`、`comparisons.py`、`pvt_failures.py`、`failure_analysis.py`、`spectra_failures.py`、`prediction_accuracy.py`、`e4_tests.py`、`mc_yield.py`、`bench_stats.py`；论文：`make_tables.py`、`make_figures.py`、`paper_numbers.py`、`finalize_paper.sh`（一键重生成全部分析/表/图/宏并编译） |
| `tools/aris_review.py` | ARIS 审稿桥：每次新开 `claude -p` 会话（只读工具），轨迹存 `.aris/traces/<skill>/` |
| `.aris/` | `reviewer.json`、`prompts/`（各轮审稿提示，含已写好的 `w2_round2.md`、`w3_claim_audit.md`、`w3_kill_attack.md`、`w3_kill_defense.md`）、`traces/` |

外部参考仓库（未入库，需要时自行 clone；版本号为交接时所读版本）：
ARIS `wanshuiyin/Auto-claude-code-research-in-sleep@9f30e83`；AnalogGym `CODA-Team/AnalogGym@0a9d139`；AnalogGym-Opt `Computing-Intelligent-Decision-Team/AnalogGym-Opt@10093e3`；AnalogCoder `laiyao1/AnalogCoder`；AnalogCoderPro `laiyao1/AnalogCoderPro@5db764d`；AnalogGenie `xz-group/AnalogGenie@efc2535`；EEsizer `eelab-dev/EEsizer@3af9421`；CktGNN `zehao-dong/CktGNN@416cd03`；LaMAGIC `turtleben/LaMAGIC@0cde737`；opensource-analog-circuits `jialinlu/opensource-analog-circuits@e8308aa`；AMSNet `lll143653/amsnet`、`AMS-Net/amsnet-kg-public`；Masala-CHAI `jitendra-bhandari/Masala-CHAI`；AnalogXpert `zhywhite/AnalogXpert`；Awesome list `qhy991/Awesome-LLM-Circuit-Agent`。SKY130 原始模型：`google/skywater-pdk-libs-sky130_fd_pr`（Apache-2.0）。

---

## 4. 环境搭建

```bash
# 系统
apt-get install -y ngspice            # 必须是 ngspice-42（`ngspice -v` 检查）；其它版本会改变数值，需重新验证
apt-get install -y texlive-latex-extra texlive-fonts-extra texlive-science latexmk   # acmart + Libertine + inconsolata
# Python ≥ 3.11
pip install numpy scipy cma optuna matplotlib
pip install openai                    # GPT 后端（见 0.5 与 7.0）
export OPENAI_API_KEY=...             # 由用户提供，切勿写入仓库
export PYTHONPATH=.
# 注意：Claude 额度已用完，不要再调用 `claude -p`；旧缓存 data/llm_cache 仍可被读取（重算旧 Claude 结果的分析时不会发新请求）
```
验证：`python -c "from spectra.sim.evaluate import evaluate"`；`bash scripts/finalize_paper.sh`（约 40 秒，重生成全部分析并编译 PDF）。LUT 已在仓库（`data/lut/`），无需重算；若需重算：`python -m scripts.gen_lut tt ff ss sf fs T=-40 T=27 T=125`。

运行时环境变量：`SPECTRA_GLOBAL_SIM_SLOTS`（全机并发 ngspice 数，4 核建议 4–6）、`SPECTRA_SIM_CONCURRENCY`（单进程内并发，4）、`SPECTRA_LLM_CONCURRENCY`（并发 LLM 调用数，10–14）。**CPU 过载会严重降低吞吐**（曾出现 load 27），务必用全局槽限制。

---

## 5. 停止时刻的精确状态

### 5.1 实验完成度（2026-11-17 05:00 UTC）
| 实验 | 范围（最终协议 v3） | 已完成 |
|---|---|---|
| E1 seed 0，主终点 61 任务 | spectra / direct / genbo / spectra_min | 43 / 42 / 34 / 35（其中鲁棒 22 个：19 / 21 / 13 / 12） |
| E1 seed 1，T3 39 任务 | spectra / direct | 9 / 9 |
| E1 T1/T2/designer 名义任务 | 各方法 ≥1 seed | 已完成（早期跑完） |
| E2 w/o diagnosis、w/o intent，seed 0–1，35 任务 | 应 70 / 70 | 61 / 59 |
| E2 w/o refinement、w/o cards、direct w/o cards，seed 0，`subset_T3`（23） | | 0 |
| E3 genbo_full、spectra_pvt_nominal，seed 0，`subset_robust`（11） | | 0 |
| E5 Haiku spectra / direct，seed 0，`subset_primary`（34） | | 8 / 7 |
| E4 故障注入 Opus / Haiku | 166 / 166 | 166 / 166（Haiku 汇总文件仍是旧的 120 例版本，需重生成） |
| MC 失配 | 鲁棒 seed-0 通过 PVT 的设计 | 0 |
| 1200 预算归档的鲁棒 run 重跑 | E1 46、E2 25、E5 8 | 部分被 E1 主链重跑（E1 鲁棒数字已含）；E2/E5 未完成 |

### 5.2 中间结果（**Claude Opus 5.5 骨干、interim，不能当最终结论**；GPT 重跑后这些只作为跨厂商对照；来源 `results/E1_summary.json`，33 个公共任务、18 个主终点任务）
- 主终点成功率：SPECTRA 81.5% [63,96]，AnalogCoder-style 74.1% [54,93]，Gen+TPE 32.4% [14,53]，SPECTRA-min 74.1% [56,89]。
- 配对检验（主终点，Holm）：vs Gen+TPE 11 胜 0 负，p=0.004（显著）；vs AnalogCoder-style 4 胜 2 负，p=0.69（不显著）；vs SPECTRA-min 6 胜 2 负，p=1.0。
- 全部公共任务成功率：SPECTRA 88.9%，direct 85.9%，Gen+TPE 59.1%，SPECTRA-min 80.8%；SPECTRA 成功 run 的调用中位数 3、仿真中位数 10；平均成本 $0.58/run。
- E4：Opus 下诊断不提升定位（top-1 77.1% vs 77.1%，各有 10 个独占正确，McNemar p=1.0）；Haiku（156 例时）60.9% → 55.1%，p=0.21（不显著，不能说“诊断有害”）。
- SPECTRA 失败模式（`results/E1_spectra_failure_modes.json`）：输给 direct 的主终点任务全部是**鲁棒基准源（ref-04、ref-05）**：PVT 环在最坏违例不下降（停滞）时仍跑满 3 轮（中位约 336 次条件评估），返回 LLM 时只剩 1–2 次修改的预算。**不得在评测集上“修复”这一点再重跑**（那是在测试集上调方法）；论文中作为失败模式与未来工作报告。
- 设计意图程序预测精度（`results/E1_spectra_prediction_accuracy.json`）：一阶量准（功耗、UGBW、增益、相位裕度），二阶量差（CMRR/PSRR、压摆率、建立时间、噪声）。
- 消融（`results/comparisons.json`）目前只有 5–8 个匹配任务，**完全不足以下结论**；早期数据中 w/o diagnosis / w/o intent 与 SPECTRA 持平或略高，需充分功效的实验确认（7.3）。
- LLM 总花费约 $396（`results/llm_usage.jsonl`）。

### 5.3 论文状态（`paper/main.pdf`，当前 8 页含参考文献，正文约 6 页）
已有：摘要（主结论 `\AbsMainClaim` 由脚本按 Holm p 和方向自动生成措辞）、引言、相关工作、基准章节（含与先前工作的对比表 `tables/compare.tex`，含最接近的 Long-Horizon Bench）、方法、实验设置、主结果（含“SPECTRA 在哪里失败”段落）、消融/PVT/骨干三个小节（文本由宏生成，**解释性文字待写**）、E4 故障注入（含诚实的零结果）、局限与结论。
待完成：最终数字、消融/PVT/骨干的解释性文字、结论中的比较性措辞须符合合同 A7（不显著不能说“reliable/outperforms”）、页面利用（还有约 1.5 页正文空间）、W2 第 2 轮审稿、claim audit、kill-argument、匿名 artifact 链接。

### 5.4 ARIS 进度
- W0/W1/W1.5（含代码审查 R1，全部 MUST-FIX 已修）完成。
- W2：第 1 轮 5/10 not-ready（`review-stage/`），所有条目已处理；第 2 轮提示已写好（`.aris/prompts/w2_round2.md`），**需在最终数字出来后执行**。
- W3：`NARRATIVE_REPORT.md`、`paper/PAPER_ACCEPTANCE_CONTRACT.md`（3 轮谈判后冻结，第 3 轮的 3 条要求已原样采纳；审稿方未再确认）。claim audit / kill-argument 提示已写好，待执行。引用审计已 PASS（`paper/CITATION_AUDIT.md`；`refs.bib` 的审计备注字段已改名为 `auditnote`，不会打印）。

---

## 6. 规模对标（用户 1.2 的第 1 点）

| 维度 | 我们（交接时） | 顶会典型（来源 `docs/refs/LIT_SURVEY.md` §4） | 差距 |
|---|---|---|---|
| Benchmark | 1 个自建（SPECTRA-Bench 117 任务）+ 故障注入集 166 例 | 1–2 个，**通常含一个公认外部基准**：AnalogCoder 24 / AnalogCoder-Pro 28 / AnalogAgent 30（功能性），AnalogGym（ICCAD'24），AutoSizer AMS-SizingBench 24 个 SKY130 电路 | **缺外部基准**（注意：任务 #4 标题曾写“AnalogCoder 24 functional tasks”，但**从未移植**） |
| 端到端 baseline | 2 个主 baseline（AnalogCoder-style、Gen+TPE）+ Gen+TPE-full（仅 11 个鲁棒任务）+ SPECTRA-min | 3–7 个（AutoSizer：GA、BO、TuRBO、CMA-ES + LEDRO、ADO-LLM、EEsizer；AnalogAgent：3 个；AnalogScout：CMA-ES、BO + 2 种 LLM 流程） | 偏少；Gen+CMA-ES（`genbo_cmaes`）和专家模板 + CMA-ES（`oracle_cmaes`）**已实现但未跑** |
| 消融 | 6 个分支（w/o diagnosis、w/o intent、w/o refinement、w/o cards、w/o PVT 精修、SPECTRA-min） | 3–5 个组件，3–5 seeds | 分支数够，**功效不足**（1–2 seeds，匹配任务太少） |
| Seeds / trials | 每任务 1–3（分层） | 3–5（AnalogScout 5 个确认 seeds + Holm） | 偏少 |
| LLM 骨干 | 2 个（Opus 5.5、Haiku 5.5） | 4–8 个 | 偏少（只能用 Claude 系列；可加 Sonnet 5.5、Fable 5.1） |
| 指标 | 成功率（TT/45 PVT）+ CI、分层成功率、成功所需仿真/调用/token/美元、anytime 曲线、MC 良率、预测误差、定位 top-1/top-3、配对检验 | Pass@k、成功率、FoM、仿真次数/时间/token | 基本对齐；3 seeds 后可加 pass@k |

---

## 7. 剩余工作（按顺序执行）

### 7.0 接手第一步（约 30 分钟）
1. 按第 4 节搭环境；确认 `ngspice -v` 为 42、GPT API 可用。
1b. **实现 GPT 后端**（约 1–2 小时）：
   - 在 `spectra/agent/llm.py` 中保持 `call(prompt, system, model, run_tag, tag, timeout, retries, effort) -> dict` 接口不变，按 `MODELS` 映射，以 `gpt`/`openai` 前缀分派到 OpenAI API（system 作为 system/developer 消息，prompt 作为 user 消息，无工具）。
   - 返回字段必须同名：`text`、`model`、`seconds`、`input_tokens`、`output_tokens`、`cost_usd`（按该模型的官方单价计算）、`reported_models`。
   - 保留磁盘缓存（键 = sha256([model_id, system, prompt, run_tag, effort])）、`results/llm_usage.jsonl` 记录、指数退避重试。
   - 温度等采样参数固定并记录。
   - 用 `--model <gpt简称>` 跑一个 T1 任务做冒烟测试（`--exp smoke`）。
1c. **审稿后端**：把 `tools/aris_review.py` 的 `claude -p` 换成 GPT 调用（或使用 ARIS 的 Codex MCP 路线）。审稿者必须能自己读仓库文件（只读）；如果只能用 API，就把需要审阅的文件内容按提示中列出的路径拼进上下文。轨迹仍保存到 `.aris/traces/`。
   - `fault_injection.py` 有 `model` 参数，E4 用 GPT 重跑：`python -m scripts.fault_injection <gpt简称>`，汇总文件名为 `results/E4_<model>_summary.json`；`scripts/e4_tests.py` 需参数化目录名。
2. 通读 `EXPERIMENT_LOG.md`、`paper/PAPER_ACCEPTANCE_CONTRACT.md`、`review-stage/AUTO_REVIEW.md`。
3. 更新 `CLAUDE.md` 的状态块（执行者改为 GPT，见第 10 节）。
4. 重生成 E4 Haiku 汇总：`PYTHONPATH=. python -m scripts.fault_injection haiku`。166 个案例已全部缓存在 `results/raw/E4_haiku/`，脚本会直接读取，不发新请求；若因缺少 Claude CLI 报错，就直接用 `results/raw/E4_haiku/*.json` 按 `fault_injection.py` 末尾的汇总代码重算。确认 `results/E4_haiku_summary.json` 的 `n_cases` = 166，然后 `python -m scripts.e4_tests`。
5. `bash scripts/finalize_paper.sh` 确认管线无误。

### 7.1 完成当前范围（协议 v3）——**改为用 GPT 骨干重跑完整范围**
由于模型切换（0.5 节），旧链（Claude）不能直接重启：它们会调用 `claude -p`。做法：
- 把 `scripts/run_E1_v3.sh`、`run_E2_E3_v2.sh`、`run_rerun_cap600.sh`、`run_mc.sh` 复制为 GPT 版本：实验名加后缀 `g`，`--model <gpt简称>`，任务文件和种子策略不变；
- 主实验优先级：E1g 的 61 个主终点任务（seed 0 → 1 → 2），再 E2g、E3g、E5g，最后 T1/T2/designer 名义任务；
- 原有的 Claude 链保留不再运行。

以下是原 v3 链的说明（GPT 版本照此结构）：
```bash
rm -f /tmp/spectra_sim_slots/*        # 清理残留的 flock 槽文件
bash scripts/relaunch_all.sh          # 启动 run_E1_v3.sh、run_E2_E3_v2.sh、run_rerun_cap600.sh、run_mc.sh
```
- `run_E1_v3.sh`：E1 seed 0 主终点 → seed 1 T3（spectra、direct）→ `results/E1_V2_DONE`。
- `run_E2_E3_v2.sh`：E2 w/o diag / w/o intent（seed 0,1）→ E2 w/o refine / w/o cards / direct w/o cards（seed 0，subset_T3）→ E3（genbo_full、spectra_pvt_nominal，seed 0，subset_robust）→ E5（Haiku，seed 0，subset_primary）→ `results/E2E3_DONE`。
- `run_rerun_cap600.sh`：等 E2E3_DONE 后补跑 E2 被归档的鲁棒 run → `results/RERUN600_DONE`。
- `run_mc.sh`：三个 DONE 都存在后跑 `mc_yield 100` → `results/MC_DONE`。
- 注意：`run_E1_v3.sh` 第一行在等待一个已经不存在的旧进程，直接继续；E1 鲁棒任务只跑 seed 0；**任何鲁棒 run 的 `budget_sims` 必须是 600**（`analyze.py` 会排除其它）。
- 预计：在 4 核上约 6–8 小时（鲁棒 run 是 CPU 瓶颈，平均 250–400 次条件评估、20–30 分钟/个；名义 run 主要受 LLM 延迟限制）。
- 吞吐建议：只要 load average < 核数就可以并行多条链；> 1.5×核数时暂停次要链（`kill -STOP`）。

### 7.2 规模对齐扩展（用户 1.2 的要求；**动手前先和用户确认预算**：估计额外 LLM 花费 $500–700、CPU 100–150 核时；单机约 2 天，3 个并行云会话约 10–12 小时）
建议的“v4 协议”，所有新增内容先写入 `EXPERIMENT_LOG.md` 再执行：
1. **Baseline 扩展到 6 个 + SPECTRA-min**（全部在 61 个主终点任务上，同 LLM、同知识卡、同预算）：
   - `oneshot`（新实现）：单次调用、无反馈的 LLM 直接出网表（对应 AnalogCoder 论文中的 raw-LLM baseline）。实现建议：在 `scripts/run_bench.py::make_runner` 增加 `oneshot`，调用 `run_direct` 并把预算设为 `Budget(llm_calls=1, sims=…)`；确认 direct 的第一次调用即产出网表。
   - `direct`（已有）、`genbo`（已有）。
   - `genbo_cmaes`（已实现）：Gen + CMA-ES。
   - `genbo_full`（已实现）：扩到全部 61 个主终点任务（现在只计划 11 个鲁棒任务）。
   - `oracle_cmaes`（已实现，`spectra/baselines/oracle.py`）：给定专家模板拓扑 + CMA-ES 在原始变量上 sizing——对应 AutoSizer/AnalogScout 的“给定拓扑 + 经典优化器”设置，作为 sizing 参考上限。注意：它使用了生成任务的模板，论文中必须说明它是有特权信息的参考，不是公平对手。
2. **Seeds**：所有方法在 61 个主终点任务上 3 seeds（目前 spectra/direct 在 T3 上 2 seeds、鲁棒 1 seed；其它 1 seed）。完成后报告 pass@1（均值）和 pass@3。
3. **骨干**：在 `subset_primary`（34）上加 Sonnet 5.5（`--model sonnet`，实验名 E5，方法 spectra、direct），若预算允许再加 Fable 5.1。论文中注明只覆盖 Claude 系列（局限）。
4. **外部基准（推荐 AnalogGym，ICCAD'24）**：SKY130 + ngspice 原生可跑的 16 个三级运放 + 5 个 LDO（细节见 `docs/refs/REPO_ANALYSIS.md` §1.1–1.3：网表、设计变量、testbench、指标提取、各电路规格目标；注意 `Qu_LEC` 文件为空、LDO 规格单位不一致）。设置：给定拓扑的 sizing 任务，300 次评估预算，3 seeds；方法：SPECTRA sizing 模式（新实现：提示中给出网表与设计变量，LLM 写 intent 程序映射到其设计变量）、CMA-ES、TPE、随机搜索（对应 AutoSizer 的经典优化器 baseline），可选 SPECTRA-min。指标：全部规格满足率、归一化 reward（其 `min((x−t)/(x+t),0)` 之和）、到达最佳所需评估数。用 AnalogGym 自带的 sky130 PDK 和 testbench，**不要**改它的规格。需要实现 `spectra/sim/analoggym.py`（读取其网表/变量/testbench、调用我们的 ngspice 运行器与缓存）。估计工程 0.5 天、CPU 约 40–50 核时（可降到 2 seeds）。备选外部基准：AnalogCoder 24 个功能任务（便宜但对 Opus 级模型已饱和，需要 Level-1 LUT 与其 PySpice 检查脚本）。
5. **执行方式**：先跑完 7.1，再按“消融 → baseline → seeds → 骨干 → 外部基准”的顺序；每完成一块就 `finalize_paper.sh` + commit/push。

### 7.3 消融：每个组件都要有贡献、实验要 solid（用户 1.2 的第 2 点）
- **在哪跑**：`data/bench/subset_primary.jsonl`（34 个难任务：23 个 T3 + 11 个鲁棒），不要在已饱和的 T1/T2 上跑（饱和任务上任何组件都显示不出差别）。
- **跑什么**（全部 3 seeds，SPECTRA 本体在这些任务上也要有 3 seeds）：`spectra_nodiag`（w/o 诊断）、`spectra_nointent`（w/o intent，raw W/L 程序）、`spectra_norefine`（w/o intent 空间精修）、`spectra_noknow`（w/o 知识卡）、`spectra_min`（w/o 诊断 + w/o LLM 修复）、`spectra_pvt_nominal`（w/o PVT-aware 精修，仅 11 个鲁棒任务）；外加 `direct_noknow` 作为“知识卡对 baseline 的作用”的对照。可选：`spectra_pvt_all`（每步在全部 45 条件上精修，检验自适应选角的成本优势）。
- **怎么报**：`scripts/comparisons.py` 已实现匹配任务块（每个块内所有方法限制在都完成的任务上）：成功率 + 95% cluster bootstrap CI、每任务胜/负、精确符号检验 + 配对置换检验（Holm 校正），以及成功所需调用/仿真、成本。成功率在难任务上可能接近，**效率（仿真/调用/成本）也是组件贡献的证据**（例如 intent 空间可能主要节省仿真），应同时报告。
- **诚实规则**：组件被称为“necessary/essential”需要配对检验支持；否则写“contributes”（给点估计和胜负）或“no measurable effect”。若某组件在功效充足的实验中无贡献：**先问用户**（交接方推荐：删除/合并该组件、简化方法并重写方法章节）。禁止事后挑任务子集、挑 seed、换指标。
- **已知风险**：E4 显示诊断本身不提升定位；早期消融中 w/o diagnosis 不差于 SPECTRA。诊断的价值若存在，最可能体现在“refine 还是 edit”的决策上，即调用数/仿真数，以及较弱骨干（Haiku）上。可以在 Haiku 上也跑 w/o diagnosis 作为**预先声明**的次要分析（先写进 `EXPERIMENT_LOG.md` 再跑）。

### 7.4 分析与论文
1. `bash scripts/finalize_paper.sh`（顺序：analyze → comparisons → pvt_failures → failure_analysis → spectra_failures → prediction_accuracy → e4_tests → make_tables → bench_stats → make_figures → paper_numbers → 编译）。新增实验后需在 `scripts/comparisons.py`、`scripts/make_tables.py`、`scripts/paper_numbers.py`、`scripts/make_figures.py` 中加入新方法的标签和块。
2. 写解释性文字：消融（`\AblationText` 之后）、PVT（`\PVTText`、`\PVTFailSentence`、`\MCSentence` 之后）、骨干（`\ScalingText`）、外部基准（新小节）。数字只能用宏。
3. 结论段的比较性措辞按合同 A7 修改（目前“reliable where it matters”在 vs direct 不显著时不允许）。
4. 页面：正文 ≤ 8 页；可用空间放族热力图（`figs/E1_families.pdf` 已生成但未用）、外部基准表。
5. 方法若因消融结果被简化，需同步改：`sections/method.tex`、`figs/overview.tex`、摘要、引言贡献列表、`NARRATIVE_REPORT.md`。

### 7.5 ARIS 关卡（全部用新开的审稿会话；提示已写好）
```bash
python3 tools/aris_review.py --skill auto-review-loop --prompt-file .aris/prompts/w2_round2.md --out review-stage/ROUND2_REVIEW.md
python3 tools/aris_review.py --skill paper-claim-audit --prompt-file .aris/prompts/w3_claim_audit.md --out paper/PAPER_CLAIM_AUDIT.md
python3 tools/aris_review.py --skill kill-argument --prompt-file .aris/prompts/w3_kill_attack.md --out paper/KILL_ATTACK.md
python3 tools/aris_review.py --skill kill-argument --prompt-file .aris/prompts/w3_kill_defense.md --out paper/KILL_DEFENSE.md
```
- W2 循环直到评分 ≥ 6 且 verdict 为 ready/almost；每轮把意见与处理写进 `review-stage/AUTO_REVIEW.md`。
- 按合同 `paper/PAPER_ACCEPTANCE_CONTRACT.md` 逐条（A1–A20）检查并记录结果（Phase 6 gate）。
- bib 有改动则重做引用审计（`paper/CITATION_AUDIT.md`）。
- 审稿者改为 GPT 家族（0.5 节）：用与执行者**不同**的 GPT 模型、每次新开会话、只读；同族审稿 → ARIS 记为 provisional；在 `AUTO_REVIEW.md` 和 `.aris/reviewer.json` 记录实际模型身份。上面的命令在 `tools/aris_review.py` 改为 GPT 后端后使用。

### 7.6 投稿准备
- 匿名代码：在 anonymous.4open.science 用本仓库创建匿名镜像（需用户 GitHub 登录），把链接写进结论段（目前写的是“an anonymised artifact accompanies this submission”）。
- 检查：双盲（无作者信息、无非匿名 URL、无自引暴露）、ACM CCS 与关键词已加、`main.log` 无未定义引用/字体、overfull ≤ 5 pt、正文 ≤ 8 页。
- 最终 `git tag submission-iccad27` 并 push。

---

## 8. 规则与经验教训（踩过的坑，务必避免）
1. **预算一致性**：鲁棒 run 统一 600 次条件评估。1200→600 的截断评分**不等价**（提示里会显示剩余预算；Gen+TPE 按剩余预算分配每轮试验数），所以旧 run 已归档并原生重跑。新实验不得混用不同预算。
2. **单一方法版本**：E1 中途修过一次 harness（迭代提示未重复 API、沙箱过严），修后**所有 SPECTRA/SPECTRA-min 结果全部重跑**，baseline 不受影响保留。以后任何影响某方法的代码改动，都要对该方法全部重跑或另起实验名。
3. **不要在评测集上调方法**（例如修 PVT 环停滞问题后重跑同一批任务）。真要改，新开实验并在新任务或留出集上验证。
4. **主终点**（T3 ∪ 鲁棒）是在中期审稿时固定的（E1 约完成 1/3 时），论文中不得称“pre-registered”。
5. **公共任务集**：所有 E1 统计只用每个方法都完成的任务（`analyze.load_common`）；消融/PVT/骨干用 `comparisons.py` 的匹配块。
6. **tier 定义唯一**：`analyze.TIER_GROUPS`（Robust = 所有鲁棒任务，含 designer 鲁棒任务；T1/T2/T3/Designer 只含名义任务）。
7. **不要给智能体泄漏信息**：任务 id 是不透明的；提示中不能出现模板名/层级。
8. **CPU 过载**：用全局 flock 槽（`SPECTRA_GLOBAL_SIM_SLOTS`）；暂停的进程会占着槽（`kill -STOP` 的进程持有的 flock 不会释放）。
9. **容器重启**：用 `scripts/relaunch_all.sh` 恢复；LLM/仿真缓存保证可续跑。
10. **论文措辞**：比较性结论需要 Holm 校正后 p<0.05 且方向正确；否则只写点估计 + CI + 胜负。负面结果（E4 零结果、二阶量预测差、鲁棒基准源失败）必须保留在正文。
11. **基线命名**：只能叫 “AnalogCoder-style”“AnalogCoder-Pro-style” 复现，不能说是原系统。
12. **不要编造文献事实**：对比表与相关工作中的数字只能来自 `docs/refs/LIT_SURVEY.md` 中已核实的条目。
13. **Commit 规范**：每完成一块就 commit + push（`git push -u origin main`，网络失败重试 4 次指数退避）。

---

## 9. 关键文件的生成关系（论文中的每个数字从哪里来）
| 论文元素 | 生成脚本 | 输入 |
|---|---|---|
| `numbers.tex` 全部宏（含摘要主结论、PVT 失败句、MC 句、失败模式句、E4 句） | `scripts/paper_numbers.py` | `results/E1_summary.json`、`comparisons.json`、`E4_*`、`E4_tests.json`、`pvt_failure_conditions.json`、`mc_yield.json`、`E1_spectra_failure_modes.json`、`E1_spectra_prediction_accuracy.json`、`E1_failures.json`、`data/bench/*` |
| `tables/main.tex`、`fault.tex`、`ablation.tex`、`pvt.tex`、`scaling.tex` | `scripts/make_tables.py` | `E1_summary.json`、`comparisons.json`、`E4_*`、`mc_yield.json` |
| `tables/bench_stats.tex` | `scripts/bench_stats.py` | `data/bench/*` |
| `tables/families.tex`、`tables/compare.tex` | 手写（基准描述 / 文献事实） | `docs/refs/LIT_SURVEY.md` |
| `figs/E1_tiers.pdf`、`E1_anytime*.pdf`、`E1_families.pdf` | `scripts/make_figures.py` | `results/raw/E1`（公共任务集） |
| `figs/program.tex` | 手写摘录，**逐字**取自 `results/raw/E1/spectra/opamp-09/s0.json` 的最终程序 | — |

---

## 10. 交接给 GPT 的特别说明
1. **模型**：执行者、实验中的智能体 LLM、ARIS 审稿者全部为 GPT 家族（0.5 节）。主实验所有方法用同一个 GPT 主模型；骨干研究（E5g）用同家族的一个更小模型，再加旧的 Claude Opus/Haiku 结果作为跨厂商对照（部分覆盖）。
2. **结果隔离**：GPT 结果写入新的实验目录（`E1g` 等）；分析脚本参数化实验名；论文主表只用 GPT 结果；跨厂商对照只在匹配任务上报告。LLM 缓存键含模型 ID，不会串用。
3. **论文改动**：
   - 设置段的模型说明、摘要（“With the same LLM …”不受影响）、局限段（“All LLM results use one model family; the backbone study varies model size, not provider”需改：现在有跨厂商对照）、局限段关于审稿同族的一句；
   - 合同 A8/A15 的相应文字；
   - E4 的解释（Opus/Haiku 结果变为补充）。
4. **提交署名**：本仓库之前的提交带有 `Co-Authored-By: Claude Opus 5.5` 尾注；GPT 的提交按其自身规范署名即可。
5. **未决的用户问题**（动手前先问用户）：
   - (a) 用哪个 GPT 模型做主骨干 / 审稿、token 预算上限、是否用多个并行会话（7.2）；
   - (b) 消融显示无贡献的组件如何处理（7.3）。
6. **执行顺序建议**：0.5 → 7.0（GPT 后端 + 冒烟测试）→ E1g 主终点 3 seeds → E2g 消融（3 seeds，34 个难任务）→ E3g → 新 baseline → E5g（小 GPT 模型 + Claude 对照）→ 外部基准（AnalogGym）→ MC → 7.4 → 7.5 → 7.6。

## 11. 合同（`paper/PAPER_ACCEPTANCE_CONTRACT.md`）当前满足情况速览
| 条目 | 状态 |
|---|---|
| A1 格式/页数/匿名 | 满足（需最终复查） |
| A2 无未定义引用/overfull | 满足（最近一次编译 0 个 >5 pt） |
| A3 数字可追溯 + 新鲜度 | 机制已就位（`finalize_paper.sh`）；最终需重跑并确认无 diff |
| A4 生成器/tier/公共任务集 | 满足 |
| A5 程序清单逐字摘录 | 满足 |
| A6 主终点表述 + 覆盖率 | 满足（宏 `\NPrimaryTasks`/`\NPrimaryAll`/`\NPrimaryFamilies`） |
| A7 比较性措辞 | 摘要已自动化；结论段待按最终数据修改 |
| A8 设置说明（同 LLM、LUT 不对称、缓存） | 需随 GPT 切换改写模型说明 |
| A9 负面结果 + E4 Haiku 来自同一案例池 | 机制满足；需重生成 Haiku 汇总（7.0 第 4 步） |
| A10 消融措辞 | 待最终数据 |
| A11 PVT 小节 | 待 E3 |
| A12 无截断评分 | 分析层已强制；需完成重跑 |
| A13 MC 文件 + 样本差异检查 | 待 MC |
| A14 指标都有表 | 满足（主表含 kTok、$/run；不报告 wall-clock） |
| A15 局限 | 满足（扩展后需更新已删除的分支列表） |
| A16 被放弃假设的范围 | 满足（无全角对比、无跨骨干泛化、无不可行检测声明） |
| A17 baseline 命名 | 满足 |
| A18 基准描述 | 满足 |
| A19 相关工作 + 引用审计 | 满足 |
| A20 可复现性 | 满足；匿名链接待用户创建 |

---

## 11. Execution update after handoff (2026-11-16 client session)

The user confirmed **GPT-5 mini** as the single main experiment backbone and explicitly removed the token/US-dollar
cap. This resolves the open choice in Sections 7.0, 7.2 and 10. New LLM calls now use the OpenAI Python client;
Claude and the legacy `opus`/`haiku` aliases are rejected. The cache and `results/llm_usage.jsonl` schema are kept,
with configurable per-million-token prices. The ARIS bridge is GPT-only and writes a bounded read-only context
manifest for each fresh review. New experiment names are `E1g`, `E2g`, `E3g`, `E4g`, and `E5g`; historical Claude
results remain isolated under their original names.

The local worktree is `E:\\CodexProjects\\spectra-analog-agent`. The server checkout is
`/root/autodl-tmp/spectra-analog-agent` on westc; `/autodl-fs/data` is intentionally not used because it is nearly
full and `/autodl-pub/data` is read-only on this instance. No local C: or D: experiment directory is used. The
three-way commit hash is recorded only after local checks pass and the changes are pushed.

## 12. 命令速查
（以下命令按 GPT-5 mini 更新；使用新实验名 `E1g` 等，历史 Claude 目录只作补充。）
```bash
# 跑实验（可续跑）
PYTHONPATH=. SPECTRA_GLOBAL_SIM_SLOTS=6 SPECTRA_SIM_CONCURRENCY=4 SPECTRA_LLM_CONCURRENCY=14 \
  python -m scripts.run_bench --exp E1g --model gpt-5-mini --methods spectra,direct --seeds 0,1,2 --tasks data/bench/E1_primary.jsonl --workers 16
# 可用方法名：spectra, spectra_min, spectra_nodiag, spectra_nointent, spectra_norefine, spectra_noknow,
#   spectra_pvt_nominal, spectra_pvt_all, direct, direct_noknow, genbo, genbo_cmaes, genbo_full, oracle_cmaes
#   （--model gpt-5-mini；方法目录名为 method@gpt-5-mini）
python -m scripts.analyze --exp E1          # 打印汇总并写 results/E1_summary.json
bash scripts/finalize_paper.sh              # 重生成一切并编译
python -m scripts.mc_yield 100              # 失配 MC
bash scripts/relaunch_all.sh                # 容器重启后恢复所有实验链
```
