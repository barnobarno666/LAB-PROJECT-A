# Four-factor full-M4 grid search

This exhaustive discrete grid combines the sampled values from the H2/CO-temperature-pressure map and the H2/CO-space-time contour. It maximizes model-predicted completed-bed outlet CO conversion.

The grid has 20,412 points; 20,412 completed and 0 failed or incomplete. The best sampled case predicts 99.99999281% conversion at H2/CO=5, 370 °C, 15 bar abs, and Wcat/FCO,in=140.4 kg_cat s/mol_CO.

Catalyst mass (3.12 g), N2/CO ratio, assumed bed geometry, and voidage stay fixed. Space time is varied by scaling the CO, H2, and N2 feed rates together at each selected H2/CO ratio.

The search maximizes conversion alone. It does not account for hydrogen consumption, throughput, or pressure cost. Pressures below 5 bar extrapolate the fitted pressure-dependent kinetics; the assumed 1 in × 12 in bed and particle density imply a sparse bed. Treat the result as an exploratory model optimum, not experimental validation. Full case data are in `four_factor_grid_search.csv`; the machine-readable summary is `optimization_summary.json`.
