# Experiment 1 full-length bed what-if

This plot keeps the Experiment 1 catalyst charge (3.12 g), feed, 350 °C temperature, and Appendix A pressure (2 bar), while assigning that catalyst mass to the stated 0.030 m diameter × 0.300 m bed.

## Assumptions

- Assumed apparent particle density: 1,250 kg/m³.
- Implied bed bulk catalyst loading: 14.713 kg/m³.
- Implied interparticle bed voidage: 0.9882296 (98.823%).
- Ergun particle diameter: 3 mm, retained from the generic verification setup because the experiment source does not report it.
- Isothermal Full M4 kinetics, unchanged and unfitted. The dashed curve repeats the original constant-pressure verification under the same chemistry and feed.

For an exact 3.00 g charge, the same geometry and particle density imply 98.868% voidage. The requested 98.98% does not follow from either 3.00 g or the source's 3.12 g charge with these dimensions.

## Result

- Constant-pressure prediction: 96.939069% conversion.
- Full-length Ergun what-if: 96.939069% conversion.
- Pressure falls from 2.000000000 to 1.999999992 bar (drop 7.865e-4 Pa).
- Reported conversion point: 40.63% at 3.12 g.

The curves overlap because the computed Ergun pressure drop is negligible in this geometry. Treat this as an illustrative extrapolation, not a validated packed-bed calculation: the implied voidage is nearly 99%, so the catalyst charge is too sparse to resemble a conventional packed bed and Ergun's packed-bed correlation is outside its usual physical setting.
