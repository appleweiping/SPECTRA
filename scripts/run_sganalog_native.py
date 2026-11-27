#!/usr/bin/env python3
"""Native SGAnalog sizing harness for Docker-free, auditable evaluation."""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path

FENCE = re.compile(r"\x60\x60\x60(?:spice|SPICE)?\s*\n(.*?)\x60\x60\x60", re.S)
SUFFIX = {"": 1.0, "n": 1e-9, "p": 1e-12, "u": 1e-6, "m": 1e-3,
          "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}

def logical_lines(text: str) -> list[str]:
    out, cur = [], None
    for raw in text.splitlines():
        if raw.startswith("+") and cur is not None:
            cur += " " + raw[1:].strip()
        else:
            if cur is not None:
                out.append(cur)
            cur = raw
    if cur is not None:
        out.append(cur)
    return out

def number(raw: str) -> float | None:
    raw = raw.strip().strip("'").strip('"')
    m = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([unpKMGkmun]?)", raw)
    if not m:
        return None
    return float(m.group(1)) * SUFFIX[m.group(2)]

def parse_sizes(text: str, reference: dict) -> dict[str, dict[str, float]]:
    match = FENCE.search(text)
    body = match.group(1) if match else text
    result: dict[str, dict[str, float]] = {}
    for line in logical_lines(body):
        toks = line.strip().split()
        if not toks or toks[0] not in reference:
            continue
        vals = {}
        for token in toks[1:]:
            if "=" not in token:
                continue
            key, raw = token.split("=", 1)
            if key not in reference[toks[0]] or raw.startswith("'"):
                continue
            val = number(raw)
            if val is None:
                continue
            if key in ("L", "W") and 0 < val < 0.01:
                val *= 1e6
            vals[key] = val
        if vals:
            result[toks[0]] = vals
    return result

def parse_subckt(deck: str, dut: str) -> tuple[int, int] | None:
    m = re.search(r"^\.subckt\s+" + re.escape(dut) + r"\b[^\n]*\n.*?^\.ends\b",
                  deck, re.S | re.M | re.I)
    return (m.start(), m.end()) if m else None

def patch_deck(deck: str, dut: str, sizes: dict[str, dict[str, float]]) -> str:
    span = parse_subckt(deck, dut)
    if span is None:
        return deck
    block = deck[span[0]:span[1]]
    for dev, params in sizes.items():
        def repl(match: re.Match[str], params=params) -> str:
            line = match.group(0)
            for key, value in params.items():
                line = re.sub(r"(?<![\w])" + re.escape(key) +
                             r"=[\d.eE+-]+", f"{key}={value:g}", line)
            return line
        block = re.sub(r"^" + re.escape(dev) +
                       r"\s[^\n]*(?:\n\+[^\n]*)*", repl, block,
                       count=1, flags=re.M)
    return deck[:span[0]] + block + deck[span[1]:]

def metrics_from_raw(path: Path, parse_raw) -> dict:
    out = {"tran": {}, "ac": {}}
    if not path.is_file():
        return out
    try:
        plots = parse_raw(str(path), max_pts=4000)
    except Exception:
        return out
    for plot in plots:
        series = {s["name"]: s["data"] for s in plot["series"]}
        volts = {k: v for k, v in series.items()
                 if k.lower().startswith("v(") and "." not in k}
        if not volts:
            continue
        candidates = ([k for k in volts if re.search(r"out", k, re.I)]
                      or sorted(volts))
        if "Transient" in plot["plotname"]:
            for vec in candidates:
                y = volts[vec]
                if len(y) > 10:
                    tail = y[len(y) // 3:]
                    out["tran"][vec] = {
                        "swing": float(max(tail) - min(tail)),
                        "mean": float(sum(tail) / len(tail))}
        elif "AC" in plot["plotname"]:
            freqs = series.get("frequency")
            for vec in candidates:
                y = volts[vec]
                if len(y) > 5:
                    mag = [20 * math.log10(max(abs(v), 1e-30)) for v in y]
                    dc, f3 = mag[0], None
                    if freqs:
                        for freq, gain in zip(freqs, mag):
                            if gain <= dc - 3:
                                f3 = float(freq)
                                break
                    out["ac"][vec] = {"dc_gain_db": float(dc), "f3db": f3}
    return out

def anchor(ref_all: dict, model_all: dict) -> dict:
    result = {}
    tr = ref_all.get("tran") or {}
    if tr:
        vec = max(tr, key=lambda v: tr[v]["swing"])
        result["tran"] = {"vector": vec, "ref": tr[vec],
                          "model": (model_all.get("tran") or {}).get(vec)}
    ac = ref_all.get("ac") or {}
    if ac:
        vec = max(ac, key=lambda v: abs(ac[v]["dc_gain_db"]))
        result["ac"] = {"vector": vec, "ref": ac[vec],
                        "model": (model_all.get("ac") or {}).get(vec)}
    return result

def run_deck(deck_text: str, name: str, work: Path, ngspice: str,
             timeout: int) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    deck = re.sub(r"write\s+\S+\.raw", f"write {name}.raw", deck_text,
                  flags=re.I)
    deck_path = work / f"{name}.cir"
    deck_path.write_text(deck, encoding="utf-8")
    started = time.perf_counter()
    try:
        proc = subprocess.run([ngspice, "-b", deck_path.name], cwd=str(work),
                              capture_output=True, text=True, timeout=timeout, env=dict(os.environ, PDK_ROOT="/foss/pdks"))
        log = proc.stdout + "\n" + proc.stderr
        status = "ok" if proc.returncode == 0 and (work / f"{name}.raw").is_file() else "failed"
        return {"rc": proc.returncode, "status": status,
                "seconds": round(time.perf_counter() - started, 4),
                "raw": str(work / f"{name}.raw"),
                "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
                "log_tail": log[-2000:]}
    except subprocess.TimeoutExpired as exc:
        log = (exc.stdout or "") + "\n" + (exc.stderr or "")
        return {"rc": None, "status": "timeout",
                "seconds": round(time.perf_counter() - started, 4),
                "raw": str(work / f"{name}.raw"),
                "log_sha256": hashlib.sha256(log.encode()).hexdigest(),
                "log_tail": log[-2000:]}
    except OSError as exc:
        return {"rc": None, "status": "exec_error",
                "seconds": round(time.perf_counter() - started, 4),
                "raw": str(work / f"{name}.raw"), "error": repr(exc)}

def model_prompt(task: dict, deck: str, seed: int = 0) -> str:
    return f"""Size this analog circuit for the SkyWater sky130A PDK.
Topology and device order are given in the task DUT subcircuit. Return only
completed device lines in a SPICE code block, with L/W/nf for MOSFETs, W/L/MF
for capacitors, and L/mult for resistors.
DUT: {task['dut']} (evaluation seed {seed})
Reference device names and current sizes:
{json.dumps(task['reference'], sort_keys=True)}
Deck excerpt:
{deck[:8000]}"""

def generate_response(prompt: str, model: str, base: str, key: str,
                      timeout: int, seed: int | None = None) -> dict:
    import urllib.request
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 16000}
    if seed is not None:
        body["seed"] = int(seed)
    req_body = json.dumps(body).encode()
    started = time.perf_counter()
    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(base.rstrip("/") + "/chat/completions",
                data=req_body,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + key})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.load(resp)
            choice = payload["choices"][0]
            return {"status": "generated",
                    "text": choice.get("message", {}).get("content", "") or "",
                    "reported_model": payload.get("model", model),
                    "usage": payload.get("usage", {}),
                    "seconds": round(time.perf_counter() - started, 4),
                    "attempts": attempt + 1}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
    return {"status": "generation_error", "error": last_error,
            "seconds": round(time.perf_counter() - started, 4),
            "attempts": 4, "text": ""}

