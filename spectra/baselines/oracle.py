"""Expert-topology oracle: optimise the benchmark's own reference template (privileged information)."""
from __future__ import annotations

from ..agent.common import Ctx
from ..bench.templates import T
from ..opt.sizing import OPTIMIZERS
from ..sim.evaluate import NOMINAL, PVT
from .genbo import FIXED_CORNERS


def run_oracle(task, optimizer="cmaes", seed=0, budget=None, method=None):
    method = method or f"oracle_{optimizer}"
    ctx = Ctx(task=task, model="none", seed=seed, method=method)
    if budget:
        ctx.budget = budget
    t = T[task["ref"]["template"]]
    build = t["build"]
    if task["ref"].get("build_kwargs"):
        kw = task["ref"]["build_kwargs"]
        build = lambda x, _b=t["build"]: _b(x, **kw)
    robust = task.get("robust", False)
    conds = FIXED_CORNERS if robust else [NOMINAL]
    n = max(1, ctx.budget.sims // len(conds) - (len(PVT) // len(conds) if robust else 0))
    res = OPTIMIZERS[optimizer](task, build, t["vars"], budget=n, conds=conds, seed=seed, stop_on_pass=True)
    ctx.sims = res.n_evals * len(conds)
    status, final = "budget_exhausted", build(res.best_x) if res.best_x else None
    if res.best_eval is not None and res.best_eval.passed:
        if robust:
            from ..sim.evaluate import evaluate
            evP = evaluate(task, final, conds=PVT); ctx.sims += len(PVT)
            status = "success" if evP.passed else "budget_exhausted"
        else:
            status = "success"
        ctx.first_pass_sims = (res.first_pass_eval or 0) * len(conds)
    return {"status": status, "final_netlist": final, **ctx.summary(), "events": []}
