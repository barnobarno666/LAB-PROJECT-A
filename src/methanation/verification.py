"""Group 14 experimental benchmark for the selected M4 reactor mode."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .config import ReactorConfig
from .reactor import SimulationResult, simulate

@dataclass(frozen=True)
class Group14Audit:
    normalized_fraction_sum: float
    tracer_reconstructed_dry_outlet_mol_h: float
    tracer_reconstructed_flows_mol_h: dict[str, float]
    dry_elemental_flow_in_mol_atom_h: dict[str, float]
    dry_elemental_flow_out_mol_atom_h: dict[str, float]
    carbon_relative_residual: float
    oxygen_relative_residual: float
    water_from_hydrogen_balance_mol_h: float
    water_from_oxygen_balance_mol_h: float
    tracer_co_conversion_fraction: float
    reported_co_conversion_fraction: float

    @property
    def physically_reconcilable(self) -> bool:
        return bool(
            np.isclose(self.normalized_fraction_sum, 1.0, atol=5e-4)
            and abs(self.carbon_relative_residual) < 1e-3
            and abs(self.oxygen_relative_residual) < 1e-3
            and self.water_from_hydrogen_balance_mol_h >= -1e-9
            and self.water_from_oxygen_balance_mol_h >= -1e-9
            and np.isclose(
                self.tracer_co_conversion_fraction,
                self.reported_co_conversion_fraction,
                atol=1e-3,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "normalized_fraction_sum": self.normalized_fraction_sum,
            "tracer_reconstructed_dry_outlet_mol_h": self.tracer_reconstructed_dry_outlet_mol_h,
            "tracer_reconstructed_flows_mol_h": self.tracer_reconstructed_flows_mol_h,
            "dry_elemental_flow_in_mol_atom_h": self.dry_elemental_flow_in_mol_atom_h,
            "dry_elemental_flow_out_mol_atom_h": self.dry_elemental_flow_out_mol_atom_h,
            "carbon_relative_residual": self.carbon_relative_residual,
            "oxygen_relative_residual": self.oxygen_relative_residual,
            "water_from_hydrogen_balance_mol_h": self.water_from_hydrogen_balance_mol_h,
            "water_from_oxygen_balance_mol_h": self.water_from_oxygen_balance_mol_h,
            "tracer_co_conversion_fraction": self.tracer_co_conversion_fraction,
            "reported_co_conversion_fraction": self.reported_co_conversion_fraction,
            "physically_reconcilable": self.physically_reconcilable,
        }
        return result


@dataclass(frozen=True)
class Group14Comparison:
    """No-fit prediction of the reported Group 14 CO-conversion measurement."""

    catalyst_mass_kg: float
    reaction_mode: str
    inlet_temperature_k: float
    inlet_pressure_bar: float
    predicted_co_conversion_fraction: float
    experimental_co_conversion_fraction: float
    signed_error_percentage_points: float
    absolute_error_percentage_points: float
    predicted_methane_yield_fraction: float
    solver_success: bool
    solver_message: str

    @property
    def model_label(self) -> str:
        return "Full M4" if self.reaction_mode == "m4_full" else "Reduced M4"

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_type": "no-fit mechanistic prediction versus unresolved source-reported conversion",
            "reaction_mode": self.reaction_mode,
            "catalyst_mass_kg": self.catalyst_mass_kg,
            "inlet_temperature_k": self.inlet_temperature_k,
            "inlet_pressure_bar": self.inlet_pressure_bar,
            "predicted_co_conversion_fraction": self.predicted_co_conversion_fraction,
            "experimental_co_conversion_fraction": self.experimental_co_conversion_fraction,
            "signed_error_percentage_points": self.signed_error_percentage_points,
            "absolute_error_percentage_points": self.absolute_error_percentage_points,
            "predicted_methane_yield_fraction": self.predicted_methane_yield_fraction,
            "solver_success": self.solver_success,
            "solver_message": self.solver_message,
        }


def audit_group14_data(data: dict[str, Any]) -> Group14Audit:
    """Diagnose whether N2-scaled GC values reproduce the reported conversion.

    This is a diagnostic only. The documented CO conversion remains the experimental
    comparison target because the GC response-factor and wet/dry measurement basis
    are not supplied well enough to make an independent absolute-flow reconstruction.
    """
    inlet = {name: float(value) for name, value in data["inlet_molar_flow_mol_h"].items()}
    outlet_y = {name: float(value) for name, value in data["outlet_dry_mole_fraction_normalized"].items()}
    if inlet["N2"] <= 0.0 or outlet_y["N2"] <= 0.0:
        raise ValueError("A positive inlet and outlet N2 value is required for tracer reconstruction.")
    fraction_sum = sum(outlet_y.values())
    total_outlet_dry = inlet["N2"] / outlet_y["N2"]
    outlet = {name: fraction * total_outlet_dry for name, fraction in outlet_y.items()}

    elemental_in = {
        "C": inlet.get("CO", 0.0),
        "H": 2.0 * inlet.get("H2", 0.0),
        "O": inlet.get("CO", 0.0),
        "N": 2.0 * inlet.get("N2", 0.0),
    }
    elemental_out = {
        "C": outlet.get("CO", 0.0) + outlet.get("CH4", 0.0) + outlet.get("CO2", 0.0),
        "H": 2.0 * outlet.get("H2", 0.0) + 4.0 * outlet.get("CH4", 0.0),
        "O": outlet.get("CO", 0.0) + 2.0 * outlet.get("CO2", 0.0),
        "N": 2.0 * outlet.get("N2", 0.0),
    }
    water_from_h = (elemental_in["H"] - elemental_out["H"]) / 2.0
    water_from_o = elemental_in["O"] - elemental_out["O"]
    tracer_conversion = (inlet["CO"] - outlet["CO"]) / inlet["CO"]
    return Group14Audit(
        normalized_fraction_sum=fraction_sum,
        tracer_reconstructed_dry_outlet_mol_h=total_outlet_dry,
        tracer_reconstructed_flows_mol_h=outlet,
        dry_elemental_flow_in_mol_atom_h=elemental_in,
        dry_elemental_flow_out_mol_atom_h=elemental_out,
        carbon_relative_residual=(elemental_out["C"] - elemental_in["C"]) / elemental_in["C"],
        oxygen_relative_residual=(elemental_out["O"] - elemental_in["O"]) / elemental_in["O"],
        water_from_hydrogen_balance_mol_h=water_from_h,
        water_from_oxygen_balance_mol_h=water_from_o,
        tracer_co_conversion_fraction=tracer_conversion,
        reported_co_conversion_fraction=float(data["reported_metrics"]["co_conversion_fraction"]),
    )


def group14_comparison_config(
    data: dict[str, Any], reaction_mode: str = "m4_full"
) -> ReactorConfig:
    """Build the model input from the measured conditions and 3 g catalyst basis.

    The governing equations are integrated in catalyst mass. Bed geometry and
    loading below merely map that 3 g mass to the generic configuration object;
    with isothermal, constant-pressure assumptions, they do not affect the rates
    or predicted conversion.
    """
    inlet = {name: float(value) for name, value in data["inlet_molar_flow_mol_h"].items()}
    catalyst_mass_kg = float(data["basis"]["catalyst_mass_g"]) / 1000.0
    loading_kg_m3 = 750.0
    diameter_m = 0.01
    cross_section_m2 = np.pi * diameter_m**2 / 4.0
    bed_length_m = catalyst_mass_kg / (loading_kg_m3 * cross_section_m2)
    return ReactorConfig.from_dict(
        {
            "reaction_mode": reaction_mode,
            "feed": {
                "total_molar_flow_mol_s": sum(inlet.values()) / 3600.0,
                "mole_ratio": inlet,
                "temperature_k": float(data["basis"]["reaction_temperature_c"]) + 273.15,
                "pressure_bar": float(data["basis"]["reaction_pressure_mmhg"]) / 750.061683,
            },
            "bed": {
                "tube_diameter_m": diameter_m,
                "bed_length_m": bed_length_m,
                "catalyst_loading_kg_m3_bed": loading_kg_m3,
                "void_fraction": 0.4,
                "particle_diameter_m": 0.003,
            },
            "thermal": {
                "mode": "isothermal",
                "wall_temperature_k": float(data["basis"]["reaction_temperature_c"]) + 273.15,
                "overall_heat_transfer_w_m2_k": 0.0,
            },
            "transport": {"mode": "constant_pressure", "gas_viscosity_pa_s": 2.5e-5},
            "activity": 1.0,
            "solver": {
                "method": "Radau",
                "rtol": 1e-8 if reaction_mode == "m4_full" else 1e-6,
                "atol_flow_mol_s": 1e-14 if reaction_mode == "m4_full" else 1e-10,
                "atol_temperature_k": 1e-7,
                "atol_pressure_pa": 1e-2,
                "max_temperature_k": 1200.0,
                "min_pressure_pa": 1e3,
                "min_hydrogen_partial_pressure_bar": 1e-8,
                "output_points": 101,
            },
        }
    )


def compare_group14_experiment(
    data: dict[str, Any], reaction_mode: str = "m4_full"
) -> tuple[Group14Comparison, SimulationResult]:
    """Run the fixed-condition, no-parameter-fit Group 14 comparison."""
    result = simulate(group14_comparison_config(data, reaction_mode))
    predicted = float(result.co_conversion[-1])
    observed = float(data["reported_metrics"]["co_conversion_fraction"])
    error_pp = 100.0 * (predicted - observed)
    return (
        Group14Comparison(
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
        ),
        result,
    )


from .plotting import (
    COLOR_EXP,
    COLOR_MODEL,
    COLOR_ZERO,
    apply_design3_style,
    save_figure,
)


def _write_report(
    data: dict[str, Any],
    audit: Group14Audit,
    comparison: Group14Comparison,
    output_dir: Path,
    result: SimulationResult | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    reaction_note = (
        "Full M4 includes direct CO2 methanation, CO methanation, and WGS "
        "(the reverse of the paper's RWGS reaction)."
        if comparison.reaction_mode == "m4_full"
        else "Reduced M4 includes CO methanation and WGS only."
    )
    inlet_note = (
        "A leading-order inlet expansion starts full M4 from the documented "
        "zero-water, zero-CO2 CO/H2 feed without adding an artificial steam flow."
        if comparison.reaction_mode == "m4_full"
        else "Expanded CO methanation and WGS rates are finite at the dry inlet."
    )
    (output_dir / "group14_data_audit.json").write_text(
        json.dumps(audit.to_dict(), indent=2), encoding="utf-8"
    )
    entries = data["conflicting_document_entries"]
    comparison_dict = comparison.to_dict()
    if result is not None:
        comparison_dict["peak_intrinsic_r1_co2_methanation_mol_kg_s"] = float(
            np.max(result.intrinsic_reaction_rates_mol_kg_s[:, 0])
        )
    (output_dir / "group14_model_comparison.json").write_text(
        json.dumps(comparison_dict, indent=2), encoding="utf-8"
    )
    _plot_conversion_comparison(
        comparison,
        output_dir / "group14_co_conversion_comparison.png",
        result=result,
    )
    report = f"""# Group 14 reported conversion versus mechanistic model

