# External benchmark expansion audit

The repository-wide task file was converted to the same public fixed-topology sizing schema for all 92 tasks,
covering 12 circuit families. A server preflight completed 48 cells across two op-amp tasks, eight external-primary
rows and three seeds with zero crashes.

The full 92-task × 8-row × 3-seed run was started on the server with the same 300 simulation-unit and 12-call caps.
It produced 122 completed cells before being stopped because robust ngspice evaluations made the projected run time
several hours. These partial cells are archived and excluded from all ranking and SOTA claims. A first launch with
an unset API environment produced only infrastructure failures and was also archived separately.

The completed and statistically analyzed external-primary result remains the preregistered 36-task, six-domain,
three-seed track in `results/external_primary_sota.md`. The expansion audit is retained to make the scope boundary
reproducible rather than silently treating an incomplete repository-wide run as evidence.
