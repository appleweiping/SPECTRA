# AnalogGym Leung Xyce matched public PVT track

The Leung_NMCF_Pin_3 topology was evaluated on Xyce-7.10 with the same 300 nominal simulation-unit cap, 12-call cap, three seeds and independent 45-condition verifier used for the ngspice track. Both rows use the same translator and metric parser.

| Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation |
|---|---:|---:|---:|---:|---:|
| spectra | 3 | 1.0000 | 0.6667 | 0.000000 | 0.136422 |
| anaflow_cleanroom | 3 | 0.6667 | 0.3333 | 0.002182 | 2.418563 |

All six cells passed strict shard checks with finite violations and exactly 45 observed PVT conditions. On this second topology and simulator, SPECTRA leads the clean-room adapter on both endpoint success rates and both mean violation axes. The adapter remains protocol-aligned rather than an official AnaFlow implementation.
