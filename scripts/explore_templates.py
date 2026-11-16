"""Explore each expert template with CMA-ES under random scalarisations of the
family profile; archive every evaluated design (x, metrics) for task derivation."""
import json, math, sys, time
import numpy as np
from spectra.bench.templates import T
from spectra.bench.profiles import PROFILES
from spectra.opt.sizing import run_cmaes
from spectra.sim.evaluate import check
from spectra.paths import ROOT

OUT = ROOT / "data" / "explore"
OUT.mkdir(parents=True, exist_ok=True)
TB_DEFAULT = {
    "opamp": {"cl": 2e-12, "iref": 10e-6}, "amp": {"vin_dc": 0.75, "cl": 0.5e-12}, "tia": {"cpd": 0.5e-12, "cl": 0.2e-12},
    "cmirror": {"iin": 20e-6, "vout_nom": 0.9}, "ldo": {"vref": 0.6, "iload_max": 5e-3, "iload_min": 50e-6, "cl": 1e-9, "vout_target": 1.2},
    "ref": {}, "comparator": {"vod": 10e-3, "cl": 50e-15}, "latch": {"dv": 2e-3, "fclk": 500e6},
    "vco": {"vctrl_range": (0.7, 1.4), "tstop": 100e-9}, "filter": {"kind": "lowpass"}, "schmitt": {"inverting": False},
    "opamp_app": {"func": "inv"},
}
TB_OVERRIDE = {"sf": {"vin_dc": 1.4}, "cm_psrc": {"direction": "source"}}
APP_FUNC = {"app_inv": "inv", "app_sum": "sum", "app_integ": "integ", "app_diff": "diff", "app_noninv": "noninv"}


def make_score(fam, w, tb):
    prof = PROFILES[fam]
    def score(ev):
        if ev.status != "ok" or not ev.per_cond:
            return 50.0
        m = list(ev.per_cond.values())[0]
        _, vio = check(prof["sanity"], m)
        s = 10.0 * vio
        for (name, sense, ref), wi in zip(prof["metrics"], w):
            v = m.get(name)
            if v is None or not np.isfinite(v):
                s += 2.0 * wi; continue
            if name in ("pm",):
                val = min(v, 75) / 60.0
            elif name in ("gain_db", "zt_dbohm", "cmrr_db", "psrr_db", "psrr_1k", "atten_db"):
                val = 10 ** ((v - ref) / 40.0)
            else:
                val = max(abs(v), 1e-30) / ref
            lv = math.log10(max(val, 1e-12))
            s += -wi * lv if sense == "+" else wi * lv
        return s
    return score


def main(names, n_obj=4, budget=120, seed=0):
    jobs = []
    for name in names:
        if T[name]["family"] == "cmirror":
            for tgt in (20e-6, 80e-6, 5e-6):
                jobs.append((name, f"{name}@{int(round(tgt * 1e6))}u", {"iout_target": tgt}))
        else:
            jobs.append((name, name, {}))
    for name, tag, extra in jobs:
        t = T[name]; fam = t["family"]
        tb = dict(TB_DEFAULT[fam]); tb.update(extra)
        tb.update(TB_OVERRIDE.get(name, {}))
        if name in APP_FUNC:
            tb["func"] = APP_FUNC[name]
        if name == "mfb_bpf":
            tb["kind"] = "bandpass"
        task = {"family": fam, "tb": tb, "specs": PROFILES[fam]["sanity"]}
        archive = []
        rng = np.random.default_rng(seed)
        t0 = time.time()
        k = len(PROFILES[fam]["metrics"])
        for j in range(n_obj):
            w = rng.dirichlet(np.ones(k)) * k
            run_cmaes(task, t["build"], t["vars"], budget=budget, seed=seed + j, score_fn=make_score(fam, w, tb),
                      archive=archive, sigma0=0.3)
        with open(OUT / f"{tag}.jsonl", "w") as f:
            for a in archive:
                f.write(json.dumps({"x": a["x"], "metrics": a["metrics"], "sanity_ok": a["passed"], "tb": tb},
                                   default=float) + "\n")
        ok = sum(a["passed"] for a in archive)
        print(f"{tag:14s} {fam:10s} evals={len(archive):4d} sane={ok:4d} time={time.time()-t0:6.1f}s", flush=True)


if __name__ == "__main__":
    names = sys.argv[1:] or list(T)
    main(names)
