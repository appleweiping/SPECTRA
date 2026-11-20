#!/usr/bin/env python3
"""Translate ngspice-style AC decks and parse native Xyce AC artifacts.

The public-circuit repositories used by SPECTRA generally provide ngspice
control blocks.  Xyce accepts the circuit and AC analysis, but emits the
frequency response in ``<deck>.FD.prn`` and measurement key/value pairs in
``<deck>.ma0``.  This module keeps the translation deterministic and derives
UGF and phase margin from the response when a Xyce ``.MEASURE`` reports
``FAILED`` at a missing crossing.

No simulator is invoked at import time.  The command line interface is
intended for server-side experiments only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Iterable


_NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"


def translate_ac_netlist(text: str, *, print_nodes: Iterable[str] = ("VDB(out)", "VP(out)")) -> str:
    """Convert an ngspice deck to a portable batch Xyce AC deck.

    Ngspice ``.control`` blocks are removed because Xyce does not interpret
    those commands.  Device, source, ``.lib`` and ``.param`` lines remain
    unchanged.  Existing ``.ac`` and ``.print ac`` directives are retained,
    while measure directives are preserved in Xyce syntax.  If a deck has no
    AC print directive, one is appended before ``.end``.
    """

    lines = text.splitlines()
    # Xyce requires parameter references in element values to be enclosed in
    # braces.  A number of public ngspice decks use bare ``dc=ibias`` or a
    # bare current-source value instead, so collect parameter names before the
    # line-by-line translation.
    parameter_names: set[str] = set()
    for raw in lines:
        match = re.match(r"^\s*\.param\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", raw, re.I)
        if match:
            parameter_names.add(match.group(1).lower())
    output: list[str] = []
    in_control = False
    has_ac = False
    has_print = False
    has_end = False
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower == ".control":
            in_control = True
            continue
        if in_control:
            if lower == ".endc":
                in_control = False
            continue
        if lower.startswith(".ac"):
            has_ac = True
        if re.match(r"^\.print\s+ac\b", lower):
            has_print = True
        if lower == ".end":
            if not has_ac:
                output.append(".AC DEC 101 1 1G")
                has_ac = True
            if not has_print:
                output.append(".PRINT AC " + " ".join(print_nodes))
                has_print = True
            output.append(".END")
            has_end = True
            continue
        # Xyce accepts explicit ``DC value``/``AC value`` fields.  Normalize
        # ngspice's ``dc=value`` and ``ac=value`` spellings, bracing a value
        # when it names a .param symbol.
        def source_value(match: re.Match[str], keyword: str) -> str:
            value = match.group(1)
            if value.startswith("{") or value.lower() not in parameter_names:
                return f"{keyword.upper()} {value}"
            return f"{keyword.upper()} {{{value}}}"

        line = re.sub(r"(?i)\bdc\s*=\s*([^\s]+)",
                      lambda match: source_value(match, "DC"), line)
        line = re.sub(r"(?i)\bac\s*=\s*([^\s]+)",
                      lambda match: source_value(match, "AC"), line)
        fields = line.split()
        if fields and fields[0][:1].lower() in {"i", "v"} and len(fields) >= 4:
            # Handle the ngspice shorthand ``I1 n+ n- ibias``.  Preserve
            # explicit DC/AC forms and numeric values.
            for index in range(3, len(fields)):
                token = fields[index]
                if token.lower() in parameter_names and not token.startswith("{"):
                    fields[index] = "{" + token + "}"
            line = " ".join(fields)
        output.append(line)
    if not has_end:
        if not has_ac:
            output.append(".AC DEC 101 1 1G")
        if not has_print:
            output.append(".PRINT AC " + " ".join(print_nodes))
        output.append(".END")
    return "\n".join(output) + "\n"


def _number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_x_yce_measure(text: str) -> dict[str, float]:
    """Parse Xyce ``.ma0`` key/value output, ignoring FAILED entries."""

    values: dict[str, float] = {}
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(\S+)", line)
        if not match:
            continue
        value = _number(match.group(2))
        if value is not None and math.isfinite(value):
            values[match.group(1).lower()] = value
    return values


def _header_tokens(line: str) -> list[str]:
    return [item for item in re.split(r"\s+|,", line.strip()) if item]


def parse_x_yce_ac_table(text: str) -> tuple[list[float], list[float], list[float]]:
    """Read Xyce ``.FD.prn`` AC output.

    The parser accepts the normal whitespace table emitted by Xyce and CSV
    output.  It returns frequency, dB magnitude and phase in degrees.  Header
    names are matched case-insensitively and parenthesized node names are
    accepted verbatim.
    """

    rows: list[list[str]] = []
    header: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("end of xyce"):
            continue
        tokens = _header_tokens(line)
        if not tokens:
            continue
        if header is None and any(re.search(r"freq|vdb|vp", token, re.I) for token in tokens):
            header = [token.lower() for token in tokens]
            continue
        if header is not None and len(tokens) >= len(header):
            # Ignore the optional integer Index column.  Numeric validation
            # avoids accidentally interpreting diagnostic lines as samples.
            candidate = tokens[:len(header)]
            if all(_number(item) is not None for item in candidate):
                rows.append(candidate)
    if header is None or not rows:
        return [], [], []
    def locate(patterns: tuple[str, ...], fallback: int) -> int:
        for index, name in enumerate(header or []):
            if any(pattern in name for pattern in patterns):
                return index
        return fallback
    freq_col = locate(("freq",), 1 if len(header) >= 4 else 0)
    db_col = locate(("vdb", "db"), 2 if len(header) >= 4 else 1)
    phase_col = locate(("vp", "phase"), 3 if len(header) >= 4 else 2)
    freq: list[float] = []
    magnitude: list[float] = []
    phase: list[float] = []
    for row in rows:
        try:
            f, db, ph = float(row[freq_col]), float(row[db_col]), float(row[phase_col])
        except (IndexError, ValueError):
            continue
        if all(math.isfinite(item) for item in (f, db, ph)) and f > 0:
            freq.append(f)
            magnitude.append(db)
            phase.append(ph)
    return freq, magnitude, phase


def _crossing(freq: list[float], magnitude: list[float], phase: list[float]) -> tuple[float, float] | None:
    for left in range(len(freq) - 1):
        a, b = magnitude[left], magnitude[left + 1]
        if a == 0.0:
            return freq[left], phase[left]
        if a * b > 0.0:
            continue
        if b == a:
            return freq[left], phase[left]
        fraction = -a / (b - a)
        log_f = math.log10(freq[left]) + fraction * (math.log10(freq[left + 1]) - math.log10(freq[left]))
        return 10.0**log_f, phase[left] + fraction * (phase[left + 1] - phase[left])
    return None


def parse_xyce_ac_output(prn_text: str, ma_text: str = "") -> dict[str, float]:
    """Return canonical AC metrics from Xyce artifacts.

    Keys are emitted in both the public-config names (``gain``, ``ugf``,
    ``pm``) and AnalogGym names (``dcgain_db``, ``gbw_hz``,
    ``phase_margin_deg``), allowing one parser to serve both tracks.
    """

    freq, magnitude, phase = parse_x_yce_ac_table(prn_text)
    measures = parse_x_yce_measure(ma_text)
    gain = measures.get("gain")
    if gain is None and magnitude:
        gain = max(magnitude)
    crossing = _crossing(freq, magnitude, phase)
    ugf = measures.get("ugf")
    pm = measures.get("pm")
    if crossing is not None:
        ugf = crossing[0]
        # Xyce's VP output is commonly reported in [0, 180] degrees while
        # ngspice reports the equivalent negative phase.  Prefer a finite
        # .MEASURE PM value, then use the convention indicated by the phase
        # sign for the fallback derived from the response table.
        if pm is None:
            pm = crossing[1] if crossing[1] >= 0.0 else 180.0 + crossing[1]
    result: dict[str, float] = {}
    if gain is not None and math.isfinite(gain):
        result.update({"gain": gain, "dcgain": gain, "dcgain_db": gain})
    if ugf is not None and math.isfinite(ugf):
        result.update({"ugf": ugf, "gain_bandwidth_product": ugf, "gbw_hz": ugf})
    if pm is not None and math.isfinite(pm):
        result.update({"pm": pm, "phase_margin_deg": pm})
    if crossing is not None and math.isfinite(crossing[1]):
        result["phase_in_deg"] = crossing[1]
    return result


def parse_artifacts(deck: Path) -> dict[str, float]:
    """Parse artifacts adjacent to a deck, including Xyce's ``.FD.prn``."""

    candidates = [Path(f"{deck}.FD.prn"), Path(f"{deck}.prn"), Path(f"{deck}.PRINT.prn")]
    prn = next((path for path in candidates if path.exists()), None)
    ma = Path(f"{deck}.ma0")
    return parse_xyce_ac_output(prn.read_text(encoding="utf-8", errors="replace") if prn else "",
                                ma.read_text(encoding="utf-8", errors="replace") if ma.exists() else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path, help="ngspice-style input deck")
    parser.add_argument("--translated", type=Path, help="write translated Xyce deck")
    parser.add_argument("--parse", action="store_true", help="parse adjacent Xyce artifacts")
    args = parser.parse_args()
    if args.translated:
        args.translated.write_text(translate_ac_netlist(args.deck.read_text(encoding="utf-8")), encoding="utf-8")
    if args.parse:
        print(json.dumps(parse_artifacts(args.translated or args.deck), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
