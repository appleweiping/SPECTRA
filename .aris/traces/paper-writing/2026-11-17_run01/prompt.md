You are negotiating the acceptance contract for an ICCAD paper BEFORE its final revision is written (experiments are
still running; interim numbers exist). Read these files directly in the repository:
- Proposed contract: paper/PAPER_ACCEPTANCE_CONTRACT.md
- Evidence inventory: NARRATIVE_REPORT.md, EXPERIMENT_LOG.md, refine-logs/FINAL_PROPOSAL.md
- Current draft: paper/main.tex and paper/sections/*.tex, paper/numbers.tex, paper/tables/*.tex
- Generators: scripts/analyze.py, scripts/paper_numbers.py, scripts/make_tables.py

Push back on the contract, not the paper: (a) assertions that are untestable or vague — demand a checkable rewrite;
(b) missing assertions — claims in the narrative/draft that no assertion covers, numbers with no traceability
assertion, foreseeable overclaim risks with no scope assertion (e.g. deviations between FINAL_PROPOSAL and the
executed protocol); (c) assertions the evidence inventory cannot possibly satisfy — flag them now.
Keep it in scope: this is a research workflow, not a security audit; no hashing schemes or speculative machinery.
Say plainly when an assertion is fine. Do not manufacture findings.
End with exactly one line:
CONTRACT_ACCEPTED: yes    or    CONTRACT_ACCEPTED: no
followed by your numbered revision demands if no.
