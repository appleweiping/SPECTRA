# AnalogGym Leung robust matched receipt

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
| anaflow_cleanroom | 3 | 1.000000 | 0.333333 | 0.000000000 | 0.015551710 | 2445.756 |
| spectra | 3 | 1.000000 | 0.666667 | 0.000000000 | 0.002469135 | 2934.992 |

## Cell audit

| Seed | Method | TT pass | TT violation | PVT success | PVT violation | Conditions | Simulations | Calls | Wall seconds |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | anaflow_cleanroom | true | 0.000000000 | false | 0.008785326 | 45 | 300 | 12 | 2451.766 |
| 0 | spectra | true | 0.000000000 | false | 0.007407406 | 45 | 300 | 12 | 2917.005 |
| 1 | anaflow_cleanroom | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 2442.189 |
| 1 | spectra | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 2895.011 |
| 2 | anaflow_cleanroom | true | 0.000000000 | false | 0.037869806 | 45 | 300 | 12 | 2443.313 |
| 2 | spectra | true | 0.000000000 | true | 0.000000000 | 45 | 300 | 12 | 2992.959 |

The six cells were produced by the source-native AnalogGym harness with the same task topology, simulator, 300-evaluation cap, 12-call field, and 45-condition independent verifier. `anaflow_cleanroom` is a clean-room adapter and is not presented as an official AnaFlow implementation. The receipt is a matched sensitivity comparison and does not replace the frozen primary SIZ7g row.
