# M4 fixed-bed methanation reactor

This package solves the steady-state, one-dimensional packed-bed model prepared for Barno and Ashiq. The `m4_full` mode uses Celoria et al.'s three M4 reactions: CO2 methanation, CO methanation, and RWGS (represented internally as the reverse WGS rate). The earlier CO methanation plus WGS subset remains available as `m4_reduced_co_wgs`.

## Run

```powershell
uv sync --group dev
uv run m4-reactor --config configs/assumed_base_case.json --output results/assumed_full_m4_case
uv run pytest
```

The run writes profile data including the three signed intrinsic reaction rates, a run summary, the resolved configuration, and four figures: conversion versus bed length, conversion versus catalyst mass, species concentrations, and temperature/pressure.

`configs/assumed_base_case.json` is a demonstration configuration based on the supplied reactor formulation, with the tube diameter corrected by the user to 1 in (0.0254 m) and the 12 in (0.3048 m) bed length retained. It is not Experiment #1 data. Catalyst loading, transport, thermal, feed, and pressure inputs remain assumptions and must be checked before reporting a comparison with experiment.

## Model contract

- State: molar flows for CO, H2, CH4, H2O, CO2, and N2; temperature; pressure.
- Integration coordinate: total catalyst mass in kg.
- Pressure state and Ergun equation: Pa. Published M4 rate-law partial pressures: bar.
- Kinetics: Celoria et al. (2025), Table 3 M4 rates and Table 5 M4 constants at 598 K.
- Reaction mode: `m4_full` or `m4_reduced_co_wgs`, selected in the JSON configuration. WGS is the negative of the paper's RWGS rate.
- Dry inlet: for a CO/H2 feed with zero water and CO2, full M4 starts from a leading-order solution at a very small catalyst mass and retains the exact dry composition at the reported inlet. This handles the published R1 inverse-water term without inventing steam. A dry inlet containing CO2 is rejected because the published R1 rate has no finite value there.
- Thermochemistry: constant reaction enthalpy/entropy approximation used only to supply internally consistent equilibrium constants for the initial solver. Replace it with a cited temperature-dependent dataset before final analysis.

The implementation fails explicitly if pressure, hydrogen, total flow, or accepted species flows leave the physical domain. Solver success is recorded separately from a terminal domain event.

## Group 14 verification data

Run the no-fit mechanistic-model comparison with:

```powershell
uv run m4-verify-group14 --data data/group14_observed_data.json --output results/group14_full_m4_verification
```

This run uses the reported 99.207% CO conversion in `Group-14 experimental data.docx` as the experimental benchmark. It evaluates full M4 at the documented 3 g catalyst mass, 350 °C, 760 mmHg, and Table 3 feed, under isothermal constant-pressure assumptions because the document has no bed geometry, particle, dilution, or heat-transfer information. It writes the predicted-versus-observed conversion, a comparison figure, and a separate nitrogen-tracer/GC-table diagnostic. No parameter fitting is performed. The published kinetics were fitted on a different 24 wt% Ni/Al2O3 catalyst at 5 and 15 bar; the approximately 1 bar comparison is an extrapolation.

## Experiment 1 verification

Use the user's Experiment 1 report with:

```powershell
uv run m4-verify-experiment1 --data data/experiment1_observed_data.json --output results/experiment1_full_m4_verification
```

This compares full M4 with the report's 40.63% CO conversion using the reported 3.12 g catalyst mass, 350 °C, inlet molar flows, and the 2 bar pressure stated in Appendix A. The report also describes atmospheric-pressure operation, so the output includes that pressure alternative. It preserves the measured 0.799/0.790 mol/h N2 inlet/outlet values without rescaling and records other GC-table inconsistencies. No parameter fitting is performed. Both verification commands accept `--reaction-mode m4_reduced_co_wgs` to reproduce the older two-reaction comparison in a separate output directory.