## Result

This is a direct, **no-fit** comparison using `{comparison.reaction_mode}`: M4 kinetic parameters are left unchanged, and the model is evaluated at the Group 14 temperature, pressure, feed, and 3 g catalyst mass. The plot compares the model prediction with the document's reported 99.207% CO conversion. That reported value is not reconciled with the same document's GC composition and flow measurements, so treat this as an unresolved reported-value comparison, not model validation.

| Metric | {comparison.model_label} prediction | Reported value | Prediction minus reported value |
|---|---:|---:|---:|
| CO conversion | {comparison.predicted_co_conversion_fraction:.3%} | {comparison.experimental_co_conversion_fraction:.3%} | {comparison.signed_error_percentage_points:+.2f} percentage points |

The model run completed: `{comparison.solver_success}`. Model conversion is calculated from molar flows as (inlet CO - outlet CO) / inlet CO. Its predicted methane yield on the CO-inlet basis is {comparison.predicted_methane_yield_fraction:.3%}.

## Values transcribed from the supplied document

- Catalyst mass: {data['basis']['catalyst_mass_g']} g
- Reaction temperature: {data['basis']['reaction_temperature_c']} C
- Reaction pressure: {data['basis']['reaction_pressure_mmhg']} mmHg
- Inlet molar flows: N2 {data['inlet_molar_flow_mol_h']['N2']} mol/h, H2 {data['inlet_molar_flow_mol_h']['H2']} mol/h, CO {data['inlet_molar_flow_mol_h']['CO']} mol/h
- Normalized dry outlet composition: {json.dumps(data['outlet_dry_mole_fraction_normalized'])}
- Reported CO conversion: {audit.reported_co_conversion_fraction:.5f}

