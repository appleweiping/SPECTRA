"""Paired exact tests for E4 (fault localisation): top-1 correctness of the LLM given raw netlist+spec table vs. given the
SPECTRA diagnosis, on the same cases (exact two-sided McNemar = binomial test on discordant cases).
Writes results/E4_tests.json."""
import json, glob
from scipy.stats import binomtest
from spectra.paths import ROOT


def norm(xs):
    return [str(x).strip().lower() for x in xs]


def test(d):
    rows = [json.load(open(f)) for f in sorted(glob.glob(str(ROOT / "results" / "raw" / d / "*.json")))]
    rows = [r for r in rows if "raw" in r and "spectra" in r and "truth" in r]
    a = [norm(r["raw"][:1]) == [r["truth"].lower()] for r in rows]
    b = [norm(r["spectra"][:1]) == [r["truth"].lower()] for r in rows]
    only_raw = sum(x and not y for x, y in zip(a, b)); only_diag = sum(y and not x for x, y in zip(a, b))
    p = binomtest(only_raw, only_raw + only_diag, 0.5).pvalue if only_raw + only_diag else 1.0
    return {"n": len(rows), "top1_raw": sum(a) / len(rows), "top1_diag": sum(b) / len(rows),
            "only_raw_correct": only_raw, "only_diag_correct": only_diag, "p_mcnemar_exact": float(p)}


if __name__ == "__main__":
    out = {"opus": test("E4"), "haiku": test("E4_haiku")}
    (ROOT / "results" / "E4_tests.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
