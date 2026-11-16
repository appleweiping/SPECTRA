Review complete. Verdict first: the simulator and verification plumbing are mostly sound (pilot metrics confirm `wrdata` layout and `$&i(vdd)` parsing work, and success is gated on an independent re-simulation of the returned netlist). But there are three things that would invalidate E1 as currently coded: a reference-topology leak in every LLM prompt, a wrong-polarity op-amp template whose consequences are silently swallowed by spec derivation, and budget caps that are not enforced. Details below, ranked.

## Findings (ranked by severity)

**1. Reference topology and tier leak to every LLM method.** Task ids are built as `{family}-{template}-t{tier}` (scripts/build_bench.py:208) and injected verbatim as `# Task {task_id}` into PLAN, ITERATE, DIRECT_PLAN, DIRECT_ITERATE, GENBO_PLAN and GENBO_RETRY (spectra/agent/prompts.py:36, 58, 91, 113, 128, 148). Every LLM method is told "miller2", "fcasc", "strongarm", "sk_lpf3", "app_integ" and whether the task is T1/T2/T3. This defeats the "topology selection" claim and the circularity defence in GATE1. Fix: opaque ids (e.g. `opamp-017`) in build_bench, and never format `task["id"]` into prompts. Same for `designer_tasks.jsonl` ids that embed the family (harmless, but be consistent).

**2. The 5T-OTA template has vinp as the inverting input; the evaluator never checks polarity; spec derivation hides the damage.** In `ota5t` (spectra/bench/templates.py:32-35) M1 (vinn) drives the mirror diode and M2 (vinp) drives vout, so vout falls when vinp rises. The archive confirms it: 504/504 ota5t rows have `_inverting: true`, 381/504 have `slew: null` (the X2 unity buffer at tb_opamp.py:88 is in positive feedback). The pilot task `opamp-ota5t-t3-02` ships a reference with `_inverting: true` and no slew/settle specs because `derive_spec` returns None for null metrics and they are silently dropped (build_bench.py:53-54, 199-200). Consequences: (a) opamp tasks derived from ota5t never carry slew/settle specs, (b) any method returning a wrong-polarity op-amp passes gain/UGBW/PM/CMRR because `_inverting` is stored as a private key and is never a spec (tb_opamp.py:120). The X1 servo still "measures" an unstable equilibrium, so the numbers look fine. `fcasc` is worse: 173/173 rows inverting, 2/173 sane, 160/173 slew null. By inspection fcasc should be non-inverting, so its bias network is probably not functioning; either way its 4 slots (one robust) cannot be built from 2 sane rows. Also `sf.jsonl` and all `cm_psrc` archives have 0 sane rows, so those slots fail. Fix: swap vinp/vinn in ota5t; debug fcasc (check pc/nc bias op points); add `{"metric": "polarity_ok", ...}` for opamp (fail when `_inverting`) to EXTRA_SPECS and to the opamp sanity profile; make build_bench abort a slot when a core metric is None instead of dropping it.

**3. Simulation budgets are not enforced and several paths exceed them.**
- `Spectra.robust_stage` runs a 45-condition PVT verify with no `sims_left()` check (spectra_agent.py:179). Same in direct.py:51 and genbo.py:100. A nominal pass at sims=2999 ends at 3044.
- `Spectra.refine` checks `used + len(conds) <= budget` but then evaluates a whole CMA population (spectra_agent.py:105-132), overshooting by up to (popsize−1)·len(conds); with 6+ params popsize>8, so the `chunk = sims_left − 45` reserve (line 192) is not sufficient.
- The oracle's CMA loop evaluates full batches after the `done()` check (spectra/opt/sizing.py:133-136), overshooting by up to popsize−1 evaluations ×3 corners.
- `Ctx.evaluate` never refuses an over-budget call (common.py:51-54), `run_bench.verify` does not record the budget, and `analyze.load` never checks `sims <= budget` or `calls <= 12` (analyze.py:26-32).
Fix: in `Ctx.evaluate`, if `self.sims + len(conds) > budget.sims` return a synthetic failed EvalResult (status "budget") and log it; in `analyze.load` mark `success=False` when sims or calls exceed the task budget; in `refine`, size the population to `min(popsize, (budget−used)//len(conds))` or stop before asking.

**4. Oracle is handicapped on robust tasks.** `run_oracle` optimises over 3 fixed corners with `stop_on_pass=True`, then does one full-PVT check and stops even with ~90% of the budget unused (spectra/baselines/oracle.py:22-31). SPECTRA iterates up to 3 refine/verify rounds with adaptive corners. The "oracle pass rate under the same budget" headline is therefore biased in SPECTRA's favour on the robust tier. Fix: loop while budget remains: on PVT failure, append the worst failing conditions to `conds` and continue the optimiser from `best_x` (mirrors `robust_stage`).

**5. Documented LUT API crashes.** DSL_DOC advertises `lut.at(corner, temp)` for −40/27/125 °C (prompts.py:17, dsl.py:61-63), but `data/lut/` only contains `*_27.npz`; `_load` (lut.py:22) raises FileNotFoundError inside the sandboxed program, which surfaces as "PROGRAM ERROR" and burns an LLM call. This hurts SPECTRA and makes the PVT-aware ablation meaningless until the LUTs exist. Fix: generate the 10 missing LUTs or remove the temperature argument from the doc.

