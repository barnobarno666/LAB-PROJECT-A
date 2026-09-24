# Experiment 1 H$_2$/CO ratio and catalyst space-time sensitivity at 1 bar

Run from the project root with:

    uv run --no-sync python -m methanation.ratio_contact_time_sensitivity --pressure-bar 1.0 --output results/experiment1_ratio_contact_time_sweep_1bar

The sweep holds catalyst charge at 3.12 g, uses the Experiment 1 inlet temperature (350 °C), and overrides inlet pressure to 1 bar absolute. It varies H$_2$/CO from 1 to 5. Contact time is varied by scaling CO and N$_2$ feed rates together while recalculating H$_2$ from the selected H$_2$/CO ratio. The coordinate is catalyst space time, $W_{cat}/F_{CO,in}$, in kg catalyst·s/mol CO. N$_2$/CO is held at its Experiment 1 inlet ratio.

The 462-cell BDF grid completed without failed cells. At the baseline space time (35.10 kg catalyst·s/mol CO), the modeled reference conversion is 78.72% at H$_2$/CO = 2.9969. This differs from the source-reported 40.63%; that value is context and was not used as a fit target. The CSV contains every grid point, and the output directory contains the contour and two one-dimensional slices.

The source describes atmospheric pressure in its abstract and discussion, while Appendix A lists 2 bar. This run uses 1 bar absolute, as requested for the report. The selected pressure is below the project's 5--15 bar kinetic-fit pressure range. The inherited 1 in diameter × 12 in geometry is not confirmed by Experiment 1; with 3.12 g catalyst and the assumed particle density of 1250 kg/m³, it implies a sparse-bed voidage of about 0.98384. Treat these results as exploratory model sensitivity, not experimental validation.
