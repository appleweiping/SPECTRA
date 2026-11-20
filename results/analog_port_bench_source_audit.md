# AnalogPortBench source and golden audit

This server receipt checks the public benchmark inventory and attaches
a source evaluator golden audit when available. It is not a matched
SPECTRA/AnaFlow transfer ranking result.

- Source commit: `5dc16f1c01858664f1912a84abfc06fd4c69f6de`
- Manifest complete: `True`
- Tasks: 54 ({'T1': 10, 'T2': 12, 'T3': 28, 'T4': 4})
- Circuits with 0.18um sources: 10/10
- Golden netlists: 50
- Golden audit: `partial_timeout` (50 rows; jobs 243/250)
- Live corner artifacts: `partial` (242 jobs; 48 complete designs)
- Ranking eligible: `False`

The source tree defines 54 tasks, including four infeasible T4 tasks.
The source evaluator and golden references validate benchmark integrity
under ngspice/SKY130. They do not evaluate SPECTRA or AnaFlow answers.