**6. Race on budget counters.** `Ctx.evaluate` does `self.sims += ...` and updates `self.best` from 4 worker threads (spectra_agent.py:119, 156; common.py:54-60) without a lock. Lost increments undercount charged simulations. `SIM_COUNTER` (ngspice.py:71-72, 102-103) has the same issue but is cosmetic. Fix: a `threading.Lock` in `Ctx`.

**7. Settling time is measured to the ideal target, not the actual final value.** `slew_settle` uses `|v − vhi| > tol·step` with vhi = vcm ± a (measure.py:73-78, tb_opamp.py:138-143). With a 0.4 V step and 1% tolerance, any buffer with gain error plus offset above 4 mV (gain below ~50 dB, or |Vos| > ~3 mV) returns `settle=None` and violation 2.0 even when it settles in nanoseconds. Specs were derived with the same measurement, so references pass, but the metric penalises legitimate topologies. Fix: settle to the mean of the last 10% of the window; report `settle` and a separate `gain_error`.

**8. Robust-tier "refine" action optimises nominal only.** After a PVT failure, the LLM's `refine` request runs `self.refine([NOMINAL], ...)` (spectra_agent.py:340-341), which exits after one generation because nominal already passes, then re-enters `robust_stage` (another 45 sims). Fix: for robust tasks use the current active corner set.

**9. `refine` can replace the current point with a worse one.** CMA-ES never evaluates u0, yet `self.params = best[1]` unconditionally (spectra_agent.py:101-107, 133-134). Fix: seed the first population with u0 or compare against the incumbent score.

**10. The "sandbox" is not one.** `sandbox_worker` executes LLM code with full builtins, the repo on PYTHONPATH, filesystem and network (sandbox_worker.py:15-19, sandbox.py:19-22). A program could import `spectra.sim.evaluate` (uncharged simulations) or read `data/bench/tasks.jsonl`, which contains `ref.x` and `ref_metrics`. Fix: restrict `__builtins__` (no `__import__`, `open`), reject programs containing `import`/`open(`/`exec`, and log program hashes for post-hoc audit.

**11. Benchmark difficulty.** All 29 pilot runs succeeded, including `direct` in 1-4 calls and the robust task in 3 calls (results/pilot/pilot_run.log). As built, T2/T3 will likely saturate and E1 will have no power to separate methods. Not a code bug, but the tier margins (build_bench.py:31-33) need to tighten, or the comparison must move to the oracle-unmet controls and cost curves.

**Minor / cosmetic.**
- `parse_value` treats `1M` as milli per SPICE (netlist.py:25-26); LLM-written `1M` for 1 MΩ becomes an ERC error that costs the direct baseline a call. Lines 32-35 are dead code. Consider accepting `M` as mega when the device is R/C and value < 0.1 would result.
- `W_MAX_TOTAL` ignores `m` (netlist.py:205-210); W=5000 with m=200 passes ERC.
- A passing design found during `sensitivities` updates `ctx.best` and `first_pass_sims` (common.py:57-60) but the agent does not notice it; the final-netlist fallback credits it anyway. Harmless for fairness, but the anytime curve then uses total sims, not first_pass_sims (analyze.py:111).
- Direct's ITERATE prompt does not show remaining calls while SPECTRA's does (prompts.py:58 vs 113).
- `claude -p` runs with cwd=/tmp but still loads the user-level CLAUDE.md (llm.py:41-50); confirm it contains no project notes.
- analyze.py:78 summarises tiers 1/2/3/D but controls use tier "C" (build_controls.py:43).
- E4 top-k compares element names case-sensitively (fault_injection.py:174-175).
- run_bench.py:5-6 docstring says 17 PVT conditions; code uses 45.

## MUST FIX before E1
1. Opaque task ids; stop formatting `task["id"]` into any prompt (prompts.py, build_bench.py:208).
2. Fix ota5t polarity, debug fcasc/sf/cm_psrc templates, add an opamp polarity spec and sanity check, and make build_bench refuse slots with None core metrics; then rebuild archives and tasks.
3. Hard budget cap in `Ctx.evaluate`, population sizing in `refine`, and a `sims/calls <= budget` check in `analyze.load`.
4. Oracle robust loop: continue optimising with failing corners instead of stopping after the first 3-corner pass.
5. Generate the −40/125 °C LUTs or remove `lut.at(temp)` from DSL_DOC.
6. Lock around `Ctx.sims`/`Ctx.best`.

## Should fix
- Settling time relative to the actual final value (measure.py).
- Robust-task `refine` on the active corner set; seed CMA with the incumbent.
- Restrict the program sandbox and audit programs for imports.
- Tighten tier margins or re-plan E1 around controls, given pilot saturation.
- `1M` parsing, W·m limit, tier "C" in analyze, case-insensitive E4 scoring, stale "17 PVT" docstring, direct prompt calls-left parity.