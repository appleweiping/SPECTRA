"""Stratified subset for ablations / backbone scaling: per family up to 2 hardest nominal tasks (T3 first) + 1 robust."""
import json, sys
from collections import defaultdict
from spectra.paths import ROOT

def main(out="subset_E2.jsonl", per_family=2):
    tasks = [json.loads(l) for l in open(ROOT / "data/bench/tasks.jsonl")]
    by = defaultdict(list)
    for t in tasks:
        by[t["family"]].append(t)
    sel = []
    for fam, ts in sorted(by.items()):
        nom = sorted([t for t in ts if not t.get("robust")], key=lambda t: (-int(t["tier"]), t["id"]))
        rob = [t for t in ts if t.get("robust")]
        sel += nom[:per_family] + rob[:1]
    with open(ROOT / "data/bench" / out, "w") as f:
        for t in sel:
            f.write(json.dumps(t) + "\n")
    print(len(sel), "tasks ->", out, "robust:", sum(t.get("robust", False) for t in sel))

if __name__ == "__main__":
    main()
