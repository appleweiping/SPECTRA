"""Executes a design program for one or more parameter sets. Invoked as a subprocess:
    python -m spectra.agent.sandbox_worker <program.py> <jobs.json> <out.json>
jobs.json: {"spec": {...}, "params": [ {name: value}, ... ] }  (empty dict -> PARAMS initial values)
"""
import json, math, sys, traceback

import numpy as np

from spectra.agent import dsl


def main(prog_path, jobs_path, out_path):
    src = open(prog_path).read()
    jobs = json.load(open(jobs_path))
    ns = {"__name__": "design_program", "math": math, "np": np, "Netlist": dsl.Netlist, "par": dsl.par,
          "db": dsl.db, "PI": dsl.PI, "UT": dsl.UT}
    out = {"ok": True, "results": []}
    try:
        exec(compile(src, "design_program.py", "exec"), ns)
        params0 = {k: v[0] for k, v in ns["PARAMS"].items()}
        out["PARAMS"] = {k: list(v) for k, v in ns["PARAMS"].items()}
    except Exception:
        out["ok"] = False
        out["error"] = traceback.format_exc(limit=3)[-2500:]
        json.dump(out, open(out_path, "w")); return
    lut = dsl.LUT()
    for ps in jobs["params"]:
        p = dict(params0); p.update(ps)
        try:
            res = ns["design"](p, lut, jobs.get("spec", {}))
            net, pred = (res if isinstance(res, tuple) else (res, {}))
            text = net.text() if hasattr(net, "text") else str(net)
            pred = {k: (float(v) if isinstance(v, (int, float, np.floating)) and math.isfinite(float(v)) else None)
                    for k, v in (pred or {}).items()}
            out["results"].append({"ok": True, "netlist": text, "pred": pred, "params": p})
        except Exception:
            out["results"].append({"ok": False, "error": traceback.format_exc(limit=4)[-2500:], "params": p})
    json.dump(out, open(out_path, "w"), default=float)


if __name__ == "__main__":
    main(*sys.argv[1:4])