def score(task: dict, ref: dict, model: dict, sizes: dict,
          ref_metrics: dict, model_metrics: dict) -> dict:
    row = {"sized_devices": len(sizes), "n_devices": task["n_devices"],
           "no_answer": len(sizes) == 0,
           "ref_converged": ref["status"] == "ok",
           "model_converged": model["status"] == "ok"}
    tr = anchor(ref_metrics, model_metrics).get("tran")
    ac = anchor(ref_metrics, model_metrics).get("ac")
    fid = []
    if tr and tr.get("model") and tr["ref"]["swing"] > 0.010:
        ratio = tr["model"]["swing"] / tr["ref"]["swing"]
        row["swing_ratio"] = ratio
        fid.append(min(ratio, 1.0 / ratio) if ratio > 0 else 0.0)
    if ac and ac.get("model") and ac["model"].get("dc_gain_db") is not None:
        delta = ac["model"]["dc_gain_db"] - ac["ref"]["dc_gain_db"]
        row["gain_delta_db"] = delta
        ratio = 10 ** (delta / 20.0)
        fid.append(min(ratio, 1.0 / ratio))
    if row["no_answer"] or not row["model_converged"]:
        row["score"] = 0.0
    elif fid:
        row["score"] = sum(fid) / len(fid)
    else:
        row["score"] = 1.0
    return row

