from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

NAVY = "#183B56"
BLUE = "#3B82A0"
TEAL = "#2A7F62"
ORANGE = "#C65D2E"
PURPLE = "#73558C"
RED = "#A33D3D"
GRAY = "#61727D"
GRID = "#DDE3E7"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.labelsize": 8.7,
    "axes.titlesize": 9,
    "xtick.labelsize": 7.8,
    "ytick.labelsize": 7.8,
    "legend.fontsize": 7.4,
    "axes.linewidth": 0.7,
    "lines.linewidth": 1.55,
    "lines.solid_capstyle": "round",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / name, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def style_axis(ax: plt.Axes, grid: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#667680")
    ax.spines["bottom"].set_color("#667680")
    ax.tick_params(direction="out", length=3, width=0.65, color="#667680")
    if grid:
        ax.grid(True, color=GRID, linewidth=0.55, zorder=0)
        ax.set_axisbelow(True)


def save_comparison() -> None:
    from methanation.experiment1_three_model_verification import run_three_model_verification

    source = json.loads((ROOT / "data" / "experiment1_observed_data.json").read_text(encoding="utf-8"))
    _, m4, kop, quin = run_three_model_verification(source)
    fig, ax = plt.subplots(figsize=(6.25, 3.65), constrained_layout=True)
    profiles = [
        ("Full M4", np.asarray(m4.catalyst_mass_kg) * 1000, 100 * np.asarray(m4.co_conversion), NAVY),
        ("Kopyscinski", np.asarray(kop.catalyst_mass_kg) * 1000, 100 * np.asarray(kop.co_conversion), PURPLE),
        ("Quindimil", np.asarray(quin.catalyst_mass_kg) * 1000, 100 * np.asarray(quin.co_conversion), ORANGE),
    ]
    for label, x, y, color in profiles:
        ax.plot(x, y, label=label, color=color, linewidth=1.75)
    measured = 100 * float(source["reported_metrics"]["co_conversion_fraction"])
    # The source basis and plotted catalyst-mass coordinate are both in grams.
    mass_g = float(source["basis"]["catalyst_mass_g"])
    ax.axhline(measured, color=RED, linestyle=(0, (3, 2)), linewidth=1.0)
    ax.scatter([mass_g], [measured], s=30, facecolor="white", edgecolor=RED,
               linewidth=1.2, zorder=5)
    ax.set(xlim=(0, 3.25), ylim=(0, 105), xlabel="Catalyst mass (g)",
           ylabel="CO conversion (%)")
    ax.xaxis.set_major_locator(MaxNLocator(7))
    ax.yaxis.set_major_locator(MaxNLocator(6))
    style_axis(ax)
    handles = [
        Line2D([], [], color=color, linewidth=1.75, label=label)
        for label, _, _, color in profiles
    ]
    handles.append(Line2D([], [], color=RED, linestyle=(0, (3, 2)), marker="o",
                           markerfacecolor="white", markeredgecolor=RED,
                           linewidth=1.0, markersize=4.2, label="Reported conversion"))
    ax.legend(handles=handles, frameon=False, loc="center right", ncol=2,
              handlelength=2.1, columnspacing=1.4)
    save(fig, "figure_01_model_comparison.png")


def save_assumed_profiles() -> None:
    data = np.genfromtxt(ROOT / "results" / "assumed_full_m4_case" / "profiles.csv",
                         delimiter=",", names=True)
    z_cm = data["bed_length_m"] * 100
    conversion = data["co_conversion"] * 100
    temp_c = data["temperature_k"] - 273.15
    pressure = data["pressure_bar"]
    fig, axes = plt.subplots(1, 2, figsize=(6.35, 2.62), constrained_layout=True)
    ax = axes[0]
    ax.plot(z_cm, conversion, color=NAVY)
    ax.scatter([z_cm[0]], [conversion[0]], marker="o", s=24, facecolor="white",
               edgecolor=NAVY, linewidth=0.9, zorder=4)
    ax.set(xlabel="Bed length (cm)", ylabel="CO conversion (%)", ylim=(0, 103))
    style_axis(ax)

    ax = axes[1]
    temp_line, = ax.plot(z_cm, temp_c, color=ORANGE, label="Temperature")
    ax.scatter([z_cm[0]], [temp_c[0]], marker="o", s=24, facecolor="white",
               edgecolor=ORANGE, linewidth=0.9, zorder=4)
    ax.set(xlabel="Bed length (cm)", ylabel="Gas temperature (°C)")
    ax.set_ylim(330, 565)
    style_axis(ax)
    ax2 = ax.twinx()
    press_line, = ax2.plot(z_cm, pressure, color=BLUE, linestyle=(0, (4, 2)),
                           linewidth=1.45, label="Pressure")
    ax2.scatter([z_cm[0]], [pressure[0]], marker="o", s=24, facecolor="white",
                edgecolor=BLUE, linewidth=0.9, zorder=4)
    ax2.set_ylabel("Pressure (bar)", color=BLUE)
    ax2.set_ylim(4.925, 5.005)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(BLUE)
    ax2.tick_params(axis="y", labelsize=7.6, colors=BLUE, direction="out", length=3, width=0.65)
    ax2.spines["top"].set_visible(False)
    handles = [
        Line2D([], [], color=ORANGE, linewidth=1.55, marker="o", markersize=4,
               markerfacecolor="white", markeredgecolor=ORANGE, label="Temperature"),
        Line2D([], [], color=BLUE, linestyle=(0, (4, 2)), linewidth=1.45,
               marker="o", markersize=4, markerfacecolor="white",
               markeredgecolor=BLUE, label="Pressure"),
    ]
    ax.legend(handles=handles, frameon=False, loc="lower right", ncol=2,
              handlelength=1.8, borderaxespad=0.15)
    axes[0].legend(handles=[Line2D([], [], color=NAVY, linewidth=1.55, marker="o",
                                  markersize=4, markerfacecolor="white",
                                  markeredgecolor=NAVY, label="CO conversion")],
                   frameon=False, loc="lower right", handlelength=1.8)
    save(fig, "figure_02_assumed_reactor_profiles.png")


def save_species_profile() -> None:
    data = np.genfromtxt(ROOT / "results" / "assumed_full_m4_case" / "profiles.csv",
                         delimiter=",", names=True)
    z_cm = data["bed_length_m"] * 100
    species = [
        ("CO", "concentration_CO_mol_m3", NAVY, "-"),
        ("H$_2$", "concentration_H2_mol_m3", BLUE, "-"),
        ("CH$_4$", "concentration_CH4_mol_m3", ORANGE, "-"),
        ("H$_2$O", "concentration_H2O_mol_m3", TEAL, "--"),
        ("CO$_2$", "concentration_CO2_mol_m3", PURPLE, "-"),
    ]
    fig, ax = plt.subplots(figsize=(6.25, 3.45), constrained_layout=True)
    for label, field, color, linestyle in species:
        vals = np.asarray(data[field], dtype=float)
        vals[vals <= 0] = np.nan
        ax.plot(z_cm, vals, label=label, color=color, linestyle=linestyle)
    ax.set_yscale("log")
    ax.set(xlabel="Bed length (cm)", ylabel="Gas concentration (mol m$^{-3}$)")
    ax.set_ylim(1e-3, 2e1)
    style_axis(ax)
    ax.legend(frameon=False, loc="center right", ncol=1)
    save(fig, "figure_03_species_profiles.png")


def save_temperature_pressure_map() -> None:
    rows = read_csv(ROOT / "results" / "temperature_pressure_full_m4_sweep" /
                    "temperature_pressure_sweep.csv")
    rows = [r for r in rows if r["status"] == "completed" and
            float(r["inlet_pressure_bar_abs"]) >= 5.0]
    temps = np.array(sorted({float(r["inlet_temperature_c"]) for r in rows}))
    pressures = np.array(sorted({float(r["inlet_pressure_bar_abs"]) for r in rows}))
    lookup = {(float(r["inlet_temperature_c"]), float(r["inlet_pressure_bar_abs"])):
              float(r["outlet_co_conversion_pct"]) for r in rows}
    z = np.array([[lookup[(t, p)] for t in temps] for p in pressures])
    fig, ax = plt.subplots(figsize=(6.2, 3.8), constrained_layout=True)
    levels = np.linspace(90, 100, 11)
    cf = ax.contourf(temps, pressures, z, levels=levels, cmap="cividis", extend="both")
    ax.scatter([350], [5], marker="o", s=32, color="white", edgecolor=NAVY,
               linewidth=1.0, zorder=4, clip_on=False)
    ax.legend(handles=[Line2D([], [], color="none", marker="o", markersize=4.5,
                              markerfacecolor="white", markeredgecolor=NAVY,
                              label="Nominal case (350 °C, 5 bar)")],
              frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01),
              handletextpad=0.45, borderaxespad=0)
    ax.set(xlabel="Inlet temperature (°C)", ylabel="Inlet pressure (bar abs.)",
           xlim=(250, 400), ylim=(5, 15))
    style_axis(ax, grid=False)
    cb = fig.colorbar(cf, ax=ax, pad=0.025, ticks=[90, 92, 94, 96, 98, 100])
    cb.set_label("Outlet CO conversion (%)", fontsize=8.2)
    cb.ax.tick_params(labelsize=7.4, length=2)
    save(fig, "figure_04_temperature_pressure_map.png")


