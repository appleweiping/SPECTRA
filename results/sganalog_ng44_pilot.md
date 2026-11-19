# SGAnalog ngspice-44.2 pilot receipt

The server cloned SGAnalog at commit `ebd7e694b79cbe8475c42bd41cf4620c5d537a0f`, resolved its `/foss/pdks/sky130A` include path to the pinned server SKY130 PDK, and ran the shipped `eval/sizing_pilot/model.cir` and `ref.cir` with ngspice-44.2. Both decks completed with raw data rows and no fatal simulator error.

The full SGAnalog harness expects the repository's pinned Docker image, which is unavailable on the server. This receipt therefore demonstrates source-netlist execution and keeps the pilot separate from a full 17-task sizing ranking.
