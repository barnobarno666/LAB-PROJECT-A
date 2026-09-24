# Isolated nitrogen-flow sensitivity

Run from the project root with:

```powershell
uv run m4-sweep-n2-flow
```

The no-fit Full M4 model holds CO at 0.320 mol/h and H2 at 0.959 mol/h, then varies N2 from 0.400 to 1.200 mol/h. The reference feed contains 0.799 mol/h N2. Temperature is 350 °C, pressure is 1 bar absolute, catalyst mass is 3.12 g, and operation is isothermal with constant pressure along the bed.

Because CO and H2 stay fixed, increasing N2 also increases total feed and dilutes the reactive species. The result isolates N2 as the changed input, while showing its combined dilution and throughput effects. At 1 bar, the model is extrapolated below its 5-15 bar kinetic-fit range. Treat the curve as a conditional model sensitivity, not experimental validation.

`n2_conversion_sweep.csv` contains the individual cases and solver status; `n2_sweep_metadata.json` records inputs and caveats.
