# M4 Barno+Ashiq implementation fidelity audit (read-only)

Date: 2026-09-20. Scope: compare `M4_BARNO_ASHIQ_MODEL_AND_IMPLEMENTATION_PLAN.md` (516 lines, specification only, no results claimed) against the runnable implementation in this directory. No code was modified for this audit. Evidence was gathered by reading source files and by read-only execution (`uv run pytest`, `uv run python -c` probes).

Geometry correction note (2026-09-23): after this audit, the user corrected the demo tube/bed diameter from 0.127 m (5 in) to 0.0254 m (1 in) and confirmed that bed length remains 0.3048 m (12 in). The old area, volume, catalyst-mass, and demo-result figures below describe the pre-correction snapshot; the runnable config and generated results now use the corrected diameter.

## Overall verdict

**Substantially faithful for the reduced-model numerical core; partially faithful on reporting/handoff details.**

- The coupled mass/energy/pressure solver on the `W` (kg catalyst) coordinate, M4 reduced kinetics, unit contract, assumed base case, stiff-solver controls, and reproducibility wiring are implemented as specified.
- Gaps are concentrated in §7/§8/§9 downstream-facing items: selectivities, dry-basis export, per-run thermochemistry label, explicit energy-residual check, tolerance-tightening acceptance test, multi-example configs, and a usable `m4_full` hook. The extra `verification.py` Group-14 audit is additive and does not violate the plan, but it is outside the plan's Barno+Ashiq scope.

Test status at audit time: `8 passed` (`test_kinetics` 3, `test_reactor` 4, `test_verification` 1).

## Section-by-section fidelity

### §1 Sources and scope — FAITHFUL

- Assignment items 1–6 (ODE system, stiff coupling, species/T profiles, X-vs-z and X-vs-W, variable T/P/feed/flow/loading, documented runnable code + base-case plots) are all present: `src/methanation/reactor.py:simulate`, `src/methanation/cli.py:main`, `src/methanation/reporting.py:write_outputs`, `configs/assumed_base_case.json`.
- Numerical verification is included in-deliverable; experimental fitting/optimization are correctly left downstream. `README.md:24` explicitly marks thermochemistry as an initial approximation to replace before final analysis.

### §2 Model choice (`m4_reduced_co_wgs` vs `m4_full`) — FAITHFUL with one PARTIAL

- FAITHFUL: reduced CO-methanation + WGS is the implemented mode. `config.py:118-119` accepts only `reaction_mode='m4_reduced_co_wgs'`. `README.md:3` states it does not claim all three published M4 reactions. WGS direction follows stoichiometry/rate signs, not the work-distribution text's mislabel (plan §2 warning respected): `kinetics.py:103-106` evaluates published RWGS then returns `-r_rwgs`.
- PARTIAL: plan asks to “keep the reaction interface capable of supporting `m4_full` separately.” The code records the choice explicitly but hard-rejects anything else, so there is no usable full-mode hook. `constants.py:30-39` defines `STOICH_FULL` for `[r1,r2,r3]` but nothing imports it (`reactor.py` hardcodes reduced derivatives at `reactor.py:98-102`). Full-mode dry-inlet singularity treatment is therefore correctly absent, but so is the extension point.

### §3 State variables and unit contract — FAITHFUL

- State `Y=[F_CO,F_H2,F_CH4,F_H2O,F_CO2,F_N2,T,P]` in mol/s, K, Pa absolute: `reactor.py:17-26,135-138`, `constants.py:SPECIES`.
- Bar conversion for kinetics (`Pa/1e5`): `reactor.py:44,81`, `constants.py:8`. Rates mol/(kg·s), energies J/mol, Cp J/(mol·K), geometry m, loading kg/m³ bed, viscosity Pa·s, U W/(m²·K): `kinetics.py`, `thermo.py`, `reactor.py:107-131`, `config.py` field names carry units.
- `R=8.314...` (`constants.py:7`), kinetic `T_ref=598 K` (`kinetics.py:13`) kept separate from inlet/wall temperatures (`configs/assumed_base_case.json:6,18`), and `F_T,y_i,p_i` recomputed every RHS evaluation (`reactor.py:70-85`). Verified.

