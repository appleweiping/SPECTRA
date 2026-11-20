#!/usr/bin/env python3
"""Offline regression checks for the public Xyce AC translator."""

from __future__ import annotations

import math

from xyce_ac_translator import parse_xyce_ac_output, translate_ac_netlist


def main() -> None:
    deck = """Title line
.param ibias=10u
VDD vdd 0 1.8
I1 out 0 ibias ac=1
.control
ac dec 10 1 1Meg
run
write old.raw
.endc
.end
"""
    translated = translate_ac_netlist(deck)
    assert ".control" not in translated.lower()
    assert "I1 out 0 {ibias}" in translated
    assert "AC 1" in translated
    assert ".PRINT AC VDB(out) VP(out)" in translated
    assert "old.raw" not in translated

    prn = """Index Frequency VDB(V(out)) VP(V(out))
0 1 20 -90
1 10 10 -100
2 100 -10 -120
"""
    ma0 = "gain=20\nugf=FAILED\npm=FAILED\n"
    metrics = parse_xyce_ac_output(prn, ma0)
    assert metrics["gain"] == 20.0
    assert math.isfinite(metrics["ugf"])
    assert math.isfinite(metrics["pm"])
    assert metrics["gbw_hz"] == metrics["ugf"]
    print("xyce_ac_translator: ok")


if __name__ == "__main__":
    main()