def save_ratio_space_time_map() -> None:
    rows = read_csv(ROOT / "results" / "experiment1_ratio_contact_time_sweep_1bar" /
                    "ratio_contact_time_sweep.csv")
    rows = [r for r in rows if r["status"] == "completed"]
    ratios = np.array(sorted({float(r["h2_co_molar_ratio"]) for r in rows}))
    stimes = np.array(sorted({float(r["catalyst_space_time_kg_s_mol_co"]) for r in rows}))
    lookup = {(float(r["h2_co_molar_ratio"]), float(r["catalyst_space_time_kg_s_mol_co"])):
              float(r["outlet_co_conversion_pct"]) for r in rows}
    z = np.array([[lookup[(x, y)] for x in ratios] for y in stimes])
    fig, ax = plt.subplots(figsize=(6.15, 3.85), constrained_layout=True)
    levels = np.linspace(20, 100, 17)
    cf = ax.contourf(ratios, stimes, z, levels=levels, cmap="cividis", extend="both")
    ref_ratio = 2.996875
    ref_stime = 35.1
    ax.scatter([ref_ratio], [ref_stime], marker="o", s=30, color="white",
               edgecolor=NAVY, linewidth=1.0, zorder=4)
    ax.legend(handles=[Line2D([], [], color="none", marker="o", markersize=4.5,
                              markerfacecolor="white", markeredgecolor=NAVY,
                              label="1 bar reference")],
              frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01),
              handletextpad=0.45, borderaxespad=0)
    ax.set_yscale("log")
    ax.set(xlabel="Inlet H$_2$/CO molar ratio",
           ylabel="Catalyst space time (kg$_{cat}$ s mol$_{CO}^{-1}$)",
           xlim=(1, 5), ylim=(stimes.min(), stimes.max()))
    style_axis(ax, grid=False)
    cb = fig.colorbar(cf, ax=ax, pad=0.025, ticks=[20, 40, 60, 80, 100])
    cb.set_label("Outlet CO conversion (%)", fontsize=8.2)
    cb.ax.tick_params(labelsize=7.4, length=2)
    save(fig, "figure_05_ratio_space_time_map.png")


