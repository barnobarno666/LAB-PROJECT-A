# Group 14 reported conversion versus mechanistic model

## Result

This is a direct, **no-fit** comparison using `m4_reduced_co_wgs`: M4 kinetic parameters are left unchanged, and the model is evaluated at the Group 14 temperature, pressure, feed, and 3 g catalyst mass. The plot compares the model prediction with the document's reported 99.207% CO conversion. That reported value is not reconciled with the same document's GC composition and flow measurements, so treat this as an unresolved reported-value comparison, not model validation.

| Metric | Reduced M4 prediction | Reported value | Prediction minus reported value |
|---|---:|---:|---:|
| CO conversion | 41.014% | 99.207% | -58.19 percentage points |

The model run completed: `True`. Model conversion is calculated from molar flows as (inlet CO - outlet CO) / inlet CO. Its predicted methane yield on the CO-inlet basis is 29.148%.

## Values transcribed from the supplied document

- Catalyst mass: 3.0 g
- Reaction temperature: 350.0 C
- Reaction pressure: 760.0 mmHg
- Inlet molar flows: N2 0.799 mol/h, H2 0.399 mol/h, CO 0.32 mol/h
- Normalized dry outlet composition: {"H2": 0.03865, "N2": 0.61912, "CH4": 0.04558, "CO": 0.14436, "CO2": 0.14832, "Ar": 0.00399}
- Reported CO conversion: 0.99207

## Comparison assumptions

- Kinetics: Reduced M4 with published M4 parameters and activity fixed at 1.0. Reduced M4 includes CO methanation and WGS only.
- Dry-inlet treatment: Expanded CO methanation and WGS rates are finite at the dry inlet.
- Reactor: isothermal at 623.15 K and constant pressure at 1.01325 bar.
- Literature scope: the M4 parameters were fitted on a 24 wt% Ni/Al2O3 catalyst at 5 and 15 bar, so this approximately 1 bar prediction extrapolates the pressure range.
- Integration endpoint: 3.000 g catalyst.
- Table 3 inlet molar flows are used exactly as documented.
- This is a prediction, not a fitted model: no kinetic, activity, heat-transfer, or transport parameter was adjusted to improve agreement.

The data document does not provide packed-bed geometry, particle size, catalyst dilution, or heat-transfer information. Consequently, this first comparison intentionally excludes axial pressure drop and non-isothermal behavior rather than inventing those inputs.

## GC and flow consistency check

Appendix B calculates 99.207% from an outlet CO flow of 0.002538 mol/h and an inlet CO flow of 0.320 mol/h. Its reported dry outlet flow and normalized GC composition imply only about 0.01088 mol/h N2, versus 0.799 mol/h N2 in the inlet. If N2 is conserved, the normalized outlet GC composition instead implies a dry outlet flow of 1.290541 mol/h. The reconstructed CO flow is 0.186303 mol/h, corresponding to CO conversion 0.41780.

## Balance results

| Quantity | Result |
|---|---:|
| Carbon residual, outlet minus inlet | 36.418% |
| Oxygen residual, outlet minus inlet | 77.853% |
| Water required by hydrogen balance | 0.231475 mol/h |
| Water required by oxygen balance | -0.249129 mol/h |

The reported-flow calculation and the N2-tracer calculation therefore disagree sharply. The tracer reconstruction also fails elemental closure, so it does not independently establish the correct conversion either. The available document is insufficient to decide which outlet-flow or GC basis is valid; 99.207% should remain labeled as a source-reported value, not a trusted validation target or fitting target.

## Document conflicts that must be resolved

- Table 1: N2 20 L/min; H2 10 L/min; CO 8 L/min
- Table 1 outlet: 550 cm3/min
- Appendix A outlet: 7.7 cm3/min = 0.462 L/h

The Table 3 inlet values numerically align with litre-per-hour rather than litre-per-minute inputs, while the document labels the Table 1 inlet values as L/min. The two outlet-flow entries are also incompatible with each other and with the listed N2 flow.

## What would make the comparison more physically complete

1. Confirm the actual inlet flow units and the measured total outlet flow, including temperature, pressure, and wet/dry basis.
2. Provide the unrounded GC peak areas or response-factor calculation and identify the internal standard/tracer used for absolute quantification.
3. Confirm whether N2 and Ar were present in the inlet, and whether the reported fractions are normalized after removing water.
4. Provide packed-bed geometry, catalyst particle size, and dilution if non-isothermal/Ergun validation is required.

With bed geometry, particle size, catalyst dilution, and thermal boundary data, the same model can be rerun with the coupled energy balance and Ergun pressure-drop equation. Unrounded GC calculations would also allow species-by-species outlet validation, rather than conversion-only benchmarking.
