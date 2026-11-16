"""Designer-specified tier: tasks written from textbook / practitioner targets, independent of the expert
templates used to derive the certified tier. Feasibility is NOT known a priori; it is certified post hoc
(any method or an extended oracle meets the specs) and reported separately."""
import json
from spectra.paths import ROOT
from spectra.bench.nl import render

S = lambda m, op, v: {"metric": m, "op": op, "value": v}
D = [
 ("opamp", "two-stage textbook example", {"cl": 10e-12, "iref": 10e-6}, [S("gain_db", ">=", 70), S("ugbw", ">=", 10e6), S("pm", ">=", 60), S("slew", ">=", 10e6), S("power", "<=", 1e-3), S("swing", ">=", 1.2)], 0),
 ("opamp", "micropower sensor OTA", {"cl": 5e-12, "iref": 1e-6}, [S("gain_db", ">=", 60), S("ugbw", ">=", 1e6), S("pm", ">=", 60), S("power", "<=", 20e-6)], 0),
 ("opamp", "high-speed OTA", {"cl": 1e-12, "iref": 10e-6}, [S("gain_db", ">=", 45), S("ugbw", ">=", 150e6), S("pm", ">=", 55), S("power", "<=", 2e-3)], 0),
 ("opamp", "high-gain op-amp", {"cl": 5e-12, "iref": 10e-6}, [S("gain_db", ">=", 90), S("ugbw", ">=", 5e6), S("pm", ">=", 60), S("power", "<=", 500e-6), S("swing", ">=", 1.0)], 0),
 ("opamp", "large-load buffer amplifier", {"cl": 100e-12, "iref": 10e-6}, [S("gain_db", ">=", 60), S("ugbw", ">=", 2e6), S("pm", ">=", 55), S("power", "<=", 500e-6)], 0),
 ("opamp", "low-noise op-amp", {"cl": 2e-12, "iref": 10e-6}, [S("noise_1k", "<=", 50e-9), S("gain_db", ">=", 60), S("ugbw", ">=", 10e6), S("pm", ">=", 55), S("power", "<=", 1e-3)], 0),
 ("opamp", "robust general-purpose op-amp", {"cl": 2e-12, "iref": 10e-6}, [S("gain_db", ">=", 60), S("ugbw", ">=", 10e6), S("pm", ">=", 50), S("power", "<=", 600e-6)], 1),
 ("ldo", "on-chip LDO 1.2 V / 10 mA", {"vref": 0.6, "iref": 10e-6, "iload_min": 100e-6, "iload_max": 10e-3, "cl": 1e-9, "vout_target": 1.2},
  [S("vout_err_pct", "<=", 2), S("load_reg", "<=", 2.0), S("line_reg", "<=", 0.01), S("psrr_1k", ">=", 40), S("iq", "<=", 100e-6), S("undershoot", "<=", 0.1), S("ripple_settled", "<=", 0.01)], 0),
 ("ldo", "robust LDO 1.2 V / 5 mA", {"vref": 0.6, "iref": 10e-6, "iload_min": 50e-6, "iload_max": 5e-3, "cl": 1e-9, "vout_target": 1.2},
  [S("vout_err_pct", "<=", 3), S("load_reg", "<=", 5.0), S("ripple_settled", "<=", 0.01), S("iq", "<=", 200e-6)], 1),
 ("ref", "bandgap reference", {}, [S("vref", "range", [1.1, 1.3]), S("tc_ppm", "<=", 30), S("power", "<=", 100e-6), S("line_reg", "<=", 0.01), S("startup_ok", ">=", 1)], 0),
 ("ref", "robust bandgap reference", {}, [S("vref", "range", [1.0, 1.35]), S("tc_ppm", "<=", 60), S("power", "<=", 200e-6), S("startup_ok", ">=", 1)], 1),
 ("comparator", "fast continuous-time comparator", {"vod": 10e-3, "cl": 50e-15, "iref": 10e-6, "vcm": 0.9},
  [S("tpd", "<=", 5e-9), S("power", "<=", 200e-6), S("polarity_ok", ">=", 1), S("vout_max", ">=", 1.62), S("vout_min", "<=", 0.18)], 0),
 ("latch", "1 GHz dynamic comparator", {"dv": 1e-3, "fclk": 1e9, "cl": 10e-15, "vcm": 0.9}, [S("correct", ">=", 1), S("delay", "<=", 150e-12), S("energy", "<=", 100e-15)], 0),
 ("vco", "GHz ring VCO", {"vctrl_range": (0.6, 1.4), "tstop": 60e-9, "cl": 10e-15}, [S("f_mid", ">=", 1e9), S("tuning_ratio", ">=", 3), S("power", "<=", 500e-6), S("swing", ">=", 1.4)], 0),
 ("vco", "low-power 100 MHz VCO", {"vctrl_range": (0.6, 1.4), "tstop": 300e-9, "cl": 10e-15}, [S("f_mid", "range", [90e6, 110e6]), S("power", "<=", 20e-6), S("swing", ">=", 1.2)], 0),
 ("filter", "2nd-order Butterworth low-pass 1 MHz", {"kind": "lowpass", "stop_ratio": 10, "iref": 10e-6, "cl": 1e-12},
  [S("fc", "range", [0.95e6, 1.05e6]), S("peaking_db", "<=", 0.5), S("atten_db", ">=", 35), S("gain_db", "range", [-1, 1]), S("power", "<=", 300e-6)], 0),
 ("filter", "3rd-order low-pass 100 kHz", {"kind": "lowpass", "stop_ratio": 10, "iref": 10e-6, "cl": 1e-12},
  [S("fc", "range", [95e3, 105e3]), S("atten_db", ">=", 55), S("gain_db", "range", [-1, 1]), S("power", "<=", 300e-6)], 0),
 ("filter", "band-pass 1 MHz, Q 2-3", {"kind": "bandpass", "iref": 10e-6, "cl": 1e-12}, [S("f0", "range", [0.95e6, 1.05e6]), S("q", "range", [2.0, 3.0]), S("gain_db", ">=", 0), S("power", "<=", 500e-6)], 0),
 ("tia", "300 MHz optical TIA", {"cpd": 0.3e-12, "cl": 0.2e-12, "iref": 10e-6}, [S("zt_dbohm", ">=", 74), S("f3db", ">=", 300e6), S("power", "<=", 2e-3), S("vout_dc", "range", [0.3, 1.5])], 0),
 ("cmirror", "1:4 wide-swing mirror", {"iin": 10e-6, "iout_target": 40e-6, "vout_nom": 0.9, "direction": "sink"}, [S("iout_err_pct", "<=", 2), S("rout", ">=", 5e6), S("v_compliance", "<=", 0.4)], 0),
 ("cmirror", "high-impedance 50 uA sink", {"iin": 50e-6, "iout_target": 50e-6, "vout_nom": 0.9, "direction": "sink"}, [S("iout_err_pct", "<=", 2), S("rout", ">=", 20e6)], 0),
 ("amp", "wideband CS gain stage", {"vin_dc": 0.75, "cl": 0.5e-12, "iref": 10e-6}, [S("gain_db", ">=", 26), S("f3db", ">=", 50e6), S("power", "<=", 300e-6), S("vout_dc", "range", [0.6, 1.2])], 0),
 ("opamp_app", "inverting amplifier x10", {"func": "inv", "iref": 10e-6, "cl": 1e-12}, [S("a1", "range", [-10.1, -9.9]), S("bw", ">=", 2e6), S("power", "<=", 500e-6), S("vout_offset", "range", [-0.02, 0.02])], 0),
 ("opamp_app", "10 kHz integrator", {"func": "integ", "iref": 10e-6, "cl": 1e-12}, [S("f_unity", "range", [9.5e3, 10.5e3]), S("slope_db_dec", "range", [-21, -19]), S("vout_offset", "range", [-0.05, 0.05]), S("power", "<=", 300e-6)], 0),
 ("schmitt", "centred Schmitt trigger", {"inverting": False}, [S("vth_hi", "range", [1.0, 1.2]), S("vth_lo", "range", [0.6, 0.8]), S("vout_max", ">=", 1.7), S("vout_min", "<=", 0.1)], 0),
]

out = []
for i, (fam, title, tb, specs, robust) in enumerate(D):
    t = {"id": f"D{i + 1:02d}-{fam}", "family": fam, "tb": tb, "specs": specs, "tier": "D", "robust": bool(robust),
         "title": title, "ref": None}
    t["nl_spec"] = render(t)
    out.append(t)
with open(ROOT / "data" / "bench" / "designer_tasks.jsonl", "w") as f:
    for t in out:
        f.write(json.dumps(t, default=float) + "\n")
print(len(out), "designer tasks")
print(out[7]["nl_spec"])
