# SGAnalog source audit

- Source: `Li-Yueting/SGAnalog`, commit `ebd7e694b79cbe8475c42bd41cf4620c5d537a0f`
- Task manifest: `eval/sizing/tasks.jsonl`, 17/17 task records
- Deck resolution: 17/17 published testbench decks found
- Classes: ADC 1, DAC 4, op-amp 3, oscillator 1, passive 4, power 4
- Device metadata: every task's `n_devices` agrees with its reference-device map
- Task-file SHA-256 and per-deck SHA-256 are recorded in `sganalog_source_audit.json`
- Audit execution: server-only source audit, no simulator invocation

This receipt establishes source and manifest completeness. The native Task 2
run remains a separate capability tier. Its direct cells use one model request
and two deck executions per task-seed, so they are not inserted into the
300-simulation/12-call SIZ7g ranking.
