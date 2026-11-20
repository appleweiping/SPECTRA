# AnalogGym robust PVT comparison

- Topology: `Leung_NMCF_Pin_3`
- Contract: `300` simulations, `12` calls, seeds `0,1,2`, `45` verifier conditions
- Profile: `spectra_robust` for SPECTRA and matched `nominal` clean-room AnaFlow
- Ranking eligible: `True`

| Method | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall seconds |
|---|---:|---:|---:|---:|---:|
| SPECTRA | 0.667 | 0.333 | 0.035259 | 0.035090 | 588.9 |
| AnaFlow clean-room | 0.667 | 0.333 | 0.002182 | 2.418563 | 2416.0 |

SPECTRA's PVT-success delta versus AnaFlow is `+0.000` and its mean-PVT-violation reduction is `+2.383474`. Its mean-wall-time delta is `-1827.1` seconds. The receipt is a matched public sensitivity stratum and is included by the literal XSOTA audit. It does not by itself establish universal analog-sizing SOTA.
