# Open-source suite Xyce-7.10 smoke

A server smoke invoked the native open-source benchmark wrapper with a temporary `ngspice` command alias pointing to Xyce-7.10. The PTM180 deck failed because the Xyce parser requires a translated analysis deck. SKY130 and BJT processes exited successfully, but the native ngspice metric parser returned no metrics. These cells are capability diagnostics and are excluded from ranking until an explicit Xyce translator and parser are implemented.
