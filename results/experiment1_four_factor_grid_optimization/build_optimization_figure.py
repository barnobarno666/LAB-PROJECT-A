"""Build a poster-ready pressure-slice figure from the four-factor grid."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FormatStrFormatter, MaxNLocator
import numpy as np


HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "four_factor_grid_search.csv"
SUMMARY_PATH = HERE / "optimization_summary.json"
OUTPUT_STEM = HERE / "four_factor_optimization_pressure_slices"

INK = "#241b35"
PAPER = "#fffdf9"
CMAP = LinearSegmentedColormap.from_list(
    "violet_sunset",
    ["#24104f", "#63358d", "#bd4f91", "#ec865f", "#f5c96a", "#fff2c6"],
    N=256,
)


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    optimum = summary["best_grid_case"]
    space_time = float(optimum["catalyst_space_time_kg_s_mol_co"])
    pressures = (5.0, 9.0, 15.0)

    records: list[dict[str, str]] = []
    with CSV_PATH.open(newline="", encoding="utf-8") as stream:
        records.extend(csv.DictReader(stream))

    ratios = sorted({float(row["h2_co_molar_ratio"]) for row in records})
    # The source-ratio point 2.996875 sits almost on top of the exact 3.0
    # stoichiometric grid point; omit the near-duplicate only in this figure.
    ratios = [r for r in ratios if not (abs(r - 3.0) < 0.01 and r != 3.0)]
    temperatures = sorted({float(row["inlet_temperature_c"]) for row in records})

    conversion_matrices: dict[float, np.ndarray] = {}
    for pressure in pressures:
        matrix = np.full((len(temperatures), len(ratios)), np.nan)
        selected = [
            row
            for row in records
            if row["status"] == "completed"
            and np.isclose(float(row["catalyst_space_time_kg_s_mol_co"]), space_time, atol=1e-9)
            and np.isclose(float(row["inlet_pressure_bar_abs"]), pressure)
        ]
        for row in selected:
            ratio = float(row["h2_co_molar_ratio"])
            if ratio not in ratios:
                continue
            ti = temperatures.index(float(row["inlet_temperature_c"]))
            ri = ratios.index(ratio)
            matrix[ti, ri] = float(row["outlet_co_conversion_pct"])
        if np.isnan(matrix).any():
            raise RuntimeError(f"Pressure slice at {pressure:g} bar has missing grid cells.")
        conversion_matrices[pressure] = matrix

    all_values = np.concatenate([array.ravel() for array in conversion_matrices.values()])
    vmin, vmax = float(np.min(all_values)), float(np.max(all_values))
    if np.isclose(vmin, vmax):
        vmin -= 0.5
        vmax += 0.5
    fill_levels = np.linspace(vmin, vmax, 19)
    line_levels = [level for level in (50.0, 60.0, 70.0, 80.0, 90.0, 95.0, 99.0) if vmin < level < vmax]

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "mathtext.fontset": "dejavuserif",
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": "#554a66",
            "xtick.color": INK,
            "ytick.color": INK,
            "savefig.facecolor": PAPER,
        }
    )

    fig = plt.figure(figsize=(13.8, 5.6), facecolor=PAPER)
    grid = fig.add_gridspec(
        1,
        4,
        width_ratios=(1.0, 1.0, 1.0, 0.055),
        left=0.075,
        right=0.94,
        bottom=0.21,
        top=0.79,
        wspace=0.17,
    )
    axes = [fig.add_subplot(grid[0, i]) for i in range(3)]
    cax = fig.add_subplot(grid[0, 3])

    contour = None
    for ax, pressure in zip(axes, pressures):
        contour = ax.contourf(
            ratios,
            temperatures,
            conversion_matrices[pressure],
            levels=fill_levels,
            cmap=CMAP,
            antialiased=True,
            extend="neither",
        )
        if len(line_levels):
            ax.contour(
                ratios,
                temperatures,
                conversion_matrices[pressure],
                levels=line_levels,
                colors="#fff8ec",
                linewidths=0.7,
                alpha=0.9,
            )

        ax.set_title(f"{pressure:g} bar abs", loc="left", fontsize=11.2, fontweight="bold", pad=8)
        ax.set_xlim(0.9, 5.18)
        ax.set_ylim(245.0, 405.0)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_yticks([250, 300, 350, 400])
        ax.grid(color="#756a7d", alpha=0.15, linewidth=0.55)
        ax.tick_params(which="major", length=4.5, width=0.75, direction="out", labelsize=9)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

        if pressure == float(optimum["inlet_pressure_bar_abs"]):
            ax.scatter(
                [float(optimum["h2_co_molar_ratio"])],
                [float(optimum["inlet_temperature_c"])],
                s=95,
                marker="*",
                facecolor="#cf2d34",
                edgecolor=PAPER,
                linewidth=1.2,
                zorder=6,
            )
            ax.annotate(
                "Grid maximum\n99.99999%",
                xy=(float(optimum["h2_co_molar_ratio"]), float(optimum["inlet_temperature_c"])),
                xytext=(3.15, 382),
                textcoords="data",
                fontsize=8.2,
                color="#a51f2b",
                ha="right",
                va="center",
                arrowprops={"arrowstyle": "->", "color": "#cf2d34", "lw": 1.0},
                bbox={"boxstyle": "round,pad=0.28", "facecolor": PAPER, "edgecolor": "#d4c9c7", "alpha": 0.97},
                zorder=7,
            )

    axes[0].set_ylabel("Inlet temperature (°C)", fontsize=10.7, labelpad=8)
    for ax in axes:
        ax.set_xlabel("Inlet H₂/CO molar ratio", fontsize=10.2, labelpad=7)

    colorbar = fig.colorbar(contour, cax=cax)
    colorbar.set_label("Outlet CO conversion (%)", fontsize=9.6, labelpad=8)
    colorbar.locator = MaxNLocator(nbins=6)
    colorbar.formatter = FormatStrFormatter("%.1f")
    colorbar.update_ticks()
    colorbar.outline.set_edgecolor("#b8b2a5")
    colorbar.outline.set_linewidth(0.7)
    colorbar.ax.tick_params(labelsize=8.5, length=3.5, width=0.7)

    fig.text(
        0.075,
        0.955,
        "CO conversion across the pressure slices",
        ha="left",
        va="top",
        fontsize=17.5,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.076,
        0.885,
        r"Full M4, isothermal  ·  $W_{cat}/F_{CO,in}=140.4$ kg$_{cat}$ s mol$^{-1}_{CO}$  ·  "
        r"$N_2/CO=2.4969$  ·  catalyst charge = 3.12 g",
        ha="left",
        va="top",
        fontsize=9.5,
        color="#5c5264",
    )
    fig.text(
        0.075,
        0.075,
        "Pressure panels show selected levels within the 5–15 bar kinetic-fit range. "
        "The star marks the best sampled grid point; 1–4 bar extrapolation cases are omitted.",
        ha="left",
        va="bottom",
        fontsize=8.4,
        color="#5c5264",
    )

    fig.savefig(OUTPUT_STEM.with_suffix(".png"), dpi=360, bbox_inches="tight", facecolor=PAPER)
    fig.savefig(OUTPUT_STEM.with_suffix(".svg"), bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    svg_path = OUTPUT_STEM.with_suffix(".svg")
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_STEM.with_suffix('.png')}")
    print(f"Wrote {OUTPUT_STEM.with_suffix('.svg')}")
    print(f"Slice conversion range: {vmin:.6f}–{vmax:.6f}%")


if __name__ == "__main__":
    main()
