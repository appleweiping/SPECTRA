"""Create per-instance mismatch (Monte-Carlo) variants of the SKY130 TT FET models for ngspice.

SKY130 implements local mismatch through global '*_slope_spectre' parameters (0 by default; Spectre varies them
per instance). We re-declare these as subcircuit-local parameters drawn with agauss(0,1,1) so that every
instance gets an independent standard-normal draw; the PDK's Pelgrom scaling (slope/sqrt(W*L*mult)) is untouched.
"""
import re
from spectra.paths import PDK_DIR

for dev, fname in [("nfet_01v8", "sky130_fd_pr__nfet_01v8__tt.pm3.spice"), ("pfet_01v8", "sky130_fd_pr__pfet_01v8__tt.pm3.spice")]:
    p = PDK_DIR / "cells" / dev / fname
    s = p.read_text()
    names = sorted(set(re.findall(r"\.param\s+(sky130_fd_pr__\w+_slope_spectre)\s*=", s)))
    lines = s.splitlines()
    out = []
    for ln in lines:
        out.append(ln)
        if re.match(r"^\.param\s+l\s*=\s*1\s+w\s*=\s*1", ln.strip()):
            for nm in names:
                out.append(f".param {nm} = {{agauss(0,1,1)}}")
    q = p.with_name(fname.replace("__tt.pm3", "__tt_mc.pm3"))
    q.write_text("\n".join(out) + "\n")
    print(dev, len(names), "mismatch params ->", q.name)
