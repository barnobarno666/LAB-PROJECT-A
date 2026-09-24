# Experiment 1 three-model CO-conversion verification

All three models were evaluated independently at **1.00 bar absolute**, 350 °C,
3.12 g catalyst, and the unchanged Experiment 1 inlet flows: N2 0.799 mol/h,
H2 0.959 mol/h, and CO 0.320 mol/h. Operation is isothermal and at constant
pressure. No kinetic or activity parameter was fitted to the reported 40.630%
CO conversion.

| Model | Predicted CO conversion | Prediction - experiment | Pressure-domain status |
|---|---:|---:|---|
| Full M4 | 78.723% | +38.09 pp | extrapolated below fitted range |
| Kopyscinski | 99.985% | +59.35 pp | within published range |
| Quindimil | 3.369% | -37.26 pp | extrapolated below fitted range |

The curves are not stitched together. Kopyscinski is evaluated inside its
published 1-2 bar range. Quindimil is shown at the user-requested 1 bar even
though its published kinetic range begins at 2 bar, and full M4 is likewise a
pressure extrapolation below its 5-15 bar fit range. Catalyst formulations also
differ among the literature models, so agreement or disagreement is a no-fit
transferability comparison rather than parameter validation.

The Quindimil curve is additionally a feed-composition extrapolation because
its parameters were fitted to CO2/H2 experiments, whereas Experiment 1 starts
with CO/H2/N2. It is included because the user requested all three models at the
same one-bar condition, not because it is claimed as an in-domain validation.

The Kopyscinski implementation uses the published corrigendum's
sqrt(p_CO) adsorption term. The Quindimil implementation retains its native atm
and mol/(g_cat h) parameter basis internally, then converts rates to mol/(kg_cat s)
for integration on the common catalyst-mass coordinate.
