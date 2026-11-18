"""E4: diagnosis accuracy by fault injection.

For reference designs of certified tasks, inject single known faults into the canonical netlist, keep cases
where at least one spec fails, and ask three diagnosers to localise the faulty element:
  rule  : rule-only diagnoser (no LLM): ranks elements by region flags + element-level sensitivities
  raw   : LLM given netlist + spec table (AnalogCoder-style feedback)
  spectra: LLM given netlist + SPECTRA diagnosis (regions, margins, element sensitivities, rule hypotheses)
Metrics: top-1 / top-3 element accuracy, stratified by fault class.
"""
import json, math, random, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from spectra.paths import ROOT
from spectra.bench.templates import T
from spectra.sim.netlist import parse
from spectra.sim.evaluate import evaluate, region_report, spec_key, violation
from spectra.agent import diagnose, llm

OUT = ROOT / "results" / "raw" / "E4"
CLASSES = ["undersize_W", "short_L", "mirror_ratio", "comp_cap", "bias_starve", "miswire_gate", "resistor_value"]


def inject(ckt, cls, rng):
    devs = ckt.devices
    mos = [d for d in devs if d.kind in ("nfet", "pfet")]
    if cls == "undersize_W":
        d = rng.choice(mos); d.W = max(0.42, d.W * 0.15); return d.name
    if cls == "short_L":
        c = [d for d in mos if d.L >= 0.4]
        if not c: return None
        d = rng.choice(c); d.L = 0.15; return d.name
    if cls == "mirror_ratio":   # a device whose gate is driven by a diode-connected device
        diodes = {d.nodes[1] for d in mos if d.nodes[0] == d.nodes[1]}
        c = [d for d in mos if d.nodes[1] in diodes and d.nodes[0] != d.nodes[1]]
        if not c: return None
        d = rng.choice(c); d.m = d.m * 3; return d.name
    if cls == "comp_cap":
        c = [d for d in devs if d.kind == "C"]
        if not c: return None
        d = rng.choice(c); d.value *= 0.05; return d.name
    if cls == "bias_starve":   # devices with gate on ibias / bias nodes and source on vss
        c = [d for d in mos if d.nodes[1] in ("ibias",) and d.nodes[0] != d.nodes[1]]
        if not c: return None
        d = rng.choice(c); d.W = max(0.42, d.W * 0.2); return d.name
    if cls == "miswire_gate":
        nodes = sorted({n for d in devs for n in d.nodes if n not in ("vdd", "vss")})
        d = rng.choice(mos)
        alt = [n for n in nodes if n != d.nodes[1]]
        if not alt: return None
        d.nodes[1] = rng.choice(alt); return d.name
    if cls == "resistor_value":
        c = [d for d in devs if d.kind == "R"]
        if not c: return None
        d = rng.choice(c); d.value *= rng.choice([0.05, 20]); return d.name
    return None


def element_sensitivity(task, ckt, failing):
    """d(failing metrics)/d(+20% element size) for every element (one sim each)."""
    base = evaluate(task, ckt.to_text())
    m0 = base.per_cond.get("tt_27C_1.8V", {})
    specs = {s["metric"]: s for s in task.get("specs", [])}
    jobs = []
    for d in ckt.devices:
        import copy
        c2 = copy.deepcopy(ckt)
        e = next(x for x in c2.devices if x.name == d.name)
        if e.kind in ("nfet", "pfet"):
            e.W *= 1.2
        elif e.kind in ("R", "C"):
            e.value *= 1.2
        else:
            continue
        jobs.append((d.name, c2.to_text()))
    with ThreadPoolExecutor(4) as ex:
        evs = list(ex.map(lambda j: evaluate(task, j[1]), jobs))
    sens = {}
    for (nm, _), ev in zip(jobs, evs):
        if ev.status != "ok":
            continue
        m1 = ev.per_cond["tt_27C_1.8V"]
        d = {}
        dv = {}
        for met in failing:
            a, b = m0.get(met), m1.get(met)
            if a is None or b is None:
                continue
            d[met] = (b - a) if (met.endswith("_db") or met in ("pm", "vout_dc", "swing")) else (100 * (b / a - 1) if a else 0)
            if met in specs:
                dv[met] = violation(specs[met], b) - violation(specs[met], a)
        if dv:
            d["_violation"] = dv
        sens[nm] = d
    return sens


def rule_rank(ev, sens, failing, ckt):
    score = {d.name: 0.0 for d in ckt.devices}
    for d, r in region_report(ev.ops).items():
        if r["region"] in ("triode", "off") or r["region"].startswith("subthreshold"):
            score[d] = score.get(d, 0) + 5 + max(0, -r["vds_margin"]) * 10
        elif r["region"] == "edge-of-saturation":
            score[d] = score.get(d, 0) + 2
    for nm, dd in sens.items():
        for met, v in dd.items():
            if met.startswith("_"):
                continue
            score[nm] = score.get(nm, 0) + min(5, abs(v) / 5)
    return [k for k, _ in sorted(score.items(), key=lambda kv: -kv[1])]


