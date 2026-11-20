# AnalogGym staged PVT sensitivity comparison

- Topology: `HoiLee_AFFC_Pin_3`
- Contract: `300` simulations, `12` calls, seeds `0,1,2`, `45` verifier conditions
- Profile: `spectra_staged` with fixed screening corners
- Ranking eligible: `False` because the staged arm is a separate sensitivity track

| Method | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall seconds |
|---|---:|---:|---:|---:|---:|
| SPECTRA staged | 1.000 | 1.000 | 0.000000 | 0.000000 | 2283.4 |
| AnaFlow clean-room | 1.000 | 0.667 | 0.000000 | 0.000346 | 1919.5 |

The staged arm leads AnaFlow on PVT success and both violation endpoints, while TT success is tied at 1.0. This is a benchmark-scoped sensitivity result. It is not merged into the frozen SIZ7g primary comparison and does not satisfy XSOTA-1.

The staged search is slower on average than AnaFlow on this topology (2283.4 s versus 1919.5 s), so the sensitivity lead is electrical and does not establish an efficiency lead.