def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--sg-root", type=Path, default=Path(os.environ.get("SGANALOG_ROOT", "external/SGAnalog")))
    ap.add_argument("--output", type=Path,
                    default=repo_root / "results/sganalog_native_receipt.json")
    ap.add_argument("--models", default="")
    ap.add_argument("--generate-model", default="")
    ap.add_argument("--model-seeds", default="0")
    ap.add_argument("--api-base", default=os.environ.get("OPENAI_BASE_URL", ""))
    ap.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    ap.add_argument("--ngspice", default=os.environ.get("NGSPICE_BIN", "ngspice"))
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    sg = args.sg_root.resolve()
    tasks = [json.loads(line) for line in (sg / "eval/sizing/tasks.jsonl").read_text().splitlines() if line.strip()]
    sys.path.insert(0, str(sg / "scripts"))
    from sim_ui import parse_raw

    run_root = args.output.resolve().parent / "_sganalog_native_work"
    run_root.mkdir(parents=True, exist_ok=True)
    protocol = {
        "benchmark": "SGAnalog",
        "model": args.generate_model or "legacy-artifact",
        "benchmark_commit": subprocess.check_output(
            ["git", "-C", str(sg), "rev-parse", "HEAD"], text=True).strip(),
        "task_count": len(tasks), "task_ids": [t["task_id"] for t in tasks],
        "pdk": "sky130A", "simulator": Path(args.ngspice).name,
        "budget": {"llm_calls": 12, "simulations": 300},
        "seeds": [int(s) for s in args.model_seeds.split(",") if s.strip()],
        "metrics": ["convergence", "transient.swing", "transient.mean",
                    "ac.dc_gain_db", "ac.f3db", "sizing_fidelity"],
        "reference_metric_rule": "author deck outputs, reporting vector anchored by reference max swing/gain",
        "model_metric_rule": "same deck and same anchored vector",
        "docker_replacement": "native ngspice invocation with generated SPICE decks",
        "budget_status": "server_generated_model" if args.generate_model else "artifact_only_for_preexisting_model_responses",
    }
    out_models = [m.strip() for m in args.models.split(",") if m.strip()]
    model_seeds = [int(s) for s in args.model_seeds.split(",") if s.strip()]
    if not model_seeds:
        model_seeds = [0]
    generated_models = [("generated:" + args.generate_model, seed) for seed in model_seeds] if args.generate_model else []
    all_model_entries = [(name, None) for name in out_models] + generated_models
    results, task_manifest = [], []
    for task in tasks:
        rel = Path(task["tb_cir"])
        if "out/sim_ui/netlists/" in rel.as_posix():
            rel = Path(rel.as_posix().replace("out/sim_ui/netlists/", "circuits/", 1))
        deck_path = sg / rel
        entry = {"task_id": task["task_id"], "repo": task["repo"],
                 "dut": task["dut"], "klass": task["klass"],
                 "deck_relpath": str(rel), "deck_exists": deck_path.is_file()}
        task_manifest.append(entry)
        if not deck_path.is_file():
            entry["error"] = "deck_missing"
            continue
        deck = deck_path.read_text(errors="replace")
        task_root = run_root / task["task_id"]
        ref = run_deck(deck, "reference", task_root / "reference", args.ngspice, args.timeout)
        ref_metrics = metrics_from_raw(Path(ref["raw"]), parse_raw)
        ref["metrics"] = ref_metrics
        for model_name, generation_seed in all_model_entries:
            generated = model_name.startswith("generated:")
            label = model_name.split(":", 1)[1] if generated else model_name
            if generated:
                if not args.api_base or not args.api_key:
                    source = {"status": "not_generated", "error": "missing_api_credentials"}
                else:
                    try:
                        source = generate_response(model_prompt(task, deck, generation_seed or 0), label, args.api_base, args.api_key, args.timeout, generation_seed)
                    except Exception as exc:
                        source = {"status": "generation_error", "error": repr(exc)}
                text = source.get("text", "")
            else:
                path = sg / "eval/sizing" / label / (task["task_id"] + ".json")
                if path.is_file():
                    try:
                        source = json.loads(path.read_text())
                        text = source.get("text", "")
                    except Exception as exc:
                        source, text = {"status": "artifact_error", "error": repr(exc)}, ""
                else:
                    source, text = {"status": "artifact_missing"}, ""
            sizes = parse_sizes(text, task["reference"])
            dir_label = label if generation_seed is None else f"{label}_seed{generation_seed}"
            model_dir = task_root / "models" / dir_label.replace("/", "_")
            if not text:
                model = {"status": "no_answer", "rc": None, "seconds": 0.0, "metrics": {}}
            else:
                model = run_deck(patch_deck(deck, task["dut"], sizes), "model", model_dir, args.ngspice, args.timeout)
                model["metrics"] = metrics_from_raw(Path(model["raw"]), parse_raw)
            srow = score(task, ref, model, sizes, ref_metrics, model["metrics"])
            results.append({
                "task": {"task_id": task["task_id"], "repo": task["repo"],
                         "dut": task["dut"], "klass": task["klass"],
                         "n_devices": task["n_devices"]},
                "model": label, "seed": generation_seed, "source": source.get("status", "artifact"),
                "source_meta": {k: v for k, v in source.items() if k != "text"},
                "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "sizes_sha256": hashlib.sha256(json.dumps(sizes, sort_keys=True).encode()).hexdigest(),
                "sizes": sizes, "reference": ref, "model_run": model, "score": srow})
    payload = {"schema": "sganalog-native-receipt/v1", "protocol": protocol,
               "task_manifest": task_manifest, "results": results,
               "summary": {"tasks": len(tasks), "deck_present": sum(1 for t in task_manifest if t.get("deck_exists")),
                           "rows": len(results)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))
    for model in sorted(set(r["model"] for r in results)):
        rows = [r["score"] for r in results if r["model"] == model]
        print(model, "n=", len(rows), "mean_score=", round(sum(r["score"] for r in rows) / max(1, len(rows)), 4),
              "converged=", sum(1 for r in rows if r["model_converged"]))

if __name__ == "__main__":
    main()
