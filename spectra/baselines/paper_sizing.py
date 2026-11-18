"""Paper-backed fixed-topology sizing adapters.

These runners are clean-room, paper-aligned reimplementations. They share the
same frozen topology, variable bounds, simulator, task text and budget.
"""
from __future__ import annotations

import json
import math

import numpy as np

from ..agent.common import Budget, Ctx
from ..agent import llm
from ..bench.templates import T
from ..opt.sizing import Var
from ..sim.evaluate import NOMINAL

PAPER_META = {
    "analogcoder": {"paper": "AnalogCoder", "venue": "AAAI-25", "repo": "https://github.com/laiyao1/AnalogCoder"},
    "ado_llm": {"paper": "ADO-LLM", "venue": "ICCAD-24", "repo": "paper-only-clean-room"},
    "anaflow": {"paper": "AnaFlow", "venue": "ICCAD-25", "repo": "paper-only-clean-room"},
    "artisan": {"paper": "Artisan", "venue": "DAC-24", "repo": "paper-only-clean-room"},
    "autosizer": {"paper": "AutoSizer", "venue": "ICML-26", "repo": "https://github.com/yuxi120407/AutoSizer"},
    "atlas": {"paper": "ATLAS", "venue": "ICCAD-26", "repo": "https://github.com/youngmin0oh/atlas"},
    "glova": {"paper": "GLOVA", "venue": "DAC-25", "repo": "paper-only-clean-room"},
}

SYSTEM = """You reproduce a published analog transistor sizing framework on a frozen topology.
Choose numeric values for the listed variables only. Do not add devices or change net names.
Return JSON with a params object whose values lie within the supplied bounds."""


def _vars(task):
    return [Var(v["name"], float(v["lo"]), float(v["hi"]), bool(v.get("log", True)), bool(v.get("integer", False)))
            for v in task["sizing"]["variables"]]


def _template(task):
    return T[task["sizing"]["template"]]["build"]


def _midpoint(vars_):
    return {v.name: math.sqrt(v.lo * v.hi) if v.log else (v.lo + v.hi) / 2 for v in vars_}


def _clip(x, vars_):
    out = {}
    for v in vars_:
        fallback = _midpoint([v])[v.name]
        try:
            value = float(x.get(v.name, fallback))
        except (TypeError, ValueError):
            value = fallback
        value = min(v.hi, max(v.lo, value))
        out[v.name] = int(round(value)) if v.integer else value
    return out


def _ask_params(ctx, task, vars_, role, context=""):
    bounds = ", ".join(f"{v.name}=[{v.lo:g},{v.hi:g}]" for v in vars_)
    prompt = f"Role: {role}.\nSpecification: {task['nl_spec']}\nVariables: {bounds}\n"
    if context:
        prompt += f"Context:\n{context}\n"
    prompt += "Return JSON only, for example {\"params\": {\"W1\": 4.0}}."
    text = ctx.ask(prompt, SYSTEM, role)
    data = llm.extract_json(text) or {}
    params = data.get("params", data) if isinstance(data, dict) else {}
    return _clip(params if isinstance(params, dict) else {}, vars_)


def _evaluate(ctx, build, x, conds=None):
    try:
        net = build(x)
    except Exception:
        return None, None, 60.0
    if conds is None:
        conds = [NOMINAL]
        if ctx.task.get("robust"):
            conds = [NOMINAL, {"corner": "ss", "temp": 125, "vdd": 1.8}, {"corner": "ff", "temp": -40, "vdd": 1.8}]
    ev = ctx.evaluate(net, list(conds))
    score = ev.score if ev.status == "ok" and math.isfinite(ev.score) else 50.0
    return ev, net, score


def _finish(ctx, net):
    status = "success" if ctx.best.get("passed") else "budget_exhausted"
    return {"status": status, "final_netlist": net or ctx.best.get("netlist"), **ctx.summary(), "events": ctx.events}