## Comparison assumptions

- Kinetics: {comparison.model_label} with published M4 parameters and activity fixed at 1.0. {reaction_note}
- Dry-inlet treatment: {inlet_note}
- Reactor: isothermal at {comparison.inlet_temperature_k:.2f} K and constant pressure at {comparison.inlet_pressure_bar:.5f} bar.
- Literature scope: the M4 parameters were fitted on a 24 wt% Ni/Al2O3 catalyst at 5 and 15 bar, so this approximately 1 bar prediction extrapolates the pressure range.
- Integration endpoint: {comparison.catalyst_mass_kg * 1000.0:.3f} g catalyst.
- Table 3 inlet molar flows are used exactly as documented.
- This is a prediction, not a fitted model: no kinetic, activity, heat-transfer, or transport parameter was adjusted to improve agreement.

The data document does not provide packed-bed geometry, particle size, catalyst dilution, or heat-transfer information. Consequently, this first comparison intentionally excludes axial pressure drop and non-isothermal behavior rather than inventing those inputs.

## GC and flow consistency check

Appendix B calculates 99.207% from an outlet CO flow of 0.002538 mol/h and an inlet CO flow of 0.320 mol/h. Its reported dry outlet flow and normalized GC composition imply only about 0.01088 mol/h N2, versus 0.799 mol/h N2 in the inlet. If N2 is conserved, the normalized outlet GC composition instead implies a dry outlet flow of {audit.tracer_reconstructed_dry_outlet_mol_h:.6f} mol/h. The reconstructed CO flow is {audit.tracer_reconstructed_flows_mol_h['CO']:.6f} mol/h, corresponding to CO conversion {audit.tracer_co_conversion_fraction:.5f}.

