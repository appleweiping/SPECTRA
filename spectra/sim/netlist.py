"""Canonical SPECTRA DUT netlist: parse, validate (ERC), and compile to SKY130.

Canonical format (what agents write)::

    .subckt dut vinp vinn vout vdd vss ibias
    M1 d g s b nfet W=4 L=0.5 m=2      * W, L in micrometres
    M2 d g s b pfet W=8 L=0.5
    R1 a b 10k
    C1 a b 2p
    .ends

Only nfet/pfet (SKY130 1.8 V), substrate pnp (``Q1 c b e pnp m=1``; collector
must be on vss), R, C are allowed inside the DUT.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

from ..paths import NMOS, PMOS
PNP = "sky130_fd_pr__pnp_05v5_W3p40L3p40"

SUFFIX = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "k": 1e3,
          "meg": 1e6, "g": 1e9, "t": 1e12}
W_MIN, W_MAX_TOTAL, L_MIN, L_MAX, W_FINGER = 0.42, 5000.0, 0.15, 20.0, 5.0
M_MAX = 200


def parse_value(tok: str) -> float:
    t = tok.strip().lower().rstrip("ohmfvas")  # tolerate units like 10kohm, 2pF
    t = tok.strip().lower()
    for unit in ["ohms", "ohm", "farad", "f)"]:
        pass
    m = re.match(r"^([-+]?\d*\.?\d+(?:e[-+]?\d+)?)\s*(meg|[fpnuµmkgt])?", t)
    if not m:
        raise ValueError(f"bad value '{tok}'")
    v = float(m.group(1))
    if m.group(2):
        v *= SUFFIX[m.group(2)]
    return v


@dataclass
class Device:
    name: str
    kind: str            # 'nfet' | 'pfet' | 'R' | 'C'
    nodes: list
    W: float = 0.0
    L: float = 0.0
    m: int = 1
    value: float = 0.0

    def line(self) -> str:
        if self.kind in ("nfet", "pfet"):
            return f"{self.name} {' '.join(self.nodes)} {self.kind} W={self.W:.4g} L={self.L:.4g} m={self.m}"
        unit = self.value
        return f"{self.name} {' '.join(self.nodes)} {unit:.6g}"


@dataclass
class Circuit:
    name: str
    ports: list
    devices: list = field(default_factory=list)

    def to_text(self) -> str:
        lines = [f".subckt {self.name} {' '.join(self.ports)}"] + [d.line() for d in self.devices] + [".ends"]
        return "\n".join(lines)

    def mosfets(self):
        return [d for d in self.devices if d.kind in ("nfet", "pfet")]

    def area_um2(self) -> float:
        return sum(d.W * d.L * d.m for d in self.mosfets())

    def total_cap(self) -> float:
        return sum(d.value for d in self.devices if d.kind == "C")


class NetlistError(Exception):
    pass


def parse(text: str, expected_ports: list | None = None) -> Circuit:
    """Parse canonical netlist text. Accepts surrounding prose / code fences."""
    m = re.search(r"\.subckt\s+(\S+)\s+([^\n]*)\n(.*?)\n\s*\.ends", text, re.S | re.I)
    if not m:
        raise NetlistError("no '.subckt ... .ends' block found")
    name, ports = m.group(1), m.group(2).split()
    body = m.group(3)
    ports = [p.lower() for p in ports]
    ckt = Circuit(name=name.lower(), ports=ports)
    seen = set()
    # join continuation lines
    raw_lines = []
    for ln in body.splitlines():
        s = ln.split(";")[0].split("$")[0].strip()
        if not s or s.startswith("*"):
            continue
        if s.startswith("+") and raw_lines:
            raw_lines[-1] += " " + s[1:]
        else:
            raw_lines.append(s)
    for s in raw_lines:
        toks = s.split()
        nm = toks[0]
        key = nm.lower()
        if key in seen:
            raise NetlistError(f"duplicate element name {nm}")
        seen.add(key)
        c = key[0]
        if c in ("m", "x") and len(toks) >= 6 and any(t.lower() in ("nfet", "pfet", "nmos", "pmos", NMOS, PMOS) for t in toks[5:6]):
            model = toks[5].lower()
            kind = "nfet" if model in ("nfet", "nmos", NMOS) else "pfet"
            params = {}
            for t in toks[6:]:
                if "=" in t:
                    k, v = t.split("=", 1)
                    params[k.lower()] = v
            try:
                W = parse_value(params.get("w", "1"))
                L = parse_value(params.get("l", "0.15"))
            except ValueError as e:
                raise NetlistError(f"{nm}: {e}")
            # tolerate metres (e.g. W=2e-6) -> micrometres
            if W < 1e-3:
                W *= 1e6
            if L < 1e-3:
                L *= 1e6
            mult = int(round(parse_value(params.get("m", params.get("mult", "1")))))
            nf = int(round(parse_value(params.get("nf", "1"))))
            dev = Device("M" + nm[1:] if c == "x" else nm, kind, [n.lower() for n in toks[1:5]], W=W, L=L,
                         m=max(1, mult))
            ckt.devices.append(dev)
        elif c == "q" and len(toks) >= 5:
            params = {k.lower(): v for k, v in (t.split("=", 1) for t in toks[5:] if "=" in t)}
            mult = int(round(parse_value(params.get("m", params.get("area", "1")))))
            ckt.devices.append(Device(nm, "pnp", [n.lower() for n in toks[1:4]], m=max(1, mult)))
        elif c in ("r", "c") and len(toks) >= 4:
            try:
                v = parse_value(toks[3].split("=")[-1])
            except ValueError as e:
                raise NetlistError(f"{nm}: {e}")
            ckt.devices.append(Device(nm, c.upper(), [toks[1].lower(), toks[2].lower()], value=v))
        else:
            raise NetlistError(f"unsupported element line: '{s}' (allowed: M..nfet/pfet, Q..pnp, R, C)")
    if expected_ports is not None:
        exp = [p.lower() for p in expected_ports]
        if ckt.ports != exp:
            raise NetlistError(f"port list must be exactly: .subckt {name} {' '.join(exp)} (got {' '.join(ckt.ports)})")
    return ckt


def erc(ckt: Circuit, ground="vss", supplies=("vdd",), sources=()) -> tuple[list, list]:
    """Static electrical-rule check. Returns (errors, warnings)."""
    errors, warns = [], []
    conn = defaultdict(list)    # node -> list of (dev, terminal)
    for d in ckt.devices:
        terms = (["d", "g", "s", "b"] if d.kind in ("nfet", "pfet") else
                 ["c", "b", "e"] if d.kind == "pnp" else ["p", "n"])
        for n, t in zip(d.nodes, terms):
            conn[n].append((d, t))
    for p in ckt.ports:
        if p not in conn:
            warns.append(f"port '{p}' is not connected to any device")
    for n, lst in conn.items():
        if n in ckt.ports or n in ("0", "gnd"):
            continue
        if len(lst) < 2:
            d, t = lst[0]
            errors.append(f"node '{n}' is dangling (only {d.name}.{t} connects to it)")
    # DC path analysis: conducting edges = R, MOS d-s; sources = ports
    adj = defaultdict(set)
    for d in ckt.devices:
        if d.kind == "R":
            a, b = d.nodes; adj[a].add(b); adj[b].add(a)
        elif d.kind in ("nfet", "pfet"):
            a, b = d.nodes[0], d.nodes[2]; adj[a].add(b); adj[b].add(a)
        elif d.kind == "pnp":
            c_, b_, e_ = d.nodes
            for a, b in ((c_, b_), (b_, e_), (c_, e_)):
                adj[a].add(b); adj[b].add(a)
    roots = set(ckt.ports) | {"0", "gnd"}
    seen = set(r for r in roots if r in conn)
    stack = list(seen)
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y); stack.append(y)
    for n in conn:
        if n not in seen:
            kinds = {t for _, t in conn[n]}
            errors.append(f"node '{n}' has no DC path to any port/supply (only connects via {sorted(kinds)}); its DC voltage is undefined")
    for d in ckt.mosfets():
        dn, g, s, b = d.nodes
        if d.kind == "nfet" and b != ground:
            errors.append(f"{d.name}: nfet bulk must connect to '{ground}' (p-substrate); got '{b}'")
        if d.kind == "pfet" and b == ground:
            errors.append(f"{d.name}: pfet bulk (n-well) tied to '{ground}' forward-biases the well")
        if dn == s:
            warns.append(f"{d.name}: drain and source are the same node '{dn}' (device does nothing)")
        if d.W < W_MIN or d.W > W_MAX_TOTAL:
            errors.append(f"{d.name}: W={d.W}um out of range [{W_MIN}, {W_MAX_TOTAL}]")
        if d.L < L_MIN or d.L > L_MAX:
            errors.append(f"{d.name}: L={d.L}um out of range [{L_MIN}, {L_MAX}]")
        if d.m > M_MAX:
            errors.append(f"{d.name}: m={d.m} exceeds {M_MAX}")
        if d.kind == "pfet" and s == ground:
            warns.append(f"{d.name}: pfet source on '{ground}' (unusual)")
        if d.kind == "nfet" and s in supplies:
            warns.append(f"{d.name}: nfet source on supply '{s}' (unusual)")
    for d in ckt.devices:
        if d.kind == "pnp" and d.nodes[0] != ground:
            errors.append(f"{d.name}: substrate pnp collector must be '{ground}' (got '{d.nodes[0]}')")
        if d.kind == "R" and not (0.1 <= d.value <= 1e9):
            errors.append(f"{d.name}: resistance {d.value:g} ohm out of range [0.1, 1e9]")
        if d.kind == "C" and not (1e-16 <= d.value <= 1e-6):
            errors.append(f"{d.name}: capacitance {d.value:g} F out of range [0.1f, 1u]")
        if d.kind in ("R", "C") and d.nodes[0] == d.nodes[1]:
            warns.append(f"{d.name}: both terminals on node '{d.nodes[0]}'")
    return errors, warns


def compile_sky130(ckt: Circuit, name: str | None = None) -> str:
    """Emit an ngspice subckt using SKY130 devices with finger splitting."""
    out = [f".subckt {name or ckt.name} {' '.join(ckt.ports)}"]
    for d in ckt.devices:
        if d.kind in ("nfet", "pfet"):
            fingers = max(1, math.ceil(d.W / W_FINGER - 1e-9))
            wf = d.W / fingers
            model = NMOS if d.kind == "nfet" else PMOS
            out.append(f"X{d.name} {' '.join(d.nodes)} {model} W={wf:.4f} L={d.L:.4f} nf=1 m={fingers * d.m}")
        elif d.kind == "pnp":
            out.append(f"X{d.name} {' '.join(d.nodes)} {ground_of(ckt)} {PNP} m={d.m}")
        elif d.kind == "R":
            # SKY130 high-resistance poly first-order model: PDK body TC1/TC2 (tnom 30 C)
            out.append(f"{d.name} {' '.join(d.nodes)} {d.value:.6g} spectra_rpoly")
        elif d.kind == "C":
            out.append(f"{d.name} {' '.join(d.nodes)} {d.value:.6g}")
    out.append(".ends")
    return "\n".join(out)


def ground_of(ckt: Circuit) -> str:
    return "vss" if "vss" in ckt.ports else "0"


def device_op_saves(ckt: Circuit, inst: str) -> list:
    """ngspice vector names for op-point params of every MOSFET in instance `inst`."""
    res = []
    for d in ckt.mosfets():
        model = NMOS if d.kind == "nfet" else PMOS
        base = f"@m.{inst}.x{d.name.lower()}.m{model}"
        for k in ("id", "gm", "gds", "vth", "vdsat", "vds", "vgs", "cgg"):
            res.append((d.name, k, f"{base}[{k}]"))
    return res
