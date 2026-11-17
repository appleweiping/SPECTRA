"""Paired exact tests for E4 fault localisation.

The default invocation targets the GPT-6.1-sol E4g case pool.  A separate
main/alternate directory and output file can be passed for an explicitly
recorded alternate backbone, e.g.::

    python -m scripts.e4_tests --main E4g --alt '' --main-key main \
        --output E4g_tests

This keeps the case-pool equality check useful without hard-coding model names
or the legacy ``E4`` directory.
"""
import argparse, json, glob
from scipy.stats import binomtest
from spectra.paths import ROOT


def norm(xs):
    return [str(x).strip().lower() for x in xs]


def test(d):
    rows = [json.load(open(f)) for f in sorted(glob.glob(str(ROOT / "results" / "raw" / d / "*.json")))]
    rows = [r for r in rows if "raw" in r and "spectra" in r and "truth" in r]
    if not rows:
        return {"n": 0, "top1_raw": None, "top1_diag": None,
                "only_raw_correct": 0, "only_diag_correct": 0, "p_mcnemar_exact": 1.0}
    a = [norm(r["raw"][:1]) == [r["truth"].lower()] for r in rows]
    b = [norm(r["spectra"][:1]) == [r["truth"].lower()] for r in rows]
    only_raw = sum(x and not y for x, y in zip(a, b)); only_diag = sum(y and not x for x, y in zip(a, b))
    p = binomtest(only_raw, only_raw + only_diag, 0.5).pvalue if only_raw + only_diag else 1.0
    return {"n": len(rows), "top1_raw": sum(a) / len(rows), "top1_diag": sum(b) / len(rows),
            "only_raw_correct": only_raw, "only_diag_correct": only_diag, "p_mcnemar_exact": float(p)}


def main(main_exp="E4g", alt_exp="", output="E4g_tests", main_key=None, alt_key=None):
    legacy = main_exp == "E4" and alt_exp == "E4_haiku" and output == "E4_tests"
    main_key = main_key or ("opus" if legacy else "main")
    alt_key = alt_key or ("haiku" if legacy else "alternate")
    out = {main_key: test(main_exp)}
    if alt_exp:
        out[alt_key] = test(alt_exp)
    outp = ROOT / "results" / (output if str(output).endswith(".json") else f"{output}.json")
    outp.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", default="E4g")
    ap.add_argument("--alt", default="", help="empty string disables the alternate arm")
    ap.add_argument("--output", default="E4g_tests")
    ap.add_argument("--main-key")
    ap.add_argument("--alt-key")
    a = ap.parse_args()
    main(a.main, a.alt, a.output, a.main_key, a.alt_key)
