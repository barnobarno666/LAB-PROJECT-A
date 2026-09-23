"""Full-M4 overview sweep in feed ratio, inlet temperature, and pressure."""

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
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

from .config import ReactorConfig
from .reactor import simulate


INK = "#241b35"
PAPER = "#fffdf9"
FIT_LINE = "#756980"
CMAP = LinearSegmentedColormap.from_list(
    "violet_sunset",
    ["#24104f", "#63358d", "#bd4f91", "#ec865f", "#f5c96a", "#fff2c6"],
    N=256,
)


def _experiment1_config(
    config_path: Path,
    observed_path: Path,
    *,
    catalyst_mass_g: float = 3.12,
    particle_density_kg_m3: float = 1250.0,
) -> tuple[ReactorConfig, dict[str, float]]:
    """Build the fixed-space-time Experiment 1 basis used in the 2D ratio map."""
    template = ReactorConfig.from_json(config_path)
    observed = json.loads(observed_path.read_text(encoding="utf-8"))
    basis = observed["basis"]
    feed = observed["inlet_molar_flow_mol_h"]
    co_mol_h = float(feed["CO"])
    h2_mol_h = float(feed["H2"])
    n2_mol_h = float(feed["N2"])
    catalyst_mass_kg = catalyst_mass_g / 1000.0
    if min(co_mol_h, catalyst_mass_kg, particle_density_kg_m3) <= 0.0:
        raise ValueError("CO flow, catalyst mass, and particle density must be positive.")

    voidage = 1.0 - catalyst_mass_kg / (particle_density_kg_m3 * template.bed_volume_m3)
    if not 0.0 < voidage < 1.0:
        raise ValueError("The catalyst mass and bed geometry imply invalid voidage.")

    data = deepcopy(template.to_dict())
    data["reaction_mode"] = "m4_full"
    data["feed"]["temperature_k"] = float(basis["reaction_temperature_c"] + 273.15)
    data["feed"]["pressure_bar"] = float(basis["reaction_pressure_bar"])
    data["feed"]["total_molar_flow_mol_s"] = (co_mol_h + h2_mol_h + n2_mol_h) / 3600.0
    data["feed"]["mole_ratio"] = {"CO": co_mol_h, "H2": h2_mol_h, "N2": n2_mol_h}
    data["bed"]["catalyst_loading_kg_m3_bed"] = catalyst_mass_kg / template.bed_volume_m3
    data["bed"]["void_fraction"] = voidage
    data["thermal"]["mode"] = "isothermal"
    data["transport"]["mode"] = "ergun"
    data["solver"]["method"] = "BDF"
    # The Experiment 1 feed scale needs the full-M4 dry-inlet initializer's
    # tighter absolute flow tolerance (same tolerance as the verification run).
    data["solver"]["atol_flow_mol_s"] = 1.0e-14
    config = ReactorConfig.from_dict(data)

    fixed = {
        "co_feed_mol_h": co_mol_h,
        "n2_feed_mol_h": n2_mol_h,
        "n2_co_ratio": n2_mol_h / co_mol_h,
        "catalyst_mass_g": catalyst_mass_g,
        "space_time_kg_s_mol_co": catalyst_mass_kg / (co_mol_h / 3600.0),
        "bed_voidage": voidage,
        "particle_density_kg_m3_assumed": particle_density_kg_m3,
        "reference_h2_co_ratio": h2_mol_h / co_mol_h,
        "reference_temperature_c": float(basis["reaction_temperature_c"]),
        "reference_pressure_bar_abs": float(basis["reaction_pressure_bar"]),
        "source_reported_co_conversion_pct": float(
            observed["reported_metrics"]["co_conversion_fraction"] * 100.0
        ),
    }
    return config, fixed


