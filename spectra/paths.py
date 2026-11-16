import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDK_DIR = ROOT / "pdk" / "sky130"
PDK_LIB = PDK_DIR / "sky130_min.lib.spice"
LUT_DIR = ROOT / "data" / "lut"
RUNS_DIR = Path(os.environ.get("SPECTRA_RUNS", ROOT / "runs"))
CORNERS = ["tt", "ff", "ss", "sf", "fs"]
NMOS = "sky130_fd_pr__nfet_01v8"
PMOS = "sky130_fd_pr__pfet_01v8"
