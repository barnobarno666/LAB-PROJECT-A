"""No-fit comparison of an M4 model with the user's Experiment 1 report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .reactor import SimulationResult, simulate
from .verification import Group14Comparison, _plot_conversion_comparison


def _model_input_data(data: dict[str, Any], pressure_bar: float | None = None) -> dict[str, Any]:
    """Adapt the Experiment 1 schema to the common reactor configuration builder."""
    basis = data["basis"]
    selected_pressure_bar = (
        float(basis["reaction_pressure_bar"])
        if pressure_bar is None
        else float(pressure_bar)
    )
    return {
        "basis": {
            "catalyst_mass_g": float(basis["catalyst_mass_g"]),
            "reaction_temperature_c": float(basis["reaction_temperature_c"]),
            "reaction_pressure_mmhg": selected_pressure_bar * 750.061683,
        },
        "inlet_molar_flow_mol_h": data["inlet_molar_flow_mol_h"],
        "reported_metrics": data["reported_metrics"],
    }


def compare_experiment1(
    data: dict[str, Any], pressure_bar: float | None = None,
    reaction_mode: str = "m4_full",
) -> tuple[Group14Comparison, SimulationResult]:
    """Run the selected M4 mode at Experiment 1 conditions."""
    from .verification import group14_comparison_config

    model_data = _model_input_data(data, pressure_bar)
    result = simulate(group14_comparison_config(model_data, reaction_mode))
    predicted = float(result.co_conversion[-1])
    observed = float(data["reported_metrics"]["co_conversion_fraction"])
    error_pp = (predicted - observed) * 100.0
    comparison = Group14Comparison(
        catalyst_mass_kg=float(result.config.catalyst_mass_kg),
        reaction_mode=result.config.reaction_mode,
        inlet_temperature_k=float(result.config.feed.temperature_k),
        inlet_pressure_bar=float(result.config.feed.pressure_bar),
        predicted_co_conversion_fraction=predicted,
        experimental_co_conversion_fraction=observed,
        signed_error_percentage_points=error_pp,
        absolute_error_percentage_points=abs(error_pp),
        predicted_methane_yield_fraction=float(result.methane_yield[-1]),
        solver_success=result.success,
        solver_message=result.message,
    )
    return comparison, result


def audit_experiment1_data(data: dict[str, Any]) -> dict[str, Any]:
    """Summarize conversion arithmetic and feed/outlet flow consistency."""
    inlet = {k: float(v) for k, v in data["inlet_molar_flow_mol_h"].items()}
    outlet = {k: float(v) for k, v in data["outlet_dry_molar_flow_mol_h"].items()}
    table4 = {
        k: float(v)
        for k, v in data["appendix_b_table4_outlet_dry_molar_flow_mol_h"].items()
    }
    fractions = {
        k: float(v)
        for k, v in data["outlet_dry_mole_fraction_normalized"].items()
    }
    direct_conversion = (inlet["CO"] - outlet["CO"]) / inlet["CO"]
    n2_relative_difference = (outlet["N2"] - inlet["N2"]) / inlet["N2"]
    n2_scaled_dry_flow = inlet["N2"] / fractions["N2"]
    n2_scaled_co_flow = n2_scaled_dry_flow * fractions["CO"]
    n2_scaled_conversion = (inlet["CO"] - n2_scaled_co_flow) / inlet["CO"]

    carbon_in = inlet["CO"]
    carbon_out = outlet["CO"] + outlet["CH4"] + outlet["CO2"]
    oxygen_in = inlet["CO"]
    oxygen_out = outlet["CO"] + 2.0 * outlet["CO2"]
    hydrogen_in = 2.0 * inlet["H2"]
    hydrogen_out = 2.0 * outlet["H2"] + 4.0 * outlet["CH4"]

    return {
        "reported_co_conversion_fraction": float(
            data["reported_metrics"]["co_conversion_fraction"]
        ),
        "co_conversion_from_reported_co_flows_fraction": direct_conversion,
        "n2_inlet_mol_h": inlet["N2"],
        "n2_outlet_mol_h": outlet["N2"],
        "n2_outlet_relative_difference": n2_relative_difference,
        "gc_composition_fraction_sum": sum(fractions.values()),
        "outlet_flow_sum_appendix_c_mol_h": sum(outlet.values()),
        "outlet_flow_sum_appendix_b_table4_mol_h": sum(table4.values()),
        "outlet_dry_flow_reported_mol_h": float(
            data["reported_outlet_dry_flow_mol_h"]
        ),
        "n2_scaled_dry_outlet_flow_mol_h": n2_scaled_dry_flow,
        "n2_scaled_co_outlet_flow_mol_h": n2_scaled_co_flow,
        "n2_scaled_co_conversion_fraction": n2_scaled_conversion,
        "carbon_relative_residual_using_appendix_c_flows": (
            carbon_out - carbon_in
        )
        / carbon_in,
        "oxygen_relative_residual_using_appendix_c_flows": (
            oxygen_out - oxygen_in
        )
        / oxygen_in,
        "water_from_hydrogen_balance_mol_h": (hydrogen_in - hydrogen_out) / 2.0,
        "water_from_oxygen_balance_mol_h": oxygen_in - oxygen_out,
        "co2_flow_appendix_b_table4_mol_h": table4["CO2"],
        "co2_flow_appendix_c_calculation_mol_h": outlet["CO2"],
    }


def _write_experiment1_report(
    data: dict[str, Any],
    audit: dict[str, Any],
    comparison: Group14Comparison,
    result: SimulationResult,
    atmospheric_comparison: Group14Comparison,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_dict = comparison.to_dict()
    comparison_dict["comparison_type"] = (
        "no-fit M4 prediction versus Experiment 1 reported CO conversion"
    )
    comparison_dict["source"] = data["source"]
    comparison_dict["peak_intrinsic_r1_co2_methanation_mol_kg_s"] = float(
        result.intrinsic_reaction_rates_mol_kg_s[:, 0].max()
    )
    comparison_dict["interpretation"] = (
        "The report's CO conversion is supported by its rounded inlet/outlet CO flows; "
        "the pressure basis and other GC species flows remain internally inconsistent."
    )
    (output_dir / "experiment1_model_comparison.json").write_text(
        json.dumps(comparison_dict, indent=2), encoding="utf-8"
    )
    (output_dir / "experiment1_data_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    _plot_conversion_comparison(
        comparison,
        output_dir / "experiment1_co_conversion_comparison.png",
        result=result,
        observation_label="Experiment 1 observed",
        annotation_prefix="Exp 1",
    )

    n2_delta_pct = audit["n2_outlet_relative_difference"] * 100.0
    reaction_note = (
        "Full M4 includes direct CO2 methanation, CO methanation, and WGS. "
        "A leading-order inlet expansion resolves the dry CO/H2 start without adding steam."
        if comparison.reaction_mode == "m4_full"
        else "Reduced M4 includes CO methanation and WGS. Its expanded rates "
        "are finite at the dry inlet."
    )
    if np.isclose(comparison.inlet_pressure_bar, 1.0):
        pressure_comparison_note = (
            "The verification pressure is the user-confirmed atmospheric value of "
            "1 bar absolute; Appendix A's conflicting 2 bar entry is retained as a "
            "source limitation rather than used for this run."
        )
    else:
        pressure_comparison_note = (
            "If the report's atmospheric-pressure prose is used instead, the same "
            f"no-fit model predicts {atmospheric_comparison.predicted_co_conversion_fraction:.3%} "
            f"at 1 bar ({atmospheric_comparison.signed_error_percentage_points:+.2f} "
            "percentage points relative to the reported conversion)."
        )
    report = f"""# Experiment 1 CO conversion versus {comparison.model_label} model

