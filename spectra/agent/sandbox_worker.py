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
                           "filter", "isinstance", "hasattr", "pow", "divmod", "print", "repr", "format", "object",
                           "staticmethod", "property", "super", "callable", "iter", "next", "slice", "complex",
                           "__build_class__", "ValueError", "Exception", "ZeroDivisionError", "KeyError", "IndexError",
                           "TypeError", "NameError", "AttributeError", "RuntimeError", "ArithmeticError", "OverflowError",
                           "AssertionError", "StopIteration", "LookupError", "NotImplementedError", "True", "False", "None"]
                 if (k in __builtins__ if isinstance(__builtins__, dict) else hasattr(__builtins__, k))}
FORBIDDEN = re.compile(r"\b(import|open|exec|eval|compile|globals|locals|getattr|setattr|delattr|vars|breakpoint|input)\b"
                       r"|__(import|builtins|class|subclasses|globals|code|dict|bases|mro|loader|spec|getattribute)__")


API_HINT = ("\n[API reminder] design(p, lut, spec) must return (Netlist, predictions). Size devices with "
            "lut.size(dev, gm_id, L, Id, vds=..., vsb=...) -> DevOP (fields W, L, Id, gm_id, vgs, vth, vdsat, gm, gds, "
            "cgg, cgd, cdd, ft, intrinsic_gain); n = Netlist('port1 port2 ...'); n.dev(name, d, g, s, b, op, m=1); "
            "n.M(name, d, g, s, b, 'nfet'|'pfet', W, L, m=1); n.Q/n.R/n.C. PARAMS = {name: (init, lo, hi)}.")


def main(prog_path, jobs_path, out_path):
    src = open(prog_path).read()
    jobs = json.load(open(jobs_path))
    bad = FORBIDDEN.search(src)
    if bad:
        json.dump({"ok": False, "error": f"forbidden construct '{bad.group(0)}': programs may not import modules or use "
                   f"I/O/introspection. Pre-imported names: math, np, Netlist, par, db, PI, UT; the gm/Id sizer is the "
                   f"`lut` argument of design(p, lut, spec): lut.size(dev, gm_id, L, Id, vds, vsb)."}, open(out_path, "w"))
        return
    ns = {"__builtins__": SAFE_BUILTINS, "__name__": "design_program", "math": math, "np": np, "Netlist": dsl.Netlist,
          "par": dsl.par, "db": dsl.db, "PI": dsl.PI, "UT": dsl.UT}
    out = {"ok": True, "results": []}
    try:
        exec(compile(src, "design_program.py", "exec"), ns)
        norm = {}
        for k, v in ns["PARAMS"].items():
            if isinstance(v, (int, float)):
                norm[k] = [float(v), float(v), float(v)]        # scalar -> fixed (not refinable)
            else:
                v = list(v)
                norm[k] = [float(v[0]), float(v[1] if len(v) > 1 else v[0]), float(v[2] if len(v) > 2 else v[0])]
        params0 = {k: v[0] for k, v in norm.items()}
        out["PARAMS"] = norm
    except Exception:
        out["ok"] = False
        out["error"] = traceback.format_exc(limit=3)[-2500:] + API_HINT
        json.dump(out, open(out_path, "w")); return
    for ps in jobs["params"]:
        # Keep provenance per parameter set.  A program may call ``lut.at``
        # while checking corners, so the facade shares one record list with
        # its derived LUTs for this job only.
        lut = dsl.LUT()
        p = dict(params0); p.update(ps)
        try:
            res = ns["design"](p, lut, jobs.get("spec", {}))
            net, pred = (res if isinstance(res, tuple) else (res, {}))
            text = net.text() if hasattr(net, "text") else str(net)
            pred = {k: (float(v) if isinstance(v, (int, float, np.floating)) and math.isfinite(float(v)) else None)
                    for k, v in (pred or {}).items()}
            usage = net.usage() if hasattr(net, "usage") else {"intent_devices": 0, "explicit_devices": 0}
            stats = {"param_count": len(norm), "intent_calls": len(lut.intent_records),
                     "intent_records": lut.intent_records, **usage}
            out["results"].append({"ok": True, "netlist": text, "pred": pred, "params": p,
                                    "program_stats": stats})
        except Exception:
            out["results"].append({"ok": False, "error": traceback.format_exc(limit=4)[-2500:] + API_HINT, "params": p})
    json.dump(out, open(out_path, "w"), default=float)


if __name__ == "__main__":
    main(*sys.argv[1:4])