def save_feed_flow_map() -> None:
    rows = read_csv(ROOT / "results" / "experiment1_feed_flow_sensitivity_1bar" /
                    "feed_flow_contour.csv")
    rows = [r for r in rows if r["status"] == "completed"]
    panels = [
        ("H2_vs_CO_at_fixed_N2", "CO inlet flow (mol h$^{-1}$)", "H$_2$ inlet flow (mol h$^{-1}$)",
         0.32, 0.959),
        ("H2_vs_N2_at_fixed_CO", "N$_2$ inlet flow (mol h$^{-1}$)", "H$_2$ inlet flow (mol h$^{-1}$)",
         0.799, 0.959),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(6.45, 3.15), constrained_layout=True,
                             sharey=True)
    norm = Normalize(vmin=20, vmax=100)
    cf = None
    for ax, (panel_key, xlab, ylab, refx, refy) in zip(axes, panels):
        subset = [r for r in rows if r["panel"] == panel_key]
        xs = np.array(sorted({float(r["x_feed_mol_h"]) for r in subset}))
        ys = np.array(sorted({float(r["y_feed_mol_h"]) for r in subset}))
        lookup = {(float(r["x_feed_mol_h"]), float(r["y_feed_mol_h"])):
                  float(r["co_conversion_pct"]) for r in subset}
        z = np.array([[lookup.get((x, y), np.nan) for x in xs] for y in ys])
        cf = ax.contourf(xs, ys, z, levels=np.linspace(20, 100, 17), cmap="cividis",
                         norm=norm, extend="both")
        ax.scatter([refx], [refy], marker="o", s=28, facecolor="white",
                   edgecolor=NAVY, linewidth=0.8, zorder=5)
        ax.set(xlabel=xlab, ylabel=ylab)
        style_axis(ax, grid=False)
    fig.legend(handles=[Line2D([], [], color="none", marker="o", markersize=4.5,
                               markerfacecolor="white", markeredgecolor=NAVY,
                               label="Experiment 1 reference")],
               frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01),
               handletextpad=0.45, borderaxespad=0)
    cb = fig.colorbar(cf, ax=axes, pad=0.025, fraction=0.045, ticks=[20, 40, 60, 80, 100])
    cb.set_label("Outlet CO conversion (%)", fontsize=8.0)
    cb.ax.tick_params(labelsize=7.2, length=2)
    save(fig, "figure_06_feed_flow_sensitivities.png")