## Balance results

| Quantity | Result |
|---|---:|
| Carbon residual, outlet minus inlet | {audit.carbon_relative_residual:.3%} |
| Oxygen residual, outlet minus inlet | {audit.oxygen_relative_residual:.3%} |
| Water required by hydrogen balance | {audit.water_from_hydrogen_balance_mol_h:.6f} mol/h |
| Water required by oxygen balance | {audit.water_from_oxygen_balance_mol_h:.6f} mol/h |

The reported-flow calculation and the N2-tracer calculation therefore disagree sharply. The tracer reconstruction also fails elemental closure, so it does not independently establish the correct conversion either. The available document is insufficient to decide which outlet-flow or GC basis is valid; 99.207% should remain labeled as a source-reported value, not a trusted validation target or fitting target.

## Document conflicts that must be resolved

- Table 1: {entries['table_1_inlet_flow_units']}
- Table 1 outlet: {entries['table_1_outlet_flow']}
- Appendix A outlet: {entries['appendix_a_outlet_flow']}

The Table 3 inlet values numerically align with litre-per-hour rather than litre-per-minute inputs, while the document labels the Table 1 inlet values as L/min. The two outlet-flow entries are also incompatible with each other and with the listed N2 flow.

## What would make the comparison more physically complete

1. Confirm the actual inlet flow units and the measured total outlet flow, including temperature, pressure, and wet/dry basis.
2. Provide the unrounded GC peak areas or response-factor calculation and identify the internal standard/tracer used for absolute quantification.
3. Confirm whether N2 and Ar were present in the inlet, and whether the reported fractions are normalized after removing water.
4. Provide packed-bed geometry, catalyst particle size, and dilution if non-isothermal/Ergun validation is required.