## No-fit comparison

The model uses the Experiment 1 catalyst mass, feed molar flows, temperature, and the selected {comparison.inlet_pressure_bar:.2f} bar absolute verification pressure. Reaction mode is `{comparison.reaction_mode}`; the published M4 kinetics are unchanged, with activity fixed at 1.0. No model parameter was fitted to this experiment. {reaction_note}

The source kinetics were fitted on a 24 wt% Ni/Al2O3 catalyst at 5 and 15 bar; both pressure interpretations here extrapolate below that range.

| Metric | {comparison.model_label} prediction | Experiment 1 report | Prediction minus report |
|---|---:|---:|---:|
| CO conversion | {comparison.predicted_co_conversion_fraction:.3%} | {comparison.experimental_co_conversion_fraction:.3%} | {comparison.signed_error_percentage_points:+.2f} percentage points |

The model run completed: `{comparison.solver_success}` ({comparison.solver_message}). Model conversion uses molar flow: (inlet CO - outlet CO) / inlet CO. Predicted methane yield on the CO-inlet basis is {comparison.predicted_methane_yield_fraction:.3%}.

{pressure_comparison_note}

## Experiment values used

- Source: {data['source']}
- Catalyst mass: {data['basis']['catalyst_mass_g']:.2f} g
- Reaction temperature: {data['basis']['reaction_temperature_c']:.1f} °C
- Verification pressure: {comparison.inlet_pressure_bar:.2f} bar absolute
- Inlet flows from Appendix C: N2 {data['inlet_molar_flow_mol_h']['N2']:.3f}, H2 {data['inlet_molar_flow_mol_h']['H2']:.3f}, CO {data['inlet_molar_flow_mol_h']['CO']:.3f} mol/h
- Outlet flows from the Appendix C sample calculation: N2 {data['outlet_dry_molar_flow_mol_h']['N2']:.3f}, CO {data['outlet_dry_molar_flow_mol_h']['CO']:.3f} mol/h
- Reported CO conversion: {data['reported_metrics']['co_conversion_fraction']:.3%}

