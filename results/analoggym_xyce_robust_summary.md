# AnalogGym robust PVT comparison

- Topology: `HoiLee_AFFC_Pin_3`
- Contract: `300` simulations, `12` calls, seeds `0,1,2`, `45` verifier conditions
- Profile: `spectra_robust` for SPECTRA and matched `nominal` clean-room AnaFlow
- Ranking eligible: `True`

| Method | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall seconds |
|---|---:|---:|---:|---:|---:|
| SPECTRA | 0.333 | 0.333 | 0.047664 | 0.077823 | 729.3 |
| AnaFlow clean-room | 1.000 | 0.333 | 0.000000 | 0.084900 | 878.3 |

SPECTRA's PVT-success delta versus AnaFlow is `+0.000` and its mean-PVT-violation reduction is `+0.007077`. Its mean-wall-time delta is `-149.0` seconds. The receipt is a matched public sensitivity stratum and is included by the literal XSOTA audit. It does not by itself establish universal analog-sizing SOTA.
