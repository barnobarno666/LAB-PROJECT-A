# H2/CO ratio, temperature, and pressure overview

Run from the project root with `uv run m4-sweep-stoich-temperature-pressure`.

The 3D scatter uses H2/CO feed ratio, inlet temperature, and inlet pressure as coordinates; point color gives predicted completed-bed CO conversion. It fixes Experiment 1 catalyst mass (3.12 g), CO flow (0.320 mol/h), and N2/CO ratio (2.496875), which fixes catalyst space time at 35.10 kg_cat s/mol_CO. The full M4 model is isothermal for this overview.

Pressure below 5 bar lies outside the published kinetic-fit pressure range. The model uses Appendix A's 2 bar Experiment 1 basis; the source also describes atmospheric pressure elsewhere. The model's Experiment 1 reference prediction is 96.94% versus the source-reported 40.63%; the reported value is not a fit target. Geometry and particle density remain inherited assumptions, producing a sparse bed at this catalyst charge. Treat this as an exploratory pre-optimization map, not validation.