### §4.1 Adsorption denominator — FAITHFUL

- `kinetics.py:66-78` implements `D=1+sqrt(K_H2·p_H2)+K_CO·p_CO+K_C·p_CH4/p_H2²+K_CH4·p_CH4`, uses `D²`, uses `sqrt(K_H2·p_H2)` (not `K_H2·sqrt(p_H2)`), and treats `K_C` as bar-based. Name `denominator` avoids confusion with tube diameter `D_t`. Hydrogen guard raises on `p_H2<=0`.

### §4.2–4.3 Rate expressions — FAITHFUL

- Signed net rates, no clamping to zero: `kinetics.py:100-106`.
- Expanded reduced forms match plan exactly; read-only probe at an interior composition agreed with the original `Q/Keq` forms to `~3e-17` (r2) and `~6e-18` (r3), confirming the algebra.
- Dry CO/H₂/N₂ inlet is finite with no artificial water/CO₂ seed: `config.py:160-161` requires positive H₂ only; `tests/test_kinetics.py:7-13` asserts finite rates with `r_WGS≈0`; probe gave `r_co≈0.107`, `r_wgs=-0.0` at the dry inlet. No `1e-8` seed exists in the inlet construction (`config.py:103-111`).

### §4.4 Reference constants — FAITHFUL

- `kinetics.py:19-32` transcribes Table 5 M4 central values exactly (`k_ref=[0.0168,1.50,0.119]`, `E_A=[118,54.9,110] kJ/mol`, `K_H2=0.500/-8.76`, `K_CO=1.41/-38.5`, `K_C=1.78 bar/-20.0`, `K_CH4=0.500/+18.8`), with `T_ref=598 K`.
- Shifted-Arrhenius/van’t Hoff forms (`kinetics.py:38-43`) match plan Eqs. 12–13. Probe: `kinetic_constants(598.0)` recovers `[0.0168,1.5,0.119]` and `adsorption_constants(598.0)` recovers `{0.5,1.41,1.78,0.5}` exactly. Positive methane term retained. No M3 values used.

### §4.5 WGS reversal and thermodynamic closure — FAITHFUL as a demo, final dataset still pending (as plan allows)

- Safest reversal used (evaluate RWGS, return negative; no separate `k_WGS` parameter): `kinetics.py:103-106`. Temperature-dependent `k3/Keq,3` is evaluated at each T, so the `E_A,WGS≈69 kJ/mol` constant-enthalpy shortcut is not frozen in.
- Closure `K1=K2·K3` holds to `1.0` at both 598 K and 623.15 K by construction (`thermo.py:14-15,36-48`; `tests/test_kinetics.py:21-23`). `ΔH1=ΔH2+ΔH3` (`-165=-206+41`) likewise.
- `thermo.py:1,36-48` + `constants.py:41-43` use a constant-Cp / constant-ΔH van’t Hoff approximation. This is what the plan permits as a labeled demonstration (“must be labeled as an approximation”), and it is labeled (`thermo.py` docstring, `constants.py:41-43` comment, `README.md:24`). It is therefore faithful for the current gate, but not a substitute for the cited Shomate/NASA dataset required before final analysis. Pressure convention (`p°=1 bar`, bar-based quotients, `Δν=-2,-2,0` implicit in reference Gibbs energies) is used consistently.
- No `0.24` Ni-mass-basis rescaling was found; rates remain per total catalyst mass as required.

### §5.1 Species balances — FAITHFUL numerically, PARTIAL structurally

- `reactor.py:98-102` matches the reduced stoichiometry exactly (`-a(r2+rWGS)`, `a(-3r2+rWGS)`, `a·r2`, `a(r2-rWGS)`, `a·rWGS`, N₂ zero). Total-flow consequence `dF_T/dW=-2ar2` follows implicitly. Fresh-catalyst `a=1` default in config.
- PARTIAL: plan prefers “a fixed species order and a stoichiometric matrix.” Fixed order is used (`constants.py:10-11`, `INDEX`), but the RHS does not consume `STOICH_FULL`; the matrix is defined yet unused. Behavior is correct; maintainability/extensibility to full M4 is weaker than specified.

