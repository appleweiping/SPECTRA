"""SPECTRA agent: design-intent programs + causal diagnosis + hierarchical repair + PVT-aware refinement."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np

from ..opt.sizing import Var
from ..sim.evaluate import NOMINAL, PVT, cond_name, spec_key
from . import diagnose, llm
from .common import Ctx, task_texts
from .knowledge import KNOWLEDGE
from .prompts import DSL_DOC, ITERATE, PLAN, ROBUST_NOTE, SYSTEM_SPECTRA
from .sandbox import run_program

METRIC_NAMES = {
    "opamp": "gain_db, ugbw, pm, power, cmrr_db, psrr_db, swing, slew, settle, noise_1k, vos",
    "amp": "gain_db, f3db, gbw, power, vout_dc, swing", "tia": "zt_dbohm, f3db, power, vout_dc, in_noise_1m",
    "cmirror": "iout_err_pct, rout, v_compliance, power", "ldo": "vout_err_pct, load_reg, line_reg, psrr_1k, iq, undershoot, overshoot, ripple_settled",
    "ref": "vref, tc_ppm, line_reg, power, psrr_1k, startup_ok", "comparator": "tpd, power, offset, polarity_ok",
    "latch": "correct, delay, energy", "vco": "f_lo, f_mid, f_hi, fmin, fmax, tuning_ratio, kvco, swing, power",
    "filter": "gain_db, fc, atten_db, peaking_db, f0, q, power", "schmitt": "vth_hi, vth_lo, hysteresis, power_avg",
    "opamp_app": "a1, a2, bw, vout_offset, power, f_unity, slope_db_dec",
}

NO_INTENT_DSL = DSL_DOC.split("Example (illustrative")[0].replace(
    "op = lut.size(dev, gm_id, L, Id, vds=0.6, vsb=0.0)", "(lut.size is DISABLED in this mode: give W and L explicitly)") + \
    "\nIn this mode, PARAMS must be device sizes (W, L in um), currents set by mirror ratios, R and C values; use n.M(...) only."


@dataclass
class Config:
    use_intent: bool = True
    use_diag: bool = True
    use_refine: bool = True
    use_knowledge: bool = True
    pvt_strategy: str = "adaptive"     # adaptive | all_corners | nominal_only
    refine_chunk: int = 80
    sens_max_params: int = 8
    minimal: bool = False              # SPECTRA-min: plan once, then intent-space CMA-ES with the whole budget


def _vars_from(params_spec, overrides=None):
    vs = []
    for k, v in params_spec.items():
        init, lo, hi = float(v[0]), float(v[1]), float(v[2])
        if overrides and k in overrides:
            try:
                lo, hi = float(overrides[k][0]), float(overrides[k][1])
            except Exception:
                pass
        if not (hi > lo):
            continue
        vs.append(Var(k, lo, hi, log=(lo > 0 and hi / lo > 4)))
    return vs


class Spectra:
    def __init__(self, task, model="opus", seed=0, cfg: Config | None = None, budget=None, method="spectra"):
        self.cfg = cfg or Config()
        self.ctx = Ctx(task=task, model=model, seed=seed, method=method)
        if budget:
            self.ctx.budget = budget
        self.task = task
        self.tb = dict(task.get("tb", {}))
        self.program = None
        self.params_spec = {}
        self.params = {}
        self.history = []
        self.status = "running"
        self.final_netlist = None

    # ------------------------------------------------------------------ program execution
    def exec_program(self, params_list):
        out = run_program(self.program, params_list, spec=self.tb)
        if out.get("ok") and out.get("PARAMS"):
            self.params_spec = {k: tuple(v) for k, v in out["PARAMS"].items()}
        if not self.cfg.use_intent and "lut.size" in (self.program or ""):
            return {"ok": False, "error": "lut.size() is disabled in this configuration: specify W and L explicitly."}
        return out

    def design_at(self, params):
        out = self.exec_program([params])
        if not out.get("ok"):
            return None, out.get("error", "program failed")
        r = out["results"][0]
        if not r["ok"]:
            return None, r["error"]
        return r, None

    # ------------------------------------------------------------------ refinement in intent space
    def refine(self, conds, budget, bounds=None, init=None):
        import cma
        vars_ = _vars_from(self.params_spec, bounds)
        if not vars_ or budget < 8:
            return None
        x0 = dict(self.params); x0.update(init or {})
        u0 = [v.to_unit(float(x0.get(v.name, self.params_spec[v.name][0]))) for v in vars_]
        es = cma.CMAEvolutionStrategy(u0, 0.15, {"bounds": [0, 1], "seed": self.ctx.seed + 7, "verbose": -9,
                                                 "popsize": max(8, 4 + int(3 * math.log(len(vars_))))})
        best = None
        used = 0
        while used + len(conds) <= budget and not es.stop():
            sols = es.ask()
            ps = [{**x0, **{v.name: v.from_unit(u) for v, u in zip(vars_, s)}} for s in sols]
            out = self.exec_program(ps)
            if not out.get("ok"):
                return None
            from concurrent.futures import ThreadPoolExecutor
            res = out["results"]

            def ev_one(r):
                if not r["ok"]:
                    return None
                return self.ctx.evaluate(r["netlist"], conds)

            with ThreadPoolExecutor(max_workers=4) as ex:
                evs = list(ex.map(ev_one, res))
            scores = []
            for p, r, ev in zip(ps, res, evs):
                used += len(conds)
                sc = ev.score if (ev is not None and ev.status == "ok") else 20.0
                scores.append(sc)
                if ev is not None and ev.status == "ok" and (best is None or sc < best[0]):
                    best = (sc, p, r, ev)
            es.tell(sols, scores)
            if best and best[3].passed:
                break
            if used + len(conds) * len(sols) > budget:
                break
        if best:
            self.params = best[1]
            self.ctx.log("refine", conds=len(conds), used=used, best=round(best[0], 4), passed=best[3].passed)
        return best

    # ------------------------------------------------------------------ sensitivities
    def sensitivities(self, ev0, failing):
        if not failing or not self.params_spec:
            return {}
        names = list(self.params_spec)[: self.cfg.sens_max_params]
        ps = []
        for k in names:
            init, lo, hi = self.params_spec[k]
            v = float(self.params.get(k, init))
            nv = min(hi, v * 1.1) if v > 0 else v + 0.1 * (hi - lo)
            if nv == v:
                nv = max(lo, v / 1.1)
            ps.append({**self.params, k: nv})
        out = self.exec_program(ps)
        if not out.get("ok"):
            return {}
        m0 = list(ev0.per_cond.values())[0]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as ex:
            evs = list(ex.map(lambda r: self.ctx.evaluate(r["netlist"]) if r["ok"] else None, out["results"]))
        sens = {}
        for k, ev in zip(names, evs):
            if ev is None or ev.status != "ok":
                continue
            m1 = list(ev.per_cond.values())[0]
            d = {}
            for met in failing:
                a, b = m0.get(met), m1.get(met)
                if a is None or b is None:
                    continue
                if met.endswith("_db") or met in ("pm", "vout_dc", "swing", "vref", "hysteresis", "vth_hi", "vth_lo",
                                                   "a1", "a2", "offset", "vos", "vout_offset"):
                    d[met] = b - a
                elif a != 0:
                    d[met] = 100 * (b / a - 1)
            sens[k] = d
        return sens

    # ------------------------------------------------------------------ robust stage
    def robust_stage(self, netlist):
        ctx = self.ctx
        evP = ctx.evaluate(netlist, PVT)
        if evP.passed:
            return True, evP
        if not self.cfg.use_refine or self.cfg.pvt_strategy == "nominal_only":
            return False, evP
        rounds = 0
        if self.cfg.pvt_strategy == "all_corners":
            active = list(PVT)
        else:
            worst = sorted(PVT, key=lambda c: -sum(v[2] for v in evP.checks[cond_name(c)].values()))
            active = [NOMINAL] + [c for c in worst[:2] if c != NOMINAL]
        while rounds < 3 and ctx.sims_left() > len(active) * 8 + len(PVT):
            rounds += 1
            chunk = min(ctx.sims_left() - len(PVT), max(self.cfg.refine_chunk, 16 * len(active)))
            best = self.refine(active, chunk)
            if not best:
                break
            evP = ctx.evaluate(best[2]["netlist"], PVT)
            ctx.log("pvt_verify", rounds=rounds, passed=evP.passed, score=round(evP.score, 3), active=len(active))
            if evP.passed:
                self.final_netlist = best[2]["netlist"]
                return True, evP
            if self.cfg.pvt_strategy == "adaptive":
                worst = sorted(PVT, key=lambda c: -sum(v[2] for v in evP.checks[cond_name(c)].values()))
                for c in worst[:2]:
                    if c not in active and len(active) < 6:
                        active.append(c)
        return False, evP

    def pvt_report(self, evP):
        rows = ["Per-condition PVT results (only failing conditions):", "| condition | failing specs (value) |", "|---|---|"]
        worst, wsc = None, -1
        for cn, chk in evP.checks.items():
            bad = [f"{k.split('>')[0].split('<')[0].split('range')[0]}={diagnose.fmt(v[0])}" for k, v in chk.items() if not v[1]]
            tot = sum(v[2] for v in chk.values())
            if tot > wsc:
                worst, wsc = cn, tot
            if bad:
                rows.append(f"| {cn} | {', '.join(bad)} |")
        detail = diagnose.spec_table(self.task, evP, None, cond=worst)
        return "\n".join(rows) + "\n\nWorst condition detail:\n" + detail

    # ------------------------------------------------------------------ minimal variant
    def run_minimal(self):
        ctx, task = self.ctx, self.task
        fixes = 0
        while True:
            err = None
            if not self.program:
                err = "No ```python design program was found in your reply."
            else:
                r, perr = self.design_at(self.params)
                if r is None:
                    err = "PROGRAM ERROR:\n" + perr
                else:
                    ev = ctx.evaluate(r["netlist"])
                    if ev.status in ("parse_error", "erc_error"):
                        err = diagnose.report(task, ev)
            if err is None or fixes >= 2:
                break
            fixes += 1
            text = ctx.ask(f"# Task {task['id']}\n{task['nl_spec']}\n\nYour design program:\n```python\n{self.program}\n```\n"
                           f"failed:\n{err}\n\nReturn the corrected complete program in a ```python block.",
                           SYSTEM_SPECTRA, f"fix{fixes}")
            self.program, self.params = llm.extract_block(text, "python") or self.program, {}
        if err is None and r is not None:
            if ev.passed:
                ok = True
            else:
                reserve = len(PVT) * 3 if task.get("robust") else 0
                best = self.refine([NOMINAL], max(8, ctx.sims_left() - reserve))
                ok = bool(best and best[3].passed)
            if ok:
                r2, _ = self.design_at(self.params)
                net = r2["netlist"] if r2 else r["netlist"]
                if not task.get("robust"):
                    self.status, self.final_netlist = "success", net
                else:
                    okp, _ = self.robust_stage(net)
                    if okp:
                        self.status, self.final_netlist = "success", self.final_netlist or net
        if self.status == "running":
            self.status = "budget_exhausted"
        if self.final_netlist is None:
            self.final_netlist = ctx.best.get("netlist")
        return {"status": self.status, "final_netlist": self.final_netlist, "program": self.program,
                "params": self.params, **ctx.summary(), "events": ctx.events}

    # ------------------------------------------------------------------ main loop
    def run(self):
        ctx, task, cfg = self.ctx, self.task, self.cfg
        t = task_texts(task)
        fam = task["family"]
        t["knowledge"] = KNOWLEDGE[fam] if cfg.use_knowledge else "(none provided)"
        prompt = PLAN.format(**t,
                             dsl=(DSL_DOC if cfg.use_intent else NO_INTENT_DSL), metric_names=METRIC_NAMES[fam])
        text = ctx.ask(prompt, SYSTEM_SPECTRA, "plan")
        self.program = llm.extract_block(text, "python")
        plan_json = llm.extract_json(text) or {}
        ctx.log("plan", topology=plan_json.get("topology"), targets=plan_json.get("targets"))
        if cfg.minimal:
            return self.run_minimal()
        it = 0
        last_score = None
        while ctx.calls_left() > 0 and ctx.sims_left() > 0:
            it += 1
            diag, ev, r = None, None, None
            if not self.program:
                diag = "No ```python design program was found in your reply. Reply with a complete program."
            else:
                r, err = self.design_at(self.params)
                if r is None:
                    diag = "PROGRAM ERROR (fix the program):\n" + err
                else:
                    ev = ctx.evaluate(r["netlist"])
                    if ev.status == "ok" and ev.passed:
                        if not task.get("robust"):
                            self.final_netlist, self.status = r["netlist"], "success"
                            break
                        ok, evP = self.robust_stage(r["netlist"])
                        if ok:
                            self.final_netlist = self.final_netlist or r["netlist"]
                            self.status = "success"
                            break
                        diag = "Nominal (TT) specs PASS but the design fails at PVT corners.\n" + self.pvt_report(evP)
                        if evP and self.cfg.use_diag:
                            rt, _ = diagnose.region_table(ev)
                            diag += "\n\nNominal operating points:\n" + rt
                    elif ev.status != "ok":
                        diag = diagnose.report(task, ev)
                    else:
                        failing = [s["metric"] for s in task["specs"]
                                   if not ev.checks[cond_name(NOMINAL)][spec_key(s)][1]]
                        if cfg.use_diag:
                            sens = self.sensitivities(ev, failing) if ev.score < 4 and ctx.sims_left() > 20 else {}
                            diag = diagnose.report(task, ev, r.get("pred"), sens)
                        else:
                            diag = diagnose.spec_table(task, ev, None)
            score = ev.score if (ev is not None and ev.status == "ok") else None
            hist_line = f"iter {it}: score={'n/a' if score is None else f'{score:.3f}'}"
            if ctx.calls_left() <= 0:
                break
            prompt = ITERATE.format(task_id=task["id"], it=it, calls_left=ctx.calls_left(), sims_left=ctx.sims_left(),
                                    nl_spec=task["nl_spec"], program=self.program or "(none)", diagnosis=diag,
                                    history="\n".join(self.history[-6:]) or "(first iteration)",
                                    robust_note=(ROBUST_NOTE if task.get("robust") else ""))
            if not cfg.use_refine:
                prompt = prompt.replace('- "refine":', '- ("refine" is NOT available in this configuration)')
            text = ctx.ask(prompt, SYSTEM_SPECTRA, f"iter{it}")
            act = llm.extract_json(text) or {}
            a = str(act.get("action", "edit")).lower()
            new_prog = llm.extract_block(text, "python")
            if a == "declare_infeasible":
                self.status = "declared_infeasible"
                ctx.log("declare_infeasible", reason=act.get("reason"))
                break
            if a == "refine" and cfg.use_refine and self.program and r is not None:
                init = act.get("params") if isinstance(act.get("params"), dict) else None
                bounds = act.get("bounds") if isinstance(act.get("bounds"), dict) else None
                if init:
                    self.params.update({k: float(v) for k, v in init.items() if isinstance(v, (int, float))})
                conds = [NOMINAL]
                best = self.refine(conds, min(cfg.refine_chunk, ctx.sims_left()), bounds=bounds)
                self.history.append(hist_line + f" -> refine (best {best[0]:.3f})" if best else hist_line + " -> refine (no result)")
            else:
                if new_prog:
                    self.program, self.params = new_prog, {}
                self.history.append(hist_line + f" -> edit: {str(act.get('reason', ''))[:120]}")
        if self.status == "running":
            self.status = "budget_exhausted"
        if self.final_netlist is None:
            self.final_netlist = ctx.best.get("netlist")
        return {"status": self.status, "final_netlist": self.final_netlist, "program": self.program,
                "params": self.params, **ctx.summary(), "events": ctx.events}
