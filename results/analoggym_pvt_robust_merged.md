# AnalogGym HoiLee robust matched receipt

- schema: `spectra-analoggym-shards/v1`
- budget: 300 simulator evaluations per cell
- LLM call field: 12
- verifier conditions per cell: 45
- seeds: 0,1,2
- methods: anaflow_cleanroom, spectra
- complete: `True`
- ranking eligible: `True`

## Aggregate

| Method | Cells | TT success | PVT success | Mean TT violation | Mean PVT violation | Mean wall seconds |
|---|---:|---:|---:|---:|---:|---:|
| anaflow_cleanroom | 3 | 1.000000 | 0.666667 | 0.000000000 | 0.000345748 | 1466.834 |
| spectra | 3 | 1.000000 | 0.666667 | 0.000000000 | 0.000345748 | 2069.891 |

## Cell audit

| Seed | Method | TT pass | TT violation | PVT success | PVT violation | Conditions | Simulations | Calls | Wall seconds |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | anaflow_cleanroom | true | 0.000000000 | false | 0.001037244 | 45 | 300 | 12 | 1447.781 |
| 0 | spectra | true | 0.000000000 | false | 0.001037244 | 45 | 300 | 12 | 2077.612 |
| 1 | anaflow_cleanroom | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 1473.083 |
| 1 | spectra | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 2080.693 |
| 2 | anaflow_cleanroom | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 1479.637 |
| 2 | spectra | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 2051.369 |

The six cells were produced by the source-native AnalogGym harness with the same task topology, simulator, 300-evaluation cap, 12-call field, and 45-condition independent verifier. `anaflow_cleanroom` is a clean-room adapter and is not presented as an official AnaFlow implementation. The receipt is a matched sensitivity comparison and does not replace the frozen primary SIZ7g row.
