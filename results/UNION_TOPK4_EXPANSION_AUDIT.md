# Union-top-k4 expansion audit

The raw archive `work/remote_archive/SIZ11g_SPECTRA_UNION_TOPK4_EXT_V1.tar.gz` has SHA-256
`3B38D3683E3840A72364BAA63452EF78B90CAF12FDADE6FB9C20FD9ED7201D6A`.

| Audit item | Observed |
|---|---:|
| Unique task-seed cells | 276 |
| Expected task-seed cells | 276 |
| Tasks | 92 |
| Families | 12 |
| Robust cells | 57 |
| Crashes | 0 |
| Maximum simulation units | 297 |
| Maximum LLM calls | 3 |
| Cells over the 300/12 caps | 0 |
| Status `success` | 85 |
| Status `budget_exhausted` | 191 |

The audit counts budget-exhausted cells in the denominator. It uses the raw `task` and `seed` fields plus the
relative task path, so a missing or duplicated task-seed cell cannot be hidden by aggregate formatting.