### §5.2 Energy balance — FAITHFUL

- `reactor.py:104-120` implements `dT/dW=[a(-ΔH2·r2-ΔH_WGS·rWGS)-4U/(D_t·ρ)(T-Tw)]/ΣF_i·C_pi` with J/mol, all gases in the Cp flow, three modes (`isothermal` zeroed, `adiabatic` wall term zero regardless of U, `heat_exchange` signed so wall heating when `T<Tw` is allowed). Probes: isothermal holds T constant; adiabatic runs to `T_peak≈821.77 K`; coupled base case `T_peak≈820.74 K` near the inlet (`z≈0.0023 m`).

### §5.3 Mass/length mapping — FAITHFUL

- `config.py:91-100` (`A_c=πD_t²/4`, `V_bed`, `W_cat=ρ·V`) and `reactor.py:29-32` (`z=W/(ρ·A_c)`) match plan. Probe reproduces plan’s consequences: `A_c≈0.0126677 m²`, `V≈0.0038611 m³`, `W≈2.89583 kg`. Both X-vs-W and X-vs-z are emitted from one solution (`reporting.py:42-56`). Loading is derived, so incompatible independent `W/L/ρ` cannot be specified — satisfying the “reject inconsistent geometry” intent by construction. Catalyst-vs-solids and total-catalyst (not Ni-only) basis respected.

### §5.4 Pressure drop — FAITHFUL

- `reactor.py:70-85,124-131` evaluates `M̄,u_s,ρ_g` locally in SI and integrates `dP/dW=-Ergun/(ρ·A_c)` in Pa/kg catalyst with kg/mol masses. `constant_pressure` comparison mode exists and holds P constant in tests. Probe on the coupled case: P decreases monotonically (`4.99958 bar` outlet, `-35.8 Pa` drop with `a=0` confirming the reaction-disabled pressure path stays live).

### §6 Provisional inputs — FAITHFUL

- `configs/assumed_base_case.json` matches the §10 demonstration table (`0.127 m`, `0.3048 m`, `750 kg/m³`, `0.40`, `0.003 m`, `2.5e-5 Pa·s`, `10 W/m²K`, `5 bar abs`, `623.15 K` exact conversion with `Tw=Tin`, `1:4:25`, `0.05 mol/s`, `a=1`). Inlet uses exact normalized fractions (`config.py:103-111`; probe sum `0.05 mol/s`), zero CH₄/H₂O/CO₂, no rounded-flow reassembly. Paper kinetic-bed geometry is not substituted. Run is labeled assumed/demo (`reporting.py:102`, `README.md:15`), not Experiment #1.

### §7 Outputs and reporting — PARTIAL

- FAITHFUL: X_CO, CH₄ yield, wet concentrations `C_i=y_i·P/(R·T)`, molar flows, pressure, four required figures (X-vs-z, X-vs-W, species-C-vs-z, T+P-vs-z), profile table + summary + resolved config + solver status/event diagnostics, peak-T value and location (`reporting.py:16-33,41-107`; `run_summary.json` shows `X≈0.99454`, `Y_CH4≈0.96203`, elemental residuals `~1e-12`).
- GAPS (all §7 explicit requirements with no implementation found):
  1. No `S_CH4`/`S_CO2` export and no NaN/masked inlet-selectivity rule; `profiles.csv` header contains conversion and yield only.
  2. No dry-basis fractions `y_i,dry=F_i/(F_T-F_H2O)` exported or labeled wet-vs-dry (only wet concentrations/mole-fractions in code).
  3. No per-run thermodynamic-basis record in `run_summary.json`/`resolved_config.json` (approximation is documented in `README`/`thermo.py` but not stamped on each output set).
  4. Peak-T internal-vs-outlet flag is left for the reader to infer from `peak_temperature_location_m`; no explicit label.
  5. Mixed CO/CO₂ selectivity convention is (correctly) absent, but should be recorded as deferred since only the CO-only convention is implemented (`reactor.py:51-58` assumes CO-feed definitions).

