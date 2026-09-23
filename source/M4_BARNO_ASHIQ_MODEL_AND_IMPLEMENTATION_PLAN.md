# M4 reactor model and implementation plan for Barno and Ashiq

This document defines the numerical work assigned to Barno and Ashiq, explains the selected M4 kinetics and the supplied reactor formulation, and gives an ordered plan for producing runnable code and base-case reactor profiles. It is a specification and implementation plan; no reactor simulation or experimental validation has been performed as part of this document.

The main deliverable is a configurable steady-state packed-bed reactor solver with coupled species, temperature, and pressure balances. It must produce CO conversion against both bed length and catalyst mass, together with species concentration and temperature profiles.

## 1. Sources and scope

| Reference | Document | Relevant location and purpose |
|---|---|---|
| [A] | [Lab_project.pdf](<C:/Users/defaultuser0.LAPTOP-LRB3T941/Downloads/Telegram Desktop/Lab_project.pdf>) | Pages 1–2: overall project; page 3: Barno + Ashiq assignment and upstream teams; page 4: downstream teams |
| [B] | [Reactor_Model_Formulation_Subah_Somo.docx](<C:/Users/defaultuser0.LAPTOP-LRB3T941/Downloads/Telegram Desktop/Reactor_Model_Formulation_Subah_Somo.docx>) | Sections 1–10: proposed reaction subset, balances, geometry, parameters, and initial conditions |
| [C] | [Celoria et al. paper](<C:/Users/defaultuser0.LAPTOP-LRB3T941/Downloads/Telegram Desktop/Kinetic_study_and_deactivation_phenomena_for_the_methanation_of.pdf>) | Page 3: reaction numbering; pages 5–7: experimental/model basis; page 8, Table 3: M4 rates; page 14, Table 5: M4 parameters |