def save_nitrogen_sweep() -> None:
    rows = read_csv(ROOT / "results" / "experiment1_n2_isolated_sensitivity_1bar" /
                    "n2_conversion_sweep.csv")
    rows = [r for r in rows if r["status"] == "completed"]
    rows.sort(key=lambda r: float(r["n2_feed_mol_h"]))
    x = np.array([float(r["n2_feed_mol_h"]) for r in rows])
    y = np.array([float(r["co_conversion_pct"]) for r in rows])
    refx = 0.799
    refy = 78.7225
    fig, ax = plt.subplots(figsize=(6.25, 3.35), constrained_layout=True)
    ax.plot(x, y, color=NAVY, linewidth=1.6)
    ax.scatter(x, y, s=9, facecolor="white", edgecolor=NAVY,
               linewidth=0.65, zorder=4)
    ax.scatter([refx], [refy], marker="o", s=30, facecolor=ORANGE,
               edgecolor="white", linewidth=0.8, zorder=5)
    ax.set(xlim=(0.38, 1.22), ylim=(66, 92),
           xlabel="Inlet N$_2$ molar flow (mol h$^{-1}$)",
           ylabel="Outlet CO conversion (%)")
    style_axis(ax)
    ax.legend(handles=[Line2D([], [], color="none", marker="o", markersize=4.5,
                              markerfacecolor=ORANGE, markeredgecolor="white",
                              label="Experiment 1 reference")],
              frameon=False, loc="upper right", handletextpad=0.45)
    save(fig, "figure_07_nitrogen_sensitivity.png")


if __name__ == "__main__":
    save_comparison()
    save_assumed_profiles()
    save_species_profile()
    save_temperature_pressure_map()
    save_ratio_space_time_map()
    save_feed_flow_map()
    save_nitrogen_sweep()
    print(f"Saved paper figures to {OUT}")
