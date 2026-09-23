# Reduced M4 fixed-bed methanation reactor

This package solves the steady-state, one-dimensional packed-bed model prepared for Barno and Ashiq. The initial implementation uses the supplied reduced M4 formulation: CO methanation plus WGS. It does not claim to reproduce all three published M4 reactions.

## Run

```powershell
uv sync --group dev
uv run m4-reactor --config configs/assumed_base_case.json --output results/assumed_base_case
uv run pytest
```

The run writes profile data, a run summary, the resolved configuration, and four figures: conversion versus bed length, conversion versus catalyst mass, species concentrations, and temperature/pressure.

`configs/assumed_base_case.json` is a demonstration configuration copied from the supplied reactor formulation. It is not Experiment #1 data. Replace its assumed geometry, catalyst loading, transport, thermal, feed, and pressure values before reporting a comparison with experiment.

## Model contract

- State: molar flows for CO, H2, CH4, H2O, CO2, and N2; temperature; pressure.
- Integration coordinate: total catalyst mass in kg.
- Pressure state and Ergun equation: Pa. Published M4 rate-law partial pressures: bar.
- Kinetics: Celoria et al. (2025), Table 3 M4 rates and Table 5 M4 constants at 598 K.
- Reaction mode: CO methanation plus WGS, where WGS is the negative of the paper's RWGS rate.
- Thermochemistry: constant reaction enthalpy/entropy approximation used only to supply internally consistent equilibrium constants for the initial solver. Replace it with a cited temperature-dependent dataset before final analysis.

The implementation fails explicitly if pressure, hydrogen, total flow, or accepted species flows leave the physical domain. Solver success is recorded separately from a terminal domain event.

## Group 14 verification data

Run the no-fit mechanistic-model comparison with:

```powershell
uv run m4-verify-group14 --data data/group14_observed_data.json --output results/group14_verification
```

This run uses the reported 99.207% CO conversion in `Group-14 experimental data.docx` as the experimental benchmark. It evaluates the unchanged reduced M4 model at the documented 3 g catalyst mass, 350 °C, 760 mmHg, and Table 3 feed, under isothermal constant-pressure assumptions because the document has no bed geometry, particle, dilution, or heat-transfer information. It writes the predicted-versus-observed conversion, a comparison figure, and a separate nitrogen-tracer/GC-table diagnostic. No parameter fitting is performed.

## Experiment 1 verification

Use the user's Experiment 1 report with:

```powershell
uv run m4-verify-experiment1 --data data/experiment1_observed_data.json --output results/experiment1_verification
```

This compares the unchanged reduced M4 model with the report's 40.63% CO conversion using the reported 3.12 g catalyst mass, 350 °C, inlet molar flows, and the 2 bar pressure stated in Appendix A. The report also describes atmospheric-pressure operation, so the output includes that pressure alternative. It preserves the measured 0.799/0.790 mol/h N2 inlet/outlet values without rescaling and records other GC-table inconsistencies. No parameter fitting is performed.