With bed geometry, particle size, catalyst dilution, and thermal boundary data, the same model can be rerun with the coupled energy balance and Ergun pressure-drop equation. Unrounded GC calculations would also allow species-by-species outlet validation, rather than conversion-only benchmarking.
"""
    (output_dir / "GROUP14_VERIFICATION_AUDIT.md").write_text(report, encoding="utf-8")


def _plot_conversion_comparison(
    comparison: Group14Comparison,
    path: Path,
    result: SimulationResult | None = None,
    observation_label: str = "Reported Group 14 value",
    annotation_prefix: str = "Reported",
) -> None:
    """Render Design 3 two-tier Physical Review precision plot with residuals."""
    import matplotlib.ticker as ticker
    from matplotlib.gridspec import GridSpec

    apply_design3_style(font_size=10.5)

    if result is not None:
        w_model = result.catalyst_mass_kg * 1000.0  # grams
        x_model = result.co_conversion * 100.0      # %
    else:
        w_max = comparison.catalyst_mass_kg * 1000.0
        w_model = np.linspace(0.0, w_max, 100)
        k_est = 2.5
        x_model = 100.0 * comparison.predicted_co_conversion_fraction * (1.0 - np.exp(-k_est * (w_model / max(w_max, 1e-6)) ** 1.3))

    w_end = float(w_model[-1]) if len(w_model) > 0 else 3.0
    w_exp = comparison.catalyst_mass_kg * 1000.0
    x_exp = comparison.experimental_co_conversion_fraction * 100.0
    residual = comparison.signed_error_percentage_points

    fig = plt.figure(figsize=(5.8, 4.8))
    gs = GridSpec(nrows=2, ncols=1, height_ratios=[3.2, 1.0], hspace=0.10)

    ax_main = fig.add_subplot(gs[0])
    ax_res = fig.add_subplot(gs[1], sharex=ax_main)

    # Upper panel: model curve and the unreconciled value reported by Group 14.
    ax_main.plot(
        w_model,
        x_model,
        color=COLOR_MODEL,
        linewidth=2.2,
        label=rf"{comparison.model_label} ($T={comparison.inlet_temperature_k - 273.15:.0f}\,^\circ\mathrm{{C}}$, $P={comparison.inlet_pressure_bar:.2f}\,\mathrm{{bar}}$)",
        zorder=3,
    )
    ax_main.plot(
        [w_exp],
        [x_exp],
        marker="o",
        linestyle="none",
        color=COLOR_EXP,
        markerfacecolor="#FFFFFF",
        markeredgecolor=COLOR_EXP,
        markeredgewidth=1.8,
        markersize=6.8,
        label=observation_label,
        zorder=4,
    )

    ax_main.annotate(
        rf"{annotation_prefix}: {x_exp:.3f}$\%$",
        xy=(w_exp, x_exp),
        xytext=(w_exp - 1.25, x_exp + 12.0),
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=-0.15",
            color=COLOR_EXP,
            lw=1.1,
        ),
        fontsize=8.8,
        fontweight="bold",
        color=COLOR_EXP,
        zorder=5,
    )

    ax_main.set_ylabel(r"$\mathrm{CO}$ Conversion, $X_{\mathrm{CO}}$ [$\%$]", labelpad=6)
    ax_main.set_xlim(0.0, max(w_end * 1.05, 3.2))
    ax_main.set_ylim(0.0, 105.0)
    ax_main.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax_main.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax_main.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    plt.setp(ax_main.get_xticklabels(), visible=False)

    ax_main.legend(
        loc="lower right",
        bbox_to_anchor=(0.96, 0.08),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#D0D0D0",
        framealpha=0.94,
        handlelength=2.0,
        handletextpad=0.6,
        labelspacing=0.45,
    )

    ax_main.text(
        0.03, 0.94, "a",
        transform=ax_main.transAxes,
        fontsize=13,
        fontweight="bold",
        va="top",
        ha="left",
    )

    # Lower panel: prediction minus reported value, in percentage points.
    ax_res.axhline(0, color=COLOR_ZERO, linestyle="--", linewidth=0.85, zorder=2)
    ax_res.plot(
        [w_exp],
        [residual],
        marker="s",
        linestyle="none",
        color=COLOR_EXP,
        markerfacecolor=COLOR_EXP,
        markeredgecolor=COLOR_EXP,
        markersize=5.2,
        zorder=4,
    )

    ax_res.set_xlabel(r"Catalyst Mass, $W$ [$\mathrm{g}$]", labelpad=6)
    ax_res.set_ylabel(r"$\Delta X_{\mathrm{CO}}$ [pp]", labelpad=6)
    y_max = max(abs(residual) * 1.25, 5.0)
    ax_res.set_ylim(-y_max, y_max)
    ax_res.tick_params(top=False)
    ax_res.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

    save_figure(fig, path, dpi=300, tight=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare an M4 model with Group 14's reported CO conversion.")
    parser.add_argument("--data", required=True, help="JSON transcribed from Group 14 data document")
    parser.add_argument("--output", required=True, help="Directory for comparison outputs")
    parser.add_argument(
        "--reaction-mode", choices=("m4_full", "m4_reduced_co_wgs"), default="m4_full"
    )
    args = parser.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    audit = audit_group14_data(data)
    comparison, result = compare_group14_experiment(data, args.reaction_mode)
    _write_report(data, audit, comparison, Path(args.output), result=result)
    print(f"predicted_co_conversion={comparison.predicted_co_conversion_fraction:.6f}")
    print(f"experimental_co_conversion={comparison.experimental_co_conversion_fraction:.6f}")
    print(f"error_percentage_points={comparison.signed_error_percentage_points:+.6f}")
    print(f"outputs={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
