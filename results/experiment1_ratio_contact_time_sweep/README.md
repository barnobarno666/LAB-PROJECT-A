# Experiment 1 H₂/CO ratio and catalyst space-time sensitivity

Run from the project root with:

```powershell
uv run m4-sweep-ratio-contact-time
```

The sweep holds catalyst charge at 3.12 g, uses the Experiment 1 inlet temperature and the Appendix A pressure interpretation (350 °C and 2 bar), and varies H₂/CO from 1 to 5. It varies contact time by scaling CO and N₂ feed rates while recalculating H₂ from the selected H₂/CO ratio. The contact-time coordinate is (W_{cat}/F_{CO,in}), in kg catalyst·s/mol CO. N₂/CO is held at its Experiment 1 inlet ratio.

The grid writes one contour and two one-dimensional slices: CO conversion versus H₂/CO at the reference contact time, and CO conversion versus contact time at the reference H₂/CO ratio. The red square on each slice is the source-reported Experiment 1 conversion at the reference operating point; it is context, not a fitted target. The CSV also records methane yield, outlet pressure, solver status, and solver messages for every cell.

## First-run result

The 462-cell BDF grid completed without failed cells. At the baseline space time (35.10 kg catalyst·s/mol CO), modeled CO conversion rises from 48.32% at H₂/CO = 1 to 96.95% at 3 and 98.87% at 5. At the baseline ratio (2.9969), reducing CO throughput fourfold raises space time to 140.40 kg catalyst·s/mol CO and gives 99.03% conversion; increasing throughput fourfold lowers space time to 8.78 and gives 76.67%. The model response shows a strong ratio effect below stoichiometric feed and diminishing conversion gains at higher ratios and space times.

These are conditional predictions at the assumed 2 bar pressure and sparse-bed geometry above. The lowest-to-highest Ergun pressure drop in the grid is only about 0.037 Pa under those assumptions.

## Fixed-bed assumptions and limits

The geometry is inherited from `configs/assumed_base_case.json` (1 in diameter × 12 in length), which Experiment 1 does not confirm. The 3.12 g charge and assumed particle density of 1250 kg/m³ imply a bed voidage of about 0.98384. That is a sparse-bed illustration, not a conventional packed-bed geometry. The model is isothermal to isolate feed composition and throughput effects. The source pressure is ambiguous; this run uses Appendix A's 2 bar value, below the project's 5–15 bar kinetic-fit pressure range. Treat the predictions as exploratory model sensitivity, not experimental validation.

The output directory also contains `sweep_metadata.json` with the resolved basis, fit-domain notes, and summary ranges. Run with `--help` to change the grid, catalyst mass, transport model, or solver.
