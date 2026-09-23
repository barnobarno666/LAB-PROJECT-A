"""Full-M4 sensitivity to inlet H2/CO ratio and catalyst space time."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .config import ReactorConfig
from .reactor import simulate


INK = "#203047"
PAPER = "#fffdf9"
BLUE = "#1c7890"
RED = "#cf3b38"
GOLD = "#df9b28"
CONTOUR_CMAP = "viridis"


def _axis_with_references(
    values: np.ndarray, references: tuple[float, ...]
) -> np.ndarray:
    result = values.copy()
    for reference in references:
        if np.min(values) <= reference <= np.max(values) and not np.any(
            np.isclose(result, reference)
        ):
            result = np.append(result, reference)
    return np.sort(result)


def _save_figure(fig, output_path: Path) -> None:
    fig.savefig(output_path.with_suffix(".png"), dpi=320, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n", encoding="utf-8")


def _base_experiment_config(
    config_path: Path,
    observed_data_path: Path,
    *,
    catalyst_mass_g: float,
    particle_density_kg_m3: float,
    transport_mode: str,
) -> tuple[ReactorConfig, dict[str, float | str]]:
    config = ReactorConfig.from_json(config_path)
    observed = json.loads(observed_data_path.read_text(encoding="utf-8"))
    basis = observed["basis"]
    inlet_mol_h = observed["inlet_molar_flow_mol_h"]

    co_mol_h = float(inlet_mol_h["CO"])
    h2_mol_h = float(inlet_mol_h["H2"])
    n2_mol_h = float(inlet_mol_h["N2"])
    if co_mol_h <= 0.0 or catalyst_mass_g <= 0.0:
        raise ValueError("The baseline CO feed and catalyst mass must be positive.")

    data = deepcopy(config.to_dict())
    bed_volume_m3 = config.bed_volume_m3
    catalyst_mass_kg = catalyst_mass_g / 1000.0
    particle_volume_capacity_kg = particle_density_kg_m3 * bed_volume_m3
    voidage = 1.0 - catalyst_mass_kg / particle_volume_capacity_kg
    if not 0.0 < voidage < 1.0:
        raise ValueError("Catalyst mass and particle density imply invalid bed voidage.")

    total_mol_h = co_mol_h + h2_mol_h + n2_mol_h
    data["reaction_mode"] = "m4_full"
    data["feed"]["temperature_k"] = float(basis["reaction_temperature_c"] + 273.15)
    data["feed"]["pressure_bar"] = float(basis["reaction_pressure_bar"])
    data["feed"]["total_molar_flow_mol_s"] = total_mol_h / 3600.0
    data["feed"]["mole_ratio"] = {"CO": co_mol_h, "H2": h2_mol_h, "N2": n2_mol_h}
    data["bed"]["catalyst_loading_kg_m3_bed"] = catalyst_mass_kg / bed_volume_m3
    data["bed"]["void_fraction"] = voidage
    data["thermal"]["mode"] = "isothermal"
    data["transport"]["mode"] = transport_mode

    metadata: dict[str, float | str] = {
        "baseline_co_feed_mol_h": co_mol_h,
        "baseline_h2_feed_mol_h": h2_mol_h,
        "baseline_n2_feed_mol_h": n2_mol_h,
        "baseline_h2_co_ratio": h2_mol_h / co_mol_h,
        "baseline_n2_co_ratio": n2_mol_h / co_mol_h,
        "baseline_total_feed_mol_h": total_mol_h,
        "baseline_catalyst_mass_g": catalyst_mass_g,
        "baseline_space_time_kg_s_mol": catalyst_mass_kg / (co_mol_h / 3600.0),
        "bed_volume_m3": bed_volume_m3,
        "bed_voidage": voidage,
        "particle_density_kg_m3_assumed": particle_density_kg_m3,
        "inlet_temperature_c": float(basis["reaction_temperature_c"]),
        "inlet_pressure_bar_abs": float(basis["reaction_pressure_bar"]),
        "transport_mode": transport_mode,
        "thermal_mode": "isothermal",
        "pressure_source_note": str(basis.get("pressure_interpretation", "")),
    }
    return ReactorConfig.from_dict(data), metadata


def _simulate_case(
    base_config: ReactorConfig,
    *,
    h2_co_ratio: float,
    space_time_multiple: float,
    baseline: dict[str, float | str],
) -> dict[str, object]:
    scenario = deepcopy(base_config.to_dict())
    co_mol_h = float(baseline["baseline_co_feed_mol_h"]) / space_time_multiple
    h2_mol_h = h2_co_ratio * co_mol_h
    n2_mol_h = float(baseline["baseline_n2_co_ratio"]) * co_mol_h
    total_mol_h = co_mol_h + h2_mol_h + n2_mol_h

    scenario["feed"]["total_molar_flow_mol_s"] = total_mol_h / 3600.0
    scenario["feed"]["mole_ratio"] = {
        "CO": co_mol_h,
        "H2": h2_mol_h,
        "N2": n2_mol_h,
    }
    case_config = ReactorConfig.from_dict(scenario)
    space_time = float(baseline["baseline_space_time_kg_s_mol"]) * space_time_multiple

    record: dict[str, object] = {
        "h2_co_molar_ratio": h2_co_ratio,
        "space_time_multiple_of_experiment1": space_time_multiple,
        "catalyst_space_time_kg_s_mol_co": space_time,
        "co_feed_mol_h": co_mol_h,
        "h2_feed_mol_h": h2_mol_h,
        "n2_feed_mol_h": n2_mol_h,
        "total_feed_mol_h": total_mol_h,
        "inlet_pressure_bar_abs": case_config.feed.pressure_bar,
    }
    try:
        result = simulate(case_config)
        if result.success:
            record.update(
                {
                    "outlet_co_conversion_pct": float(result.co_conversion[-1] * 100.0),
                    "outlet_ch4_yield_pct": float(result.methane_yield[-1] * 100.0),
                    "peak_temperature_c": float(np.max(result.temperature_k) - 273.15),
                    "outlet_pressure_bar_abs": float(result.pressure_pa[-1] / 100000.0),
                    "pressure_drop_pa": float(
                        (result.pressure_pa[0] - result.pressure_pa[-1])
                    ),
                    "status": "completed",
                    "terminal_event": result.terminal_event or "",
                    "solver_function_evaluations": int(result.nfev),
                    "message": result.message,
                }
            )
        else:
            record.update(
                {
                    "outlet_co_conversion_pct": float("nan"),
                    "outlet_ch4_yield_pct": float("nan"),
                    "peak_temperature_c": float(np.max(result.temperature_k) - 273.15),
                    "outlet_pressure_bar_abs": float(result.pressure_pa[-1] / 100000.0),
                    "pressure_drop_pa": float(
                        (result.pressure_pa[0] - result.pressure_pa[-1])
                    ),
                    "status": "incomplete",
                    "terminal_event": result.terminal_event or "",
                    "solver_function_evaluations": int(result.nfev),
                    "message": result.message,
                }
            )
    except Exception as error:  # Preserve failed grid cells in the audit CSV.
        record.update(
            {
                "outlet_co_conversion_pct": float("nan"),
                "outlet_ch4_yield_pct": float("nan"),
                "peak_temperature_c": float("nan"),
                "outlet_pressure_bar_abs": float("nan"),
                "pressure_drop_pa": float("nan"),
                "status": "error",
                "terminal_event": "",
                "solver_function_evaluations": 0,
                "message": f"{type(error).__name__}: {error}",
            }
        )
    return record


def _write_contour(
    ratios: np.ndarray,
    space_times: np.ndarray,
    conversion_pct: np.ndarray,
    *,
    reference_ratio: float,
    reference_space_time: float,
    reference_conversion: float,
    output_path: Path,
    conditions_note: str,
) -> None:
    values = conversion_pct[np.isfinite(conversion_pct)]
    low, high = float(np.min(values)), float(np.max(values))
    if np.isclose(low, high):
        low -= 0.5
        high += 0.5
    levels = np.linspace(low, high, 17)

    plt.rcParams.update(
        {
            "font.family": "serif",
            "mathtext.fontset": "dejavuserif",
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "savefig.facecolor": PAPER,
        }
    )
    fig, ax = plt.subplots(figsize=(10.2, 7.3), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    contour = ax.contourf(
        ratios,
        space_times,
        np.ma.masked_invalid(conversion_pct),
        levels=levels,
        cmap=CONTOUR_CMAP,
        extend="both",
    )
    if high - low > 1.0e-8:
        ax.contour(
            ratios,
            space_times,
            np.ma.masked_invalid(conversion_pct),
            levels=np.linspace(low, high, 7)[1:-1],
            colors="#fffdf9",
            linewidths=0.75,
            alpha=0.9,
        )
    ax.axvline(3.0, color="#f3d477", linewidth=1.6, linestyle="--", label="Stoichiometric H₂/CO = 3")
    ax.scatter(
        [reference_ratio],
        [reference_space_time],
        s=84,
        marker="o",
        facecolor=PAPER,
        edgecolor=INK,
        linewidth=1.5,
        zorder=5,
        label=f"Experiment 1 reference model: {reference_conversion:.1f}%",
    )
    ax.set_yscale("log")
    ax.set_xlabel(r"Inlet H$_2$/CO molar ratio", fontsize=12, labelpad=9)
    ax.set_ylabel(
        r"Catalyst space time, $W_{cat}/F_{CO,in}$ [kg$_{cat}$ s mol$^{-1}_{CO}$]",
        fontsize=11.5,
        labelpad=10,
    )
    ax.set_title(
        "CO Conversion: Feed Stoichiometry × Catalyst Space Time",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=16,
    )
    ax.grid(color="#ffffff", alpha=0.18, linewidth=0.65)
    ax.legend(loc="lower right", frameon=True, facecolor=PAPER, edgecolor="#d7d2c8", fontsize=9)
    colorbar = fig.colorbar(contour, ax=ax, pad=0.025, fraction=0.05)
    colorbar.set_label("Outlet CO conversion [%]", fontsize=10.5)
    colorbar.outline.set_edgecolor("#b8b2a5")
    fig.text(0.12, 0.035, conditions_note, ha="left", va="bottom", fontsize=8.4, color="#595b61")
    fig.subplots_adjust(left=0.14, right=0.87, top=0.88, bottom=0.15)
    _save_figure(fig, output_path)
    plt.close(fig)


def _write_slice(
    x: np.ndarray,
    conversion_pct: np.ndarray,
    *,
    x_label: str,
    title: str,
    output_path: Path,
    x_scale: str,
    reference_x: float,
    reference_conversion: float,
    reported_conversion: float,
    source_note: str,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "mathtext.fontset": "dejavuserif",
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "savefig.facecolor": PAPER,
        }
    )
    fig, ax = plt.subplots(figsize=(9.0, 5.8), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.plot(x, conversion_pct, color=BLUE, linewidth=2.4, marker="o", markersize=4.4, label="Full M4 prediction")
    ax.axvline(reference_x, color=GOLD, linewidth=1.35, linestyle=(0, (2, 3)), label="Reference condition")
    ax.scatter(
        [reference_x],
        [reference_conversion],
        s=72,
        marker="o",
        facecolor=PAPER,
        edgecolor=INK,
        linewidth=1.4,
        zorder=5,
    )
    ax.scatter(
        [reference_x],
        [reported_conversion],
        s=64,
        marker="s",
        color=RED,
        edgecolor=PAPER,
        linewidth=0.7,
        zorder=5,
        label=f"Experiment 1 reported at reference: {reported_conversion:.2f}%",
    )
    ax.set_xscale(x_scale)
    ax.set_ylim(0.0, 100.0)
    ax.set_xlabel(x_label, fontsize=11.5, labelpad=8)
    ax.set_ylabel("Outlet CO conversion [%]", fontsize=11.5, labelpad=8)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", pad=13)
    ax.grid(axis="y", color="#756b5d", alpha=0.15, linewidth=0.7)
    ax.legend(loc="best", frameon=True, facecolor=PAPER, edgecolor="#d7d2c8", fontsize=8.7)
    fig.text(0.12, 0.025, source_note, ha="left", va="bottom", fontsize=8.0, color="#595b61")
    fig.subplots_adjust(left=0.13, right=0.97, top=0.88, bottom=0.18)
    _save_figure(fig, output_path)
    plt.close(fig)


def run_sweep(
    config_path: Path,
    observed_data_path: Path,
    output_dir: Path,
    *,
    ratio_min: float = 1.0,
    ratio_max: float = 5.0,
    ratio_points: int = 21,
    space_time_min_multiple: float = 0.25,
    space_time_max_multiple: float = 4.0,
    space_time_points: int = 21,
    catalyst_mass_g: float = 3.12,
    particle_density_kg_m3: float = 1250.0,
    transport_mode: str = "ergun",
    solver_method: str = "BDF",
) -> dict[str, object]:
    if ratio_points < 3 or space_time_points < 3:
        raise ValueError("Each sweep axis needs at least three points.")
    if ratio_min >= ratio_max or space_time_min_multiple <= 0.0 or space_time_min_multiple >= space_time_max_multiple:
        raise ValueError("Sweep minima must be positive and smaller than their maxima.")
    if transport_mode not in {"ergun", "constant_pressure"}:
        raise ValueError("transport_mode must be ergun or constant_pressure.")
    if solver_method not in {"Radau", "BDF"}:
        raise ValueError("solver_method must be Radau or BDF.")

    base_config, baseline = _base_experiment_config(
        config_path,
        observed_data_path,
        catalyst_mass_g=catalyst_mass_g,
        particle_density_kg_m3=particle_density_kg_m3,
        transport_mode=transport_mode,
    )
    config_data = base_config.to_dict()
    config_data["solver"]["method"] = solver_method
    base_config = ReactorConfig.from_dict(config_data)
    observed = json.loads(observed_data_path.read_text(encoding="utf-8"))
    reference_ratio = float(baseline["baseline_h2_co_ratio"])
    reference_space_time = float(baseline["baseline_space_time_kg_s_mol"])
    reported_conversion_pct = float(observed["reported_metrics"]["co_conversion_fraction"] * 100.0)

    ratios = _axis_with_references(
        np.linspace(ratio_min, ratio_max, ratio_points), (3.0, reference_ratio)
    )
    space_time_multiples = _axis_with_references(
        np.geomspace(space_time_min_multiple, space_time_max_multiple, space_time_points),
        (1.0,),
    )
    space_times = reference_space_time * space_time_multiples
    conversion_pct = np.full((len(space_time_multiples), len(ratios)), np.nan)
    rows: list[dict[str, object]] = []
    total_cases = conversion_pct.size
    started_at = time.perf_counter()

    for time_index, time_multiple in enumerate(space_time_multiples):
        for ratio_index, ratio in enumerate(ratios):
            row = _simulate_case(
                base_config,
                h2_co_ratio=float(ratio),
                space_time_multiple=float(time_multiple),
                baseline=baseline,
            )
            rows.append(row)
            if row["status"] == "completed":
                conversion_pct[time_index, ratio_index] = float(row["outlet_co_conversion_pct"])

        completed = (time_index + 1) * len(ratios)
        print(f"solved {completed}/{total_cases} cases", flush=True)

    successful = [row for row in rows if row["status"] == "completed"]
    failed = total_cases - len(successful)
    if not successful:
        raise RuntimeError("Every ratio/contact-time case failed; no plots can be written.")

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ratio_contact_time_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    ref_ratio_index = int(np.argmin(np.abs(ratios - reference_ratio)))
    ref_time_index = int(np.argmin(np.abs(space_time_multiples - 1.0)))
    reference_row = rows[ref_time_index * len(ratios) + ref_ratio_index]
    reference_conversion = float(reference_row["outlet_co_conversion_pct"])
    if not np.isfinite(reference_conversion):
        raise RuntimeError("The baseline ratio/contact-time case failed; slices cannot be anchored.")

    bed = base_config.bed
    conditions_note = (
        f"Fixed: Experiment 1 T={float(baseline['inlet_temperature_c']):.0f} °C, "
        f"P={float(baseline['inlet_pressure_bar_abs']):.2f} bar; W={catalyst_mass_g:.2f} g; "
        f"D={bed.tube_diameter_m * 1000:.1f} mm, L={bed.bed_length_m * 1000:.1f} mm; "
        f"ε={float(baseline['bed_voidage']):.4f}; isothermal; {transport_mode} pressure model."
    )
    contour_path = output_dir / "ratio_contact_time_co_conversion"
    _write_contour(
        ratios,
        space_times,
        conversion_pct,
        reference_ratio=reference_ratio,
        reference_space_time=reference_space_time,
        reference_conversion=reference_conversion,
        output_path=contour_path,
        conditions_note=conditions_note,
    )

    ratio_slice_path = output_dir / "co_conversion_vs_h2_co_ratio"
    _write_slice(
        ratios,
        conversion_pct[ref_time_index, :],
        x_label=r"Inlet H$_2$/CO molar ratio",
        title="CO Conversion vs H₂/CO Ratio",
        output_path=ratio_slice_path,
        x_scale="linear",
        reference_x=reference_ratio,
        reference_conversion=reference_conversion,
        reported_conversion=reported_conversion_pct,
        source_note=(
            f"Space time fixed at Experiment 1 baseline: {reference_space_time:.2f} "
            "kgcat s mol−1 CO. The red square marks the reported value at the reference point; it is not a fit target."
        ),
    )

    baseline_ratio_index = int(np.argmin(np.abs(ratios - reference_ratio)))
    space_slice_path = output_dir / "co_conversion_vs_space_time"
    _write_slice(
        space_times,
        conversion_pct[:, baseline_ratio_index],
        x_label=r"Catalyst space time, $W_{cat}/F_{CO,in}$ [kg$_{cat}$ s mol$^{-1}_{CO}$]",
        title="CO Conversion vs Catalyst Space Time",
        output_path=space_slice_path,
        x_scale="log",
        reference_x=reference_space_time,
        reference_conversion=reference_conversion,
        reported_conversion=reported_conversion_pct,
        source_note=(
            f"H₂/CO fixed at the Experiment 1 baseline ({reference_ratio:.4f}); the red square marks "
            "the source-reported conversion at the reference point, not a fit target."
        ),
    )

    elapsed_seconds = time.perf_counter() - started_at
    conversion_values = [float(row["outlet_co_conversion_pct"]) for row in successful]
    methane_values = [float(row["outlet_ch4_yield_pct"]) for row in successful]
    metadata: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": "m4_full",
        "metric": "completed-bed outlet CO conversion (%)",
        "sweep_grid": {
            "h2_co_ratio": [float(np.min(ratios)), float(np.max(ratios))],
            "h2_co_ratio_points": int(len(ratios)),
            "space_time_kg_s_mol_co": [float(np.min(space_times)), float(np.max(space_times))],
            "space_time_multiples": [float(np.min(space_time_multiples)), float(np.max(space_time_multiples))],
            "space_time_points": int(len(space_times)),
        },
        "reference_case": {
            "h2_co_ratio": reference_ratio,
            "catalyst_space_time_kg_s_mol_co": reference_space_time,
            "co_feed_mol_h": float(baseline["baseline_co_feed_mol_h"]),
            "outlet_co_conversion_pct": reference_conversion,
            "source_reported_conversion_pct": reported_conversion_pct,
            "outlet_ch4_yield_pct": float(reference_row["outlet_ch4_yield_pct"]),
            "peak_temperature_c": float(reference_row["peak_temperature_c"]),
            "outlet_pressure_bar_abs": float(reference_row["outlet_pressure_bar_abs"]),
        },
        "fixed_inputs": baseline,
        "solver_method": solver_method,
        "source_roles": {
            "input_basis": str(observed.get("source", "Experiment 1 observed data file")),
            "reported_conversion_is_fit_target": False,
            "pressure_interpretation": str(baseline["pressure_source_note"]),
        },
        "model_domain_and_geometry_notes": [
            "The chosen Experiment 1 pressure is 2 bar; the project's published kinetic-fit pressure range begins at 5 bar, so all cells extrapolate in pressure.",
            "The 1 in x 12 in reactor dimensions are inherited assumptions, not dimensions confirmed by Experiment 1.",
            "At 3.12 g, the assumed geometry and particle density imply very high voidage; this is a sparse-bed illustration, not a conventional packed-bed validation.",
            "The model is isothermal at the reported inlet temperature; this sweep isolates composition and throughput effects but does not predict hot spots.",
            "Throughput variation scales CO and N2 together; H2 is recalculated from the selected H2/CO ratio.",
        ],
        "sweep_behavior": {
            "varied": ["inlet H2/CO ratio", "CO feed rate at fixed catalyst mass and bed voidage"],
            "held_fixed": ["catalyst mass", "bed geometry", "bed voidage", "inlet temperature", "inlet pressure", "N2/CO ratio", "isothermal operation"],
            "space_time_definition": "catalyst mass / inlet CO molar flow",
            "failed_or_incomplete_cells": "retained in the CSV and masked in plots",
        },
        "completed_cases": len(successful),
        "failed_or_incomplete_cases": failed,
        "conversion_range_pct": [min(conversion_values), max(conversion_values)],
        "methane_yield_range_pct": [min(methane_values), max(methane_values)],
        "elapsed_seconds": elapsed_seconds,
        "outputs": [
            csv_path.name,
            "ratio_contact_time_co_conversion.png",
            "ratio_contact_time_co_conversion.svg",
            "co_conversion_vs_h2_co_ratio.png",
            "co_conversion_vs_h2_co_ratio.svg",
            "co_conversion_vs_space_time.png",
            "co_conversion_vs_space_time.svg",
        ],
    }
    (output_dir / "sweep_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(
        f"completed={len(successful)} failed_or_incomplete={failed} "
        f"conversion_pct={min(conversion_values):.3f}..{max(conversion_values):.3f} "
        f"reference_pct={reference_conversion:.3f}"
    )
    print(f"outputs={output_dir.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sweep full-M4 CO conversion over inlet H2/CO ratio and catalyst space time."
    )
    parser.add_argument("--config", type=Path, default=Path("configs/assumed_base_case.json"))
    parser.add_argument("--observed-data", type=Path, default=Path("data/experiment1_observed_data.json"))
    parser.add_argument("--output", type=Path, default=Path("results/experiment1_ratio_contact_time_sweep"))
    parser.add_argument("--ratio-min", type=float, default=1.0)
    parser.add_argument("--ratio-max", type=float, default=5.0)
    parser.add_argument("--ratio-points", type=int, default=21)
    parser.add_argument("--space-time-min-multiple", type=float, default=0.25)
    parser.add_argument("--space-time-max-multiple", type=float, default=4.0)
    parser.add_argument("--space-time-points", type=int, default=21)
    parser.add_argument("--catalyst-mass-g", type=float, default=3.12)
    parser.add_argument("--particle-density-kg-m3", type=float, default=1250.0)
    parser.add_argument("--transport-mode", choices=("ergun", "constant_pressure"), default="ergun")
    parser.add_argument("--solver-method", choices=("Radau", "BDF"), default="BDF")
    args = parser.parse_args()
    run_sweep(
        args.config,
        args.observed_data,
        args.output,
        ratio_min=args.ratio_min,
        ratio_max=args.ratio_max,
        ratio_points=args.ratio_points,
        space_time_min_multiple=args.space_time_min_multiple,
        space_time_max_multiple=args.space_time_max_multiple,
        space_time_points=args.space_time_points,
        catalyst_mass_g=args.catalyst_mass_g,
        particle_density_kg_m3=args.particle_density_kg_m3,
        transport_mode=args.transport_mode,
        solver_method=args.solver_method,
    )


if __name__ == "__main__":
    main()
