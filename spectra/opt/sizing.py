"""Black-box sizing optimizers over a parametric netlist template.

Used for (i) deriving feasible benchmark specs from expert templates and (ii) the
optimizer baselines (random search, CMA-ES, TPE) and SPECTRA's refinement stage.
"""
from __future__ import annotations

import math
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import numpy as np

from ..sim.evaluate import evaluate


@dataclass
class Var:
    name: str
    lo: float
    hi: float
    log: bool = True
    integer: bool = False

    def to_unit(self, v):
        v = min(max(v, self.lo), self.hi)
        if self.log:
            return (math.log(v) - math.log(self.lo)) / (math.log(self.hi) - math.log(self.lo))
        return (v - self.lo) / (self.hi - self.lo)

    def from_unit(self, u):
        u = min(max(u, 0.0), 1.0)
        v = math.exp(math.log(self.lo) + u * (math.log(self.hi) - math.log(self.lo))) if self.log else self.lo + u * (self.hi - self.lo)
        return int(round(v)) if self.integer else v


@dataclass
class OptResult:
    best_x: dict
    best_score: float
    best_eval: object
    history: list = field(default_factory=list)   # (n_eval, score, passed)
    n_evals: int = 0
    n_sims: int = 0
    seconds: float = 0.0
    first_pass_eval: int | None = None


def objective_value(task, ev, power_weight=0.0):
    """Scalar objective: violation score, plus optional secondary objective once feasible."""
    s = ev.score if math.isfinite(ev.score) else 50.0
    sec = task.get("objective")
    if sec and ev.status == "ok" and ev.per_cond:
        m = list(ev.per_cond.values())[0].get(sec["metric"])
        if m is not None and m > 0:
            ref = sec.get("ref", 1.0)
            val = math.log10(m / ref)
            s += sec.get("weight", 0.05) * (val if sec.get("sense", "min") == "min" else -val)
    return s


class Runner:
    def __init__(self, task, template, variables, conds=None, workers=4, stop_on_pass=False, score_fn=None,
                 archive=None):
        self.task, self.template, self.vars = task, template, variables
        self.conds, self.workers, self.stop_on_pass = conds, workers, stop_on_pass
        self.score_fn = score_fn
        self.archive = archive   # optional list collecting (x, metrics-per-cond, passed)
        self.res = OptResult({}, float("inf"), None)
        self.t0 = time.time()

    def x_from_unit(self, u):
        return {v.name: v.from_unit(ui) for v, ui in zip(self.vars, u)}

    def eval_units(self, us):
        xs = [self.x_from_unit(u) for u in us]

        def one(x):
            try:
                net = self.template(x)
            except Exception as e:  # template failure counts as invalid design
                return None
            return evaluate(self.task, net, conds=self.conds, keep_ops=False)

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            evs = list(ex.map(one, xs))
        scores = []
        for x, ev in zip(xs, evs):
            self.res.n_evals += 1
            if ev is None:
                scores.append(60.0); continue
            self.res.n_sims += ev.n_sims
            sc = self.score_fn(ev) if self.score_fn else objective_value(self.task, ev)
            scores.append(sc)
            if self.archive is not None and ev.status == "ok":
                self.archive.append({"x": x, "metrics": ev.per_cond, "passed": bool(ev.passed), "score": sc})
            if sc < self.res.best_score:
                self.res.best_score, self.res.best_x, self.res.best_eval = sc, x, ev
            if ev.passed and self.res.first_pass_eval is None:
                self.res.first_pass_eval = self.res.n_evals
            self.res.history.append((self.res.n_evals, sc, bool(ev.passed)))
        return scores

    def done(self, budget):
        if self.res.n_evals >= budget:
            return True
        return self.stop_on_pass and self.res.first_pass_eval is not None


def run_random(task, template, variables, budget=200, conds=None, seed=0, x0=None, workers=4, stop_on_pass=False):
    rng = np.random.default_rng(seed)
    R = Runner(task, template, variables, conds, workers, stop_on_pass)
    if x0:
        R.eval_units([[v.to_unit(x0[v.name]) for v in variables]])
    while not R.done(budget):
        n = min(workers * 2, budget - R.res.n_evals)
        R.eval_units(rng.random((n, len(variables))).tolist())
    R.res.seconds = time.time() - R.t0
    return R.res


def run_cmaes(task, template, variables, budget=300, conds=None, seed=0, x0=None, sigma0=0.25, workers=4,
              stop_on_pass=False, popsize=None, score_fn=None, archive=None):
    import cma
    R = Runner(task, template, variables, conds, workers, stop_on_pass, score_fn, archive)
    u0 = [v.to_unit(x0[v.name]) for v in variables] if x0 else [0.5] * len(variables)
    opts = {"bounds": [0, 1], "seed": seed + 1, "verbose": -9, "popsize": popsize or max(8, 4 + int(3 * math.log(len(variables))))}
    es = cma.CMAEvolutionStrategy(u0, sigma0, opts)
    if x0:
        R.eval_units([u0])
    while not R.done(budget) and not es.stop():
        sols = es.ask()
        sc = R.eval_units([list(x) for x in sols])
        es.tell(sols, sc)
    R.res.seconds = time.time() - R.t0
    return R.res


def run_tpe(task, template, variables, budget=200, conds=None, seed=0, x0=None, workers=4, stop_on_pass=False):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    R = Runner(task, template, variables, conds, workers, stop_on_pass)
    sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=min(20, budget // 4), multivariate=True)
    study = optuna.create_study(direction="minimize", sampler=sampler)
    if x0:
        study.enqueue_trial({v.name: v.to_unit(x0[v.name]) for v in variables})
    while not R.done(budget):
        n = min(workers, budget - R.res.n_evals)
        trials = [study.ask() for _ in range(n)]
        us = [[t.suggest_float(v.name, 0.0, 1.0) for v in variables] for t in trials]
        sc = R.eval_units(us)
        for t, s in zip(trials, sc):
            study.tell(t, s)
    R.res.seconds = time.time() - R.t0
    return R.res


OPTIMIZERS = {"random": run_random, "cmaes": run_cmaes, "tpe": run_tpe}
