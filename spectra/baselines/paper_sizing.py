"""Paper-backed fixed-topology sizing adapters.

These runners are clean-room, paper-aligned reimplementations. They share the
same frozen topology, variable bounds, simulator, task text and budget.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

from ..agent.common import Budget, Ctx
from ..agent import diagnose
from ..agent.knowledge import render_cards, retrieve_cards
from ..agent import llm
from ..bench.templates import T
from ..opt.sizing import Var
from ..sim.evaluate import NOMINAL

PAPER_META = {
    "spectra": {"paper": "SPECTRA (ours)", "venue": "this work", "repo": "local framework"},
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

SYSTEM_SPECTRA_FIXED = """You are the SPECTRA fixed-topology sizing agent.
The circuit topology and simulator interface are frozen by the benchmark. You may choose only
the numeric sizing variables listed in the task. Use the family knowledge, structured diagnosis,
and observed simulator measurements to propose a physically coherent design. Return JSON only
with a params object. Every value must lie within the supplied bounds."""


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


def _ask_params(ctx, task, vars_, role, context="", system=SYSTEM):
    bounds = ", ".join(f"{v.name}=[{v.lo:g},{v.hi:g}]" for v in vars_)
    prompt = f"Role: {role}.\nSpecification: {task['nl_spec']}\nVariables: {bounds}\n"
    if context:
        prompt += f"Context:\n{context}\n"
    prompt += "Return JSON only, for example {\"params\": {\"W1\": 4.0}}."
    text = ctx.ask(prompt, system, role)
    data = llm.extract_json(text) or {}
    params = data.get("params", data) if isinstance(data, dict) else {}
    return _clip(params if isinstance(params, dict) else {}, vars_)


def _safe_ask_params(ctx, task, vars_, role, context="", system=SYSTEM):
    """Keep a transient gateway failure inside the fixed-budget run.

    The strict row records the failed attempt and falls back to the deterministic
    midpoint so the SPECTRA refinement stage can still consume the remaining
    simulator budget. This preserves a completed, auditable row instead of
    converting an infrastructure timeout into a missing task.
    """
    try:
        return _ask_params(ctx, task, vars_, role, context, system), False
    except llm.LLMError as exc:
        ctx.calls += 1
        ctx.log("llm_failure_fallback", error=str(exc)[:240], role=role)
        return _midpoint(vars_), True


def run_spectra(task, model="gpt-6.1-sol", seed=0, budget=None):
    """Run SPECTRA's diagnosis/knowledge/refinement loop on the frozen topology.

    This adapter keeps the strict track's fixed-topology contract. SPECTRA controls the
    intent proposal, structured failure diagnosis, knowledge-card retrieval and bounded
    refinement, while the public template supplies the immutable netlist topology.
    """
    ctx = Ctx(task=task, model=model, seed=seed, method="spectra")
    ctx.budget = budget or Budget()
    vars_, build = _vars(task), _template(task)
    initial_cards = retrieve_cards(task, None)
    initial_context = "Family knowledge cards:\n" + render_cards(initial_cards)
    x, llm_failed = _safe_ask_params(ctx, task, vars_, "SPECTRA intent planner",
                                     initial_context, SYSTEM_SPECTRA_FIXED)
    refinement_done = False
    robust = bool(task.get("robust"))
    if robust and os.environ.get("SPECTRA_PVT_STRATEGY", "fullgrid") == "staged":
        return _run_spectra_staged(task, model, seed, ctx, vars_, build, x, llm_failed)
    # Robust tasks use the same 300 condition-evaluation budget as every other
    # strict row, but spend it on the actual 45-corner objective.  The old path
    # stopped as soon as TT passed, which made a nominally good design consume
    # three search corners and then fail the independent PVT verifier.  Keeping
    # the full-grid score in-loop gives the diagnosis and violation objective the
    # information that the final verifier uses.
    robust_conds = None
    if robust:
        from ..sim.evaluate import PVT
        robust_conds = PVT
    ev, net, score = _evaluate(ctx, build, x, conds=robust_conds)
    if robust:
        _update_robust_best(ctx, ev, net, score)
    ctx.log("spectra_plan", score=score, passed=bool(ev and ev.passed), topology="frozen")
    if ev is not None and ev.passed:
        if robust:
            _update_robust_best(ctx, ev, net, score)
            return _finish(ctx, ctx.best.get("netlist"))
        else:
            ctx.best = {"score": score, "netlist": net, "passed": True}
        return _finish(ctx, net)

    # Keep the same 12-call cap. Each revision receives a structured diagnosis and
    # versioned family cards, then the remaining simulation budget is used by the
    # active-set trust-region refinement implemented by the SPECTRA adapter.
    while not llm_failed and ctx.calls_left() > 1 and ctx.sims_left() > 0:
        analysis = diagnose.analyze(task, ev) if ev is not None and ev.status == "ok" else None
        cards = retrieve_cards(task, analysis) if analysis else []
        context = ""
        if analysis:
            context += "Structured diagnosis:\n" + diagnose.render_analysis(analysis)
        if cards:
            context += "\nKnowledge cards:\n" + render_cards(cards)
        context += "\nCurrent parameters:\n" + json.dumps(x, sort_keys=True)
        x, llm_failed = _safe_ask_params(ctx, task, vars_, "SPECTRA diagnosis-guided revision", context,
                                         SYSTEM_SPECTRA_FIXED)
        # Full-grid evaluations are charged in 45-unit blocks.  If the tail of
        # the budget cannot fit a full block, use the fixed three-corner search
        # set while retaining the best full-grid candidate found so far.
        eval_conds = robust_conds if (robust_conds is not None and ctx.sims_left() >= len(robust_conds)) else None
        ev, net, score = _evaluate(ctx, build, x, conds=eval_conds)
        if robust and eval_conds is robust_conds:
            _update_robust_best(ctx, ev, net, score)
        ctx.log("spectra_revision", score=score, passed=bool(ev and ev.passed),
                diagnosis=analysis.get("schema") if analysis else None,
                cards=[c.get("id") for c in cards])
        if ev is not None and ev.passed and (not robust or eval_conds is robust_conds):
            if robust:
                _update_robust_best(ctx, ev, net, score)
                return _finish(ctx, ctx.best.get("netlist"))
            else:
                ctx.best = {"score": score, "netlist": net, "passed": True}
            return _finish(ctx, net)
        # Reserve a bounded refinement tranche after enough evidence has accumulated.
        # For robust tasks the refinement is charged against the full PVT grid so
        # that a local move cannot improve only the three search corners.
        if robust and ctx.calls >= 2 and ctx.sims_left() >= 4 * len(robust_conds):
            refine_budget = min(4 * len(robust_conds), ctx.sims_left())
            refined = _cmaes(ctx, build, vars_, seed + 71, x0=x, budget=refine_budget,
                             tag="spectra_pvt_fullgrid_refine", conds=robust_conds,
                             popsize=4)
            refinement_done = True
            if refined:
                net = refined
                ctx.log("spectra_refine_trace", budget=refine_budget,
                         returned_best=True, objective="full_pvt_worst_violation")
            break
        if not robust and ctx.calls >= 1 and ctx.sims_left() >= 24:
            refine_budget = min(240, ctx.sims_left())
            refined = _cmaes(ctx, build, vars_, seed + 71, x0=x, budget=refine_budget,
                             tag="spectra_active_set_refine")
            refinement_done = True
            if refined:
                net = refined
                ctx.log("spectra_refine_trace", budget=refine_budget,
                         returned_best=True)
                ctx.best = {"score": score, "netlist": net, "passed": False}
            break
    if llm_failed and not refinement_done and ctx.sims_left() >= 24:
        refine_budget = min(240, ctx.sims_left())
        refined = _cmaes(ctx, build, vars_, seed + 71, x0=x, budget=refine_budget,
                         tag="spectra_fallback_refine")
        if refined:
            net = refined
            ctx.log("spectra_refine_trace", budget=refine_budget, returned_best=True,
                    fallback=True)
    # A robust tail evaluation may use only the three search corners after the
    # 45-corner blocks no longer fit.  Never let that tail replace the best
    # full-grid candidate that was actually scored against the verifier.
    final_net = ctx.best.get("netlist") if robust else (net or ctx.best.get("netlist"))
    return _finish(ctx, final_net)


def _run_spectra_staged(task, model, seed, ctx, vars_, build, x, llm_failed):
    """Optional staged robust strategy for sensitivity analysis.

    It keeps an incumbent that passes TT plus two representative corners while
    reserving the remaining budget for full-grid local refinement.  The default
    strict row remains the full-grid strategy above.  This path is deliberately
    selected by an environment flag so it cannot silently replace the primary
    evidence.
    """
    from ..sim.evaluate import PVT
    search_conds = [NOMINAL, {"corner": "ss", "temp": 125, "vdd": 1.8},
                    {"corner": "ff", "temp": -40, "vdd": 1.8}]
    ev, net, score = _evaluate(ctx, build, x, conds=search_conds)
    staged_best = {"score": score, "netlist": net, "params": dict(x), "passed": bool(ev and ev.passed)}
    staged_rank = (0 if staged_best["passed"] else 1, score)
    ctx.log("spectra_staged_plan", score=score, passed=staged_best["passed"], search_corners=3)
    revisions = 0
    while not llm_failed and ctx.calls_left() > 1 and revisions < 2 and ctx.sims_left() >= len(search_conds):
        analysis = diagnose.analyze(task, ev) if ev is not None and ev.status == "ok" else None
        cards = retrieve_cards(task, analysis) if analysis else []
        context = ""
        if analysis:
            context += "Structured diagnosis:\n" + diagnose.render_analysis(analysis)
        if cards:
            context += "\nKnowledge cards:\n" + render_cards(cards)
        context += "\nCurrent parameters:\n" + json.dumps(x, sort_keys=True)
        x, llm_failed = _safe_ask_params(ctx, task, vars_, "SPECTRA staged diagnosis revision",
                                         context, SYSTEM_SPECTRA_FIXED)
        ev, net, score = _evaluate(ctx, build, x, conds=search_conds)
        ctx.log("spectra_staged_revision", score=score, passed=bool(ev and ev.passed),
                diagnosis=analysis.get("schema") if analysis else None,
                cards=[c.get("id") for c in cards])
        candidate_rank = (0 if ev is not None and ev.passed else 1, score)
        if ev is not None and ev.status == "ok" and candidate_rank < staged_rank:
            staged_best = {"score": score, "netlist": net, "params": dict(x), "passed": bool(ev.passed)}
            staged_rank = candidate_rank
        revisions += 1
    # One full-grid evaluation anchors the PVT objective, then a small-sigma
    # CMA search stays near the TT-feasible staged incumbent.
    # Preserve a staged TT-feasible incumbent while full-grid candidates are
    # being tested. A full-grid candidate that still fails TT must not replace
    # this incumbent merely because its PVT worst-case score is numerically
    # smaller.
    if staged_best.get("passed") and staged_best.get("netlist"):
        ctx.best = {"score": float("inf"), "netlist": staged_best["netlist"], "passed": False,
                    "robust_rank": (0, float("inf")), "robust_tt_pass": True}
    if ctx.sims_left() >= len(PVT) and staged_best.get("netlist"):
        ev_full, net_full, score_full = _evaluate(ctx, build, staged_best.get("params", _midpoint(vars_)), conds=PVT)
        _update_robust_best(ctx, ev_full, net_full, score_full)
    if ctx.sims_left() >= 4 * len(PVT) and ctx.best.get("netlist"):
        _cmaes(ctx, build, vars_, seed + 197, x0=_params_from_netlist(task, vars_, staged_best),
               budget=4 * len(PVT), tag="spectra_pvt_staged_refine", conds=PVT, popsize=4, sigma=0.08)
    final_net = ctx.best.get("netlist") or staged_best.get("netlist")
    return _finish(ctx, final_net)


def _params_from_netlist(task, vars_, staged_best):
    """Return the staged parameter center when it is already represented."""
    # The staged path retains parameters directly via this private field.  Fall
    # back to geometric midpoints for old result records.
    return staged_best.get("params") or _midpoint(vars_)


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


def _update_robust_best(ctx, ev, net, score):
    """Keep TT feasibility lexicographically ahead of PVT violation.

    A full-grid candidate can reduce a cold-corner violation by sacrificing the
    nominal target.  The strict endpoint requires TT success as well, so such a
    candidate must not replace a TT-feasible incumbent merely because its raw
    worst-corner score is smaller.
    """
    if ev is None or ev.status != "ok" or not net:
        return
    nominal = ev.checks.get("tt_27C_1.8V", {})
    tt_pass = bool(nominal) and all(v[1] for v in nominal.values())
    rank = (0 if tt_pass else 1, float(score))
    old_rank = ctx.best.get("robust_rank", (1, float("inf")))
    if rank < old_rank:
        ctx.best = {"score": score, "netlist": net, "passed": ev.passed,
                    "robust_rank": rank, "robust_tt_pass": tt_pass}


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


def _cmaes(ctx, build, vars_, seed, x0=None, budget=None, tag="cmaes", conds=None, popsize=None, sigma=0.25):
    import cma
    budget = ctx.sims_left() if budget is None else min(budget, ctx.sims_left())
    if budget <= 0 or not vars_:
        return ctx.best.get("netlist")
    u0 = [v.to_unit((x0 or _midpoint(vars_)).get(v.name, _midpoint([v])[v.name])) for v in vars_]
    options = {"bounds": [0, 1], "seed": seed, "verbose": -9}
    if popsize is not None:
        options["popsize"] = int(popsize)
    es = cma.CMAEvolutionStrategy(u0, sigma, options)
    while budget > 0 and ctx.sims_left() > 0 and not es.stop():
        solutions = es.ask()
        scores = []
        for unit in solutions:
            x = {v.name: v.from_unit(float(u)) for v, u in zip(vars_, unit)}
            ev, net, score = _evaluate(ctx, build, x, conds=conds)
            scores.append(score)
            ctx.log("paper_search", algorithm=tag, score=score, passed=bool(ev and ev.passed))
            if conds is not None:
                _update_robust_best(ctx, ev, net, score)
            budget -= 1
            if budget <= 0 or ctx.sims_left() <= 0:
                break
            if ev is not None and ev.passed:
                return net
        # A final truncated batch can contain fewer points than CMA-ES needs
        # for an update when the strict simulation budget is exhausted.
        if len(scores) >= int(getattr(getattr(es, "sp", None), "mu", 4)):
            es.tell(solutions[:len(scores)], scores)
        else:
            break
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
    "spectra": run_spectra,
    "analogcoder": run_analogcoder,
    "ado_llm": run_ado_llm,
    "anaflow": run_anaflow,
    "artisan": run_artisan,
    "autosizer": run_autosizer,
    "atlas": run_atlas,
    "glova": run_glova,
}
