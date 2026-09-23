"""Run and plot a full-M4 inlet-temperature/pressure sensitivity grid."""

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
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FormatStrFormatter
import numpy as np

from .config import ReactorConfig
from .reactor import simulate


CMAP = LinearSegmentedColormap.from_list(
    "violet_sunset",
    ["#24104f", "#63358d", "#bd4f91", "#ec865f", "#f5c96a", "#fff2c6"],
    N=256,
)
INK = "#241b35"
PAPER = "#fffdf9"


def _axis_with_references(
    minimum: float,
    maximum: float,
    points: int,
    references: tuple[float, ...],
) -> np.ndarray:
    values = np.linspace(minimum, maximum, points)
    for reference in references:
        if minimum <= reference <= maximum and not np.any(np.isclose(values, reference)):
            values = np.append(values, reference)
    return np.sort(values)


def _draw_contour_band(
    ax,
    temperature_c: np.ndarray,
    pressure_bar: np.ndarray,
    conversion_pct: np.ndarray,
):
    valid_values = conversion_pct[np.isfinite(conversion_pct)]
    low = float(np.min(valid_values))
    high = float(np.max(valid_values))
    if np.isclose(low, high):
        low -= 0.5
        high += 0.5
    contour = ax.contourf(
        temperature_c,
        pressure_bar,
        np.ma.masked_invalid(conversion_pct),
        levels=np.linspace(low, high, 17),
        cmap=CMAP,
        antialiased=True,
    )
    line_levels = np.linspace(low, high, 6)[1:-1]
    ax.contour(
        temperature_c,
        pressure_bar,
        np.ma.masked_invalid(conversion_pct),
        levels=line_levels,
        colors="#fff8ec",
        linewidths=0.75,
        alpha=0.85,
    )
    return contour, low, high


def _style_sweep_axes(ax, temperature_c: np.ndarray, pressure_bar: np.ndarray) -> None:
    ax.set_xlim(float(temperature_c[0]), float(temperature_c[-1]))
    ax.set_ylim(float(pressure_bar[0]), float(pressure_bar[-1]))
    ax.set_xlabel(r"Inlet temperature, $T_{\mathrm{in}}$ [$^\circ$C]", fontsize=11.5, labelpad=9)
    ax.set_ylabel(r"Inlet pressure, $P_{\mathrm{in}}$ [bar abs]", fontsize=11.5, labelpad=9)
    ax.set_xticks(np.arange(np.ceil(temperature_c[0] / 25) * 25, temperature_c[-1] + 1, 25))
    ax.set_yticks([p for p in (1, 3, 5, 7, 10, 12, 15) if pressure_bar[0] <= p <= pressure_bar[-1]])
    ax.tick_params(which="major", length=5, width=0.8, direction="out")
    ax.grid(color="#6f6276", alpha=0.13, linewidth=0.55)


def _add_nominal_marker(ax, base_config: ReactorConfig, baseline_conversion_pct: float) -> None:
    nominal_temperature_c = base_config.feed.temperature_k - 273.15
    ax.scatter(
        [nominal_temperature_c],
        [base_config.feed.pressure_bar],
        s=62,
        marker="o",
        facecolor=PAPER,
        edgecolor=INK,
        linewidth=1.5,
        zorder=5,
    )
    ax.annotate(
        f"Nominal case  {baseline_conversion_pct:.2f}%",
        xy=(nominal_temperature_c, base_config.feed.pressure_bar),
        xytext=(12, 12),
        textcoords="offset points",
        fontsize=9,
        color=INK,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": PAPER, "edgecolor": "#cfc5d1", "alpha": 0.96},
        arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.8},
        zorder=6,
    )


def _write_fixed_note(fig, base_config: ReactorConfig, wall_temperature_c: float) -> None:
    bed = base_config.bed
    fixed_note = (
        rf"Fixed: CO:H$_2$:N$_2$ = 1:4:25; $F_{{T,0}}$ = {base_config.feed.total_molar_flow_mol_s:.3g} mol s$^{{-1}}$; "
        rf"bed = {bed.tube_diameter_m / 0.0254:.2f} in $\times$ {bed.bed_length_m / 0.0254:.2f} in; "
        rf"wall = {wall_temperature_c:.0f} $^\circ$C."
    )
    fig.text(0.105, 0.065, fixed_note, ha="left", va="center", fontsize=8.4, color="#51475e")


