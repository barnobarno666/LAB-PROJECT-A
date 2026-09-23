# Fixed-bed catalyst-mass and voidage sweep

This plot holds bed diameter at 0.030 m and bed length at 0.300 m, assumes apparent particle density 1250 kg/m³, and varies the total catalyst charge assigned uniformly to that full volume. The main sweep ends at 159.04 g, where the derived voidage reaches the previous reference value of 0.40.

## What each plotted point means

For every total catalyst charge W, the bed bulk loading is W/V and the derived voidage is

`phi = 1 - W / (rho_p * V_bed)`.

The blue conversion curve follows the original verification's isothermal, constant-pressure Full M4 model. Under that assumption, the conversion at each total catalyst weight comes from integrating the mass balance to W. The secondary axis shows the voidage implied by the same total charge and fixed bed volume. Each x-axis value is a separate hypothetical full-bed loading case; voidage is uniform for each case, rather than changing axially down one bed.

The teal markers show selected independent Ergun runs using the voidage and bulk loading implied by each mass. The particle diameter is retained as 3 mm because the source experiment does not report it. The red square shows the source-reported Experiment 1 conversion for reference; it does not confirm the assumed 3 cm × 30 cm geometry.

At the source charge of 3.12 g, the derived voidage is 98.823%, and the constant-pressure model predicts 96.939% conversion. At 159.04 g, the bed voidage is 40% and the model predicts 99.656% conversion.

## Physical interpretation

This is a useful loading-sensitivity picture, but the low-mass cases imply nearly 100% voidage: catalyst pellets would be sparse across the full tube rather than forming a conventional packed bed. Ergun results at those loadings are illustrative extrapolations. For a normal packed bed, hold packing voidage approximately fixed and let active bed length change with catalyst mass.