def _tpe(ctx, build, vars_, seed, x0=None, budget=None, tag="tpe"):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    budget = ctx.sims_left() if budget is None else min(budget, ctx.sims_left())
    if budget <= 0 or not vars_:
        return ctx.best.get("netlist")
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(
        seed=seed, n_startup_trials=min(12, max(4, budget // 5)), multivariate=True))
    if x0:
        study.enqueue_trial({v.name: min(v.hi, max(v.lo, x0[v.name])) for v in vars_})
    while budget > 0 and ctx.sims_left() > 0:
        trial = study.ask()
        x = {v.name: trial.suggest_float(v.name, v.lo, v.hi, log=v.log) for v in vars_}
        ev, net, score = _evaluate(ctx, build, x)
        study.tell(trial, score)
        ctx.log("paper_search", algorithm=tag, score=score, passed=bool(ev and ev.passed))
        budget -= 1
        if ev is not None and ev.passed:
            return net
    return ctx.best.get("netlist")


def _cmaes(ctx, build, vars_, seed, x0=None, budget=None, tag="cmaes"):
    import cma
    budget = ctx.sims_left() if budget is None else min(budget, ctx.sims_left())
    if budget <= 0 or not vars_:
        return ctx.best.get("netlist")
    u0 = [v.to_unit((x0 or _midpoint(vars_)).get(v.name, _midpoint([v])[v.name])) for v in vars_]
    es = cma.CMAEvolutionStrategy(u0, 0.25, {"bounds": [0, 1], "seed": seed, "verbose": -9})
    while budget > 0 and ctx.sims_left() > 0 and not es.stop():
        solutions = es.ask()
        scores = []
        for unit in solutions:
            x = {v.name: v.from_unit(float(u)) for v, u in zip(vars_, unit)}
            ev, net, score = _evaluate(ctx, build, x)
            scores.append(score)
            ctx.log("paper_search", algorithm=tag, score=score, passed=bool(ev and ev.passed))
            budget -= 1
            if budget <= 0 or ctx.sims_left() <= 0:
                break
            if ev is not None and ev.passed:
                return net
        es.tell(solutions[:len(scores)], scores)
    return ctx.best.get("netlist")


def _gp_bo(ctx, build, vars_, seed, starts, budget):
    """Small GP-BO loop matching ADO-LLM's LLM-seeded BO idea."""
    rng = np.random.default_rng(seed)
    points, values = [], []
    for x in starts:
        ev, net, score = _evaluate(ctx, build, x)
        points.append(np.array([v.to_unit(x[v.name]) for v in vars_])); values.append(score)
        ctx.log("paper_search", algorithm="ado_llm_gp", score=score, passed=bool(ev and ev.passed))
        if ev is not None and ev.passed:
            return net
    while budget > 0 and ctx.sims_left() > 0:
        pool = rng.random((128, len(vars_)))
        X, y = np.asarray(points), np.asarray(values)
        d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2)
        length = max(0.05, float(np.median(np.sqrt(d2[d2 > 0]))) if np.any(d2 > 0) else 0.25)
        K = np.exp(-d2 / (2 * length * length)) + np.eye(len(X)) * 1e-6
        inv = np.linalg.solve(K, y)
        cross = np.exp(-((pool[:, None, :] - X[None, :, :]) ** 2).sum(axis=2) / (2 * length * length))
        mean = cross @ inv
        var = np.maximum(1e-9, 1.0 - (cross @ np.linalg.solve(K, cross.T)).diagonal())
        unit = pool[int(np.argmin(mean - 1.5 * np.sqrt(var)))]
        x = {v.name: v.from_unit(float(u)) for v, u in zip(vars_, unit)}
        ev, net, score = _evaluate(ctx, build, x)
        points.append(unit); values.append(score); budget -= 1
        ctx.log("paper_search", algorithm="ado_llm_gp", score=score, passed=bool(ev and ev.passed))
        if ev is not None and ev.passed:
            return net
    return ctx.best.get("netlist")


def _narrow(vars_, centre, factor=0.35):
    narrowed = []
    for v in vars_:
        c = centre.get(v.name, _midpoint([v])[v.name])
        if v.log:
            lo, hi = max(v.lo, c * factor), min(v.hi, c / factor)
        else:
            span = (v.hi - v.lo) * factor
            lo, hi = max(v.lo, c - span), min(v.hi, c + span)
        narrowed.append(Var(v.name, lo, hi, v.log, v.integer) if hi > lo else v)
    return narrowed


def _lhs(ctx, build, vars_, seed, n, history=None):
    rng = np.random.default_rng(seed)
    for i in range(n):
        x = {v.name: v.from_unit(float((i + rng.random()) / n)) for v in vars_}
        ev, net, score = _evaluate(ctx, build, x)
        if history is not None:
            history.append((np.array([v.to_unit(x[v.name]) for v in vars_]), score, bool(ev and ev.passed)))
        ctx.log("paper_search", algorithm="mapper_lhs", score=score, passed=bool(ev and ev.passed))
        if ev is not None and ev.passed:
            return net
    return ctx.best.get("netlist")


def _atlas_graph_search(ctx, build, vars_, seed, history):
    """Mapper-style bridge/frontier/interior acquisition over normalized samples."""
    rng = np.random.default_rng(seed)
    if not history:
        return ctx.best.get("netlist")
    points = np.array([h[0] for h in history])
    scores = np.array([h[1] for h in history])
    k = max(2, min(5, len(points) // 4))
    for _ in range(min(40, ctx.sims_left())):
        distances = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=-1)
        np.fill_diagonal(distances, np.inf)
        nearest = np.partition(distances, k - 1, axis=1)[:, :k].mean(axis=1)
        order = np.argsort(scores)
        frontier = order[:max(1, len(order) // 4)]
        bridge = np.argsort(-nearest)[:max(1, len(order) // 4)]
        pool = np.unique(np.concatenate([frontier, bridge]))
        anchor = points[int(rng.choice(pool))]
        direction = rng.normal(0, 0.12, len(vars_))
        if int(rng.integers(2)) == 0:
            direction += points[int(rng.choice(frontier))] - anchor
        unit = np.clip(anchor + direction, 0.0, 1.0)
        x = {v.name: v.from_unit(float(u)) for v, u in zip(vars_, unit)}
        ev, net, score = _evaluate(ctx, build, x)
        points = np.vstack([points, unit]); scores = np.append(scores, score)
        ctx.log("paper_search", algorithm="mapper_bridge_frontier", score=score, passed=bool(ev and ev.passed))
        if ev is not None and ev.passed:
            return net
    return ctx.best.get("netlist")


def run_analogcoder(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="analogcoder")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    x, net = _ask_params(ctx, task, vars_, "feedback-enhanced direct sizing"), None
    for _ in range(4):
        ev, net, _ = _evaluate(ctx, build, x)
        if ev is not None and ev.passed:
            break
        if ctx.calls_left() <= 0:
            break
        feedback = "no result" if ev is None else json.dumps(ev.summary(), default=str)[:4000]
        x = _ask_params(ctx, task, vars_, "direct sizing revision", feedback)
    return _finish(ctx, net)


def run_ado_llm(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="ado_llm")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    starts = [_ask_params(ctx, task, vars_, "LLM-guided Bayesian-optimization initialization", f"seed_point={i}") for i in range(min(5, ctx.calls_left()))]
    return _finish(ctx, _gp_bo(ctx, build, vars_, seed, starts, ctx.sims_left()))


def run_anaflow(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="anaflow")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    plan = _ask_params(ctx, task, vars_, "multi-agent circuit and specification analyst")
    ev, _, score = _evaluate(ctx, build, plan)
    context = f"analyst score={score}; " + (json.dumps(ev.summary(), default=str)[:3500] if ev else "no result")
    advisor = _ask_params(ctx, task, vars_, "critic and adaptive-sampling advisor", context)
    return _finish(ctx, _tpe(ctx, build, vars_, seed + 31, x0=advisor, tag="adaptive_sample_bo"))


def run_artisan(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="artisan")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    x = _ask_params(ctx, task, vars_, "domain-specific op-amp sizing plan and parameter tuning")
    return _finish(ctx, _cmaes(ctx, build, vars_, seed + 41, x0=x, tag="artisan_parameter_tuning"))


def run_ledro(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="ledro")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    x = _ask_params(ctx, task, vars_, "LLM design-space reduction")
    reduced = _narrow(vars_, x, factor=0.30)
    ctx.log("space_reduction", kept_variables=len(reduced), factor=0.30)
    return _finish(ctx, _tpe(ctx, build, reduced, seed + 7, x0=x, tag="reduced_space_bo"))


def run_autosizer(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="autosizer")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    x = _ask_params(ctx, task, vars_, "reflective outer-loop search-space construction")
    first = max(1, ctx.sims_left() // 2)
    _tpe(ctx, build, vars_, seed + 11, x0=x, budget=first, tag="autosizer_inner")
    reflection = _ask_params(ctx, task, vars_, "reflective outer-loop bounds update", "incumbent score and netlist are in the simulation trace")
    return _finish(ctx, _tpe(ctx, build, _narrow(vars_, reflection, factor=0.45), seed + 12, x0=reflection, tag="autosizer_refined_inner"))


def run_astra(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="astra")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    x = _ask_params(ctx, task, vars_, "gm/id knowledge initialization and critical-device reasoning")
    critical = vars_[:max(1, min(4, len(vars_)))]
    ctx.log("critical_variable_selection", variables=[v.name for v in critical])
    base = _midpoint(vars_)
    def build_critical(partial):
        return build({**base, **partial})
    critical_x = {v.name: x.get(v.name, base[v.name]) for v in critical}
    _tpe(ctx, build_critical, critical, seed + 17, x0=critical_x,
         budget=max(1, ctx.sims_left() // 2), tag="astra_focal_bo")
    return _finish(ctx, _tpe(ctx, build, vars_, seed + 18, x0=x, tag="astra_global_bo"))


def run_glova(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="glova")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    x = _ask_params(ctx, task, vars_, "risk-sensitive global/local variation-aware initialization")
    rng = np.random.default_rng(seed + 51)
    best = x
    rounds = max(1, min(8, ctx.sims_left() // max(1, len(vars_))))
    for rd in range(rounds):
        candidates = []
        for _ in range(3):
            candidate = dict(best)
            for v in vars_:
                u = v.to_unit(candidate[v.name]) + float(rng.normal(0, 0.12 if rd else 0.25))
                candidate[v.name] = v.from_unit(u)
            candidates.append(candidate)
        for candidate in candidates:
            ev, net, score = _evaluate(ctx, build, candidate)
            ctx.log("paper_search", algorithm="risk_sensitive_global_local", score=score, passed=bool(ev and ev.passed))
            if ev is not None and ev.status == "ok" and score < ctx.best.get("score", float("inf")):
                best = candidate
            if ev is not None and ev.passed:
                return _finish(ctx, net)
            if ctx.sims_left() <= 0:
                break
    return _finish(ctx, ctx.best.get("netlist"))


def run_atlas(task, model="gpt-6.1-sol", seed=0, budget=None):
    ctx = Ctx(task=task, model=model, seed=seed, method="atlas")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    n = min(24, ctx.sims_left())
    history = []
    _lhs(ctx, build, vars_, seed + 23, n, history=history)
    ctx.log("mapper_graph", nodes=n, normalized=True, landscape_edge="nearest-neighbor", acquisition="bridge_frontier_interior")
    return _finish(ctx, _atlas_graph_search(ctx, build, vars_, seed + 24, history))


RUNNERS = {
    "analogcoder": run_analogcoder,
    "ado_llm": run_ado_llm,
    "anaflow": run_anaflow,
    "artisan": run_artisan,
    "autosizer": run_autosizer,
    "atlas": run_atlas,
    "glova": run_glova,
}
