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


def _write_panel_figures(
    output_dir: Path,
    *,
    co_values: np.ndarray,
    h2_values: np.ndarray,
    n2_values: np.ndarray,
    co_surface: np.ndarray,
    n2_surface: np.ndarray,
) -> None:
    apply_design3_style(font_size=14)
    output_dir.mkdir(parents=True, exist_ok=True)
    levels = np.linspace(0.0, 100.0, 21)
    panels = (
        (
            "co_conversion_h2_co",
            co_values,
            co_surface,
            r"Inlet CO flow, $F_{\mathrm{CO,in}}$ (mol h$^{-1}$)",
        ),
        (
            "co_conversion_h2_n2",
            n2_values,
            n2_surface,
            r"Inlet N$_2$ flow, $F_{\mathrm{N_2,in}}$ (mol h$^{-1}$)",
        ),
    )
    for stem, x_values, surface, x_label in panels:
        x_grid, y_grid = np.meshgrid(x_values, h2_values)
        fig, ax = plt.subplots(figsize=(7.6, 6.0), facecolor=PAPER)
        ax.set_facecolor(PAPER)
        filled = ax.contourf(
            x_grid,
            y_grid,
            np.ma.masked_invalid(surface),
            levels=levels,
            cmap=CONTOUR_CMAP,
        )
        ax.set_xlabel(x_label)
        ax.set_ylabel(r"Inlet H$_2$ flow, $F_{\mathrm{H_2,in}}$ (mol h$^{-1}$)")
        ax.set_xlim(float(x_values[0]), float(x_values[-1]))
        ax.set_ylim(float(h2_values[0]), float(h2_values[-1]))
        cbar = fig.colorbar(filled, ax=ax, pad=0.035, fraction=0.055)
        cbar.set_label("CO conversion (%)")
        cbar.set_ticks(np.arange(0.0, 101.0, 20.0))
        fig.tight_layout(pad=0.6)
        fig.savefig(output_dir / f"{stem}.png", dpi=600, bbox_inches="tight")
        svg_path = output_dir / f"{stem}.svg"
        fig.savefig(svg_path, bbox_inches="tight")
        svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
        svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n", encoding="utf-8")
        plt.close(fig)
    for suffix in (".png", ".svg"):
        (output_dir / f"reactive_feed_flow_contour{suffix}").unlink(missing_ok=True)


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

    _write_panel_figures(
        output_dir,
        co_values=co_values,
        h2_values=h2_values,
        n2_values=n2_values,
        co_surface=co_surface,
        n2_surface=n2_surface,
    )

    failed = sum(record["status"] != "completed" for record in records)
    metadata: dict[str, object] = {
        "model": "m4_full",
        "metric": "completed-bed outlet CO conversion percent",
        "common_model_conditions": {
            "temperature_c": float(experiment1["basis"]["reaction_temperature_c"]),
            "pressure_bar_abs": pressure_bar,
            "pressure_override_note": (
                f"Both contour panels use {pressure_bar:g} bar. Group 14 source reports 760 mmHg; "
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
            "co_conversion_h2_co.png",
            "co_conversion_h2_co.svg",
            "co_conversion_h2_n2.png",
            "co_conversion_h2_n2.svg",
            "feed_flow_contour.csv",
            "feed_flow_metadata.json",
            "README.md",
        ],
        "limits": [
            "The contour is a no-fit model sensitivity, not experimental validation.",
            f"Both source points are evaluated at common {pressure_bar:g} bar and "
            f"{catalyst_mass_g:g} g for a controlled comparison.",
            f"Full-M4 kinetic results at {pressure_bar:g} bar extrapolate below the 5-15 bar fit range.",
            "The Group-14 reported conversion is unresolved against its source GC and flow data.",
        ],
    }
    (output_dir / "feed_flow_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        f"""# Poster feed-flow contours

Run from the project root with: uv run m4-sweep-feed-flows

The two standalone plots use the no-fit Full M4 model at
{float(experiment1["basis"]["reaction_temperature_c"]):g} °C, {pressure_bar:g} bar,
{catalyst_mass_g:g} g catalyst, isothermal and constant-pressure conditions.
co_conversion_h2_co varies H2 and CO inlet molar flows while holding N2 at
0.799 mol/h. co_conversion_h2_n2 varies H2 and N2 while holding CO at 0.320 mol/h.

The image files contain the contour results, axes, and conversion scale only.
Both surfaces use the common pressure of {pressure_bar:g} bar. The predictions
extrapolate below the 5-15 bar kinetic-fit range.

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
