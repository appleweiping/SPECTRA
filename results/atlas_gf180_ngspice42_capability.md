# ATLAS GF180 capability check

The server prepared the public GF180 model tree and ran the ATLAS two-stage GF180 smoke with ngspice-42. The run returned code 1 because the PDK emitted `par_vth=$` and `var_vth` was undefined. ATLAS specifies ngspice 44.2, so this failed cell is excluded from performance ranking.

- Source commit: `dd23c5ba7beb598909be593e4a84c81dab92cc69`
- Simulator: ngspice-42
- Budget: 5
- Seed: 0
- Ranking eligible: false
- Raw log SHA-256: `f2a28df9ebefea98017de21167b501568d1b5a27f282c537aee070b3d9c8ca01`
