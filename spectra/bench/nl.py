"""Natural-language rendering of benchmark tasks (deterministic, designer style)."""
from __future__ import annotations


def eng(v, unit=""):
    if v is None:
        return "?"
    a = abs(v)
    for s, f in (("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("u", 1e-6), ("n", 1e-9), ("p", 1e-12), ("f", 1e-15)):
        if a >= f * 0.9999:
            x = v / f
            txt = f"{x:.3g}"
            return f"{txt} {s}{unit}".strip()
    return f"{v:.3g} {unit}".strip()


PHRASE = {
    "gain_db": ("DC gain", "dB", "db"), "ugbw": ("unity-gain bandwidth", "Hz", "eng"), "pm": ("phase margin", "degrees", "plain"),
    "power": ("total power consumption (including the reference current)", "W", "eng"), "cmrr_db": ("CMRR at low frequency", "dB", "db"),
    "psrr_db": ("PSRR (VDD) at low frequency", "dB", "db"), "swing": ("output swing", "V", "plain"), "slew": ("slew rate", "V/s", "eng"),
    "settle": ("1% settling time for the large step", "s", "eng"), "noise_1k": ("input-referred noise density at 1 kHz", "V/sqrt(Hz)", "eng"),
    "vos": ("systematic input offset", "V", "eng"), "f3db": ("-3 dB bandwidth", "Hz", "eng"), "gbw": ("gain-bandwidth product", "Hz", "eng"),
    "vout_dc": ("output DC level", "V", "plain"), "zt_dbohm": ("transimpedance gain", "dB-ohm", "db"),
    "in_noise_1m": ("input-referred noise current density at 1 MHz", "A/sqrt(Hz)", "eng"),
    "iout_err_pct": ("output-current error relative to the target", "%", "plain"), "rout": ("output resistance at the nominal output voltage", "ohm", "eng"),
    "v_compliance": ("output compliance voltage (minimum output voltage keeping >=95% of the current)", "V", "plain"),
    "vout_err_pct": ("output-voltage error relative to the target", "%", "plain"), "load_reg": ("load regulation", "V/A (= mV/mA)", "plain"),
    "line_reg": ("line regulation", "V/V", "eng"), "psrr_1k": ("PSRR at 1 kHz", "dB", "db"), "iq": ("quiescent current (at minimum load, including IREF)", "A", "eng"),
    "undershoot": ("load-step undershoot", "V", "eng"), "overshoot": ("load-step overshoot", "V", "eng"),
    "ripple_settled": ("residual ringing (peak-to-peak) 7-10 us after each load step", "V", "eng"),
    "vref": ("reference voltage at 27 C", "V", "plain"), "tc_ppm": ("temperature coefficient over -40..125 C", "ppm/C", "plain"),
    "startup_ok": ("reliable start-up (1 = yes)", "", "plain"), "tpd": ("propagation delay", "s", "eng"), "offset": ("input offset", "V", "eng"),
    "polarity_ok": ("correct output polarity (1 = yes)", "", "plain"), "vout_max": ("output high level", "V", "plain"),
    "vout_min": ("output low level", "V", "plain"), "correct": ("correct decisions (1 = yes)", "", "plain"),
    "delay": ("clock-to-output delay", "s", "eng"), "energy": ("energy per comparison", "J", "eng"),
    "f_mid": ("oscillation frequency at the mid control voltage", "Hz", "eng"), "fmin": ("lowest frequency over the control range", "Hz", "eng"),
    "fmax": ("highest frequency over the control range", "Hz", "eng"), "tuning_ratio": ("tuning ratio fmax/fmin", "", "plain"),
    "kvco": ("VCO gain |Kvco|", "Hz/V", "eng"), "fc": ("-3 dB cutoff frequency", "Hz", "eng"), "atten_db": ("attenuation at the stop frequency", "dB", "db"),
    "peaking_db": ("passband peaking", "dB", "db"), "gain_db_f": ("passband gain", "dB", "db"), "f0": ("centre frequency", "Hz", "eng"),
    "q": ("quality factor", "", "plain"), "vth_hi": ("upper switching threshold", "V", "plain"), "vth_lo": ("lower switching threshold", "V", "plain"),
    "hysteresis": ("hysteresis width", "V", "plain"), "power_avg": ("average power", "W", "eng"), "a1": ("gain from vin1", "V/V", "plain"),
    "a2": ("gain from vin2", "V/V", "plain"), "bw": ("closed-loop -3 dB bandwidth", "Hz", "eng"), "vout_offset": ("output DC offset from 0.9 V", "V", "plain"),
    "f_unity": ("integrator unity-gain frequency", "Hz", "eng"), "slope_db_dec": ("magnitude slope below f_unity", "dB/decade", "plain"),
    "gain_dc_db": ("DC gain", "dB", "db"),
}


def spec_phrase(s):
    name, unit, style = PHRASE.get(s["metric"], (s["metric"], "", "plain"))
    def val(v):
        if style == "eng":
            return eng(v, unit)
        return f"{v:.4g} {unit}".strip()
    if s["op"] == ">=":
        return f"{name} of at least {val(s['value'])}"
    if s["op"] == "<=":
        return f"{name} of at most {val(s['value'])}"
    lo, hi = s["value"]
    return f"{name} between {val(lo)} and {val(hi)}"


FUNC = {
    "opamp": "an operational amplifier (differential input, single-ended output)",
    "amp": "a single-ended voltage amplifier", "tia": "a transimpedance amplifier for a photodiode front-end",
    "cmirror": "a current mirror", "ldo": "a low-dropout linear regulator", "ref": "a self-biased voltage reference",
    "comparator": "a continuous-time voltage comparator", "latch": "a clocked (dynamic) comparator",
    "vco": "a voltage-controlled oscillator", "filter": "an active filter", "schmitt": "a Schmitt trigger",
    "opamp_app": "an op-amp-based analog computing circuit",
}


def conditions(fam, tb):
    c = []
    if "cl" in tb:
        c.append(f"load capacitance {eng(tb['cl'], 'F')}")
    if "iref" in tb and fam not in ("ldo",):
        c.append(f"a {eng(tb['iref'], 'A')} reference current is available at ibias")
    if fam == "ldo":
        c.append(f"input 1.8 V, reference {tb.get('vref', 0.6)} V, target output {tb.get('vout_target')} V, load current "
                 f"{eng(tb.get('iload_min'), 'A')} to {eng(tb.get('iload_max'), 'A')}, {eng(tb['iref'] if 'iref' in tb else 10e-6, 'A')} bias current at ibias")
    if fam == "amp":
        c.append(f"input DC bias {tb.get('vin_dc', 0.75)} V")
    if fam == "tia":
        c.append(f"photodiode capacitance {eng(tb.get('cpd', 0.5e-12), 'F')}")
    if fam == "cmirror":
        c.append(f"input current {eng(tb.get('iin'), 'A')}, target output current {eng(tb.get('iout_target'), 'A')} "
                 f"(ratio {tb.get('iout_target', 1) / tb.get('iin', 1):.3g}) at {tb.get('vout_nom', 0.9)} V")
    if fam == "comparator":
        c.append(f"input common mode {tb.get('vcm', 0.9)} V, overdrive +-{eng(tb.get('vod', 0.01), 'V')}")
    if fam == "latch":
        c.append(f"clock {eng(tb.get('fclk', 5e8), 'Hz')}, input difference +-{eng(tb.get('dv', 2e-3), 'V')} around {tb.get('vcm', 0.9)} V")
    if fam == "vco":
        lo, hi = tb.get("vctrl_range", (0.7, 1.4))
        c.append(f"control voltage range {lo}-{hi} V")
    if fam == "filter":
        c.append(f"{tb.get('kind', 'lowpass')} response" + (f", stop frequency = {tb.get('stop_ratio', 10)} x fc" if tb.get("kind", "lowpass") == "lowpass" else ""))
    if fam == "opamp_app":
        c.append({"inv": "function: inverting amplifier of vin1 (vin2 unused)", "noninv": "function: non-inverting amplifier of vin1 (vin2 unused)",
                  "sum": "function: inverting summer vout - 0.9 = -(g1 (vin1 - 0.9) + g2 (vin2 - 0.9))",
                  "diff": "function: difference amplifier vout - 0.9 = g (vin2 - vin1)", "integ": "function: inverting integrator of vin1 (vin2 unused)"}[tb.get("func", "inv")])
    return c


def render(task):
    fam, tb = task["family"], task["tb"]
    parts = [f"Design {FUNC[fam]} in the SkyWater SKY130 process (1.8 V devices, VDD = 1.8 V)."]
    cond = conditions(fam, tb)
    if cond:
        parts.append("Operating conditions: " + "; ".join(cond) + ".")
    parts.append("Requirements: " + "; ".join(spec_phrase(s) for s in task["specs"]) + ".")
    if task.get("robust"):
        parts.append("All requirements must hold across process corners (tt, ff, ss, sf, fs), temperatures -40/27/125 C "
                     "and supply 1.62-1.98 V.")
    return " ".join(parts)
