# Poster feed-flow contours

Run from the project root with: uv run m4-sweep-feed-flows

The two standalone plots use the no-fit Full M4 model at 350 °C, 2 bar, 3.12 g
catalyst, isothermal and constant-pressure conditions. `co_conversion_h2_co`
varies H2 and CO inlet molar flows while holding N2 at 0.799 mol/h.
`co_conversion_h2_n2` varies H2 and N2 while holding CO at 0.320 mol/h.

The image files contain the contour results, axes, and conversion scale only.
Both surfaces use the common conditions requested for comparison. At 2 bar,
the predictions extrapolate below the 5-15 bar kinetic-fit range.

The CSV records every grid cell and solver status. The JSON file records the
resolved conditions and source-point predictions.
