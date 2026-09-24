"""Full-M4 contour maps over reactive feed rates and inert-gas dilution."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np

from .config import ReactorConfig
from .plotting import apply_design3_style
from .reactor import simulate
from .verification import group14_comparison_config


PAPER = "#fffdf9"
PA_PER_BAR_IN_MMHG = 750.061683
CONTOUR_CMAP = LinearSegmentedColormap.from_list(
    "feed_flow_violet_sunset",
    ["#24104f", "#63358d", "#bd4f91", "#ec865f", "#f5c96a", "#fff2c6"],
    N=256,
)
GROUP14_COLOR = "#c92a2a"
SUBAH_COLOR = "#007c91"


def _axis_with_references(values: np.ndarray, references: tuple[float, ...]) -> np.ndarray:
    result = values.copy()
    for reference in references:
        if np.min(values) <= reference <= np.max(values) and not np.any(
            np.isclose(result, reference, rtol=0.0, atol=1.0e-12)
        ):
            result = np.append(result, reference)
    return np.sort(result)


def _common_model_config(
    group14_data: dict[str, object],
    experiment1_data: dict[str, object],
    *,
    catalyst_mass_g: float,
    pressure_bar: float,
) -> dict[str, object]:
    current_basis = experiment1_data["basis"]
    common = deepcopy(group14_data)
    common["basis"]["catalyst_mass_g"] = catalyst_mass_g
    common["basis"]["reaction_temperature_c"] = float(current_basis["reaction_temperature_c"])
    common["basis"]["reaction_pressure_mmhg"] = pressure_bar * PA_PER_BAR_IN_MMHG
    common["inlet_molar_flow_mol_h"] = deepcopy(
        experiment1_data["inlet_molar_flow_mol_h"]
    )
    config = group14_comparison_config(common, reaction_mode="m4_full").to_dict()
    config["transport"]["mode"] = "constant_pressure"
    config["thermal"]["mode"] = "isothermal"
    config["solver"]["method"] = "BDF"
    config["solver"]["rtol"] = 1.0e-6
    config["solver"]["atol_flow_mol_s"] = 1.0e-10
    return config


def _simulate_flows(
    base_config: dict[str, object], flows_mol_h: dict[str, float]
) -> tuple[float, bool, str]:
    config_data = deepcopy(base_config)
    config_data["feed"]["mole_ratio"] = dict(flows_mol_h)
    config_data["feed"]["total_molar_flow_mol_s"] = sum(flows_mol_h.values()) / 3600.0
    result = simulate(ReactorConfig.from_dict(config_data))
    return float(result.co_conversion[-1] * 100.0), result.success, result.message


def _run_surface(
    base_config: dict[str, object],
    *,
    panel: str,
    x_species: str,
    x_values: np.ndarray,
    y_values: np.ndarray,
    fixed_species: str,
    fixed_flow_mol_h: float,
) -> tuple[np.ndarray, list[dict[str, object]]]:
    conversion = np.full((len(y_values), len(x_values)), np.nan)
    records: list[dict[str, object]] = []
    total = len(x_values) * len(y_values)
    completed = 0
    for iy, h2_flow in enumerate(y_values):
        for ix, x_flow in enumerate(x_values):
            flows = {"CO": 0.0, "H2": float(h2_flow), "N2": 0.0}
            flows[x_species] = float(x_flow)
            flows[fixed_species] = float(fixed_flow_mol_h)
            try:
                value, success, message = _simulate_flows(base_config, flows)
                if success:
                    conversion[iy, ix] = value
                    status = "completed"
                else:
                    status = "incomplete"
            except Exception as error:
                value = float("nan")
                message = f"{type(error).__name__}: {error}"
                status = "error"
            records.append(
                {
                    "panel": panel,
                    "x_species": x_species,
                    "x_feed_mol_h": float(x_flow),
                    "y_species": "H2",
                    "y_feed_mol_h": float(h2_flow),
                    "fixed_species": fixed_species,
                    "fixed_feed_mol_h": float(fixed_flow_mol_h),
                    "co_feed_mol_h": flows["CO"],
                    "h2_feed_mol_h": flows["H2"],
                    "n2_feed_mol_h": flows["N2"],
                    "total_feed_mol_h": sum(flows.values()),
                    "co_conversion_pct": value,
                    "status": status,
                    "solver_message": message,
                }
            )
            completed += 1
        print(f"{panel}: solved {completed}/{total} cases", flush=True)
    return conversion, records


def _point_value(
    values: np.ndarray,
    x_values: np.ndarray,
    y_values: np.ndarray,
    x: float,
    y: float,
) -> float:
    ix = int(np.argmin(np.abs(x_values - x)))
    iy = int(np.argmin(np.abs(y_values - y)))
    if not np.isclose(x_values[ix], x) or not np.isclose(y_values[iy], y):
        raise ValueError("A source point is missing from the resolved contour grid.")
    value = float(values[iy, ix])
    if not np.isfinite(value):
        raise RuntimeError("A source-point model simulation did not complete.")
    return value


def _draw_source_point(
    ax,
    *,
    x: float,
    y: float,
    color: str,
    marker: str,
    label: str,
    conversion_text: str,
    offset: tuple[int, int],
) -> None:
    ax.scatter(
        [x],
        [y],
        s=78,
        marker=marker,
        facecolor=PAPER,
        edgecolor=color,
        linewidth=1.8,
        zorder=6,
    )
    ax.annotate(
        f"{label}\n{conversion_text}",
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        fontsize=7.6,
        color="#192a3a",
        bbox={"boxstyle": "round,pad=0.28", "facecolor": PAPER, "edgecolor": color, "alpha": 0.94},
        arrowprops={"arrowstyle": "-", "color": color, "lw": 0.8},
        zorder=7,
    )


def _write_figure(
    output_path: Path,
    *,
    co_values: np.ndarray,
    h2_values: np.ndarray,
    n2_values: np.ndarray,
    co_surface: np.ndarray,
    n2_surface: np.ndarray,
    group14: dict[str, object],
    experiment1: dict[str, object],
    group14_model_co_pct: float,
    experiment1_model_co_pct: float,
    catalyst_mass_g: float,
    pressure_bar: float,
    temperature_c: float,
    fixed_n2_mol_h: float,
    fixed_co_mol_h: float,
) -> None:
    apply_design3_style(font_size=9.5)
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 6.3), sharey=True, facecolor=PAPER)
    for ax in axes:
        ax.set_facecolor(PAPER)

    levels = np.linspace(0.0, 100.0, 21)
    co_x, co_y = np.meshgrid(co_values, h2_values)
    n2_x, n2_y = np.meshgrid(n2_values, h2_values)
    co_contour = axes[0].contourf(
        co_x,
        co_y,
        np.ma.masked_invalid(co_surface),
        levels=levels,
        cmap=CONTOUR_CMAP,
        extend="both",
    )
    axes[1].contourf(
        n2_x,
        n2_y,
        np.ma.masked_invalid(n2_surface),
        levels=levels,
        cmap=CONTOUR_CMAP,
        extend="both",
    )

    contour_lines = (20, 40, 60, 70, 80, 90, 95, 98)
    for ax, x_grid, y_grid, values in (
        (axes[0], co_x, co_y, co_surface),
        (axes[1], n2_x, n2_y, n2_surface),
    ):
        finite = values[np.isfinite(values)]
        available = [
            level for level in contour_lines
            if finite.size and finite.min() < level < finite.max()
        ]
        if available:
            lines = ax.contour(
                x_grid,
                y_grid,
                np.ma.masked_invalid(values),
                levels=available,
                colors="#fffdf9",
                linewidths=0.75,
                alpha=0.9,
            )
            ax.clabel(lines, inline=True, fontsize=7.4, fmt="%g%%")
        ax.grid(color="#ffffff", alpha=0.2, linewidth=0.6)
        ax.set_ylim(float(h2_values[0]), float(h2_values[-1]))

    group14_flows = group14["inlet_molar_flow_mol_h"]
    experiment1_flows = experiment1["inlet_molar_flow_mol_h"]
    observed_group14 = 100.0 * float(group14["reported_metrics"]["co_conversion_fraction"])
    observed_experiment1 = 100.0 * float(experiment1["reported_metrics"]["co_conversion_fraction"])

    _draw_source_point(
        axes[0],
        x=float(group14_flows["CO"]),
        y=float(group14_flows["H2"]),
        color=GROUP14_COLOR,
        marker="o",
        label="Group 14",
        conversion_text=f"model {group14_model_co_pct:.1f}% | report {observed_group14:.2f}%*",
        offset=(10, 9),
    )
    _draw_source_point(
        axes[0],
        x=float(experiment1_flows["CO"]),
        y=float(experiment1_flows["H2"]),
        color=SUBAH_COLOR,
        marker="D",
        label="Subah Exp. 1",
        conversion_text=f"model {experiment1_model_co_pct:.1f}% | report {observed_experiment1:.2f}%",
        offset=(10, -35),
    )
    _draw_source_point(
        axes[1],
        x=float(group14_flows["N2"]),
        y=float(group14_flows["H2"]),
        color=GROUP14_COLOR,
        marker="o",
        label="Group 14",
        conversion_text=f"model {group14_model_co_pct:.1f}% | report {observed_group14:.2f}%*",
        offset=(10, 9),
    )
    _draw_source_point(
        axes[1],
        x=float(experiment1_flows["N2"]),
        y=float(experiment1_flows["H2"]),
        color=SUBAH_COLOR,
        marker="D",
        label="Subah Exp. 1",
        conversion_text=f"model {experiment1_model_co_pct:.1f}% | report {observed_experiment1:.2f}%",
        offset=(10, -35),
    )

    co_line = np.linspace(float(co_values[0]), float(co_values[-1]), 200)
    stoich_h2 = 3.0 * co_line
    inside = stoich_h2 <= float(h2_values[-1])
    axes[0].plot(
        co_line[inside],
        stoich_h2[inside],
        color="#f3d477",
        linestyle="--",
        linewidth=1.5,
        label=r"Stoichiometric H$_2$/CO = 3",
        zorder=4,
    )
    axes[0].set_title(
        r"(a) Reactive feeds; $\mathrm{N_2}$ held fixed",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    axes[1].set_title(
        r"(b) $\mathrm{H_2}$ feed and $\mathrm{N_2}$ dilution; CO held fixed",
        loc="left",
        fontsize=11,
        fontweight="bold",
    )
    axes[0].set_xlabel(r"Inlet CO flow, $F_{\mathrm{CO,in}}$ [mol h$^{-1}$]")
    axes[1].set_xlabel(r"Inlet N$_2$ flow, $F_{\mathrm{N_2,in}}$ [mol h$^{-1}$]")
    axes[0].set_ylabel(r"Inlet H$_2$ flow, $F_{\mathrm{H_2,in}}$ [mol h$^{-1}$]")

    shared_handles = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            markerfacecolor=PAPER,
            markeredgecolor=GROUP14_COLOR,
            markersize=7,
            label="Group-14 feed",
        ),
        Line2D(
            [],
            [],
            marker="D",
            linestyle="none",
            markerfacecolor=PAPER,
            markeredgecolor=SUBAH_COLOR,
            markersize=6.5,
            label="Subah Experiment-1 feed",
        ),
        Line2D([], [], color="#f3d477", linestyle="--", linewidth=1.5, label=r"H$_2$/CO = 3 stoichiometric line"),
    ]
    fig.suptitle(
        "Full-M4 CO conversion across inlet feed rates",
        x=0.07,
        ha="left",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    fig.legend(
        handles=shared_handles,
        loc="upper center",
        bbox_to_anchor=(0.53, 0.925),
        ncol=3,
        frameon=True,
        facecolor=PAPER,
        edgecolor="#d7d2c8",
        fontsize=8.3,
    )
    cbar = fig.colorbar(co_contour, ax=axes, pad=0.025, fraction=0.045, shrink=0.88)
    cbar.set_label("Predicted outlet CO conversion [%]")
    fig.text(
        0.07,
        0.025,
        (
            f"Common model: {temperature_c:.0f} °C, {pressure_bar:.2f} bar, "
            f"{catalyst_mass_g:.2f} g, isothermal constant-pressure Full M4, activity 1. "
            f"Panel (a) N$_2$ = {fixed_n2_mol_h:.3f} mol/h; panel (b) CO = {fixed_co_mol_h:.3f} mol/h.\n"
            "Group-14 source used 3.00 g and 760 mmHg; its point is evaluated at the requested common 2 bar and 3.12 g. "
            "Subah PDF pressure is disputed; Appendix A states 2 bar.\n"
            "*Group-14's reported 99.207% is unresolved against its source GC/flow data. "
            "These 2-bar predictions extrapolate below the 5-15 bar kinetic-fit range."
        ),
        ha="left",
        va="bottom",
        fontsize=7.4,
        color="#555b65",
        wrap=True,
    )
    fig.subplots_adjust(left=0.09, right=0.87, top=0.84, bottom=0.22, wspace=0.20)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path.with_suffix(".png"), dpi=320, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n", encoding="utf-8")
    plt.close(fig)


def run_sweep(
    group14_data_path: Path,
    experiment1_data_path: Path,
    output_dir: Path,
    *,
    flow_points: int = 19,
    catalyst_mass_g: float = 3.12,
    pressure_bar: float = 2.0,
) -> dict[str, object]:
    if flow_points < 5:
        raise ValueError("flow_points must be at least 5.")
    group14 = json.loads(group14_data_path.read_text(encoding="utf-8"))
    experiment1 = json.loads(experiment1_data_path.read_text(encoding="utf-8"))
    group_flows = group14["inlet_molar_flow_mol_h"]
    subah_flows = experiment1["inlet_molar_flow_mol_h"]
    for species in ("CO", "N2"):
        if not np.isclose(float(group_flows[species]), float(subah_flows[species])):
            raise ValueError(
                f"The two sources must have the same {species} feed for these paired panels."
            )

    fixed_co = float(subah_flows["CO"])
    fixed_n2 = float(subah_flows["N2"])
    h2_values = _axis_with_references(
        np.linspace(0.20, 1.20, flow_points),
        (float(group_flows["H2"]), float(subah_flows["H2"])),
    )
    co_values = _axis_with_references(
        np.linspace(0.24, 0.40, flow_points),
        (float(group_flows["CO"]), float(subah_flows["CO"])),
    )
    n2_values = _axis_with_references(
        np.linspace(0.40, 1.20, flow_points),
        (float(group_flows["N2"]), float(subah_flows["N2"])),
    )

    common = _common_model_config(
        group14,
        experiment1,
        catalyst_mass_g=catalyst_mass_g,
        pressure_bar=pressure_bar,
    )
    co_surface, co_records = _run_surface(
        common,
        panel="H2_vs_CO_at_fixed_N2",
        x_species="CO",
        x_values=co_values,
        y_values=h2_values,
        fixed_species="N2",
        fixed_flow_mol_h=fixed_n2,
    )
    n2_surface, n2_records = _run_surface(
        common,
        panel="H2_vs_N2_at_fixed_CO",
        x_species="N2",
        x_values=n2_values,
        y_values=h2_values,
        fixed_species="CO",
        fixed_flow_mol_h=fixed_co,
    )
    group14_model = _point_value(
        co_surface,
        co_values,
        h2_values,
        float(group_flows["CO"]),
        float(group_flows["H2"]),
    )
    experiment1_model = _point_value(
        co_surface,
        co_values,
        h2_values,
        float(subah_flows["CO"]),
        float(subah_flows["H2"]),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    records = co_records + n2_records
    with (output_dir / "feed_flow_contour.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    _write_figure(
        output_dir / "reactive_feed_flow_contour",
        co_values=co_values,
        h2_values=h2_values,
        n2_values=n2_values,
        co_surface=co_surface,
        n2_surface=n2_surface,
        group14=group14,
        experiment1=experiment1,
        group14_model_co_pct=group14_model,
        experiment1_model_co_pct=experiment1_model,
        catalyst_mass_g=catalyst_mass_g,
        pressure_bar=pressure_bar,
        temperature_c=float(experiment1["basis"]["reaction_temperature_c"]),
        fixed_n2_mol_h=fixed_n2,
        fixed_co_mol_h=fixed_co,
    )

    failed = sum(record["status"] != "completed" for record in records)
    metadata: dict[str, object] = {
        "model": "m4_full",
        "metric": "completed-bed outlet CO conversion percent",
        "common_model_conditions": {
            "temperature_c": float(experiment1["basis"]["reaction_temperature_c"]),
            "pressure_bar_abs": pressure_bar,
            "pressure_override_note": (
                "Both contour panels use 2 bar by request. Group 14 source reports 760 mmHg; "
                "Subah's PDF conflicts between Appendix A and its narrative."
            ),
            "catalyst_mass_g": catalyst_mass_g,
            "thermal_mode": "isothermal",
            "transport_mode": "constant_pressure",
            "activity": 1.0,
            "fit_pressure_range_bar": [5.0, 15.0],
            "solver_method": "BDF",
            "solver_rtol": 1.0e-6,
            "solver_atol_flow_mol_s": 1.0e-10,
        },
        "panels": {
            "H2_vs_CO_at_fixed_N2": {
                "x_axis": "CO inlet molar flow (mol/h)",
                "y_axis": "H2 inlet molar flow (mol/h)",
                "fixed_N2_mol_h": fixed_n2,
                "co_range_mol_h": [float(co_values[0]), float(co_values[-1])],
                "h2_range_mol_h": [float(h2_values[0]), float(h2_values[-1])],
            },
            "H2_vs_N2_at_fixed_CO": {
                "x_axis": "N2 inlet molar flow (mol/h)",
                "y_axis": "H2 inlet molar flow (mol/h)",
                "fixed_CO_mol_h": fixed_co,
                "n2_range_mol_h": [float(n2_values[0]), float(n2_values[-1])],
                "h2_range_mol_h": [float(h2_values[0]), float(h2_values[-1])],
            },
        },
        "source_points": {
            "Group-14": {
                "inlet_molar_flow_mol_h": group_flows,
                "source_catalyst_mass_g": float(group14["basis"]["catalyst_mass_g"]),
                "source_pressure_mmhg": float(group14["basis"]["reaction_pressure_mmhg"]),
                "reported_conversion_pct": 100.0
                * float(group14["reported_metrics"]["co_conversion_fraction"]),
                "common_basis_model_prediction_pct": group14_model,
                "interpretation": "The reported 99.207% is unresolved against source flow and GC data.",
            },
            "Subah_Experiment_1": {
                "inlet_molar_flow_mol_h": subah_flows,
                "source_catalyst_mass_g": float(experiment1["basis"]["catalyst_mass_g"]),
                "source_pressure_bar": float(experiment1["basis"]["reaction_pressure_bar"]),
                "reported_conversion_pct": 100.0
                * float(experiment1["reported_metrics"]["co_conversion_fraction"]),
                "common_basis_model_prediction_pct": experiment1_model,
                "interpretation": experiment1["basis"]["pressure_interpretation"],
            },
        },
        "grid": {
            "flow_points_per_axis_before_reference_insertion": flow_points,
            "total_cases": len(records),
            "failed_or_incomplete_cases": failed,
        },
        "output_files": [
            "reactive_feed_flow_contour.png",
            "reactive_feed_flow_contour.svg",
            "feed_flow_contour.csv",
            "feed_flow_metadata.json",
            "README.md",
        ],
        "limits": [
            "The contour is a no-fit model sensitivity, not experimental validation.",
            "Both source points are evaluated at common 2 bar and 3.12 g for a controlled comparison.",
            "Full-M4 kinetic results at 2 bar extrapolate below the 5-15 bar fit range.",
            "The Group-14 reported conversion is unresolved against its source GC and flow data.",
        ],
    }
    (output_dir / "feed_flow_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        """# Reactive-feed and nitrogen-flow contour