def _simulate_point(
    base_config: ReactorConfig,
    fixed: dict[str, float],
    *,
    h2_co_ratio: float,
    temperature_c: float,
    pressure_bar: float,
) -> dict[str, object]:
    co_mol_h = fixed["co_feed_mol_h"]
    h2_mol_h = h2_co_ratio * co_mol_h
    n2_mol_h = fixed["n2_feed_mol_h"]
    scenario = deepcopy(base_config.to_dict())
    scenario["feed"]["temperature_k"] = temperature_c + 273.15
    scenario["feed"]["pressure_bar"] = pressure_bar
    scenario["feed"]["total_molar_flow_mol_s"] = (co_mol_h + h2_mol_h + n2_mol_h) / 3600.0
    scenario["feed"]["mole_ratio"] = {"CO": co_mol_h, "H2": h2_mol_h, "N2": n2_mol_h}

    record: dict[str, object] = {
        "h2_co_molar_ratio": h2_co_ratio,
        "inlet_temperature_c": temperature_c,
        "inlet_pressure_bar_abs": pressure_bar,
        "catalyst_space_time_kg_s_mol_co": fixed["space_time_kg_s_mol_co"],
        "co_feed_mol_h": co_mol_h,
        "h2_feed_mol_h": h2_mol_h,
        "n2_feed_mol_h": n2_mol_h,
    }
    try:
        result = simulate(ReactorConfig.from_dict(scenario))
        record.update(
            {
                "outlet_co_conversion_pct": float(result.co_conversion[-1] * 100.0)
                if result.success
                else float("nan"),
                "outlet_ch4_yield_pct": float(result.methane_yield[-1] * 100.0)
                if result.success
                else float("nan"),
                "outlet_pressure_bar_abs": float(result.pressure_pa[-1] / 100000.0),
                "pressure_drop_pa": float(result.pressure_pa[0] - result.pressure_pa[-1]),
                "status": "completed" if result.success else "incomplete",
                "terminal_event": result.terminal_event or "",
                "solver_function_evaluations": int(result.nfev),
                "message": result.message,
            }
        )
    except Exception as error:  # Keep failed cells visible in the output table.
        record.update(
            {
                "outlet_co_conversion_pct": float("nan"),
                "outlet_ch4_yield_pct": float("nan"),
                "outlet_pressure_bar_abs": float("nan"),
                "pressure_drop_pa": float("nan"),
                "status": "error",
                "terminal_event": "",
                "solver_function_evaluations": 0,
                "message": f"{type(error).__name__}: {error}",
            }
        )
    return record


