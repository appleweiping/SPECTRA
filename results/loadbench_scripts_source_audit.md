# LOADBench scripts source audit

This is a server-side source audit of the public evaluation helpers. The
large dataset was not downloaded and no electrical ranking cell is inferred.

- Source commit: `03cc45620afbbbee19652d83d625f26f3368d951`
- License status: `no-license-file-in-script-repository`
- Dataset downloaded: `False`
- Ranking status: `capability_only_source_audit`
- Smoke status: `pass`

| File | Role | Present | SHA-256 |
|---|---|:---:|---|
| `README.md` | protocol and metric definitions | yes | `3266ea6d02111d409ac5a0b6277848e9d8d5f0cd91b0402c73a15c8ac2a514a6` |
| `struct_matcher.py` | netlist structural matching | yes | `a128d330e6e56ed8bc04a5c6c6aec2109ea4e8486e2f9b4852c31d74d2ab482f` |
| `circuit_generation_coverage.py` | topology coverage | yes | `a9a640a1f6b50c9a354e6ed802ad0c9c1647b1b00a36b7b936cb995b45aede5d` |
| `topology_selection_eval.py` | top-k and MFHR | yes | `6e12f579b89118e0c8607df413bfbbe3598a9dcffa88c4ce5415871b3af20a2d` |
| `optimization_helper.py` | 12-D hypervolume ratio | yes | `a0f6e23c614df092f3a68b4f8028f4c111bab376fbefa8128ea04ccdc4b1ac02` |
| `inverse_sizing.py` | MAPE, outliers, satisfaction and R2 | yes | `f49da56bb60aa13d14b32c11b3ff7ebb8061905c1c7849400ee5c0c2660694b4` |

The smoke uses synthetic one-row DataFrames and only checks metric
plumbing. It is not a LOADBench dataset result and is excluded from
the SIZ7g and XSOTA-1 gates.