## Conversion and N2 check

The report's conversion arithmetic is `(0.320 - 0.190) / 0.320 = {audit['co_conversion_from_reported_co_flows_fraction']:.5f}`, which rounds to 40.63%. N2 is 0.799 mol/h at the inlet and 0.790 mol/h at the outlet, a {n2_delta_pct:.2f}% difference relative to the inlet. The comparison keeps both reported values unchanged and does not rescale the outlet, consistent with treating this small N2 discrepancy as negligible.

As a cross-check, the normalized GC fractions sum to {audit['gc_composition_fraction_sum']:.4f}. Scaling those fractions to conserve inlet N2 gives a CO conversion of {audit['n2_scaled_co_conversion_fraction']:.2%}, close to the report's rounded-flow result. The listed dry outlet total is {audit['outlet_dry_flow_reported_mol_h']:.3f} mol/h; the Appendix C component flows sum to {audit['outlet_flow_sum_appendix_c_mol_h']:.3f} mol/h.

## Source limitations

- Appendix A states 2 bar, but the abstract and Results and Discussion describe atmospheric pressure. The user confirmed that this verification should use 1 bar absolute.
- Appendix B Table 4 lists CO2 at {audit['co2_flow_appendix_b_table4_mol_h']:.3f} mol/h, while the Appendix C calculation uses {audit['co2_flow_appendix_c_calculation_mol_h']:.3f} mol/h. The stated CH4/CO2 selectivity of 0.16 also follows the 0.050 mol/h value.
- Using the Appendix C outlet flows, carbon is short by {abs(audit['carbon_relative_residual_using_appendix_c_flows']):.1%} and oxygen by {abs(audit['oxygen_relative_residual_using_appendix_c_flows']):.1%}. The hydrogen balance implies {audit['water_from_hydrogen_balance_mol_h']:.3f} mol/h water, while the oxygen balance permits only {audit['water_from_oxygen_balance_mol_h']:.3f} mol/h. Thus the CO conversion is arithmetically supported by the reported CO flows and the N2 flow is close, but the full species table is not a closed material balance.

The experiment provides a more credible conversion benchmark than the previously used Group 14 report. The remaining model-to-experiment gap is a no-fit model mismatch under the stated conditions; the comparison does not establish whether it comes from catalyst activity, kinetic transferability, the pressure ambiguity, or another experimental effect.
"""
    (output_dir / "EXPERIMENT1_VERIFICATION_AUDIT.md").write_text(
        report, encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare an M4 model with the Experiment 1 report."
    )
    parser.add_argument("--data", required=True, help="Experiment 1 transcription as JSON")
    parser.add_argument("--output", required=True, help="Directory for verification outputs")
    parser.add_argument(
        "--reaction-mode", choices=("m4_full", "m4_reduced_co_wgs"), default="m4_full"
    )
    args = parser.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    comparison, result = compare_experiment1(data, reaction_mode=args.reaction_mode)
    if not comparison.solver_success or result.terminal_event is not None:
        raise RuntimeError(
            f"Model did not reach the full catalyst-mass endpoint: {comparison.solver_message}; "
            f"terminal_event={result.terminal_event}"
        )
    atmospheric_comparison, atmospheric_result = compare_experiment1(
        data, pressure_bar=1.0, reaction_mode=args.reaction_mode
    )
    if not atmospheric_comparison.solver_success or atmospheric_result.terminal_event is not None:
        raise RuntimeError("Atmospheric-pressure alternative did not reach the full endpoint.")
    audit = audit_experiment1_data(data)
    _write_experiment1_report(
        data,
        audit,
        comparison,
        result,
        atmospheric_comparison,
        Path(args.output),
    )
    print(f"predicted_co_conversion={comparison.predicted_co_conversion_fraction:.6f}")
    print(f"reported_co_conversion={comparison.experimental_co_conversion_fraction:.6f}")
    print(f"error_percentage_points={comparison.signed_error_percentage_points:+.6f}")
    print(f"atmospheric_pressure_prediction={atmospheric_comparison.predicted_co_conversion_fraction:.6f}")
    print(f"n2_outlet_relative_difference={audit['n2_outlet_relative_difference']:+.6f}")
    print(f"outputs={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
