# Open-source analog circuits full ngspice-44.2 capability sweep

The server ran the repository's native `NgspiceBenchmark` on every `32` checked-in `circuits/*/config.json` default point with ngspice-44.2. All 32 simulations returned finite parser records and `_sim_success=true`; total simulator wall time was 341.85s. This is a capability receipt before matched optimization and independent PVT adaptation.

| Source class | Cells | Successful |
|---|---:|---:|
| bjt | 1 | 1 |
| other | 3 | 3 |
| ptm180 | 2 | 2 |
| sky130 | 26 | 26 |

The source suite exposes heterogeneous metric schemas and mostly nominal testbenches. The receipt therefore does not pool objectives across circuits. A future matched track must retain each config's own metric specs, use the same SPECTRA/AnaFlow budget and seeds, and add source-defined PVT or mismatch verification where available.