### §8 Phased plan — summary

- Phase 1 (contract): FAITHFUL. Structured config, validation (positive P/T/flow/geometry, `0<ε<1`, non-negative ratios, positive H₂, mode/method whitelists, unit-suffixed fields), explicit reduced-mode record, provisional-vs-experiment separation. `config.py:117-161`.
- Phase 2 (properties/rates): FAITHFUL as implementation, PARTIAL as verification. Independent `kinetic_constants`/`adsorption_constants`/`cp`/`ΔH`/`Keq`/reduced-rate functions with denominator/rate diagnostics exist, but tests cover only dry-inlet finiteness, denominator positivity, and cycle closure — not 598 K recovery, WGS-sign reversal, equilibrium near-zero, or expanded-vs-original equivalence (all verified here by read-only probes, but not locked in by tests).
- Phase 3 (isothermal/isobaric balances): FAITHFUL. `tests/test_reactor.py:14-26` checks N₂ invariance, `X>0`, elemental residuals `<1e-8`, and constant P. Small-ΔW linearization and explicit total-flow assertion are not in tests.
- Phase 4 (energy): PARTIAL. Coupling, isothermal switch, adiabatic and wall-exchange paths all run (probed), but no automated energy-residual check (`10⁻⁵` target) or enthalpy-flow vs wall-integral consistency check exists in code or tests.
- Phase 5 (Ergun/length): FAITHFUL functionally, PARTIAL as tests. Local properties, pressure ODE, z-derivation, constant-P comparison, and outlet-length agreement (`tests/test_reactor.py:29-34`) exist; an explicit non-increasing-P assertion and a dedicated reaction-disabled Ergun case are not in tests (both verified here by probe).
- Phase 6 (stiffness/failures): FAITHFUL with one test gap. `Radau` default + `BDF` cross-check (`reactor.py:167-176`; `tests/test_reactor.py:50-58` with `<1e-4` X and `<0.1 K` agreement), component-scaled `rtol=1e-6` / `atol=[1e-10,1e-5,0.1]` exactly as proposed, terminal P/T/H₂ events treated as partial (`success` requires full bed + no event + no materially negative flow, `reactor.py:181-189`), narrow `max(flows,0)` safeguard for trial evaluations with `10·atol_flow` rejection of accepted states (`reactor.py:74-78,188`). Missing: the `10×` tolerance-tightening acceptance check (probe here: tightening `rtol` to `1e-7` changes X by `~4.8e-10` and peak T by `~4.3e-6 K`, so the criterion would pass, but it is not in the test suite). No misleading success plots: `cli.py:19-26` always writes labeled outputs and exits non-zero on incomplete runs.
- Phase 7 (interface/figures): FAITHFUL except §7 gaps plus one gap: only `assumed_base_case.json` is shipped, so “examples for changing T/P/ratio/flow/loading” are not yet provided as runnable configs. `simulate(config)->result` (`reactor.py:141`), clean `uv` commands (`README.md:7-11`), downstream plotting, unit-labeled figures, and config-saving are present.
- Phase 8 (handoff): PARTIAL. Mode/equations/sources/assumptions/commands/remaining-inputs are documented; scalar activity is applied consistently in mass and heat terms with no `da/dW` time-confusion (`reactor.py:98-110`); validation team gets the interface and N₂-tracer reasoning via the extra Group-14 audit, but the dry/wet export convention and selectivity outputs they need are the §7 gaps above. No decay constants are invented.

### §9 Acceptance criteria — itemized