PROMPT = """A transistor-level circuit in SKY130 (1.8 V) was designed for the task below, but ONE element was then
corrupted by a single fault (wrong size/value, wrong mirror ratio, wrong gate connection, ...). The circuit now fails
some specs. Identify the corrupted element.

Task: {nl}

Netlist (canonical format; W/L in um):
```spice
{net}
```

{evidence}

Reply with a ```json block {{"ranking": ["<most likely element name>", "<2nd>", "<3rd>"], "fault": "<short description>"}}."""


def main(n_per_template=6, seed=0, model="gpt-6.1-sol"):
    import zlib
    global OUT
    exp_tag = "E4g" if model.lower() in {"gpt", "openai", "gpt-mini", "gpt-6.1-sol", "gpt61-sol"} else f"E4_{model}"
    OUT = ROOT / "results" / "raw" / exp_tag
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(l) for l in open(ROOT / "data" / "bench" / "tasks.jsonl")]
    seen, cases = set(), []
    for t in tasks:
        if t.get("robust") or t["ref"]["template"] in seen:
            continue
        seen.add(t["ref"]["template"])
        rng = random.Random(seed * 1000 + zlib.crc32(t["ref"]["template"].encode()))
        net = T[t["ref"]["template"]]["build"](t["ref"]["x"])
        made = 0
        for attempt in range(40):
            if made >= n_per_template:
                break
            cls = CLASSES[(attempt + made) % len(CLASSES)]
            ckt = parse(net)
            name = inject(ckt, cls, rng)
            if not name:
                continue
            ev = evaluate(t, ckt.to_text())
            if ev.status != "ok" or ev.passed:
                continue
            failing = [s["metric"] for s in t["specs"] if not ev.checks["tt_27C_1.8V"][spec_key(s)][1]]
            cases.append((t, ckt, name, cls, ev, failing, f"{t['ref']['template']}_{made}")); made += 1
    print(len(cases), "fault cases", flush=True)

    def run_case(i):
        t, ckt, name, cls, ev, failing, key = cases[i]
        fp = OUT / f"{key}.json"
        if fp.exists():
            return json.loads(fp.read_text())
        sens = element_sensitivity(t, ckt, failing)
        rule = rule_rank(ev, sens, failing, ckt)
        raw_ev = diagnose.spec_table(t, ev, None)
        analysis = diagnose.analyze(t, ev, None, sens)
        spectra_ev = diagnose.render_analysis(analysis)
        res = {"case": key, "task": t["id"], "template": t["ref"]["template"], "truth": name, "class": cls,
               "failing": failing, "rule": rule[:3], "diagnosis": analysis,
               "mechanism": {"attribution": analysis.get("attribution", []),
                             "d_violation": {a["param"]: a["d_vio"] for a in analysis.get("attribution", [])
                                             if a.get("d_vio") is not None}}}
        for arm, evid in (("raw", raw_ev), ("spectra", spectra_ev)):
            r = llm.call(PROMPT.format(nl=t["nl_spec"], net=ckt.to_text(), evidence=evid),
                         "You are an expert analog IC designer debugging a circuit.", model=model,
                         run_tag=f"E4|{key}|{arm}", tag=f"E4:{arm}")
            js = llm.extract_json(r["text"]) or {}
            res[arm] = [str(x) for x in (js.get("ranking") or [])][:3]
            res[arm + "_cost"] = r["cost_usd"]
        fp.write_text(json.dumps(res))
        return res

    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(run_case, range(len(cases))))
    summ = {}
    for arm in ("rule", "raw", "spectra"):
        norm = lambda xs: [str(x).strip().lower() for x in xs]
        top1 = sum(norm(r[arm][:1]) == [r["truth"].lower()] for r in results) / len(results)
        top3 = sum(r["truth"].lower() in norm(r[arm][:3]) for r in results) / len(results)
        summ[arm] = {"top1": top1, "top3": top3}
        for cls in CLASSES:
            rr = [r for r in results if r["class"] == cls]
            if rr:
                summ[arm][cls] = {"n": len(rr), "top1": sum(norm(r[arm][:1]) == [r["truth"].lower()] for r in rr) / len(rr),
                                  "top3": sum(r["truth"].lower() in norm(r[arm][:3]) for r in rr) / len(rr)}
    summ["n_cases"] = len(results)
    (ROOT / "results" / ("E4g_summary.json" if exp_tag == "E4g" else f"{exp_tag}_summary.json")).write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main(model=sys.argv[1] if len(sys.argv) > 1 else "gpt-6.1-sol")
