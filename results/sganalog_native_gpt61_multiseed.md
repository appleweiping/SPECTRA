# SGAnalog native GPT-6.1-sol multiseed receipt

- Source commit: `ebd7e694b79cbe8475c42bd41cf4620c5d537a0f`
- Benchmark: SGAnalog `eval/sizing/tasks.jsonl`, 17 tapeout-derived tasks
- PDK: SKY130A
- Simulator: native ngspice-44.2, Docker-free harness
- Model: GPT-6.1-sol
- Seeds: 0, 1, 2, for 51 generated task-seed rows
- Declared SIZ7g budget reference: 300 simulations and 12 LLM calls per task-seed cell. Actual direct Task 2 run: one GPT request plus two native ngspice deck executions per cell. This track is not SIZ7g-budget-compliant and is not pooled into SIZ7g ranking.
- Metrics: convergence, transient swing/mean, AC DC gain, AC f3dB, sizing fidelity

The receipt contains 48 successful model simulations and 3 failed rows. Failures remain in the receipt and in the denominator. The mean sizing-fidelity score across all 51 rows is 0.849548. This is a native harness and source-audit track. Its task-level objective differs from the fixed-topology SIZ7g PVT objective, so it is reported as a separate capability benchmark and is not pooled into the SIZ7g ranking.

Raw generated decks, model outputs and reference outputs remain on the server under `results/_sganalog_native_work/`. The JSON receipt is `results/sganalog_native_gpt61_multiseed.json`.