def _write_plot(
    temperature_c: np.ndarray,
    pressure_bar: np.ndarray,
    conversion_pct: np.ndarray,
    baseline_conversion_pct: float,
    output_path: Path,
    *,
    wall_temperature_c: float,
    base_config: ReactorConfig,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "mathtext.fontset": "dejavuserif",
            "axes.labelcolor": INK,
            "axes.edgecolor": "#554a66",
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "savefig.facecolor": PAPER,
        }
    )
    fig = plt.figure(figsize=(11.0, 8.8), facecolor=PAPER)
    ax = fig.add_axes([0.12, 0.31, 0.75, 0.55])
    fit_mask = pressure_bar >= 5.0
    extended_mask = pressure_bar <= 5.0

    extended_data = conversion_pct[extended_mask, :]
    fit_data = conversion_pct[fit_mask, :]
    extended_contour, extended_low, extended_high = _draw_contour_band(
        ax, temperature_c, pressure_bar[extended_mask], extended_data
    )
    fit_contour, fit_low, fit_high = _draw_contour_band(
        ax, temperature_c, pressure_bar[fit_mask], fit_data
    )
    _style_sweep_axes(ax, temperature_c, pressure_bar)

    ax.axhspan(
        float(pressure_bar[0]),
        5.0,
        facecolor="none",
        edgecolor="#665775",
        hatch="/",
        linewidth=0.35,
        alpha=0.14,
        zorder=3,
    )
    ax.axhline(5.0, color=INK, linewidth=1.35, zorder=4)
    _add_nominal_marker(ax, base_config, baseline_conversion_pct)

    fig.suptitle(
        "Full M4 temperature–pressure sensitivity",
        x=0.12,
        y=0.975,
        ha="left",
        fontsize=16,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.12,
        0.915,
        r"Outlet CO conversion, $X_{\mathrm{CO,out}}$  ·  separate linear scales above and below 5 bar",
        ha="left",
        va="bottom",
        fontsize=10.2,
        color="#685d70",
    )

    fit_cax = fig.add_axes([0.15, 0.17, 0.31, 0.022])
    extended_cax = fig.add_axes([0.54, 0.17, 0.31, 0.022])
    fit_colorbar = fig.colorbar(fit_contour, cax=fit_cax, orientation="horizontal")
    extended_colorbar = fig.colorbar(extended_contour, cax=extended_cax, orientation="horizontal")
    for colorbar, low, high in (
        (fit_colorbar, fit_low, fit_high),
        (extended_colorbar, extended_low, extended_high),
    ):
        colorbar.set_ticks(np.linspace(low, high, 5))
        colorbar.ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        colorbar.outline.set_edgecolor("#b9afbf")
        colorbar.outline.set_linewidth(0.7)
    fig.text(0.15, 0.202, "5–15 bar · Celoria fit pressures", fontsize=8.7, color=INK)
    fig.text(0.54, 0.202, "1–5 bar · below 5 bar outside fit range", fontsize=8.7, color=INK)

    _write_fixed_note(fig, base_config, wall_temperature_c)
    fig.text(
        0.105,
        0.033,
        "Hatching marks 1–<5 bar (outside the paper's pressure-fit range); the two color scales are independent.",
        ha="left",
        va="center",
        fontsize=8.2,
        color="#756a7a",
    )

    fig.savefig(output_path.with_suffix(".png"), dpi=320, bbox_inches="tight")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def _write_fit_domain_plot(
    temperature_c: np.ndarray,
    pressure_bar: np.ndarray,
    conversion_pct: np.ndarray,
    baseline_conversion_pct: float,
    output_path: Path,
    *,
    wall_temperature_c: float,
    base_config: ReactorConfig,
) -> None:
    fit_mask = pressure_bar >= 5.0
    fit_pressure = pressure_bar[fit_mask]
    fit_conversion = conversion_pct[fit_mask, :]
    fig, ax = plt.subplots(figsize=(9.2, 7.0), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    contour, low, high = _draw_contour_band(
        ax, temperature_c, fit_pressure, fit_conversion
    )
    _style_sweep_axes(ax, temperature_c, fit_pressure)
    ax.set_yticks([5, 7, 10, 12, 15])
    ax.set_title("5–15 bar · Celoria kinetic-fit pressure range", loc="left", fontsize=11, pad=8)
    _add_nominal_marker(ax, base_config, baseline_conversion_pct)

    colorbar = fig.colorbar(contour, ax=ax, pad=0.025, fraction=0.045)
    colorbar.set_label(r"Outlet CO conversion [%]", rotation=90, labelpad=12, fontsize=10.5)
    colorbar.set_ticks(np.linspace(low, high, 6))
    colorbar.ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    colorbar.outline.set_edgecolor("#b9afbf")
    colorbar.outline.set_linewidth(0.7)

    fig.suptitle(
        "Full M4 temperature–pressure sensitivity",
        x=0.12,
        y=0.985,
        ha="left",
        fontsize=16,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.12,
        0.895,
        r"Outlet CO conversion, $X_{\mathrm{CO,out}}$",
        ha="left",
        va="bottom",
        fontsize=10.5,
        color="#685d70",
    )
    _write_fixed_note(fig, base_config, wall_temperature_c)
    fig.subplots_adjust(left=0.12, right=0.88, top=0.84, bottom=0.16)
    fig.savefig(output_path.with_suffix(".png"), dpi=320, bbox_inches="tight")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def run_sweep(
    config_path: Path,
    output_dir: Path,
    *,
    points: int = 21,
    temperature_min_c: float = 250.0,
    temperature_max_c: float = 400.0,
    pressure_min_bar: float = 1.0,
    pressure_max_bar: float = 15.0,
) -> dict[str, object]:
    base_config = ReactorConfig.from_json(config_path)
    if base_config.reaction_mode != "m4_full":
        raise ValueError("This sweep requires reaction_mode='m4_full'.")
    if points < 3:
        raise ValueError("points must be at least 3.")
    if temperature_min_c >= temperature_max_c or pressure_min_bar >= pressure_max_bar:
        raise ValueError("Each sweep minimum must be less than its maximum.")
    if pressure_min_bar <= 0.0:
        raise ValueError("pressure_min_bar must be positive.")

    nominal_temperature_c = base_config.feed.temperature_k - 273.15
    temperatures_c = _axis_with_references(
        temperature_min_c,
        temperature_max_c,
        points,
        (250.0, 280.0, 310.0, 340.0, 370.0, 400.0, nominal_temperature_c),
    )
    pressures_bar = _axis_with_references(
        pressure_min_bar,
        pressure_max_bar,
        points,
        (5.0, 15.0, base_config.feed.pressure_bar),
    )
    conversion_pct = np.full((len(pressures_bar), len(temperatures_c)), np.nan)
    rows: list[dict[str, object]] = []
    total_cases = conversion_pct.size
    completed_cases = 0
    started_at = time.perf_counter()
    wall_temperature_c = base_config.thermal.wall_temperature_k - 273.15

    for pressure_index, pressure in enumerate(pressures_bar):
        for temperature_index, temperature_c in enumerate(temperatures_c):
            scenario_data = deepcopy(base_config.to_dict())
            scenario_data["feed"]["temperature_k"] = float(temperature_c + 273.15)
            scenario_data["feed"]["pressure_bar"] = float(pressure)
            try:
                result = simulate(ReactorConfig.from_dict(scenario_data))
                if result.success:
                    outlet_conversion_pct = float(result.co_conversion[-1] * 100.0)
                    conversion_pct[pressure_index, temperature_index] = outlet_conversion_pct
                    status = "completed"
                else:
                    outlet_conversion_pct = float("nan")
                    status = "incomplete"
                row = {
                    "inlet_temperature_c": float(temperature_c),
                    "inlet_pressure_bar_abs": float(pressure),
                    "outlet_co_conversion_pct": outlet_conversion_pct,
                    "outlet_methane_yield_pct": float(result.methane_yield[-1] * 100.0),
                    "peak_temperature_c": float(np.max(result.temperature_k) - 273.15),
                    "outlet_pressure_bar_abs": float(result.pressure_pa[-1] / 100000.0),
                    "status": status,
                    "terminal_event": result.terminal_event or "",
                    "solver_function_evaluations": int(result.nfev),
                    "message": result.message,
                }
            except Exception as error:  # Retain failed grid cells explicitly in the audit table.
                row = {
                    "inlet_temperature_c": float(temperature_c),
                    "inlet_pressure_bar_abs": float(pressure),
                    "outlet_co_conversion_pct": float("nan"),
                    "outlet_methane_yield_pct": float("nan"),
                    "peak_temperature_c": float("nan"),
                    "outlet_pressure_bar_abs": float("nan"),
                    "status": "error",
                    "terminal_event": "",
                    "solver_function_evaluations": 0,
                    "message": f"{type(error).__name__}: {error}",
                }
            rows.append(row)
            completed_cases += 1
            if completed_cases % 25 == 0 or completed_cases == total_cases:
                print(f"solved {completed_cases}/{total_cases} cases", flush=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "temperature_pressure_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    successful = [row for row in rows if row["status"] == "completed"]
    failed = total_cases - len(successful)
    if not successful:
        raise RuntimeError("Every full-M4 sweep case failed; no contour can be drawn.")
    hotspot_extrapolations = [
        row for row in successful if float(row["peak_temperature_c"]) > 400.0
    ]
    pressure_extrapolations = [
        row for row in successful if float(row["inlet_pressure_bar_abs"]) < 5.0
    ]
    sampled_peak_temperatures_c = [
        float(row["peak_temperature_c"]) for row in successful
    ]

    baseline_row = next(
        row
        for row in rows
        if np.isclose(row["inlet_temperature_c"], nominal_temperature_c)
        and np.isclose(row["inlet_pressure_bar_abs"], base_config.feed.pressure_bar)
    )
    baseline_conversion_pct = float(baseline_row["outlet_co_conversion_pct"])
    figure_path = output_dir / "full_m4_temperature_pressure_contour"
    _write_plot(
        temperatures_c,
        pressures_bar,
        conversion_pct,
        baseline_conversion_pct,
        figure_path,
        wall_temperature_c=wall_temperature_c,
        base_config=base_config,
    )
    fit_domain_figure_path = output_dir / "full_m4_temperature_pressure_contour_5_15bar"
    _write_fit_domain_plot(
        temperatures_c,
        pressures_bar,
        conversion_pct,
        baseline_conversion_pct,
        fit_domain_figure_path,
        wall_temperature_c=wall_temperature_c,
        base_config=base_config,
    )

    elapsed_seconds = time.perf_counter() - started_at
    minimum_case = min(successful, key=lambda row: float(row["outlet_co_conversion_pct"]))
    maximum_case = max(successful, key=lambda row: float(row["outlet_co_conversion_pct"]))

    def summary_case(row: dict[str, object]) -> dict[str, float]:
        return {
            "inlet_temperature_c": float(row["inlet_temperature_c"]),
            "inlet_pressure_bar_abs": float(row["inlet_pressure_bar_abs"]),
            "outlet_co_conversion_pct": float(row["outlet_co_conversion_pct"]),
            "peak_temperature_c": float(row["peak_temperature_c"]),
        }

    metadata: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": "m4_full",
        "sensitivity_metric": "completed-bed outlet CO conversion (%)",
        "temperature_range_c": [float(temperatures_c[0]), float(temperatures_c[-1])],
        "pressure_range_bar_abs": [float(pressures_bar[0]), float(pressures_bar[-1])],
        "temperature_points": int(len(temperatures_c)),
        "pressure_points": int(len(pressures_bar)),
        "paper_kinetic_test_nodes": {
            "temperature_c": [250.0, 280.0, 310.0, 340.0, 370.0, 400.0],
            "pressure_bar_abs": [5.0, 15.0],
            "between_node_values": (
                "model interpolation within the published fit envelope; "
                "pressure below 5 bar is extrapolation"
            ),
        },
        "nominal_case": {
            "inlet_temperature_c": float(nominal_temperature_c),
            "inlet_pressure_bar_abs": float(base_config.feed.pressure_bar),
            "outlet_co_conversion_pct": baseline_conversion_pct,
        },
        "completed_cases": int(len(successful)),
        "failed_or_incomplete_cases": int(failed),
        "conversion_range_pct": [
            float(minimum_case["outlet_co_conversion_pct"]),
            float(maximum_case["outlet_co_conversion_pct"]),
        ],
        "minimum_conversion_case": summary_case(minimum_case),
        "maximum_conversion_case": summary_case(maximum_case),
        "published_kinetic_fit_domain": {
            "temperature_c": [250.0, 400.0],
            "pressure_bar_abs": [5.0, 15.0],
        },
        "plot_layout": {
            "combined_plot_pressure_bands_bar_abs": [[1.0, 5.0], [5.0, 15.0]],
            "combined_plot_color_scales": "independent linear scales for each pressure band",
            "visually_marked_outside_fit_region": "hatched inlet pressures from 1 to below 5 bar",
            "additional_design": "full_m4_temperature_pressure_contour_5_15bar.png and .svg",
        },
        "cases_with_peak_temperature_above_400c": int(len(hotspot_extrapolations)),
        "cases_with_inlet_pressure_below_5bar": int(len(pressure_extrapolations)),
        "sampled_peak_temperature_range_c": [
            min(sampled_peak_temperatures_c),
            max(sampled_peak_temperatures_c),
        ],
        "elapsed_seconds": float(elapsed_seconds),
        "fixed_inputs": base_config.to_dict(),
        "sweep_behavior": {
            "varied": ["feed.temperature_k", "feed.pressure_bar"],
            "wall_temperature_held_at_c": float(wall_temperature_c),
            "all_other_inputs_held_at_base_config": True,
            "failed_or_incomplete_cells": "excluded from the contour and retained as status rows in the CSV",
        },
        "interpretation_note": (
            "Inlet temperatures lie within the published 250 to 400 C fit range. Inlet pressures from 5 to 15 bar "
            "lie within the fit range; pressures below 5 bar are extrapolations included to cover the 1 bar "
            "experimental condition. The paper sampled six temperatures and two pressures; values between those nodes "
            "within the fit envelope are model interpolations. "
            f"{len(hotspot_extrapolations)} of {len(successful)} cases have sampled peak bed temperatures above "
            f"400 C (sampled peak range {min(sampled_peak_temperatures_c):.1f} to "
            f"{max(sampled_peak_temperatures_c):.1f} C) and therefore extrapolate the kinetics locally. "
            "The contour is exploratory because all outputs are conditional predictions "
            "under assumed base-case inputs, and the thermochemistry remains approximate."
        ),
    }
    (output_dir / "sweep_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(
        f"completed={len(successful)} failed_or_incomplete={failed} "
        f"nominal_conversion_pct={baseline_conversion_pct:.6f}"
    )
    print(f"outputs={output_dir.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a full-M4 inlet-temperature/pressure sensitivity sweep and contour plot."
    )
    parser.add_argument("--config", type=Path, default=Path("configs/assumed_base_case.json"))
    parser.add_argument(
        "--output", type=Path, default=Path("results/temperature_pressure_full_m4_sweep")
    )
    parser.add_argument("--points", type=int, default=21, help="base points on each axis")
    parser.add_argument("--temperature-min-c", type=float, default=250.0)
    parser.add_argument("--temperature-max-c", type=float, default=400.0)
    parser.add_argument("--pressure-min-bar", type=float, default=1.0)
    parser.add_argument("--pressure-max-bar", type=float, default=15.0)
    args = parser.parse_args()
    run_sweep(
        args.config,
        args.output,
        points=args.points,
        temperature_min_c=args.temperature_min_c,
        temperature_max_c=args.temperature_max_c,
        pressure_min_bar=args.pressure_min_bar,
        pressure_max_bar=args.pressure_max_bar,
    )


if __name__ == "__main__":
    main()