| Check | Verdict | Evidence |
|---|---|---|
| Parameter transcription + 598 K recovery | FAITHFUL (implementation), PARTIAL (tests) | Values exact; probe recovers `k_ref`/`K_ref` at 598 K, but no test asserts it |
| Rate reversal WGS=−RWGS | FAITHFUL (implementation), PARTIAL (tests) | By construction `kinetics.py:103-106`; probe confirms, no dedicated test |
| Reduced dry inlet, no seed | FAITHFUL | `tests/test_kinetics.py:7-13` + probe |
| Element balances `<1e-6` | FAITHFUL | Test `<1e-8`; coupled run `~1e-12` (`run_summary.json:15-20`) |
| Activity zero | FAITHFUL (implementation), PARTIAL (tests) | Code keeps T/P paths live; probe `a=0` holds species constant with `ΔP≈35.8 Pa`; test uses isothermal+isobaric only |
| Equilibrium near-zero, reverse allowed | PARTIAL | Reverse allowed (no clamp); no constructed-equilibrium test |
| Thermodynamic closure r1=r2+r3 | FAITHFUL | `tests/test_kinetics.py:21-23`, probe ratio `1.0` |
| Energy residual `<1e-5` | GAP | No implementation or test found |
| Coordinate mapping | FAITHFUL | `tests/test_reactor.py:29-34`; probe outlet matches config |
| Solver convergence (10× tightening → ΔX<1e-4, ΔT<0.1 K) | GAP in tests, would-pass by probe | No test; probe `ΔX≈4.8e-10`, `ΔT≈4.3e-6 K` |
| Solver comparison Radau/BDF | FAITHFUL | `tests/test_reactor.py:50-58` |
| Output integrity (full bed, finite, non-negative, labels) | FAITHFUL | `reactor.py:181-204`, `reporting.py:87-107`; probe finite, `min flow 0.0`, monotonic P |

### §10 Layout and checklist — PARTIAL (equivalent, not identical)

- Proposed `parameters.py` → implemented as `constants.py` + `M4Parameters` in `kinetics.py` + `config.py`; proposed `solver.py` → merged into `reactor.py:simulate`; `thermo.py`/`kinetics.py`/`reactor.py`/`reporting.py`/`cli.py` match intent; `tests/test_balances.py`+`test_solver.py` → merged as `tests/test_reactor.py`; extras `__init__.py` and `verification.py` + `data/group14_observed_data.json` + `results/group14_verification/` are additive.
- Dependency choice (`numpy/scipy/matplotlib/pytest`, stdlib `json/csv/argparse`) and `uv` workflow match the plan. No notebook-order dependency.
- Checklist: reduced-vs-full recorded; units/thermo inputs confirmed as demo-grade; loading/geometry/feed resolved as assumed; reduced isothermal + energy + pressure implemented; conservation + BDF cross-check done; both conversion plots + species/T profiles emitted; configs/data/summaries exported; assumed-vs-experimental labeling present; clean `uv` run documented. Remaining checklist gaps are the §7/§9 items above (selectivity/dry export, per-run thermo stamp, energy residual, tolerance-tightening lock-in, varying-input examples, full-M4 hook).

## Notes on extras (not infidelity)

- `src/methanation/verification.py` + `tests/test_verification.py` + Group-14 audit correctly refuse validation: N₂-tracer reconstruction gives `C +36.4%`, `O +77.9%`, negative O-balance water (`-0.249 mol/h`), and tracer conversion `0.418` vs reported `0.992`. This enforces the plan’s “obtain actual inputs/GC basis before calling anything a base case” and the downstream-team boundary. The `Ar` outlet entry has no counterpart in the six-species model; the audit treats it as a data-quality flag rather than a model species, which is reasonable but should be stated explicitly wherever the audit is cited.

## What would close the gaps (no code changed)

1. Export `S_CH4`/`S_CO2` with NaN/masked inlet handling and document the mixed-feed convention as deferred.
2. Export labeled wet and dry fractions/flows alongside concentrations.
3. Stamp thermochemistry basis + config hash in every `run_summary.json`.
4. Add automated energy-residual and `10×`-tolerance tests; add explicit WGS-sign, 598 K-recovery, equilibrium, monotonic-P, and Ergun-with-`a=0` tests.
5. Ship minimal example configs sweeping T, P, ratio, flow, and loading; expose (or explicitly defer) an `m4_full` entry point instead of a bare rejection, and either consume `STOICH_FULL` in the RHS or remove it to avoid dead code.
