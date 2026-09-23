# Source to implementation review

Reviewed 20 September 2026. The project brief, attached Experiment 1 report, Subah and Somo formulation, Celoria paper, implementation plan, existing fidelity audit, Python source and tests were inspected. At that review, production code and source documents were not changed; scratch document extractions and bounded probes were used. The subsequent geometry correction and generated outputs are tracked in this Git repository.

Geometry update, 23 September 2026: the user corrected the modeled tube/bed diameter to 1 in (0.0254 m) and confirmed the bed length remains 12 in (0.3048 m). The supplied formulation's 5 in diameter is superseded for the runnable demo; outputs and the geometry discussion below have been updated to the corrected configuration.

The implementation plan is a sound **reduced-model development plan**, but its completion gates have not all been met. The current implementation is a useful numerical prototype, not a validated representation of the Group 14 experiment. The principal problems are the experimental basis, incomplete thermochemical consistency, and incorrect verification logic. The published reduced rate expressions are not the main problem.

## 1. Source hierarchy and assignment

1. `source/Lab_project.pdf`, pages 1–4: overall project and team responsibilities. Barno and Ashiq own runnable stiff numerical integration, species and temperature profiles, conversion versus length and catalyst mass, and configurable operating inputs. Experimental fitting, full sensitivity studies, deactivation identification and optimization are downstream tasks. Numerical correctness remains part of the coding deliverable.
2. Attached `C:/Users/defaultuser0.LAPTOP-LRB3T941/Downloads/Telegram Desktop/5_6237695348895129370.pdf`: Methodology reference only, as clarified by the user. Its numerical results and operating values are not validation inputs. The numerical data source is `source/Group-14 experimental data.docx` (also supplied as a Markdown transcription); no separate Group 14 PDF is present in this workspace.
3. `source/Reactor_Model_Formulation_Subah_Somo.docx`: proposed balances and a deliberately reduced kinetic network, with largely assumed operating inputs.
4. `source/Kinetic_study_and_deactivation_phenomena_for_the_methanation_of.pdf`: Celoria et al., CEJ 512 (2025), 162113. Table 3 on page 8 and Table 5 on page 14 were visually checked for equations, powers and units.
5. `M4_BARNO_ASHIQ_MODEL_AND_IMPLEMENTATION_PLAN.md`: implementation specification, not evidence that its gates passed.

Instructions, deadlines and assignments inside these documents were treated as project context, not new instructions to execute unrelated work.

## 2. Separate the assumed demonstration from Group 14

| Quantity | Supplied formulation / demo | Group 14 numerical data |
|---|---:|---:|
| Catalyst mass | 0.11583 kg, inferred from corrected geometry | 0.003 kg |
| Temperature | 623.15 K | 350 C |
| Pressure | 5 bar assumed | 760 mmHg reported reaction pressure |
| CO:H2:N2 feed ratio | 1:4:25 | 0.320:0.399:0.799 from Table 3 |
| Total inlet flow | 0.05 mol/s = 180 mol/h | 1.518 mol/h, Table 3 |
| Reported CO conversion | None: demonstration | 99.207% |

The demo has approximately 38.6 times the Group 14 catalyst mass and 118.6 times its total molar flow. Its catalyst-mass-to-total-flow ratio is about 0.326 times the Group 14 ratio; feed composition and pressure differ too. A near-complete demo conversion therefore says nothing about agreement with Experiment 1. These comparisons use the Group 14 Table 3 inlet values conditionally; the document's flow-unit conflicts still need resolution.

The attached report establishes the methodological sequence: catalyst preparation, calcination, hydrogen activation, fixed-bed reaction, downstream cooling/condensation, gas collection and GC analysis. This explains why dry GC composition must be distinguished from the wet reactor outlet. Do not transfer that report's numerical results, feed rates or other run-specific values into the Group 14 configuration.

The user has confirmed a 1-inch tube/bed diameter and retained the 12-inch packed-bed length for the runnable model, superseding the formulation's 5-inch diameter. At 750 kg/m³ loading these dimensions imply an estimated 0.11583 kg catalyst; this remains an inferred mass because the loading basis is assumed. Neither the paper's small experimental bed nor an arbitrary effective geometry establishes any other laboratory conditions.

## 3. What is correct in the formulation and plan

- Species balances, W-to-z mapping, local ideal-gas properties, heat-transfer area conversion and Ergun conversion are structurally correct for the stated pseudo-homogeneous model.
- WGS is the negative of the paper's RWGS rate. The displayed CO + H2O -> CO2 + H2 reaction in the assignment is WGS despite its RWGS label.
- The code correctly uses pressure in Pa for reactor mechanics and bar for kinetics, J/mol for energies, and kg of total catalyst for rate basis.
- The adsorption denominator contains sqrt(K_H2*p_H2), and K_C has units of bar. The plan corrects the formulation's dimensionless K_C label.
- The expanded reduced rates avoid artificial inlet CO2/water seeds without removing reverse reaction rates.
- Table 5 M4 kinetic and adsorption central estimates, including positive methane adsorption enthalpy, are transcribed correctly.
- The activity factor consistently multiplies both species source terms and reaction heat.