[C] is Celoria et al., *Kinetic study and deactivation phenomena for the methanation of CO₂ and CO mixed syngas on a Ni/Al₂O₃ catalyst*, Chemical Engineering Journal 512 (2025), 162113. DOI: [10.1016/j.cej.2025.162113](https://doi.org/10.1016/j.cej.2025.162113).

The two supplied copies of the paper are byte-identical, verified by SHA-256, and constitute one source. The paper's supporting information was not supplied separately; its thermophysical-property tables and detailed derivations should not be treated as already available.

The assignment in [A] makes Barno and Ashiq responsible for:

1. Implementing the ODE system in Python or MATLAB.
2. Handling stiff coupling between mass and energy balances.
3. Producing species concentration and temperature profiles along the bed.
4. Producing conversion versus bed length and conversion versus catalyst weight.
5. Allowing temperature, pressure, feed ratio, flow rate, and catalyst loading to vary through inputs.
6. Delivering documented, runnable computational code and base-case profile plots.

The source lists 14 September as the original deadline for this component. This plan uses completion gates rather than assigning new dates.

| Team | Responsibility relevant to this implementation |
|---|---|
| Mehrab + Yeamin | Supply and review kinetics, thermodynamics, units, and the CO₂ formation pathway |
| Subah + Somo | Supply and review governing equations, geometry, assumptions, and reactor parameters |
| Barno + Ashiq | Implement, verify, document, and export the numerical solution |
| Shihab + Rifat | Compare with Experiment #1 and perform validation and sensitivity studies using the solver |
| Ouishi + Rimi | Develop deactivation treatment, thermal analysis, and optimization using the solver |

Numerical verification belongs in Barno and Ashiq's deliverable. Experimental fitting, full parameter studies, deactivation parameter identification, and optimization are downstream work. The solver must expose the inputs and outputs those teams need.

## 2. Model choice and the distinction that must remain explicit

**The selected kinetic family is M4. The supplied reactor formulation is a reduced, two-reaction version of M4.**

The paper defines three reversible reactions [C, p. 3]:

| Paper index | Forward reaction | Standard reaction enthalpy reported near 298 K |
|---|---|---|
| 1 | CO₂ + 4H₂ ⇌ CH₄ + 2H₂O | −165 kJ/mol |
| 2 | CO + 3H₂ ⇌ CH₄ + H₂O | −206 kJ/mol |
| 3 | CO₂ + H₂ ⇌ CO + H₂O, RWGS | +41 kJ/mol |

Subah and Somo retain reaction 2, reverse reaction 3 into WGS, and omit reaction 1 [B, §§1, 4]. The resulting model is CO methanation plus WGS:

$$
\mathrm{CO+H_2O\rightleftharpoons CO_2+H_2},\qquad r_{\mathrm{WGS}}=-r_3.
$$

The work-distribution text calls this displayed CO-consuming reaction “reverse water-gas shift”; the displayed direction is actually WGS. Follow the stoichiometry and consistent rate signs.

**Implementation basis proposed here:** first implement the two-reaction formulation supplied by Subah and Somo, with the corrections below. Name this mode `m4_reduced_co_wgs`. Keep the reaction interface capable of supporting `m4_full` separately. Do not describe reduced-mode results as a reproduction of the complete published M4 model.

If the team's intended meaning of “M4” is all three published rates, enable reaction 1 only after resolving its dry-inlet singularity and supplying consistent thermodynamics. This is a scientific scope choice to record before presenting final results; it does not prevent documenting or implementing the supplied reduced model.

Although reaction 1 is the stoichiometric sum of reactions 2 and 3, its fitted kinetic contribution is not automatically redundant. Omitting it can change predicted rates and selectivity once CO₂ is present. A CO-only inlet does not prove reaction 1 remains irrelevant downstream, because WGS produces CO₂.

The paper fitted M4 on 24 wt% Ni/Al₂O₃ using an isothermal, isobaric reactor representation [C, §§2.2, 3.2.4]. Applying those intrinsic rates to a non-isothermal reactor with pressure drop is the project's reactor-model extension. The paper's kinetic experiments used 250–400 °C and pressures of 5 and 15 bar [C, p. 5]; calculations outside that evidence base must be identified as extrapolations.

## 3. State variables and unit contract

Use catalyst mass $W$, in kg of catalyst, as the integration coordinate:

$$
\mathbf{Y}(W)=[F_{CO},F_{H_2},F_{CH_4},F_{H_2O},F_{CO_2},F_{N_2},T,P].
$$

| Quantity | Internal convention |
|---|---|
| Molar flows $F_i$ | mol/s |
| Temperature $T$ | K |
| State pressure $P$ | Pa, absolute |
| Partial pressures supplied to M4 | bar, obtained by dividing Pa by $10^5$ |
| Reaction rates | mol/(kg catalyst·s) |
| Reaction and adsorption energies | J/mol in all calculations |
| Species heat capacities | J/(mol·K) |
| Geometry and particle diameter | m |
| Catalyst loading per bed volume $\rho_{cat,bed}$ | kg catalyst/m³ bed |
| Viscosity $\mu$ | Pa·s |
| Overall heat-transfer coefficient $U$ | W/(m²·K) |

Use $R=8.314\ \mathrm{J/(mol\,K)}$. Distinguish $T_{ref}=598\ \mathrm K$, the kinetic reference temperature, from inlet temperature $T_{in}$ and wall temperature $T_w$. The supplied formulation uses $T_0$ for different purposes; the implementation must not.

At every RHS evaluation:

$$
F_T=\sum_i F_i,\qquad y_i=F_i/F_T,\qquad p_i=y_iP/10^5.
$$

The $p_i$ in all kinetic expressions below are numerical pressures in bar. Never use Pa in a rate law with the published bar-based constants.

## 4. M4 kinetics and parameter values

### 4.1 Shared adsorption denominator

Use a separate name for the adsorption term so it cannot be confused with tube diameter:

$$
\mathcal D=1+\sqrt{K_{H_2}p_{H_2}}+K_{CO}p_{CO}
+K_C\frac{p_{CH_4}}{p_{H_2}^{2}}+K_{CH_4}p_{CH_4}.
$$

All M4 rates use $\mathcal D^2$. The hydrogen term is $\sqrt{K_{H_2}p_{H_2}}$, not $K_{H_2}\sqrt{p_{H_2}}$. The units of $K_C$ are **bar**, not dimensionless as shown in [B]'s table. This makes its denominator contribution dimensionless [C, Tables 3 and 5].

### 4.2 Published rates

From [C, Table 3, Eqs. 19–21]:

$$
r_1=\frac{k_1p_{CO_2}p_{H_2}^{3/2}}{p_{H_2O}\mathcal D^2}
\left(1-\frac{Q_1}{K_{eq,1}}\right),
\qquad Q_1=\frac{p_{CH_4}p_{H_2O}^2}{p_{CO_2}p_{H_2}^4}.
$$

$$
r_2=\frac{k_2p_{CO}\sqrt{p_{H_2}}}{\mathcal D^2}
\left(1-\frac{Q_2}{K_{eq,2}}\right),
\qquad Q_2=\frac{p_{CH_4}p_{H_2O}}{p_{CO}p_{H_2}^3}.
$$

$$
r_3=\frac{k_3p_{CO_2}\sqrt{p_{H_2}}}{\mathcal D^2}
\left(1-\frac{Q_3}{K_{eq,3}}\right),
\qquad Q_3=\frac{p_{CO}p_{H_2O}}{p_{CO_2}p_{H_2}}.
$$

Rates are signed net rates; a negative value means the reverse reaction. Do not clamp them to zero.

### 4.3 Numerically preferable reduced-model expressions

For positive hydrogen pressure, algebraically expand the driving-force terms:

$$
r_2=\frac{k_2}{\mathcal D^2}
\left[p_{CO}\sqrt{p_{H_2}}
-\frac{p_{CH_4}p_{H_2O}}{K_{eq,2}p_{H_2}^{5/2}}\right],
$$

$$
r_3=\frac{k_3}{\mathcal D^2}
\left[p_{CO_2}\sqrt{p_{H_2}}
-\frac{p_{CO}p_{H_2O}}{K_{eq,3}\sqrt{p_{H_2}}}\right],
\qquad r_{\mathrm{WGS}}=-r_3.
$$

This avoids dividing by CO, CO₂, or water in the reduced model. An exactly dry CO/H₂/N₂ inlet is then permissible: initially $r_{\mathrm{WGS}}=0$, while methanation generates water and subsequently enables WGS. The artificial $10^{-8}$ mol/s water and CO₂ seeds in [B] are unnecessary for this reduced formulation.

Hydrogen depletion still requires a domain guard. The full $r_1$ expression also contains an inverse water pressure; adding arbitrary trace water is not a demonstrated treatment of its dry-inlet limit. Full M4 requires a documented boundary treatment supported by the model derivation, or a specified positive-steam inlet with a sensitivity assessment. Do not silently reuse the reduced-mode dry boundary for full M4.

### 4.4 Reference constants

Central estimates from [C, Table 5, M4 column], with $T_{ref}=598$ K:

| Parameter | Value | Units |
|---|---:|---|
| $k_{1,ref}$ | 0.0168 | mol/(kg·s·bar^1.5) |
| $k_{2,ref}$ | 1.50 | mol/(kg·s·bar^1.5) |
| $k_{3,ref}$ | 0.119 | mol/(kg·s·bar^1.5) |
| $E_{A,1}$ | 118 | kJ/mol |
| $E_{A,2}$ | 54.9 | kJ/mol |
| $E_{A,3}$ | 110 | kJ/mol |
| $K_{H_2,ref}$ | 0.500 | bar⁻¹ |
| $\Delta H_{H_2}$ | −8.76 | kJ/mol |
| $K_{CO,ref}$ | 1.41 | bar⁻¹ |
| $\Delta H_{CO}$ | −38.5 | kJ/mol |
| $K_{C,ref}$ | 1.78 | bar |
| $\Delta H_C$ | −20.0 | kJ/mol |
| $K_{CH_4,ref}$ | 0.500 | bar⁻¹ |
| $\Delta H_{CH_4}$ | +18.8 | kJ/mol |

Retain the positive methane adsorption parameter as published. Store values, units, source locations, and parameter overrides together. Use the M4 column throughout; M3 has similar rate expressions but different fitted constants.

Temperature dependence follows [C, Eqs. 12–13]:

$$
k_j(T)=k_{j,ref}\exp\left[-\frac{E_{A,j}}R\left(\frac1T-\frac1{T_{ref}}\right)\right],
$$

$$
K_i(T)=K_{i,ref}\exp\left[-\frac{\Delta H_i}R\left(\frac1T-\frac1{T_{ref}}\right)\right].
$$

These $k_{j,ref}$ values are rate constants at 598 K. They are not the infinite-temperature prefactors of an unshifted Arrhenius expression.

### 4.5 WGS reversal and thermodynamic closure

The safest implementation evaluates the published RWGS rate and returns its negative for WGS. If a separate WGS constant is exposed, enforce:

$$
K_{eq,WGS}=K_{eq,3}^{-1},\qquad
k_{WGS}(T)=k_3(T)/K_{eq,3}(T).
$$

Under a constant reaction-enthalpy approximation only:

$$
E_{A,WGS}=E_{A,3}-\Delta H_3\approx110-41=69\ \mathrm{kJ/mol}.
$$

[B] reports $K_{eq,WGS}(598)=30.1$ and $k_{WGS,ref}=3.59$. Their arithmetic is consistent with $0.119\times30.1\approx3.58$, within rounding. These are converted, approximate values, not additional independent fitted parameters from Table 5. If temperature-dependent thermochemistry is used, compute $k_3/K_{eq,3}$ at each temperature rather than freezing the 69 kJ/mol approximation.

The final thermodynamic module should supply species $C_{p,i}(T)$, $h_i^\circ(T)$, and $s_i^\circ(T)$ from a consistent, cited dataset. The paper uses Shomate thermochemistry [C, §2.2.2]. Calculate:

$$
\Delta H_j(T)=\sum_i\nu_{ij}h_i^\circ(T),\quad
\Delta G_j^\circ(T)=\sum_i\nu_{ij}[h_i^\circ(T)-Ts_i^\circ(T)],
\quad K_j^\circ=\exp[-\Delta G_j^\circ/(RT)].
$$

With pressure-based quotients, $K_{eq,j}=K_j^\circ(p^\circ)^{\Delta\nu_j}$. Use $p^\circ=1$ bar and the same bar convention throughout; reactions 1 and 2 have $\Delta\nu=-2$, whereas reaction 3 has $\Delta\nu=0$.

Full M4 must satisfy $K_{eq,1}=K_{eq,2}K_{eq,3}$ and $\Delta H_1=\Delta H_2+\Delta H_3$. Independently using the rounded Gibbs energies on paper page 3 introduces a roughly 1 kJ/mol closure discrepancy. Derive all three reactions from the same species data. A constant-enthalpy demo may be useful, but must be labeled as an approximation and must still use a consistent reaction basis.

## 5. Reactor equations

### 5.1 Species balances

For reduced mode, use fresh-catalyst activity $a=1$ initially:

$$
\begin{aligned}
dF_{CO}/dW&=-a(r_2+r_{WGS}),\\
dF_{H_2}/dW&=a(-3r_2+r_{WGS}),\\
dF_{CH_4}/dW&=ar_2,\\
dF_{H_2O}/dW&=a(r_2-r_{WGS}),\\
dF_{CO_2}/dW&=ar_{WGS},\\
dF_{N_2}/dW&=0.
\end{aligned}
$$

Prefer a fixed species order and a stoichiometric matrix in code. For full M4, the columns for $[r_1,r_2,r_3]$, with reaction 3 in the published RWGS direction, are:

$$
\nu=\begin{bmatrix}
0&-1&1\\
-4&-3&-1\\
1&1&0\\
2&1&1\\
-1&0&-1\\
0&0&0
\end{bmatrix},\qquad \frac{d\mathbf F}{dW}=a\nu\mathbf r.
$$

Reduced mode can use the same matrix with $r_1=0$. Total flow changes as $dF_T/dW=-2ar_2$ in reduced mode, or $-2a(r_1+r_2)$ in full mode. WGS itself is mole-conserving.

### 5.2 Energy balance

For reduced mode:

$$
\frac{dT}{dW}=
\frac{a[-\Delta H_2(T)r_2-\Delta H_{WGS}(T)r_{WGS}]
-\dfrac{4U}{D_t\rho_{cat,bed}}(T-T_w)}
{\sum_iF_iC_{p,i}(T)}.
$$

The numerator is heat released or removed per kg catalyst per second. Convert kJ/mol to J/mol. Include nitrogen and all other modeled gases in the heat-capacity flow. Full mode uses $-a\sum_j\Delta H_jr_j$ in the reaction term.

Provide three thermal modes: isothermal, adiabatic with $U=0$, and heat exchange with specified $U$ and $T_w$. Keep wall and inlet temperatures independently configurable. The wall can heat the gas when $T<T_w$; do not clamp the heat-transfer term to cooling only.

### 5.3 Catalyst mass and bed length

For uniform packing:

$$
A_c=\pi D_t^2/4,\qquad
W(z)=\rho_{cat,bed}A_cz,\qquad
z(W)=W/(\rho_{cat,bed}A_c).
$$

Define $\rho_{cat,bed}=W_{cat}/V_{bed}$. For a diluted bed, it is not the total solid loading of catalyst plus inert, and it is not the skeletal catalyst density. The kinetic mass basis is total catalyst mass, not mass of nickel alone. Do not multiply published rates by 0.24 without a separate justified change of basis.

For the same uniformly packed run, conversion versus mass and conversion versus length are coordinate transformations of one physical solution. They are both required outputs, not independent validation evidence.

When varying catalyst loading, specify the physical change. Increasing bed length at fixed packing changes $W_{cat}$; changing catalyst dilution at fixed length changes $\rho_{cat,bed}$. Reject configurations that independently specify incompatible $W_{cat}$, $L$, and $\rho_{cat,bed}$.

### 5.4 Pressure drop

Compute local mixture properties using SI pressure:

$$
\overline M=\sum_i y_iM_i,\qquad
u_s=\frac{F_TRT}{PA_c},\qquad
\rho_g=\frac{P\overline M}{RT}.
$$

Then:

$$
\frac{dP}{dW}=-\frac1{\rho_{cat,bed}A_c}
\left[\frac{150\mu(1-\epsilon_b)^2u_s}{d_p^2\epsilon_b^3}
+\frac{1.75\rho_g(1-\epsilon_b)u_s^2}{d_p\epsilon_b^3}\right].
$$

Use molar masses in kg/mol. The result is Pa/kg catalyst. Provide a constant-pressure mode for comparison. Evaluate velocity and density locally rather than keeping inlet values fixed. For a diluted or irregular bed, record how effective particle diameter and voidage were obtained.

## 6. Inputs available now and information still needed

These values come from [B, §10] and are a provisional demonstration case:

| Input | Supplied value | Status to preserve |
|---|---:|---|
| Tube/bed diameter | 0.0254 m (1 in) | User-confirmed correction on 2026-09-23; supersedes the 0.127 m value in [B] |
| Bed length | 0.3048 m (12 in) | Supplied value retained; user confirms it is unchanged |
| Catalyst loading per bed volume | 750 kg/m³ | Assumed; clarify catalyst versus total solids basis |
| Bed voidage | 0.40 | Assumed |
| Particle diameter | 0.003 m | Assumed |
| Gas viscosity | $2.5\times10^{-5}$ Pa·s | Assumed constant |
| Heat-transfer coefficient | 10 W/(m²·K) | Assumed |
| Inlet pressure | 5 bar absolute | Assumed; not verified Experiment #1 data |
| Inlet temperature | 623 K | Supplied approximate 350 °C; exact conversion is 623.15 K |
| Wall temperature | Equal to inlet temperature | Assumed |
| Feed ratio CO:H₂:N₂ | 1:4:25 | Supplied demonstration basis |
| Total inlet molar flow | 0.05 mol/s | Supplied demonstration basis |
| Catalyst activity | 1 | Fresh-catalyst baseline |

Compute inlet flows from exact normalized fractions: $F_{CO,0}=0.05/30$, $F_{H_2,0}=4(0.05)/30$, and $F_{N_2,0}=25(0.05)/30$. Use zero CH₄, H₂O, and CO₂ for the reduced dry-feed case. Do not assemble the inlet from rounded flow values and then assume its total is exact.

The corrected dimensions imply $A_c\approx0.0005067\ \mathrm{m^2}$, $V_{bed}\approx0.0001544\ \mathrm{m^3}$, and approximately 0.1158 kg catalyst if 750 kg/m³ is truly the catalyst loading. These are calculated consequences of the configured inputs, not measured catalyst mass; the original 0.127 m diameter would imply 2.896 kg at the same length and loading.

For comparison, the paper's kinetic bed used 75 mg catalyst plus 375 mg SiC, approximately 23 mm bed height, and approximately 266 μm particles inside a 4 mm inner-diameter quartz tube [C, p. 5]. The supplied project geometry is a different reactor. Do not substitute paper geometry for Experiment #1 or assume paper transport checks validate the proposed 3 mm particles.

Before labeling a run as the experimental base case, obtain:

- Actual catalyst mass, dilution, particle size, and catalyst identity/pretreatment. The model uses the user-confirmed 1 in diameter and unchanged 12 in bed length.
- Actual inlet composition, moisture, temperature, and absolute pressure.
- Actual feed rate and whether a volumetric reading refers to standard, normal, or reactor conditions, including its reference temperature and pressure.
- The wall/furnace condition and an agreed treatment of heat transfer, viscosity, and species heat capacities.
- Experiment #1 GC values, calibration/concentration basis, wet or dry reporting, and whether nitrogen is retained in reported fractions.
- The selected reaction mode and the approved thermochemical data.

For a stated reference volumetric flow, convert $F_T=P_{ref}\dot V_{ref}/(RT_{ref,flow})$. Do not equate NL/h, actual L/h, and mol/s. Keep the flow-reference temperature separate from the kinetic reference temperature.

## 7. Outputs and reporting definitions

For a CO feed without inlet carbon-containing products:

$$
X_{CO}=\frac{F_{CO,0}-F_{CO}}{F_{CO,0}},\quad
S_{CH_4}=\frac{F_{CH_4}-F_{CH_4,0}}{F_{CO,0}-F_{CO}},\quad
S_{CO_2}=\frac{F_{CO_2}-F_{CO_2,0}}{F_{CO,0}-F_{CO}},
$$

$$
Y_{CH_4}=\frac{F_{CH_4}-F_{CH_4,0}}{F_{CO,0}},\qquad
C_i=\frac{y_iP}{RT}.
$$

Use net production for flexible feeds. Selectivities are undefined when the CO-consumption denominator is zero or negligible; report NaN or a masked point at the inlet, not zero or an arbitrary ratio. For mixed CO/CO₂ feeds, define a separate carbon-based performance convention before interpreting net product/CO-consumption ratios as selectivity.

For gas analysis after water removal:

$$
y_{i,dry}=F_i/(F_T-F_{H_2O}),\qquad i\ne H_2O.
$$

Export wet and dry fractions with explicit labels. CO conversion is based on molar flow, not simply the fractional drop in GC mole fraction, because total flow changes. If nitrogen is measured and conserved, it can support reconstruction of dry outlet flow for the validation team.

Required figures are CO conversion versus $z$, CO conversion versus $W$, species concentrations versus $z$, and temperature versus $z$. Also export molar flows, pressure, selectivities, and methane yield so downstream teams can inspect the solution. Mark the temperature maximum and its location; identify whether it is an internal maximum or an outlet maximum.

Each run should save a profile table, a concise summary, the complete input configuration, model mode, thermodynamic basis, solver settings/status, and any domain-limit termination. A demonstration run must be labeled “assumed-input demonstration”; “validated” requires comparison with actual measurements.

## 8. Implementation plan

Python is the proposed language. Use `uv` for environment and dependency management. Suggested dependencies are NumPy, SciPy, Matplotlib, and a test runner; use the standard library for configuration and table export where sufficient. A notebook can illustrate the workflow, but the deliverable should run from a clean command without notebook execution-order dependencies.

### Phase 1 — Establish the input and model contract

Create a species-order definition, source-tagged M4 parameter set, structured configuration, and input validation. Separate the provisional case from the eventual Experiment #1 case. Record the reduced/full reaction choice explicitly.

Validate positive pressure, temperature, total flow, geometry, and catalyst mass; $0<\epsilon_b<1$; nonnegative inlet flows; consistent geometry/loading; and complete thermodynamic inputs. Specify units in field names or metadata. Do not silently normalize contradictory input descriptions.

**Completion gate:** one configuration resolves into an unambiguous inlet state and catalyst-mass endpoint, with all assumed values identified.

### Phase 2 — Implement properties and rate functions

Implement temperature-dependent kinetic and adsorption constants, heat capacities, reaction enthalpies, equilibrium constants, and reduced M4 rates as independent functions. Use the expanded net-rate expressions. Return diagnostics such as the denominator and signed reaction rates.

Check the 598 K reference values, all parameter signs and units, WGS/RWGS reversal, finite rates at the dry reduced-model inlet, and zero net rate at constructed equilibrium states. Compare expanded and original expressions at positive interior compositions where both are defined.

**Completion gate:** the rate module passes algebraic and thermodynamic checks independently of the reactor integrator.

### Phase 3 — Integrate isothermal and constant-pressure species balances

Implement the stoichiometric RHS on the $W$ basis, with $T$ and $P$ fixed. Start with the reduced model and activity one. Return structured results rather than embedding calculations inside plotting functions.

Check elemental conservation and nitrogen invariance. At small catalyst mass, compare the integrated change with $\Delta\mathbf F\approx\mathbf F'(0)\Delta W$. Verify the total-flow relation implied by stoichiometry.

**Completion gate:** a finite, physically admissible species solution with successful solver completion and acceptable conservation residuals.

### Phase 4 — Add energy coupling

Add the temperature state, first adiabatically and then with wall heat exchange. Keep an explicit isothermal switch. Use temperature-dependent properties where available and record any property approximation used for demonstrations.

Check the heat-release sign, conservation of gas enthalpy flow in the adiabatic case, and consistency of enthalpy-flow change with integrated wall heat exchange in the heated/cooled case. Do not demand monotonically increasing temperature in every case: reversibility and heat transfer can change its trend.

**Completion gate:** temperature coupling passes an energy residual check and remains stable under tighter solver tolerances.

### Phase 5 — Add Ergun pressure drop and length mapping

Add local velocity/density evaluation and the pressure ODE. Derive $z$ from the same catalyst loading used in the balances. Run a constant-pressure comparison and a reaction-disabled pressure-drop case.

**Completion gate:** positive pressure, a non-increasing pressure profile for forward flow, correct dimensional conversion, and agreement of outlet length with the configured bed geometry.

### Phase 6 — Make stiff integration and failures explicit

Use an implicit stiff solver such as `solve_ivp` with `Radau`; use `BDF` for a bounded cross-check. Record method, relative/absolute tolerances, function evaluations, termination status, and final coordinate. An explicit solver is not the default acceptance test for this coupled system.

Use component-scaled tolerances because flows, temperature, and pressure have different magnitudes. A proposed starting point is relative tolerance $10^{-6}$, flow absolute tolerance around $10^{-10}$ mol/s for the provisional flow scale, temperature absolute tolerance $10^{-5}$ K, and pressure absolute tolerance $10^{-1}$ Pa. Refine these based on convergence and the smallest physically meaningful flow.

Provide terminal events for pressure and hydrogen-domain limits and a configured upper temperature bound. Treat a limit event as a partial calculation, not a successfully completed bed. The bounds are numerical/model limits unless physical operating limits have been supplied.

Implicit methods may evaluate slightly negative trial flows even when the physical solution is nonnegative. Handle those evaluations with a narrowly defined, scale-aware numerical safeguard and step/tolerance control. Reject materially negative accepted states; do not clip final profiles to hide errors. Demonstrate that any floor or safeguard does not control the reported result.

**Completion gate:** tighter tolerances and a second stiff method give materially unchanged outputs; failures produce useful diagnostics and no misleading success plots.

### Phase 7 — Produce the runnable interface and figures

Expose a single simulation function, conceptually `simulate(config) -> result`, and a command that loads a configuration, runs the model, and exports tables/figures. Keep plotting downstream of successful result checks. Provide examples for changing temperature, pressure, feed ratio, total flow, and catalyst mass.

Generate the four required figures, plus pressure and performance summaries. Use explicit units and distinguish wet concentration, dry composition, conversion, yield, and selectivity. Save the configuration alongside each output set.

**Completion gate:** a fresh session can reproduce the assumed-input base-case outputs using documented `uv` commands.

### Phase 8 — Prepare the team handoff

Document model mode, equations, source parameters, assumptions, numerical checks, run commands, and remaining experimental inputs. Give the validation team the simulation interface and dry/wet reporting convention. Give the deactivation team an activity input without inventing decay constants.

For later activity studies, $a$ can initially be a prescribed scalar or spatial profile used consistently in mass and reaction-heat terms. A time-dependent deactivation ODE is in physical time; do not insert $da/dt$ directly into the $W$-coordinate system as $da/dW$. A later transient or quasi-steady coupling needs its own formulation.

**Completion gate:** code, example configuration, profile data, figures, and numerical verification notes are ready for the other teams to use.

## 9. Verification and acceptance criteria

The following are proposed numerical acceptance targets, not results already obtained:

| Check | Expected evidence |
|---|---|
| Parameter transcription | Table 5 M4 values and 598 K recovery agree with the source |
| Rate reversal | WGS equals negative RWGS at representative positive compositions |
| Reduced dry inlet | Finite rates with zero inlet water/CO₂; no artificial product seed required |
| Element balances | Carbon, hydrogen, oxygen, and nitrogen flow residuals below $10^{-6}$ relative to their nonzero inlet scales |
| Activity zero | Species flows stay constant; thermal exchange and pressure drop may remain active |
| Equilibrium behavior | Constructed equilibrium states produce near-zero net rates; reverse rates remain permitted |
| Thermodynamic closure | Full-mode constants and enthalpies satisfy reaction 1 = reaction 2 + reaction 3 |
| Energy balance | Scaled integrated energy residual below a documented target, initially $10^{-5}$, with consistent species enthalpies |
| Coordinate mapping | $W=\rho_{cat,bed}A_cz$ and outlet dimensions agree |
| Solver convergence | Tightening tolerances by 10× changes outlet conversion by less than $10^{-4}$ absolute and peak temperature by less than 0.1 K |
| Solver comparison | Radau/BDF agree to the selected reporting accuracy on at least one coupled case |
| Output integrity | Full configured bed reached, finite outputs, accepted flows nonnegative within stated tolerance, and correct success/event labels |

Compute conserved elemental flows directly:

$$
B_C=F_{CO}+F_{CH_4}+F_{CO_2},\qquad
B_H=2F_{H_2}+4F_{CH_4}+2F_{H_2O},
$$

$$
B_O=F_{CO}+F_{H_2O}+2F_{CO_2},\qquad B_N=2F_{N_2}.
$$

For the reduced model with no inlet methane or CO₂, carbon closure also requires $S_{CH_4}+S_{CO_2}\approx1$ wherever conversion is large enough to define those ratios reliably.

Numerical success does not establish physical applicability. Intrinsic kinetics assume negligible transport limitations; the proposed project particle size and bed differ substantially from the paper. Reassess transport effects for the actual setup before claiming experimental agreement or predictive validity.

## 10. Suggested code organization and final checklist

The following is a proposed layout, not a set of files already created:

```text
project/
  pyproject.toml
  uv.lock
  README.md
  configs/
    assumed_base_case.json
  src/methanation/
    parameters.py
    thermo.py
    kinetics.py
    reactor.py
    solver.py
    reporting.py
    cli.py
  tests/
    test_kinetics.py
    test_balances.py
    test_solver.py
  results/
    assumed_base_case/
```

Keep the structure small enough for the team to understand. A proposed internal split is for Barno to implement kinetics, properties, and RHS functions, while Ashiq implements solver controls, exports, and plots; both review units and conservation together. This individual split is a suggestion, since [A] assigns the component jointly.

- [ ] Record whether final results use reduced M4 or full M4.
- [ ] Confirm thermodynamic inputs and all pressure/energy units.
- [ ] Resolve catalyst loading, geometry, and feed definitions.
- [ ] Implement and verify the reduced isothermal model.
- [ ] Add and verify energy and pressure coupling.
- [ ] Complete stiff-solver convergence and conservation checks.
- [ ] Generate both required conversion plots and species/temperature profiles.
- [ ] Export reproducible configurations, profile data, and run summaries.
- [ ] Label assumed-input demonstrations separately from experimental cases.
- [ ] Provide a documented clean-run command using `uv`.
- [ ] Hand off the numerical model to validation and deactivation teams.

Completion of this plan means Barno and Ashiq have delivered a reproducible numerical implementation with verified balances and clear assumptions. Experimental validation and optimization follow through the assigned teams.

