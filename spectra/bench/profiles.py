"""Per-family metric profiles used for template exploration and task derivation.

Each metric: (name, sense) with sense '+' (larger is better) or '-' (smaller is better),
and reference scale used in log-normalisation. SANITY are constraints that every
reference design must satisfy (so tasks are realistic).
"""
PROFILES = {
    "opamp": {"metrics": [("gain_db", "+", 40), ("ugbw", "+", 1e7), ("pm", "+", 60), ("power", "-", 1e-4),
                          ("cmrr_db", "+", 60), ("psrr_db", "+", 60), ("swing", "+", 1.0), ("slew", "+", 1e7),
                          ("noise_1k", "-", 1e-7), ("settle", "-", 1e-7)],
              "sanity": [{"metric": "polarity_ok", "op": ">=", "value": 1}, {"metric": "pm", "op": ">=", "value": 50},
                         {"metric": "gain_db", "op": ">=", "value": 30},
                         {"metric": "vout_dc", "op": "range", "value": (0.6, 1.2)}]},
    "amp": {"metrics": [("gain_db", "+", 20), ("f3db", "+", 1e7), ("power", "-", 1e-4), ("swing", "+", 0.8),
                        ("gbw", "+", 1e8)],
            "sanity": [{"metric": "vout_dc", "op": "range", "value": (0.45, 1.35)}]},
    "tia": {"metrics": [("zt_dbohm", "+", 80), ("f3db", "+", 1e8), ("power", "-", 1e-4), ("in_noise_1m", "-", 3e-12)],
            "sanity": [{"metric": "vout_dc", "op": "range", "value": (0.3, 1.5)}]},
    "cmirror": {"metrics": [("rout", "+", 1e6), ("v_compliance", "-", 0.3), ("iout_err_pct", "-", 2)],
                "sanity": [{"metric": "iout_err_pct", "op": "<=", "value": 5}]},
    "ldo": {"metrics": [("load_reg", "-", 1.0), ("line_reg", "-", 0.005), ("psrr_1k", "+", 50), ("iq", "-", 50e-6),
                        ("undershoot", "-", 0.1), ("vout_err_pct", "-", 1)],
            "sanity": [{"metric": "vout_err_pct", "op": "<=", "value": 3}, {"metric": "ripple_settled", "op": "<=", "value": 0.01}]},
    "ref": {"metrics": [("tc_ppm", "-", 50), ("line_reg", "-", 0.01), ("power", "-", 2e-5), ("psrr_1k", "+", 40)],
            "sanity": [{"metric": "startup_ok", "op": ">=", "value": 1}, {"metric": "vref", "op": "range", "value": (0.4, 1.5)}]},
    "comparator": {"metrics": [("tpd", "-", 1e-8), ("power", "-", 1e-4), ("offset", "-", 5e-3)],
                   "sanity": [{"metric": "polarity_ok", "op": ">=", "value": 1}, {"metric": "vout_max", "op": ">=", "value": 1.62},
                              {"metric": "vout_min", "op": "<=", "value": 0.18}]},
    "latch": {"metrics": [("delay", "-", 3e-10), ("energy", "-", 1e-13)],
              "sanity": [{"metric": "correct", "op": ">=", "value": 1}]},
    "vco": {"metrics": [("f_mid", "+", 1e9), ("tuning_ratio", "+", 2), ("power", "-", 1e-4), ("swing", "+", 1.5)],
            "sanity": [{"metric": "swing", "op": ">=", "value": 1.2}]},
    "filter": {"metrics": [("fc", "+", 1e6), ("atten_db", "+", 30), ("power", "-", 1e-4), ("peaking_db", "-", 1)],
               "sanity": [{"metric": "gain_db", "op": "range", "value": (-1.0, 1.0)}]},
    "schmitt": {"metrics": [("hysteresis", "+", 0.3), ("power_avg", "-", 1e-5)],
                "sanity": [{"metric": "vout_max", "op": ">=", "value": 1.7}, {"metric": "vout_min", "op": "<=", "value": 0.1}]},
    "opamp_app": {"metrics": [("bw", "+", 1e6), ("power", "-", 1e-4)],
                  "sanity": [{"metric": "vout_offset", "op": "range", "value": (-0.05, 0.05)}]},
}
