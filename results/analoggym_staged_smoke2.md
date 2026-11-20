# AnalogGym staged PVT smoke

- Source commit: SPECTRA staged-search implementation (`d0fa3ad`)
- Topology: `HoiLee_AFFC_Pin_3`
- Simulator: ngspice-44.2
- Seed: 0
- Search budget: 6 units for smoke only
- Independent verifier: 45 PVT conditions
- Screening corners: `tt_27C_1.8V`, `ss_-40C_1.62V`, `ss_125C_1.98V`, `ff_-40C_1.98V`, `ff_125C_1.62V`
- Result: finite metrics and 45/45 observed conditions. TT pass and PVT pass are false at this intentionally tiny smoke budget.

This receipt proves the staged path executes on a source-native deck. It is not a matched ranking cell and is excluded from XSOTA-1.