def _write_plot(
    ratios: np.ndarray,
    temperatures_c: np.ndarray,
    pressures_bar: np.ndarray,
    conversion_pct: np.ndarray,
    *,
    fixed: dict[str, float],
    output_path: Path,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "mathtext.fontset": "dejavuserif",
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": "#554a66",
            "savefig.facecolor": PAPER,
        }
    )
    fig = plt.figure(figsize=(12.0, 9.0), facecolor=PAPER)
    ax = fig.add_subplot(111, projection="3d", facecolor=PAPER)
    ratio_grid, temperature_grid = np.meshgrid(ratios, temperatures_c)
    pressure_plane = np.full_like(ratio_grid, 5.0)
    ax.plot_surface(
        ratio_grid,
        temperature_grid,
        pressure_plane,
        color=FIT_LINE,
        alpha=0.11,
        edgecolor=FIT_LINE,
        linewidth=0.25,
        antialiased=False,
        shade=False,
    )
    pressure_grid, temperature_grid_stoich = np.meshgrid(pressures_bar, temperatures_c)
    stoich_plane = np.full_like(pressure_grid, 3.0)
    ax.plot_surface(
        stoich_plane,
        temperature_grid_stoich,
        pressure_grid,
        color="#df9b28",
        alpha=0.055,
        linewidth=0,
        antialiased=False,
        shade=False,
    )

    point_shape = conversion_pct.shape
    r_grid = np.broadcast_to(ratios[None, None, :], point_shape)
    t_grid = np.broadcast_to(temperatures_c[None, :, None], point_shape)
    p_grid = np.broadcast_to(pressures_bar[:, None, None], point_shape)
    valid = np.isfinite(conversion_pct)
    scatter = ax.scatter(
        r_grid[valid],
        t_grid[valid],
        p_grid[valid],
        c=conversion_pct[valid],
        cmap=CMAP,
        norm=Normalize(vmin=0.0, vmax=100.0),
        s=17,
        alpha=0.88,
        edgecolors="none",
        depthshade=False,
        rasterized=True,
    )

    reference_indices = (
        int(np.argmin(np.abs(ratios - fixed["reference_h2_co_ratio"]))),
        int(np.argmin(np.abs(temperatures_c - fixed["reference_temperature_c"]))),
        int(np.argmin(np.abs(pressures_bar - fixed["reference_pressure_bar_abs"]))),
    )
    reference_conversion = float(conversion_pct[reference_indices[2], reference_indices[1], reference_indices[0]])
    ax.scatter(
        [ratios[reference_indices[0]]],
        [temperatures_c[reference_indices[1]]],
        [pressures_bar[reference_indices[2]]],
        marker="*",
        s=155,
        color="white",
        edgecolors=INK,
        linewidths=1.2,
        depthshade=False,
        zorder=10,
    )

    ax.set_xlabel(r"Inlet H$_2$/CO molar ratio", labelpad=12, fontsize=11)
    ax.set_ylabel("Inlet temperature (°C)", labelpad=12, fontsize=11)
    ax.set_zlabel("Inlet pressure (bar abs)", labelpad=10, fontsize=11)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_yticks([250, 300, 350, 400])
    ax.set_zticks([1, 2, 5, 10, 15])
    ax.set_xlim(float(ratios[0]), float(ratios[-1]))
    ax.set_ylim(float(temperatures_c[0]), float(temperatures_c[-1]))
    ax.set_zlim(float(pressures_bar[0]), float(pressures_bar[-1]))
    ax.view_init(elev=25, azim=-56)
    ax.set_box_aspect((1.15, 1.5, 1.15))
    ax.grid(True, alpha=0.18)

    ax.legend(
        handles=[
            Line2D(
                [],
                [],
                marker="*",
                linestyle="none",
                markerfacecolor="white",
                markeredgecolor=INK,
                markersize=11,
                label=f"Experiment 1 reference ({reference_conversion:.1f}%)",
            ),
            Patch(facecolor=FIT_LINE, edgecolor=FIT_LINE, alpha=0.22, label="5 bar kinetic-fit boundary"),
            Line2D([], [], color="#df9b28", linestyle="--", linewidth=1.7, label="Stoichiometric H$_2$/CO = 3"),
        ],
        loc="upper left",
        bbox_to_anchor=(0.0, 0.98),
        frameon=True,
        facecolor=PAPER,
        edgecolor="#d7d0dc",
        fontsize=8.6,
    )

    fig.suptitle(
        "CO Conversion Across Feed Stoichiometry, Temperature, and Pressure",
        x=0.08,
        y=0.97,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.08,
        0.925,
        rf"Fixed $W_{{cat}}/F_{{CO,in}}$ = {fixed['space_time_kg_s_mol_co']:.2f} kg$_{{cat}}$ s mol$^{{-1}}_{{CO}}$  ·  "
        rf"$W_{{cat}}$ = {fixed['catalyst_mass_g']:.2f} g  ·  isothermal full M4",
        ha="left",
        fontsize=9.8,
        color="#685d70",
    )
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.10, shrink=0.74, aspect=28)
    colorbar.set_label("Predicted outlet CO conversion (%)", fontsize=10)
    colorbar.set_ticks(np.arange(0, 101, 20))
    colorbar.outline.set_edgecolor("#b9afbf")
    fig.text(
        0.08,
        0.045,
        "P < 5 bar is below the published kinetic-fit pressure range. "
        f"Reference model: {reference_conversion:.1f}% vs source-reported {fixed['source_reported_co_conversion_pct']:.2f}% (not a fit target). "
        "Each point is one independent inlet-condition simulation.",
        ha="left",
        fontsize=8.5,
        color="#51475e",
    )
    fig.subplots_adjust(left=0.02, right=0.92, top=0.88, bottom=0.085)
    fig.savefig(output_path.with_suffix(".png"), dpi=320, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n", encoding="utf-8")
    plt.close(fig)


def run_sweep(
    config_path: Path,
    observed_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    base_config, fixed = _experiment1_config(config_path, observed_path)
    ratios = np.linspace(1.0, 5.0, 11)
    ratios = np.sort(np.append(ratios, fixed["reference_h2_co_ratio"]))
    temperatures_c = np.array([250.0, 280.0, 300.0, 310.0, 340.0, 350.0, 370.0, 385.0, 400.0])
    pressures_bar = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 9.0, 12.0, 15.0])
    conversion_pct = np.full((len(pressures_bar), len(temperatures_c), len(ratios)), np.nan)
    rows: list[dict[str, object]] = []
    total_cases = conversion_pct.size
    started = time.perf_counter()
    solved = 0

    for pressure_index, pressure in enumerate(pressures_bar):
        for temperature_index, temperature_c in enumerate(temperatures_c):
            for ratio_index, ratio in enumerate(ratios):
                row = _simulate_point(
                    base_config,
                    fixed,
                    h2_co_ratio=float(ratio),
                    temperature_c=float(temperature_c),
                    pressure_bar=float(pressure),
                )
                rows.append(row)
                if row["status"] == "completed":
                    conversion_pct[pressure_index, temperature_index, ratio_index] = float(
                        row["outlet_co_conversion_pct"]
                    )
                solved += 1
                if solved % 75 == 0 or solved == total_cases:
                    print(f"solved {solved}/{total_cases} cases", flush=True)

    successful = [row for row in rows if row["status"] == "completed"]
    failed = total_cases - len(successful)
    if not successful:
        raise RuntimeError("Every stoichiometry/temperature/pressure case failed.")

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "stoich_temperature_pressure_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    _write_plot(
        ratios,
        temperatures_c,
        pressures_bar,
        conversion_pct,
        fixed=fixed,
        output_path=output_dir / "stoich_temperature_pressure_co_conversion",
    )
    values = [float(row["outlet_co_conversion_pct"]) for row in successful]
    minimum_row = min(successful, key=lambda row: float(row["outlet_co_conversion_pct"]))
    maximum_row = max(successful, key=lambda row: float(row["outlet_co_conversion_pct"]))
    metadata: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": "m4_full",
        "metric": "completed-bed outlet CO conversion (%)",
        "grid": {
            "h2_co_ratio": ratios.tolist(),
            "inlet_temperature_c": temperatures_c.tolist(),
            "inlet_pressure_bar_abs": pressures_bar.tolist(),
            "point_count": total_cases,
        },
        "fixed_basis": fixed,
        "model_settings": {
            "thermal_mode": "isothermal",
            "transport_mode": "ergun",
            "solver_method": "BDF",
            "co_feed_fixed_mol_h": fixed["co_feed_mol_h"],
            "n2_co_ratio_fixed": fixed["n2_co_ratio"],
        },
        "kinetic_fit_domain": {
            "temperature_c": [250.0, 400.0],
            "pressure_bar_abs": [5.0, 15.0],
            "interpretation": "points below 5 bar extrapolate the pressure-dependent kinetics; values between fit nodes interpolate",
        },
        "completed_cases": len(successful),
        "failed_or_incomplete_cases": failed,
        "conversion_range_pct": [min(values), max(values)],
        "minimum_conversion_case": {
            key: minimum_row[key]
            for key in ("h2_co_molar_ratio", "inlet_temperature_c", "inlet_pressure_bar_abs", "outlet_co_conversion_pct")
        },
        "maximum_conversion_case": {
            key: maximum_row[key]
            for key in ("h2_co_molar_ratio", "inlet_temperature_c", "inlet_pressure_bar_abs", "outlet_co_conversion_pct")
        },
        "reference_case_conversion_pct": float(
            conversion_pct[
                int(np.argmin(np.abs(pressures_bar - fixed["reference_pressure_bar_abs"]))),
                int(np.argmin(np.abs(temperatures_c - fixed["reference_temperature_c"]))),
                int(np.argmin(np.abs(ratios - fixed["reference_h2_co_ratio"]))),
            ]
        ),
        "elapsed_seconds": time.perf_counter() - started,
        "interpretation_note": (
            "Space time is omitted as an axis and held at the Experiment 1 reference value by keeping catalyst mass and CO feed fixed. "
            "This is an isothermal overview at the Experiment 1 bed/feed basis, unlike the earlier assumed-base-case heat-exchange temperature-pressure map. "
            "The 1 in by 12 in geometry and particle density are assumed; their combination with 3.12 g gives a sparse bed. "
            "This pre-optimization map is exploratory, not experimental validation."
        ),
    }
    (output_dir / "sweep_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# H2/CO ratio, temperature, and pressure overview\n\n"
        "Run from the project root with `uv run m4-sweep-stoich-temperature-pressure`.\n\n"
        "The 3D scatter uses H2/CO feed ratio, inlet temperature, and inlet pressure as coordinates; point color gives predicted completed-bed CO conversion. "
        "It fixes Experiment 1 catalyst mass (3.12 g), CO flow (0.320 mol/h), and N2/CO ratio (2.496875), which fixes catalyst space time at 35.10 kg_cat s/mol_CO. "
        "The full M4 model is isothermal for this overview.\n\n"
        "Pressure below 5 bar lies outside the published kinetic-fit pressure range. The model uses Appendix A's 2 bar Experiment 1 basis; the source also describes atmospheric pressure elsewhere. "
        f"The model's Experiment 1 reference prediction is {metadata['reference_case_conversion_pct']:.2f}% versus the source-reported {fixed['source_reported_co_conversion_pct']:.2f}%; the reported value is not a fit target. "
        "Geometry and particle density remain inherited assumptions, producing a sparse bed at this catalyst charge. Treat this as an exploratory pre-optimization map, not validation.\n",
        encoding="utf-8",
    )
    print(
        f"completed={len(successful)} failed_or_incomplete={failed} "
        f"conversion_pct={min(values):.3f}..{max(values):.3f} "
        f"reference_pct={metadata['reference_case_conversion_pct']:.3f}"
    )
    print(f"outputs={output_dir.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an isothermal full-M4 overview in H2/CO ratio, inlet temperature, and inlet pressure."
    )
    parser.add_argument("--config", type=Path, default=Path("configs/assumed_base_case.json"))
    parser.add_argument("--observed", type=Path, default=Path("data/experiment1_observed_data.json"))
    parser.add_argument(
        "--output", type=Path, default=Path("results/experiment1_stoich_temperature_pressure_sweep")
    )
    args = parser.parse_args()
    run_sweep(args.config, args.observed, args.output)


if __name__ == "__main__":
    main()
