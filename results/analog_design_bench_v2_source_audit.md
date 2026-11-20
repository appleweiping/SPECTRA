# Analog Design Bench v2 source audit

This receipt audits the public frozen task manifest and instruction files on the
server. The repository does not ship the isolated evaluator or submitted circuit
artifacts. No electrical score, pass rate, or SIZ7g ranking cell is inferred from
this source-only audit.

- Release: `analog-design-bench-v2`
- Source commit: `972f7cd7c95381134387b250edf18f3bd23bdd25`
- Tasks: 50 manifest slots, 50 complete task directories
- PVT-declared tasks: 38
- Mismatch-declared tasks: 36
- Ranking status: `capability_only_source_audit`
- Blocking evidence: isolated verifier and submitted circuit artifacts are external to this git source; no matched SPECTRA/AnaFlow cells were run

## Task metric declarations

| Task | Text-derived metric flags | PVT | Mismatch |
|---|---|:---:|:---:|
| `sky130-class-d-halfbridge-eff95-tt` | frequency, power | no | no |
| `sky130-programmable-icc-iptat-current-mirror-pvt` | dc, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-gmr-degen-amp-constant-gm-pvt` | ac, dc, frequency, mismatch, power, pvt, transient | yes | yes |
| `sky130-gmr-degenerated-diff-amp-gain2-bw70m-power1p2mw-sdr60` | ac, dc, frequency, mismatch, power, transient | no | yes |
| `sky130-bootstrap-driver-pt` | ac, dc, power, transient | no | no |
| `sky130-ring-amp-3stage-gain8-400uw` | ac, power, transient | no | no |
| `sky130-ldo-ota5-robust-pvt-mc` | ac, dc, frequency, mismatch, noise, pvt, transient | yes | yes |
| `sky130-buf-ppsf-bs-gain1-sfdr90` | ac, dc, frequency, mismatch, power, spectral, transient | no | yes |
| `sky130-cml-divider-div2-range1gto10g` | dc, frequency, mismatch, noise, power, transient | no | yes |
| `sky130-tia-zt8k-bw750m-noise5p-sfdr70-power5m-pt` | ac, dc, frequency, mismatch, noise, power, spectral | no | yes |
| `sky130-bandgap-reference-pvt` | dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-beta-multiplier-reference-pvt-mc` | dc, mismatch, power, pvt, transient | yes | yes |
| `sky130-constant-gm-stable-gain-amplifier-pvt` | ac, dc, frequency, mismatch, power, pvt, transient | yes | yes |
| `sky130-low-power-oscillator-2mhz-pvt` | frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-unregulated-charge-pump-10mhz-pvt` | frequency, mismatch, power, pvt, transient | yes | yes |
| `sky130-two-stage-miller-opamp-gain60-ugb200-pm60-noise50uv-pvt` | ac, dc, frequency, noise, power, pvt, transient | yes | no |
| `sky130-nmos-pass-ldo-0p4v-pvt-mc` | ac, dc, mismatch, power, pvt | yes | yes |
| `sky130-regulated-charge-pump-10mhz-pvt` | dc, frequency, mismatch, power, pvt, transient | yes | yes |
| `sky130-switched-capacitor-2to1-converter-pvt` | frequency, noise, power, pvt, transient | yes | no |
| `sky130-analog-input-mux-8to1-pvt` | ac, dc, frequency, mismatch, noise, pvt, transient | yes | yes |
| `sky130-high-psrr-bandgap-reference-pvt` | ac, dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-bootstrap-sampler-fft` | ac, frequency, power | no | no |
| `sky130-cmos-switched-resistor-dac-5bit-pvt` | dc, mismatch, power, pvt, transient | yes | yes |
| `sky130-current-starved-ring-vco-pvt` | frequency, power, pvt, transient | yes | no |
| `sky130-complementary-folded-cascode-ab-opamp-pvt` | ac, dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-fully-differential-ota-c-biquad-pvt` | ac, frequency, mismatch, noise, power, pvt | yes | yes |
| `sky130-flash-adc-4bit-50msps` | dc, frequency, mismatch, noise, power, spectral | no | yes |
| `sky130-fct-residue-amplifier-900msps` | ac, dc, frequency, mismatch, power, pvt, spectral, transient | yes | yes |
| `sky130-ahuja-compensated-two-stage-load-range-pvt` | ac, dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-gilbert-cell-mixer-2p4ghz-pvt-mismatch` | ac, frequency, mismatch, power, pvt, spectral | yes | yes |
| `sky130-bottom-plate-sampler-pvt` | ac, frequency, power, pvt, spectral | yes | no |
| `sky130-cml-tx-driver-28g-nrz-pvt` | ac, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-fd-sampling-feedback-ota-gain1-settling40ns-noise300uv-pvt-mc` | ac, dc, frequency, mismatch, noise, power, pvt, spectral, transient | yes | yes |
| `sky130-fd-sampling-feedback-ota-gain8-settling10ns-noise1mv-pvt-mc` | ac, dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-fd-two-stage-miller-opamp-gain60-pm60-noise50uv-pvt` | ac, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-telescopic-cascode-ota-pvt-fix` | ac, dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
| `sky130-three-stage-nested-miller-ota-pvt` | ac, dc, frequency, mismatch, power, pvt, transient | yes | yes |
| `sky130-capless-ldo-1v0-20ma-pvt` | ac, dc, frequency, mismatch, noise, pvt, transient | yes | yes |
| `sky130-low-power-line-driver-pvt` | ac, dc, frequency, power, pvt | yes | no |
| `sky130-delta-sigma-adc-1bit-first-order-osr32-sndr40` | ac, dc, frequency, mismatch, noise, power, pvt, spectral, transient | yes | yes |
| `sky130-two-stage-miller-opamp-gain70-ugb20-pm60-noise50uv-pvt` | ac, dc, frequency, noise, power, pvt, transient | yes | no |
| `sky130-sar-adc-6bit-async` | dc, mismatch, noise, power, spectral, transient | no | yes |
| `sky130-inductive-lna-2p4ghz-gain12-nf2-pvt` | ac, frequency, noise, power, pvt | yes | no |
| `sky130-ota-5t-gain40-pm60-noise50uv-pvt` | ac, dc, frequency, noise, power, pvt | yes | no |
| `sky130-transistor-divide-by-2` | frequency | no | no |
| `sky130-flash-adc-3bit-pvt` | dc, frequency, mismatch, noise, power, pvt, spectral, transient | yes | yes |
| `sky130-pll-charge-pump-pvt` | dc, mismatch, power, pvt, transient | yes | yes |
| `sky130-sar-adc-4bit-async` | dc, mismatch, noise, power, spectral, transient | no | yes |
| `sky130-lc-vco-2ghz-pvt` | frequency, power, pvt, transient | yes | no |
| `sky130-folded-cascode-ota-gain130-pm60-noise50uv-pvt` | ac, dc, frequency, mismatch, noise, power, pvt, transient | yes | yes |
