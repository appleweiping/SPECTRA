"""AnalogCoder-style baseline: the LLM writes a sized netlist directly and revises it from simulation feedback.

Faithful to AnalogCoder's loop (design plan + code/netlist, simulate, feed back errors / operating-point problems
and spec results, retry), adapted to SKY130 and quantitative specs. Same LLM, same budgets as SPECTRA.
"""
from __future__ import annotations

from ..agent import diagnose, llm
from ..agent.common import Ctx, task_texts
from ..agent.prompts import DIRECT_ITERATE, DIRECT_PLAN, SYSTEM_DIRECT
from ..sim.evaluate import PVT, region_report


def _feedback(task, ev, evP=None):
    if ev.status != "ok":
        return diagnose.report(task, ev)
    fb = diagnose.spec_table(task, ev, None)
    # AnalogCoder-style operating-point sanity message (zero-current devices)
    off = [d for d, r in region_report(ev.ops).items() if r["region"] == "off"]
    if off:
        fb += "\nThe circuit does not function correctly: the drain current I_D of " + ", ".join(off) + " is 0."
    if evP is not None:
        bad = []
        for cn, chk in evP.checks.items():
            b = [f"{k}: {diagnose.fmt(v[0])}" for k, v in chk.items() if not v[1]]
            if b:
                bad.append(f"- {cn}: " + "; ".join(b))
        fb += "\nNominal specs pass, but these PVT conditions fail:\n" + "\n".join(bad[:17])
    return fb


def run_direct(task, model="gpt-6.1-sol", seed=0, budget=None, method="direct", knowledge_override=None):
    ctx = Ctx(task=task, model=model, seed=seed, method=method)
    if budget:
        ctx.budget = budget
    t = task_texts(task)
    if knowledge_override is not None:
        t["knowledge"] = knowledge_override
    text = ctx.ask(DIRECT_PLAN.format(**t), SYSTEM_DIRECT, "plan")
    status, final = "budget_exhausted", None
    it = 0
    while True:
        net = llm.extract_block(text, "spice") or llm.extract_block(text, "")
        if net is None:
            fb = "No ```spice netlist block found. Provide the complete netlist."
        else:
            ev = ctx.evaluate(net)
            evP = None
            if ev.status == "ok" and ev.passed:
                if not task.get("robust"):
                    status, final = "success", net
                    break
                evP = ctx.evaluate(net, PVT)
                if evP.status == "budget":
                    break
                if evP.passed:
                    status, final = "success", net
                    break
            fb = _feedback(task, ev, evP)
        if ctx.calls_left() <= 0 or ctx.sims_left() <= 0:
            break
        it += 1
        text = ctx.ask(DIRECT_ITERATE.format(task_id="", it=it, calls_left=ctx.calls_left(), nl_spec=task["nl_spec"],
                                             netlist=net or "(none)", feedback=fb), SYSTEM_DIRECT, f"iter{it}")
    if final is None:
        final = ctx.best.get("netlist")
    return {"status": status, "final_netlist": final, **ctx.summary(), "events": ctx.events}
