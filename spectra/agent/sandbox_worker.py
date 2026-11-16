"""Executes a design program for one or more parameter sets. Invoked as a subprocess:
    python -m spectra.agent.sandbox_worker <program.py> <jobs.json> <out.json>
jobs.json: {"spec": {...}, "params": [ {name: value}, ... ] }  (empty dict -> PARAMS initial values)
"""
import json, math, re, sys, traceback

import numpy as np

from spectra.agent import dsl


SAFE_BUILTINS = {k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
                 for k in ["abs", "min", "max", "sum", "round", "range", "len", "enumerate", "zip", "float", "int",
                           "bool", "str", "dict", "list", "tuple", "set", "sorted", "reversed", "any", "all", "map",
                           "filter", "isinstance", "pow", "divmod", "print", "ValueError", "Exception", "ZeroDivisionError",
                           "KeyError", "IndexError", "TypeError", "True", "False", "None"]
                 if (k in __builtins__ if isinstance(__builtins__, dict) else hasattr(__builtins__, k))}
FORBIDDEN = re.compile(r"\b(import|open|exec|eval|compile|globals|locals|getattr|setattr|__\w+__)\b")


def main(prog_path, jobs_path, out_path):
    src = open(prog_path).read()
    jobs = json.load(open(jobs_path))
    bad = FORBIDDEN.search(src)
    if bad:
        json.dump({"ok": False, "error": f"forbidden construct '{bad.group(0)}': programs may not import modules or use "
                   f"I/O/introspection; math, np, Netlist, par, db, PI, UT are pre-imported."}, open(out_path, "w"))
        return
    ns = {"__builtins__": SAFE_BUILTINS, "__name__": "design_program", "math": math, "np": np, "Netlist": dsl.Netlist,
          "par": dsl.par, "db": dsl.db, "PI": dsl.PI, "UT": dsl.UT}
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
