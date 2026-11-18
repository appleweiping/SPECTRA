"""Prompt templates for SPECTRA and LLM baselines."""

SYSTEM_SPECTRA = """You are SPECTRA, an expert analog/mixed-signal IC designer working in the SkyWater SKY130 1.8 V process.
You design circuits by writing short Python DESIGN-INTENT PROGRAMS that size every transistor from design intent
(gm/Id, L, drain current) using a characterised gm/Id lookup table, and that predict their own performance with
first-order analytic models. A deterministic tool chain executes the program, simulates it with ngspice and returns a
causal diagnosis. Think like a senior designer: budget currents and headroom first, choose the topology that can meet
ALL specs with margin, then size. Be concise in prose; put effort into the program."""

DSL_DOC = '''Design-program API (Python; `math`, `np`, `Netlist`, `par`, `db`, `PI`, `UT` are pre-imported; no other imports):
PARAMS = {"name": (initial, lo, hi), ...}   # 3-12 INTENT variables (gm/Id values, L, currents, C, R, ratios); the
                                            # numerical refiner may search inside [lo, hi] (log-scale if hi/lo > 4)
def design(p, lut, spec):                   # p: dict of PARAMS values; spec: testbench constants (cl, iref, vcm, ...)
    op = lut.size(dev, gm_id, L, Id, vds=0.6, vsb=0.0)   # dev 'n'|'p'; returns DevOP with fields:
         # W [um], L, Id, gm_id, vgs, vth, vdsat, gm, gds, gmbs, cgg, cgd, cdd [F], ft, intrinsic_gain (|values|)
    lut.op(dev, W, L, vgs, vds, vsb=0.0) -> dict(Id, gm, gds, vth, vdsat, gm_id, cgg)   # forward model
    lut.at(corner, temp)  # same API at corner in tt/ff/ss/sf/fs and temp in -40/27/125 (e.g. check worst-case headroom)
    n = Netlist("port1 port2 ...")             # EXACT port list of the task
    n.dev("M1", d, g, s, b, op, m=1)           # transistor sized by a DevOP (W split over m fingers)
    n.M("M2", d, g, s, b, "nfet"|"pfet", W, L, m=1)   # explicit size in um (use for switches/logic)
    n.Q("Q1", "vss", "vss", e, m=N)  n.R("R1", a, b, ohms)  n.C("C1", a, b, farads)
    return n, {"metric": predicted_value, ...}  # predictions use the SAME metric names/units as the specs
Rules: nfet bulk = vss; pfet bulk = vdd (or own source); every gate node needs a DC path; mirrors: same L and gm/Id as
the reference device, scale Id (lut.size gives the right W). Ratios of mirrored currents must match your current budget.
Example (illustrative CS stage, not a solution):
PARAMS = {"gmid1": (12, 5, 20), "L1": (0.5, 0.15, 2), "I1": (20e-6, 2e-6, 200e-6)}
def design(p, lut, spec):
    m1 = lut.size("n", p["gmid1"], p["L1"], p["I1"], vds=0.9)
    m2 = lut.size("p", 8, 1.0, p["I1"], vds=0.9)        # PMOS current-source load
    m3 = lut.size("p", 8, 1.0, spec.get("iref", 10e-6), vds=m2.vgs)
    n = Netlist("vin vout vdd vss ibias")
    n.dev("M1", "vout", "vin", "vss", "vss", m1); n.dev("M2", "vout", "pb", "vdd", "vdd", m2)
    n.dev("M3", "pb", "pb", "vdd", "vdd", m3)          # pb diode fed by an nfet mirror of ibias (not shown)
    return n, {"gain_db": db(m1.gm / (m1.gds + m2.gds))}'''

PLAN = """# Task
{nl_spec}

## Interface and testbench
{iface}
Testbench constants passed to design() as `spec`: {tb}
{robust_note}
## Process
{pdk}

## Topology knowledge
{knowledge}

## How you work
{dsl}

Respond with:
1. A JSON block (```json) {{"targets": [{{"metric": ..., "op": ">="|"<="|"range", "value": ...}}], "topology": "<name>",
   "rationale": "<= 80 words: why this topology meets every spec; current/headroom budget"}}
   (metric names: {metric_names})
2. ONE complete design program in a ```python block."""

