"""Shared run bookkeeping for SPECTRA and baselines."""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field

from ..sim.evaluate import NOMINAL, PVT, evaluate, cond_name
from .knowledge import FAMILY_IFACE, KNOWLEDGE, PDK_SHEET
from .prompts import ROBUST_NOTE
from . import llm


@dataclass
class Budget:
    llm_calls: int = 12
    sims: int = 300            # condition-evaluations


@dataclass
class Ctx:
    task: dict
    model: str = "gpt-5-mini"
    seed: int = 0
    budget: Budget = field(default_factory=Budget)
    method: str = ""
    calls: int = 0
    sims: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    llm_seconds: float = 0.0
    t0: float = field(default_factory=time.time)
    events: list = field(default_factory=list)
    first_pass_sims: int | None = None
    first_pass_calls: int | None = None
    best: dict = field(default_factory=lambda: {"score": float("inf"), "netlist": None})
    lock: object = field(default_factory=threading.Lock)
    over_budget_refusals: int = 0

    @property
    def run_tag(self):
        return f"{self.method}|{self.task['id']}|s{self.seed}"

    def ask(self, prompt, system, tag):
        r = llm.call(prompt, system, model=self.model, run_tag=self.run_tag + f"|c{self.calls}", tag=f"{self.method}:{tag}")
        self.calls += 1
        self.tokens_in += r["input_tokens"]; self.tokens_out += r["output_tokens"]
        self.cost += r["cost_usd"]; self.llm_seconds += r["seconds"]
        self.log("llm", tag=tag, cached=r.get("cached", False), out_tokens=r["output_tokens"])
        return r["text"]

    def evaluate(self, netlist, conds=None):
        """Charged evaluation. Refuses (status 'budget') when the call would exceed the simulation budget."""
        from ..sim.evaluate import EvalResult
        conds = conds or [NOMINAL]
        with self.lock:
            if self.sims + len(conds) > self.budget.sims:
                self.over_budget_refusals += 1
                return EvalResult("budget", errors=["simulation budget exhausted"])
            self.sims += len(conds)          # reserve before simulating (parse/ERC errors are refunded below)
        ev = evaluate(self.task, netlist, conds=conds)
        with self.lock:
            if ev.status in ("parse_error", "erc_error"):
                self.sims -= len(conds)
            nominal_only = len(conds) == 1
            if ev.status == "ok" and nominal_only:
                if ev.score < self.best["score"]:
                    self.best = {"score": ev.score, "netlist": netlist, "passed": ev.passed}
                if ev.passed and self.first_pass_sims is None:
                    self.first_pass_sims, self.first_pass_calls = self.sims, self.calls
        return ev

    def log(self, kind, **kw):
        self.events.append({"t": round(time.time() - self.t0, 2), "kind": kind, "calls": self.calls, "sims": self.sims, **kw})

    def calls_left(self):
        return self.budget.llm_calls - self.calls

    def sims_left(self):
        return self.budget.sims - self.sims

    def summary(self):
        return {"method": self.method, "task": self.task["id"], "seed": self.seed, "model": self.model,
                "calls": self.calls, "sims": self.sims, "tokens_in": self.tokens_in, "tokens_out": self.tokens_out,
                "cost_usd": round(self.cost, 4), "llm_seconds": round(self.llm_seconds, 1),
                "wall_seconds": round(time.time() - self.t0, 1), "first_pass_sims": self.first_pass_sims,
                "first_pass_calls": self.first_pass_calls, "budget_sims": self.budget.sims,
                "budget_calls": self.budget.llm_calls, "over_budget_refusals": self.over_budget_refusals}


def task_texts(task):
    fam = task["family"]
    tb = {k: v for k, v in task.get("tb", {}).items()}
    robust = task.get("robust", False)
    return {"task_id": "", "nl_spec": task["nl_spec"], "iface": FAMILY_IFACE[fam], "tb": json.dumps(tb, default=str),
            "pdk": PDK_SHEET, "robust_note": ("\n" + ROBUST_NOTE + "\n") if robust else "",
            "knowledge": KNOWLEDGE[fam]}
