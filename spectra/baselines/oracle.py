"""Expert-topology oracle: optimise the benchmark's own reference template (privileged information).

Same simulation budget as the agents. For robust tasks it mirrors SPECTRA's PVT loop: optimise over an active
condition set, verify on the full 45-condition grid, add the two worst failing conditions, continue from the
incumbent until the budget is spent.
"""
from __future__ import annotations

from ..agent.common import Ctx
from ..bench.templates import T
from ..opt.sizing import OPTIMIZERS
from ..sim.evaluate import NOMINAL, PVT, cond_name, evaluate
from .genbo import FIXED_CORNERS


def run_oracle(task, optimizer="cmaes", seed=0, budget=None, method=None):
    method = method or f"oracle_{optimizer}"
    ctx = Ctx(task=task, model="none", seed=seed, method=method)
    if budget:
        ctx.budget = budget
    t = T[task["ref"]["template"]]
    build, vars_ = t["build"], t["vars"]
    robust = task.get("robust", False)
    conds = list(FIXED_CORNERS) if robust else [NOMINAL]
    status, final, x0 = "budget_exhausted", None, None
    for rnd in range(8):
        reserve = len(PVT) if robust else 0
        n = (ctx.sims_left() - reserve) // len(conds)
        if n < 4:
            break
        res = OPTIMIZERS[optimizer](task, build, vars_, budget=n, conds=conds, seed=seed + rnd, x0=x0, stop_on_pass=True)
        ctx.sims += res.n_evals * len(conds)
        if res.best_x:
            x0, final = res.best_x, build(res.best_x)
        if not (res.best_eval is not None and res.best_eval.passed):
            break
        if ctx.first_pass_sims is None and not robust:
            ctx.first_pass_sims = ctx.sims
        if not robust:
            status = "success"
            break
        evP = evaluate(task, final, conds=PVT)
        ctx.sims += len(PVT)
        if evP.passed:
            status = "success"; ctx.first_pass_sims = ctx.sims
            break
        worst = sorted(PVT, key=lambda c: -sum(v[2] for v in evP.checks[cond_name(c)].values()))
        for c in worst[:2]:
            if c not in conds and len(conds) < 6:
                conds.append(c)
    return {"status": status, "final_netlist": final, **ctx.summary(), "events": []}
