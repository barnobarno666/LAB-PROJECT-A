# Fixed-bed catalyst-mass and voidage sweep (corrected geometry)

Uses `configs/assumed_base_case.json`: **1 in (0.0254 m) diameter × 12 in (0.3048 m) length**. Apparent particle density is assumed as 1250 kg/m3. The plot varies total catalyst charge assigned uniformly to this fixed volume and ends at 115.83 g, where derived voidage reaches 0.40.

For each total charge W, `phi = 1 - W/(rho_p*V_bed)`. Voidage is uniform for each separate loading case, not an axial profile. The blue curve uses Experiment 1 conditions with the original constant-pressure Full M4 assumption. Teal markers are independent Ergun simulations at selected loads, using the mass-derived voidage and assumed 3 mm particle diameter from the base case. The red square is the source-reported conversion for context; the experiment source does not confirm these dimensions.

At 3.12 g, derived voidage is 98.384% and constant-pressure conversion is 96.939%. At 115.83 g, voidage is 40% and conversion is 99.610%. Ergun pressure drop is 2.151e-03 Pa at the source mass and 16.402 Pa at the max load.

Near 100% voidage, catalyst is sparse through the full tube rather than conventionally packed. Ergun results in this range are illustrative extrapolations. For a conventional packed bed, keep voidage roughly fixed and change active bed length with catalyst mass.