The paper's M4 has three reactions. The formulation intentionally removes direct CO2 methanation and retains CO methanation plus WGS. This is a reduced model using M4 parameters, not the complete published M4. The fitted parameters were estimated jointly for the full network: retaining two expressions does not establish unchanged predictive accuracy. Conversely, automatically enabling the third rate is not a justified repair; its inverse-water dependence requires a documented dry-boundary treatment.

The paper's transport checks apply to its catalyst and experimental packing, not automatically to the project's unscreened crushed catalyst or assumed 3 mm particles. Formulation assumption 8 overstates this justification. Literature kinetics can supply the initial mechanistic hypothesis; experimental applicability remains to be checked.

## 4. Experimental calculations must be reconciled before fitting

### Group 14 is the numerical source

The attached methodology report's result calculations are outside this validation assessment. In Group 14, the reported 0.307 selectivity is the CH4/CO2 product ratio, not methane fraction of converted CO.

The Group 14 report conflicts between L/min labels and mol/h inlet values, and between 550 cm3/min and 7.7 cm3/min outlet flow. Its reported dry outlet N2 flow is 0.01088 mol/h versus 0.799 mol/h at inlet, incompatible with inert conservation on the stated common basis.

The fresh no-fit run predicts 41.0144% CO conversion versus the reported 99.207%. A nitrogen-tracer reconstruction gives 41.7805%, but also gives carbon excess of 36.42%, oxygen excess of 77.85% and negative water from oxygen balance. The numerical proximity of 41.01% and 41.78% does not validate the model because the full reconstructed composition fails closure.

`verification.py` may preserve 99.207% as a reported number for comparison. However, its language that the GC inconsistency is not a reason to discard the benchmark is too strong. The derived conversion and inconsistent absolute outlet flow are related. Label this an unresolved reported-value comparison, not trusted experimental validation or a fitting target.

## 5. Reproduced implementation defects and omissions

### P1: Initial domain limits do not prevent a successful run

Locations: `src/methanation/config.py:117`, `src/methanation/reactor.py:141`.

Events detect crossings; they do not reject states already outside the admissible region. Three bounded probes with zero activity and suitable fixed T/P modes all returned `success=True`, no event:

- Inlet T = 623.15 K, configured maximum T = 600 K.
- Inlet P = 500000 Pa, configured minimum P = 600000 Pa.
- Inlet hydrogen partial pressure = 0.6667 bar, configured minimum = 1 bar.

Validate the initial state against every active bound before integration, and check finite values. `simulate` should validate even when a caller constructs or replaces dataclasses directly. Current positive-only checks also do not reject NaN. Distinguish failed runs from usable partial results.

### P1: The physical reconciliation classifier is mathematically wrong

Location: `src/methanation/verification.py:32`.

It requires dry outlet oxygen to equal inlet oxygen, although water was removed. It also fails to require agreement between water inferred from H and O balances.

Reproduced using inlet CO/H2/N2 = 1/3/1 mol/h and nitrogen-scaled dry outlet fractions:

| Dry outlet flows CO,H2,CH4,CO2,N2 | H-derived water | O-derived water | Current classifier |
|---|---:|---:|---|
| 0.7, 2.5, 0.2, 0.1, 1 | 0.1 | 0.1 | Rejects a balanced case |
| 0.8, 2.0, 0.1, 0.1, 1 | 0.8 | 0.0 | Accepts an inconsistent case |

Require carbon and inert closure and agreement of nonnegative reconstructed water flows within appropriate tolerances. A dry oxygen deficit is not automatically an error. Do not equate chemical reconciliation with agreement to a separately reported conversion; report those checks separately.

### P1 for final thermal work: Thermochemistry does not meet the plan's energy gate

Locations: `src/methanation/thermo.py:14`, `src/methanation/constants.py:43`, `src/methanation/reactor.py:104`.

Constant reaction enthalpies are combined with constant species heat capacities whose stoichiometric differences are nonzero: delta-Cp = -38.7, -29.7 and -9.0 J/(mol K), respectively for CO2 methanation, CO methanation and RWGS. Consistent species enthalpies therefore imply temperature-dependent reaction enthalpies. Cycle closure K1 = K2*K3 alone does not establish that consistency.

