# Experiment 1 CO conversion versus Full M4 model

## No-fit comparison

The model uses the Experiment 1 catalyst mass, feed molar flows, temperature, and the 2 bar pressure stated in Appendix A. Reaction mode is `m4_full`; the published M4 kinetics are unchanged, with activity fixed at 1.0. No model parameter was fitted to this experiment. Full M4 includes direct CO2 methanation, CO methanation, and WGS. A leading-order inlet expansion resolves the dry CO/H2 start without adding steam.

The source kinetics were fitted on a 24 wt% Ni/Al2O3 catalyst at 5 and 15 bar; both pressure interpretations here extrapolate below that range.

| Metric | Full M4 prediction | Experiment 1 report | Prediction minus report |
|---|---:|---:|---:|
| CO conversion | 96.939% | 40.630% | +56.31 percentage points |

The model run completed: `True` (The solver successfully reached the end of the integration interval.). Model conversion uses molar flow: (inlet CO - outlet CO) / inlet CO. Predicted methane yield on the CO-inlet basis is 72.544%.

If the report's prose saying atmospheric pressure is correct instead of Appendix A's 2 bar, the same no-fit model predicts 78.723% at 1 bar, a +38.09 percentage-point difference from the reported conversion. Pressure ambiguity changes the prediction materially, but neither interpretation reproduces the reported result.

## Experiment values used

- Source: exp1 sub.pdf, abstract, Results and Discussion, Appendices A-C
- Catalyst mass: 3.12 g
- Reaction temperature: 350.0 °C
- Primary pressure assumption: 2.00 bar, interpreted as absolute model pressure from Appendix A
- Inlet flows from Appendix C: N2 0.799, H2 0.959, CO 0.320 mol/h
- Outlet flows from the Appendix C sample calculation: N2 0.790, CO 0.190 mol/h
- Reported CO conversion: 40.630%

## Conversion and N2 check

The report's conversion arithmetic is `(0.320 - 0.190) / 0.320 = 0.40625`, which rounds to 40.63%. N2 is 0.799 mol/h at the inlet and 0.790 mol/h at the outlet, a -1.13% difference relative to the inlet. The comparison keeps both reported values unchanged and does not rescale the outlet, consistent with treating this small N2 discrepancy as negligible.

As a cross-check, the normalized GC fractions sum to 0.9976. Scaling those fractions to conserve inlet N2 gives a CO conversion of 38.99%, close to the report's rounded-flow result. The listed dry outlet total is 1.110 mol/h; the Appendix C component flows sum to 1.098 mol/h.

## Source limitations

- The appendix states 2 bar, but the abstract and Results and Discussion describe operation at atmospheric pressure. The figure uses 2 bar; the atmospheric-pressure model result is reported above.
- Appendix B Table 4 lists CO2 at 0.005 mol/h, while the Appendix C calculation uses 0.050 mol/h. The stated CH4/CO2 selectivity of 0.16 also follows the 0.050 mol/h value.
- Using the Appendix C outlet flows, carbon is short by 22.5% and oxygen by 9.4%. The hydrogen balance implies 0.903 mol/h water, while the oxygen balance permits only 0.030 mol/h. Thus the CO conversion is arithmetically supported by the reported CO flows and the N2 flow is close, but the full species table is not a closed material balance.

The experiment provides a more credible conversion benchmark than the previously used Group 14 report. The remaining model-to-experiment gap is a no-fit model mismatch under the stated conditions; the comparison does not establish whether it comes from catalyst activity, kinetic transferability, the pressure ambiguity, or another experimental effect.
