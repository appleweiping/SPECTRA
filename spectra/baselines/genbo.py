"""AnalogCoder-Pro-style baseline: LLM proposes a (parameterised) topology, TPE (Optuna) sizes it with SPICE.

Up to `rounds` regenerations with feedback of the best TPE result. Same LLM and simulation budget as SPECTRA.
For PVT-robust tasks the TPE objective is the worst case over a fixed practitioner corner set
(tt/27C, ss/125C, ff/-40C) followed by full PVT verification.
"""
from __future__ import annotations

import re

from ..agent import diagnose, llm
from ..agent.common import Ctx, task_texts
from ..agent.prompts import GENBO_PLAN, GENBO_RETRY, SYSTEM_DIRECT
from ..opt.sizing import Var
from ..sim.evaluate import NOMINAL, PVT

FIXED_CORNERS = [NOMINAL, {"corner": "ss", "temp": 125, "vdd": 1.8}, {"corner": "ff", "temp": -40, "vdd": 1.8}]


def _parse(text):
    net = llm.extract_block(text, "spice")
    js = llm.extract_json(text) or {}
    params = js.get("params", {}) if isinstance(js, dict) else {}
    vars_, init = [], {}
    for k, v in params.items():
        try:
            i0, lo, hi = float(v[0]), float(v[1]), float(v[2])
        except Exception:
            continue
        if hi <= lo or lo <= 0:
            continue
        vars_.append(Var(k, lo, hi, log=True)); init[k] = min(max(i0, lo), hi)
    return net, vars_[:16], init


def _fill(net, x):
    def rep(m):
        k = m.group(1)
        return f"{x[k]:.6g}" if k in x else m.group(0)
    return re.sub(r"\{(\w+)\}", rep, net)


def run_genbo(task, model="gpt-6.1-sol", seed=0, budget=None, rounds=3, method="genbo", optimizer="tpe", adaptive_pvt=False):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    ctx = Ctx(task=task, model=model, seed=seed, method=method)
    if budget:
        ctx.budget = budget
    t = task_texts(task)
    robust = task.get("robust", False)
    conds = FIXED_CORNERS if robust else [NOMINAL]
    text = ctx.ask(GENBO_PLAN.format(**t), SYSTEM_DIRECT, "plan")
    status, final = "budget_exhausted", None
    best_overall = (float("inf"), None, None)
    for rd in range(rounds):
        net, vars_, init = _parse(text)
        best = (float("inf"), None, None)
        if net:
            per_round = max(len(conds), (ctx.sims_left()) // (rounds - rd))
            if optimizer == "tpe":
                sampler = optuna.samplers.TPESampler(seed=seed + rd, n_startup_trials=10, multivariate=True)
                study = optuna.create_study(direction="minimize", sampler=sampler)
                if init:
                    study.enqueue_trial(init)
            else:
                import cma
                u0 = [v.to_unit(init.get(v.name, (v.lo * v.hi) ** 0.5)) for v in vars_] or [0.5]
                es = cma.CMAEvolutionStrategy(u0, 0.25, {"bounds": [0, 1], "seed": seed + rd + 1, "verbose": -9})
                pending = []
            used = 0
            while used + len(conds) <= per_round and ctx.sims_left() >= len(conds):
                if optimizer == "tpe":
                    tr = study.ask()
                    x = {v.name: tr.suggest_float(v.name, v.lo, v.hi, log=True) for v in vars_}
                else:
                    if not pending:
                        sols = es.ask(); pending = [list(u) for u in sols]; scores_cma = []; batch = sols
                    u = pending.pop(0)
                    x = {v.name: v.from_unit(ui) for v, ui in zip(vars_, u)}
                filled = _fill(net, x)
                ev = ctx.evaluate(filled, conds)
                used += len(conds)
                sc = ev.score if ev.status == "ok" else 20.0 + (10.0 if ev.status != "sim_error" else 0.0)
                if optimizer == "tpe":
                    study.tell(tr, sc)
                else:
                    scores_cma.append(sc)
                    if not pending:
                        es.tell(batch, scores_cma)
                if sc < best[0]:
                    best = (sc, filled, ev)
                if ev.status in ("parse_error", "erc_error") and used >= 3 * len(conds):
                    break     # structural error: no point tuning
                if ev.passed:
                    break
            if best[2] is not None and best[2].passed:
                if not robust:
                    status, final = "success", best[1]
                    break
                evP = ctx.evaluate(best[1], PVT)
                if evP.passed:
                    status, final = "success", best[1]
                    break
                if adaptive_pvt and evP.status == "ok":
                    from ..sim.evaluate import cond_name
                    worst = sorted(PVT, key=lambda c: -sum(v[2] for v in evP.checks[cond_name(c)].values()))
                    conds = list(conds) + [c for c in worst[:2] if c not in conds]
                    conds = conds[:8]
                fb = "Passes tt/ss125/ff-40 but fails full PVT:\n" + "\n".join(
                    f"- {cn}: " + "; ".join(f"{k}={diagnose.fmt(v[0])}" for k, v in chk.items() if not v[1])
                    for cn, chk in evP.checks.items() if not all(v[1] for v in chk.values()))
            elif best[2] is not None:
                fb = diagnose.report(task, best[2]) if best[2].status != "ok" else diagnose.spec_table(task, best[2], None)
            else:
                fb = "No valid design evaluated."
        else:
            fb = "No ```spice block found."
        if best[0] < best_overall[0]:
            best_overall = best
        if rd == rounds - 1 or ctx.calls_left() <= 0 or ctx.sims_left() <= 0:
            break
        text = ctx.ask(GENBO_RETRY.format(task_id=task["id"], it=rd + 1, nl_spec=task["nl_spec"], netlist=net or "(none)",
                                          feedback=fb), SYSTEM_DIRECT, f"regen{rd + 1}")
    if final is None:
        final = best_overall[1] or ctx.best.get("netlist")
    return {"status": status, "final_netlist": final, **ctx.summary(), "events": ctx.events}
