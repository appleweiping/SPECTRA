# Public three-PDK TT adapter run v2

This server run uses the same 300 simulator evaluations and seeds 0, 1, 2 for both rows on three public configurations. It is a TT-only adapter audit because these source configs do not expose a common process/voltage/temperature evaluator. `ranking_eligible` remains false.

| Task / model group | SPECTRA TT success | AnaFlow clean-room TT success | SPECTRA mean violation | AnaFlow mean violation | Budget cells |
|---|---:|---:|---:|---:|---:|
| bjt_ce_amp | 3/3 | 3/3 | 0.0000 | 0.0000 | 3×300 |
| gh_autockt_opamp | 0/3 | 0/3 | 0.2251 | 0.2816 | 3×300 |
| ptm180nm_opamp | 2/3 | 2/3 | 0.0102 | 0.0115 | 3×300 |

The public adapter row does not establish PVT success, cross-simulator parity, or a paper-faithful AnaFlow implementation. PTM180 is mixed across seeds, BJT is tied, and BPTM45 has zero TT passes for both methods despite lower SPECTRA violation.
