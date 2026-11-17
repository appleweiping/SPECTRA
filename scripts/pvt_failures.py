"""Which PVT conditions break designs that pass at TT (all experiments)."""
import json, glob, collections
from spectra.paths import ROOT
c = collections.Counter(); n = 0
for f in glob.glob(str(ROOT / "results/raw/E*/*/*/s*.json")):
    r = json.load(open(f)); v = r.get("verify", {})
    if r.get("task_meta", {}).get("robust") and v.get("tt_pass") and not v.get("pvt_pass"):
        n += 1
        for cn in v.get("pvt_fail_conds", []):
            c[cn] += 1
bc, bt, bv = collections.Counter(), collections.Counter(), collections.Counter()
for k, v in c.items():
    a, b, d = k.split("_")[:3]; bc[a] += v; bt[b] += v; bv[d] += v
json.dump({"n_designs": n, "fail_counts": dict(c), "by_corner": bc, "by_temp": bt, "by_vdd": bv},
          open(ROOT / "results/pvt_failure_conditions.json", "w"), indent=1)
print(n, bv, bc, bt)
