# Public PTM45 matched receipt

- Source: `jialinlu/opensource-analog-circuits`, `circuits/gh_autockt_opamp`
- Model group: BPTM 45 nm BSIM4 (`45nm_bulk.txt`)
- Simulator: ngspice 44.2
- Protocol: 300 simulations, 12 calls, seeds 0/1/2, SPECTRA versus clean-room AnaFlow adapter
- Corner mode: source TT only. The public deck contains no `.lib` process-corner selector, so the adapter does not synthesize process corners and `ranking_eligible=false`.
- Metrics: AC gain, unity-gain frequency, phase margin. Normalized violation is the mean target residual over these metrics.

| Method | Seed | TT violation | TT pass | PVT violation | PVT pass | Wall seconds |
|---|---:|---:|:---:|---:|:---:|---:|
| SPECTRA | 0 | 0.228280 | no | 0.228280 | no | 7.73 |
| AnaFlow adapter | 0 | 0.283354 | no | 0.283354 | no | 6.02 |
| SPECTRA | 1 | 0.222821 | no | 0.222821 | no | 5.98 |
| AnaFlow adapter | 1 | 0.295630 | no | 0.295630 | no | 6.13 |
| SPECTRA | 2 | 0.238388 | no | 0.238388 | no | 6.31 |
| AnaFlow adapter | 2 | 0.265900 | no | 0.265900 | no | 6.27 |

SPECTRA has lower TT violation on all three seeds. Neither method satisfies all three targets on this source task. This receipt is capability evidence for the PTM45 model group and is excluded from multi-corner SOTA aggregates because the source deck has no matched PVT contract.

Reproduction command, run on the declared server only:

```bash
/root/miniconda3/bin/python scripts/run_public_config_pvt.py \
  --source-root <workspace>/bench_sources/opensource-analog-circuits \
  --config <workspace>/bench_sources/opensource-analog-circuits/circuits/gh_autockt_opamp/config.json \
  --simulator <workspace>/sim-build/ngspice-44.2-install/bin/ngspice \
  --track-id public_v7_ptm45_gh_autockt_opamp_ng44 --pdk ptm45_bsim4 \
  --budget 300 --seeds 0,1,2 --methods spectra,anaflow_cleanroom \
  --output results/public_v7_ptm45_merged.json --pvt-mode source
```