An adiabatic demo probe using species formation enthalpies that reproduce the code's reaction heats at 298.15 K, then integrating the code's own species Cp, gives an outlet-minus-inlet enthalpy-flow drift of approximately -17.09 W. This is not solver tolerance error; it follows from the inconsistent property assumptions.

The README labels this an initial approximation, so it is acceptable as a provisional demonstration. It does not pass the plan's final energy-conservation gate. Derive Cp, h, s, reaction heats and equilibrium constants from one cited dataset and test adiabatic enthalpy conservation and wall-heat closure.

### P2: Report and handoff outputs are incomplete

Location: `src/methanation/reporting.py`.

Missing: methane/CO2 selectivities, CH4/CO2 ratio matching the lab convention, dry and wet mole fractions, and the thermochemical approximation in each run's metadata. Product ratio and converted-carbon selectivity must be separately named; they are not interchangeable.

The code reports temperature maxima only on the output grid. Changing the same demo from 401 to 20001 output points changes the recorded maximum from 820.7449 K at 2.286 mm to 820.8188 K at 2.57556 mm. The temperature difference is small here, but the maximum location changes about 0.29 mm. Use dense-solution refinement for maxima before hotspot constraint/optimization work. This peak is about 548 C, outside the paper's cited 250–400 C kinetic fitting range, and must be marked as extrapolation.

### P2: Failure handling and flexible inputs need completion

- `reactor.py:75` calls an RHS trial state an accepted state. Implicit solver trial evaluations can throw an exception before event localization; this path has no structured failure result. The existing tests do not establish robust boundary behavior.
- `cli.py:20` writes ordinary plots before checking success. The JSON labels partial runs, but standalone plots do not. Partial profiles need visible status and reached/configured endpoints.
- `verification.py:192` calculates prediction errors even for incomplete results, and its CLI does not exit unsuccessfully when the solver reports failure.
- CO-free feeds pass the positive-H2 input rule, while CO conversion and methane yield divide by inlet CO. Explicitly reject unsupported performance bases or export undefined values intentionally.
- `M4Parameters` exists, but `reactor_rhs` always uses default parameters. Kinetic-parameter sensitivity requires a real config-to-solver parameter path. Operating-condition sweeps such as the inlet-temperature/pressure contour are available without changing kinetic constants; their assumed inputs and extrapolation limits must stay visible.

## 6. Evidence and limits of the current tests

Fresh `uv run pytest`: **9 passed**. The test suite establishes dry reduced-rate finiteness, adsorption denominator positivity, reaction-cycle closure, elemental conservation, coordinate mapping, zero-activity behavior in fixed T/P mode, Radau/BDF agreement for one demo, and current Group 14 behavior.

The original 5-inch reduced-model demo reproduced X_CO = 0.9945443951. With the corrected 1-inch diameter, the regenerated reduced-model result is X_CO = 0.9577994 (`results/assumed_base_case/`); full M4 gives X_CO = 0.958073 (`results/assumed_full_m4_case/`). Neither run tests experimental validity, initial-limit rejection, correct wet/dry elemental reconciliation, consistent energy closure, or the correctness of the reported experimental conversion.

The prior `M4_IMPLEMENTATION_FIDELITY_AUDIT.md` is stale: it reports eight tests and says the Group 14 code refuses validation, while the current code explicitly preserves an ungated benchmark comparison. Its claims of complete input and failure-handling fidelity are contradicted by the probes above. Its energy section checks the algebraic RHS form, not consistency of the property functions.

## 7. Ordered correction plan within Barno and Ashiq's scope

1. Keep reduced M4 explicitly named. Confirm whether the final scientific requirement is this reduced model or full published M4; do not silently switch networks.
2. Keep the attachment as methodology-only and use Group 14 for numerical data. Separate the assumed demo from Group 14 results. Reconcile Group 14 calibration and flow bases against original records before defining a validation target.
3. Correct initial-state bounds, finite input checks, chemical reconciliation and unsuccessful-run reporting. Lock the reproduced counterexamples into regression tests.
4. Replace provisional thermochemistry with one consistent cited property dataset. Pass the plan's energy checks before treating temperature profiles as final.
5. Finish selectivity/product-ratio and wet/dry exports, property provenance and reliable maximum-temperature reporting.
6. Run bounded verification: rate equivalence and equilibrium checks; elemental and energy closure; 10x tolerance refinement; Radau/BDF comparison; pressure-drop limiting case; domain-event cases; fresh CLI outputs.
7. Deliver the runnable solver and clearly labeled base-case profiles. Once real bed geometry and thermal/pressure conditions are confirmed, generate the laboratory X-versus-z and temperature profiles and hand off to validation/sensitivity teams.

The plan needs targeted amendments, not a new architecture. The existing kinetics and balance structure are worth retaining. Neither expanding to optimization nor fitting an activity factor can substitute for resolving these earlier gates.
