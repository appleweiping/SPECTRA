ARIS Gate 1 (idea-discovery → research-review + novelty-check). Target venue: ICCAD (ACM/IEEE, 8 pages, double blind).

Read these files yourself (repository root is your cwd):
- RESEARCH_BRIEF.md
- idea-stage/IDEA_REPORT.md
- refine-logs/FINAL_PROPOSAL.md
- refine-logs/EXPERIMENT_PLAN.md
- docs/refs/LIT_SURVEY.md (at least §0, §2, §4, §5; consult entries for AaLLM, AnalogSAGE, SAFTAC, AnalogScout, AnalogCoder-Pro)
- skim the code under spectra/sim/ and spectra/bench/templates.py to judge feasibility of the evaluation substrate.

Act as a senior ICCAD PC member and an adversarial novelty checker. Deliver:
1. Novelty assessment vs. the closest 5 prior works (be concrete: what is genuinely new, what is incremental).
2. Scores 1–10: novelty, significance, technical soundness of the plan, feasibility with the stated compute,
   expected ICCAD acceptance if executed well.
3. The 5 most serious weaknesses / likely reviewer attacks, each with a concrete minimum fix.
4. Experiments that are missing or mis-specified (baselines, budgets, statistics, benchmark construction leakage —
   e.g. specs derived from the same templates the oracle baseline uses).
5. Verdict: PROCEED / PROCEED-WITH-CHANGES / REVISE-IDEA, and the 3 most important changes.
Be specific and quantitative. Do not be polite for its own sake.
