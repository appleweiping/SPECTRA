"""Resumable, parallel benchmark runner.

python -m scripts.run_bench --exp E1 --methods spectra,direct,genbo --seeds 0,1,2 [--tasks file] [--filter regex]
       [--model opus] [--workers 6]
Each run -> results/raw/<exp>/<method>/<task_id>/s<seed>.json, including an INDEPENDENT final verification of the
returned netlist at TT and (for robust tasks) at all 45 PVT conditions (not charged to the method's budget).
"""
import argparse, json, re, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from spectra.paths import ROOT
from spectra.agent.common import Budget
from spectra.sim.evaluate import evaluate, NOMINAL, PVT

RAW = ROOT / "results" / "raw"


def budget_for(task):
    return Budget(llm_calls=12, sims=600 if task.get("robust") else 300)


def make_runner(method, model):
    from spectra.agent.spectra_agent import Spectra, Config
    from spectra.baselines.direct import run_direct
    from spectra.baselines.genbo import run_genbo
    from spectra.baselines.oracle import run_oracle
    abl = {"spectra": Config(), "spectra_nointent": Config(use_intent=False), "spectra_nodiag": Config(use_diag=False),
           "spectra_norefine": Config(use_refine=False), "spectra_noknow": Config(use_knowledge=False),
           "spectra_pvt_all": Config(pvt_strategy="all_corners"), "spectra_pvt_nominal": Config(pvt_strategy="nominal_only"),
           "spectra_min": Config(minimal=True)}
    if method in abl:
        return lambda task, seed: Spectra(task, model=model, seed=seed, cfg=abl[method], budget=budget_for(task),
                                          method=method).run()
    if method == "direct":
        return lambda task, seed: run_direct(task, model=model, seed=seed, budget=budget_for(task))
    if method == "genbo":
        return lambda task, seed: run_genbo(task, model=model, seed=seed, budget=budget_for(task))
    if method == "genbo_full":     # fairness variant: regenerate until calls run out + adaptive PVT corners
        return lambda task, seed: run_genbo(task, model=model, seed=seed, budget=budget_for(task), rounds=12,
                                            method="genbo_full", adaptive_pvt=True)
    if method == "direct_noknow":
        def _dn(task, seed):
            import spectra.agent.common as C
            orig = C.KNOWLEDGE
            return run_direct(task, model=model, seed=seed, budget=budget_for(task), method="direct_noknow",
                              knowledge_override="(none provided)")
        return _dn
    if method == "genbo_cmaes":
        return lambda task, seed: run_genbo(task, model=model, seed=seed, budget=budget_for(task), optimizer="cmaes",
                                            method="genbo_cmaes")
    if method.startswith("oracle_"):
        opt = method.split("_", 1)[1]
        return lambda task, seed: run_oracle(task, optimizer=opt, seed=seed, budget=budget_for(task))
    raise ValueError(method)


def verify(task, netlist):
    if not netlist:
        return {"tt_pass": False, "pvt_pass": False if task.get("robust") else None, "tt_score": None}
    ev = evaluate(task, netlist)
    out = {"tt_pass": bool(ev.passed), "tt_score": ev.score, "tt_metrics": ev.summary()["per_cond"].get("tt_27C_1.8V"),
           "status": ev.status, "errors": ev.errors[:3]}
    if task.get("robust"):
        evP = evaluate(task, netlist, conds=PVT)
        out["pvt_pass"] = bool(evP.passed)
        out["pvt_score"] = evP.score
        out["pvt_fail_conds"] = [c for c, chk in evP.checks.items() if not all(v[1] for v in chk.values())]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--methods", required=True)
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--tasks", default=str(ROOT / "data" / "bench" / "tasks.jsonl"))
    ap.add_argument("--filter", default="")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    tasks = [json.loads(l) for l in open(a.tasks)]
    if a.filter:
        tasks = [t for t in tasks if re.search(a.filter, t["id"])]
    seeds = [int(s) for s in a.seeds.split(",")]
    methods = a.methods.split(",")
    jobs = []
    for t in tasks:          # interleave methods so partial results are comparable and load is mixed
        for s in seeds:
            for m in methods:
                tag = m if a.model == "opus" or m.startswith("oracle") else f"{m}@{a.model}"
                out = RAW / a.exp / tag / t["id"] / f"s{s}.json"
                if not out.exists():
                    jobs.append((m, tag, t, s, out))
    print(f"{len(jobs)} runs to do", flush=True)
    runners = {m: make_runner(m, a.model) for m in methods}

    def do(job):
        m, tag, t, s, out = job
        t0 = time.time()
        try:
            res = runners[m](t, s)
        except Exception as e:
            res = {"status": "crash", "error": traceback.format_exc()[-3000:], "final_netlist": None}
        res["verify"] = verify(t, res.get("final_netlist"))
        res["task_meta"] = {"family": t["family"], "tier": t.get("tier"), "robust": t.get("robust", False),
                            "infeasible": t.get("infeasible", False)}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, default=float))
        return f"{tag:22s} {t['id']:34s} s{s} {res.get('status'):18s} tt={res['verify']['tt_pass']} " \
               f"pvt={res['verify'].get('pvt_pass')} calls={res.get('calls')} sims={res.get('sims')} " \
               f"${res.get('cost_usd', 0):.2f} {time.time() - t0:.0f}s"

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(do, j) for j in jobs]
        for f in as_completed(futs):
            try:
                print(f.result(), flush=True)
            except Exception as e:
                print("ERROR", e, flush=True)


if __name__ == "__main__":
    main()
