You are simulating a hostile ICCAD program-committee member. This is a kill-argument adversarial check: do NOT give a
balanced review. Read paper/main.tex, paper/sections/*.tex, paper/tables/*.tex, paper/figs/*.tex, paper/numbers.tex
(and the result files under results/ and code under spectra/ and scripts/ if you need to verify something). Do not
read review-stage/, idea-stage/, refine-logs/, .aris/, NARRATIVE_REPORT.md or paper/*CONTRACT* — this must be a
fresh pass on the paper and its evidence.
Construct the single strongest argument for rejecting this paper, ~200 words (max 250), as one coherent argument a
senior area chair would find decisive. Pick the most damaging combination of: claim-vs-evidence gap, scope overclaim
in title/abstract, unfair or weak baselines, benchmark validity (self-made tasks, saturation, certificates), statistical
weakness, novelty relative to prior LLM analog agents, reproducibility.
Output: "## Attack memo" with the ~200-word argument, then "## Atomic points" listing 3-7 atomic rejection points
(one line each, numbered).