Run from the project root with: uv run m4-sweep-feed-flows

The two panels use the no-fit Full M4 model at 350 °C, 2 bar, 3.12 g catalyst,
isothermal and constant-pressure conditions. Panel (a) varies the absolute H2
and CO inlet molar flows while holding N2 at 0.799 mol/h. Panel (b) varies H2
and N2 while holding CO at 0.320 mol/h. Thus N2 is included as a separate inert
dilution sensitivity, rather than treated as a reactive stoichiometric feed.

Markers show the reported inlet-flow coordinates. Their labels compare the
common-basis model prediction with the conversion reported by each source.
Group 14's source pressure is 760 mmHg and catalyst mass is 3.00 g; the
contour uses 2 bar and 3.12 g for both datasets by request. Group 14's 99.207%
reported conversion is unresolved against its own GC and flow values. The
Subah report also conflicts on pressure between Appendix A and its narrative.
Both model predictions are extrapolations below the 5-15 bar kinetic-fit range.

The CSV records every grid cell and solver status. The JSON file records the
resolved conditions and source-point predictions.
""",
        encoding="utf-8",
    )
    print(
        f"completed={len(records) - failed} failed_or_incomplete={failed} "
        f"group14_model_pct={group14_model:.3f} experiment1_model_pct={experiment1_model:.3f}"
    )
    print(f"outputs={output_dir.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sweep Full-M4 CO conversion over absolute H2/CO and H2/N2 feed rates."
    )
    parser.add_argument("--group14-data", type=Path, default=Path("data/group14_observed_data.json"))
    parser.add_argument(
        "--experiment1-data", type=Path, default=Path("data/experiment1_observed_data.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/experiment1_feed_flow_sensitivity")
    )
    parser.add_argument("--flow-points", type=int, default=19)
    parser.add_argument("--catalyst-mass-g", type=float, default=3.12)
    parser.add_argument("--pressure-bar", type=float, default=2.0)
    args = parser.parse_args()
    run_sweep(
        args.group14_data,
        args.experiment1_data,
        args.output,
        flow_points=args.flow_points,
        catalyst_mass_g=args.catalyst_mass_g,
        pressure_bar=args.pressure_bar,
    )


if __name__ == "__main__":
    main()
