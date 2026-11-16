"""Oracle-unmet control tasks: tighten certified tasks beyond what an extended expert-template oracle reaches.

For each selected certified task, every '>=' spec is raised and every '<=' spec lowered by a family-agnostic factor
(dB: +6 dB, deg: +10 deg, ratio metrics: x/÷1.6), then an extended CMA-ES oracle (400 evaluations, warm-started at the reference) on the
task's own template tries to meet them. Tasks the oracle cannot meet are kept and labelled 'oracle_unmet'.
"""
import copy, json, math, sys
from spectra.paths import ROOT
from spectra.bench.templates import T
from spectra.bench.nl import render
from spectra.opt.sizing import run_cmaes
from scripts.build_bench import DB, LOG_PLUS, LOG_MINUS, LIN_PLUS, LIN_MINUS

def tighten(s):
    s = copy.deepcopy(s); m, op, v = s["metric"], s["op"], s["value"]
    if op == "range":
        return s
    if m in DB or m.endswith("_db"):
        s["value"] = v + 6 if op == ">=" else v - 6
    elif m == "pm":
        s["value"] = min(85, v + 10)
    elif m in LOG_PLUS or m in LIN_PLUS:
        s["value"] = float(f"{v * 1.6:.3g}") if op == ">=" else v
    elif m in LOG_MINUS or m in LIN_MINUS:
        s["value"] = float(f"{v / 1.6:.3g}") if op == "<=" else v
    elif m.endswith("_pct"):
        s["value"] = round(v / 2, 2)
    return s

def main(n=6):
    tasks = [json.loads(l) for l in open(ROOT / "data/bench/tasks.jsonl")]
    pick, fams = [], set()
    for t in sorted(tasks, key=lambda t: (-int(t["tier"]), t["id"])):
        if t.get("robust") or t["family"] in fams:
            continue
        pick.append(t); fams.add(t["family"])
        if len(pick) >= n:
            break
    out = []
    for t in pick:
        c = copy.deepcopy(t)
        c["specs"] = [tighten(s) for s in t["specs"]]
        c["id"] = "C-" + t["id"]; c["tier"] = "C"; c["infeasible"] = True
        tpl = T[t["ref"]["template"]]
        best = 1e9
        for seed in (0,):
            r = run_cmaes(c, tpl["build"], tpl["vars"], budget=400, seed=seed, x0=t["ref"]["x"], stop_on_pass=True)
            best = min(best, r.best_score)
            if r.first_pass_eval:
                break
        c["oracle_best_violation"] = best
        status = "oracle_unmet" if best > 0 else "oracle_met"
        print(c["id"], status, round(best, 3), flush=True)
        if status == "oracle_unmet":
            c["nl_spec"] = render(c)
            out.append(c)
    with open(ROOT / "data/bench/control_tasks.jsonl", "w") as f:
        for c in out:
            f.write(json.dumps(c, default=float) + "\n")
    print(len(out), "controls")

if __name__ == "__main__":
    main()
