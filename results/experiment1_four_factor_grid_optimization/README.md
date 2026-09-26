# Four-factor full-M4 grid search

This exhaustive discrete grid combines the sampled values from the H2/CO-temperature-pressure map and the H2/CO-space-time contour. It maximizes model-predicted completed-bed outlet CO conversion.

The grid has 20,412 points; 20,412 completed and 0 failed or incomplete. The best sampled case predicts 99.99999281% conversion at H2/CO=5, 370 °C, 15 bar abs, and Wcat/FCO,in=140.4 kg_cat s/mol_CO.

Catalyst mass (3.12 g), N2/CO ratio, assumed bed geometry, and voidage stay fixed. Space time is varied by scaling the CO, H2, and N2 feed rates together at each selected H2/CO ratio.

The search maximizes conversion alone. It does not account for hydrogen consumption, throughput, or pressure cost. Pressures below 5 bar extrapolate the fitted pressure-dependent kinetics; the assumed 1 in × 12 in bed and particle density imply a sparse bed. Treat the result as an exploratory model optimum, not experimental validation. Full case data are in `four_factor_grid_search.csv`; the machine-readable summary is `optimization_summary.json`.

## One-factor sensitivity slices

The one-factor sensitivity figure shows outlet CO conversion against H2/CO ratio, inlet temperature, inlet pressure, and catalyst space time. Each curve is a direct slice through the saved grid: the other three factors stay at the best sampled settings. An open circle marks the best sampled value of the factor on that panel. The four panels use independent, zoomed conversion axes so the small differences near complete conversion remain visible; the pressure slice is restricted to the 5–15 bar kinetic-fit range.

The four-panel figure is saved as one_factor_sensitivities_2x2. The same four plots are also saved separately as sensitivity_h2_co_ratio, sensitivity_inlet_temperature, sensitivity_inlet_pressure, and sensitivity_catalyst_space_time. Each standalone plot places the open-circle legend inside the axes. Each figure is available as PNG, SVG, and PDF. Rebuild all eight files by running uv run python results/experiment1_four_factor_grid_optimization/build_one_factor_sensitivities.py.

## Poster figure

`four_factor_optimization_pressure_slices.png` and `.svg` show H2/CO versus inlet temperature at 5, 9, and 15 bar, with space time fixed at the grid-search optimum. The three panels share one conversion scale. The star marks the optimum in the 15 bar panel. Pressures below 5 bar are omitted because they extrapolate the fitted pressure-dependent kinetics.

Rebuild the figure from the grid CSV with:

```powershell
uv run python results/experiment1_four_factor_grid_optimization/build_optimization_figure.py
```