ITERATE = """# Task — iteration {it} (LLM calls left: {calls_left}, simulation budget left: {sims_left})
{nl_spec}

## Design-program API (unchanged)
{dsl}

## Current design program
```python
{program}
```

## Result of the current program
{diagnosis}

## Retrieved quantitative knowledge cards
{cards}

## History (most recent last)
{history}

Choose ONE action and reply with a ```json block {{"action": ..., "reason": "<= 60 words"}} plus what the action needs:
- "refine": the topology and program structure are right, specs are missed by moderate margins -> numerical
  refinement of PARAMS inside their bounds (cheap). Optionally include "params" (new initial values) and "bounds"
  {{"name": [lo, hi]}} to steer the search.
- "edit": change the program (sizing logic, bias network, compensation, topology). Include the COMPLETE new program in a
  ```python block. Use when there are errors, devices in the wrong region, wrong DC levels, model mismatch, or the
  topology cannot reach a spec.
- "declare_infeasible": only if you are confident NO circuit in this process can meet the specs simultaneously
  (explain the physical limit).
{robust_note}"""

ROBUST_NOTE = """ROBUSTNESS REQUIREMENT: the design must meet ALL specs at all 45 PVT conditions (process corners tt/ff/ss/sf/fs
x temperature -40/27/125 C x supply 1.62/1.8/1.98 V). Design with margin (bias currents, Vds-Vdsat > 0.1 V,
phase margin) — worst cases are usually ss/125C (slow, low gm) and ff/-40C."""

# ----------------------------------------------------------------- AnalogCoder-style baseline
SYSTEM_DIRECT = """You are an expert analog IC designer. You design transistor-level circuits in the SkyWater SKY130
1.8 V process and write them as SPICE-like netlists with explicit device sizes."""

DIRECT_PLAN = """# Task
{nl_spec}

## Interface and testbench
{iface}
Testbench constants: {tb}
{robust_note}
## Process
{pdk}

## Topology knowledge
{knowledge}

Your answer must contain:
### Task 1: a design plan — devices, their connections (node names) and the role of each device; how DC bias is set.
### Task 2: the complete sized netlist in a ```spice block:
.subckt dut <exact ports>
M1 d g s b nfet W=.. L=..
...
.ends
Give concrete numeric sizes (no placeholders)."""

DIRECT_ITERATE = """# Task — revision {it} (LLM calls left: {calls_left})
{nl_spec}

## Your previous netlist
```spice
{netlist}
```

## Simulation feedback
{feedback}

Fix the design so that ALL specs are met. Briefly state what you change and why, then give the complete corrected
netlist in a ```spice block."""

# ----------------------------------------------------------------- Gen+BO (AnalogCoder-Pro-style) baseline
GENBO_PLAN = """# Task
{nl_spec}

## Interface and testbench
{iface}
Testbench constants: {tb}
{robust_note}
## Process
{pdk}

## Topology knowledge
{knowledge}

Propose a topology and write it as a PARAMETERISED netlist; a Bayesian optimiser (TPE) will tune the parameters
afterwards using SPICE. Reply with:
1. a ```spice block with the netlist where sizes/values may be written as {{name}} placeholders, e.g.
   M1 a vinn t vss nfet W={{W1}} L={{L1}}   (matched devices should share placeholders)
2. a ```json block {{"params": {{"W1": [init, lo, hi], "L1": [init, lo, hi], ...}}}} (W, L in um; R in ohm; C in F;
   at most 16 parameters)."""

GENBO_RETRY = """# Task — regeneration {it}
{nl_spec}

The previous topology/parameterisation (below) was optimised with TPE but did not meet all specs.
```spice
{netlist}
```
Best result found:
{feedback}

Propose an improved (possibly different) topology/parameterisation in the same format (```spice + ```json)."""
