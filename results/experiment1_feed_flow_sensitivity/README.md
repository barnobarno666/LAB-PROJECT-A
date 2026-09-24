# Reactive-feed and nitrogen-flow contour

Run from the project root with: uv run m4-sweep-feed-flows

The two panels use the no-fit Full M4 model at 350 °C, 2 bar, 3.12 g catalyst,
isothermal and constant-pressure conditions. Panel (a) varies the absolute H2
and CO inlet molar flows while holding N2 at 0.799 mol/h. Panel (b) varies H2
and N2 while holding CO at 0.320 mol/h. Thus N2 is included as a separate inert
dilution sensitivity, rather than treated as a reactive stoichiometric feed.

Markers show the reported inlet-flow coordinates. Their labels compare the
common-basis model prediction with the conversion reported by each source.
Group 14's source pressure is 760 mmHg and catalyst mass is 3.00 g; the
contour uses 2 bar and 3.12 g for both datasets by request. Group 14's 99.207%
reported conversion is unresolved against its own GC and flow values. The
Subah report also conflicts on pressure between Appendix A and its narrative.
Both model predictions are extrapolations below the 5-15 bar kinetic-fit range.

The CSV records every grid cell and solver status. The JSON file records the
resolved conditions and source-point predictions.
