# SGAnalog Xyce AC translator probe

- Source commit: `ebd7e694b79cbe8475c42bd41cf4620c5d537a0f`
- Tasks probed: **17**
- Status counts: `{"failed": 17}`
- Xyce: `<workspace>/sim-build/xyce-7.10-serial-install/bin/Xyce`
- Ranking eligibility: **false**

The probe translates each pinned SGAnalog task deck into a sibling Xyce AC deck, executes Xyce with a bounded timeout, and records the source/translated hashes, return code, log digest, and parser output. The source decks depend on the SGAnalog SKY130 model environment. In this run all 17 probes returned an Xyce parser failure from the included mismatch-function expression, so no AC metric is promoted to a sizing result.

| Task | Status | Return code | Parsed AC keys |
|---|---|---:|---|
| `sz000` | `failed` | 1 | — |
| `sz001` | `failed` | 1 | — |
| `sz002` | `failed` | 1 | — |
| `sz003` | `failed` | 1 | — |
| `sz004` | `failed` | 1 | — |
| `sz005` | `failed` | 1 | — |
| `sz006` | `failed` | 1 | — |
| `sz007` | `failed` | 1 | — |
| `sz008` | `failed` | 1 | — |
| `sz009` | `failed` | 1 | — |
| `sz010` | `failed` | 1 | — |
| `sz011` | `failed` | 1 | — |
| `sz012` | `failed` | 1 | — |
| `sz013` | `failed` | 1 | — |
| `sz014` | `failed` | 1 | — |
| `sz015` | `failed` | 1 | — |
| `sz016` | `failed` | 1 | — |

This is simulator compatibility evidence for the public AC translator. It is not a SIZ7g cell, does not compare SPECTRA with AnaFlow, and cannot support an all-simulator SOTA claim.
